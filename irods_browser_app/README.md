# iRODS browser in HydroShare #

Author: Hong Yi

### irods_browser implementation in HydroShare that was repurposed from iPlant geonode-irods application developed by Amit Juneja ###

The HydroShare app that allows a user to login to iRODS and browse iRODS collections and data objects from a specified zone
and select a data object to download from the specified iRODS zone and upload to HydroShare Django to create a HydroShare resource.
Irods python client API is used to retrieve collection and data objects for browsing, and the actual data transfer is done using icommands
for performance reasons.