# iRODS browser in CommonsShare #

Author: Hong Yi

### irods_browser implementation in CommonsShare that was repurposed from iPlant geonode-irods application developed by Amit Juneja ###

The CommonsShare app that allows a user to login to iRODS and browse iRODS collections and data objects from a specified zone
and select a data object to download from the specified iRODS zone and upload to CommonsShare Django to create a CommonsShare resource.
Irods python client API is used to retrieve collection and data objects for browsing, and the actual data transfer is done using icommands
for performance reasons.