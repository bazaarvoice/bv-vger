usage()
{
    echo Usage: `basename $0` "deployEnv" >&2
    echo "" >&2
    echo "Prints to standard output a shell command that defines the Postgres CLI for the given deployment environment." >&2
}

dbParams()
{
$binDir/../deploy/env-config.sh -p $1 |
tr -d ":'" |
awk '
    $1 == "AWS_RS_PASS" { password = $2; next; }
    $1 == "AWS_RS_USER" { user = $2; next; }
    $1 == "CLUSTER_ENDPOINT" { cluster = $2; next; }
    $1 == "DATABASE_NAME" { db = $2; next; }
    $1 == "REDSHIFT_PORT" { port = $2; next; }
    END { printf "%s %s %s %s %s", cluster, port, db, user, password; }
'
}

# Get input parameters
while [ $# -gt 0 ] ; do
  case $1 in
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

if [ $# -ne 1 ] ; then
  usage; exit 1
fi

env=$1
case $env in
   prod|qa) ;;
      *) echo "Unknown deployment environment: $env" >&2; exit 1;;   
esac

# CLI environment variables already defined?
if [ "$PGCMD" -a "$PGPASSWORD" ] ; then
    # Yes, return "do nothing" command
    echo :
else
    # No, get database connection for this environment
    which psql >/dev/null || { echo "Postgres CLI not installed. Please run 'brew install postgres'." >&2; exit 1; }
    binDir=$(dirname $0)
    read cluster port db user password <<<$(dbParams $env)

    # Export CLI environment variable definitions
    echo export PGCMD="'psql -h $cluster -p $port -d $db -U $user -q -F , -v ON_ERROR_STOP=on -P null=null -A -t'" PGPASSWORD=$password
fi
