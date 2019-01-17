import boto3
import os
import json
import requests
import urllib
import re
from redshift_connection import RedshiftConnection

import web_api_constants

def response_formatter(status_code='400', body={'message': 'error'}):
    api_response = {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin' : '*',
            "Access-Control-Allow-Credentials" : True,
            'Access-Control-Allow-Headers': '*',
            'Content-Type': 'application/json',
            'Access-Control-Expose-Headers': 'X-Amzn-Remapped-Authorization',
            'Access-Control-Allow-Methods' : 'GET, POST, PUT, DELETE, OPTIONS'
        },
        'body': json.dumps(body)
    }
    return api_response

def find_default_start_state(JH_USER, JH_PASS, columns):
    default_state = ''
    first_column = ''
    contains_open = False
    for index, column in enumerate(columns):
        state = column['name']
        if index == 0:
            first_column = state
        if contains_open:
            # If open status was found in the previous state, return current state
            default_state = state
            return default_state
        for status in column['mappedStatuses']:
            status_name = status['name']
            if (status_name == 'Open'):
                contains_open = True
    # After iterating through all columns and the 'Open' status was never found,
    # use the first column as the default lead time start state
    if contains_open == False:
        default_state = first_column

    return default_state

def find_default_end_state(JH_USER, JH_PASS, columns):
    default_state = 'Pseudo End State'
    contains_closed = False
    for column in reversed(columns):
        state = column['name']
        for status in column['mappedStatuses']:
            status_name = status['name']
            if (status_name == 'Closed'):
                contains_closed = True
                break
        if contains_closed == True:
            default_state = state
            return default_state

    return default_state

