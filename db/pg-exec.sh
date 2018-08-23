usage()
{
    echo Usage: `basename $0` "[sqlFile...]"  >&2
    echo "" >&2
    echo "Executes SQL commands from the given files (or, if omitted, from standard input) in the current Postgres CLI environment." >&2
}

while [ $# -gt 0 ] ; do
  case $1 in
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

if [ -z "$PGCMD" -o -z "$PGPASSWORD" ] ; then
    echo "Postgres CLI environment not defined. Please run commands returned by pg-cli.sh." >&2
    exit 1
fi

# Execute all SQL commands in a single transaction
(echo 'BEGIN; '; cat $*; echo 'COMMIT;') | $PGCMD || exit 1
