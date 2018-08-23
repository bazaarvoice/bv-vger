from __future__ import print_function
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

def underscore_to_camelcase(text):
    '''
    Converts underscore_delimited_text to camelCase.
    Useful for JSON output
    '''
    return ''.join(word.title() if i else word for i, word in enumerate(text.split('_')))

def handler(event, context):
    # Grab the data passed to the lambda function through the browser URL (API Gateway)
    try:
        project_id = (event.get('pathParameters').get('id'))
    except Exception as e:
        payload = {"message": "Id path parameter not given"}
        return response_formatter(status_code='400', body=payload)

    columns = ["board_name", "board_id", "rolling_time_window_days", "issue_filter", "last_issue_change",
               "include_subtasks", "excluded_issue_types"]

    try:
        redshift = RedshiftConnection()
        results = redshift.getIssueConfiguration(project_id)
    except Exception:
        redshift.closeConnection()
        payload = {"message": "Internal Error"}
        return response_formatter(status_code='500', body=payload)

    if not results:
        payload = {"message": "No resource with project ID {} found".format(project_id)}
        return response_formatter(status_code='404', body=payload)

    project_issue_configs = {}
    for row in results:
        for index, data in enumerate(row):
                project_issue_configs[underscore_to_camelcase(columns[index])] = data

    return response_formatter(status_code='200', body=project_issue_configs)
