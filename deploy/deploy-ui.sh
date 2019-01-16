#!/usr/bin/env bash
set -e

usage()
{
    echo Usage: `basename $0` "<env> <ssm_store>" >&2
    echo "" >&2
    echo "  Deploys UI JavaScript code and supporting API code to the specified environment (either 'qa' or 'prod')" >&2
}

while [[ $# -gt 0 ]] ; do
  case $1 in
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

if [[ $# -ne 2 ]] ; then
    usage
    exit 1
fi

bindir=`dirname $0`
bindir=`cd ${bindir}; pwd`

# Define the target S3 bucket for this environment
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

case ${env} in
   prod|qa) bucket_name=$(aws ssm get-parameter --name /${ssm_store}/s3/${env}/bucket_name --query "Parameter"."Value" --output text);;
         *) echo "Unknown environment: $env" >&2; exit 1;;
esac

# Define the UI config file for this environment         
ui_config=`${bindir}/ui-config.sh ${env}`

# Deploy UI code to S3 bucket
cd ${bindir}/..
aws s3 sync source/webpage s3://${bucket_name}/vger --include "*" --exclude 'reports/*' 
rm ${ui_config}

cd ${bindir}
