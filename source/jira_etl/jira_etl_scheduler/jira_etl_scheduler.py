from __future__ import print_function
import psycopg2
import os
import boto3
import json


def handler(event, context):
    lambda_client = boto3.client('lambda')
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

    selectAllTeamsQuery = "SELECT id, name FROM team_project ORDER BY last_issue_change IS NULL DESC, last_issue_change ASC"
    cur.execute(selectAllTeamsQuery)
    rows = cur.fetchall()
    for row in rows:
        teamConfig = {"id": row[0]}
        print ("Starting JIRA ETL for project {}".format(row[1]))
        jsonPayload = json.dumps(teamConfig)

        function_name = "vger-sls-jira-etl-{}".format(ENV)
        lambda_client.invoke(FunctionName=function_name, InvocationType="Event", Payload=jsonPayload)

    print ("jiraScheduler Done")
