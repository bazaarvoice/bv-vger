from __future__ import print_function
import json
import yaml
import os
import requests
import urllib
import jira_etl_lib
import psycopg2
import time
from jira_transform import jiraTransform

import jira_etl_constants

def handler(event, context):
    connection_detail = {
        'dbname': os.environ['DATABASE_NAME'],
        'host': os.environ["CLUSTER_ENDPOINT"],
        'port': os.environ['REDSHIFT_PORT'],
        'user': os.environ['AWS_RS_USER'],
        'password': os.environ['AWS_RS_PASS']
    }

    conn = psycopg2.connect(**connection_detail)
    start_time = time.time()

    columns = ["id", "name", "issue_filter", "last_issue_change"]

    getTeamConfigQuery = "SELECT {} FROM team_project WHERE id = %s".format(','.join(columns))

    with conn:
        with conn.cursor() as cur:
            cur.execute(getTeamConfigQuery, (event["id"],))
            result = cur.fetchone()
            teamConfig = {
                columns[0]: result[0],
                columns[1]: result[1],
                columns[2]: result[2],
                columns[3]: result[3]
            }

    getLastETLQuery = "SELECT last_etl_run FROM team_project_etl WHERE team_project_id = %s"

    with conn:
        with conn.cursor() as cur:
            cur.execute(getLastETLQuery, (event["id"],))
            result = cur.fetchone()

    with conn:
        with conn.cursor() as cur:
            if result is None:
                updateLastETLRunQuery = "INSERT INTO team_project_etl (last_etl_run, team_project_id) VALUES (%s, %s)"
            elif (not result[0]) or (start_time - result[0] > 300):
                updateLastETLRunQuery = "UPDATE team_project_etl SET last_etl_run = %s WHERE team_project_id = %s"
            else:
                print("ERROR: ETL for project {} is already running at time {}".format(
                    teamConfig.get("name"), result[0]
                ))
                return

            cur.execute(updateLastETLRunQuery, (int(start_time), event["id"]))

    E_JH_USER = os.environ["JH_USER"]
    E_JH_PASS = os.environ["JH_PASS"]

    # Write file headers for the CSV file
    base_header = ['changedTimestamp', 'issueKey', 'fieldName', 'prevValue', 'newValue']
    base_columns = ['changedTimestamp', 'issueKey', 'fieldName', 'prevValue', 'newValue']
    # Concatenate the headers and column names together with id
    headers = ([teamConfig['id']] + base_header)
    columns = ([teamConfig['id']] + base_columns)

    fileName = teamConfig['name']
    print ("Fetching issues for {}".format(teamConfig['name']))

    if teamConfig['last_issue_change']:
        initialLoad = False
        timestampSince = teamConfig['last_issue_change']
    else:
        initialLoad = True
        timestampSince = 0

    # Define the value for the first part of the CSVs to be created
    filePart = 1
    # Store the max issues and fire off lambdas while incrementing the
    # starting index with the batch size to return all issues
    startAt = 0
    batchSize = 1000

    # # Query for the total number of issues for this JQL
    # # https://developer.atlassian.com/jiradev/jira-apis/jira-rest-apis/jira-rest-api-tutorials/jira-rest-api-example-query-issues
    query = jira_etl_lib.create_final_issue_jql(teamConfig,timestampSince)
    print (query)

    queryString = urllib.quote(query, safe='')
    queryString += '&fields=*none&maxResults=0'
    pageURL = jira_etl_constants.JQL_SEARCH_URL.format(queryString)

    # Should not use jira client interface here
    # Jira client returns entire issue list although
    # we are only concerned about meta data containing total number of issues here
    r = requests.get(pageURL, auth=(E_JH_USER, E_JH_PASS))

    if int(r.status_code) == 200:
        content = r.json()
        dump = json.dumps(content)
        yamlObj = yaml.safe_load(dump)
        totalIssues = yamlObj['total']
    else:
        print ("ERROR: Status code: {} returned".format(int(r.status_code)))
        return

    print ("Total issues: {}".format(totalIssues))

    if (totalIssues == 0):
        print ("No new issues for {}".format(teamConfig['name']))
    else:
        while startAt < totalIssues:
            print ("Starting batch loading! Part: " + str(filePart))
            print ("starting at {}".format(startAt))
            print ("batch size of {}".format(batchSize))
            # Create the payload for the lambda function
            payload = {"columns": columns, "headers": headers, "fileName": fileName, "filePart": filePart, "batchSize": batchSize, "startAt": startAt, "teamConfig": teamConfig, "initialLoad": initialLoad, "timestampSince": timestampSince}

            jiraTransform(payload)

            # Increment the starting index
            startAt += batchSize

            # Increment the file part
            filePart += 1

    # Finished within 5 min
    with conn:
        with conn.cursor() as cur:
            resetLastETLRunQuery = "UPDATE team_project_etl SET last_etl_run = NULL WHERE team_project_id = %s"
            cur.execute(resetLastETLRunQuery, (event["id"],))
    print("ETL for project {} finished in {} seconds".format(teamConfig.get("name"), time.time() - start_time))
    return
