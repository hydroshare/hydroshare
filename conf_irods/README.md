- root contains irods-docker-entrypoint.sh and irods.config
- /etc/irods contains database_config.json, server_config.json, service_account.config and other files that seem to be stock, already part of the docker image

- /var/lib/irods/.irods/irods_environment.json
- /var/lib/irods/.odbc.ini
- /var/lib/irods/.pgpass


## Create Linux user ${HS_USER_ZONE_PROXY_USER} on ${HS_USER_ZONE_HOST}
#echo "INFO: Create Linux user ${HS_USER_ZONE_PROXY_USER} on ${HS_USER_ZONE_HOST}"
#echo "[root@${HS_USER_ZONE_HOST}]$ useradd -m -p ${HS_USER_ZONE_PROXY_USER_PWD} -s /bin/bash ${HS_USER_ZONE_PROXY_USER}"
#docker exec ${HS_USER_ZONE_HOST} sh -c "useradd -m -p ${HS_USER_ZONE_PROXY_USER_PWD} -s /bin/bash ${HS_USER_ZONE_PROXY_USER}"
#echo "[root@${HS_USER_ZONE_HOST}]$ cp create_user.sh delete_user.sh /home/${HS_USER_ZONE_PROXY_USER}"
#docker cp create_user.sh ${HS_USER_ZONE_HOST}:/home/${HS_USER_ZONE_PROXY_USER}
#docker cp delete_user.sh ${HS_USER_ZONE_HOST}:/home/${HS_USER_ZONE_PROXY_USER}
#docker exec ${HS_USER_ZONE_HOST} chown -R ${HS_USER_ZONE_PROXY_USER}:${HS_USER_ZONE_PROXY_USER} /home/${HS_USER_ZONE_PROXY_USER}
#docker exec ${HS_USER_ZONE_HOST} sh -c "echo "${HS_USER_ZONE_PROXY_USER}":"${HS_USER_ZONE_PROXY_USER}" | chpasswd"
#
## modify /etc/irods/server_config.json
#echo "INFO: federation configuration for ${IRODS_HOST}"
#docker exec ${IRODS_HOST} sh -c "jq '.federation[0].icat_host=\"${HS_USER_ZONE_HOST}\" | .federation[0].zone_name=\"${HS_USER_IRODS_ZONE}\" | .federation[0].zone_key=\"${HS_USER_IRODS_ZONE}_KEY\" | .federation[0].negotiation_key=\"${SHARED_NEG_KEY}\"' /etc/irods/server_config.json > /tmp/tmp.json"
#docker exec ${IRODS_HOST} sh -c "cat /tmp/tmp.json | jq '.' > /etc/irods/server_config.json && chown irods:irods /etc/irods/server_config.json && rm -f /tmp/tmp.json"
#docker exec ${IRODS_HOST} sh -c "cat /etc/irods/server_config.json | jq '.federation'"
#
#echo "INFO: federation configuration for ${HS_USER_ZONE_HOST}"
#docker exec ${HS_USER_ZONE_HOST} sh -c "jq '.federation[0].icat_host=\"${IRODS_HOST}\" | .federation[0].zone_name=\"${IRODS_ZONE}\" | .federation[0].zone_key=\"${IRODS_ZONE}_KEY\" | .federation[0].negotiation_key=\"${SHARED_NEG_KEY}\"' /etc/irods/server_config.json > /tmp/tmp.json"
#docker exec ${HS_USER_ZONE_HOST} sh -c "cat /tmp/tmp.json | jq '.' > /etc/irods/server_config.json && chown irods:irods /etc/irods/server_config.json && rm -f /tmp/tmp.json"
#docker exec ${HS_USER_ZONE_HOST} sh -c "cat /etc/irods/server_config.json | jq '.federation'"
#
## make resource ${IRODS_DEFAULT_RESOURCE} in ${IRODS_ZONE}
#echo "[rods@${IRODS_HOST}]$ iadmin mkresc ${IRODS_DEFAULT_RESOURCE} unixfilesystem ${IRODS_HOST}:/var/lib/irods/iRODS/Vault"
#docker run --rm --env-file env-files/rods@${IRODS_HOST}.env \
#    mjstealey/docker-irods-icommands:4.1.8 \
#    sh -c "iadmin mkresc ${IRODS_DEFAULT_RESOURCE} unixfilesystem ${IRODS_HOST}:/var/lib/irods/iRODS/Vault"
#
## make user ${IRODS_USERNAME} in ${IRODS_ZONE}
#echo "[rods@${IRODS_HOST}]$ iadmin mkuser ${IRODS_USERNAME} rodsuser"
#echo "[rods@${IRODS_HOST}]$ iadmin moduser ${IRODS_USERNAME} password ${IRODS_AUTH}"
#docker run --rm --env-file env-files/rods@${IRODS_HOST}.env \
#    mjstealey/docker-irods-icommands:4.1.8 \
#    sh -c "iadmin mkuser ${IRODS_USERNAME} rodsuser && iadmin moduser ${IRODS_USERNAME} password ${IRODS_AUTH}"
#
## make ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} and ${HS_USER_ZONE_PROXY_USER} in ${HS_USER_ZONE_HOST}
#echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkuser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} rodsuser"
#echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin moduser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} password ${HS_WWW_IRODS_PROXY_USER_PWD}"
#docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
#    mjstealey/docker-irods-icommands:4.1.8 \
#    sh -c "iadmin mkuser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} rodsuser && iadmin moduser ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} password ${HS_WWW_IRODS_PROXY_USER_PWD}"
#
#echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkuser ${HS_USER_ZONE_PROXY_USER} rodsadmin"
#echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin moduser ${HS_USER_ZONE_PROXY_USER} password ${HS_USER_ZONE_PROXY_USER_PWD}"
#docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
#    mjstealey/docker-irods-icommands:4.1.8 \
#    sh -c "iadmin mkuser ${HS_USER_ZONE_PROXY_USER} rodsadmin && iadmin moduser ${HS_USER_ZONE_PROXY_USER} password ${HS_USER_ZONE_PROXY_USER_PWD}"
#
## make resource ${HS_IRODS_LOCAL_ZONE_DEF_RES} in ${HS_USER_ZONE_HOST}
#echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkresc ${HS_IRODS_LOCAL_ZONE_DEF_RES} unixfilesystem ${HS_USER_ZONE_HOST}:/var/lib/irods/iRODS/Vault"
#docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
#    mjstealey/docker-irods-icommands:4.1.8 \
#    sh -c "iadmin mkresc ${HS_IRODS_LOCAL_ZONE_DEF_RES} unixfilesystem ${HS_USER_ZONE_HOST}:/var/lib/irods/iRODS/Vault"
#
## iint the ${HS_USER_ZONE_PROXY_USER} in ${HS_USER_ZONE_HOST}
#echo "[${HS_USER_ZONE_PROXY_USER}@${HS_USER_ZONE_HOST}]$ iinit"
#docker exec -u ${HS_USER_ZONE_PROXY_USER} ${HS_USER_ZONE_HOST} sh -c "export IRODS_HOST=${ICAT2IP} && export IRODS_PORT=${IRODS_PORT} && export IRODS_USER_NAME=${HS_USER_ZONE_PROXY_USER} && export IRODS_PASSWORD=${HS_USER_ZONE_PROXY_USER_PWD} && iinit ${HS_USER_ZONE_PROXY_USER_PWD}"
## add irods_environment.json file for rods user
#jq -n --arg h "${HS_USER_ZONE_HOST}" --arg p ${IRODS_PORT} --arg z "${HS_USER_IRODS_ZONE}" --arg n "${HS_USER_ZONE_PROXY_USER}" '{"irods_host": $h, "irods_port": 1247, "irods_zone_name": $z, "irods_user_name": $n}' > env-files/rods@${HS_USER_ZONE_HOST}.json
#docker cp env-files/rods@${HS_USER_ZONE_HOST}.json ${HS_USER_ZONE_HOST}:/home/${HS_USER_ZONE_PROXY_USER}/.irods/irods_environment.json
#docker exec ${HS_USER_ZONE_HOST} chown ${HS_USER_ZONE_PROXY_USER}:${HS_USER_ZONE_PROXY_USER} /home/${HS_USER_ZONE_PROXY_USER}/.irods/irods_environment.json
#
## give ${IRODS_USERNAME} own rights over ${HS_USER_IRODS_ZONE}/home
#echo "[rods@${HS_USER_ZONE_HOST}]$ iadmin mkuser ${IRODS_USERNAME}#${IRODS_ZONE} rodsuser"
#docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
#    mjstealey/docker-irods-icommands:4.1.8 \
#    sh -c "iadmin mkuser "${IRODS_USERNAME}"#"${IRODS_ZONE}" rodsuser"
#
#echo "[rods@${HS_USER_ZONE_HOST}]$ ichmod -r -M own ${IRODS_USERNAME}#${IRODS_ZONE} /${HS_USER_IRODS_ZONE}/home"
#docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
#    mjstealey/docker-irods-icommands:4.1.8 \
#    sh -c "ichmod -r -M own "${IRODS_USERNAME}"#"${IRODS_ZONE}" /${HS_USER_IRODS_ZONE}/home"
#
## give ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} own rights over ${HS_USER_IRODS_ZONE}/home
#echo "[rods@${HS_USER_ZONE_HOST}]$ ichmod -r -M own ${HS_LOCAL_PROXY_USER_IN_FED_ZONE} /${HS_USER_IRODS_ZONE}/home"
#docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
#    mjstealey/docker-irods-icommands:4.1.8 \
#    sh -c "ichmod -r -M own "${HS_LOCAL_PROXY_USER_IN_FED_ZONE}" /${HS_USER_IRODS_ZONE}/home"
#
## set ${HS_USER_IRODS_ZONE}/home to inherit
#echo "[rods@${HS_USER_ZONE_HOST}]$ ichmod -r -M inherit /${HS_USER_IRODS_ZONE}/home"
#docker run --rm --env-file env-files/rods@${HS_USER_ZONE_HOST}.env \
#    mjstealey/docker-irods-icommands:4.1.8 \
#    sh -c "ichmod -r -M inherit /"${HS_USER_IRODS_ZONE}"/home"



