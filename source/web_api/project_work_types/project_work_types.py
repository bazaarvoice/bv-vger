from __future__ import print_function
import os
import json
import psycopg2

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

    # Defining environment variables for accessing private information
    E_AWS_RS_USER = os.environ['AWS_RS_USER']
    E_AWS_RS_PASS = os.environ['AWS_RS_PASS']
    DATABASE_NAME = os.environ['DATABASE_NAME']
    REDSHIFT_PORT = os.environ['REDSHIFT_PORT']
    CLUSTER_ENDPOINT = os.environ['CLUSTER_ENDPOINT']

    # Connect to the Vger Redshift DB
    conn = psycopg2.connect(dbname=DATABASE_NAME, host=CLUSTER_ENDPOINT, port=REDSHIFT_PORT,
                            user=E_AWS_RS_USER, password=E_AWS_RS_PASS)
    cur = conn.cursor()

    selectIDQuery = """
    SELECT team_work_types.work_type,
           team_work_types.issue_type,
           team_jira_issue_types.subtask
    FROM team_work_types
      INNER JOIN team_jira_issue_types
             ON (team_work_types.team_project_id = team_jira_issue_types.team_project_id
            AND team_work_types.issue_type = team_jira_issue_types.issue_type)
    WHERE team_work_types.team_project_id = %s
    """

    excludedIssueTypeQuery = "SELECT excluded_issue_types, include_subtasks FROM team_project WHERE id = %s"
    try:
        cur.execute(selectIDQuery, (projectID,))
        workTypeResults = cur.fetchall()

        cur.execute(excludedIssueTypeQuery, (projectID,))
        fetch_result = cur.fetchone()
        excludedTypeStr = fetch_result[0]
        excludedTypeList = excludedTypeStr.split(",")
        include_subtask = fetch_result[1]

    except Exception as e:
        cur.close()
        conn.close()
        payload = {"message": "Internal Error: {}".format(e)}
        response={
            "statusCode": 500,
            "body": json.dumps(payload)
        }
        return response

    workTypes = {}

    for result in workTypeResults:
        work_type = result[0]
        issue_type = result[1]
        type_subtask = result[2]
        if issue_type not in excludedTypeList:
            # Either all subtask is allowed or the issue type is not a subtask
            if include_subtask or (not type_subtask):
                # If workTypes already has work type defined, append result to list
                if work_type in workTypes:
                    workTypes[work_type].append(issue_type)
                # If workTypes does not have work type defined, create new list with issue type as entry
                else:
                    workTypes[work_type] = [issue_type]

    response={
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
            "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS
        },
        "body": json.dumps(workTypes)
    }

    cur.close()
    conn.close()
    return response
