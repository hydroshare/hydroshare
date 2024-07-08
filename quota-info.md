# The HydrosShare quota system

The HS quota system relies on cooperation between iRods storage zones (two at this time) and the Django application.

## Current Implementation

### Django Quota System

The quota system relies on resource sizes.
Resource sizes are calculated as a sum of cached ResourceFile sizes.

Django signals are used to update the stored UserQuota values in the database.

The configuration for the quota system within django is done via the admin panel. The [QuotaMessage](theme/models.py) model contains the configurable messages as well as default grace period and soft/hard limits.

Quota is enforced at all points of ingestion as well as during file processes that can result in more storage being used (for instance unzipping).

Users can request additional quota allocation from within their profile. Such a request notifies **DEFAULT_SUPPORT_EMAIL** and the request can be approved/denied from within the sent email or within the HydroShare amdin panel.

User quota does not include storage for resource "bags". Separate processes are being developed to help reign-in bag storage. User quota also does not currently include storage used for published resources.


## Historical Perspective

The quota system used to rely on calculating file sizes using irods microservices and then storing aggregate values in irods metadata AVUs. This system is now deprecated. Notes are included here in case they prove handy to future generations.

A significant change in the quota implementation was made circa April 2024 when it was discovered that the existing iRods microservices were not capturing all filesystem CRUD activities (particularly those related to zipping). At that time, attempts were conducted to add PEP (enforcement points) into the existing microservices, unsuccessfully. Because quota had not previously been enforced, the deficiencies in the microservices went unnoticed for many eons. Because of these deficiencies, the irods quota AVU system was abandoned.

### Old Django Quota System

When an update is made in one of the iRods zones (ex `iput `), the irods microservices recalculate the quota for the user that "holds" the involved storage objecct(s). Once the microservices complete their calculation, they make a get request to [update_quota_usage](hs_core/hydroshare/resource.py). This kicks off a process to read the metadata AVUs within iRods, where the microservices have stored the calculated usage values for the user. These updated values are then used to update the according [UserQuota](theme/models.py) in the django database. At this time, the UserQuota is one-to-one with a user account.

The configuration for the quota system within django is done via the admin pane. The [QuotaMessage](theme/models.py) model contains the configurable messages as well as default grace period and soft/hard limits.

Quota is enforced at all points of ingestion as well as during file processes that can result in more storage being used (for instance unzipping). Enforcement for the iRods UserZone would necessarily be accomplished at the iRods level. An example stubbing-out of how this could be accomplished can be found in [set_userzone_quota.sh](irods/set_userzone_quota.sh). However, ideally such an implementation would rely either on the quota system embedded in iRods, or perhaps using policy/rule enforcement with more microservices specific to the UserZone.

Users can request additional quota allocation from within their profile. Such a request notifies **DEFAULT_SUPPORT_EMAIL** and the request can be approved/denied from within the sent email or within the HydroShare amdin panel.

User quota does not include storage for resource "bags". Separate processes are being developed to help reign-in bag storage.


### HydroShare Quota on iRODS Layer

#### 1. Introduction

The microservices are written in C/C++ and called on iRODS kernel layer without rodsAdmin permission. They manage all changes on a iRODS collection named: HydroShare Root Document Directory (HSRDD) which stores all HydroShare User Resource. Sub-collections of HSRDD are named: HydroShare User Resource Directory (HSURD). Each HSURD and all data stored on it could be owned by more than one HydroShare User but only one of them could be the quotaHolder.

Any new file created in any HSURD will be caught and its information is sent to a microservice of quota system in iRODS kernel. The microservice will detect who the quotaHolder of the new file is using a AVU named “quotaUserName” which is set in all HSURD(s) and adds the file size to the User Usage. A similar process will also run if a file is deleted. However, the called microservice will decrease the User Usage.

If the AVU which controls the maximum file-size usage of a HydroShare User is set to a positive value, a quota enforcement will be run with respect to that user. Otherwise, users could unlimitedly store on iRODS system.

In the first version (1.x), the system cannot work across multiple iRODS servers. The ability of working together of servers is done in Django layer to keep the system architecture simpler and clearer.

The source code of this system now is being managed on https://github.com/hydroshare/hydroshare-quota. 

#### 2. How it works

Whenever an object (e.g. a file, an user, an AVU...) is changed in iRODS, some RULE(s) will be called depending on what actually happened. All of them could be modified to adapt to the user requirements by a simple programming language named iRODS Rule-Oriented Language. Therefore, the HydroShare quota system will modify the following five default RULEs to catch some change(s) on iRODS server:

