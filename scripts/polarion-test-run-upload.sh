#!/bin/bash

# requires curl and betelgeuse pypi package installed
# https://betelgeuse.readthedocs.io/en/latest/
set -e

usage() {
cat <<EOM

usage: $0 options

Tool to upload Test Run data into Polarion

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
  -r, --results <junit-file>
         Specify junit file to transform and upload
  -i, --id <test-run-id>
         Specify test run identifier


EXAMPLE:
  $0 -s http://polarion.example.com/polarion/ -u Polar -p *** -P PolarStuff -d tests/foreman -r test-results.xml -i "Testing 6.8.0 Snap 7.0"

EOM
}

if ! options=$(getopt -o hs:u:p:P:d:r:i: -l help,server:,user:,password:,project:,directory:,results:,id: -- "$@"); then
  exit 1
fi

eval set -- $options

while [ $# -gt 0 ]; do
    case $1 in
    -s|--server) POLARION_URL="$2" ; shift ;;
    -u|--user) POLARION_USERNAME="$2" ; shift ;;
    -p|--password) POLARION_PASSWORD="$2" ; shift ;;
    -P|--project) POLARION_PROJECT="$2" ; shift ;;
    -d|--directory) TEST_DIRECTORY="$2" ; shift ;;
    -r|--results) JUNIT_FILE="$2" ; shift ;;
    -i|--id) TEST_RUN_ID="$2" ; shift ;;
    -h|--help) usage ;  exit ;;
    (--) shift; break;;
    (-*) echo "$0: error: unrecognized option $1" 1>&2; usage ; exit 1;;
    (*) break;;
    esac
    shift
done

if [[ -z $POLARION_URL || -z $POLARION_USERNAME || -z $POLARION_PASSWORD || -z $POLARION_PROJECT || -z $TEST_DIRECTORY || -z $JUNIT_FILE || -z $TEST_RUN_ID ]] ; then
  echo "$0: error: one or more mandatory options are missing"
  usage
  exit 1
fi

TOKEN_PREFIX=""
POLARION_SELECTOR="name=Satellite 6"
TEST_RUN_GROUP_ID="$(echo ${TEST_RUN_ID} | cut -d' ' -f2 | cut -d'-' -f1)"

set -x
sed -i 's/\x1b/ESC/g' "${JUNIT_FILE}"
betelgeuse ${TOKEN_PREFIX} test-run \
    --custom-fields "isautomated=true" \
    --custom-fields "arch=x8664" \
    --custom-fields "variant=server" \
    --response-property "${POLARION_SELECTOR}" \
    --test-run-title "${TEST_RUN_ID}" \
    --test-run-id "${TEST_RUN_ID}" \
    --test-run-group-id "${TEST_RUN_GROUP_ID}" \
    --status inprogress \
    "${JUNIT_FILE}" "${TEST_DIRECTORY}" "${POLARION_USERNAME}" "${POLARION_PROJECT}" "${JUNIT_FILE}"
curl -f -k -u "${POLARION_USERNAME}:${POLARION_PASSWORD}" -F file=@${JUNIT_FILE} "${POLARION_URL}import/xunit"
