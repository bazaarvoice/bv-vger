from __future__ import print_function
import time
import os

# These packages are needed in the ZIP file uploaded into Lambda
import boto3
import psycopg2
import json


def handler (event, context):

    # Defining Redshift connection

    DATABASE_NAME = os.environ['DATABASE_NAME']
    REDSHIFT_PORT = os.environ['REDSHIFT_PORT']
    CLUSTER_ENDPOINT = os.environ['CLUSTER_ENDPOINT']
    E_AWS_RS_USER = os.environ['AWS_RS_USER']
    E_AWS_RS_PASS = os.environ['AWS_RS_PASS']
    ENV = os.environ['ENV']
    conn = psycopg2.connect(dbname=DATABASE_NAME, host=CLUSTER_ENDPOINT, port=REDSHIFT_PORT,
                            user=E_AWS_RS_USER, password=E_AWS_RS_PASS)
    cur = conn.cursor()

    # Get all the repos in the Vger database
    selectRepoQuery = "SELECT DISTINCT repo_name FROM team_repo{}".format("_temp" if event.get("table") else "")
    cur.execute(selectRepoQuery)
    repos = cur.fetchall()
    repoList = []
    for repo in repos:
        repoList.append(repo[0])

    # Depending on the time the scheduler invokes the function, it will perform a different param
    # Convert the time into a datetime object so we can easily grab the hour.
    # NOTE: Using the hour of the event is very hacky and there is definitely a better/easier way to
    # NOTE: Perform this logic
    date = event.get('time')
    time_tuple = time.strptime(date, "%Y-%m-%dT%H:%M:%SZ")  # UTC hour here
    hour = time_tuple[3]

    # Defining Lambda client
    lambda_client = boto3.client('lambda')
    # For each repo in the list of all repos, extract all recent data from it by invoking the extract
    # Lambda function
    for repo in repoList:
        if hour in [0, 4, 8, 12, 16, 20]:
            # NOTE equivalent to 18, 22, 2, 6, 10, 14 in CST. Plus 1 if in DST.
            payload = {"repo": repo, "table": event.get("table") if event.get("table") else "pull_requests"}
            json_payload = json.dumps(payload)
            print("Started ETL for "+repo+" pull request")
            function_name = "vger-sls-git-etl-pr-{}".format(ENV)
            lambda_client.invoke(FunctionName=function_name, InvocationType="Event", Payload=json_payload)
        elif hour in [1, 5, 9, 13, 17, 21]:
            # NOTE equivalent to 19, 23, 3, 7, 11, 15 in CST. Plus 1 if in DST.
            payload = {
                "repo": repo,
                "table": event.get("table") if event.get("table") else "tags",
                "reset": True if hour == 5 else False  # TODO proper logic for reset run
            }
            json_payload = json.dumps(payload)
            print("Started ETL for " + repo + " tag")
            function_name = "vger-sls-git-etl-tag-{}".format(ENV)
            lambda_client.invoke(FunctionName=function_name, InvocationType="Event", Payload=json_payload)
