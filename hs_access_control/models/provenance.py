from django.contrib.auth.models import User, Group
from django.db import models
from django.db.models import F, Max
from django.core.exceptions import PermissionDenied

from hs_core.models import BaseResource
from hs_access_control.models.privilege import PrivilegeCodes
from hs_access_control.models.community import Community

#################################
# classes that track provenance of privileges
# These are used to implement undo and for forensic analysis.
#################################


class ProvenanceBase(models.Model):
    """Methods reused by all provenance classes

    These methods are independent of the types of the foreign keys they act upon,
    and so can be reused in all provenance classes.

    **Using any of these routines directly will break provenance.** Instead, they are
    called from the specific "provenance" classes when needed.
    """

    class Meta:
        abstract = True

    def __str__(self):
        """print name for debugging"""
        return 'grantee=' + str(self.grantee) + \
               ', entity=' + str(self.entity) + \
               ', privilege=' + PrivilegeCodes.NAMES[self.privilege] + \
               ' (' + str(self.privilege) + ')' + \
               ', grantor=' + str(self.grantor) + \
               ', start=' + str(self.start) + \
               ', undone=' + str(self.undone)

    @classmethod
    def __get_current_start(cls, **kwargs):
        """
        Get the last start time for a given pair of keys.

        This is the timestamp of the record that represents current state.

        Usage:
            UserResourceProvenance.__get_current_start(resource={X}, user={Y})
            UserGroupProvenance.__get_current_start(group={X}, user={Y})
            GroupResourceProvenance.__get_current_start(resource={X}, group={Y})
        """
        result = cls.objects\
            .filter(**kwargs)\
            .aggregate(Max('start'))
        # This can be None if there is no start pair
        return result['start__max']

    @classmethod
    def get_current_record(cls, **kwargs):
        """
        Get the current provenance record for a given pair of keys.

        There is always an exact match between this record and the record in the
        matching Privilege model.

        Usage:
            UserResourceProvenance.get_current_record(resource={X}, user={Y})
            UserGroupProvenance.get_current_record(group={X}, user={Y})
            GroupResourceProvenance.get_current_record(resource={X}, group={Y})
            UserCommunityProvenance.get_current_record(user={X}, community={Y})
            GroupCommunityProvenance.get_current_record(group={X}, community={Y})
        """
        if __debug__:
            assert len(kwargs) == 2
        # First, compute the latest start time for the privilege.
        # This is the start of the effective record.
        start = cls.__get_current_start(**kwargs)
        # Then, fetch that unique record.
        if start is not None:
            return cls.objects\
                .get(start=start, **kwargs)
        else:
            return None

    @classmethod
    def get_privilege(cls, **kwargs):
        """
        Get the privilege implied by provenance state.

        There is always an exact match between get_privilege for Provenance
        and Privilege models.

        Usage:
            UserResourceProvenance.get_privilege(resource={X}, user={Y})
            UserGroupProvenance.get_privilege(group={X}, user={Y})
            GroupResourceProvenance.get_privilege(resource={X}, group={Y})
            UserCommunityProvenance.get_privilege(user={X}, community={Y})
            GroupCommunityProvenance.get_privilege(group={X}, community={Y})
        """
        if __debug__:
            assert len(kwargs) == 2
        result = cls.get_current_record(**kwargs)
        if result is not None:
            return result.privilege
        else:
            return PrivilegeCodes.NONE

    @classmethod
    def update(cls, **kwargs):
        """
        Add a provenance record to the provenance chain.

        The Provenance models are append-only tables, in the sense that no
        record is ever deleted or changed. At any point in time the last record
        entered for a pair is binding.  Records are automatically timestamped to enforce this.

        Usage:
            UserResourceProvenance.update(resource={X}, user={Y}, privilege={Z}, ...)
            UserGroupProvenance.update(group={X}, user={Y}, privilege={Z}, ...)
            GroupResourceProvenance.update(resource={X}, group={Y}, privilege={Z}, ...)
            UserCommunityProvenance.update(user={X}, community={Y}, privilege={Z}, ...)
            GroupCommunityProvenance.update(group={X}, community={Y}, privilege={Z}, ...)
        """
        cls.objects.create(**kwargs)

    @classmethod
    def __get_prev_start(cls, **kwargs):
        """
        Get the previous start time.

        An undo consists of backing up one time step from the current record to
        find the previous one. This is then reinstated as the current record by
        creating a copy. This can only be done once.

        Usage:
            UserResourceProvenance.__get_prev_start(resource={X}, user={Y})
            UserGroupProvenance.__get_prev_start(group={X}, user={Y})
            GroupResourceProvenance.__get_prev_start(resource={X}, group={Y})
            UserCommunityProvenance.__get_prev_start(user={X}, community={Y})
            GroupCommunityProvenance.__get_prev_start(group={X}, community={Y})
        """
        if __debug__:
            assert len(kwargs) == 2
        last = cls.__get_current_start(**kwargs)
        if last is not None:
            result = cls.objects\
                .filter(start__lt=last,
                        **kwargs) \
                .aggregate(Max('start'))
            return result['start__max']
        else:
            return None

    @classmethod
    def __get_prev_record(cls, **kwargs):
        """
        Get the previous privilege record for a given pair.

        This is the record that will be copied to reinstate its privilege after an undo.

        Usage:
            UserResourceProvenance.__get_prev_record(resource={X}, user={Y})
            UserGroupProvenance.__get_prev_record(group={X}, user={Y})
            GroupResourceProvenance.__get_prev_record(resource={X}, group={Y})
            UserCommunityProvenance.__get_prev_record(user={X}, community={Y})
            GroupCommunityProvenance.__get_prev_record(group={X}, community={Y})
        """
        if __debug__:
            assert len(kwargs) == 2
        # First, compute the latest start time for the privilege.
        # This is the start of the effective record.
        start = cls.__get_prev_start(**kwargs)

        # Then, fetch that (hopefully) unique record(s). There is a small chance of non-uniqueness.
        if start is not None:
            return cls.objects.get(start=start, **kwargs)
        else:
            return None

    @classmethod
    def undo_share(cls, **kwargs):
        """
        Undo one provenance change

        To undo a change, one must find the last record and step back one time step.
        One must also prevent backstep records from themselves being backstepped.

        Usage:
        ------

                cls.undo_share({destination-args}, grantor={user})

        where {destination-args} consist of the pair of entities (user/group, user/resource,
        or group/resource) being controlled. The correct combination depends upon the subclass
        in which this routine is inherited.  E.g.,

                UserResourceProvenance.undo_share(resource={resource}, user={user}, grantor={user})

        is one such combination.

        Note that this does not modify the *Privilege class accordingly. That must be done
        separately.

        **This is never used directly in normal programming.** Use the routines in UserAccess.

        Important: this does not protect against removing the last owner.
        Supplementary logic is necessary
        """
        if __debug__:
            assert 'grantor' in kwargs
            assert isinstance(kwargs['grantor'], User)
            assert len(kwargs) == 3
        grantor = kwargs['grantor']
        del kwargs['grantor']
        current = cls.get_current_record(**kwargs)
        if current is None:
            raise PermissionDenied("No privilege to undo")
        if current.undone:
            raise PermissionDenied("Current privilege is already undone.")
        if current.grantor != grantor:
            raise PermissionDenied("Current user is not grantor")

        previous = cls.__get_prev_record(**kwargs)
        if previous is not None:
            # create a rollback record that reinstates the previous privilege.
            cls.update(privilege=previous.privilege,
                       grantor=previous.grantor,
                       undone=True,
                       **kwargs)
        else:
            # put in a record revoking all privilege -- cannot be undone
            cls.update(privilege=PrivilegeCodes.NONE,
                       grantor=None,
                       undone=True,
                       **kwargs)

    @classmethod
    def share(cls, **kwargs):
        """
        Share a thing with a user or group

        The thing can be a resource or group.  This is an unprotected method that does
        an unconditional share.  Use this only to completely bypass access control.

        Usage
        -----

                cls.share({destination-args}, privilege={privilege-code}, grantor={user})

        where {destination-args} consist of the pair of entities (user/group, user/resource,
        or group/resource) being controlled. The correct combination depends upon the subclass
        in which this routine is inherited.  E.g.,

                UserResourceProvenance.share(resource={resource}, user={user},
                                            privilege={privilege}, grantor={user})

        is one such combination.

        Note that this does not modify the *Privilege class accordingly.
        That must be done separately.
        """
        cls.update(**kwargs)

    @classmethod
    def unshare(cls, **kwargs):
        """
        Unshare a thing with a user or group

        The thing can be a resource or group.  This is an unprotected method that does
        an unconditional unshare.  Use this only for privileged unshare. Otherwise,
        use undo_share

        Usage
        -----

                cls.unshare({destination-args}, grantor={user})

        where {destination-args} consist of the pair of entities (user/group, user/resource,
        or group/resource) being controlled. this is exactly equivalent with:

                cls.share(grantor={user}, {destination-args},
                          privilege=PrivilegeCodes.NONE)

        where {destination-args} consist of the pair of entities (user/group, user/resource,
        or group/resource) being controlled. The correct combination depends upon the subclass
        in which this routine is inherited.  E.g.,

                UserResourceProvenance.unshare(resource={resource}, user={user}, grantor={user})

        is one such combination.

        Unshares can be undone using undo_share.

        Note that this does not modify the *Privilege class accordingly.
        That must be done separately.

        """
        cls.update(privilege=PrivilegeCodes.NONE, **kwargs)


