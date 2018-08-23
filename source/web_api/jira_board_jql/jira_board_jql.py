from __future__ import print_function
from response_helper import response_formatter
from lambda_preprocessor import LambdaPreprocessorError
from vger_jira_preprocessor import VgerJiraPreprocessor


def handler(event, context):
    try:
        jira_preprocessor = VgerJiraPreprocessor(event)

        jira_preprocessor.generate_query_parameters(category="board_name")
        jira_preprocessor.validate_jira_board_name()

        issue_filter = jira_preprocessor.get_board_jql()

        payload = {'issue_filter': issue_filter}
        response = response_formatter(status_code='200', body=payload)

    except LambdaPreprocessorError as e:
        response = e.args[0]
    except Exception as e:
        payload = {'message': 'Internal error: {}'.format(e)}
        response = response_formatter(status_code='500', body=payload)

    return response
