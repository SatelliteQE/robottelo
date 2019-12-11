#!/usr/bin/env bash

# This script finds empty :id: and replace with new uuids
# Then it finds for duplicates and replaces last occurrence with new uuids
# finally it fixes ':id:xyz' to ':id: xyz' (missing space after :)

ID_TOKEN=":id:"

if [ "$1" = "--check" ]; then
    CHECK_ONLY=true
    echo "Running in uuid-check only mode..."
else
    CHECK_ONLY=false
    echo "Running in uuid-fix mode..."
fi

# finds occurrences of empty id: testimony tags
EMPTY_IDS=$(grep -E -i -r -n "\s*${ID_TOKEN}\s*(.+[[:blank:]]|$)" tests/foreman/ --include=*.py)

if [ -n "$EMPTY_IDS" ]; then
   if [ $CHECK_ONLY = true ]; then
       echo "Empty $ID_TOKEN found in testimony tags"
       echo $EMPTY_IDS
       exit 1
   else
       echo "Generating new UUIDS for empty $ID_TOKEN tags..."
   fi
else
   echo "No empty $ID_TOKEN was found"
fi

# iterate if any empty :id found
for output_line in $EMPTY_IDS
do
    if (echo "$output_line" | grep "tests/foreman"); then
        OLDIFS=$IFS
        # splits the grep output to get filename and occurrence line number
        IFS=':' read -r filename line <<< $output_line
        # generate uuid and place in specific line number
        NEW_ID=$(python -c 'import uuid; print(uuid.uuid4())')
        sed -r -i~ "${line}s/${ID_TOKEN}(.+[[:blank:]]|$)/${ID_TOKEN} ${NEW_ID}/g" $filename
        IFS=$OLDIFS
    fi
done

# This script finds duplicated :id and replaces with new uuids

# Finds occurrences of :id: in testimony tags then
# sort the output and filters only the duplicated
# then looks for existence of ":id:" in final output
# NOTE: can't print the line number -n here because of uniq -d
DUP_EXISTS=$(grep -r -i $ID_TOKEN tests/foreman/ --include="*.py" | sort -k2 | uniq -d -f2)

if [ -n "$DUP_EXISTS" ]; then
   if [ $CHECK_ONLY = true ]; then
       echo "Duplicate $ID_TOKEN found in testimony tags"
       echo -e "${DUP_EXISTS}"
       exit 1
   else
       echo "Generating new UUIDS for duplicated $ID_TOKEN tags..."
   fi
else
   echo "No duplicated $ID_TOKEN was found"
fi

grep -r -i $ID_TOKEN tests/foreman/ --include="*.py" | sort -k2 | uniq -d -f2 | while read -r line ; do
    OLDIFS=$IFS
    IFS=':' read -r dup_file dup_id <<< $line
    echo "filename: $dup_file"
    echo "Id to replace: $dup_id"
    NEW_ID=$(python -c 'import uuid; print(uuid.uuid4())')
    echo "Replacing with the new id: $NEW_ID"
    LAST_LINE=$(grep -i -n "$dup_id" $dup_file | tail -1)

    IFS=':' read -r linenumber linecontent <<< $LAST_LINE
    echo $linenumber
    trimmed_linecontent=$(echo $linecontent)
    sed -i~ "${linenumber}s/${trimmed_linecontent}/${ID_TOKEN} ${NEW_ID}/g" $dup_file
    echo "----------------------------------------------------------------"
    IFS=$OLDIFS
done

# This script finds id: missing spaces after :


MISSING_SPACES=$(grep -E -i -r -n "${ID_TOKEN}[^ ]" tests/foreman/ --include=*.py)

if [ -n "$MISSING_SPACES" ]; then
   if [ $CHECK_ONLY = true ]; then
       echo "Found $ID_TOKEN tags missing space after : ..."
       echo $MISSING_SPACES
       exit 1
   else
       echo "Fixing $ID_TOKEN tags missing spaces..."
   fi
else
   echo "No $ID_TOKEN missing spaces was found"
fi

grep -E -i -r -n "${ID_TOKEN}[^ ]" tests/foreman/ --include=*.py | while read -r line ; do
    OLDIFS=$IFS
    IFS=':' read -r missing_file linenumber linecontent <<< $line
    IFS=':' read -r tag uuid <<< $linecontent
    trimmed_linecontent=$(echo $linecontent)
    sed -i~ "${linenumber}s/${trimmed_linecontent}/${tag}: ${uuid}/g" $missing_file
    IFS=$OLDIFS
done