class UserGroupProvenance(ProvenanceBase):
    """
    Provenance of privileges of a user over a group

    Having any privilege over a group is synonymous with membership.

    This is an append-only ledger of group privilege that serves as complete provenance
    of access changes.  At any time, one privilege applies to each grantee and group.
    This is the privilege with the latest start date.  For performance reasons, this
    information is cached in a separate table UserGroupPrivilege.

    To undo a privilege, one appends a record to this table with PrivilegeCodes.NONE.
    This is indistinguishable from having no record at all.  Thus, this provides a
    complete time-based journal of what privilege was in effect when.

    An "undone" field allows one-step undo but prohibits further undo.

    """
    privilege = models.IntegerField(choices=PrivilegeCodes.CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)

    start = models.DateTimeField(editable=False, auto_now_add=True)

    user = models.ForeignKey(User,
                             null=False,
                             editable=False,
                             related_name='u2ugq',
                             help_text='user to be granted privilege')

    group = models.ForeignKey(Group,
                              null=False,
                              editable=False,
                              related_name='g2ugq',
                              help_text='group to which privilege applies')

    grantor = models.ForeignKey(User,
                                null=True,
                                editable=False,
                                related_name='x2ugq',
                                help_text='grantor of privilege')

    undone = models.BooleanField(editable=False, default=False)

    class Meta:
        unique_together = ('user', 'group', 'start')

    @property
    def grantee(self):
        """ make printing of privilege records work properly in superclass"""
        return self.user

    @property
    def entity(self):
        """ make printing of privilege records work properly in superclass"""
        return self.group

    @classmethod
    def get_undo_users(cls, group, grantor):
        """
        get the users for which a specific grantee can undo privilege

        :param group: group to check.
        :param grantor: user that would initiate the rollback.

        Note: undo is somewhat independent of access control. A user need not hold
        a privilege to undo a privilege that was previously granted.
        """

        if __debug__:
            assert isinstance(grantor, User)
            assert isinstance(group, Group)

        # users are those last granted a privilege over the entity by the grantor
        # This syntax is curious due to undesirable semantics of .exclude.
        # All conditions on the filter must be specified in the same filter statement.
        selected = User.objects.filter(u2ugq__group=group)\
                               .annotate(start=Max('u2ugq__start'))\
                               .filter(u2ugq__start=F('start'),
                                       u2ugq__grantor=grantor,
                                       u2ugq__undone=False)
        # launder out annotations used to select users
        return User.objects.filter(pk__in=selected).exclude(pk=grantor.pk)

    @classmethod
    def update(cls, group, user, privilege, grantor, undone=False):
        """
        Add a provenance record to the provenance chain.

        This is just a wrapper around ProvenanceBase.update that makes parameters explicit.
        """

        if __debug__:
            assert isinstance(group, Group)
            assert isinstance(user, User)
            assert grantor is None or isinstance(grantor, User)
            assert privilege >= PrivilegeCodes.OWNER and privilege <= PrivilegeCodes.NONE

        super(UserGroupProvenance, cls).update(group=group,
                                               user=user,
                                               privilege=privilege,
                                               grantor=grantor,
                                               undone=undone)


