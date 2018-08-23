from __future__ import print_function
import datetime
import json
import pytz
from query_parameters import QueryParameters
from redshift_connection import RedshiftConnection
from work_type_parser import WorkTypeParser
from jira_helper import get_completion_event_statuses
from percentile import R7PercentileCalculator

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
        quarters = queryParameters.getQuarterDates().split(',')
        workTypes = queryParameters.getWorktypes()

        workTypeParser = WorkTypeParser(workTypes,projectID)
        workTypeParser.validateWorkTypes(redshift.getCursor(), redshift.getConn())

    except ValueError as err:
        redshift.closeConnection()
        payload = {"message": "{}".format(err)}
        response={
            "statusCode": 400,
            "body": json.dumps(payload)
        }
        return response

    #dates are sunday 19:00 while missing last 3 zeros to standardize to 1970 date. 
    #This is the same format as the dates stored in the database
    #Therefore, to convert a date using javascripts built in Date(), remove last 3 zeroes and vise versa

    status_list = get_completion_event_statuses(redshift, projectID)

    issueTypesList = workTypeParser.issueTypesList
    invalidResolutionsList = workTypeParser.invalidResolutionsList

    numOfQuarters = len(quarters)

    selectCompletedQuery = """
    SELECT 
    """

    loopCounter = 0
    indexOfQuarterDict = numOfQuarters - 1
    #build all but last part of select string
    while loopCounter < numOfQuarters - 1:
        selectCompletedQuery += " sum(case when (changed < " + str(quarters[indexOfQuarterDict - 1])
        selectCompletedQuery += " AND changed >= " + str(quarters[indexOfQuarterDict]) + ") then 1 else 0 end) q" + str(loopCounter + 1)
        loopCounter += 1
        if loopCounter != numOfQuarters - 1:
            selectCompletedQuery += ","
        indexOfQuarterDict -= 1
        
    selectCompletedQuery += """
    FROM issue_change  
    WHERE team_project_id = %s
    AND new_value IN %s
    AND prev_value IN %s
    AND (%s = 0 OR issue_type IN %s)
    AND (%s = 0 OR resolution NOT IN %s)    
    """
    selectCompletedQuery = cur.mogrify(selectCompletedQuery, 
                                       (projectID,
                                        tuple(status_list["completed"]),
                                        tuple(status_list["working"]),
                                        1 if issueTypesList else 0,
                                        tuple(issueTypesList) if issueTypesList else (None,),
                                        1 if invalidResolutionsList else 0,
                                        tuple(invalidResolutionsList) if invalidResolutionsList else (None,)
                                        )
                                       )
    
    try:
        print(selectCompletedQuery)
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

    changes = changes[0]
    organizedTotals = sorted(changes)
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

    payload = []
    payload.append(["actualData", changes])
    payload.append(["fiftiethStraight", fiftiethPercentilesStraight])
    payload.append(["eightiethStraight", eightiethPercentilesStraight])
    payload.append(["ninetiethStraight", ninetiethPercentilesStraight])
    payload.append(["twentiethStraight", twentiethPercentilesStraight])
    payload.append(["tenthStraight", tenthPercentilesStraight])

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
