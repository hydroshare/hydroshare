#!/usr/bin/env bash

source env-files/use-local-irods.env
echo "CONFIGURE: local_settings.py"
grep -v '^#' < env-files/use-local-irods.env | { \
    while read line; do
        if [[ ! -z "${line}" ]]; then
            HSVAR=$(echo ${line} | cut -d '=' -f 1)
            HSVAL=$(echo ${line} | cut -d '=' -f 2)
            echo "$ sed -i /^\<"${HSVAR}"\>.*/c\\"${HSVAR}"="${HSVAL}" ../hydroshare/local_settings.py"
            sed -i "/^\<"${HSVAR}"\>.*/c\\"${HSVAR}"="${HSVAL}"" ../hydroshare/local_settings.py
        fi
    done
}

exit 0;