import base64
import boto3
import json
import os
import unittest
from moto import mock_lambda

class GitPullRequestsTest(unittest.TestCase):

    @mock_lambda
    def test_invoke_request_response(self):
        """ Confirm zip package includes all required library and can be invoked successfully """
        
        # Environment Variables
        DATABASE_NAME = os.environ['DATABASE_NAME']
        REDSHIFT_PORT = os.environ['REDSHIFT_PORT']
        CLUSTER_ENDPOINT = os.environ['CLUSTER_ENDPOINT']
        E_AWS_RS_USER = os.environ['AWS_RS_USER']
        E_AWS_RS_PASS = os.environ['AWS_RS_PASS']
        
        zip_file_name = 'docker_zipped_git_pull_requests.py.zip'

        # Create mock lambda function from zip file
        conn = boto3.client('lambda', 'us-east-1')
        conn.create_function(
            FunctionName='vger-git-pull-requests',
            Runtime='python2.7',
            # Role='',
            #ENTER ROLE
            Handler='git_pull_requests.handler',
            Code={
                'ZipFile': open(zip_file_name, 'rb').read(),
            },
            Description='test lambda function',
            Timeout=300,
            MemorySize=1024,
            Publish=True,
            Environment={
                'Variables': {
                    'AWS_RS_PASS': E_AWS_RS_PASS,
                    'AWS_RS_USER': E_AWS_RS_USER,
                    'DATABASE_NAME': DATABASE_NAME,
                    'CLUSTER_ENDPOINT': CLUSTER_ENDPOINT,
                    'REDSHIFT_PORT': REDSHIFT_PORT
                }
            }
        )

        # Mock API gateway query data
        in_data = {
            'queryStringParameters':{  
               'dateSince':'2017-07-07',
               'repoName':'gops-vger,ffs',
               'days':'90',
               'dateUntil':'2017-10-05'
            },
            'pathParameters':{  
               'id':'16'
            },
        }
        
        result = conn.invoke(FunctionName='vger-git-pull-requests', InvocationType='RequestResponse', Payload=json.dumps(in_data))
        self.assertEqual(result['StatusCode'], 202)
        # print('return body: ' + json.loads(base64.b64decode(success_result['LogResult']))['body'])

    def test_function_has_prod_alias(self):
        """ Confirm function has prod alias """
        conn = boto3.client('lambda', 'us-east-1')
        response = conn.get_alias(
            FunctionName='vger-git-pull-requests',
            Name='prod'
        )
        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 200)

    def test_function_has_dev_alias(self):
        """ Confirm function has dev alias """
        conn = boto3.client('lambda', 'us-east-1')
        response = conn.get_alias(
            FunctionName='vger-git-pull-requests',
            Name='dev'
        )
        self.assertEqual(response['ResponseMetadata']['HTTPStatusCode'], 200)

    def test_function_prod_permission(self):
        """ Confirm function has invoke permissions on prod alias """
        conn = boto3.client('lambda', 'us-east-1')
        response = conn.get_policy(
            FunctionName='vger-git-pull-requests',
            Qualifier='prod'
        )
        res = json.loads(response['Policy'])
        self.assertEqual(res['Statement'][0]['Action'], 'lambda:InvokeFunction')

    def test_function_dev_permission(self):
        """ Confirm function has invoke permissions on dev alias """
        conn = boto3.client('lambda', 'us-east-1')
        response = conn.get_policy(
            FunctionName='vger-git-pull-requests',
            Qualifier='dev'
        )
        res = json.loads(response['Policy'])
        self.assertEqual(res['Statement'][0]['Action'], 'lambda:InvokeFunction')
