#!/bin/bash

export CONFIG_DIRECTORY='./config'
export WORKING_DIR='/projects/hydroshare/hsdata/zdt/beta'
export CONFIG_FILE="${WORKING_DIR}/deploy/hydroshare-config.yaml"
export WORKER_FILE="${WORKING_DIR}/workers.lst"
export CURRENT_FILE="${WORKING_DIR}/current-vm"
export RUNNING_FILE="${WORKING_DIR}/running-vm"
export HOME_DIR=${PWD}
export CURRENT_VM=`cat $CURRENT_FILE 2>/dev/null`
export EXTERNAL_METRICS_HOST='public.cuahsi.org'
export INTERNAL_METRICS_HOST='metrics-hs-01.edc.renci.org:8080'
export RUNNING_VM=`cat nginx/config-files/hs-nginx.conf | grep -m 1 proxy_pass | cut -f3 -d'/' | cut -f1 -d';'`
export BACKUP_VM=`cat $WORKER_FILE | grep -v $RUNNING_VM | head -1`
echo -n $RUNNING_VM > $RUNNING_FILE
export IS_RUNNING=`docker ps | grep 'nginx:1.11'`
export FQDN_OR_IP=`hostname`
