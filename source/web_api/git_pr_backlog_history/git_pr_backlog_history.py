from __future__ import print_function
import pytz
import datetime
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
        lambda_preprocessor.generate_time_interval_date(trace_back=False)

        failed_pr_volumes, total_weeks_list = lambda_preprocessor.get_failed_pull_requests_volume()

        data = {}
        for week in total_weeks_list:
            data[str(week)] = {"Merged": 0, "Rejected": 0}

        start_time = total_weeks_list[0]
        end_time = total_weeks_list[-1]

        for result in failed_pr_volumes:
            pr_number, created_time, closed_time, volume, completed = result

            if created_time < start_time:
                week_start_time = start_time
            else:
                week_start_date = created_time - datetime.timedelta(days=created_time.weekday())
                week_start_time = datetime.datetime(week_start_date.year, week_start_date.month,
                                                    week_start_date.day) + datetime.timedelta(weeks=1)

            if closed_time > end_time:
                week_end_time = end_time
            else:
                week_end_date = closed_time - datetime.timedelta(days=closed_time.weekday())
                week_end_time = datetime.datetime(week_end_date.year, week_end_date.month,
                                                  week_end_date.day) + datetime.timedelta(weeks=1)

            while week_start_time <= week_end_time:
                if completed:
                    data[str(week_start_time)]["Merged"] += volume
                else:
                    data[str(week_start_time)]["Rejected"] += volume
                week_start_time += datetime.timedelta(weeks=1)

        payload = dict()
        payload["Rejected Volume"] = [[pytz.utc.localize(week).isoformat(), data[str(week)]["Rejected"]] for week in
                                      total_weeks_list]

        payload["Merged Volume"] = [[pytz.utc.localize(week).isoformat(), data[str(week)]["Merged"]] for week in
                                    total_weeks_list]

        response = response_formatter(status_code='200', body=payload)

    except LambdaPreprocessorError as e:
        response = e.args[0]
    except Exception as e:
        payload = {'message': 'Internal error: {}'.format(e)}
        response = response_formatter(status_code='500', body=payload)

    return response
