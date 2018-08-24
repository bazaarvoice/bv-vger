from __future__ import print_function
import pytz
import numpy
from response_helper import response_formatter
from lambda_preprocessor import LambdaPreprocessor, LambdaPreprocessorError
from vger_git_pr_preprocessor import VgerGitPRPreprocessor


def handler(event, context):
    try:
        lambda_preprocessor = VgerGitPRPreprocessor(event)

        # General validation and generation
        lambda_preprocessor.verify_project_id()
        lambda_preprocessor.validate_project_id()

        lambda_preprocessor.generate_query_parameters(category="repo")
        lambda_preprocessor.verify_project_repo()

        lambda_preprocessor.generate_rolling_window_weeks()
        lambda_preprocessor.generate_time_interval_date(trace_back=True)
        rolling_window_weeks = lambda_preprocessor.param["rolling_window_weeks"]

        pr_counts, total_weeks_list = lambda_preprocessor.get_merged_pull_requests()

        num_merged_pull_requests = [data[0] for data in pr_counts]
        rolling_weeks_used = []

        coefficient_of_variation = []

        # For all the weeks in rollingWeeks perform the throughput calculations moving the window
        # each time
        for index in range(len(total_weeks_list)):
            if index + rolling_window_weeks >= len(total_weeks_list):
                break
            closed_pull_requests_subset = num_merged_pull_requests[index:index + rolling_window_weeks]
            std = numpy.std(closed_pull_requests_subset)
            mean = numpy.mean(closed_pull_requests_subset)
            if mean == 0:
                coefficient_of_variation.append(0)
            else:
                coefficient_of_variation.append(std / mean)

            week = pytz.utc.localize(total_weeks_list[index + rolling_window_weeks]).isoformat()
            rolling_weeks_used.append(week)

        payload = zip(rolling_weeks_used, coefficient_of_variation)
        response = response_formatter(status_code='200', body=payload)

    except LambdaPreprocessorError as e:
        response = e.args[0]

    except Exception as e:
        payload = {'message': 'Internal error: {}'.format(e)}
        response = response_formatter(status_code='500', body=payload)

    return response
