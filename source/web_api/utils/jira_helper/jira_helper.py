from __future__ import print_function


def get_completion_event_statuses(redshift, project_id):

    cur = redshift.getCursor()

    state_query = """
    SELECT
        s.status,
        w.seq_number >= lead.end_seq_number AS is_complete_status
    FROM
        team_status_states s,
        team_work_states w,
        team_project p,
        (SELECT lp.id as team_project_id, lss.seq_number AS start_seq_number, lse.seq_number AS end_seq_number
         FROM team_project lp, team_work_states lss, team_work_states lse
         WHERE lss.team_project_id = lp.id AND lss.state_name = lp.default_lead_time_start_state
         AND lse.team_project_id = lp.id AND lse.state_name = lp.default_lead_time_end_state) lead
    WHERE
        p.id = (%s)
        AND lead.team_project_id = p.id
        AND w.team_project_id = p.id
        AND w.seq_number >= lead.start_seq_number
        AND s.team_project_id = p.id
        AND s.state_name = w.state_name
    """

    cur.execute(state_query, (project_id,))

    working_status = []
    completed_status = []
    status_results = cur.fetchall()
    for status in status_results:
        if status[1]:
            completed_status.append(status[0])
        else:
            working_status.append(status[0])

    return {"working": working_status, "completed": completed_status}

