from __future__ import print_function
from __future__ import division
from query_parameters import QueryParameters
from time_interval_calculator import TimeIntervalCalculator
from response_helper import response_formatter
from lambda_preprocessor import LambdaPreprocessor, preprocessor_error_handling
from redshift_connection import RedshiftConnection


class VgerRedshiftPreprocessor(LambdaPreprocessor):
    def __init__(self, event):
        LambdaPreprocessor.__init__(self, event)
        self.redshift = RedshiftConnection()

    @preprocessor_error_handling
    def verify_project_id(self):
        try:
            self.param["project_id"] = self.event.get('pathParameters').get('id')
        except Exception as e:
            payload = {'message': 'Missing Attribute in path parameters: {}'.format(e)}
            return response_formatter(body=payload)

    @preprocessor_error_handling
    def validate_project_id(self):
        try:
            self.redshift.validateProjectID(self.param["project_id"])
        except Exception as e:
            payload = {'message': 'Project with id={0} cannot be found: {1}'.format(self.param["project_id"], e)}
            return response_formatter(status_code='404', body=payload)

    @preprocessor_error_handling
    def generate_query_parameters(self, category="", time=True):
        try:
            query_param = QueryParameters(self.event)
            if time:
                self.param["days"] = query_param.getDays()
                self.param["query_date_until"] = query_param.getDate('dateUntil')
                self.param["query_date_since"] = query_param.getDate('dateSince')
            if category == "repo":
                self.param["repo_list"] = query_param.getRepoName().split(',') if query_param.getRepoName() else []
        except Exception as e:
            payload = {'message': 'Invalid query parameters: {0}'.format(e)}
            return response_formatter(status_code='404', body=payload)

    @preprocessor_error_handling
    def verify_project_repo(self):
        try:
            if self.param.get("repo_list"):
                db_repo = self.redshift.getRepos(self.param["project_id"])
                invalid_repo = [str(repo) for repo in self.param["repo_list"] if str(repo) not in db_repo]
                if invalid_repo:
                    raise ValueError(invalid_repo)
        except Exception as e:
            payload = {'message': 'Invalid repository request: {}'.format(e)}
            return response_formatter(status_code='404', body=payload)

    @preprocessor_error_handling
    def generate_rolling_window_weeks(self):
        try:
            rolling_window_days = self.redshift.selectRollingWindow(self.param["project_id"])
            self.param["rolling_window_weeks"] = rolling_window_days // 7
        except Exception as e:
            payload = {'message': 'Error on calculating rolling window weeks: {}'.format(e)}
            return response_formatter(status_code='500', body=payload)

    @preprocessor_error_handling
    def generate_time_interval_date(self, trace_back=False):
        try:
            time_interval_calculator = TimeIntervalCalculator(
                self.param["query_date_until"], self.param["query_date_since"], self.param["days"])
            # Shift back one week to count PRs made in the week before the following Monday
            time_interval_calculator.decrementDateSinceWeeks(self.param["rolling_window_weeks"] if trace_back else 1)

            self.param["date_since"] = time_interval_calculator.getDateSince()
            self.param["date_until"] = time_interval_calculator.getDateUntil()
        except ValueError as e:
            payload = {'message': 'Invalid date request: {}'.format(e)}
            return response_formatter(status_code='404', body=payload)