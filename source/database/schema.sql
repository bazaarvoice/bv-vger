-- --------------------------------------------------------------------------------
-- Team project info
-- --------------------------------------------------------------------------------

CREATE TABLE team (
    -- Defines the properties of a team
    id INT IDENTITY(1,1),
    name VARCHAR (60) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE team_project (
    -- Defines the properties of a team project
    id INT IDENTITY(1,1),

    -- Configurable properties
    name VARCHAR (60) NOT NULL,
    team_id INT REFERENCES team (id),
    board_name VARCHAR (60) NOT NULL,
    board_id INT NOT NULL,
    issue_filter VARCHAR (1024),                -- JQL expression that combines with JIRA project key(s) to select the issues for this team project
    default_lead_time_start_state VARCHAR (60),    -- The work state that marks the beginning of the default lead time interval (e.g. Ready)
    default_lead_time_end_state VARCHAR (60),      -- The work state that marks the end of the default lead time interval (e.g. Done)
    last_issue_change BIGINT,                   -- The timestamp of the last issue change event recorded for this project
    rolling_time_window_days INT NOT NULL,         -- The size of the time window (in calendar days) for calculating statistics 
    include_subtasks BOOLEAN,                               -- Boolean value determining whether subtasks should be tracked for the team's project
    excluded_issue_types VARCHAR(60),                           -- Comma delimited list of issue types to exclude for team's project

    PRIMARY KEY (id)
);

-- --------------------------------------------------------------------------------
-- Jira issue info
-- --------------------------------------------------------------------------------

CREATE TABLE team_jira_project (
    -- Defines the JIRA projects that belong to a team project
    team_project_id INT REFERENCES team_project (id),
    jira_project_key VARCHAR (60) NOT NULL,
    PRIMARY KEY (team_project_id, jira_project_key)
);

CREATE TABLE team_work_states (
    -- Defines the project-specific sequence of work states. By default, work states are defined by board column names.
    team_project_id INT REFERENCES team_project (id),
    state_name VARCHAR (60) NOT NULL,
    seq_number INT NOT NULL,
    PRIMARY KEY (team_project_id, state_name)
);

CREATE TABLE team_status_states (
    -- Maps Jira status values to project-specific work states.
    team_project_id INT REFERENCES team_project (id),
    status VARCHAR (60) NOT NULL,
    state_name VARCHAR (60) NOT NULL,
    PRIMARY KEY (team_project_id, status)
);

CREATE TABLE team_work_types (
    -- Maps Jira issue type values to project-specific work types. By default, work types are defined by the standard issue types for associated JIRA projects.
    team_project_id INT REFERENCES team_project (id),
    issue_type VARCHAR (60) NOT NULL,
    work_type VARCHAR (60) NOT NULL,
    PRIMARY KEY (team_project_id, issue_type)
);

CREATE TABLE issue_change (
    -- An issue change event. These events may be recorded only for certain specific fields.
    id INT IDENTITY(1,1),
    team_project_id INT REFERENCES team_project (id) NOT NULL,
    changed BIGINT NOT NULL,
    issue_key VARCHAR (60) NOT NULL,
    field_name VARCHAR (60) NOT NULL,
    prev_value VARCHAR (60),
    new_value VARCHAR (60),
    issue_type VARCHAR (60) NOT NULL,
    resolution VARCHAR (60),
    subtask BOOLEAN,
    PRIMARY KEY (id)
);

-- --------------------------------------------------------------------------------
-- Git repo info
-- --------------------------------------------------------------------------------

CREATE TABLE team_repo (
    -- Defines the repos associated with a team project
    team_project_id INT REFERENCES team_project (id),
    repo_name VARCHAR (60) NOT NULL,
    PRIMARY KEY (team_project_id, repo_name)
);

CREATE TABLE tags (
    -- Defines the tags associated with a repo
    repo VARCHAR (120),
    name VARCHAR (120),
    commit_time TIMESTAMP,
    PRIMARY KEY (repo, name)
);

CREATE TABLE pull_requests (
    -- Defines the pull requests associated with a repo
    repo VARCHAR (120),
    pr_number INT,
    created_at TIMESTAMP,
    closed_at TIMESTAMP,
    num_of_commits INT,
    lines_added INT,
    lines_deleted INT,
    changed_files INT,
    merged_at TIMESTAMP,
    PRIMARY KEY (repo, pr_number)
);

CREATE TABLE git_watermarks (
    -- Store watermarks for git ETL processes
    repo_name VARCHAR(120) NOT NULL,
    table_name VARCHAR(60) NOT NULL,
    watermark_value VARCHAR(120),
    PRIMARY KEY(repo_name, table_name)
);

CREATE TABLE team_jira_issue_types (
    team_project_id INT REFERENCES team_project (id) NOT NULL,
    issue_type VARCHAR (60) NOT NULL,
    subtask BOOLEAN,
    PRIMARY KEY (team_project_id, issue_type)
);

CREATE TABLE team_project_etl (
    team_project_id INT REFERENCES team_project (id) NOT NULL,
    last_etl_run BIGINT
);