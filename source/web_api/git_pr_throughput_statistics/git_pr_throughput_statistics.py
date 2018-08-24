from __future__ import print_function
from __future__ import division
import pytz
from percentile import percentile_calculation
from response_helper import response_formatter
from lambda_preprocessor import LambdaPreprocessorError
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

        num_closed_pull_requests = [data[0] for data in pr_counts]
        rolling_weeks_used = []

        tenth_percentiles = []
        twentieth_percentiles = []
        fiftieth_percentiles = []
        eightieth_percentiles = []
        ninetieth_percentiles = []

        for index in range(len(total_weeks_list)):
            if index + rolling_window_weeks >= len(total_weeks_list):
                break
            closed_pull_requests_subset = num_closed_pull_requests[index:index+rolling_window_weeks]
            sorted_weeks = sorted(closed_pull_requests_subset)

            tenth_percentiles.append(percentile_calculation(0.1, sorted_weeks))
            twentieth_percentiles.append(percentile_calculation(0.2, sorted_weeks))
            fiftieth_percentiles.append(percentile_calculation(0.5, sorted_weeks))
            eightieth_percentiles.append(percentile_calculation(0.8, sorted_weeks))
            ninetieth_percentiles.append(percentile_calculation(0.9, sorted_weeks))

            week = pytz.utc.localize(total_weeks_list[index+rolling_window_weeks]).isoformat()
            rolling_weeks_used.append(week)

        payload = {
            "tenth": zip(rolling_weeks_used, tenth_percentiles),
            "twentieth": zip(rolling_weeks_used, twentieth_percentiles),
            "fiftieth": zip(rolling_weeks_used, fiftieth_percentiles),
            "eightieth": zip(rolling_weeks_used, eightieth_percentiles),
            "ninetieth": zip(rolling_weeks_used, ninetieth_percentiles)
        }
        response = response_formatter(status_code='200', body=payload)

    except LambdaPreprocessorError as e:
        response = e.args[0]

    except Exception as e:
        payload = {'message': 'Internal error: {}'.format(e)}
        response = response_formatter(status_code='500', body=payload)

    return response
