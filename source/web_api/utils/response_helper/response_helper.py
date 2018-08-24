import json


def response_formatter(status_code='400', body=None):
    if body is None:
        body = {'message': 'error'}
    api_response = {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True
        },
        'body': json.dumps(body)
    }
    return api_response
