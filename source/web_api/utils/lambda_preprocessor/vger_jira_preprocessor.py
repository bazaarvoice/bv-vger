from __future__ import print_function
import os
import re
from urllib import quote

import requests

from lambda_preprocessor import preprocessor_error_handling, LambdaPreprocessor
from response_helper import response_formatter

import web_api_constants

class VgerJiraPreprocessor(LambdaPreprocessor):
    def __init__(self, event):
        LambdaPreprocessor.__init__(self, event)
        self.jira_config = {
            "JIRA_USER": os.environ['JH_USER'],
            "JIRA_PASS": os.environ['JH_PASS'],
            "JIRA_URL": os.environ['JH_JIRAURL']
        }

    @preprocessor_error_handling
    def generate_query_parameters(self, category=""):
        try:
            if category == "board_name":
                self.param["board_name"] = self.event.get("queryStringParameters").get("boardName")
        except Exception as e:
            payload = {'message': 'Invalid query parameters: {0}'.format(e)}
            return response_formatter(status_code='404', body=payload)

    @preprocessor_error_handling
    def validate_jira_board_name(self):
        try:
            if self.param.get("board_name"):
                encoded_board_name = quote(self.param["board_name"], safe='')
                # Jira only allows to query board names that contain a string
                # which may result in multiple values returned
                JIRA_BOARD_API = web_api_constants.BOARD_NAME_URL.format(self.jira_config["JIRA_URL"],
                                                                          encoded_board_name)
                content = requests.get(JIRA_BOARD_API,
                                       auth=(self.jira_config["JIRA_USER"], self.jira_config["JIRA_PASS"])).json()
                boards = content['values']
                if boards:
                    for board in boards:
                        if self.param["board_name"] == board["name"]:
                            self.param["board_id"] = board["id"]
                    if not self.param.get("board_id"):
                        payload = {'message': 'Do you mean one of the following boards: {}'.format(
                            ",".join([board["name"] for board in boards]))}
                        return response_formatter(status_code='400', body=payload)
                else:
                    payload = {'message': 'Can not find board {} in JIRA'.format(self.param["board_name"])}
                    return response_formatter(status_code='404', body=payload)
            else:
                payload = {'message': 'No board name can be found in the query parameters.'}
                return response_formatter(status_code='404', body=payload)
        except Exception as e:
            payload = {'message': 'Internal Error: {}'.format(e)}
            return response_formatter(status_code='500', body=payload)

    def get_board_jql(self):
        JIRA_BOARD_CONFIG_API = web_api_constants.CONFIG_API_URL.format(
            self.jira_config["JIRA_URL"], self.param["board_id"])
        board_config = requests.get(JIRA_BOARD_CONFIG_API,
                                    auth=(self.jira_config["JIRA_USER"], self.jira_config["JIRA_PASS"])).json()

        main_query = board_config['filterConfig']['query']
        sub_query = board_config['subqueryConfig']['subqueries'][0]['query']

        has_order_by = re.search("order by", main_query.lower())
        if has_order_by:
            main_query = main_query[:has_order_by.start()]

        if sub_query:
            issue_filter = '(' + main_query + ') AND (' + sub_query + ')'
        else:
            issue_filter = main_query

        return issue_filter

    def get_board_id(self):
        return self.param["board_id"]
    
