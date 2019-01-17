#!/usr/bin/env bash
usage()
{
  echo Usage: `basename $0` "[-n] <deployEnv> [teamName] [projectName]" >&2
    echo "" >&2
    echo "Deletes the given team project from the given deployment environment. The project to delete" >&2
    echo "is defined by the given team name and project name. If either value is omitted, you must" >&2
    echo "enter a value interactively." >&2
    echo "" >&2
    echo "  -n  Info mode. If specified, just prints actions to be taken without actually doing anything." >&2
}

# Get input parameters
while [[ $# -gt 0 ]] ; do
  case $1 in
    -n) info=1;;
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

if [[ $# -lt 1 ]] ; then
  usage; exit 1
fi

env=$1; shift
case ${env} in
   prod|qa) ;;
      *) echo "Unknown deployment environment: $env" >&2; exit 1;;   
esac

team=$1; shift
if [[ -z "$team" ]] ; then
    read -p "Team name: " team
fi

project="$*"
if [[ -z "$project" ]] ; then
    read -p "Project name: " project
fi

# Configure the Postgres CLI for this deployment environment
binDir=$(dirname $0)
eval $(${binDir}/pg-cli.sh ${env})

# Get team id
teamId=$(${binDir}/pg-exec.sh <<<"select id from team where name = '${team}';") || exit 1
if [[ -z "$teamId" ]] ; then
    echo "Team='${team}' not found" >&2
    exit 1
fi

# Get project id
projectId=$(${binDir}/pg-exec.sh <<<"select id from team_project where team_id = ${teamId} and name = '${project}';") || exit 1
if [[ -z "$projectId" ]] ; then
    echo "Project='${project}' not found" >&2
    exit 1
fi

# Get project repos
repos=$(${binDir}/pg-exec.sh ${env} <<<"select repo_name from team_repo where team_project_id = ${projectId};") || exit 1

echo "Deleting project='${project}' for team='${team}'..." >&2
if [[ -z "$info" ]] ; then
    ${binDir}/pg-exec.sh ${env} <<EOF
delete from team_jira_project where team_project_id = ${projectId};
delete from team_work_types where team_project_id = ${projectId};
delete from team_status_states where team_project_id = ${projectId};
delete from team_work_states where team_project_id = ${projectId};
delete from issue_change where team_project_id = ${projectId};
delete from team_project where id = ${projectId};
EOF
    if [[ $? -ne 0 ]] ; then
        exit 1;
    fi
fi

# Delete data for any repo associated only with the deleted project
if [[ "$repos" ]] ; then
    ${binDir}/delete-repo.sh -q ${info:+-n} ${env} ${repos}
fi

