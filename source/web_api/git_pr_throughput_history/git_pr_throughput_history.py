from __future__ import print_function
import pytz
from response_helper import response_formatter
from lambda_preprocessor import LambdaPreprocessorError
from vger_git_pr_preprocessor import VgerGitPRPreprocessor
from percentile import R7PercentileCalculator


def handler(event, context):
    # Verify proejct id from path parameters
    try:
        lambda_preprocessor = VgerGitPRPreprocessor(event)

        # General validation and generation
        lambda_preprocessor.verify_project_id()
        lambda_preprocessor.validate_project_id()

        lambda_preprocessor.generate_query_parameters(category="repo")
        lambda_preprocessor.verify_project_repo()

        lambda_preprocessor.generate_rolling_window_weeks()
        lambda_preprocessor.generate_time_interval_date(trace_back=False)

        pr_counts, total_weeks_list = lambda_preprocessor.get_merged_pull_requests()

        num_merged_pull_requests = [data[0] for data in pr_counts]
        weeks = [pytz.utc.localize(week).isoformat() for week in total_weeks_list[1:]]
        payload = zip(weeks, num_merged_pull_requests)

        #for striaght line percentile calculations
        print(num_merged_pull_requests)
        organizedTotals = num_merged_pull_requests
        organizedTotals = sorted(organizedTotals)
        lengthOfDataSet = len(organizedTotals)

        # Calculate striaght percentile values using the R7 statistical method
        # https://en.wikipedia.org/wiki/Quantile (find: R-7)
        ninetiethPercentilesStraightPoint = R7PercentileCalculator(90.0, organizedTotals, lengthOfDataSet)
        eightiethPercentilesStraightPoint = R7PercentileCalculator(80.0, organizedTotals, lengthOfDataSet)
        fiftiethPercentilesStraightPoint = R7PercentileCalculator(50.0, organizedTotals, lengthOfDataSet)
        twentiethPercentilesStraightPoint = R7PercentileCalculator(20.0, organizedTotals, lengthOfDataSet)
        tenthPercentilesStraightPoint = R7PercentileCalculator(10.0, organizedTotals, lengthOfDataSet)

        #make each "straight percentile" an array of values of equal length to 
        ninetiethPercentilesStraight = [ninetiethPercentilesStraightPoint] * lengthOfDataSet
        eightiethPercentilesStraight = [eightiethPercentilesStraightPoint] * lengthOfDataSet
        fiftiethPercentilesStraight = [fiftiethPercentilesStraightPoint] * lengthOfDataSet
        twentiethPercentilesStraight = [twentiethPercentilesStraightPoint] * lengthOfDataSet
        tenthPercentilesStraight = [tenthPercentilesStraightPoint] * lengthOfDataSet

        payload.append(["fiftiethStraight", fiftiethPercentilesStraight])
        payload.append(["eightiethStraight", eightiethPercentilesStraight])
        payload.append(["ninetiethStraight", ninetiethPercentilesStraight])
        payload.append(["twentiethStraight", twentiethPercentilesStraight])
        payload.append(["tenthStraight", tenthPercentilesStraight])    

        print(payload)

        response = response_formatter(status_code='200', body=payload)

    except LambdaPreprocessorError as e:
        response = e.args[0]

    except Exception as e:
        payload = {'message': 'Internal error: {}'.format(e)}
        response = response_formatter(status_code='500', body=payload)

    # Lambda must return a response
    return response
