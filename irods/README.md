## Using local federated iRODS

The scripts herein are a one-way street that update the configuration of HydroShare to use a locally deployed federated pair 
of iCAT v.4.1.8 servers in Docker.

Effected files:
-	modified:   hsctl
-	modified:   hydroshare/local_settings.py
-	modified:   scripts/templates/docker-compose-local-irods.template

### How to use

Generate a `local_settings.py` file by copying `hydroshare/local_settings.template` to `hydroshare/local_settings.py`

From within the `irods` directory, run the script named **use-local-irods.sh**

**NOTE:** This script requires that package `jq` be installed on the host from which the script is being run. If it's not present it can be installed by invoking `sudo apt-get install jq` in Ubuntu (or similar) environments. 

```bash
$ cd irods
$ ./use-local-irods.sh
```

  - Optionally the user can choose to persist the iRODS vault and datbase to their local filesystem so that these files would be available even if the containers are destroyed and recreated.

  ```bash
  $ cd irods
  $ ./use-local-irods.sh --persist
  ```
  The `--persist` flag will create two new directories as `/home/${USER}/icat1` and `/home/${USER}/icat2` where iRODS vault and database files will be persisted. These directories will remain in place until the user manually destroys them.

The script will run, deploy and federate two iCAT servers, and modify the three aforementioned files to be configured to use the 
newly created iRODS Docker servers. Once the script has completed, return back the the main `hydroshare` directory and run
the **hsctl** script as you normally would.

```bash
$ cd ../
$ ./hsctl rebuild --db
```

Subsequent runs may require a git checkout of the three effected files since there is no guarantee that the internal Docker IP addresses originally assigned to the containers will reused each time. 

Example:

```bash
$ git checkout hsctl hydroshare/local_settings.py scripts/templates/docker-compose-local-irods.template
```

### In Docker

If all deploys as it should you will see this reflected in the `docker ps` output. As an example:

```
$ docker ps
CONTAINER ID        IMAGE                               COMMAND                  CREATED             STATUS              PORTS                                                                                 NAMES
5af966576bff        hydroshare_defaultworker            "/bin/bash init-defau"   17 minutes ago      Up 9 minutes                                                                                              defaultworker
7047505e0374        hydroshare_hydroshare               "/bin/bash init-hydro"   17 minutes ago      Up 9 minutes        0.0.0.0:8000->8000/tcp, 0.0.0.0:1338->2022/tcp                                        hydroshare
82aefa42b4f6        makuk66/docker-solr:4.10.4          "sh -c '/bin/bash /op"   17 minutes ago      Up 17 minutes       0.0.0.0:32786->8983/tcp                                                               solr
e67b799315ab        hydroshare/hs_postgres:9.4.7         "/docker-entrypoint.s"   17 minutes ago      Up 17 minutes       5432/tcp                                                                              postgis
52c67ebb6b57        rabbitmq:3.5                        "/docker-entrypoint.s"   17 minutes ago      Up 17 minutes       4369/tcp, 5671-5672/tcp, 25672/tcp                                                    rabbitmq
0b1a6c66a585        mjstealey/docker-irods-icat:4.1.8   "/irods-docker-entryp"   22 minutes ago      Up 22 minutes       1248/tcp, 5432/tcp, 20000-20199/tcp, 0.0.0.0:32785->22/tcp, 0.0.0.0:32784->1247/tcp   users.local.org
a4d976bcdeb7        mjstealey/docker-irods-icat:4.1.8   "/irods-docker-entryp"   22 minutes ago      Up 22 minutes       1248/tcp, 5432/tcp, 20000-20199/tcp, 0.0.0.0:32783->1247/tcp                          data.local.org
```

### Restarting after all containers have been stopped or host has been shutdown

It can be useful to retain the system state after all containers have been stopped or a system running HydroShare with local iRODS has been shutdown.

Assuming that the user has initially started with the `--persist` option, a normal initial deployment would look like this.

```bash
$ cd irods
$ ./use-local-irods.sh --persist
$ cd ../
$ ./hsctl rebuild --db
```
After some time the user could choose to stop all containers, or shut down the system they are running on.

```bash
$ docker stop $(docker ps -a -q)
```
To bring all containers back up, and to have the state of the local iRODS containers persisited, the user would do the following.

```bash
$ cd irods
$ ./use-local-irods.sh --persist
$ cd ../
$ ./hsctl start
```

This should recreate the HydroShare application as it was prior to beign stopped or shut down with all iRODS related information intact.

### Known issues at this time

None at this time
