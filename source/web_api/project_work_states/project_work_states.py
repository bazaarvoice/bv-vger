from __future__ import print_function
import json
from redshift_connection import RedshiftConnection

'''
Returns list of objects with work states and list of status belonging to that work state

'''

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
    # Grab the data passed to the lambda function through the browser URL (API Gateway)
    try:
        project_id = (event.get('pathParameters').get('id'))
    except Exception as e:
        payload = {"message": "Id path parameter not given"}
        return response_formatter(status_code='400', body=payload)

    redshift = RedshiftConnection()
    try:
        redshift.validateProjectID(project_id)
    except Exception:
        redshift.closeConnection()
        payload = {"message": "No resource with project ID {} found".format(project_id)}
        return response_formatter(status_code='404', body=payload)

    try:
        # Fetch list of state names in sequence 
        state_names = redshift.getWorkStates(project_id) # list[(state_name(str)]
    except Exception:
        redshift.closeConnection()
        payload = {"message": "Internal Error"}
        return response_formatter(status_code='500', body=payload)
    
    try: 
        # Fetch default lead time start/end states
        default_lead_time_start_state = redshift.getLeadTimeStartState(project_id)
        default_lead_time_end_state = redshift.getLeadTimeEndState(project_id)
    except Exception:
        redshift.closeConnection()
        payload = {"message": "Internal Error"}
        return response_formatter(status_code='500', body=payload)
        
    work_states = []
    for state in state_names:
        try:
            # Fetch list of status belonging to the state
            status = redshift.statusListOfState(project_id, state[0]) # list[str]
            work_states.append({
                'name': state[0],
                'status': status
            })
        except:
            payload = {"message": "Internal Error"}
            return response_formatter(status_code='500', body=payload)
        
    payload = {}
    payload['defaultLeadTimeStartState'] = default_lead_time_start_state
    payload['defaultLeadTimeEndState'] = default_lead_time_end_state
    payload['workStates'] = work_states

    redshift.closeConnection()
    return response_formatter(status_code='200', body=payload)