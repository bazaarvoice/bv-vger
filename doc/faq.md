# Vger Developer FAQ

* [Overall](#overall)
* [Database](#database)
    * [SQL Workbench](#sql-workbench)
    * [Redshift](#redshift)
* [Frontend](#frontend)
    * [AngularJS](*angular)
* [Python](#python)
    * [psycopg2](*psycopg2)
    * [GraphQL](*graphql)
    * [JIRA](*jira)

## Overall

#### What code style should I follow?

For changes made in any already-exist files, I recommend follow the style within that file. For any new files or you cannot tell what's the style in the file, I suggest to follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for `Python` and the [style guide](https://github.com/johnpapa/angular-styleguide/tree/master/a1) for `AngularJS`.

## Database

### SQL Workbench

#### SQL Workbench always asks me to reconnect after a short period. Any solution?

Inside the connection profile in SQL Workbench, choose `connect scripts` and put `SELECT 1` in the `Statement to keep connection alive` field and set `Idle time` to `5m`. Save the profile and should be good for now.

#### I have updated/inserted/deleted something in database and I cannot see the change! Why?

If you are using SQL Workbench to execute your commands, make sure you have commited your changes. To view any changes in SQL Workbench, you need to "Reload data from database" or basically "Reconnect" to view the updated table directly in SQL Workbench.

### Redshift

#### I use `schema.sql` to create table and it does not work! Why?

Redshift does not accept any primary key/reference key. `schema.sql` is just used for reference. If you want to create any tables using the schema, please remove the primary key restriction and any reference.

#### Why the same query in Redshift sometimes can be really slow but sometimes return instantly?

Redshift has a mechanic called [result caching](https://docs.aws.amazon.com/redshift/latest/dg/c_challenges_achieving_high_performance_queries.html#result-caching).

#### I got "Serializable Isolation Violation" in Redshift. What should I do?

To wrap your SQL commands at transaction level using `psycopg2` in `python`, [here](http://www.postgresqltutorial.com/postgresql-python/transaction/) is an example.

## Frontend

#### Unexpected server error! What could happen?

1. The relevant project does not exist anymore, but somehow still appears in UI. Make sure you have removed the obsolete projects.
2. Work state definition is incorrect. This happens a lot and could be duplicated work states/default start state or end date does not match any work states. Try reset work states to board.
3. Check CloudWatch Log and start debugging!


### Angular

#### How do I debug AngularJS?

[Cmd + Option + J] brings up the browser console, then follow the instruction [here](https://www.ng-book.com/p/Debugging-AngularJS/).

#### I tried some library and they do not work. Why?

Make sure the library is in `AngularJS` (aka. Angular 1). For example, we are using [AngularJS Boostrap](https://angular-ui.github.io/bootstrap/) not [Bootstrap 4](https://ng-bootstrap.github.io/#/home).

## Python

#### Lambda timed out/error! What could happen/How to figure out what happen?

1. Check CloudWatch logs/browser console logs. Sometimes Lambda is not deployed properly and will result in missing packages(Vger Helpers or third party packages). If that's the case, first make sure you have include all the folders for the Lambda in `serverless.yml` and pip packages in the corresponding `requirements.txt`. If everything is correct, try to redeploy. If still giving same errors, restart your Docker and deploy again.
2. For Lambdas with API Gateway trigger, the response needs to be return within 30 seconds. If Lambda returns just a little bit more than 30 seconds based on the CloudWatch log, try a full refresh. Same lambda will trigger again, but this time redshift result will be cached so it will be faster.
3. If still not working:
    1. Check if the table in redshift gets locked.
    2. If the lambda uses JIRA/GitHub, check their API statuses.
    3. Profile the lambda and it can give you a detail view of the run time for each statement in the code. If it's just slow generally, try to increase memory size of the Lambda since the compute power of Lambda is based on memory size <sup>[Ref](https://serverless.zone/my-accidental-3-5x-speed-increase-of-aws-lambda-functions-6d95351197f3)</sup>. If you decided to redesign the algorithm, the module [`multiprocessing`](https://docs.python.org/2/library/multiprocessing.html) might be helpful.

### Psycopg2

#### Why use "%s" in SQL query instead of string.format()?

Check [here](http://initd.org/psycopg/docs/usage.html#passing-parameters-to-sql-queries).

#### I have a large amount of SQL to execute and it would be too slow to execute them one by one. Any suggestion?

Check [psycopg2.extras](http://initd.org/psycopg/docs/extras.html#fast-execution-helpers).

### GraphQL

#### How to use GraphQL(GitHub v4 API) in python?

Check `source/git_etl/git_etl_tag.py`<sup>[Ref](https://platform.github.community/t/access-graphql-api-via-python-client/746/7)</sup>.

### JIRA

#### JIRA ETL keeps timed out and unable to update new issue changes. What could happen?

1. If only one specfic project is not working, it might be a bug on JIRA side that they cannot handle such query properly and return the value in time. For example, in `source/jira_etl/jira_transform.py` line 35:

```python
issueList = jira_c.search_issues(query, expand='changelog',
                                 startAt=startAt, maxResults=batchSize, fields='changelog,created,issuetype,resolution')
```
Normally for total 1000(batchSize) issues it will take 50-70 seconds to return, however the following JQL requires more than 370 seconds(while Lambda will time out in 300 seconds), specifically for the following timestamp:
```
(project = 'Conversations Client Satisfaction') AND updatedDate > '2017-12-31 07:25' ORDER BY updatedDate ASC
```
Note that if switch the timestamp to '2017-12-30' or '2018-01-01' would not result in the super long response time. The mechanics behind this mysterious hang is still unclear. Such hang will only appear in some of the large projects, and if it happens, add a restriction like `createdDate > '2016-01-01'` in the project definition JQL might solve the problem without losing too much data. 

3. If still not working, probably try to optimize JIRA ETL or figure out another way to get JIRA issue changes.

