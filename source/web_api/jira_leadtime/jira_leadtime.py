from __future__ import print_function
import boto3
import os
import psycopg2
import math
import datetime
import pytz

from bisect import insort
from operator import itemgetter

from time_interval_calculator import TimeIntervalCalculator
from work_type_parser import WorkTypeParser
from query_parameters import QueryParameters
from redshift_connection import RedshiftConnection
from percentile import percentile_calculation
from response_helper import response_formatter


def handler(event, context):
    # Grab the data passed to the lambda function through the browser URL (API Gateway)
    try:
        projectID = event.get('pathParameters').get('id')
    except Exception as e:
        payload = {"message": "Id path parameter not given: {]".format(e)}
        return response_formatter(status_code=404, body=payload)

    redshift = RedshiftConnection()

    try:
        redshift.validateProjectID(projectID)
    except Exception as e:
        redshift.closeConnection()
        payload = {"message": "No resource with project ID {} found: {}".format(projectID, e)}
        return response_formatter(status_code=404, body=payload)

    try:
        # Grab the query string parameter of offset(days), dateUntil, dateSince, and workTypes
        queryParameters = QueryParameters(event)
        days = queryParameters.getDays()
        dateUntilParameter = queryParameters.getDate('dateUntil')
        dateSinceParameter = queryParameters.getDate('dateSince')
        workTypes = queryParameters.getWorktypes()

        workTypeParser = WorkTypeParser(workTypes, projectID)
        workTypeParser.validateWorkTypes(redshift.getCursor(), redshift.getConn())

        rollingWindowDays = redshift.selectRollingWindow(projectID)
        # Convert rollingWindowDays to rollingWindowWeeks
        rollingWindowWeeks = int(math.floor(rollingWindowDays / 7.0))
        timeInterval = TimeIntervalCalculator(dateUntilParameter, dateSinceParameter, days)
        timeInterval.decrementDateSinceWeeks(rollingWindowWeeks)

    except ValueError as err:
        redshift.closeConnection()
        payload = {"message": "{}".format(err)}
        return response_formatter(status_code=400, body=payload)

    # Get the actual start and end date after adding rolling weeks in epoch format
    dateSince = timeInterval.getDateSinceInt()
    dateUntil = timeInterval.getDateUntilInt()

    # Generate list of weeks
    endDate = dateUntil
    startDate = dateSince
    rollingWeeks = [startDate]
    secsPerWeek = 604800
    # Insert into weeks all the mondays until dateUntil for label purposes
    while startDate < endDate:
        startDate += secsPerWeek
        rollingWeeks.append(startDate)

    # Init redshift connection
    ENV = os.environ['ENV']
    ssm_base = os.environ["VGER_SSM_BASE"]
    ssm_client = boto3.client('ssm')

    connection_detail = {
        'dbname': ssm_client.get_parameter(Name='/{ssm_env}/redshift/{env}/database_name'.format(ssm_base=ssm_base, env=ENV)),
        'host': ssm_client.get_parameter(Name='/{ssm_env}/redshift/{env}/cluster_endpoint'.format(ssm_base=ssm_base, env=ENV)),
        'port': ssm_client.get_parameter(Name='/{ssm_env}/redshift/{env}/port'.format(ssm_base=ssm_base, env=ENV)),
        'user': ssm_client.get_parameter(Name='/{ssm_env}/redshift/{env}/username'.format(ssm_base=ssm_base, env=ENV)),
        'password': ssm_client.get_parameter(Name='/{ssm_env}/redshift/{env}/password'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)
    }

    conn = psycopg2.connect(**connection_detail)

    # Get the sequence for start and end states for current project
    default_state_query = """
    SELECT seq_number
    FROM   team_project, team_work_states
    WHERE  team_project.id = %s
    AND    team_work_states.team_project_id = %s
    AND    (team_work_states.state_name = team_project.default_lead_time_start_state OR 
            team_work_states.state_name = team_project.default_lead_time_end_state)
    ORDER BY seq_number
    """
    with conn:
        with conn.cursor() as cur:
            cur.execute(default_state_query, (projectID, projectID))
            default_state_results = cur.fetchall()
            start_state_seq = default_state_results[0][0]
            end_state_seq = default_state_results[1][0]

    # Get all work states for current project and generate dict for lead time calculation purposes
    work_state_query = """
    SELECT state_name, seq_number
    FROM team_work_states
    WHERE team_project_id = %s
    ORDER BY seq_number
    """
    with conn:
        with conn.cursor() as cur:
            cur.execute(work_state_query, (projectID,))
            work_states_results = cur.fetchall()
            lead_time_states = [work_state for work_state, work_seq in work_states_results if
                                start_state_seq <= work_seq < end_state_seq]
            work_states_dict = {work_seq: work_state for work_state, work_seq in work_states_results}

    # Filter out invalid issue types and resolutions
    issueTypesList = workTypeParser.issueTypesList
    invalidResolutionsList = workTypeParser.invalidResolutionsList

    # Init rolling interval dict for each week for output purposes
    rolling_intervals = {}
    for index in range(len(rollingWeeks)):
        if index + rollingWindowWeeks >= len(rollingWeeks):
            # Avoids indexing out of range
            break
        week = datetime.datetime.fromtimestamp(rollingWeeks[index + rollingWindowWeeks], tz=pytz.utc).isoformat()
        rolling_intervals[week] = {
            "rolling_interval_start": rollingWeeks[index],
            "rolling_interval_end": rollingWeeks[index + rollingWindowWeeks],
            "leadtime": {
                "Overall": []
            }
        }
        for state in lead_time_states:
            rolling_intervals[week]["leadtime"][state] = []

    # Get all issues within time range and their work state changing history
    issue_query = """
    SELECT issue_key,
           listagg(CASE WHEN s1.seq_number IS NULL THEN -1 ELSE s1.seq_number END,',') within group(ORDER BY issue_change.changed) AS prev_number_seq,
           listagg(CASE WHEN s2.seq_number IS NULL THEN -1 ELSE s2.seq_number END,',') within group(ORDER BY issue_change.changed) AS new_number_seq,
           listagg(issue_change.changed,',') within group(ORDER BY issue_change.changed) AS changed_seq
    FROM issue_change
      LEFT JOIN (SELECT team_status_states.team_project_id,
                        team_status_states.status,
                        team_status_states.state_name,
                        team_work_states.seq_number
                 FROM team_status_states
                   LEFT JOIN team_work_states
                          ON team_status_states.team_project_id = team_work_states.team_project_id
                         AND team_status_states.state_name = team_work_states.state_name) s1
             ON s1.team_project_id = issue_change.team_project_id
            AND s1.status = issue_change.prev_value
      LEFT JOIN (SELECT team_status_states.team_project_id,
                        team_status_states.status,
                        team_status_states.state_name,
                        team_work_states.seq_number
                 FROM team_status_states
                   LEFT JOIN team_work_states
                          ON team_status_states.team_project_id = team_work_states.team_project_id
                         AND team_status_states.state_name = team_work_states.state_name) s2
             ON s2.team_project_id = issue_change.team_project_id
            AND s2.status = issue_change.new_value
    WHERE issue_change.team_project_id = %s
    AND   field_name = 'Status'
    AND (%s = 0 OR issue_type IN %s)
    AND (%s = 0 OR resolution NOT IN %s)
    GROUP BY issue_key
    """
    with conn:
        with conn.cursor() as cur:
            cur.execute(issue_query,
                        (projectID,
                         1 if issueTypesList else 0,
                         tuple(issueTypesList) if issueTypesList else (None,),
                         1 if invalidResolutionsList else 0,
                         tuple(invalidResolutionsList) if invalidResolutionsList else (None,)
                         )
                        )
            results = cur.fetchall()

    # Convert results to dict format
    issues = [{"issue_name": result[0],
               "raw_info": zip(result[1].split(","), result[2].split(","), result[3].split(",")),
               "latest_seq": int(result[2].split(",")[-1])
               } for result in results]

    # If latest/current status is not after lead time end state, it means issue is not done and should be filtered out
    # This keeps only finished issues in result set, meaning every issue will now have all worktime states and will be a finished issue
    issues = [issue for issue in issues if issue["latest_seq"] >= end_state_seq]
    # issues = [issue for issue in issues if issue["leadtime"].get("Overall")]

    # still need to filter out issues that were closed before or after dateSince/DataUntil
    counter = 0
    issuesToDelete = []
    # since poping shifts the indices, each time something needs to be poped, must be subtracted by number of pops needing to be done
    numOfPops = 0

    for issue in issues:
        isIssueDeleted = False
        # Init lead time dictionary
        issue["leadtime"] = {el: 0 for el in [item for item in lead_time_states]}
        # Find the first time to get into leadtime state from pre-leadtime state
        for info in issue["raw_info"]:
            prev_seq_number = int(info[0])
            next_seq_number = int(info[1])
            state_transition_time = int(info[2])
            if prev_seq_number < start_state_seq <= next_seq_number < end_state_seq:
                issue["start_state_time"] = state_transition_time
                break
        # Find the last time to get into post-leadtime state from leadtime state
        for info in reversed(issue["raw_info"]):
            prev_seq_number = int(info[0])
            next_seq_number = int(info[1])
            state_transition_time = int(info[2])
            if start_state_seq <= prev_seq_number < end_state_seq <= next_seq_number:
                issue["end_state_time"] = state_transition_time
                break

        # if issue was completed before or after the set amount of time passed into leadtime script, remove it from issues
        if ("end_state_time" in issue) and (issue["end_state_time"] < int(dateSince) or issue["end_state_time"] > int(
                dateUntil)) and isIssueDeleted == False:
            issuesToDelete.append(counter - numOfPops)
            numOfPops = numOfPops + 1
            isIssueDeleted = True

        # Calculate overall leadtime
        if issue.get("start_state_time") and issue.get("end_state_time"):
            start_time = datetime.datetime.fromtimestamp(issue["start_state_time"])
            end_time = datetime.datetime.fromtimestamp(issue["end_state_time"])
            issue_working_days = TimeIntervalCalculator.workday_diff(start_time, end_time)
            issue["leadtime"]["Overall"] = float("{0:.2f}".format(issue_working_days))
        # if needed parameters don't exist, remove from loop
        elif isIssueDeleted == False:
            issuesToDelete.append(counter - numOfPops)
            numOfPops = numOfPops + 1
            isIssueDeleted = True

            # remove issue if it is less than 15 minutes (0.01) to prevent issues from being displayed on chart as 0
        if ("Overall" in issue["leadtime"]) and issue["leadtime"]["Overall"] < 0.01 and isIssueDeleted == False:
            issuesToDelete.append(counter - numOfPops)
            numOfPops = numOfPops + 1
            isIssueDeleted = True

        counter = counter + 1

    # issues = [issue for issue in issues if issue["leadtime"].get("Overall")]

    # Filter out if the issue did not have finish during the time period
    for num in issuesToDelete:
        issues.pop(num)

    for issue in issues:
        # Calculate lead time for each work state
        state_transition_time = -1
        # Loop through the state changing history and add up lead time for all states
        for info in issue["raw_info"]:
            prev_work_state = work_states_dict.get(int(info[0]))
            new_state_transition_time = int(info[2])
            if prev_work_state in lead_time_states and state_transition_time > 0:
                start_time = datetime.datetime.fromtimestamp(state_transition_time)
                end_time = datetime.datetime.fromtimestamp(new_state_transition_time)
                issue_working_days = TimeIntervalCalculator.workday_diff(start_time, end_time)
                issue["leadtime"][prev_work_state] += issue_working_days

            # Update for looping purposes
            state_transition_time = new_state_transition_time

        # Insert issue lead time into all intervals in ascending order for the percentile calculation
        for key, value in rolling_intervals.iteritems():
            if (value["rolling_interval_start"] < issue["start_state_time"] < value["rolling_interval_end"] and
                    value["rolling_interval_start"] < issue["end_state_time"] < value["rolling_interval_end"]):
                for state, leadtime in issue["leadtime"].iteritems():
                    insort(value["leadtime"][state], leadtime)

    # Init Output
    payload = {
        "fiftieth": {},
        "eightieth": {},
        "ninetieth": {}
    }
    for percentile, content in payload.iteritems():
        for state in lead_time_states:
            content[state] = []
        content["Overall"] = []

    # Generate Output
    for key, value in rolling_intervals.iteritems():
        for state, leadtime in value["leadtime"].iteritems():
            payload["fiftieth"][state].append((key, percentile_calculation(0.5, leadtime)))
            payload["eightieth"][state].append((key, percentile_calculation(0.8, leadtime)))
            payload["ninetieth"][state].append((key, percentile_calculation(0.9, leadtime)))

    # Rearrange Output
    for percentile_res, content in payload.iteritems():
        for state, leadtimes in content.iteritems():
            leadtimes.sort(key=itemgetter(0))

    return response_formatter(status_code=200, body=payload)
