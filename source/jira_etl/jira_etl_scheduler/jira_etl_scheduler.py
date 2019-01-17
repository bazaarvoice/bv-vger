from __future__ import print_function
import psycopg2
import os
import boto3
import json


def handler(event, context):
    ssm_base = os.environ["VGER_SSM_BASE"]
    ENV = os.environ['ENV']

    lambda_client = boto3.client('lambda')
    ssm_client = boto3.client('ssm')
    # Defining Redshift connection
    DATABASE_NAME = ssm_client.get_parameter(
        Name='/{ssm_base}/redshift/{env}/database_name'.format(ssm_base=ssm_base, env=ENV))
    REDSHIFT_PORT = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/port'.format(ssm_base=ssm_base, env=ENV))
    CLUSTER_ENDPOINT = ssm_client.get_parameter(
        Name='/{ssm_base}/redshift/{env}/cluster_endpoint'.format(ssm_base=ssm_base, env=ENV))
    E_AWS_RS_USER = ssm_client.get_parameter(
        Name='/{ssm_base}/redshift/{env}/username'.format(ssm_base=ssm_base, env=ENV))
    E_AWS_RS_PASS = ssm_client.get_parameter(
        Name='/{ssm_base}/redshift/{env}/password'.format(ssm_base=ssm_base, env=ENV))
    conn = psycopg2.connect(dbname=DATABASE_NAME, host=CLUSTER_ENDPOINT, port=REDSHIFT_PORT,
                            user=E_AWS_RS_USER, password=E_AWS_RS_PASS)
    cur = conn.cursor()

    selectAllTeamsQuery = "SELECT id, name FROM team_project ORDER BY last_issue_change IS NULL DESC, last_issue_change ASC"
    cur.execute(selectAllTeamsQuery)
    rows = cur.fetchall()
    for row in rows:
        teamConfig = {"id": row[0]}
        print("Starting JIRA ETL for project {}".format(row[1]))
        jsonPayload = json.dumps(teamConfig)

        function_name = "vger-sls-jira-etl-{}".format(ENV)
        lambda_client.invoke(FunctionName=function_name, InvocationType="Event", Payload=jsonPayload)

    print("jiraScheduler Done")
