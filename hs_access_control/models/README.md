Access control classes for hydroshare.

This module implements access control for hydroshare.  Privilege models act on users,
groups, and resources, and determine what objects are accessible to which users.  These models:

* determine four kinds of privilege

   1) user privilege over resources.
   2) user membership in and privilege over groups.
   3) group privilege over resources.
   4) user ownership of communities.
   5) community membership of and privilege over groups.

* track the provenance of privilege granting to:

   1) allow accounting for what happened.
   2) allow limited undo of prior actions.
   3) limit each user to accumulating one privilege over a thing...

Notes and quandaries
--------------------

* A resource or group can become unowned as a result of a user becoming inactive.
  In this case, logic must not break.
* users of ResourceAccess.edit_resources, ResourceAccess.edit_users, ResourceAccess.view_users
  should be aware that

    * Listed resources include all accessible resources (via user or group sharing)
    * privileges are cumulative over all flags
    * Thus, these are not lists for display; they are access lists.

* In general, use get_resources_with_explicit_access to create display lists.

* In general, the system reports "effective" privilege.

    * effective privilege: that after accounting for resource flags (particularly, 'published'
      and 'immutable'.
    * declared privilege: that before accounting for resource flags.

  Thus, it is possible that sharing something immutable with CHANGE privilege will result in
  effective VIEW privilege.
