#!/usr/bin/env bash
usage()
{
    echo Usage: `basename $0` "[-q] [-n] <deployEnv> <repoName...>" >&2
    echo "" >&2
    echo "Deletes data for the given GitHub repos from the given deployment environment." >&2
    echo "Repo data is deleted ONLY for a repo that is no longer referenced by any team project." >&2
    echo "" >&2
    echo "  -q  Quiet mode. If specified, repos that cannot be deleted are silently ignored." >&2
    echo "" >&2
    echo "  -n  Info mode. If specified, just prints actions to be taken without actually doing anything." >&2
}

# Get input parameters
while [[ $# -gt 0 ]] ; do
  case $1 in
    -q) quiet=1;;
    -n) info=1;;
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

if [[ $# -lt 2 ]] ; then
  usage; exit 1
fi

env=$1; shift
case ${env} in
   prod|qa) ;;
      *) echo "Unknown deployment environment: $env" >&2; exit 1;;
esac

repos=$*

# Configure the Postgres CLI for this deployment environment
binDir=$(dirname $0)
eval $(${binDir}/pg-cli.sh ${env})

for repo in ${repos}; do
    projects=$(${binDir}/pg-exec.sh ${env} <<<"select p.name from team_repo r left join team_project p on r.team_project_id=p.id where r.repo_name='${repo}';") || exit 1

    if [[ -z "${projects}" ]] ; then
        echo "Repo=${repo} not found" >&2
        test "$info" || exit 1
        
    elif [[ "${projects}" = "null" ]] ; then
        echo "Deleting ${repo}..." >&2
        test "$info" || ${binDir}/pg-exec.sh ${env} <<EOF
delete from team_repo where repo_name = '${repo}';
delete from git_watermarks where repo_name = '${repo}';
delete from tags where repo = '${repo}';
delete from commits where repo = '${repo}';
delete from pull_requests where repo = '${repo}';
EOF
        if [[ $? -ne 0 ]] ; then
            exit 1;
        fi
        
    elif [[ -z "$quiet" || "$info" ]] ; then
        echo "Can't delete repo=${repo} -- still used by these projects: $(paste -s -d, - <<<"${projects}")" >&2
        test "$info" || exit 1
    fi
done
