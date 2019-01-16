#!/usr/bin/env bash
set -e

usage()
{
    echo Usage: `basename $0` "<env>" >&2
    echo "" >&2
    echo "  Sets up UI configuration for the specified environment (either 'qa' or 'prod')" >&2
}

while [[ $# -gt 0 ]] ; do
  case $1 in
    -*) usage; exit 1;;
     *) break;;
  esac
  shift
done

if [[ $# -ne 1 ]] ; then
    usage
    exit 1
fi

bindir=`dirname $0`
bindir=`cd ${bindir}; pwd`

env=$1
case ${env} in
   prod|qa) ;;
         *) echo "Unknown environment: $env"; exit 1;;
esac

# Setup the UI config file for this environment         
cd ${bindir}/..

ui_src_path=source/webpage
config_src_path=${ui_src_path}/shared
env_src_path=deploy/${env}
config_file_name=constants.js

cp ${env_src_path}/${config_file_name} ${config_src_path}

# Return the generated config file path
echo `pwd`/${config_src_path}/${config_file_name}
