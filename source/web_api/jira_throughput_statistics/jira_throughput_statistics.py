from __future__ import print_function
import math
import datetime
import json
import pytz
from percentile import percentile_calculation
from query_parameters import QueryParameters
from work_type_parser import WorkTypeParser
from time_interval_calculator import TimeIntervalCalculator
from redshift_connection import RedshiftConnection
from jira_helper import get_completion_event_statuses


def handler(event, context):
    # Grab the data passed to the lambda function through the browser URL (API Gateway)
    try:
        projectID = (event.get('pathParameters').get('id'))
    except Exception as e:
        print (e)
        payload = {"message": "Id path parameter not given"}
        response={
            "statusCode": 400,
            "body": json.dumps(payload)
        }
        return response

    redshift = RedshiftConnection()
    cur = redshift.getCursor()

    try:
        redshift.validateProjectID(projectID)
    except Exception:
        redshift.closeConnection()
        payload = {"message": "No resource with project ID {} found".format(projectID)}
        response={
            "statusCode": 404,
            "body": json.dumps(payload)
        }
        return response

    try:
        # Grab the query string parameter of offset(days), dateUntil, dateSince, and workTypes
        queryParameters = QueryParameters(event)
        days = queryParameters.getDays()
        dateUntil = queryParameters.getDate('dateUntil')
        dateSince = queryParameters.getDate('dateSince')
        workTypes = queryParameters.getWorktypes()

        workTypeParser = WorkTypeParser(workTypes,projectID)
        workTypeParser.validateWorkTypes(redshift.getCursor(), redshift.getConn())

        rollingWindowDays = redshift.selectRollingWindow(projectID)
        # Convert rollingWindowDays to rollingWindowWeeks
        rollingWindowWeeks = int(math.floor(rollingWindowDays/7.0))
        timeInterval = TimeIntervalCalculator(dateUntil, dateSince, days)
        timeInterval.decrementDateSinceWeeks(rollingWindowWeeks)

    except ValueError as err:
        redshift.closeConnection()
        payload = {"message": "{}".format(err)}
        response={
            "statusCode": 400,
            "body": json.dumps(payload)
        }
        return response

    dateSince = timeInterval.getDateSinceInt()
    dateUntil = timeInterval.getDateUntilInt()

    endDate = dateUntil
    startDate = dateSince

    # Perform rolling average starting from startDate
    rollingWeeks = [startDate]

    secsPerWeek = 604800
    # Insert into rollingWeeks list all the mondays until dateUntil
    while (startDate < endDate):
        startDate += secsPerWeek
        rollingWeeks.append(startDate)

    status_list = get_completion_event_statuses(redshift, projectID)

    issueTypesList = workTypeParser.issueTypesList
    invalidResolutionsList = workTypeParser.invalidResolutionsList

    selectCompletedQuery = """
        SELECT MAX(changed) AS maxdate FROM issue_change 
        WHERE team_project_id = %s
        AND changed < %s
        AND changed >= %s
        AND new_value IN %s
        AND prev_value IN %s
        AND (%s = 0 OR issue_type IN %s)
        AND (%s = 0 OR resolution NOT IN %s)
        GROUP BY issue_key ORDER BY maxdate ASC
        """
    selectCompletedQuery = cur.mogrify(selectCompletedQuery,
                                       (projectID, rollingWeeks[-1], rollingWeeks[0],
                                        tuple(status_list["completed"]),
                                        tuple(status_list["working"]),
                                        1 if issueTypesList else 0,
                                        tuple(issueTypesList) if issueTypesList else (None,),
                                        1 if invalidResolutionsList else 0,
                                        tuple(invalidResolutionsList) if invalidResolutionsList else (None,)
                                        )
                                       )

    try:
        changes = redshift.executeCommitFetchAll(selectCompletedQuery)
    except Exception:
        print ("Could not perform query: {}".format(selectCompletedQuery))
        redshift.closeConnection()
        payload = {"message": "Internal error"}
        response={
            "statusCode": 500,
            "body": json.dumps(payload)
        }
        return response

    changeIndex = 0
    numCompletedIssues = []
    for week in rollingWeeks:
        if week == rollingWeeks[0]:
            continue
        completed = 0
        while (changeIndex < len(changes) and changes[changeIndex][0] < week):
            completed+=1
            changeIndex+=1
        numCompletedIssues.append(completed)

    rollingWeeksUsed = []

    tenthPercentiles = []
    twentiethPercentiles = []
    fiftiethPercentiles = []
    eightiethPercentiles = []
    ninetiethPercentiles = []

    # For all the weeks in rollingWeeks perform the throughput calculations moving the window
    # each time
    for index in range(len(rollingWeeks)):
        if index + rollingWindowWeeks >= len(rollingWeeks):
            # Avoids indexing out of range
            break
        numCompletedIssuesSubset = numCompletedIssues[index:index+rollingWindowWeeks]
        sortedWeeks = sorted(numCompletedIssuesSubset)
        # Perform the calculation for each percentile
        # Percentile calculation includes linear interpolation for more accurate values
        # https://commons.apache.org/proper/commons-math/javadocs/api-3.0/org/apache/commons/math3/stat/descriptive/rank/Percentile.html
        ninetiethPercentiles.append(percentile_calculation(0.9, sortedWeeks))
        eightiethPercentiles.append(percentile_calculation(0.8, sortedWeeks))
        fiftiethPercentiles.append(percentile_calculation(0.5, sortedWeeks))
        twentiethPercentiles.append(percentile_calculation(0.2, sortedWeeks))
        tenthPercentiles.append(percentile_calculation(0.1, sortedWeeks))

        week = datetime.datetime.fromtimestamp(rollingWeeks[index+rollingWindowWeeks], tz=pytz.utc).isoformat()
        rollingWeeksUsed.append(week)

    # For logging purposes print out the return arrays
    print ("Fiftieth Percentiles: {}".format(fiftiethPercentiles))
    print ("Eightieth Percentiles: {}".format(eightiethPercentiles))
    print ("Ninetieth Percentiles: {}".format(ninetiethPercentiles))

    payload={
                "fiftieth": zip(rollingWeeksUsed, fiftiethPercentiles),
                "eightieth": zip(rollingWeeksUsed, eightiethPercentiles),
                "ninetieth": zip(rollingWeeksUsed, ninetiethPercentiles),
                "twentieth": zip(rollingWeeksUsed, twentiethPercentiles),
                "tenth": zip(rollingWeeksUsed, tenthPercentiles)
            }

    response={
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
            "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS
        },"body": json.dumps(payload)

    }

    redshift.closeConnection()
    return response
