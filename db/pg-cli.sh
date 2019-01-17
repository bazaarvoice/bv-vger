#!/usr/bin/env bash
usage()
{
    echo Usage: `basename $0` "<deployEnv> <ssm_store>" >&2
    echo "" >&2
    echo "Prints to standard output a shell command that defines the Postgres CLI for the given deployment environment." >&2
}

# Get input parameters
while [[ $# -gt 0 ]] ; do
  case $1 in
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

if [[ $# -ne 1 ]] ; then
  usage; exit 1
fi

env=$1
case ${env} in
   prod|qa) ;;
      *) echo "Unknown deployment environment: $env" >&2; exit 1;;   
esac

ssm_store=$2
if [[ -z "$ssm_store" ]] ; then
    echo "no ssm-store was defined" >&2
    exit 1
fi

# CLI environment variables already defined?
if [[ "$PGCMD" && "$PGPASSWORD" ]] ; then
    # Yes, return "do nothing" command
    echo :
else
    # No, get database connection for this environment
    which psql >/dev/null || { echo "Postgres CLI not installed. Please run 'brew install postgres'." >&2; exit 1; }
    binDir=$(dirname $0)

    cluster=$(aws ssm get-parameter --name /${ssm_store}/redshift/${env}/cluster_endpoint --query "Parameter"."Value" --output text)
    port=$(aws ssm get-parameter --name /${ssm_store}/redshift/${env}/port --query "Parameter"."Value" --output text)
    db=$(aws ssm get-parameter --name /${ssm_store}/redshift/${env}/database_name --query "Parameter"."Value" --output text)
    user=$(aws ssm get-parameter --name /${ssm_store}/redshift/${env}/username --query "Parameter"."Value" --output text)
    password=$(aws ssm get-parameter --name /${ssm_store}/redshift/${env}/password --query "Parameter"."Value" --output text --with-decryption)

    # Export CLI environment variable definitions
    # -h ~> hostname
    # -p ~> port
    # -d ~> database name
    # -U ~> username
    # -q ~> quiet
    # -F ~> field separator
    # -v ~> variable set
    # -P ~> specifies printing options
    # -A ~> print all non-empty input lines to standard output
    # -t ~> turn off printing column names and footers
    export PGCMD="'psql -h $cluster -p $port -d $db -U $user -q -F , -v ON_ERROR_STOP=on -P null=null -A -t'"
    export PGPASSWORD=${password}
fi