=========================================

[root@users.local.org]$ apt-get install -y openssh-client openssh-server && mkdir /var/run/sshd && sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config && sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd && /etc/init.d/ssh restart
Reading package lists...
Building dependency tree...
Reading state information...
The following extra packages will be installed:
  libwrap0 libx11-6 libx11-data libxau6 libxcb1 libxdmcp6 libxext6 libxmuu1
  ncurses-term openssh-sftp-server tcpd xauth
Suggested packages:
  ssh-askpass libpam-ssh keychain monkeysphere rssh molly-guard ufw
The following NEW packages will be installed:
  libwrap0 libx11-6 libx11-data libxau6 libxcb1 libxdmcp6 libxext6 libxmuu1
  ncurses-term openssh-client openssh-server openssh-sftp-server tcpd xauth
0 upgraded, 14 newly installed, 0 to remove and 92 not upgraded.
Need to get 2,655 kB of archives.
After this operation, 11.2 MB of additional disk space will be used.
Get:1 http://security.debian.org/ jessie/updates/main libx11-data all 2:1.6.2-3+deb8u2 [126 kB]
Get:2 http://security.debian.org/ jessie/updates/main libx11-6 amd64 2:1.6.2-3+deb8u2 [729 kB]
Get:3 http://deb.debian.org/debian/ jessie/main libwrap0 amd64 7.6.q-25 [58.5 kB]
Get:4 http://deb.debian.org/debian/ jessie/main libxau6 amd64 1:1.0.8-1 [20.7 kB]
Get:5 http://deb.debian.org/debian/ jessie/main libxdmcp6 amd64 1:1.1.1-1+b1 [24.9 kB]
Get:6 http://deb.debian.org/debian/ jessie/main libxcb1 amd64 1.10-3+b1 [44.4 kB]
Get:7 http://security.debian.org/ jessie/updates/main openssh-client amd64 1:6.7p1-5+deb8u7 [693 kB]
Get:8 http://deb.debian.org/debian/ jessie/main libxext6 amd64 2:1.3.3-1 [52.7 kB]
Get:9 http://deb.debian.org/debian/ jessie/main libxmuu1 amd64 2:1.1.2-1 [23.3 kB]
Get:10 http://security.debian.org/ jessie/updates/main openssh-sftp-server amd64 1:6.7p1-5+deb8u7 [38.0 kB]
Get:11 http://deb.debian.org/debian/ jessie/main ncurses-term all 5.9+20140913-1+deb8u3 [454 kB]
Get:12 http://security.debian.org/ jessie/updates/main openssh-server amd64 1:6.7p1-5+deb8u7 [329 kB]
Get:13 http://deb.debian.org/debian/ jessie/main tcpd amd64 7.6.q-25 [22.9 kB]
Get:14 http://deb.debian.org/debian/ jessie/main xauth amd64 1:1.0.9-1 [38.2 kB]
dpkg-preconfigure: unable to re-open stdin:
Fetched 2,655 kB in 3s (781 kB/s)
Selecting previously unselected package libwrap0:amd64.
(Reading database ... 14463 files and directories currently installed.)
Preparing to unpack .../libwrap0_7.6.q-25_amd64.deb ...
Unpacking libwrap0:amd64 (7.6.q-25) ...
Selecting previously unselected package libxau6:amd64.
Preparing to unpack .../libxau6_1%3a1.0.8-1_amd64.deb ...
Unpacking libxau6:amd64 (1:1.0.8-1) ...
Selecting previously unselected package libxdmcp6:amd64.
Preparing to unpack .../libxdmcp6_1%3a1.1.1-1+b1_amd64.deb ...
Unpacking libxdmcp6:amd64 (1:1.1.1-1+b1) ...
Selecting previously unselected package libxcb1:amd64.
Preparing to unpack .../libxcb1_1.10-3+b1_amd64.deb ...
Unpacking libxcb1:amd64 (1.10-3+b1) ...
Selecting previously unselected package libx11-data.
Preparing to unpack .../libx11-data_2%3a1.6.2-3+deb8u2_all.deb ...
Unpacking libx11-data (2:1.6.2-3+deb8u2) ...
Selecting previously unselected package libx11-6:amd64.
Preparing to unpack .../libx11-6_2%3a1.6.2-3+deb8u2_amd64.deb ...
Unpacking libx11-6:amd64 (2:1.6.2-3+deb8u2) ...
Selecting previously unselected package libxext6:amd64.
Preparing to unpack .../libxext6_2%3a1.3.3-1_amd64.deb ...
Unpacking libxext6:amd64 (2:1.3.3-1) ...
Selecting previously unselected package libxmuu1:amd64.
Preparing to unpack .../libxmuu1_2%3a1.1.2-1_amd64.deb ...
Unpacking libxmuu1:amd64 (2:1.1.2-1) ...
Selecting previously unselected package ncurses-term.
Preparing to unpack .../ncurses-term_5.9+20140913-1+deb8u3_all.deb ...
Unpacking ncurses-term (5.9+20140913-1+deb8u3) ...
Selecting previously unselected package openssh-client.
Preparing to unpack .../openssh-client_1%3a6.7p1-5+deb8u7_amd64.deb ...
Unpacking openssh-client (1:6.7p1-5+deb8u7) ...
Selecting previously unselected package openssh-sftp-server.
Preparing to unpack .../openssh-sftp-server_1%3a6.7p1-5+deb8u7_amd64.deb ...
Unpacking openssh-sftp-server (1:6.7p1-5+deb8u7) ...
Selecting previously unselected package openssh-server.
Preparing to unpack .../openssh-server_1%3a6.7p1-5+deb8u7_amd64.deb ...
Unpacking openssh-server (1:6.7p1-5+deb8u7) ...
Selecting previously unselected package tcpd.
Preparing to unpack .../tcpd_7.6.q-25_amd64.deb ...
Unpacking tcpd (7.6.q-25) ...
Selecting previously unselected package xauth.
Preparing to unpack .../xauth_1%3a1.0.9-1_amd64.deb ...
Unpacking xauth (1:1.0.9-1) ...
Processing triggers for systemd (215-17+deb8u5) ...
Setting up libwrap0:amd64 (7.6.q-25) ...
Setting up libxau6:amd64 (1:1.0.8-1) ...
Setting up libxdmcp6:amd64 (1:1.1.1-1+b1) ...
Setting up libxcb1:amd64 (1.10-3+b1) ...
Setting up libx11-data (2:1.6.2-3+deb8u2) ...
Setting up libx11-6:amd64 (2:1.6.2-3+deb8u2) ...
Setting up libxext6:amd64 (2:1.3.3-1) ...
Setting up libxmuu1:amd64 (2:1.1.2-1) ...
Setting up ncurses-term (5.9+20140913-1+deb8u3) ...
Setting up openssh-client (1:6.7p1-5+deb8u7) ...
Setting up openssh-sftp-server (1:6.7p1-5+deb8u7) ...
Setting up openssh-server (1:6.7p1-5+deb8u7) ...
Creating SSH2 RSA key; this may take some time ...
2048 d0:79:95:2e:64:80:2b:f4:e8:17:fa:10:47:d8:d7:41 /etc/ssh/ssh_host_rsa_key.pub (RSA)
Creating SSH2 DSA key; this may take some time ...
1024 f1:ac:9a:25:f0:84:a5:d8:0d:7a:18:3f:7a:d6:22:1f /etc/ssh/ssh_host_dsa_key.pub (DSA)
Creating SSH2 ECDSA key; this may take some time ...
256 47:5f:7e:d3:93:4a:1d:c2:44:25:a7:36:9e:0e:90:03 /etc/ssh/ssh_host_ecdsa_key.pub (ECDSA)
Creating SSH2 ED25519 key; this may take some time ...
256 48:44:1e:17:e4:b8:00:ec:dd:1a:2a:b1:a0:56:57:50 /etc/ssh/ssh_host_ed25519_key.pub (ED25519)
invoke-rc.d: policy-rc.d denied execution of start.
Setting up tcpd (7.6.q-25) ...
Setting up xauth (1:1.0.9-1) ...
Processing triggers for libc-bin (2.19-18+deb8u6) ...
Processing triggers for systemd (215-17+deb8u5) ...
Restarting OpenBSD Secure Shell server: sshd.
INFO: Create Linux user hsuserproxy on users.local.org
[root@users.local.org]$ useradd -m -p hsuserproxy -s /bin/bash hsuserproxy
[root@users.local.org]$ cp create_user.sh delete_user.sh /home/hsuserproxy
lstat /Users/mobrien/repo/hydroshare/conf_irods/create_user.sh: no such file or directory
lstat /Users/mobrien/repo/hydroshare/conf_irods/delete_user.sh: no such file or directory
INFO: update /etc/hosts
[root@data.local.org]$ echo "'172.17.0.3' users.local.org" >> /etc/hosts
[root@users.local.org]$ echo "'172.17.0.2' data.local.org" >> /etc/hosts
INFO: make remote zone for each
[rods@data.local.org]$ iadmin mkzone hydroshareuserZone remote 172.17.0.3:1247
[rods@users.local.org]$ iadmin mkzone hydroshareZone remote 172.17.0.2:1247
INFO: federation configuration for data.local.org
[
  {
    "icat_host": "users.local.org",
    "zone_name": "hydroshareuserZone",
    "zone_key": "hydroshareuserZone_KEY",
    "negotiation_key": "hydroshareZonehydroshareuserZone"
  }
]
INFO: federation configuration for users.local.org
[
  {
    "icat_host": "data.local.org",
    "zone_name": "hydroshareZone",
    "zone_key": "hydroshareZone_KEY",
    "negotiation_key": "hydroshareZonehydroshareuserZone"
  }
]
[rods@data.local.org]$ iadmin mkresc hydroshareReplResc unixfilesystem data.local.org:/var/lib/irods/iRODS/Vault
Creating resource:
Name:		"hydroshareReplResc"
Type:		"unixfilesystem"
Host:		"data.local.org"
Path:		"/var/lib/irods/iRODS/Vault"
Context:	""
[rods@data.local.org]$ iadmin mkuser wwwHydroProxy rodsuser
[rods@data.local.org]$ iadmin moduser wwwHydroProxy password wwwHydroProxy
[rods@users.local.org]$ iadmin mkuser localHydroProxy rodsuser
[rods@users.local.org]$ iadmin moduser localHydroProxy password wwwHydroProxy
[rods@users.local.org]$ iadmin mkuser hsuserproxy rodsadmin
[rods@users.local.org]$ iadmin moduser hsuserproxy password hsuserproxy
[rods@users.local.org]$ iadmin mkresc hydroshareLocalResc unixfilesystem users.local.org:/var/lib/irods/iRODS/Vault
Creating resource:
Name:		"hydroshareLocalResc"
Type:		"unixfilesystem"
Host:		"users.local.org"
Path:		"/var/lib/irods/iRODS/Vault"
Context:	""
[hsuserproxy@users.local.org]$ iinit
./build_containers.sh: line 187: jq: command not found
[rods@users.local.org]$ iadmin mkuser wwwHydroProxy#hydroshareZone rodsuser
[rods@users.local.org]$ ichmod -r -M own wwwHydroProxy#hydroshareZone /hydroshareuserZone/home
[rods@users.local.org]$ ichmod -r -M own localHydroProxy /hydroshareuserZone/home
[rods@users.local.org]$ ichmod -r -M inherit /hydroshareuserZone/home
