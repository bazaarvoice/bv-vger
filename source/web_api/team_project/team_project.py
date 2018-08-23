from __future__ import print_function
import math
import os
import datetime
import json
import urllib
import psycopg2

def handler(event, context):
    # Grab the data passed to the lambda function through the browser URL (API Gateway)
    try:
        teamID = (event.get('pathParameters').get('id'))
    except Exception as e:
        payload = {"message": "Could not get id path parameter"}
        response={
            "statusCode": 400,
            "body": json.dumps(payload)
        }
        return response

    # Defining environment variables for accessing private information
    E_AWS_RS_USER = os.environ['AWS_RS_USER']
    E_AWS_RS_PASS = os.environ['AWS_RS_PASS']
    DATABASE_NAME = os.environ['DATABASE_NAME']
    REDSHIFT_PORT = os.environ['REDSHIFT_PORT']
    CLUSTER_ENDPOINT = os.environ['CLUSTER_ENDPOINT']

    # Connect to the Vger Redshift DB
    conn = psycopg2.connect(dbname=DATABASE_NAME, host=CLUSTER_ENDPOINT, port=REDSHIFT_PORT,
                            user=E_AWS_RS_USER, password=E_AWS_RS_PASS)
    cur = conn.cursor()

    selectIDQuery = "SELECT name, id FROM team WHERE id = %s"

    try:
        cur.execute(selectIDQuery, (teamID,))
        conn.commit()
        results = cur.fetchall()
    except Exception:
        cur.close()
        conn.close()
        payload = {"message": "Internal Error. Could not query database given parameters"}
        response={
            "statusCode": 500,
            "body": json.dumps(payload)
        }
        return response

    if not results:
        cur.close()
        conn.close()
        payload = {"message": "No resource with team ID {} found".format(teamID)}
        response={
            "statusCode": 404,
            "body": json.dumps(payload)
        }
        return response

    query = "SELECT name, id FROM team_project WHERE team_project.team_id = %s"

    try:
        projectName = (event.get('queryStringParameters').get('name'))
    except Exception as e:
        projectName = None

    try:
        if projectName is not None:
            try:
                decodedProject = urllib.unquote(projectName).decode('utf8')
            except Exception as e:
                payload = {"message": "Could not decode given project name parameter: {}".format(projectName)}
                response = {
                    "statusCode": 400,
                    "body": json.dumps(payload)
                }
                return response
            query += " AND name = %s"
            cur.execute(query, (teamID, decodedProject))
        else:
            cur.execute(query, (teamID,))
        conn.commit()
        results = cur.fetchall()
    except Exception:
        cur.close()
        conn.close()
        payload = {"message": "Internal Error. Could not query database given parameters"}
        response={
            "statusCode": 500,
            "body": json.dumps(payload)
        }
        return response

    payload = []
    columns = ['name', 'id']
    for result in results:
        teamConfig = [result[0], result[1]]
        payload.append(dict(zip(columns, teamConfig)))

    response={
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin" : "*", # Required for CORS support to work
            "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS
        },
        "body": json.dumps(payload)
    }

    cur.close()
    conn.close()
    return response