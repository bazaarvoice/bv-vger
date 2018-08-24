#seperate script built in-case this functionality is expanded to include its own API endpoint
from jira_throughput_history import *

def buildTicketPayload(jiraResults, weeks):
    changeIndex = 0
    payload = []
    currentWeekTicketsStr = ""

    for week in weeks:
        if week == weeks[0]:
            continue

        while (changeIndex < len(jiraResults) and jiraResults[changeIndex][0] < week):
            if not currentWeekTicketsStr:
                currentWeekTicketsStr += jiraResults[changeIndex][1]
            else:
                currentWeekTicketsStr += "," + jiraResults[changeIndex][1]
            changeIndex+=1
        
        # isoformat implicitly assumes utc time without appending trailing 'Z'
        time = datetime.datetime.fromtimestamp(week, tz=pytz.utc).isoformat()+"Z"
        payload.append([time, currentWeekTicketsStr])
        
        #empty list before filling it with next set of tickets
        currentWeekTicketsStr = ""

    return payload
