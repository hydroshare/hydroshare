**xDCIShare Web Service API Design**

March 19, 2015

Version 1.0

Jeffery S. Horsburgh, Brian Miles, Dan Ames, Jefferson Heard

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [Introduction](#introduction)
- [Development Approach](#development-approach)
- [Authentication and Authorization](#authentication-and-authorization)
- [Web Service Interface Definitions](#web-service-interface-definitions)
  - [Resource Management API](#resource-management-api)
  - [User Management and Authorization API](#user-management-and-authorization-api)
  - [Resource Discovery API](#resource-discovery-api)
  - [Social API](#social-api)
  - [DataONE Member Node API](#dataone-member-node-api)
- [Acknowledgements](#acknowledgements)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


Introduction
============

xDCIShare will expose web service Application Programmer Interfaces (APIs) that support interaction between client applications and the main xDCIShare system and facilitate development of these client applications. xDCIShare will also expose web services that conform to the DataONE web service end-point specifications defined in the DataONE architectural documentation (DataONE, 2013). However compliance with DataONE data format specifications will not be guaranteed in the initial version of the xDCIShare API. Data format compliance would need to be added at a later date so that xDCIShare can become a DataONE Member Node as described in the xDCIShare Data Management Plan. As a design principle, the xDCIShare web service APIs will expose the same functionality that can be accomplished through the xDCIShare web user interface so that client applications can mimic that functionality.

Development Approach
====================

In general, xDCIShare web services will be implemented using a Representational State Transfer (REST) based approach using HTTP as the transport protocol and XML and/or JSON for encoding messages. The current development approach is investigating use of the Tastypie (<http://tastypieapi.org/>) web service API framework for the Django (<https://www.djangoproject.com/>) web framework.

Authentication and Authorization
================================

Many of the xDCIShare web service API functions require authorization. The xDCIShare web service APIs will use the same access control scheme as the xDCIShare web user interface. If a user is authorized to do something in the web interface, they will be authorized to do it via the web service APIs as well.

Web Service Interface Definitions
=================================

The following sections describe the xDCIShare web service APIs. The APIs will be versioned, and users will be able to specify the version number in the URL of their REST requests. In each section, a table lists the functions included in each API and then details of each function are given following the table. Note that API endpoints that rely on filtering are formatted according to TastyPie conventions. The formatting of such endpoints are subject to change to reflect the actual API implementation, which may not use TastyPie.

Resource Management API
-----------------------

The xDCIShare Resource Management API will enable client applications to create new resources, retrieve existing resources, get metadata for existing resources, update existing resources, publish resources, and delete resources. The table below lists the REST URLs that will be implemented as part of the xDCIShare Resource Management API.

Table 1. Summary of xDCIShare Resource Management API methods.

| **Release** | **REST Path**                           | **Function**                       | **Parameters**                  |
|-------------|-----------------------------------------|------------------------------------|---------------------------------|
| 1           | GET /resource/{pid}                     | xDCIShare.getResource()           | (pid) --\> OctetStream          |
| 1           | GET /scimeta/{pid}                      | xDCIShare.getScienceMetadata()    | (pid) --\> ScienceMetadata      |
| 1           | GET /sysmeta/{pid}                      | xDCIShare.getSystemMetadata()     | (pid) --\> SystemMetadata       |
| 1           | GET /resourcemap/{pid}                  | xDCIShare.getResourceMap()        | (pid) --\> ResourceMap          |
| 1           | GET /resource/{pid}/files/{filename}    | xDCIShare.getResourceFile()       | (pid, filename) --\> file       |
| 4           | GET /revisions/{pid}                    | xDCIShare.getRevisions()          | (pid) --\> ResourceList         |
| 4           | GET /related/{pid}                      | xDCIShare.getRelated()            | (pid) --\> ResourceList         |
| 1           | GET /checksum/{pid}                     | xDCIShare.getChecksum()           | (pid) --\> Checksum             |
| 1           | POST /resource                          | xDCIShare.createResource()        | (Resource) --\> pid             |
| 1           | PUT /resource/{pid}                     | xDCIShare.updateResource()        | (pid, Resource) --\> pid        |
| 1           | PUT /resource/{pid}/ files/{file}       | xDCIShare.addResourceFile()       | (pid, file) --\> pid            |
| 1           | PUT /scimeta/{pid}                      | xDCIShare.updateScienceMetadata() | (pid, ScienceMetadata) --\> pid |
| 1           | DELETE /resource/{pid}                  | xDCIShare.deleteResource()        | (pid) --\> pid                  |
| 1           | DELETE /resource/{pid}/files/{filename} | xDCIShare.deleteResourceFile()    | (pid, filename) --\> pid        |
| 4           | PUT /publishResource/{pid}              | xDCIShare.publishResource()       | (pid) --\> pid                  |
| 4           | GET /resolveDOI/{doi}                   | xDCIShare.resolveDOI()            | (doi) --\> pid                  |


### xDCIShare.getResource**(*pid*)* --\> OctetStream

Retrieve a resource identified by the pid from xDCIShare. The response must contain the bytes of the indicated resource, and the checksum of the bytes retrieved should match the checksum recorded in the system metadata for that resource. The bytes of the resource will be encoded as a zipped BagIt archive; this archive will contain resource contents as well as science metadata. If the resource does not exist in xDCIShare, then Exceptions.NotFound must be raised. Resources can be any unit of content within xDCIShare that has been assigned a pid.

**REST URL**: GET /resource/{pid}

**Parameters**: pid – Unique xDCIShare identifier for the resource to be retrieved.

**Returns**: Bytes of the specified resource.

**Return Type**: OctetStream

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request

**Notes**: All resources and resource versions will have a unique internal xDCIShare identifier (pid). A DOI will be assigned to all formally published versions of a resource. For this method, passing in a pid (which is a xDCIShare internal identifer) would return a specific resource version corresponding to the pid. A DOI would have to be resolved using xDCIShare.resolveDOI() to get the pid for the resource, which could then be used with this method. The obsoletion chain will be contained within the system metadata for resources and so it can be traversed by calling xDCIShare.getSystemMetadata().


### xDCIShare.getScienceMetadata**(*pid*)* --\> ScienceMetadata

Describes the resource identified by the pid by returning the associated science metadata object. If the resource does not exist, Exceptions.NotFound must be raised.

**REST URL**: GET /scimeta/{pid}

**Parameters**: pid – Unique xDCIShare identifier for the resource whose science metadata is to be retrieved.

**Returns**: Science metadata XML document describing the resource.

**Return Type**: ScienceMetadata

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.getSystemMetadata**(*pid*)* --\> SystemMetadata

Describes the resource identified by the pid by returning the associated system metadata object. If the resource does not exist, Exceptions.NotFound must be raised.

**REST URL**: GET /sysmeta/{pid}

**Parameters**: pid – Unique xDCIShare identifier for the resource whose system metadata is to be retrieved.

**Returns**: System metadata XML document describing the resource.

**Return Type**: SystemMetadata

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.getResourceMap**(*pid*)* --\> ResourceMap

Describes the resource identified by the pid by returning the associated resource map document. If the resource does not exist, Exceptions.NotFound must be raised.

**REST URL**: GET /resourcemap/{pid}

**Parameters**: pid – Unique xDCIShare identifier for the resource whose resource map is to be retrieved.

**Returns**: Resource map XML document describing the resource.

**Return Type**: ResourceMap

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.getResourceFile**(*pid*, *filename*)* --\> file

Called by clients to get an individual file within a xDCIShare resource.

**REST URL**: GET /resource/{pid}/files/{filename}

**Parameters**: pid – Unique xDCIShare identifier for the resource from which the file will be extracted.

filename – The data bytes of the file that will be extracted from the resource identified by pid

**Returns**: The bytes of the file extracted from the resource, with MIME type corresponding to filename extension.

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist or the file identified by filename does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.getRevisions**(*pid*)* --\> List of pids

Returns a list of pids for resources that are revisions of the resource identified by the specified pid.

**REST URL**: GET /revisions/{pid}

**Parameters**: pid – Unique xDCIShare identifier for the resource whose revisions are to be retrieved.

**Returns**: List of pids for resources that are revisions of the specified resource.

**Return Type**: List of pids

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The Resource identified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.getRelated**(*pid*)* --\> List of pids

Returns a list of pids for resources that are related to the resource identified by the specified pid.

**REST URL**: GET /related/{pid}

**Parameters**: pid – Unique xDCIShare identifier for the resource whose related resources are to be retrieved.

**Returns**: List of pids for resources that are related to the specified resource.

**Return Type**: List of pids

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.getChecksum**(*pid*)* --\> Checksum

Returns a checksum for the specified resource using the MD5 algorithm. The result is used to determine if two instances referenced by a pid are identical.

**REST URL**: GET /checksum/{pid}

**Parameters**: pid – Unique xDCIShare identifier for the resource for which the checksum is to be returned.

**Returns**: Checksum of the resource identified by pid.

**Return Type**: Checksum

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource specified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.createResource**(*resource*)* --\> pid

Called by a client to add a new resource to xDCIShare. The caller must have authorization to write content to xDCIShare. The pid for the resource is assigned by xDCIShare upon inserting the resource.  The create method returns the newly-assigned pid.

**REST URL**: POST /resource

**Parameters**: resource – The data bytes of the resource, encoded as a zipped BagIt archive, to be added to xDCIShare

**Returns**: The pid assigned to the newly created resource

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized to write to xDCIShare

Exceptions.InvalidContent – The content of the resource is incomplete

Exception.ServiceFailure – The service is unable to process the request

**Note**: The calling user will automatically be set as the owner of the created resource.


### xDCIShare.updateResource**(*pid*, *resource*)* --\> pid

Called by clients to update a resource in xDCIShare.

**REST URL**: PUT /resource/{pid}

**Parameters**: pid – Unique xDCIShare identifier for the resource that is to be updated.

resource – The data bytes of the resource, encoded as a zipped BagIt archive, that will update the existing resource identified by pid

**Returns**: The pid assigned to the updated resource

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.InvalidContent – The content of the resource is incomplete

Exception.ServiceFailure – The service is unable to process the request

**Notes**: For mutable resources (resources that have not been formally published), the update overwrites existing data and metadata using the resource that is passed to this method. If a user wants to create a copy or modified version of a mutable resource this should be done using xDCIShare.createResource().

For immutable resources (formally published resources), this method creates a new resource that is a new version of the formally published resource. xDCIShare will record the update by storing the SystemMetadata.obsoletes and SystemMetadata.obsoletedBy fields for the respective resources in their system metadata. xDCIShare MUST check or set the values of SystemMetadata.obsoletes and SystemMetadata.obsoletedBy so that they accurately represent the relationship between the new and old objects. xDCIShare MUST also set SystemMetadata.dateSysMetadataModified. The modified system metadata entries must then be available in xDCIShare.listObjects() to ensure that any cataloging systems pick up the changes when filtering on SystmeMetadata.dateSysMetadataModified. A formally published resource can only be obsoleted by one newer version. Once a resource is obsoleted, no other resources can obsolete it.


### xDCIShare.addResourceFile**(*pid*, *file*)* --\> pid

Called by clients to update a resource in xDCIShare by adding a single file.

**REST URL**: PUT /resource/{pid}/files/{file}

**Parameters**: pid – Unique xDCIShare identifier for the resource that is to be updated.

file – The data bytes of the file that will be added to the existing resource identified by pid

**Returns**: The pid assigned to the updated resource

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.InvalidContent – The content of the file is invalid

Exception.ServiceFailure – The service is unable to process the request

**Notes**: For mutable resources (resources that have not been formally published), the update adds the file that is passed to this method to the resource. For immutable resources (formally published resources), this method creates a new resource that is a new version of the formally published resource. xDCIShare will record the update by storing the SystemMetadata.obsoletes and SystemMetadata.obsoletedBy fields for the respective resources in their system metadata. xDCIShare MUST check or set the values of SystemMetadata.obsoletes and SystemMetadata.obsoletedBy so that they accurately represent the relationship between the new and old objects. xDCIShare MUST also set SystemMetadata.dateSysMetadataModified. The modified system metadata entries must then be available in xDCIShare.listObjects() to ensure that any cataloging systems pick up the changes when filtering on SystmeMetadata.dateSysMetadataModified. A formally published resource can only be obsoleted by one newer version. Once a resource is obsoleted, no other resources can obsolete it.


### xDCIShare.updateScienceMetadata**(*pid, ScienceMetadata*)* --\> pid

Called by clients to update the science metadata for a resource in xDCIShare.

**REST URL**: PUT /scimeta/{pid}

**Parameters**: pid – Unique xDCIShare identifier for the resource that is to be updated.

ScienceMetadata – The data bytes of the XML ScienceMetadata that will update the existing Science Metadata for the resource identified by pid

**Returns**: The pid assigned to the resource whose Science Metadata was updated

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.InvalidContent – The content of the resource is incomplete

Exception.ServiceFailure – The service is unable to process the request

**Notes**: For mutable resources (resources that have not been formally published), the update overwrites existing Science Metadata using the ScienceMetadata that is passed to this method. For immutable resources (formally published resources), this method creates a new resource that is a new version of the formally published resource. xDCIShare will record the update by storing the SystemMetadata.obsoletes and SystemMetadata.obsoletedBy fields for the respective resources in their system metadata. xDCIShare MUST check or set the values of SystemMetadata.obsoletes and SystemMetadata.obsoletedBy so that they accurately represent the relationship between the new and old objects. xDCIShare MUST also set SystemMetadata.dateSysMetadataModified. The modified system metadata entries must then be available in xDCIShare.listObjects() to ensure that any cataloging systems pick up the changes when filtering on SystmeMetadata.dateSysMetadataModified. A formally published resource can only be obsoleted by one newer version. Once a resource is obsoleted, no other resources can obsolete it.


### xDCIShare.deleteResource**(*pid*)* --\> pid

Deletes a resource managed by xDCIShare. The caller must be an owner of the resource or an administrator to perform this function. The operation removes the resource from further interaction with xDCIShare services and interfaces. The implementation may delete the resource bytes, and should do so since a delete operation may be in response to a problem with the resource (e.g., it contains malicious content, is inappropriate, or is subject to a legal request). If the resource does not exist, the Exceptions.NotFound exception is raised.

**REST URL**: DELETE /resource/{pid}

**Parameters**: pid – The unique xDCIShare identifier of the resource to be deleted

**Returns**: The pid of the resource that was deleted

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request

**Note**: Only xDCIShare administrators will be able to delete formally published resources.


### xDCIShare.deleteResourceFile**(*pid, filename*)* --\> pid

Deletes an individual file from a xDCIShare resource. If the file does not exist, the Exceptions.NotFound exception is raised.

**REST URL**: DELETE /resource/{pid}/files/{filename}

**Parameters**: pid – The unique xDCIShare identifier for the resource from which the file will be deleted

filename – Name of the file to be deleted from the resource

**Returns**: The pid of the resource from which the file was deleted

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist or the file identified by file does not exist

Exception.ServiceFailure – The service is unable to process the request

**Note**: For mutable resources (resources that have not been formally published), this method modifies the resource by deleting the file. For immutable resources (formally published resources), this method creates a new resource that is a new version of the formally published resource. xDCIShare will record the update by storing the SystemMetadata.obsoletes and SystemMetadata.obsoletedBy fields for the respective resources in their system metadata. xDCIShare MUST check or set the values of SystemMetadata.obsoletes and SystemMetadata.obsoletedBy so that they accurately represent the relationship between the new and old objects. xDCIShare MUST also set SystemMetadata.dateSysMetadataModified. The modified system metadata entries must then be available in xDCIShare.listObjects() to ensure that any cataloging systems pick up the changes when filtering on SystemMetadata.dateSysMetadataModified. A formally published resource can only be obsoleted by one newer version. Once a resource is obsoleted, no other resources can obsolete it.


### xDCIShare.publishResource**(*pid*)* --\> pid

Formally publishes a resource in xDCIShare. Triggers the creation of a DOI for the resource, and triggers the exposure of the resource to the xDCIShare DataONE Member Node. The user must be an owner of a resource or an adminstrator to perform this action.

**REST URL**: PUT /publishResource/{pid}

**Parameters**: pid – Unique xDCIShare identifier for the resource to be formally published.

**Returns**: The pid of the resource that was published

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request

**Note**: This is different than just giving public access to a resource via access control rules.


### xDCIShare.resolveDOI**(*doi*)* --\> pid

Takes as input a DOI and returns the internal xDCIShare identifier (pid) for a resource. This method will be used to get the xDCIShare pid for a resource identified by a doi for further operations using the web service API.

**REST URL**: GET /resolveDOI/{doi}

**Parameters**: doi – A doi assigned to a resource in xDCIShare.

**Returns**: The pid of the resource that was published

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request

**Note**: All xDCIShare methods (except this one) will use xDCIShare internal identifiers (pids). This method exists so that a program can resolve the pid for a DOI.


User Management and Authorization API
-------------------------------------

The User Management and Authorization API will enable client applications to set access rules and ownership for resources, create and update user accounts, create and update groups, get information about users or groups, and retrieve lists of resources associated with users and groups. The table below lists the REST URLs that will be implemented as part of the xDCIShare User Management and Authorization API. The following assume that each Resource has a single owner. However other users can be given “Full” permissions with all of the privileges of ownership. A single owner is needed for the purpose of disk space quotas so that a Resource only counts against the quota of one user. In all other respects, a user with “Full” permissions over a resource and an owner as described below are the same.

Table 2. xDCIShare user management and authorization API URLs and methods.

| **Release** | **REST Path**                                                                                                                      | **Function**                  | **Parameters**                                            |
|-------------|------------------------------------------------------------------------------------------------------------------------------------|-------------------------------|-----------------------------------------------------------|
| 1           | PUT /resource/owner/{pid}?user={userID}                                                                                            | xDCIShare.setResourceOwner() | (pid, userID) --\> pid                                    |
| 1           | PUT /resource/accessRules/{pid}/?principaltype=(user|group)&principleID={id}&access=(edit|view|donotdistribute)&allow=(true|false) | xDCIShare.setAccessRules()   | (pid, principalType, principleID, access, allow) --\> pid |
| 1           | POST /accounts                                                                                                                     | xDCIShare.createAccount()    | (user) --\> userID                                        |
| 1           | PUT /accounts/{userID}                                                                                                             | xDCIShare.updateAccount()    | (userID, user) --\> userID                                |
| 1           | GET /accounts/{userID}                                                                                                             | xDCIShare.getUserInfo()      | (userID) --\> user                                        |
| 1           | GET /accounts?query={query}[&status={status}&start={start}&count={count}]                                                          | xDCIShare.listUsers()        | (query, status, start, count) --\> userList               |
| 1           | GET /group/{groupID}                                                                                                               | xDCIShare.getGroupInfo()     | (groupID) --\> group                                      |
| 1           | GET /groups?query={query}[&status={status}&start={start}&count={count}]                                                            | xDCIShare.listGroups()       | (query, status, start, count) --\> groupList              |
| 1           | POST /groups                                                                                                                       | xDCIShare.createGroup()      | (group) --\> groupID                                      |
| 1           | PUT /groups                                                                                                                        | xDCIShare.updateGroup()      | (groupID, group) --\> groupID                             |
| 1           | PUT /groups/{groupID}/owner/?user={userID}                                                                                         | xDCIShare.setGroupOwner()    | (groupID, userID) --\> groupID                            |
| 1           | DELETE /groups/{groupID}/owner/?user={userID}                                                                                      | xDCIShare.deleteGroupOwner() | (groupID, userID) --\> groupID                            |
| 1           | GET /resourceList?groups\_\_contains={groupID}                                                                                     | xDCIShare.getResourceList()  | (queryType, groupID) --\> resourceList                    |
| 1           | GET /resourceList?creator={userID}                                                                                                 | xDCIShare.getResourceList()  | (queryType, userID) --\> resourceList                     |
| 1           | GET /resourceList?sharedWith={userID}                                                                                              | xDCIShare.getResourceList()  | (queryType, userID) --\> resourceList                     |
| 1           | GET /resourceList?creationDate\_\_range={fromDate},{toDate}                                                                        | xDCIShare.getResourceList()  | (queryType, fromDate, toDate) --\> resourceList           |


### xDCIShare.setResourceOwner**(*pid, userID*)* --\> pid

Changes ownership of the specified resource to the user specified by a userID.

**REST URL**: PUT /resource/owner/{pid}?user={userID}

**Parameters**: pid – Unique xDCIShare identifier for the resource to be modified

userID – ID for the user to be set as an owner of the resource identified by pid

**Returns**: The pid of the resource that was modified

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request

**Note**: This can only be done by the resource owner or a xDCIShare administrator.


### xDCIShare.setAccessRules**(*pid, principalType, principalID, access, allow*)* --\> pid

Set the access permissions for an object identified by pid. Triggers a change in the system metadata. Successful completion of this operation in indicated by a HTTP response of 200. Unsuccessful completion of this operation must be indicated by returning an appropriate exception such as NotAuthorized.

**REST URL**: PUT /resource/accessRules/{pid}/?principaltype=(user|group)&principleID={id}&access=(edit|view|donotdistribute)&allow=(true|false)

**Parameters**: pid – Unique xDCIShare identifier for the resource to be modified

principalType – The type of principal (user or group)

principalID – Identifier for the user or group to be granted access

access – Permission to be assigned to the resource for the principal

allow – True for granting the permission, False to revoke

**Returns**: The pid of the resource that was modified

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exceptions.NotFound – The principal identified by principalID does not exist

Exception.ServiceFailure – The service is unable to process the request

**Note**: “Do not distribute” is an attribute of the resource that is set by a user with “Full” permissions and only applies to users with “Edit” and “View” privileges. There is no “share” privilege in xDCIShare. Share permission is implicit unless prohibited by the “Do not distribute” attribute. The only permissions in xDCIShare are “View”, “Edit” and “Full”.


### xDCIShare.createAccount**(*user*)* --\> userID

Create a new user within the xDCIShare system.

**REST URL**: POST /accounts

**Parameters**: user – An object containing the attributes of the user to be created

**Returns**: The userID of the user that was created

**Return Type**: userID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.InvalidContent – The content of the user object is invalid

Exception.ServiceFailure – The service is unable to process the request

**Note**: This would be done via a JSON object (user) that is in the POST request. Should set a random password, and then send an email to make them verify the account. Unverified accounts can't login and are automatically deleted after a specified time (according to policy).


### xDCIShare.updateAccount**(*userID, user*)* --\> userID

Update an existing user within the xDCIShare system. The user calling this method must have write access to the account details.

**REST URL**: PUT /accounts/{userID}

**Parameters**: userID – ID of the existing user to be modified

user – An object containing the modified attributes of the user to be modified

**Returns**: The userID of the user that was modified

**Return Type**: userID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The user identified by userID does not exist

Exceptions.InvalidContent – The content of the user object is invalid

Exception.ServiceFailure – The service is unable to process the request

**Note**: This would be done via a JSON object (user) that is in the PUT request.


### xDCIShare.getUserInfo**(*userID*)* --\> user

Get the information about a user identified by userID. This would be their profile information, groups they belong to, etc.

**REST URL**: GET /accounts/{userID}

**Parameters**: userID – ID of the existing user to be modified

**Returns**: An object containing the details for the user

**Return Type**: user

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The user identified by userID does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.listUsers**(*query, status, start, count*)* --\> userList

List the users that match search criteria.

**REST URL**: GET /accounts?query={query}[&status={status}&start={start}&count={count}]

**Parameters**: query – a string specifying the query to perform

status – (optional) parameter to filter users returned based on status

start=0 – (optional) the zero-based index of the first value, relative to the first record of the resultset that matches the parameters

count=100 – (optional) the maximum number of results that should be returned in the response

**Returns**: An object containing a list of userIDs that match the query. If none match, an empty list is returned.

**Return Type**: userList

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.getGroupInfo**(*groupID*)* --\> group

Get the information about a group identified by groupID. For a group this would be its description and membership list.

**REST URL**: GET /group/{groupID}

**Parameters**: groupID – ID of the existing user to be modified

**Returns**: An object containing the details for the group

**Return Type**: group

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The group identified by groupID does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.listGroups**(*query, status, start, count*)* --\> groupList

List the groups that match search criteria.

**REST URL**: GET /groups?query={query}[&status={status}&start={start}&count={count}]

**Parameters**: query – a string specifying the query to perform

status – (optional) parameter to filter groups returned based on status

start=0 – (optional) the zero-based index of the first value, relative to the first record of the resultset that matches the parameters

count=100 – (optional) the maximum number of results that should be returned in the response

**Returns**: An object containing a list of groupIDs that match the query. If none match, an empty list is returned.

**Return Type**: groupList

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.createGroup**(*group*)* --\> groupID

Create a group within xDCIShare. Groups are lists of users that allow all members of the group to be referenced by listing solely the name of the group. Group names must be unique within xDCIShare. Groups can only be modified by users listed as group owners.

**REST URL**: POST /groups

**Parameters**: group – An object containing the attributes of the group to be created

**Returns**: The groupID of the group that was created

**Return Type**: groupID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.InvalidContent – The content of the group object is invalid

Exceptions.GroupNameNotUnique – The name of the group already exists in xDCIShare

Exception.ServiceFailure – The service is unable to process the request

**Note**: This would be done via a JSON object (group) that is in the POST request. May want to add an email verification step to avoid automated creation of fake groups. The creating user would automatically be set as the owner of the created group.


### xDCIShare.updateGroup**(*groupID, group*)* --\> groupID

Modify details of group identified by groupID or add or remove members to/from the group. Group members can be modified only by an owner of the group, otherwise a NotAuthorized exception is thrown. Group members are provided as a list of users that replace the group membership.

**REST URL**: PUT /groups/{groupID}

**Parameters**: groupID – groupID of the existing group to be modified

group – An object containing the modified attributes of the group to be modified and the modified list of userIDs in the group membership

**Returns**: The groupID of the group that was modified

**Return Type**: groupID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The group identified by groupID does not exist

Exceptions.InvalidContent – The content of the group object is invalid

Exception.ServiceFailure – The service is unable to process the request

**Note**: This would be done via a JSON object (group) that is in the PUT request.


### xDCIShare.setGroupOwner**(*groupID, userID*)* --\> groupID

Adds ownership of the group identified by groupID to the user specified by userID. This can only be done by a group owner or xDCIShare administrator.

**REST URL**: PUT /groups/{groupID}/owner/?user={userID}

**Parameters**: groupID – groupID of the existing group to be modified

userID – userID of the existing user to be set as the owner of the group

**Returns**: The groupID of the group that was modified

**Return Type**: groupID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The group identified by groupID does not exist

Exceptions.NotFound – The user identified by userID does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.deleteGroupOwner**(*groupID, userID*)* --\> groupID

Removes a group owner identified by a userID from a group specified by groupID. This can only be done by a group owner or xDCIShare administrator.

**REST URL**: DELETE /groups/{groupID}/owner/?user={userID}

**Parameters**: groupID – groupID of the existing group to be modified

userID – userID of the existing user to be removed as the owner of the group

**Returns**: The groupID of the group that was modified

**Return Type**: groupID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The group identified by groupID does not exist

Exceptions.NotFound – The user identified by userID does not exist

Exceptions.InvalidRequest – The request would result in removal of the last remaining owner of the group

Exception.ServiceFailure – The service is unable to process the request

**Note**: A group must have at least one owner.


### xDCIShare.getResourceList**(*queryType, groupID*)* --\> resourceList

Return a list of pids for Resources that have been shared with a group identified by groupID.

**REST URL**: GET /resourceList?groups\_\_contains={groupID}

**Parameters**: queryType – string specifying the type of query being performed

groupID – groupID of the group whose list of shared resources is to be returned

**Returns**: A list of pids for resources that have been shared with the group identified by groupID. If no resources have been shared with a group, an empty list is returned.

**Return Type**: resourceList

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The group identified by groupID does not exist

Exception.ServiceFailure – The service is unable to process the request

**Note**: See http://django-tastypie.readthedocs.org/en/latest/resources.html\#basic-filtering for implementation details and example. We may want to modify this method to return more than just the pids for resources so that some metadata for the list of resources returned could be displayed without having to call xDCIShare.getScienceMetadata() and xDCIShare.GetSystemMetadata() for every resource in the returned list.


### xDCIShare.getResourceList**(*queryType, userID*)* --\> resourceList

Return a list of pids for Resources that a user identified by userID has created.

**REST URL**: GET /resourceList?creator={userID}

**Parameters**: queryType – string specifying the type of query being performed

userID – userID of the user whose list of created resources is to be returned

**Returns**: A list of pids for resources that have been created by the user. If no resources have been created by the user, an empty list is returned.

**Return Type**: resourceList

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The user identified by userID does not exist

Exception.ServiceFailure – The service is unable to process the request

**Note**: See http://django-tastypie.readthedocs.org/en/latest/resources.html\#basic-filtering for implementation details and example. We may want to modify this method to return more than just the pids for resources so that some metadata for the list of resources returned could be displayed without having to call xDCIShare.getScienceMetadata() and xDCIShare.GetSystemMetadata() for every resource in the returned list.


### xDCIShare.getResourceList**(*queryType, userID*)* --\> resourceList

Return a list of pids for Resources that have been shared with a user identified by userID.

**REST URL**: GET /resourceList?sharedWith={userID}

**Parameters**: queryType – string specifying the type of query being performed

userID – userID of the user whose list of shared resources is to be returned

**Returns**: A list of pids for resources that have been shared with the user. If no resources have been shared with the user, an empty list is returned.

**Return Type**: resourceList

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The user identified by userID does not exist

Exception.ServiceFailure – The service is unable to process the request

**Note**: See http://django-tastypie.readthedocs.org/en/latest/resources.html\#basic-filtering for implementation details and example. We may want to modify this method to return more than just the pids for resources so that some metadata for the list of resources returned could be displayed without having to call xDCIShare.getScienceMetadata() and xDCIShare.GetSystemMetadata() for every resource in the returned list.


### xDCIShare.getResourceList**(*queryType, fromDate, toDate*)* --\> resourceList

Return a list of pids for Resources whose creation date lies within the specified range.

**REST URL**: GET /resourceList?creationDate\_\_range={fromDate},{toDate}

**Parameters**: queryType – string specifying the type of query being performed

fromDate – the beginning date for the date range

toDate – the ending date for the date range

**Returns**: A list of pids for resources that were created within the given date range. If no resources were created within the given date range, an empty list is returned.

**Return Type**: resourceList

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.InvalidDateRange – The date range provided by the user is invalid

Exception.ServiceFailure – The service is unable to process the request

**Note**: See http://django-tastypie.readthedocs.org/en/latest/resources.html\#basic-filtering for implementation details and example. We may want to modify this method to return more than just the pids for resources so that some metadata for the list of resources returned could be displayed without having to call xDCIShare.getScienceMetadata() and xDCIShare.GetSystemMetadata() for every resource in the returned list.


Resource Discovery API
----------------------

The table below lists the REST URLs that will be implemented as part of the xDCIShare Resource Discovery API.

Table 3. xDCIShare resource discovery API URLs and methods.

| **Release** | **REST Path**                                                                                                      | **Function**                   | **Parameters**                                                   |
|-------------|--------------------------------------------------------------------------------------------------------------------|--------------------------------|------------------------------------------------------------------|
| 2           | GET /resourceList [?fromDate={fromDate}&toDate={toDate} &resourceType={resourceType} &start={start}&count={count}] | xDCIShare.listResources()     | (fromDate, toDate, resourceType, start, count) --\> resourceList |
| 2           | GET /resourceTypes                                                                                                 | xDCIShare.listResourceTypes() | () --\> resourceTypeList                                         |
| 2           | GET /formats                                                                                                       | xDCIShare.listFormats()       | () --\> resourceFormatList                                       |
| 2           | GET /search/{queryType}/{query}                                                                                    | xDCIShare.search()            | (queryType, query) --\> resourceList                             |
| 2           | GET /search                                                                                                        | xDCIShare.listSearchEngines() | () --\> searchEngineList                                         |


### xDCIShare.listResources**(*fromDate, toDate, resourceType, start, count*)* --\> resourceList

Return a list of pids for Resources whose creation date lies within the specified range, and optionally are of a particular resource type. This method is required to support cataloging of resources contained within xDCIShare.

**REST URL**: GET /resourceList [?fromDate={fromDate}&toDate={toDate} &resourceType={resourceType} &start={start}&count={count}]

**Parameters**: fromDate – (optional) the beginning date for the date range

toDate – (optional) the ending date for the date range

resourceType – (optional) a type of resource for which to return results

start=0 – (optional) the zero-based index of the first value, relative to the first record of the resultset that matches the parameters

count=100 – (optional) the maximum number of results that should be returned in the response

**Returns**: A list of pids for resources that meet the given criteria. If no resources meet the criteria, an empty list is returned.

**Return Type**: resourceList

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exception.ServiceFailure – The service is unable to process the request

**Note**: This method is primarily to support outside services that would want to harvest the xDCIShare metadata catalog.


### xDCIShare.listResourceTypes**()* --\> resourceTypeList

Returns a list of all resource types registered in the xDCIShare resource type vocabulary

**REST URL**: GET /resourceTypes

**Parameters**: None

**Returns**: A list of resourceTypes supported by xDCIShare

**Return Type**: resourceTypeList

**Raises**: Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.listFormats**()* --\> resourceFormatList

Returns a list of all resource formats registered in the xDCIShare resource format vocabulary

**REST URL**: GET /formats

**Parameters**: None

**Returns**: A list of resource formats supported by xDCIShare

**Return Type**: resourceFormatList

**Raises**: Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.search**(**queryType, query**)* --\> resourceList

Search the xDCIShare metadata catalog and return a list of pids for resources that match the search criteria. Search may be implemented using more than one type of search engine. The queryType parameter indicates which search engine should be targeted. The value and form of query is determined by the search engine.

**REST URL**: GET /search/{queryType}/{query}

**Parameters**: queryType – the search engine to be used for the search

query – a string containing the query to be executed on the search engine

**Returns**: A list of pids for resources that match the criteria in the query. If no resources match the query criteria, an empty list is returned.

**Return Type**: resourceList

**Raises**: Exception.InvalidQueryType – the query type is invalid

Exception.InvalidQuery – the query string is invalid

Exception.ServiceFailure – The service is unable to process the request

**Note**: We may want to modify this method to return more than just the pids for resources so that some metadata for the list of resources returned could be displayed without having to call xDCIShare.getScienceMetadata() and xDCIShare.GetSystemMetadata() for every resource in the returned list. ***Also, this method is still pending selection of the underlying metadata catalog and search engine(s).***


Social API
----------

The table below lists the REST URLs that will be implemented as part of the xDCIShare Social API.

Table 4. xDCIShare social API URLs and methods.

| **Release** | **REST Path**                                             | **Function**                      | **Parameters**                              |
|-------------|-----------------------------------------------------------|-----------------------------------|---------------------------------------------|
| 1           | POST /resource/endorse/{pid}/{userID}                     | xDCIShare.endorseResource()      | (pid, userID) --\> pid                      |
| 4           | POST /followUser/{userID}/{followerID}                    | xDCIShare.followUser()           | (userID, followerID) --\> userID            |
| 4           | DELETE /followUser/{userID}/{followerID}                  | xDCIShare.deleteFollowUser()     | (userID, followerID) --\> userID            |
| 4           | POST /followResource/{pid}/{followerID}                   | xDCIShare.followResource()       | (pid, followerID) --\> pid                  |
| 4           | DELETE /followResource/{pid}/{followerID}                 | xDCIShare.deleteFollowResource() | (pid, followerID) --\> pid                  |
| 4           | POST /followGroup/{groupID}/{followerID}                  | xDCIShare.followGroup()          | (groupID, followerID) --\> groupID          |
| 4           | DELETE /followGroup/{groupID}/{followerID}                | xDCIShare.deleteFollowGroup()    | (groupID, followerID) --\> groupID          |
| 1           | POST /resource/annotation/{pid}/{userID}                  | xDCIShare.annotateResource()     | (pid, annotation, userID) --\> annotationID |
| 1           | GET /resource/annotations/{pid}                           | xDCIShare.getAnnotations()       | (pid) --\> annotationList                   |
| 1           | POST /resource/annotation/endorse/{annotationID}/{userID} | xDCIShare.endorseAnnotation()    | (annotationID, userID) --\> annotationID    |


### xDCIShare.endorseResource**(*pid, userID*)* --\> pid

Create an endorsement or (+1) for a resource in xDCIShare identified by pid for the user identified by userID

**REST URL**: POST /resource/endorse/{pid}/{userID}

**Parameters**: pid – Unique xDCIShare identifier for the resource being endorsed

userID – userID of the user that is endorsing the resource identified by pid

**Returns**: The pid of the resource that was endorsed

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exceptions.NotFound – The user identified by userID does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.followUser**(*userID, followerID*)* --\> userID

Start following a xDCIShare user identified by userID.

**REST URL**: POST /followUser/{userID}/{followerID}

**Parameters**: userID – userID of the xDCIShare user to be followed

followerID – userID of the xDCIShare user requesting to follow the user identified by userID

**Returns**: The userID of the xDCIShare user being followed

**Return Type**: userID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The user identified by userID does not exist

Exceptions.NotFound – The user identified by followerID does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.deleteFollowUser**(*userID, followerID*)* --\> userID

Stop following a xDCIShare user identified by userID.

**REST URL**: DELETE /followUser/{userID}/{followerID}

**Parameters**: userID – userID of the xDCIShare user being followed

followerID – userID of the xDCIShare user following the user identified by userID

**Returns**: The userID of the xDCIShare user being followed

**Return Type**: userID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The user identified by userID does not exist

Exceptions.NotFound – The user identified by followerID does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.followResource**(*pid, followerID*)* --\> pid

Start following a xDCIShare resource identified by pid.

**REST URL**: POST /followResource/{pid}/{followerID}

**Parameters**: pid – Unique xDCIShare identifier for the resource to be followed

followerID – userID of the xDCIShare user requesting to follow the resource identified by pid

**Returns**: The pid of the xDCIShare resource being followed

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exceptions.NotFound – The user identified by followerID does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.deleteFollowResource**(*pid, followerID*)* --\> pid

Stop following a xDCIShare resource identified by pid.

**REST URL**: DELETE /followResource/{pid}/{followerID}

**Parameters**: pid – Unique xDCIShare identifier for the resource being followed

followerID – userID of the xDCIShare user following the resource identified by pid

**Returns**: The pid of the xDCIShare resource being followed

**Return Type**: pid

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exceptions.NotFound – The user identified by followerID does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.followGroup**(*groupID, followerID*)* --\> groupID

Start following a xDCIShare group identified by groupID.

**REST URL**: POST /followGroup/{groupID}/{followerID}

**Parameters**: groupID – Unique xDCIShare identifier for the group to be followed

followerID – userID of the xDCIShare user requesting to follow the group identified by groupID

**Returns**: The groupID of the xDCIShare group being followed

**Return Type**: groupID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The group identified by groupID does not exist

Exceptions.NotFound – The user identified by followerID does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.deleteFollowGroup**(*groupID, followerID*)* --\> groupID

Stop following a xDCIShare group identified by groupID.

**REST URL**: DELETE /followGroup/{groupID}/{followerID}

**Parameters**: groupID – Unique xDCIShare identifier for the group being followed

followerID – userID of the xDCIShare user following the group identified by groupID

**Returns**: The groupID of the xDCIShare group being followed

**Return Type**: groupID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The group identified by groupID does not exist

Exceptions.NotFound – The user identified by followerID does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.annotateResource**(*pid, annotation, userID, previousAnnotationID*)* --\> annotationID

Create a comment about a resource in xDCIShare identified by pid.

**REST URL**: POST /resource/annotation/{pid}/{userID}

**Parameters**: pid – Unique xDCIShare identifier for the resource being annotated
annotation – an object containing the annotation to be applied to the resource identified by pid
userID – userID of the xDCIShare user creating the annotation
previousAnnotationID - (optional) AnnotationID of the previous comment on this resource that this comment follows on from. If omitted the comment is a new comment on a resource.

**Returns**: The annotationID of the annotation that is created

**Return Type**: annotationID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exceptions.InvalidContent – The content of the annotation object is invalid

Exceptions.NotFound – The user identified by userID does not exist

Exception.ServiceFailure – The service is unable to process the request

Exceptions.NotFound - The previousAnnotationID is not an annotation of the resource identified by pid


### xDCIShare.getAnnotations**(*pid*)* --\> annotationList

Get the list of annotations for a resource identified by pid.

**REST URL**: GET /resource/annotations/{pid}

**Parameters**: pid – Unique xDCIShare identifier for the resource whose annotations are to be retrieved

**Returns**: An object containing a list of annotations that have been added to a xDCIShare resource identified by pid.

**Return Type**: annotationList

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The resource identified by pid does not exist

Exception.ServiceFailure – The service is unable to process the request


### xDCIShare.endorseAnnotation**(*annotationID, userID*)* --\> annotationID

Create an endorsement or (+1) by a user identified by userID for an annotation identified by annotationID.

**REST URL**: POST /resource/annotation/endorse/{annotationID}/{userID}

**Parameters**: annotationID – Unique xDCIShare identifier for the annotation to be endorsed

userID – userID of the xDCIShare user creating the annotation endorsement

**Returns**: The annotationID of the annotation that is endorsed

**Return Type**: annotationID

**Raises**: Exceptions.NotAuthorized – The user is not authorized

Exceptions.NotFound – The annotation identified by annotationID does not exist

Exceptions.NotFound – The user identified by userID does not exist

Exception.ServiceFailure – The service is unable to process the request

DataONE Member Node API
-----------------------

The xDCIShare Data Management Plan states that xDCIShare will implement the DataONE Member Node APIs and become a DataONE Member Node. Most of the methods in the previous sections have equivalent methods in the DataONE Member Node APIs. xDCIShare will have to implement that additional methods described in the DataONE API documentation to become a fully compliant DataONE Member Node (see [http://mule1.dataone.org/ArchitectureDocs-current/apis/MN\_APIs.html\#](http://mule1.dataone.org/ArchitectureDocs-current/apis/MN_APIs.html)).

Acknowledgements
================

This work was supported by the National Science Foundation under collaborative grants OCI-1148453 and OCI-1148090 for the development of xDCIShare (<http://www.hydroshare.org>). Any opinions, findings and conclusions or recommendations expressed in this material are those of the authors and do not necessarily reflect the views of the National Science Foundation.

DataONE (2013). DataONE APIs. <http://mule1.dataone.org/ArchitectureDocs-current/apis/index.html>.
