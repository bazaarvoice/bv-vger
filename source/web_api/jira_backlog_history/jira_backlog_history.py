from __future__ import print_function
import datetime
import json
import pytz
from query_parameters import QueryParameters
from redshift_connection import RedshiftConnection
from time_interval_calculator import TimeIntervalCalculator
from work_type_parser import WorkTypeParser
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

    selectIDQuery = cur.mogrify("SELECT name, id FROM team_project WHERE id = %s", (projectID,))

    try:
        IDResults = redshift.executeCommitFetchAll(selectIDQuery)
    except Exception:
        redshift.closeConnection()
        payload = {"message": "Internal Error"}
        response={
            "statusCode": 500,
            "body": json.dumps(payload)
        }
        return response

    if not IDResults:
        redshift.closeConnection()
        payload = {"message": "No resource with project ID {} found".format(projectID)}
        response={
            "statusCode": 404,
            "body": json.dumps(payload)
        }
        return response

    # Grab the query string parameter of dateUntil, dateSince, and offset
    # If omitted dateUntil will be set to current date and time
    # If omitted dateSince will be 90 days before dateUntil
    # These repetitive try/catch blocks are necessary as Lambda throw an exception if the specified
    # parameter is not given.
    try:
        days = int(event.get('queryStringParameters').get('days'))
    except Exception as e:
        # If days not given, set it to default of 90
        days = 90
    try:
        dateUntil = event.get('queryStringParameters').get('dateUntil')
    except Exception as e:
        dateUntil = None
    try:
        dateSince = event.get('queryStringParameters').get('dateSince')
    except Exception as e:
        dateSince = None
    try:
        workTypes = event.get('queryStringParameters').get('workTypes')
    except Exception as e:
        # If workTypes not given, all issue types will be returned
        workTypes = None

    try:
        # Try to decode the given date parameters, if undecodable throw exception
        query_param = QueryParameters()
        dateUntil = query_param.decodeDateParam(dateUntil)
        dateSince = query_param.decodeDateParam(dateSince)
    except ValueError as err:
        redshift.closeConnection()
        payload = {"message": "{}".format(err)}
        response={
            "statusCode": 400,
            "body": json.dumps(payload)
        }
        return response


    workTypeParser = WorkTypeParser(workTypes,projectID)
    try:
        workTypeParser.validateWorkTypes(redshift.getCursor(), redshift.getConn())
    except ValueError as err:
        redshift.closeConnection()
        payload = {"message": "{}".format(err)}
        response={
            "statusCode": 400,
            "body": json.dumps(payload)
        }
        return response

    try:
        timeInterval = TimeIntervalCalculator(dateUntil, dateSince, days)
        timeInterval.decrementDateSinceWeeks(1)
    except ValueError as err:
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
    weeks = [startDate]

    secsPerWeek = 604800
    # Insert into weeks all the mondays until dateUntil
    while (startDate < endDate):
        startDate += secsPerWeek
        weeks.append(startDate)

    issueTypesList = workTypeParser.issueTypesList

    status_list = get_completion_event_statuses(redshift, projectID)

    try:
        selectOpenClosedQuery = """
        SELECT changed, new_value, issue_key
        FROM  issue_change 
        WHERE team_project_id = %(project_id)s
        AND   prev_value = ''
        AND   changed < %(date_until)s
        AND   field_name = 'Status'
        AND (%(issue_type_flag)s = 0 OR issue_type IN %(issue_type_list)s)
        UNION
        SELECT completed.changed,
               'Completed' AS new_value,
               completed.issue_key
        FROM (SELECT MAX(changed) AS changed,
                     'Completed' AS new_value,
                     issue_key
              FROM  issue_change
              WHERE team_project_id = %(project_id)s
              AND   new_value IN %(completed_status)s
              AND   changed < %(date_until)s
              AND   field_name = 'Status'
              AND (%(issue_type_flag)s = 0 OR issue_type IN %(issue_type_list)s)
              GROUP BY issue_key) completed
          LEFT JOIN issue_change uncompleted
                 ON uncompleted.issue_key = completed.issue_key
                AND uncompleted.changed > completed.changed
                AND uncompleted.new_value NOT IN %(completed_status)s
        WHERE uncompleted.changed IS NULL
        ORDER BY changed
        """
        selectOpenClosedQuery = cur.mogrify(selectOpenClosedQuery, {
            "project_id": projectID,
            "date_until": dateUntil,
            "completed_status": tuple(status_list["completed"]),
            "issue_type_list": tuple(issueTypesList) if issueTypesList else (None,),
            "issue_type_flag": 1 if issueTypesList else 0
        })
        cur.execute(selectOpenClosedQuery)
        changes = cur.fetchall()
    except Exception as e:
        print ("ERROR: {}".format(e))
        redshift.closeConnection()
        payload = {"message": "Internal server error"}
        response={
            "statusCode": 500,
            "body": json.dumps(payload)
        }
        return response

    changeIndex = 0

    payload = {"Created": [],
               "Completed": []}
    completed = 0
    created = 0
    for week in weeks:
        while changeIndex < len(changes) and changes[changeIndex][0] < week:
            newValue = changes[changeIndex][1]
            if newValue == 'Completed':
                completed += 1
            elif newValue == 'Open':
                created += 1
            changeIndex += 1

        # isoformat implicitly assumes utc time without appending trailing 'Z'
        weekStr = datetime.datetime.fromtimestamp(week, tz=pytz.utc).isoformat()
        payload["Created"].append([weekStr, created])
        payload["Completed"].append([weekStr, completed])

    response={
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
            "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS
        },
        "body": json.dumps(payload)
    }

    redshift.closeConnection()
    return response
