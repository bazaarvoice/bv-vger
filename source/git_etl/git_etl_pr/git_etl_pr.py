from __future__ import division
import os
import requests
import psycopg2
import json

import git_etl_constants

def handler(event, context):
    # AWS connection init
    connection_detail = {
        'dbname': os.environ['DATABASE_NAME'],
        'host': os.environ["CLUSTER_ENDPOINT"],
        'port': os.environ['REDSHIFT_PORT'],
        'user': os.environ['AWS_RS_USER'],
        'password': os.environ['AWS_RS_PASS']
    }

    conn = psycopg2.connect(**connection_detail)

    # Git key
    E_GIT_API_USER = os.environ['GIT_API_USER']
    E_GIT_API_KEY = os.environ['GIT_API_KEY']

    MINIMUM_RATE_REMAINING = 500
    PAGE_SIZE = 100

    repo_name = event.get('repo')
    table_name = event.get('table')

    # Get watermark
    watermark_query = "SELECT watermark_value FROM git_watermarks WHERE repo_name = (%s) AND table_name = (%s)"
    with conn:
        with conn.cursor() as cur:
            cur.execute(watermark_query, (repo_name, table_name, ))
            watermark_result = cur.fetchone()
            objects_added = int(watermark_result[0]) if watermark_result else 0

    # Init URLs
    git_url = git_etl_constants.GIT_URL
    detail_pr_url = git_url + repo_name + "/pulls/"

    # Start from the page depends on watermark, ascending order based on created_at timestamp
    page_watermark = objects_added // PAGE_SIZE + 1
    general_pr_url = git_url + repo_name + "/pulls?state=all&direction=asc" + "&per_page=" + str(PAGE_SIZE)
    page_url = general_pr_url + "&page={}".format(page_watermark)

    # Init watermark update query
    update_watermarks = """
    UPDATE git_watermarks SET watermark_value = (%s)
    WHERE repo_name = (%s) AND table_name = (%s);
    """

    with conn:
        with conn.cursor() as cur:
            # Init watermark into database
            if watermark_result is None:
                init_watermarks = """
                INSERT INTO git_watermarks (repo_name, table_name, watermark_value) VALUES (%s, %s, %s);
                """
                cur.execute(init_watermarks, (repo_name, table_name, 0,))
                conn.commit()

            # Init new table if not exists
            create_new_table_query = """
            CREATE TABLE IF NOT EXISTS {}(LIKE pull_requests);
            """.format(table_name)
            cur.execute(create_new_table_query)
            conn.commit()

    inpage_watermark = objects_added % PAGE_SIZE  # 0 index

    print("Start getting new records on repo {}".format(repo_name))
    # Insert new records
    r = requests.get(page_url, auth=(E_GIT_API_USER, E_GIT_API_KEY))
    if r.ok:
        contents = json.loads(r.content)
        new_records = contents[inpage_watermark:] if contents else None
        while new_records:
            with conn:
                with conn.cursor() as cur:
                    # Loop on current page
                    for content in new_records:
                        # Insert into database and commit along with watermarks update
                        insert_query = """
                        INSERT INTO {}
                        (repo, pr_number, created_at)
                        VALUES
                        (%s, %s, %s)
                        """.format(table_name)
                        cur.execute(insert_query, (repo_name, content.get("number"), content.get("created_at"),))

                    # Update watermark whenever one page is finished to avoid connection drops or lambda timeout
                    new_watermark = objects_added + len(new_records)
                    cur.execute(update_watermarks,
                                # Update watermark at the end of each page
                                (new_watermark, repo_name, table_name,))
                    conn.commit()
                    objects_added = new_watermark

            # Check API rate limit and stop executing if reached the limit
            rate_remaining = int(r.headers['X-RateLimit-Remaining'])
            print("New watermark has been set to {} for repo {}.".format(objects_added, repo_name))
            if rate_remaining < MINIMUM_RATE_REMAINING:
                print("Reached minimum rate remaining. Stop executing.")
                return

            # Get next page information
            pagination = r.links
            next_page = pagination.get("next")
            if next_page:
                page_url = next_page["url"]
                r = requests.get(page_url, auth=(E_GIT_API_USER, E_GIT_API_KEY))
                if r.ok:
                    new_records = json.loads(r.content)
                else:
                    print("ERROR while getting information of next page: {}".format(str(r.content)))
                    return
            else:
                new_records = None
    else:
        print("ERROR while getting information of the page with watermark: {}".format(str(r.content)))
        return

    # Select all open records:
    open_pr_query = """
    SELECT pr_number FROM {} WHERE closed_at is null AND repo = (%s)
    """.format(table_name)
    with conn:
        with conn.cursor() as cur:
            cur.execute(open_pr_query, (repo_name,))
            open_prs = cur.fetchall()
            open_prs_count = len(open_prs)

    print("Finished getting new records on repo {}. Start updating all {} open pull requests.".format(
        repo_name, open_prs_count))
    # Update open records if they are closed
    for idx, open_pr in enumerate(open_prs):
        # Construct url for specific pull request url based on pull number
        open_pr_url = detail_pr_url + str(open_pr[0])
        r = requests.get(open_pr_url, auth=(E_GIT_API_USER, E_GIT_API_KEY))
        if r.ok:
            with conn:
                with conn.cursor() as cur:
                    content = json.loads(r.content)
                    if content.get("closed_at"):
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
                                    (content.get("closed_at"), content.get("merged_at"),
                                     content.get("additions"), content.get("deletions"),
                                     content.get("commits"), content.get("changed_files"),
                                     repo_name, open_pr[0],))
                        conn.commit()

            # If reaching the limit, stop syncing the records and wait for next time
            rate_remaining = int(r.headers['X-RateLimit-Remaining'])
            if rate_remaining < MINIMUM_RATE_REMAINING:
                print("Reached minimum rate remaining. Stop executing.")
                return

            # Logging purpose
            if (idx + 1) % (PAGE_SIZE // 2) == 0:
                print("{}/{} open pull requests update on repo {} finished.".format(idx+1, open_prs_count, repo_name))

        else:
            print("ERROR on API requests while updating open pull requests: {}".format(str(r.content)))
            return

    print("All {} pull requests update on repo {} finished.".format(open_prs_count, repo_name))
    return
