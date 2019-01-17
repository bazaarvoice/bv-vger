import boto3
import os
import psycopg2


def handler(event, context):
    ENV = os.environ['ENV']
    ssm_base = os.environ["VGER_SSM_BASE"]
    ssm_client = boto3.client('ssm')

    connection_detail = {
        'dbname': ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/database_name'.format(ssm_base=ssm_base, env=ENV)),
        'host': ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/cluster_endpoint'.format(ssm_base=ssm_base, env=ENV)),
        'port': ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/port'.format(ssm_base=ssm_base, env=ENV)),
        'user': ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/username'.format(ssm_base=ssm_base, env=ENV)),
        'password': ssm_client.get_parameter(Name='/{ssm_base}/redshift/{env}/password'.format(ssm_base=ssm_base, env=ENV), WithDecryption=True)
    }

    conn = psycopg2.connect(**connection_detail)

    with conn:
        with conn.cursor() as cur:
            # Insert all issue types that appears in issue_change but does not exists in team_jira_issue_types
            # LEFT JOIN will ignores any duplicated insert
            insert_query = """
            INSERT INTO team_jira_issue_types
            (
              issue_type,
              subtask,
              team_project_id
            )
            SELECT DISTINCT (issue_type),
                   subtask,
                   team_project_id
            FROM issue_change
              LEFT JOIN team_jira_issue_types USING (issue_type, subtask, team_project_id)
            WHERE team_jira_issue_types.team_project_id IS NULL
            """
            cur.execute(insert_query)

    with conn:
        with conn.cursor() as cur:
            project_and_excluded_types_query = "SELECT id, excluded_issue_types, include_subtasks FROM team_project"
            cur.execute(project_and_excluded_types_query)
            results = cur.fetchall()

            for result in results:
                excluded_type_list = result[1].split(",")
                project_id = result[0]
                include_subtasks = result[2]

                issue_type_query = "SELECT issue_type, subtask FROM team_jira_issue_types WHERE team_project_id = %s"
                cur.execute(issue_type_query, (project_id,))
                all_issue_type_list = cur.fetchall()

                existed_issue_type_query = "SELECT issue_type FROM team_work_types WHERE team_project_id = %s"
                cur.execute(existed_issue_type_query, (project_id,))
                existed_issue_type_list = [res[0] for res in cur.fetchall()]
                insert_issue_types = []
                for issue_type_info in all_issue_type_list:
                    issue_type = issue_type_info[0]
                    issue_subtask_type = issue_type_info[1]
                    if (include_subtasks or (not issue_subtask_type)) and (
                            issue_type not in excluded_type_list and issue_type not in existed_issue_type_list):
                        insert_issue_types.append(issue_type)

                for issue_type in insert_issue_types:
                    insert_work_type_query = """
                    INSERT INTO team_work_types (team_project_id, issue_type, work_type)
                    VALUES (%s, %s, %s)
                    """
                    cur.execute(insert_work_type_query, (project_id, issue_type, issue_type))

    return
