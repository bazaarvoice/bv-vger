# Lambda Documentation

* [Overview](lambdas.md#overview)
* [ETL Lambda](lambdas.md#etl-lambda)
  * [ETL Manual Triggering](lambdas.md#etl-manual-triggering)
  * [ETL Logic](lambdas.md#etl-logic)
    * [JIRA ETL](lambdas.md#jira-etl)
    * [JIRA Issue Type ETL](lambdas.md#jira-issue-type-etl)
    * [GitHub Tag ETL](lambdas.md#github-tag-etl)
    * [GitHub Pull Request ETL](lambdas.md#github-pull-request-etl)
* [Web API Lambda](lambdas.md#web-api-lambda)
  * [Template](lambdas.md#web-api-lambda-template)
  * [Helper Functions](lambdas.md#helper-functions-explaination)

## Overview

Vger is using the [Serverless Framework](https://serverless.com/framework/docs/providers/aws/guide/installation/) (v1.23.0) to automate packaging and deployment of all lambda functions. The default lambda packaging can sometimes fail due to the difference in runtime environment (EC2 instance) vs the development environment (Mac OS). To overcome this issue, we are using the [_serverless-package-python-functions_](https://www.npmjs.com/package/serverless-package-python-functions) plugin which will assist in downloading the required libraries from a [Docker image](https://hub.docker.com/r/lambci/lambda/) that closely resembles the EC2 instance environment.

The serverless-package-python-functions plugin is preinstalled to this repo `/source/web_api/node_modules/` and requires no additional setup; specifically, we are using [this](https://github.com/StidZhang/serverless-package-python-functions) personal version because of a bug mentioned [here](https://github.com/ubaniabalogun/serverless-package-python-functions/issues/34).

All lambdas belonging to Vger are named `vger-sls-*-{stage}`, where `{stage}` is either `qa` or `prod`.

## ETL Lambda

ETLs with stage name `prod` load into `git` database, and `qa` load into `vger_dev`. CloudWatch events are only setup for  production environment and there are no scheduled `qa` ETLs running to save unnecessary costs.

### ETL Manual Triggering

To trigger ETL manually, for `jira_etl_scheduler`, `jira_issue_type_etl` and `git_etl_scheduler`, just create an empty test event in AWS Lambda console inside the Lambda function configuration page and hit __Test__ in the top-right corner.

For other ETLs, here's the template for test event:
```
git-etl-pr
{
  "repo": "bv-vger",
  "table": "pull_requests"
}

git-etl-tag
{
  "repo": "bv-vger",
  "table": "tags",
  "reset": False
}

jira-etl
{
  "id": 20
}
```

### ETL Logic

All ETLs are triggered as an "Event" asychronously.

The main restriction for AWS Lambda is the 300 seconds [maximum execution limit](https://docs.aws.amazon.com/lambda/latest/dg/limits.html). For normal ETL run, it won't create any problems since ETL runs every 4 hours and the amount of data gets processed each time can be easily handled within 300 seconds. However, for new projects/new repos, they might already have thousands of issues/pull requests before start using Vger and the amount of data will not be able to finish processing within 300 seconds, and lambda can get cut down at any seconds. Therefore, we introduce watermark so that when Lambda kicks of next time, it will know how much it has already processed.

Another behaviour of ETL lambda that is worth mentioning is [automatic retry](https://docs.aws.amazon.com/lambda/latest/dg/retries-on-errors.html). Automatic retry will reinvoke any asychronous Lambda executions that failed, including those lambdas timed out. It cannot be disabled and need to be taken care of when designing ETLs.

#### JIRA ETL

JIRA ETL scheduler is triggered by CloudWatch event every 4 hours and then invoke JIRA ETL on each individual project and load issue changes into the `issue_change` table.

JIRA ETL uses the field `last_issue_change` in table `team_project` as a watermark, and only looks for issues that gets updated after the watermark. Currently, it will load 1000(or less) issues into database at a time, and if there're still more issues, it will keep loading issues at a time until ETL times out. Usually in one Lambda invocation, it can load 2-5 times until it times out.

Another table `team_project_etl` is introduced and JIRA ETL will check the table to see if any ETL is running right now and if so stop execution.

Compare to other ETLs, JIRA ETL saves new issue changes to a csv file, uploads csv file to S3 and copy the file from S3 to Redshift table rather than directly insert to Redshift.

#### JIRA Issue Type ETL

JIRA issue type ETL is triggered by CloudWatch event every 4 hours and select distinct work types from `issue_change` table and load to `team_jira_issue_type` table and updates `team_work_types` table accordingly. It's relatively short and normally finished within 20 seconds.

#### GitHub Tag ETL

Git ETL scheudler is triggered every hour and it will invoke git-tag-etl on each individual repo every 4 hours based on the schduler invoked time and load data into `tags`.

Tag ETL uses table `git_watermarks` to store the [cursor value of pagination](http://graphql.org/learn/pagination/) in GraphQL as a watermark.

Compare to contents in all other ETLs, git tags is mutable, which means having only cumulative invocation will not guarantee the correctness for tags, so an invocataion with field `"reset": true` is triggered once a day(should be less frequent) which wipes out the database and re-ETL all tags.

Thanks to GraphQL, a complete re-ETL for a repo with 5000 tags can be finished in 45 seconds.

Github GraphQL API has a [rate limit of 5000 points/hr](https://developer.github.com/v4/guides/resource-limitations/), calculated separately from REST API. Current ETL process is far away from reaching the limit and no other projects in BV is sharing the limit now, but it should be in consideration when it scales up.

#### GitHub Pull Request ETL

Git ETL scheudler is triggered every hour and it will invoke git-pr-etl on each individual repo every 4 hours based on the schduler invoked time and load data into `pull_requests`.

Pull requests ETL uses table `git_watermarks` to store the total amount of pull requests that has been created as a watermark, and use it as a reference for [pagination in Github REST API](https://developer.github.com/v3/guides/traversing-with-pagination/). It does not use GraphQL because of the instability, but code can be found in `source/git_etl/git_etl_pr/git_etl_pr_new.py`. 

Compare to Github tag ETL, GitHub pull requests also need to handle [rate limit](https://developer.github.com/v3/rate_limit/) properly. The rate limit right now is 5000 requests/hr shared by the entire BV, so any update to this ETL should handle the rate limit properly.


## Web API Lambda

The lambdas must be carefully organized for Serverless and its plugin to work. Each lambda functions should be contained inside a folder along with requirements.txt listing all dependent libraries for that specific lambda file. Custom helper functions that are not lambdas themselves should be also placed within an individual folder under the utils directory. Any dependent libraries for these helper functions should be listed in the requirements.txt of *those lambda functions that are importing the helper functions*.

Take a look at the following example folder structure and the current serverless.yml located in the web_api directory for reference:

```
web_api/
├── utils
│   ├── helper1
│   │   └── helper1.py
│   └── helper2
│       └── helper2.py
|
├── lambda1
│   ├── lambda1.py
│   └── requirements.txt
├── lambda2
│   ├── lambda2.py
│   └── requirements.txt
│
└── serverless.yml
```


### Web API Lambda Template

Each lambda function must at minimum have one function definition used for invocation handler (entry point) that takes in an event and context as its argument parameter:

```python
# General Web API lambda template
def handler(event, context):
    # main function body

    some_id = event.get('pathParameters').get('id')                   # event can provide pathParameters
    some_query = event.get('queryStringParameters').get('queryParam') # event can provide queryParameters

    # response body
    body = {} 

    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin" : "*",      # Required for CORS support to work
            "Access-Control-Allow-Credentials" : True # Required for cookies, authorization headers with HTTPS
        },
        "body": body
    }

    # all web api lambdas must return a response
    return response

```

Some new lambdas use an updated template such as `git_pr_leadtime.py`:

```python
# New Template
from response_helper import response_formatter
from lambda_preprocessor import LambdaPreprocessorError
from vger_some_preprocessor import VgerSomePreprocessor

def handler(event, context):
    try:
    lambda_preprocessor = VgerSomePreprocessor(event)

    # General validation and generation of project ids if needed
    lambda_preprocessor.verify_project_id()
    lambda_preprocessor.validate_project_id()
    
    # Process parameters
    lambda_preprocessor.generate_query_parameters(some_criteria_here)
    
    # Main function body here
    ...
    payload = {"field_name": value}
    
    # Generate response
    response = response_formatter(status_code='200', body=payload)
    
    # Error handling
    except LambdaPreprocessorError as e:
        response = e.args[0]

    except Exception as e:
        payload = {'message': 'Internal error: {}'.format(e)}
        response = response_formatter(status_code='500', body=payload)

    return response
```

After creating a new lambda, you must run the full serverless deployment to include it to the existing CloudFormation stack. If you deploy the lambda function independent of the stack, you will later run in trouble syncing the function when adding it to cf stack down the road.

### Helper Functions Explaination

__Note__: Many of the helper functions can be and should be reorganized.

`jira_helper` finds jira statuses in-lead-time and post-lead-time.

`jql_parser` helps to generate warning information for invalid JQL in project definition.

`lambda_preprocessor` contains functions that are widely used in all web api Lambdas, such as `verify_id` and `validate_id`. 

`percentile` contains percentile calculation used by both JIRA and GitHub throughput statistics.

`query_parameters` transforms parameters for other calculation/processing.

`redshift_connection` has most of the functions that communicates with Redshift.

`response_helper` generates proper response format with code and return.

`time_interval_calculator` contains most calculation with time, including generating rolling windows and getting work day difference.

`work_type_parser` convert and validate work types. It also provides an invalid resolution list to filter out.
