import urllib
import datetime

class QueryParameters(object):
    def __init__(self, event=None):
        if event:
            self.parameters = event.get('queryStringParameters')

    def getDays(self):
        try:
            days = self.parameters.get('days', 90)
        except Exception as e:
            days = 90
        return days

    def getDate(self, inputDate):
        try:
            date = self.parameters.get(inputDate)
        except Exception as e:
            date = None
        try:
            date = self.decodeDateParam(date)
        except ValueError as err:
            raise err
        return date

    def getWorktypes(self):
        try:
            workTypes = self.parameters.get('workTypes')
        except Exception as e:
            workTypes = None
        return workTypes

    def getQuarterDates(self):
        try:
            dates = self.parameters.get('dates')
        except Exception as e:
            dates = None
        return dates

    def getProjectID(self):
        try: 
            projectID = self.parameters.get('id')
        except ValueError as err:
            raise err
        return projectID
    
    def getRepoName(self):
        try: 
            repoName = self.parameters.get('repoName')
        except Exception as err:
            repoName = ''
        return repoName

    def decodeDateParam(self, date):
        if (date != None):
            try:
                decodedDate = urllib.unquote(date).decode('utf8')
                # decodedDate = datetime.datetime.strptime(decodedDate,'%Y-%m-%d')
            except:
                raise ValueError('Could not decode date(s). Ensure the given dates are '
                                 'URL encoded (ex YYYY-MM-DD encodes to YYYY-MM-DD). Given: {}'.format(date))
            return decodedDate

    def getJQL(self):
        try: 
            jql = self.parameters.get('jql')
        except ValueError as err:
            raise err
        return jql