class UserResourceProvenance(ProvenanceBase):
    """
    Provenance of privileges of a user over a resource.

    This is an append-only ledger of group privilege that serves as complete provenance
    of access changes.  At any one time, one privilege applies to each user and group.
    This is the privilege with the latest start date.  For performance reasons, this
    information is cached in a separate table UserResourcePrivilege.

    To undo a privilege, one appends a record to this table with PrivilegeCodes.NONE.
    This is indistinguishable from having no record at all.  Thus, this provides a
    time-based journal of what privilege was in effect when.

    An "undone" field allows one-step undo but prohibits further undo.
    """

    privilege = models.IntegerField(choices=PrivilegeCodes.CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)

    start = models.DateTimeField(editable=False, auto_now_add=True)

    user = models.ForeignKey(User,
                             null=False,
                             editable=False,
                             related_name='u2urq',
                             help_text='user to be granted privilege')

    resource = models.ForeignKey(BaseResource,
                                 null=False,
                                 editable=False,
                                 related_name='r2urq',
                                 help_text='resource to which privilege applies')

    grantor = models.ForeignKey(User,
                                null=True,
                                editable=False,
                                related_name='x2urq',
                                help_text='grantor of privilege')

    undone = models.BooleanField(editable=False, default=False)

    class Meta:
        unique_together = ('user', 'resource', 'start')

    @property
    def grantee(self):
        return self.user

    @property
    def entity(self):
        return self.resource

    @classmethod
    def get_undo_users(cls, resource, grantor):
        """ get the users for which a specific user can roll back privilege """

        if __debug__:
            assert isinstance(grantor, User)
            assert isinstance(resource, BaseResource)

        # users are those last granted a privilege over the resource by the grantor
        # This syntax is curious due to undesirable semantics of .exclude.
        # All conditions on the filter must be specified in the same filter statement.
        selected = User.objects.filter(u2urq__resource=resource)\
                               .annotate(start=Max('u2urq__start'))\
                               .filter(u2urq__start=F('start'),
                                       u2urq__grantor=grantor,
                                       u2urq__undone=False)
        # launder out annotations used to select users
        return User.objects.filter(pk__in=selected).exclude(pk=grantor.pk)

    @classmethod
    def update(cls, resource, user, privilege, grantor, undone=False):
        """
        Add a provenance record to the provenance chain.

        This is just a wrapper around ProvenanceBase.update with type checking.

        The Provenance models are append-only tables, in the sense that no old records
        are ever deleted; new records are added and timestamped as current.
        """
        if __debug__:
            assert isinstance(resource, BaseResource)
            assert isinstance(user, User)
            assert grantor is None or isinstance(grantor, User)
            assert privilege >= PrivilegeCodes.OWNER and privilege <= PrivilegeCodes.NONE

        super(UserResourceProvenance, cls).update(resource=resource,
                                                  user=user,
                                                  privilege=privilege,
                                                  grantor=grantor,
                                                  undone=undone)


