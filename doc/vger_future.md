# Future of Vger

* [Short Term](#already-on-jira-board)
* [Long Term](#looking-forward)

The followings are some complicated issues that is worth to look at after you are more familiar with Vger.

1. Backlog Graph Improvement
  - Currently backlog counts all JIRA issues even if the issue is abandoned(resolution = "Won't Fix" etc.), which does not match the definition in throughput graph. A more accurate definition of issues being "Created" and "Completed" is needed in the future.
  - A third line should be added to the graph indicates how much tickets are completed successfully or how much tickets are abandoned.

2. Handle JIRA Status Definition Change
  - If a JIRA board has changed its status definition then Vger will lose all issues before definition change. For example, if a project decides to change their ending state from "Closed" to "Finished", all issues before the status definition change will never reach ending state since they are only "Closed", results in a huge gap in the backlog graph.

## Not on the Board yet

Discuss with other team members before putting them on the board.

1. Handle repo that no longer exists
  - After teams add repos in their project configuration, they could delete the repo in BV GitHub and Vger can no longer access any data for that repo and results in ERROR for GitHub ETL for that specfic repo! For now the ERROR will not crash any thing but it should be properly handled.
  - Another solution is to use "GitHub Team" for project configuration.

2. Toast Message in poped up window is not displayed properly
  - In some cases, user needs to scroll up to see the toast messages, and no users will do that. Should change the toast message location.
  
3. Rewrite JIRA ETL logic
  - Use recursive call to avoid 300 seconds timeout.
  
## Looking Forward

1. Setup proper testing framework and implement unit tests and integration tests. An automated test before deployment would also be nice to have. 

2. Have some proper logging. No more print here and there inside the CloudWatch log, can be done while doing code clean up.

3. Add ORM for database using [SQLAlchemy](https://www.sqlalchemy.org/). It will also help creating unit/integration tests for Vger.

4. Setup actual local development environment of Vger instead of sharing lambdas/database with QA environment.

## Just saying

1. Switch to Python 3. The official EOL date for Python 2.7 is January 1, 2020.

2. Switch to [`python-lambda`](https://github.com/nficano/python-lambda) for deployment instead of using `Serverless` + `serverless-package-python-functions` plugin.

3. Switch to another database to lower cost. Right now Vger is only using less than 1% storage of the smallest dense in Redshift. Switch to a database that charges based on storage size would lower the cost a lot and allow operations like `UPSERT`.
