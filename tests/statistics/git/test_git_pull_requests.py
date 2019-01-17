import boto3
import json
import os
import unittest
from moto import mock_lambda


class GitPullRequestsTest(unittest.TestCase):

    @mock_lambda
    def test_invoke_request_response(self):
        """ Confirm zip package includes all required library and can be invoked successfully """
        ENV = os.environ['ENV']
        ssm_base = os.environ["VGER_SSM_BASE"]
        ssm_client = boto3.client('ssm')

        database_name = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/database_name'.format(ssm_base=ssm_base, env=ENV))
        redshift_port = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/port'.format(ssm_base=ssm_base, env=ENV))
        cluster_endpoint = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/cluster_endpoint'.format(ssm_base=ssm_base, env=ENV))
        e_aws_rs_user = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/username'.format(ssm_base=ssm_base, env=ENV))
        e_aws_rs_pass = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/password'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)

        zip_file_name = 'docker_zipped_git_pull_requests.py.zip'

        # Create mock lambda function from zip file
        conn = boto3.client('lambda', 'us-east-1')
        conn.create_function(
            FunctionName='vger-git-pull-requests',
            Runtime='python2.7',
            # Role='',
            # ENTER ROLE
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
                    'AWS_RS_PASS': e_aws_rs_pass,
                    'AWS_RS_USER': e_aws_rs_user,
                    'DATABASE_NAME': database_name,
                    'CLUSTER_ENDPOINT': cluster_endpoint,
                    'REDSHIFT_PORT': redshift_port
                }
            }
        )

        # Mock API gateway query data
        in_data = {
            'queryStringParameters': {
                'dateSince': '2017-07-07',
                'repoName': 'gops-vger,ffs',
                'days': '90',
                'dateUntil': '2017-10-05'
            },
            'pathParameters': {
                'id': '16'
            },
        }

        result = conn.invoke(FunctionName='vger-git-pull-requests', InvocationType='RequestResponse',
                             Payload=json.dumps(in_data))
        self.assertEqual(result['StatusCode'], 202)

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