class GroupResourceProvenance(ProvenanceBase):
    """
    Provenance of privileges of a group over a resource.

    The group privilege over a resource is not directly meaningful.
    it is resolved instead into user privilege for each member of
    the group, as listed in UserGroupProvenance and GroupCommunityProvenance above.

    This is an append-only ledger of group privilege that serves as complete provenance
    of access changes.  At any one time, one privilege applies to each user and resource.
    This is the privilege with the latest start date.  For performance reasons, this
    information is cached in a separate table GroupResourcePrivilege.

    To undo a privilege, one appends a record to this table with PrivilegeCodes.NONE.
    This is indistinguishable from having no record at all.  Thus, this provides a
    time-based journal of what privilege was in effect when.

    An "undone" field allows one-step undo but prohibits further undo.

    """

    privilege = models.IntegerField(choices=PrivilegeCodes.CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)

    start = models.DateTimeField(editable=False, auto_now_add=True)

    group = models.ForeignKey(Group,
                              null=False,
                              editable=False,
                              related_name='g2grq',
                              help_text='group to be granted privilege')

    resource = models.ForeignKey(BaseResource,
                                 null=False,
                                 editable=False,
                                 related_name='r2grq',
                                 help_text='resource to which privilege applies')

    grantor = models.ForeignKey(User,
                                null=True,
                                editable=False,
                                related_name='x2grq',
                                help_text='grantor of privilege')

    undone = models.BooleanField(editable=False, default=False)

    class Meta:
        unique_together = ('group', 'resource', 'start')

    @property
    def grantee(self):
        return self.group

    @property
    def entity(self):
        return self.resource

    @classmethod
    def get_undo_groups(cls, resource, grantor):
        """ get the groups for which a specific user can roll back privilege """

        if __debug__:
            assert isinstance(grantor, User)
            assert isinstance(resource, BaseResource)

        # groups are those last granted a privilege over the resource by the grantor
        # This syntax is curious due to undesirable semantics of .exclude.
        # All conditions on the filter must be specified in the same filter statement.
        # We wish to avoid the state INITIAL, which cannot be undone.
        # This is accomplished by setting a NULL grantor for INITIAL.
        selected = Group.objects.filter(g2grq__resource=resource)\
            .annotate(start=Max('g2grq__start'))\
            .filter(g2grq__start=F('start'),
                    g2grq__grantor=grantor,
                    g2grq__undone=False)

        # launder out annotations used to select users
        return Group.objects.filter(pk__in=selected)

    @classmethod
    def update(cls, resource, group, privilege, grantor, undone=False):
        """
        Add a provenance record to the provenance chain.

        This is just a wrapper around ProvenanceBase.update with argument type checking.
        """
        if __debug__:
            assert isinstance(resource, BaseResource)
            assert isinstance(group, Group)
            assert grantor is None or isinstance(grantor, User)
            assert privilege >= PrivilegeCodes.OWNER and privilege <= PrivilegeCodes.NONE

        super(GroupResourceProvenance, cls).update(resource=resource,
                                                   group=group,
                                                   privilege=privilege,
                                                   grantor=grantor,
                                                   undone=undone)


