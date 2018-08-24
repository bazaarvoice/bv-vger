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
        work_types = data
    except:
        payload = {'message': 'Invalid user input'}
        return response_formatter(status_code='400', body=payload)
    
    # Parse project_id from the URL
    try:
        project_id = (event.get('pathParameters').get('id'))
    except:
        payload = {"message": "Could not get id path parameter"}
        return response_formatter(status_code='400', body=payload)
    
    # Update work types
    try:
        insert_value_list = []
        for key in work_types:
            for issue in work_types[key]:
                insert_value_list.append((project_id, issue, key))
        redshift = RedshiftConnection()
        redshift.updateTeamWorkTypes(project_id, insert_value_list)
    except:
        payload = {'message': 'Internal error'}
        return response_formatter(status_code='500', body=payload)
    finally:
        redshift.closeConnection()

    return response_formatter(status_code='200', body={})