## Using local federated iRODS

The scripts herein are a one-way street that update the configuration of HydroShare to use a locally deployed federated pair 
of iCAT v.4.1.8 servers in Docker.

Effected files:
-	modified:   hsctl
-	modified:   hydroshare/local_settings.py
-	modified:   scripts/templates/docker-compose-local-irods.template

### How to use

From within the `irods` directory, run the script named **use-local-irods.sh**

```bash
$ cd irods
$ ./use-local-irods.sh
```
The script will run, deploy and federate two iCAT servers, and modify the three aforementioned files to be configured to use the 
newly created iRODS Docker servers. Once the script has completed, return back the the main `hydroshare` directory and run
the **hsctl** script as you normally would.

```bash
$ cd ../
$ ./hsctl rebuild --db
```

### In Docker

If all deploys as it should you will see this reflected in the `docker ps` output. As an example:

```
$ docker ps
CONTAINER ID        IMAGE                               COMMAND                  CREATED             STATUS              PORTS                                                                                 NAMES
40fbf4c5ce0d        hydroshare_defaultworker            "/bin/bash init-defau"   53 minutes ago      Up 46 minutes                                                                                             defaultworker
d6dd948dd220        hydroshare_dockerworker             "/bin/bash init-docke"   53 minutes ago      Up 46 minutes                                                                                             dockerworker
46e74eb63c86        hydroshare_hydroshare               "/bin/bash init-hydro"   53 minutes ago      Up 46 minutes       0.0.0.0:8000->8000/tcp, 0.0.0.0:1338->2022/tcp                                        hydroshare
aabeaf3b88e3        mjstealey/docker-irods-icat:4.1.8   "/irods-docker-entryp"   56 minutes ago      Up 56 minutes       1248/tcp, 5432/tcp, 20000-20199/tcp, 0.0.0.0:32779->22/tcp, 0.0.0.0:32778->1247/tcp   users.local.org
120b4b31a3b9        mjstealey/docker-irods-icat:4.1.8   "/irods-docker-entryp"   56 minutes ago      Up 56 minutes       1248/tcp, 5432/tcp, 20000-20199/tcp, 0.0.0.0:32777->1247/tcp                          data.local.org
abdbbf412771        mjstealey/hs_postgres:9.4.7         "/docker-entrypoint.s"   About an hour ago   Up 53 minutes       5432/tcp                                                                              postgis
f9dfb9981949        makuk66/docker-solr:4.10.4          "sh -c '/bin/bash /op"   About an hour ago   Up 53 minutes       0.0.0.0:32780->8983/tcp                                                               solr
e259b96f8731        redis:2.8                           "docker-entrypoint.sh"   About an hour ago   Up 53 minutes       6379/tcp                                                                              redis
cf1828ee0096        rabbitmq:3.5                        "/docker-entrypoint.s"   About an hour ago   Up 53 minutes       4369/tcp, 5671-5672/tcp, 25672/tcp                                                    rabbitmq
```

### Known issues at this time

There is an iRODS related error that occurs when an attempt is made to create an iRODS account in the user zone from the profile 
edit page. The error is denoted in the yellow popup as "*Failure iRODS server failed to create this iRODS account mjs. 
Check the server log for details.*" As well as in the **hydroshare.log** file.

