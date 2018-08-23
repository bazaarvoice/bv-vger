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
            "headers": {
                "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
                "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS
            },
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

    selectIDQuery = "SELECT repo_name FROM team_repo WHERE team_project_id = %s"

    try:
        cur.execute(selectIDQuery, (projectID,))
        conn.commit()
        repoResults = cur.fetchall()
    except Exception:
        cur.close()
        conn.close()
        payload = {"message": "Internal Error"}
        response={
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
                "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS
            },
            "body": json.dumps(payload)
        }
        return response

    repos = [result[0] for result in repoResults] if repoResults else []

    response={
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
            "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS
        },
        "body": json.dumps(repos)
    }

    cur.close()
    conn.close()
    return response