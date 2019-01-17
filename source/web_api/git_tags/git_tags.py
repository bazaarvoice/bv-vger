from __future__ import print_function
import boto3
import os
import json
import datetime
import urllib
import psycopg2


def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    returnDate = d + datetime.timedelta(days=days_ahead)
    return returnDate


def handler(event, context):
    # Grab the data passed to the lambda function through the browser URL (API Gateway)
    try:
        projectID = (event.get('pathParameters').get('id'))
    except Exception as e:
        print(e)
        payload = {"message": "Id path parameter not given"}
        response = {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
                "Access-Control-Allow-Credentials": True  # Required for cookies, authorization headers with HTTPS
            },
            "body": json.dumps(payload)
        }
        return response

    # Defining environment variables for accessing private information
    ENV = os.environ['ENV']
    ssm_base = os.environ["VGER_SSM_BASE"]
    ssm_client = boto3.client('ssm')

    E_AWS_RS_USER = ssm_client.get_parameter(Name='/{ssm_base}/redshift/env/username'.format(ssm_base=ssm_base, env=ENV))
    E_AWS_RS_PASS = ssm_client.get_parameter(Name='/{ssm_base}/redshift/env/password'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)
    DATABASE_NAME = ssm_client.get_parameter(Name='/{ssm_base}/redshift/env/database_name'.format(ssm_base=ssm_base, env=ENV))
    REDSHIFT_PORT = ssm_client.get_parameter(Name='/{ssm_base}/redshift/env/port'.format(ssm_base=ssm_base, env=ENV))
    CLUSTER_ENDPOINT = ssm_client.get_parameter(Name='/{ssm_base}/redshift/env/cluster_endpoint'.format(ssm_base=ssm_base, env=ENV))

    # Connect to the Vger Redshift DB
    conn = psycopg2.connect(dbname=DATABASE_NAME, host=CLUSTER_ENDPOINT, port=REDSHIFT_PORT,
                            user=E_AWS_RS_USER, password=E_AWS_RS_PASS)
    cur = conn.cursor()

    selectIDQuery = "SELECT repo_name FROM team_repo WHERE team_project_id = %s"

    try:
        cur.execute(selectIDQuery, (projectID,))
        conn.commit()
        repoResults = cur.fetchall()
    except Exception:
        cur.close()
        conn.close()
        payload = {"message": "Internal Error"}
        response = {
            "statusCode": 500,
            "headers": {
                "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
                "Access-Control-Allow-Credentials": True  # Required for cookies, authorization headers with HTTPS
            },
            "body": json.dumps(payload)
        }
        return response

    if not repoResults:
        cur.close()
        conn.close()
        response = {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
                "Access-Control-Allow-Credentials": True  # Required for cookies, authorization headers with HTTPS
            },
            "body": json.dumps(repoResults)
        }
        return response

    # Grab the query string parameter of dateUntil, dateSince, and offset
    # If omitted dateUntil will be set to current date and time
    # If omitted dateSince will be 90 days before dateUntil
    # These repetitive try/catch blocks are necessary as Lambda throw an exception if the specified
    # parameter is not given.
    try:
        days = int(event.get('queryStringParameters').get('days'))
    except Exception as e:
        # If days not given, set it to default of 90
        days = 90
    try:
        dateUntil = event.get('queryStringParameters').get('dateUntil')
    except Exception as e:
        dateUntil = None
    try:
        dateSince = event.get('queryStringParameters').get('dateSince')
    except Exception as e:
        dateSince = None

    try:
        # Try to decode the given date parameters, if undecodable throw exception
        if (dateUntil != None):
            decodedDate = urllib.unquote(dateUntil).decode('utf8')
            decodedDate = datetime.datetime.strptime(decodedDate, '%Y-%m-%d')
            dateUntil = decodedDate
        if (dateSince != None):
            decodedDate = urllib.unquote(dateSince).decode('utf8')
            decodedDate = datetime.datetime.strptime(decodedDate, '%Y-%m-%d')
            dateSince = decodedDate
    except:
        cur.close()
        conn.close()
        payload = {
            "message": "Could not decode date(s). Ensure the given dates are URL encoded (ex YYYY-MM-DD encodes to YYYY-MM-DD). Given:"}
        if (dateUntil != None):
            payload["message"] += " dateUntil:{}".format(dateUntil)
        if (dateSince != None):
            payload["message"] += " dateSince:{}".format(dateSince)
        response = {
            "statusCode": 400,
            "headers": {
                "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
                "Access-Control-Allow-Credentials": True  # Required for cookies, authorization headers with HTTPS
            },
            "body": json.dumps(payload)
        }
        return response

    today = datetime.datetime.today()
    if (not (dateUntil != None and dateSince != None)):
        if (dateUntil != None):
            # If dateUntil specified later than today
            if (dateUntil > today):
                dateUntil = today
            # If only dateUntil is given, calculate dateSince
            dateSince = dateUntil - datetime.timedelta(days)
        elif (dateSince != None):
            # If only dateSince is given, calculate dateUntil
            dateUntil = dateSince + datetime.timedelta(days)
        else:
            # If neither dateUntil nor dateSince parameters specified,
            # set dateUntil to today,
            # set dateSince to days prior to dateUntil
            dateUntil = today
            dateSince = dateUntil - datetime.timedelta(days)
    else:
        if (dateSince > dateUntil):
            cur.close()
            conn.close()
            payload = {"message": "Given dateSince which is later than dateUntil"}
            response = {
                "statusCode": 400,
                "headers": {
                    "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
                    "Access-Control-Allow-Credentials": True  # Required for cookies, authorization headers with HTTPS
                },
                "body": json.dumps(payload)
            }
            return response

    # Adjust dateSince to earliest Monday within the specified time interval
    dateSince = next_weekday(dateSince, 0)
    # Adjust dateSince one week earlier as also need to count number of issues for week after specified dateSince
    dateSince = dateSince - datetime.timedelta(weeks=1)

    # If dateUntil specified later than today
    if (dateUntil > today):
        dateUntil = today

    # Round dateUntil to previous Sunday Midnight
    dateUntil = dateUntil - datetime.timedelta(days=dateUntil.weekday())

    repos = []
    payload = {}

    for result in repoResults:
        repos.append(result)

    for repo in repos:
        # repo will be a list of 1, thus index the zeroth element
        selectTagsQuery = """
        SELECT commit_time, name FROM tags
        WHERE repo = %s 
        AND commit_time BETWEEN %s AND %s ORDER BY commit_time ASC
        """
        try:
            cur.execute(selectTagsQuery, (repo[0], dateSince, dateUntil))
            conn.commit()
            tagResults = cur.fetchall()
        except Exception:
            cur.close()
            conn.close()
            payload = {"message": "Internal Error"}
            response = {
                "statusCode": 500,
                "headers": {
                    "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
                    "Access-Control-Allow-Credentials": True  # Required for cookies, authorization headers with HTTPS
                },
                "body": json.dumps(payload)
            }
            return response

        payload[repo[0]] = []
        for tag in tagResults:
            payload[repo[0]].append([str(tag[0]), tag[1]])

    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",  # Required for CORS support to work
            "Access-Control-Allow-Credentials": True  # Required for cookies, authorization headers with HTTPS
        },
        "body": json.dumps(payload)
    }

    cur.close()
    conn.close()
    return response
