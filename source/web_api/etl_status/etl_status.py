from __future__ import print_function
from vger_redshift_preprocessor import VgerRedshiftPreprocessor
from lambda_preprocessor import LambdaPreprocessorError
from response_helper import response_formatter


def handler(event, context):
    try:
        lambda_preprocessor = VgerRedshiftPreprocessor(event)
        lambda_preprocessor.verify_project_id()
        lambda_preprocessor.validate_project_id()

        query = "SELECT last_etl_run FROM team_project_etl WHERE team_project_id = %s"
        cursor = lambda_preprocessor.redshift.getCursor()
        cursor.execute(query, (lambda_preprocessor.param["project_id"],))
        result = cursor.fetchone()
        if result is None or result[0] is None:
            payload = {"last_etl_run": None}
        else:
            payload = {"last_etl_run": int(result[0])}
        response = response_formatter(status_code='200', body=payload)

    except LambdaPreprocessorError as e:
        response = e.args[0]

    except Exception as e:
        payload = {"message": "Internal Error: {}".format(e)}
        response = response_formatter(status_code="500", body=payload)

    return response
