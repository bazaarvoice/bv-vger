import json
from redshift_connection import RedshiftConnection

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

def handler(event, context):
    # Validate user input
    try: 
        # User input
        data = json.loads(event['body'])
        work_states = data['workStates']
        default_lead_time_start_state = data['defaultLeadTimeStartState']
        default_lead_time_end_state = data['defaultLeadTimeEndState']
    except:
        payload = {'message': 'Invalid user input'}
        return response_formatter(status_code='400', body=payload)
    
    # Parse project_id from the URL
    try:
        project_id = (event.get('pathParameters').get('id'))
    except:
        payload = {"message": "Could not get id path parameter"}
        return response_formatter(status_code='400', body=payload)
    
    # Update work states
    try:
        status_state_values = [] # Values to insert in team_status_states table
        work_state_values = []    # Vaues to insert in team_work_states table
        seq_number = 0           # Sequence counter for team_work_states table
        
        for work_state in work_states:
            for status in work_state['status']:
                status_state_values.append((int(project_id), str(status), str(work_state['name'])))
            
            work_state_values.append((int(project_id), str(work_state['name']), seq_number))
            seq_number += 1

        redshift = RedshiftConnection()
        redshift.updateTeamStatusStates(project_id, status_state_values)
        redshift.updateTeamWorkStates(project_id, work_state_values)
        redshift.updateDefaultLeadTimeStates(project_id, default_lead_time_start_state, default_lead_time_end_state)
    except:
        payload = {'message': 'Internal error'}
        return response_formatter(status_code='500', body=payload)
    finally:
        redshift.closeConnection()

    return response_formatter(status_code='200', body={})