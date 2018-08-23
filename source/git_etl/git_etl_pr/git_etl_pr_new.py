from __future__ import print_function
import os
import requests
import psycopg2
import json
from psycopg2.extras import execute_values
from iso8601 import parse_date

import git_etl_constants

def handler(event, context):
    repo = event.get("repo")
    table_name = event.get("table")

    # Note Rate limit on GraphQL is different than REST API limit
    MINIMUM_RATE_REMAINING = 100

    # AWS connection init
    connection_detail = {
        'dbname': os.environ['DATABASE_NAME'],
        'host': os.environ["CLUSTER_ENDPOINT"],
        'port': os.environ['REDSHIFT_PORT'],
        'user': os.environ['AWS_RS_USER'],
        'password': os.environ['AWS_RS_PASS']
    }

    conn = psycopg2.connect(**connection_detail)

    E_GIT_API_KEY = os.environ['GIT_API_KEY']

    graphql_url = git_etl_constants.GRAPHQL_URL
    headers = {'Authorization': 'token {}'.format(E_GIT_API_KEY)}
    next_page = True

    watermark_query = "SELECT watermark_value FROM git_watermarks WHERE repo_name = (%s) AND table_name = (%s)"
    with conn:
        with conn.cursor() as cur:
            cur.execute(watermark_query, (repo, table_name))
            watermark_result = cur.fetchone()
            graphql_cursor = watermark_result[0] if watermark_result else ""

    insert_new_pr_query = """
    INSERT INTO {} 
    (repo, pr_number, created_at, closed_at, num_of_commits, lines_added, lines_deleted, changed_files, merged_at) 
    VALUES %s
    """.format(table_name)
    insert_watermarks = "INSERT INTO git_watermarks (repo_name, table_name, watermark_value) VALUES (%s, %s, %s)"

    while next_page:
        query = {
            "query": """
            query {
              repository(owner: %s, name: "%s") {
                pullRequests(first:100, %s) {
                  edges {
                    node {
                      number
                      createdAt
                      closedAt
                      commits { 
                        totalCount
                      }
                      additions
                      deletions
                      changedFiles
                      mergedAt
                    }
                  }
                  pageInfo {
                   endCursor
                   hasNextPage
                  }
                }
              }
              rateLimit {
                remaining
              }
            }
            """ % (git_etl_constants.ORGANIZATION, repo, ' after: "{}"'.format(graphql_cursor) if graphql_cursor else "")}

        r = requests.post(url=graphql_url, json=query, headers=headers)
        if r.ok:
            data = json.loads(r.content).get("data")

            # Check minimum rate
            rate_limit_remaining = data.get('rateLimit').get('remaining')
            if rate_limit_remaining < MINIMUM_RATE_REMAINING:
                print("Reached minimum rate remaining. Stop executing.")
                return

            repository = data.get('repository')
            if repository is None:
                print("Repository {} does not exist any more. Please update project repos.".format("repo"))
                return
            content = repository.get('pullRequests')

            format_prs = []
            for pull_request in content.get('edges'):
                node = pull_request["node"]

                # Do not insert any detail value until the pull request is closed
                pr_number = node.get("number")
                created_at = parse_date(node.get("createdAt")) if node.get("createdAt") else None
                closed_at = parse_date(node.get("closedAt")) if node.get("closedAt") else None
                num_of_commits = node.get("commits").get("totalCount") if node.get("closedAt") else None
                additions = node.get("additions") if node.get("closedAt") else None
                deletions = node.get("deletions") if node.get("closedAt") else None
                changed_files = node.get("changedFiles") if node.get("closedAt") else None
                merged_at = parse_date(node.get("mergedAt")) if node.get("mergedAt") else None
                format_pr = (
                    repo, pr_number, created_at, closed_at, num_of_commits, additions, deletions,
                    changed_files, merged_at
                )
                format_prs.append(format_pr)

            page_info = content.get('pageInfo')
            next_page = page_info.get('hasNextPage')
            graphql_cursor = page_info.get('endCursor')

            with conn:
                with conn.cursor() as cur:
                    if graphql_cursor:
                        cur.execute("DELETE FROM git_watermarks WHERE repo_name = %s AND table_name = %s",
                                    (repo, table_name))
                        cur.execute(insert_watermarks, (repo, table_name, graphql_cursor))

                    execute_values(cur, insert_new_pr_query, format_prs, template=None, page_size=100)

            print("{} new pull requests in repo {} inserted into database".format(len(format_prs), repo))



        else:
            print("Cursor: {}".format(graphql_cursor))
            print("Unexpected error on GraphQL API request: {}".format(str(r.content)))
            return

    # Select all open records:
    open_pr_query = """
    SELECT pr_number FROM {} WHERE closed_at is null AND repo = (%s)
    """.format(table_name)
    with conn:
        with conn.cursor() as cur:
            cur.execute(open_pr_query, (repo,))
            open_prs = cur.fetchall()
            open_prs_count = len(open_prs)
    closed_count = 0

    print("Finished updating new pull requests in repo {}. Start updating all {} open pull requests.".format(
        repo, open_prs_count))

    for idx, open_pr in enumerate(open_prs):
        # Construct url for specific pull request url based on pull number
        query = {
            "query": """
            query {
              repository(owner: %s, name: "%s") {
                pullRequest(number: %s) {
                  number
                  createdAt
                  closedAt
                  additions
                  deletions
                  changedFiles
                  mergedAt
                  commits { 
                    totalCount
                  }
                }
              }
            }
            """ % (git_etl_constants.ORGANIZATION, repo, open_pr[0])
        }
        r = requests.post(url=graphql_url, json=query, headers=headers)
        if r.ok:
            data = json.loads(r.content).get("data")
            repository = data.get('repository')
            if repository is None:
                print("Repository {} does not exist any more. Please update project repos.".format("repo"))
                return
            content = repository.get('pullRequest')
            if content.get("closed_at"):
                closed_count += 1
                with conn:
                    with conn.cursor() as cur:
                        update_pull_requests = """
                        UPDATE {}
                        SET closed_at = (%s),
                        merged_at = (%s),
                        lines_added = (%s),
                        lines_deleted = (%s),
                        num_of_commits = (%s),
                        changed_files = (%s)
                        WHERE repo = (%s) AND pr_number = (%s)
                        """.format(table_name)
                        cur.execute(update_pull_requests,
                                    (content.get("closedAt"),
                                     content.get("mergedAt"),
                                     content.get("additions"),
                                     content.get("deletions"),
                                     content.get("commits").get("totalCount"),
                                     content.get("changedFiles"),
                                     repo,
                                     content.get("number")))

            # If reaching the limit, stop syncing the records and wait for next time
            rate_remaining = int(r.headers['X-RateLimit-Remaining'])
            if rate_remaining < MINIMUM_RATE_REMAINING:
                print("Reached minimum rate remaining. Stop executing.")
                return

        else:
            print("ERROR on API requests while updating open pull requests: {}".format(str(r.content)))
            return

    print("{}/{} open pull requests are closed in repo {} finished.".format(closed_count, open_prs_count, repo))
    return
