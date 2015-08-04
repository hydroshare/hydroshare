#!/bin/bash

find /home/docker/hydroshare -user root -ls | tr -s ' ' | cut -d ' ' -f 12 > root-items.txt

while read line ; do
    echo "*** REMOVE: ${line} ***"
    rm -rf $line;
done < root-items.txt

exit;