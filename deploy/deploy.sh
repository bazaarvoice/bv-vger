set -e

usage()
{
    echo Usage: `basename $0` "env" >&2
    echo "" >&2
    echo "  Deploys UI JavaScript code and supporting API code to the specified environment (either 'qa' or 'prod')" >&2
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

bindir=`dirname $0`
bindir=`cd $bindir; pwd`

# Run private file transfer script (only works if bv-vger-config is in same root directory as bv-vger)
cd ..
sh bv-vger-config/vger-config-setup-private.sh 
cd ${bindir}

# Define the target S3 bucket for this environment
env=$1
source deployConstants.sh

case $env in
   prod) bucket_name=${prod_bucket};;
     qa) bucket_name=${qa_bucket};;
      *) echo "Unknown environment: $env" >&2; exit 1;;   
esac

# Define the UI config file for this environment         
ui_config=`${bindir}/ui-config.sh $env`

# Deploy UI code to S3 bucket
cd ${bindir}/..
aws s3 sync source/webpage s3://${bucket_name}/vger --include "*" --exclude 'reports/*' 
rm $ui_config

# Deploy API code
${bindir}/deploy-lambda.sh $env source/web_api

# Deploy reports
${bindir}/build-deploy-reports.sh $env

cd ${bindir}

# Run public file transfer script (only works if bv-vger-config is in same root directory as bv-vger)
cd ../..
sh bv-vger-config/vger-config-setup-public.sh 
cd ${bindir}