class UserCommunityProvenance(ProvenanceBase):
    """
    Provenance of privileges of a user over a community

    Having any privilege over a community is synonymous with membership.

    This is an append-only ledger of user privilege that serves as complete provenance
    of access changes.  At any time, one privilege applies to each grantee and group.
    This is the privilege with the latest start date.  For performance reasons, this
    information is cached in a separate table UserCommunityPrivilege.

    To undo a privilege, one appends a record to this table with PrivilegeCodes.NONE.
    This is indistinguishable from having no record at all.  Thus, this provides a
    complete time-based journal of what privilege was in effect when.

    An "undone" field allows one-step undo but prohibits further undo.

    """
    privilege = models.IntegerField(choices=PrivilegeCodes.CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)

    start = models.DateTimeField(editable=False, auto_now_add=True)

    community = models.ForeignKey(Community,
                                  null=False,
                                  editable=False,
                                  related_name='c2ucq',
                                  help_text='community to be granted privilege')

    user = models.ForeignKey(User,
                             null=False,
                             editable=False,
                             related_name='u2ucq',
                             help_text='user to which privilege applies')

    grantor = models.ForeignKey(User,
                                null=True,
                                editable=False,
                                related_name='x2ucq',
                                help_text='grantor of privilege')

    undone = models.BooleanField(editable=False, default=False)

    class Meta:
        unique_together = ('community', 'user', 'start')

    @property
    def grantee(self):
        """ make printing of privilege records work properly in superclass"""
        return self.community

    @property
    def entity(self):
        """ make printing of privilege records work properly in superclass"""
        return self.user

    @classmethod
    def get_undo_users(cls, community, grantor):
        """
        get the users for which a specific grantee can undo privilege

        :param community: community to check.
        :param grantor: user that would initiate the rollback.

        Note: undo is somewhat independent of access control. A user need not hold
        a privilege to undo a privilege that was previously granted.
        """

        if __debug__:
            assert isinstance(grantor, User)
            assert isinstance(community, Community)

        # users are those last granted a privilege over the entity by the grantor
        # This syntax is curious due to undesirable semantics of .exclude.
        # All conditions on the filter must be specified in the same filter statement.
        selected = User.objects.filter(u2ucq__community=community)\
                               .annotate(start=Max('u2ucq__start'))\
                               .filter(u2ucq__start=F('start'),
                                       u2ucq__grantor=grantor,
                                       u2ucq__undone=False)
        return selected

    @classmethod
    def update(cls, user, community, privilege, grantor, undone=False):
        """
        Add a provenance record to the provenance chain.

        :param user: shared user
        :param community: community with which user is shared.
        :param grantor: user that would initiate the rollback.

        This is just a wrapper around ProvenanceBase.update that makes parameters explicit.
        """

        if __debug__:
            assert isinstance(user, User)
            assert isinstance(community, Community)
            assert grantor is None or isinstance(grantor, User)
            assert privilege >= PrivilegeCodes.OWNER and privilege <= PrivilegeCodes.NONE

        super(UserCommunityProvenance, cls).update(user=user,
                                                   community=community,
                                                   privilege=privilege,
                                                   grantor=grantor,
                                                   undone=undone)


