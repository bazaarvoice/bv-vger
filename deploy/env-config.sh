#!/usr/bin/env bash
set -e

usage()
{
    echo Usage: `basename $0` "[-f] [-p] <deployEnv> [lambdaDir]" >&2
    echo "" >&2
    echo "  Generates the environment variable configuration file for the given deployment environment (either 'qa' or 'prod')" >&2
    echo "  in the specified lambda directory. If lambdaDir is omitted, the current working directory is assumed." >&2
    echo "" >&2
    echo "  -f    If specified, overwrites any existing configuration file." >&2
    echo "" >&2
    echo "  -p    If specified, prints environment variable configuration to standard output file without creating any" >&2
    echo "        configuration file. In this case, the lambdaDir argument is ignored." >&2
}

printAwsConfig()
{
    if [[ -z "`which jq`" ]] ; then
        echo "This command requires the 'jq' program. Please run 'brew install jq'." >&2
        exit 1
    fi
    aws lambda get-function-configuration --function-name vger-sls-create-project-${env} |
        jq -M -r ".Environment.Variables | to_entries + [{key: \"ENV\", value: \"${env}\"}]  | map(.key + \": '\" + .value + \"'\") | .[]"
}

while [[ $# -gt 0 ]] ; do
  case $1 in
    -p) print=1;;
    -f) force=1;;
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

if [[ $# -lt 1 || $# -gt 2 ]] ; then
    usage
    exit 1
fi

env=$1
case ${env} in
   prod|qa) ;;
      *) echo "Unknown deployment environment: $env" >&2; exit 1;;   
esac

if [[ "$print" ]] ; then
    printAwsConfig
else
    lambdaDir=${2:-`pwd`}
    if [[ ! -f ${lambdaDir}/serverless.yml ]] ; then
        echo "${lambdaDir} is not a lambda directory" >&2
        exit 1
    fi

    # Need to generate a new config file?
    cd ${lambdaDir}
    configFile=env/env.${env}.yml
    if [[ ! -f ${configFile} || "$force" ]] ; then
        # Yes, extract environment variables from current AWS configuration
        mkdir -p `dirname ${configFile}`
        printAwsConfig > ${configFile}
    fi
fi
