import os
import json
import requests
import psycopg2
import urllib
from redshift_connection import RedshiftConnection

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


def handler(event, context):
    # Validate user input
    try:
        # User input
        data = json.loads(event['body'])
        team_name = data['name']

    except:
        payload = {'message': 'Invalid user input'}
        return response_formatter(status_code='404', body=payload)

    # Validate Team name
    try:
        redshift = RedshiftConnection()
        team_exists = redshift.validateTeamName(team_name)
        # If team name already exsits:
        if team_exists:
            payload = {'message': 'Team name already exists'}
            return response_formatter(status_code='400', body=payload)
    except:
        payload = {'message': 'Internal error'}
        return response_formatter(status_code='500', body=payload)
    finally:
        redshift.closeConnection()

    # Create an entry in team table
    try:
        redshift = RedshiftConnection()
        redshift.insertTeam(team_name)
    except Exception as e:
        payload = {'message': 'Failed to insert {} into team {}'.format(team_name, e)}
        return response_formatter(status_code='500', body=payload)
    finally:
        redshift.closeConnection()
        
    # Get id of the newly created team
    try:
        redshift = RedshiftConnection()
        team_id = redshift.getTeamId(team_name)
    except Exception as e:
        payload = {'message': 'Internal error'}
        return response_formatter(status_code='500', body=payload)
    finally:
        redshift.closeConnection()

    payload = {
        'name': team_name,
        'id': team_id
    }
    return response_formatter(status_code='201', body=payload)