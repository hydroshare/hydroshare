## HydroShare migration

### Overview

Pre-migration preparation

- preDumpMigrationFiles
- dumpMigrationFiles
- postDumpMigrationFile

Migration

- configure target system
- preLoadMigrationFiles
- loadMigarionFiles
- postLoadMigrationFiles

Post-migration clean up

- target system validation
- iRODS AVU validation

### How To

Migrating from one system to another will require the use of iRODS iCommands, fuse and the hydroshare repository from Github. The version of each one of these should be based upon what is presently being used by the HydroShare application. There are a collection of scripts located in the `hydrosahre/migration-scripts` directory that should be used for performing various elements of the migration.

The system being migrated from will be referred to as the **Source**, and the system being migrated to will be referred to as the **Target**

The **Source** system should be running and in a stable state prior to attempting any kind of migration.

### Pre-migration


- Make an exact copy of the HydroShare resources stored in iRODS using iCommands `irsync`. This should performed from the location where you plan to hold the copy of the HydroShare resources as regular files.
	- Makes use of multiple iRODS user environments via the IRODS_ENVIRONMENT_FILE variable for the following:
		- `SOURCE_IRODS_USER` = iRODS proxy user of the Source
		- `TARGET_IRODS_USER` = iRODS proxy user of the Target
		- `MIGRATION_IRODS_USER` = iRODS proxy user for migration (for fuse mount)
		- It is possible for the **SOURCE** and **TARGET** iRODS users to be the same if migrating back to the same system. This case would involve a full purge of the iRODS vault inbetween the dump and load stages of migration.

	```
	IRODS_ENVIRONMENT_FILE=~/.irods/SOURCE_IRODS_USER.json irsync -r i:/SOURCE/VAULT/TO/COPY /LOCAL/COPY
	IRODS_ENVIRONMENT_FILE=~/.irods/MIGRATION_IRODS_USER.json irsync -r /LOCAL/COPY i:/MIGRATION/VAULT/FOR/FUSE/MOUNT
	# TODO: validator script for checksums of source and migration irods resources
	```

- Run the dump migration scripts from the **Source**.

	```
	cd migration-scripts
	./preDumpMigrationFiles
	cd ../
	./dumpMigrationFiles
	cd migration-scripts
	./postDumpMigrationFiles
	cd ../
	scp migration-files-MM-DD-YY.tar.gz http://LOCATION_ACCESSIBLE_TO_TARGET_BY_WGET/migration-files-MM-DD-YY.tar.gz
	```

### Migration

The **Target** system should have iRODS iCommands and fuse properly installed on it.

- Run the load migration scripts from the **Target**.
	
	```
	git clone https://github.com/hydroshare/hydroshare.git
	cd hydroshare
	# update config/hydroshare-config.yaml
	# update hydroshare/local_setting.py
	cd migration-scripts
	./preLoadMigrationFiles http://LOCATION_ACCESSIBLE_TO_TARGET_BY_WGET/migration-files-MM-DD-YY.tar.gz
	cd ../
	./LoadMigrationFiles
	cd migration-scripts
	./postLoadMigrationFiles
	```

### Clean up

- Validate the data migration between **Source** and **Target** systems
- Using iCommands, validate the resourece AVU metadata on the **Target** system

	```
	IRODS_ENVIRONMENT_FILE=~/.irods/TARGET_IRODS_USER.json ils
	# choose a /PATH/TO/RESOURCE to validate
	IRODS_ENVIRONMENT_FILE=~/.irods/TARGET_IRODS_USER.json imeta ls -C /PATH/TO/RESOURCE
	```
- Optionally delete the `migration-files-MM-DD-YY.tar.gz` file that is left in the main hydroshare directory.
