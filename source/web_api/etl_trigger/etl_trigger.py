from __future__ import print_function
import os
import json
import boto3
from vger_redshift_preprocessor import VgerRedshiftPreprocessor
from lambda_preprocessor import LambdaPreprocessorError
from response_helper import response_formatter


def handler(event, context):
    try:
        lambda_client = boto3.client('lambda')
        ENV = os.environ['ENV']
        if event.get('queryStringParameters'):
            print("Invoke issue type etl in {}".format(ENV))
            function_name = "vger-sls-jira-issue-type-etl-{}".format(ENV)
            lambda_client.invoke(FunctionName=function_name, InvocationType="Event")
            payload = {"message": "Successfully invoked issue type ETL"}
        else:
            lambda_preprocessor = VgerRedshiftPreprocessor(event)
            lambda_preprocessor.verify_project_id()
            lambda_preprocessor.validate_project_id()
            project_id = lambda_preprocessor.param["project_id"]

            print("Invoke etl for project {} in {}".format(project_id, ENV))
            function_name = "vger-sls-jira-etl-{}".format(ENV)
            json_payload = json.dumps({"id": project_id})
            lambda_client.invoke(FunctionName=function_name, InvocationType="Event", Payload=json_payload)

            payload = {"message": "Successfully invoked JIRA ETL for project {}".format(project_id)}
        response = response_formatter(status_code='200', body=payload)

    except LambdaPreprocessorError as e:
        response = e.args[0]

    except Exception as e:
        payload = {'message': 'Internal error: {}'.format(e)}
        response = response_formatter(status_code='500', body=payload)

    return response
