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

# Run current UI code in a local Web server
cd ${bindir}/source/webpage/reports

#NOTE: if adding new links or changing things that require file paths, uncomment 'local' section in head of index.html
#run 'npm run build to bundle and optimize react app
npm run build
echo "Done building report app!" 

#reRouter not called since local deployment of the standalone app is required to make dynamic changes to app
#Redirects away from quarterly-reports fail when on report-ui-local because the app is not
#encapsulated by angular app anymore and is ran locally. This script should only be run when doing local 
#react development on quarterly reports

npm start
