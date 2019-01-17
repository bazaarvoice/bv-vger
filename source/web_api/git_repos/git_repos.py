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
            "headers": {
                "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
                "Access-Control-Allow-Credentials": True  # Required for cookies, authorization headers with HTTPS
            },
            "body": json.dumps(payload)
        }
        return response

    # Defining environment variables for accessing private information
    ENV = os.environ['ENV']
    ssm_base = os.environ["VGER_SSM_BASE"]
    ssm_client = boto3.client('ssm')

    E_AWS_RS_USER = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/username'.format(ssm_base=ssm_base, env=ENV))
    E_AWS_RS_PASS = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/password'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)
    DATABASE_NAME = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/database_name'.format(ssm_base=ssm_base, env=ENV))
    REDSHIFT_PORT = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/port'.format(ssm_base=ssm_base, env=ENV))
    CLUSTER_ENDPOINT = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/cluster_endpoint'.format(ssm_base=ssm_base, env=ENV))

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
        response = {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
                "Access-Control-Allow-Credentials": True  # Required for cookies, authorization headers with HTTPS
            },
            "body": json.dumps(payload)
        }
        return response

    repos = [result[0] for result in repoResults] if repoResults else []

    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
            "Access-Control-Allow-Credentials": True  # Required for cookies, authorization headers with HTTPS
        },
        "body": json.dumps(repos)
    }

    cur.close()
    conn.close()
    return response
