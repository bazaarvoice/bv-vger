from __future__ import print_function
import boto3
import os
import json
import psycopg2


def handler(event, context):
    # Grab the data passed to the lambda function through the browser URL (API Gateway)
    try:
        projectID = (event.get('pathParameters').get('id'))
    except Exception as e:
        print(e)
        payload = {"message": "Id path parameter not given"}
        response = {
            "statusCode": 400,
            "body": json.dumps(payload)
        }
        return response

    # Defining environment variables for accessing private information
    ENV = os.environ['ENV']
    ssm_base = os.environ["VGER_SSM_BASE"]
    ssm_client = boto3.client('ssm')

    DATABASE_NAME = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/database_name'.format(ssm_base=ssm_base, env=ENV))
    REDSHIFT_PORT = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/port'.format(ssm_base=ssm_base, env=ENV))
    CLUSTER_ENDPOINT = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/cluster_endpoint'.format(ssm_base=ssm_base, env=ENV))
    E_AWS_RS_USER = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/username'.format(ssm_base=ssm_base, env=ENV))
    E_AWS_RS_PASS = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/password'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)

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
        response = {
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

    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
            "Access-Control-Allow-Credentials": True  # Required for cookies, authorization headers with HTTPS
        },
        "body": json.dumps(workTypes)
    }

    cur.close()
    conn.close()
    return response
