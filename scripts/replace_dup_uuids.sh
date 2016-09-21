#!/usr/bin/env bash

# This script finds duplicated @id and replaces with new uuids

grep -r -i "@id:" tests/foreman/ | sort | uniq -d | grep "@id:" | while read -r line ; do
    OLDIFS=$IFS
    IFS=':' read -r dup_file dup_id <<< $line
    echo "filename: $dup_file"
    echo "Id to replace: $dup_id"
    NEW_ID=$(uuidgen)
    echo "Replacing with the new id: $NEW_ID"
    LAST_LINE=$(grep -i -n "$dup_id" $dup_file | tail -1)

    IFS=':' read -r linenumber linecontent <<< $LAST_LINE
    echo $linenumber
    trimmed_linecontent=$(echo $linecontent)
    sed -i~ "${linenumber}s/${trimmed_linecontent}/@id: ${NEW_ID}/g" $dup_file
    echo "----------------------------------------------------------------"
    IFS=$OLDIFS
done
