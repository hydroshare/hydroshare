# This file serves as a centralized place for storing all keys currently being supported in
# extended metadata for web app tool resource

# The tool_app_key is used to associate a specific resource with a specific web app tool if
# both have the matching value for tool_app_key
tool_app_key = 'appkey'

# The irods_path_key and irods_resc_key are used for a web app tool resource to specify
# the federated irods target path and resource specific to the web app tool for the requesting
# resource to be copied over to the target federated irods server by iRODS file transfer.
# The copy operation only happens right before the web app tool is being launched so the requesting
# resource data are ready to be consumed by the web app when it is launched.
irods_path_key = 'irods_federation_target_path'
irods_resc_key = 'irods_federation_target_resource'
# The user_auth_flag_key is optional and can be used for a web app tool resource that specifies
# irods_path_key and irods_resc_key to additionally specify whether the web app requires user
# to be authenticated in HydroShare before using the web app. If this optional key is not specified,
# the default action is to assume no user authentication is required by the web app.
user_auth_flag_key = 'require_user_authentication'
