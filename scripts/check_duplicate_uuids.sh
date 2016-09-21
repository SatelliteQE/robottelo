#!/usr/bin/env bash

# This script checks duplicated or empty uuids and exit with 1 if found

# finds occurrences of empty @id: testimony tags
grep -E -i -r -n "@id:(.+[[:blank:]]|$)" tests/foreman/
EMPTY=$?

if [ $EMPTY = 0 ]; then
    echo "Empty @id found in testimony tags"
    exit 1
fi

# Finds occurrences of @id: in testimony tags then
# sort the output and filters only the duplicated
# then looks for existence of "@id:" in final output
# NOTE: can't print the line number -n here because of uniq -d
grep -r -i "@id:" tests/foreman/ | sort | uniq -d | grep "@id:"
DUPLICATE=$?

# grep exits with status code 0 if text is found
# but we need to invert the logic here
# if duplicate found return with error 1
if [ $DUPLICATE = 0 ]; then
    echo "Duplicate @id found in testimony tags"
    exit 1
fi
