#!/usr/bin/env bash

# this script finds empty @id: and replace with new uuids

# finds occurrences of empty @id: testimony tags
EMPTY_IDS=$(grep -E -i -r -n "@id:(.+[[:blank:]]|$)" tests/foreman/)

if [ -n "$EMPTY_IDS" ]; then
   echo "Generating new UUIDS for empty @id tags..."
else
   echo "No empty @id was found"
fi

# iterate if any empty @id found
for output_line in $EMPTY_IDS
do
    if (echo "$output_line" | grep "tests/foreman"); then
        OLDIFS=$IFS
        # splits the grep output to get filename and occurrence line number
        IFS=':' read -r filename line <<< $output_line
        # generate uuid and place in specific line number
        sed -r -i~ "${line}s/@id:(.+[[:blank:]]|$)/@id: $(uuidgen)/g" $filename
        IFS=$OLDIFS
    fi
done
