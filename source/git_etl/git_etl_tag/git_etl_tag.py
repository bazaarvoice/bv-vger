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
    reset = event.get('reset')

    print("Start updating table {} on repo {}".format(table_name, repo))

    # Note Rate limit on GraphQL is counted separated from REST API limit.
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
    next_page = True
    tags = []

    if reset:
        graphql_cursor = ""
    else:
        watermark_query = "SELECT watermark_value FROM git_watermarks WHERE repo_name = (%s) AND table_name = (%s)"
        with conn:
            with conn.cursor() as cur:
                cur.execute(watermark_query, (repo, table_name,))
                watermark_result = cur.fetchone()
                graphql_cursor = watermark_result[0] if watermark_result else ""

    while next_page:
        query = {
            "query": """
            query {
              repository(owner: %s, name: "%s") {
                tags: refs(refPrefix: "refs/tags/", first:100, after: "%s", orderBy: {field: TAG_COMMIT_DATE, direction: ASC}) {
                  edges {
                    node {
                      name
                      target {
                        __typename
                        ... on Tag {
                          target {
                            ... on Commit {
                              author:committer {
                                date
                              }
                            }
                          }
                        }
                        ... on Commit {
                          author:committer {
                            date
                          }
                        }
                      }
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
            """ % (git_etl_constants.ORGANIZATION, repo, graphql_cursor)}
        headers = {'Authorization': 'token {}'.format(E_GIT_API_KEY)}

        r = requests.post(url=graphql_url, json=query, headers=headers)
        if r.ok:
            data = json.loads(r.content).get("data")
            repository = data.get('repository')
            if repository is None:
                print("Repository {} does not exist. Please update project repo setting.".format(repo))
                return
            content = repository.get('tags')

            format_tags = []
            for tag in content.get('edges'):
                node = tag["node"]
                target = node.get("target")
                tag_name = node.get("name")

                # NOTE: Not all commit date is in UTC. Need to parse date.
                if target.get("__typename") == 'Tag':  # Annotated Tags
                    commit_date = parse_date(target.get("target").get("author").get("date"))
                else:  # Lightweight Tags
                    commit_date = parse_date(target.get("author").get("date"))

                format_tag = (repo, tag_name, commit_date)
                format_tags.append(format_tag)
            tags.extend(format_tags)

            page_info = content.get('pageInfo')
            next_page = page_info.get('hasNextPage')
            graphql_cursor = page_info.get('endCursor')

            # Check minimum rate
            rate_limit_remaining = data.get('rateLimit').get('remaining')
            if rate_limit_remaining < MINIMUM_RATE_REMAINING:
                print("Reached minimum rate remaining. Stop executing.")
                return

        else:
            print("Unexpected error on GraphQL API request: {}".format(str(r.content)))
            return

    if not tags:
        print("No tag update is needed on repo {}.".format(repo))
        return
    else:
        print("{} tags will be updated on repo {}.".format(len(tags), repo))

    # NOTE When inserting datetime with psycopg2 directly, it will convert to the 'SQL user timezone' automatically.
    # NOTE Currently on AWS for masteruser timezone is UTC as desired.
    insert_query = 'INSERT INTO {} (repo, name, commit_time) VALUES %s'.format(table_name)
    insert_watermarks = "INSERT INTO git_watermarks (repo_name, table_name, watermark_value) VALUES (%s, %s, %s)"
    with conn:
        with conn.cursor() as cur:
            if reset:
                cur.execute("DELETE FROM {} WHERE repo = %s".format(table_name), (repo,))

            # Update watermark
            cur.execute("DELETE FROM git_watermarks WHERE repo_name = %s AND table_name = %s", (repo, table_name))
            cur.execute(insert_watermarks, (repo, table_name, graphql_cursor))

            execute_values(cur, insert_query, tags, template=None, page_size=100)

    return
