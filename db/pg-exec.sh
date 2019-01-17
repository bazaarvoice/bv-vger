#!/usr/bin/env bash
usage()
{
    echo Usage: `basename $0` "<env> [sqlFile...]"  >&2
    echo "" >&2
    echo "Executes SQL commands from the given files (or, if omitted, from standard input) in the current Postgres CLI environment." >&2
}

while [[ $# -gt 0 ]] ; do
  case $1 in
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

env=$1; shift
case ${env} in
   prod|qa) ;;
      *) echo "Unknown deployment environment: $env" >&2; exit 1;;
esac

if [[ -z "$PGCMD" || -z "$PGPASSWORD" ]] ; then
    ./pg-cli.sh ${env}
fi

# Execute all SQL commands in a single transaction
(echo 'BEGIN; '; cat $*; echo 'COMMIT;') | ${PGCMD} || exit 1
