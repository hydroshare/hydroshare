#!/bin/bash

for DIR in $(ls -l | grep ^d | awk '{ print $NF }')
do
    cd $DIR
    curl -o jquery-ui.css "http://code.jquery.com/ui/1.10.3/themes/$DIR/jquery-ui.css"
    cd ..
done
