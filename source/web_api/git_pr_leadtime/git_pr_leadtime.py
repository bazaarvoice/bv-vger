from __future__ import print_function
import pytz
from response_helper import response_formatter
from lambda_preprocessor import LambdaPreprocessorError
from vger_git_pr_preprocessor import VgerGitPRPreprocessor
from time_interval_calculator import TimeIntervalCalculator
from percentile import percentile_calculation


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

        merged_prs, total_weeks_list = lambda_preprocessor.get_merged_pull_requests_timestamp()

        lead_times = [[row[1], TimeIntervalCalculator.workday_diff(row[0], row[1])] for row in merged_prs]

        rolling_weeks_used = []
        fiftieth_percentiles = []
        eightieth_percentiles = []
        ninetieth_percentiles = []

        for index in range(len(total_weeks_list)):
            if index + rolling_window_weeks >= len(total_weeks_list):
                break
            start_date = total_weeks_list[index]
            end_date = total_weeks_list[index + rolling_window_weeks]
            lead_time_subset = filter(lambda x: start_date < x[0] < end_date, lead_times)
            sorted_lead_time_subset = sorted([lead_time[1] for lead_time in lead_time_subset])

            fiftieth_percentiles.append(percentile_calculation(0.5, sorted_lead_time_subset))
            eightieth_percentiles.append(percentile_calculation(0.8, sorted_lead_time_subset))
            ninetieth_percentiles.append(percentile_calculation(0.9, sorted_lead_time_subset))

            week = pytz.utc.localize(total_weeks_list[index + rolling_window_weeks]).isoformat()
            rolling_weeks_used.append(week)

        payload = {
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
