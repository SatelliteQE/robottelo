#!/bin/bash

# requires curl and betelgeuse pypi package installed
# https://betelgeuse.readthedocs.io/en/latest/
set -e

usage() {
cat <<EOM

usage: $0 options

Tool to upload Test Case data into Polarion

OPTIONS:
  -h, --help
         Show this message
  -s, --server <polarion URL>
         Upload to the specified polarion instance
  -u, --user <username>
         Specify the user name to use for authentication
  -p, --password <password>
         Specify the password to use for authentication
         You can pass POLARION_PASSWORD env variable instead of this option
  -P, --project <projectname>
         Specifiy the polarion project to use
  -d, --directory <directory_path>
         Specify the directory path of tests


EXAMPLE:
  $0 -s http://polarion.example.com/polarion/ -u Polar -p *** -P PolarStuff -d tests/foreman

EOM
}

if ! options=$(getopt -o hs:u:p:P:d: -l help,server:,user:,password:,project:,directory: -- "$@"); then
  exit 1
fi

eval set -- $options

while [ $# -gt 0 ]; do
    case $1 in
    -s|--server) POLARION_URL="$2" ; shift ;;
    -u|--user) POLARION_USERNAME="$2" ; shift ;;
    -p|--password) POLARION_PASSWORD="$2" ; shift ;;
    -P|--project) POLARION_PROJECT="$2" ; shift ;;
    -d|--directory) TESTS_DIRECTORY="$2" ; shift ;;
    -h|--help) usage ;  exit ;;
    (--) shift; break;;
    (-*) echo "$0: error: unrecognized option $1" 1>&2; usage ; exit 1;;
    (*) break;;
    esac
    shift
done

if [[ -z $POLARION_URL || -z $POLARION_USERNAME || -z $POLARION_PASSWORD || -z $POLARION_PROJECT || -z $TESTS_DIRECTORY ]] ; then
  echo "$0: error: one or more mandatory options are missing"
  usage
  exit 1
fi

# setting up Betelgeuse Configuration Module (--config-module)
# https://betelgeuse.readthedocs.io/en/latest/config.html
export PYTHONPATH="${PWD}"
cat > betelgeuse_config.py <<EOF
from betelgeuse import default_config
DEFAULT_APPROVERS_VALUE = '${POLARION_USERNAME}:approved'
DEFAULT_STATUS_VALUE = 'approved'
DEFAULT_SUBTYPE2_VALUE = '-'
TESTCASE_CUSTOM_FIELDS = default_config.TESTCASE_CUSTOM_FIELDS + ('customerscenario',)
TRANSFORM_CUSTOMERSCENARIO_VALUE = default_config._transform_to_lower
DEFAULT_CUSTOMERSCENARIO_VALUE = 'false'
EOF

set -x
betelgeuse requirement "${TESTS_DIRECTORY}" "${POLARION_PROJECT}" "requirement.xml"
curl -f -k -u "${POLARION_USERNAME}:${POLARION_PASSWORD}" -F file=@requirement.xml "${POLARION_URL}import/requirement"

betelgeuse --config-module "betelgeuse_config" test-case \
    --response-property "satellite6=testcases" \
    --automation-script-format "https://github.com/SatelliteQE/robottelo/blob/master/{path}#L{line_number}" \
    "${TESTS_DIRECTORY}" "${POLARION_PROJECT}" test-cases.xml
curl -f -k -u "${POLARION_USERNAME}:${POLARION_PASSWORD}" -F file=@test-cases.xml "${POLARION_URL}import/testcase"