def handler(event, context):
    ENV = os.environ['ENV']
    ssm_base = os.environ["VGER_SSM_BASE"]
    ssm_client = boto3.client('ssm')

    # Set env variables
    GIT_API_USER = ssm_client.get_parameter(Name='/{ssm_base}/git/{env}/api_user'.format(ssm_base=ssm_base, env=ENV))
    GIT_API_KEY = ssm_client.get_parameter(Name='/{ssm_base}/git/{env}/api_key'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)
    JH_USER = ssm_client.get_parameter(Name='/{ssm_base}/jira/{env}/username'.format(ssm_base=ssm_base, env=ENV))
    JH_PASS = ssm_client.get_parameter(Name='/{ssm_base}/jira/{env}/password'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)
    JH_JIRAURL = ssm_client.get_parameter(Name='/{ssm_base}/jira/{env}/host_url'.format(ssm_base=ssm_base, env=ENV))
    
    # Validate user input
    try: 
        # User input
        data = json.loads(event['body'])
        project_name = data['name']
        board_name = data['issues']['boardName']
        
        # Git repositories are optional input
        if 'repoNames' in data:
            git_repos = data['repoNames']
    except:
        payload = {'message': 'Invalid user input'}
        return response_formatter(status_code='404', body=payload)

    # Parse team_id from the URL
    try:
        team_id = (event.get('pathParameters').get('id'))
    except Exception as e:
        payload = {"message": "Could not get id path parameter"}
        return response_formatter(status_code='400', body=payload)

    # Validate Project name
    try:
        redshift = RedshiftConnection()
        project_exists = redshift.validateProjectName(project_name)
        # If project name already exsits:
        if project_exists:
            payload = {'message': 'Project name already exists'}
            return response_formatter(status_code='400', body=payload)
    except:
        payload = {'message': 'Internal error'}
        return response_formatter(status_code='500', body=payload)
    finally:
        redshift.closeConnection()

    # Validate Jira Board
    try:
        # TODO urllib required?
        encoded_board_name = urllib.quote(board_name, safe='')
        # Jira only allows to query board names that contain a string
        # which may result in multiple values returned
        JIRA_BOARD_API = web_api_constants.BOARD_NAME_URL.format(JH_JIRAURL, encoded_board_name)
        content = requests.get(JIRA_BOARD_API, auth=(JH_USER, JH_PASS)).json()
        boards = content['values']
        for board in boards:
            if board['name'] == board_name:
                board_id = board['id']
        board_id # raise exception if it does not exists
    except:
        payload = {'message': 'Jira Board Name: {} cannot be found'.format(board_name)}
        return response_formatter(status_code='404', body=payload)
    
    # Git repositories are optional input, validate if provided
    if 'repoNames' in data:
        # Validate Git repo
        try:
            for repo in git_repos:
                GITHUB_API = web_api_constants.GITHUB_API_URL.format(repo)
                r = requests.get(GITHUB_API, headers={'Authorization': 'token %s' % GIT_API_KEY})
                if r.status_code != 200:
                    raise Exception
        except:
            payload = {'message': 'Git Repository Names: {} cannot be found'.format([str(i) for i in git_repos])}
            return response_formatter(status_code='404', body=payload)

    # Default values 
    # This is a first version of insertion/creation of team project
    # Update the logic as you add more inputs into the creation form 
    # Or we can keep the initial creation simple and allow user to edit the project later on
    excluded_issue_types = []
    include_subtasks = True
    work_types = None
    rolling_time_window_days = 90
    pseudo_end_state_name = 'Pseudo End State'

    # Get board configurations
    try: 
        JIRA_BOARD_CONFIG_API = web_api_constants.CONFIG_API_URL.format(JH_JIRAURL, board_id)
        board_config = requests.get(JIRA_BOARD_CONFIG_API, auth=(JH_USER, JH_PASS)).json()
        default_start_state = find_default_start_state(JH_USER, JH_PASS, board_config['rapidListConfig']['mappedColumns'])
        default_end_state = find_default_end_state(JH_USER, JH_PASS, board_config['rapidListConfig']['mappedColumns'])
        
        main_query = board_config['filterConfig']['query']
        sub_query = board_config['subqueryConfig']['subqueries'][0]['query']

        has_order_by = re.search("order by", main_query.lower())
        if has_order_by:
            main_query = main_query[:has_order_by.start()]
        
        if sub_query:
            issue_filter = '(' + main_query + ') AND (' + sub_query + ')'
        else:
            issue_filter = main_query
        
    except:
        payload = {'message': 'Service unavailable'}
        return response_formatter(status_code='503', body=payload)

    # Create an entry in team_project table
    try:
        excluded_issue_types_string = ",".join(excluded_issue_types)
        redshift = RedshiftConnection()
        redshift.insertTeamProject(project_name, team_id, board_name, board_id, issue_filter,
                                   default_start_state, default_end_state, rolling_time_window_days, 
                                   include_subtasks, excluded_issue_types_string)
    except Exception as e:
        payload = {'message': 'Failed to insert {} into team_project {}'.format(project_name, e)}
        return response_formatter(status_code='500', body=payload)
    finally:
        redshift.closeConnection()

    # Get project ID
    try:
        redshift = RedshiftConnection()
        project_id = redshift.getProjectId(project_name)
    except Exception as e:
        payload = {'message': 'Failed to get project id with name {}: {}'.format(project_name, e)}
        return response_formatter(status_code='500', body=payload)
    finally:
        redshift.closeConnection()

    # Create entries in team_status_states and team_work_states table
    try:
        redshift = RedshiftConnection()
        status_state_values = []
        work_state_values = []
        seq_number = 0
        for column in board_config['rapidListConfig']['mappedColumns']:
            state = str(column['name']) # convert unicode string to regular string
            work_state_values.append((project_id, state, seq_number))
            seq_number += 1
            for status in column['mappedStatuses']:
                status_name = str(status['name']) # convert unicode string to regular string
                status_state_values.append((project_id, status_name, state))

        # Board requires additional pseudo kanban column to map closed tickets if originally unmapped from all columns
        # Insert pseudo kaban column into team_status_states and team_work_states table
        if (default_end_state ==  pseudo_end_state_name):
            status_state_values.append((project_id, 'Closed', pseudo_end_state_name))
            work_state_values.append((project_id, pseudo_end_state_name, seq_number))
        
        redshift.updateTeamStatusStates(project_id, status_state_values)
        redshift.updateTeamWorkStates(project_id, work_state_values)
    except Exception as e:
        payload = {'message': 'Failed to insert into team_work_states and team_status_states table {}'.format(e)}
        return response_formatter(status_code='500', body=payload)
    finally:
        redshift.closeConnection()

    # Create entries in team_repo
    if 'repoNames' in data:
        try:
            redshift = RedshiftConnection()
            insert_repo_list = []
            for repo in git_repos:
                insert_repo_list.append((project_id, repo))
            redshift.updateTeamRepos(project_id, insert_repo_list)
        except Exception as e:
            payload = {'message': 'Failed to insert into team_repo table {}'.format(e)}
            return response_formatter(status_code='500', body=payload)
        finally:
            redshift.closeConnection()

    payload = {
        'name': project_name,
        'id': project_id
    }
    return response_formatter(status_code='201', body=payload)