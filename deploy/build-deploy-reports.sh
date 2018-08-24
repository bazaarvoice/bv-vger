#!/bin/bash        
set -e

echo "//-------------------------PHASE 0: BUILD OPTIMIZED APP---------------------------//"
# Define the UI config file for the QA environment         

#Directory of current file
bindir=`dirname $0`
bindir=`cd $bindir; pwd`

# Run private file transfer script (only works if bv-vger-config is in same root directory as bv-vger)
cd ..
sh bv-vger-config/vger-config-setup-private.sh 
cd ${bindir}

# Run current UI code in a local Web server
cd ${bindir}/../source/webpage/reports

#run 'npm run build to bundle and optimize react app
npm run build
echo "Done building report app!" 

#execute post-build script to reroute configuration folders since quarterly-reports is not a stand-alone app
sh reRouter.sh
echo "Done rerouting report app for S3!" 

#leave current directory in order to deploy S3 bucket
cd ${bindir}

echo "//-------------------------PHASE 1: INITIAL CONFIGURATION---------------------------//"

usage()
{
    echo Usage: `basename $0` "env" >&2
    echo "" >&2
    echo "  Sets up report configuration for the specified environment (either 'qa' or 'prod') and then deploys" >&2
}

while [ $# -gt 0 ] ; do
  case $1 in
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

if [ $# -ne 1 ] ; then
    usage
    exit 1
fi

echo "//-------------------------PHASE 2: DEFINE S3 BUCKET---------------------------//"

# Define the target S3 bucket for this environment
env=$1
source deployConstants.sh

case $env in
   prod) bucket_name=${prod_bucket};;
     qa) bucket_name=${qa_bucket};;
      *) echo "Unknown environment: $env" >&2; exit 1;;   
esac

# Define the UI config file for this environment         
reports_config=`${bindir}/reports-config.sh $env`

echo "//-------------------------PHASE 3: DEPLOY TO S3 BUCKET---------------------------//"

# Deploy UI code to S3 bucket
cd ${bindir}/..
aws s3 sync source/webpage/reports s3://${bucket_name}/vger/vger-tools/reports --exclude 'node_modules/*'

#deploy rerouting of app.routes, and then unroute so that tool works locally as well
aws s3 sync source/webpage s3://${bucket_name}/vger --exclude "*" --include "app.routes.js"

#deroute files so that they can be operated in local development
cd ${bindir}/../source/webpage/reports
sh deRouter.sh

echo "Done derouting report app for local dev!" 

rm $reports_config

#leave current directory in order to get back template files
cd ${bindir}

# Run public file transfer script (only works if bv-vger-config is in same root directory as bv-vger)
cd ../..
sh bv-vger-config/vger-config-setup-public.sh 
cd ${bindir}
