from __future__ import print_function
import boto3
import os

# These packages are needed in the ZIP file uploaded into Lambda
from jira_load import jiraLoad
import pandas as pd
import jira_etl_lib

def find_issues(initialLoad=True, startAt=0, batchSize=1000, getTotal=False, timestampSince=0, teamConfig={}):
    ENV = os.environ['ENV']
    ssm_base = os.environ["VGER_SSM_BASE"]
    ssm_client = boto3.client('ssm')

    E_JH_USER = ssm_client.get_parameter(Name='/{ssm_base}/jira/{env}/username'.format(ssm_base=ssm_base, env=ENV))
    E_JH_PASS = ssm_client.get_parameter(Name='/{ssm_base}/jira/{env}/password'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)
    E_JH_JIRAURL = ssm_client.get_parameter(Name='/{ssm_base}/jira/{env}/host_url'.format(ssm_base=ssm_base, env=ENV))

    #  JIRA client connection and session
    connection = {}
    connection['username'] = E_JH_USER
    connection['password'] = E_JH_PASS
    connection['domain'] = E_JH_JIRAURL

    try:
        jira_c = jira_etl_lib.get_jira_client(connection)
    except Exception, err:
        print ("Could not connect to jira.")
        print ("Are environment variables JH_USER, JH_PASS and JH_JIRAURL set correctly:")
        print ("JH_JIRAURL: %s" %connection['domain'])
        print ("JH_USER: %s" %connection['username'])
        print ("JH_PASS: %s" %connection['password'])
        return

    query = jira_etl_lib.create_final_issue_jql(teamConfig,timestampSince)

    # Query JIRA using their own native search_issues() function
    # with our JQLs. Only retrieve the changelog and created fields for optimization
    issueList = jira_c.search_issues(query, expand='changelog',
                                        startAt=startAt, maxResults=batchSize, fields='changelog,created,issuetype,resolution')
    print ("Fetched " + str(len(issueList)) + " issues")

    return (issueList)

def getDataFrame(batchSize=1000, startAt=0, timestampSince=0, initialLoad=True, teamConfig={}):
    lastIssueChange = 0
    series = {
        'teamProjectID': {'data': [], 'dtype': 'string'},
        'changed': {'data': [], 'dtype': 'datetime64[ns]'},
        'issueKey': {'data': [], 'dtype': 'string'},
        'fieldName': {'data': [], 'dtype': 'string'},
        'prevValue': {'data': [], 'dtype': 'string'},
        'newValue': {'data': [], 'dtype': 'string'},
        'issueType': {'data': [], 'dtype': 'string'},
        'resolution': {'data': [], 'dtype': 'string'},
        'subTask': {'data': [], 'dtype': 'boolean'}
    }

    issueList = find_issues(initialLoad=initialLoad, startAt=startAt, batchSize=batchSize, timestampSince=timestampSince, teamConfig=teamConfig)

    for issue in issueList:
        item = {
            'teamProjectID': teamConfig.get('id'),
            'changed': None,
            'issueKey': issue.key,
            'fieldName': 'Status',
            'prevValue': None,
            'newValue': None,
            'issueType': None,
            'resolution': None
        }

        issueType = str(issue.fields.issuetype.name)
        subTask = issue.fields.issuetype.subtask
        # The following code handles the issue changes
        for change in issue.changelog.histories:
            statusChange = False
            for items in change.items:
                field = str(items.field)
                changedTimestampEPOCH = jira_etl_lib.date_str_to_epoch_timestamp(change.created)

                if field == 'status' and changedTimestampEPOCH > timestampSince:
                    statusChange = True
                    prevValue = str(items.fromString)
                    newValue = str(items.toString)
                    item['prevValue'] = prevValue
                    item['newValue'] = newValue
                    item['changed'] = changedTimestampEPOCH
                    item['issueType'] = issueType
                    item['subTask'] = subTask
                    item['resolution'] = None
                    # If the issue has a resolution, track it
                    if hasattr(issue.fields, "resolution") and issue.fields.resolution is not None:
                        resolution = str(issue.fields.resolution.name)
                        item['resolution'] = resolution
                    if lastIssueChange == 0 or changedTimestampEPOCH > lastIssueChange:
                        lastIssueChange = changedTimestampEPOCH

            if statusChange:
                for k, v in item.items():
                    series[k]['data'].append(v)

        # The following code handles the issue creation from null -> Open
        createdTimestampEPOCH = jira_etl_lib.date_str_to_epoch_timestamp(issue.fields.created)

        statusChange = False
        if createdTimestampEPOCH > timestampSince:
            statusChange = True
            item['prevValue'] = None
            item['newValue'] = 'Open'
            item['changed'] = createdTimestampEPOCH
            item['issueType'] = issueType
            item['subTask'] = subTask
            item['resolution'] = None
            if lastIssueChange == 0 or createdTimestampEPOCH > lastIssueChange:
                lastIssueChange = createdTimestampEPOCH

        if statusChange:
            for k, v in item.items():
                series[k]['data'].append(v)

    print ('########################################################')
    print ("Fetched " + str(len(series['changed']['data'])) + " issue changes")
    print ('########################################################')

    data = {}
    for k, v in series.items():
        data[k] = pd.Series(v['data'])

    df = pd.DataFrame(data,
                      columns=['teamProjectID', 'changed', 'issueKey', 'fieldName', 'prevValue', 'newValue', 'issueType', 'resolution', 'subTask'])

    return [df, lastIssueChange]

def jiraTransform(data):
    filePart = data.get('filePart')
    batchSize = data.get('batchSize')
    startAt = data.get('startAt')
    teamConfig = data.get('teamConfig')
    timestampSince = data.get('timestampSince')
    initialLoad = data.get('initialLoad')

    # Turn the JIRA data into a dataframe
    results = getDataFrame(batchSize=batchSize, startAt=startAt, timestampSince=timestampSince, initialLoad=initialLoad, teamConfig=teamConfig)
    df = results[0]
    lastIssueChange = results[1]
    # Set the index of each issue in the batch
    df.index += startAt
    # AWS Lambda functions can only write to /tmp/
    csvPath = "/tmp/project_"+str(teamConfig.get("id"))+"_part_"+str(filePart)+"_"+os.environ["ENV"]+".csv"
    print ("Writing data to", csvPath)
    df.to_csv(csvPath, index=False, header=None)
    payload={"teamConfig": teamConfig, "csvPath": csvPath, "lastIssueChange": lastIssueChange}
    # Load the CSV
    jiraLoad(payload)