```
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] starting thread (client mode): 0x7b0d3f90L
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] Local version/idstring: SSH-2.0-paramiko_1.16.0
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] Remote version/idstring: SSH-2.0-OpenSSH_6.7p1 Debian-5+deb8u3
[22/Oct/2016 01:37:16] INFO [paramiko.transport:282] Connected (version 2.0, client OpenSSH_6.7p1)
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] kex algos:[u'curve25519-sha256@libssh.org', u'ecdh-sha2-nistp256', u'ecdh-sha2-nistp384', u'ecdh-sha2-nistp521', u'diffie-hellman-group-exchange-sha256', u'diffie-hellman-group14-sha1'] server key:[u'ssh-rsa', u'ssh-dss', u'ecdsa-sha2-nistp256', u'ssh-ed25519'] client encrypt:[u'aes128-ctr', u'aes192-ctr', u'aes256-ctr', u'aes128-gcm@openssh.com', u'aes256-gcm@openssh.com', u'chacha20-poly1305@openssh.com'] server encrypt:[u'aes128-ctr', u'aes192-ctr', u'aes256-ctr', u'aes128-gcm@openssh.com', u'aes256-gcm@openssh.com', u'chacha20-poly1305@openssh.com'] client mac:[u'umac-64-etm@openssh.com', u'umac-128-etm@openssh.com', u'hmac-sha2-256-etm@openssh.com', u'hmac-sha2-512-etm@openssh.com', u'hmac-sha1-etm@openssh.com', u'umac-64@openssh.com', u'umac-128@openssh.com', u'hmac-sha2-256', u'hmac-sha2-512', u'hmac-sha1'] server mac:[u'umac-64-etm@openssh.com', u'umac-128-etm@openssh.com', u'hmac-sha2-256-etm@openssh.com', u'hmac-sha2-512-etm@openssh.com', u'hmac-sha1-etm@openssh.com', u'umac-64@openssh.com', u'umac-128@openssh.com', u'hmac-sha2-256', u'hmac-sha2-512', u'hmac-sha1'] client compress:[u'none', u'zlib@openssh.com'] server compress:[u'none', u'zlib@openssh.com'] client lang:[u''] server lang:[u''] kex follows?False
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] Kex agreed: diffie-hellman-group14-sha1
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] Cipher agreed: aes128-ctr
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] MAC agreed: hmac-sha2-256
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] Compression agreed: none
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] kex engine KexGroup14 specified hash_algo <built-in function openssl_sha1>
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] Switch to new keys ...
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] Adding ssh-rsa host key for users.local.org: 0e6525f0ff7006dd555e9d4a161a49ed
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] userauth is OK
[22/Oct/2016 01:37:16] INFO [paramiko.transport:282] Authentication (password) successful!
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] [chan 0] Max packet in: 32768 bytes
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] [chan 0] Max packet out: 32768 bytes
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] Secsh channel 0 opened.
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] [chan 0] Sesch channel 0 request ok
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] [chan 0] Sesch channel 0 request ok
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] [chan 0] EOF received (0)
[22/Oct/2016 01:37:16] DEBUG [django:106] ['  - iadmin mkuser mjs rodsuser\r\n', 'hsuserproxy\r\n', 'ERROR: _rcConnect: connectToRhost error, server on users.local.org:0 is probably down status = -305111 USER_SOCK_CONNECT_ERR, Connection refused\r\n', 'ERROR: rcConnect failure USER_SOCK_CONNECT_ERR (Connection refused) (-305111) _rcConnect: connectToRhost failed\r\n', '  - iadmin moduser mjs password 12345678\r\n', 'ERROR: _rcConnect: connectToRhost error, server on users.local.org:0 is probably down status = -305111 USER_SOCK_CONNECT_ERR, Connection refused\r\n', 'ERROR: rcConnect failure USER_SOCK_CONNECT_ERR (Connection refused) (-305111) _rcConnect: connectToRhost failed\r\n', '  - ichmod -rM own wwwHydroProxy#hydroshareZone /hydroshareuserZone/home\r\n', 'ERROR: _rcConnect: connectToRhost error, server on users.local.org:0 is probably down status = -305111 USER_SOCK_CONNECT_ERR, Connection refused\r\n', '  - ichmod -rM inherit /hydroshareuserZone/home/mjs\r\n', 'ERROR: _rcConnect: connectToRhost error, server on users.local.org:0 is probably down status = -305111 USER_SOCK_CONNECT_ERR, Connection refused\r\n']
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] [chan 0] EOF sent (0)
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] Dropping user packet because connection is dead.
[22/Oct/2016 01:37:16] DEBUG [paramiko.transport:282] Dropping user packet because connection is dead.
```
