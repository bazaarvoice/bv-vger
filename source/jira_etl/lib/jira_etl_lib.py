from jira import JIRA
import datetime
import time
from dateutil.parser import parse
import pytz

def get_jira_client(connection):
    url = connection['domain']
    username = connection['username']
    password = connection['password']

    # Use the environment varibles to connect to the JIRA API
    if username is None or password is None or url is None:
        jira  = False
    else:
        jira_options = {'server': url}
        jira = JIRA(jira_options, basic_auth=(username, password))

    return jira

def create_final_issue_jql(teamConfig, dateSinceTimestamp):
    query = "({})".format(teamConfig.get('issue_filter'))

    if dateSinceTimestamp is not None:
        # NOTE: Jira does not allow querying for issues by the second
        print (dateSinceTimestamp)
        dateSince = epoch_timestamp_to_date_str(dateSinceTimestamp)
        print (dateSince)
        query += " AND updatedDate > '{}'".format(dateSince[:-9])

    query += " ORDER BY updatedDate ASC"

    return query

def date_str_to_epoch_timestamp(jira_str):
    # date_str_to_epoch_timestamp: converts a string into epoch timestamp
    # jira API returns string in format iso 8601. ex:'2017-07-03T17:38:01.000-0500'
    # changedDateTime parses string into python datetime object
    changedDateTime = parse(jira_str)
    # startEpoch contains datetime referring beginning of epoch time
    startEpoch = datetime.datetime.fromtimestamp(0, tz=pytz.utc)
    # Find the difference between two dates and return the number of seconds
    changedTimestampEPOCH = changedDateTime - startEpoch
    return long(changedTimestampEPOCH.total_seconds())

def epoch_timestamp_to_date_str(last_change_epoch_timestamp):
    # epoch_timestamp_to_query_str: converts a given epoch timestamp into a string
    # representing a date in JIRA local time zone
    # Use JIRA local time zone = US/Central
    tz = pytz.timezone('US/Central')
    lastChangeDatetime = str(datetime.datetime.fromtimestamp(last_change_epoch_timestamp, tz=tz))
    return lastChangeDatetime