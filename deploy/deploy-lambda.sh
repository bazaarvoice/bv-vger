#!/usr/bin/env bash
set -e

usage()
{
    echo Usage: `basename $0` "[-f] <deployEnv> <ssm_store> [lambdaDir]" >&2
    echo "" >&2
    echo "  Deploys lambda functions defined in the given lambdaDir to the given deployment environment (either 'qa' or 'prod')." >&2
    echo "  If lambdaDir is omitted, the current working directory is assumed." >&2
    echo "" >&2
    echo "  -f    If specified, forces generation of a new environment variable configuration file for this deployment environment" >&2
}

while [[ $# -gt 0 ]] ; do
  case $1 in
    -f) force==1;;
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

if [[ $# -lt 2 || $# -gt 3 ]] ; then
    usage
    exit 1
fi

bindir=`dirname $0`
bindir=`cd ${bindir}; pwd`

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

cd ..
lambdaDir=${3:-`pwd`}
if [[ ! -f ${lambdaDir}/serverless.yml ]] ; then
    echo "${lambdaDir} is not a lambda directory" >&2
    exit 1
fi
cd ${lambdaDir}

# If necessary, generate the environment variable configuration for this lambda directory
${bindir}/env-config.sh ${force:+-f} ${env}

serverless deploy --stage ${env} --ssm-store ${ssm_store}

cd ${bindir}
