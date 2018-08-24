set -e

usage()
{
    echo Usage: `basename $0`  >&2
    echo "" >&2
    echo "  Runs the current UI code locally, using the QA environment" >&2
}

while [ $# -gt 0 ] ; do
  case $1 in
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

if [ $# -ne 0 ] ; then
    usage
    exit 1
fi

# Define the UI config file for the QA environment         
bindir=`dirname $0`
ui_config=`${bindir}/deploy/ui-config.sh qa`

# Run current UI code in a local Web server
cd ${bindir}/source/webpage
http-server -o

# Clean up generated config file for QA environment
rm $ui_config