class GroupCommunityProvenance(ProvenanceBase):
    """
    Provenance of privileges of a group over a community

    Having any privilege over a community is synonymous with membership.

    This is an append-only ledger of group privilege that serves as complete provenance
    of access changes.  At any time, one privilege applies to each grantee and group.
    This is the privilege with the latest start date.  For performance reasons, this
    information is cached in a separate table GroupCommunityPrivilege.

    To undo a privilege, one appends a record to this table with PrivilegeCodes.NONE.
    This is indistinguishable from having no record at all.  Thus, this provides a
    complete time-based journal of what privilege was in effect when.

    An "undone" field allows one-step undo but prohibits further undo.

    """
    privilege = models.IntegerField(choices=PrivilegeCodes.CHOICES,
                                    editable=False,
                                    default=PrivilegeCodes.VIEW)

    start = models.DateTimeField(editable=False, auto_now_add=True)

    community = models.ForeignKey(Community,
                                  null=False,
                                  editable=False,
                                  related_name='c2gcq',
                                  help_text='group to be granted privilege')

    group = models.ForeignKey(Group,
                              null=False,
                              editable=False,
                              related_name='g2gcq',
                              help_text='group to which privilege applies')

    grantor = models.ForeignKey(User,
                                null=True,
                                editable=False,
                                related_name='x2gcq',
                                help_text='grantor of privilege')

    undone = models.BooleanField(editable=False, default=False)

    class Meta:
        unique_together = ('community', 'group', 'start')

    @property
    def grantee(self):
        """ make printing of privilege records work properly in superclass"""
        return self.community

    @property
    def entity(self):
        """ make printing of privilege records work properly in superclass"""
        return self.group

    @classmethod
    def get_undo_groups(cls, community, grantor):
        """
        get the groups for which a specific grantee can undo privilege

        :param community: community to check.
        :param grantor: user that would initiate the rollback.

        Note: undo is somewhat independent of access control. A user need not hold
        a privilege to undo a privilege that was previously granted.
        """

        if __debug__:
            assert isinstance(grantor, User)
            assert isinstance(community, Community)

        # users are those last granted a privilege over the entity by the grantor
        # This syntax is curious due to undesirable semantics of .exclude.
        # All conditions on the filter must be specified in the same filter statement.
        selected = Group.objects.filter(g2gcq__community=community)\
                               .annotate(start=Max('g2gcq__start'))\
                               .filter(g2gcq__start=F('start'),
                                       g2gcq__grantor=grantor,
                                       g2gcq__undone=False)
        return selected

    @classmethod
    def update(cls, group, community, privilege, grantor, undone=False):
        """
        Add a provenance record to the provenance chain.

        :param group: shared group
        :param community: community with which group is shared.
        :param grantor: user that would initiate the rollback.

        This is just a wrapper around ProvenanceBase.update that makes parameters explicit.
        """

        if __debug__:
            assert isinstance(group, Group)
            assert isinstance(community, Community)
            assert grantor is None or isinstance(grantor, User)
            assert privilege >= PrivilegeCodes.OWNER and privilege <= PrivilegeCodes.NONE

        super(GroupCommunityProvenance, cls).update(group=group,
                                                    community=community,
                                                    privilege=privilege,
                                                    grantor=grantor,
                                                    undone=undone)
