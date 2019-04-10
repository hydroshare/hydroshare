Access Control Usage Notes 
--------------------------

The following routines in the access control system have been checked for
usage and have the following statuses: 

Old Method | Current Method | Status 
--- | --- | ---  
g.get_editable_resources() | g.edit_resources | used
g.get_held_resources() | g.view_resources | used
- | g.edit_users | needed for groups
- | g.view_users | needed for groups
r.get_combined_privilege(user) | r.get_effective_privilege(user)  | used
-  | r.owners | used
-  | r.edit_groups | needed for groups 
-  | r.edit_users | used
-  | r.view_groups | needed for groups 
-  | r.view_users | used
u.get_owned_resources() | u.owned_resources | used 
u.get_editable_resources() | u.edit_resources | used 
u.get_held_resources() | u.view_resources | used 
- | u.get_resources_with_explicit_access(privilege) | used 
- | u.owns_resource(resource)  | used 
- | u.can_change_resource(resource)  | used 
- | u.can_change_resource_flags(resource) | used 
- | u.can_view_resource(resource)  | used 
- | u.create_group(title) | needed for groups 
u.get_owned_groups() | u.owned_groups | needed for groups
u.get_editable_groups() | u.edit_groups | needed for groups 
u.get_held_groups() | u.view_groups | needed for groups 
- | u.get_groups_with_explicit_access(privilege)  | needed for groups
- | u.owns_group(group)  | needed for groups
- | u.can_change_group(group)  | needed for groups
- | u.can_change_group_flags(group) | needed for groups
- | u.can_view_group(group)  | needed for groups
- | u.share_resource_with_user(resource, user, privilege) | used
- | u.unshare_resource_with_user(resource, user) | used
- | u.can_unshare_resource_with_user(resource, user) | used
- | u.undo_share_resource_with_user(resource, user) | used
- | u.can_undo_share_resource_with_user(resource, user) | used
- | u.share_resource_with_group(resource, group, privilege) | needed for groups
- | u.unshare_resource_with_group(resource, group) | needed for groups
- | u.can_unshare_resource_with_group(resource, group) | needed for groups
- | u.undo_share_resource_with_group(resource, group) | needed for groups
- | u.can_undo_share_resource_with_group(resource, group) | needed for groups
- | u.share_group_with_user(resource, user, privilege) | needed for groups
- | u.unshare_group_with_user(resource, user) | needed for groups
- | u.can_unshare_group_with_user(resource, user) | needed for groups
- | u.undo_share_group_with_user(resource, user) | needed for groups
- | u.can_undo_share_group_with_user(resource, user) | needed for groups

