import json
import boto3
import os
import requests
from redshift_connection import RedshiftConnection

import web_api_constants


def response_formatter(status_code='400', body={'message': 'error'}):
    api_response = {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True
        },
        'body': json.dumps(body)
    }
    return api_response


def handler(event, context):
    # Validate user input
    try:
        # User input
        data = json.loads(event['body'])
        repos = data
    except:
        payload = {'message': 'Invalid user input'}
        return response_formatter(status_code='400', body=payload)

    # Parse project_id from the URL
    try:
        project_id = (event.get('pathParameters').get('id'))
    except:
        payload = {"message": "Could not get id path parameter"}
        return response_formatter(status_code='400', body=payload)

    # Validate repository names
    try:
        ENV = os.environ['ENV']
        ssm_base = os.environ["VGER_SSM_BASE"]
        ssm_client = boto3.client('ssm')

        GIT_API_USER = ssm_client.get_parameter(
            Name='/{ssm_base}/git/{env}/api_user'.format(ssm_base=ssm_base, env=ENV))
        GIT_API_KEY = ssm_client.get_parameter(
            Name='/{ssm_base}/git/{env}/api_key'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)
        for repo in repos:
            GITHUB_API = web_api_constants.GITHUB_API_URL.format(repo)
            r = requests.get(GITHUB_API, headers={'Authorization': 'token %s' % GIT_API_KEY})
            if r.status_code != 200:
                payload = {'message': 'Invalid repository name: \'{}\''.format(repo)}
                return response_formatter(status_code='400', body=payload)
    except:
        # Git API fail
        payload = {'message': 'Service Unavailable'}
        return response_formatter(status_code='503', body=payload)

    try:
        redshift = RedshiftConnection()
        insert_repo_list = []
        for repo in repos:
            insert_repo_list.append((project_id, repo))
        redshift.updateTeamRepos(project_id, insert_repo_list)
    except:
        payload = {'message': 'Internal error'}
        return response_formatter(status_code='500', body=payload)
    finally:
        redshift.closeConnection()

    return response_formatter(status_code='200', body={})
