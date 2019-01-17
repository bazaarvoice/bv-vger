from __future__ import print_function
import math
import os
import boto3
import boto
import psycopg2
from filechunkio import FileChunkIO

import jira_etl_constants


def jiraLoad(data):
    ENV = os.environ['ENV']
    ssm_base = os.environ["VGER_SSM_BASE"]
    ssm_client = boto3.client('ssm')

    # Defining environment variables for accessing private information
    E_AWS_RS_USER = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/username'.format(ssm_base=ssm_base, env=ENV))
    E_AWS_RS_PASS = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/password'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)
    teamConfig = data.get('teamConfig')

    # Constants related to the database on the private facing Redshift database
    BUCKET = jira_etl_constants.S3_ENG_BUCKET
    DATABASE_NAME = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/database_name'.format(ssm_base=ssm_base, env=ENV))
    REDSHIFT_PORT = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/port'.format(ssm_base=ssm_base, env=ENV))
    CLUSTER_ENDPOINT = ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/cluster_endpoint'.format(ssm_base=ssm_base, env=ENV))

    # Since the script is run on lambda, the only file we can write to is /tmp
    PATH = data.get('csvPath')
    splitPath = (PATH.split('/'))
    fileName = splitPath[-1]
    lastIssueChange = long(data.get('lastIssueChange'))

    # Connect to S3 using boto
    c = boto.connect_s3()
    b = c.get_bucket(BUCKET)

    # Find out the size of the file to determine if chunking is needed
    source_size = os.stat(PATH).st_size

    # Skip the repo if there isn't any extracted data
    if source_size != 0:
        print(PATH + " starting load")
        print("lastIssueChange: {}".format(lastIssueChange))
        # Create a multipart upload request
        mp = b.initiate_multipart_upload(os.path.basename(PATH))

        # Use a chunk size of 50 MiB for large files which may exceed this
        # sending the file and uploading in parts helps for large data files
        # and for copying into Redshift
        chunk_size = 52428800
        chunk_count = int(math.ceil(source_size / float(chunk_size)))

        # Send the file parts, using FileChunkIO to create a file-like object
        # that points to a certain byte range within the original file. We
        # set bytes to never exceed the original file size.
        for i in range(chunk_count):
            offset = chunk_size * i
            bytes = min(chunk_size, source_size - offset)
            with FileChunkIO(PATH, 'r', offset=offset, bytes=bytes) as fp:
                mp.upload_part_from_file(fp, part_num=i + 1)

        # Finish the upload
        mp.complete_upload()

        conn = psycopg2.connect(dbname=DATABASE_NAME, host=CLUSTER_ENDPOINT, port=REDSHIFT_PORT,
                                user=E_AWS_RS_USER, password=E_AWS_RS_PASS)
        cur = conn.cursor()
        # Generating the SQL transaction to copy the uploaded file to Redshift
        # Update the lastIssueChange timestamp into team_project
        transactionQuery = "BEGIN TRANSACTION;" \
                           "COPY issue_change from 's3://" + BUCKET + "/" + fileName + \
                           "' credentials 'aws_iam_role=arn:aws:iam::" + jira_etl_constants.AWS_ACCOUNT_NUMBER + ":role/vger-python-lambda" + \
                           "' dateformat 'auto' timeformat 'auto' csv;" \
                           "UPDATE team_project SET last_issue_change='{}' WHERE id={};" \
                           "END TRANSACTION;".format(lastIssueChange, teamConfig.get('id'))
        cur.execute(transactionQuery)
        conn.commit()
        # Delete the file after uploading
        b.delete_key(fileName)
        print(fileName + " loaded")

        cur.close()
        conn.close()

    else:
        # If the file size is 0
        print("No data extracted. Nothing was loaded to Redshift")