acDataDeletePolicy: will be called before a file is deleted
acPostProcForObjRename: will be called after a file is moved successfully to a new location (this PEP is temporary commented out)
acPostProcForCopy: will be called after a file is copied successfully to a new location
acPostProcForPut: will be called after a file is put successfully from local storage to iRODS
acPreProcForModifyAVUMetadata: will be called before an AVU setting is done in any iRODS object
acPostProcForModifyAVUMetadata: will be called after any AVU setting is done successfully

When a file is created

acPostProForCopy or acPostProcForPut will be called depending on how the file was created, as the follows:
(1) An user created a Resource on www.hydroshare.org; or
(2) An user upload a file to his iRODS user home directory by his iRODS native account; or
(3) An user used his iRODS native account to copy a file from his iRODS user zone to HydroShare zone.

In any case, the microservice “msiHSAddNewFile” will be called with these parameters:
$objPath: This is a system variable, which will be generated by iRODS kernel and store the full path on iRODS system of the new file. This variable could be accessed in most of RULEs. In the latest version, we detect the iRODS user name from this path then use this name for storing HydroShare user usage.

We use iRODS Collection to store all HydroShare User Usage on it. Usage(s) are stored as the value of AVU attributes. 

The HydroShare Bags Path: This parameter is used to determine which Collection is used to store all user usage. By default, its value is “/hydroshareZone/home/cuahsiDataProxy/bags” and it can be changed depending on the actual iRODS server configuration. Any changes inside of this path will be ignored.

An AVU name: This is the name of AVU which is used to store the quotaHolder of resource. By default, it is titled “quotaUserName”.

Server Role: By default, its value is “Federated”. If it’s “Federated”, microservices will calculate user usage in HydroShare Root Dir and iRODS user home directory. Otherwise, only HydroShare Root Dir is accounted.

When the msiHSAddNewFile is called, it does not know how a file was created: by (1), (2) or by (3). However, with the value of $objPath, the microservice can consecutively go upward until reaching the directory containing the AVU: “quotaUserName” or meeting the root directory. In the first case, the value of the Collection at the stopped-by position is the quotaHolder of the newly created file. The second one means that there is no quotaHolder of the created file.

UPDATED: In “Federated” Server, msiHSAddNewFile can detect a new file was created on HydroShare Root Dir or iRODS user home directory depend on the full path of the new file and the “bags” directory.

If the new file was created on iRODS user home directory, the directory name will be assigned to the quotaHolder.

After the quotaHolder was detected, his/her usage would be easily increased by adding the size of the new file to the value of the AVU “<quotaHolder’s name>-usage”

If there is an error while a file is being put/copied, either acPostProcForCopy or acPostProcForPut will not be called.

When a file is removed

When a file is deleted, the acDataDeletePolicy RULE will be called by iRODS kernel. It calls the msiHSRemoveFile and this microservice will carry out a similar process to the msiHSAddNewFile except subtraction of the file size of deleted file.

When an AVU “quotaUserName” or “resetQuotaDir” is set

The acPostProcForModifyAVUMetadata would be called when any AVU value of an Object is set/added/modified or removed successfully. In our case, this RULE was modified to catch only one of the two following events: 
There is a change in the AVU named “quotaUserName”. This change is setting or adding a new AVU value on a directory; or
There is an change in the AVU named “resetQuotaDir”. This change is setting or adding a new AVU value on a directory.

We don’t catch “modified” or “removed” action in this RULE.

If an AVU “quotaUserName” is set on a directory, that means we have a new quotaHolder on this directory. Thus, the msiHSAddQuotaHolder will be called to compute the size of the directory, and then add the size to the AVU which has been storing the quotaHolder Usage. The size of the directory is the total of all file size on it (including all subdirectories).

If an AVU “resetQuotaDir” is set (in any iRODS objects except “bags” and inside “bags”), that means all HydroShare User Usage need to be re-computed by the msiHSResetQuotaDir microservice. This function should be very useful when this quota component is installed on an iRODS server which already has HydroShare data. It also needs to recalculate User Usage in systems which sometimes have bugs.

When an AVU “quotaUserName” is removed

The acPreProcForModifyAVUMetadata would be called BEFORE any AVU value of an Object is set/added/modified or removed. In our case, this RULE was modified to catch only one event: 
There is a change in the AVU named “quotaUserName”. This change is removing current value from a directory.

Thus, the msiHSRemoveQuotaHolder will be called to calculate the size of the directory, and then subtract the size from the AVU which has stored the quotaHolder Usage. The size of the directory is the total of all file size on it (including all subdirectories).
