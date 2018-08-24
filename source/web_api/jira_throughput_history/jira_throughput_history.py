from __future__ import print_function
import datetime
import json
import math
import pytz
from query_parameters import QueryParameters
from redshift_connection import RedshiftConnection
from time_interval_calculator import TimeIntervalCalculator
from work_type_parser import WorkTypeParser
from jira_helper import get_completion_event_statuses

from percentile import R7PercentileCalculator
import jira_throughput_tickets

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

        timeInterval = TimeIntervalCalculator(dateUntil, dateSince, days)
        timeInterval.decrementDateSinceWeeks(1)

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
    weeks = [startDate]

    secsPerWeek = 604800
    # Insert into weeks all the mondays until dateUntil
    while (startDate < endDate):
        startDate += secsPerWeek
        weeks.append(startDate)

    status_list = get_completion_event_statuses(redshift, projectID)

    issueTypesList = workTypeParser.issueTypesList
    invalidResolutionsList = workTypeParser.invalidResolutionsList

    selectCompletedQuery = """
    SELECT MAX(changed) AS maxdate, issue_key FROM issue_change 
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
                                       (projectID, weeks[-1], weeks[0],
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
        payload = {"message": "Internal server error"}
        response={
            "statusCode": 500,
            "body": json.dumps(payload)
        }
        return response

    ticketsByWeekPayload = []
    ticketsByWeekPayload = jira_throughput_tickets.buildTicketPayload(changes, weeks)

    changeIndex = 0
    payload = []
    organizedTotals = []

    for week in weeks:
        if week == weeks[0]:
            continue
        completed = 0
        while (changeIndex < len(changes) and changes[changeIndex][0] < week):
            completed+=1
            changeIndex+=1
        # isoformat implicitly assumes utc time without appending trailing 'Z'
        weekStr = datetime.datetime.fromtimestamp(week, tz=pytz.utc).isoformat()+"Z"
        payload.append([weekStr, completed])
        organizedTotals.append(completed)

    organizedTotals = sorted(organizedTotals)
    lengthOfDataSet = len(organizedTotals)

    # Calculate striaght percentile values using the R7 statistical method
    # https://en.wikipedia.org/wiki/Quantile (find: R-7)
    ninetiethPercentilesStraightPoint = R7PercentileCalculator(90.0, organizedTotals, lengthOfDataSet)
    eightiethPercentilesStraightPoint = R7PercentileCalculator(80.0, organizedTotals, lengthOfDataSet)
    fiftiethPercentilesStraightPoint = R7PercentileCalculator(50.0, organizedTotals, lengthOfDataSet)
    twentiethPercentilesStraightPoint = R7PercentileCalculator(20.0, organizedTotals, lengthOfDataSet)
    tenthPercentilesStraightPoint = R7PercentileCalculator(10.0, organizedTotals, lengthOfDataSet)

    #make each "straight percentile" an array of values of equal length to 
    ninetiethPercentilesStraight = [ninetiethPercentilesStraightPoint] * lengthOfDataSet
    eightiethPercentilesStraight = [eightiethPercentilesStraightPoint] * lengthOfDataSet
    fiftiethPercentilesStraight = [fiftiethPercentilesStraightPoint] * lengthOfDataSet
    twentiethPercentilesStraight = [twentiethPercentilesStraightPoint] * lengthOfDataSet
    tenthPercentilesStraight = [tenthPercentilesStraightPoint] * lengthOfDataSet

    payload.append(["fiftiethStraight", fiftiethPercentilesStraight])
    payload.append(["eightiethStraight", eightiethPercentilesStraight])
    payload.append(["ninetiethStraight", ninetiethPercentilesStraight])
    payload.append(["twentiethStraight", twentiethPercentilesStraight])
    payload.append(["tenthStraight", tenthPercentilesStraight])

    #since 2 outputs needed to be encoded into body of response, separate by string to parse and break into 
    #2 outputs on front-end
    newPayload = payload + ["tickets"] + ticketsByWeekPayload

    response={
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
            "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS
        },
        "body": json.dumps(newPayload),
    }

    redshift.closeConnection()
    return response
