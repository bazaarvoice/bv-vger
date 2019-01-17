import boto3
import os
import json
import requests
from redshift_connection import RedshiftConnection

import web_api_constants

def response_formatter(status_code='400', body={'message': 'error'}):
    api_response = {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin' : '*',
            'Access-Control-Allow-Credentials' : True
        },
        'body': json.dumps(body)
    }
    return api_response

def find_default_start_state(work_states):
    default_state = ''
    first_column = ''
    contains_open = False
    for index, column in enumerate(work_states):
        state = column['name']
        if index == 0:
            first_column = state
        if contains_open:
            # If open status was found in the previous state, return current state
            default_state = state
            return default_state
        contains_open = any(status_name == "Open" for status_name in column["status"])
    # After iterating through all columns and the 'Open' status was never found,
    # use the first column as the default lead time start state
    if not contains_open:
        default_state = first_column

    return default_state


def find_default_end_state(work_states):
    default_state = 'Pseudo End State'
    for column in reversed(work_states):
        state = column['name']
        contains_closed = any(status_name == "Closed" for status_name in column["status"])
        if contains_closed:
            default_state = state
            return default_state

    return default_state


def handler(event, context):
    # parse project_id from the URL
    try:
        project_id = (event.get('pathParameters').get('id'))
    except Exception as e:
        payload = {"message": "Could not get id path parameter"}
        return response_formatter(status_code='400', body=payload)

    pseudo_end_state_name = 'Pseudo End State'
    work_states = []

    # get board id
    try:
        redshift = RedshiftConnection()
        board_id = redshift.getBoardId(project_id)
        print(board_id)
    except:
        payload = {'message': 'Internal error'}
        return response_formatter(status_code='500', body=payload)

    ENV = os.environ['ENV']
    ssm_base = os.environ["VGER_SSM_BASE"]
    ssm_client = boto3.client('ssm')

    JH_USER = ssm_client.get_parameter(Name='/{ssm_base}/jira/{env}/username'.format(ssm_base=ssm_base, env=ENV))
    JH_PASS = ssm_client.get_parameter(Name='/{ssm_base}/jira/{env}/password'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)
    JH_JIRAURL = ssm_client.get_parameter(Name='/{ssm_base}/jira/{env}/host_url'.format(ssm_base=ssm_base, env=ENV))
    # connect to jira api and retrieve board configuration
    try:
        JIRA_BOARD_CONFIG_API = web_api_constants.CONFIG_URL.format(JH_JIRAURL, board_id)
        board_config = requests.get(JIRA_BOARD_CONFIG_API, auth=(JH_USER, JH_PASS)).json()

        # Ignore the first empty backlog column
        first_column = board_config['columnConfig']['columns'][0]
        if first_column.get("name") == "Backlog" and (not first_column.get("statuses")):
            board_config['columnConfig']['columns'].pop(0)

        for column in board_config['columnConfig']['columns']:
            state = {
                "name": str(column["name"]),
                "status": []
            }
            for status in column['statuses']:
                status_object = requests.get(status['self'], auth=(JH_USER, JH_PASS)).json()
                state['status'].append(str(status_object['name']))  # convert unicode string to regular string
            work_states.append(state)
            print(state)

        default_lead_time_start_state = find_default_start_state(work_states)
        default_lead_time_end_state = find_default_end_state(work_states)
    except:
        payload = {'message': 'Service unavailable'}
        return response_formatter(status_code='503', body=payload)

    # Cover edge cases when projects do not use explicitly defined column for closed tickets
    if default_lead_time_end_state == pseudo_end_state_name:
        state = {
            "name": pseudo_end_state_name,
            "status": ["Closed"]
        }
        work_states.append(state)
        print(state)

    payload = {
        "defaultLeadTimeStartState": default_lead_time_start_state,
        "defaultLeadTimeEndState": default_lead_time_end_state,
        "workStates": work_states
    }

    return response_formatter(status_code='200', body=payload)