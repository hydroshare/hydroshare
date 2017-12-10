"""
 This model supports user labeling of resources in various ways.
 For a User u, this instantiates a subobject u.ulabels (like u.uaccess)
 that contains all the labeling functions.

 Functions include:

 * u.ulabels.label_resource(r, label)
   instantiates a label for a resource. Resources can have multiple labels.

 * u.ulabels.unlabel_resource(r, label)
   removes a label; there can be many labels.

 * u.ulabels.clear_resource_labels(r)
   removes all labels for a resource

 * u.ulabels.favorite_resource(r)
   favorites a resource

 * u.ulabels.unfavorite_resource(r)
   removes a favorite

 and the reporting functions

 * u.ulabels.labeled_resources
   A queryset of resources that are labeled.

 * u.ulabels.favorited_resources
   A queryset of resources that have been favorited

 * u.ulabels.get_resources_with_label(label)
   Get a queryset of resources possessing a specific label.

 For a BaseResource r, this also adds a subobject rlabels that reports on labels for resources

 * r.rlabels.get_labels(u)

 * r.rlabels.is_favorite(u)

 * r.rlabels.is_mine(u)

"""
# TODO: combine label filtering with access control

import re

from django.contrib.auth.models import User
from django.db import models
from django.db import transaction
from django.db.models import Q

from hs_core.models import BaseResource

class FlagCodes(object):
    """
    Flag codes describe the meanings of per-user flags for a resource.

    * 1 or FlagCodes.FAVORITE:
      marked as a favorite on "My Resources" page

    * 2 or FlagCodes.MINE:
      marked as being part of "My Resources" on "Discover" page.
    """
    FAVORITE = 1
    MINE = 2
    FLAG_CHOICES = (
        (FAVORITE, 'Favorite'), # marked as favorite in my resources page.
        (MINE, 'Mine'),         # marked as mine in discovery page.
    )


class UserResourceLabels(models.Model):
    """
    Labels of a user for a resource

    This model stores labels of an individual user, like an access control list. T
    """
    start = models.DateTimeField(editable=False, auto_now=True)

    user = models.ForeignKey(User, null=False, editable=False,
                             related_name='u2url',  # unused but must be defined and unique
                             help_text='user assigning a label',
                             on_delete=models.CASCADE)

    resource = models.ForeignKey(BaseResource, null=False, editable=False,
                                 related_name='r2url',  # unused but must be defined and unique
                                 help_text='resource to which a label applies',
                                 on_delete=models.CASCADE)

    label = models.TextField(null=False)

    class Meta:
        unique_together = ('user', 'resource', 'label')


class UserResourceFlags(models.Model):
    """
    Per-user flagging of resources.

    This model stores labels of an individual user, like an access
    control list; There are several kinds of labels documented in FlagCodes.
    These are similar in implementation but differ in semantics.
    """
    kind = models.IntegerField(choices=FlagCodes.FLAG_CHOICES,
                               editable=False,
                               default=FlagCodes.FAVORITE)

    start = models.DateTimeField(editable=False, auto_now=True)

    user = models.ForeignKey(User, null=False, editable=False,
                             related_name='u2urf',  # unused but must be defined and unique
                             help_text='user assigning a flag',
                             on_delete=models.CASCADE)

    resource = models.ForeignKey(BaseResource, null=False, editable=False,
                                 related_name="r2urf",  # unused but must be defined and unique
                                 help_text='resource to which a flag applies',
                                 on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'resource', 'kind')


class UserStoredLabels(models.Model):
    """
    Storage class for persistent labels that are reusable across different kinds of objects
    """
    user  = models.ForeignKey(User, null=False,
                              help_text='user who stored the label',
                              related_name='ul2usl',
                              on_delete=models.CASCADE)
    label = models.TextField(help_text='label to be stored by user')
    class Meta:
        unique_together = ('user', 'label')


class UserLabels(models.Model):
    """
    Projection class puts methods and content inside basic User object
    so that one can access things easily from that context.
    This model is injected into the BaseResource as the related name "user".
    Thus for an User u, u.user is this model.
    """

    user = models.OneToOneField(User,
                                editable=False,
                                null=True,
                                related_name='ulabels',  # induced field in User class.
                                related_query_name='ulabels',
                                on_delete=models.CASCADE)

    ##########################################
    # PUBLIC FUNCTIONS: resources
    ##########################################

    @property
    def labeled_resources(self):
        """
        Get a QuerySet of resources labeled by a user.
        This eliminates duplicates.
        """
        return BaseResource.objects.filter(r2url__user=self.user).distinct()

    def get_flagged_resources(self, this_flagcode):
        """
        Get resources with a specific flag.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert this_flagcode == FlagCodes.FAVORITE or this_flagcode == FlagCodes.MINE

        return BaseResource.objects.filter(r2urf__user=self.user,
                                           r2urf__kind=this_flagcode)

    @property
    def favorited_resources(self):
        """
        Get a QuerySet of resources favorited by a user.
        This eliminates duplicates.
        """

        return self.get_flagged_resources(FlagCodes.FAVORITE)

    @property
    def my_resources(self):
        """
        Get a QuerySet of resources marked as mine (add to my resources) by a user.
        This eliminates duplicates.
        """
        return self.get_flagged_resources(FlagCodes.MINE)

    @property
    def resources_of_interest(self):
        """
        Get a QuerySet of resources the user has tagged in any way.
        """
        return BaseResource.objects.filter(Q(r2url__user=self.user) | Q(r2urf__user=self.user)).distinct()

    def get_resources_with_label(self, this_label):
        """
        Get a QuerySet of resources with a specific label.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_label, basestring)

        label_string = UserLabels.clean_label(this_label)  # remove leading and trailing spaces
        return BaseResource.objects.filter(r2url__user=self.user,
                                           r2url__label__exact=label_string)\
                                    .distinct()\
                                    .order_by('r2url__label')

    @property
    def user_labels(self):
        """
        Get a QuerySet of labels in use now.
        """
        return UserResourceLabels.objects.values_list('label', flat=True)\
                                 .filter(user=self.user)\
                                 .distinct().order_by('label')

    ######################################
    # Label a resource
    ######################################

    @staticmethod
    def clean_label(name):
        label_string = re.sub('/', r'', name)                   # no /'s
        label_string = label_string.strip()                     # no leading or trailing whitespace
        label_string = re.sub(r'\s+', r' ', label_string)       # collapse multiple whitespace, including tabs
        return label_string

    def label_resource(self, this_resource, this_label):
        """
        Assign a label to a resource

        Users are allowed to label any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_label, basestring)

        # remove leading and trailing spaces
        label_string = UserLabels.clean_label(this_label)
        with transaction.atomic():  # empirically, get_or_create is not atomic.
            UserResourceLabels.objects.get_or_create(resource=this_resource,
                                                     label=label_string,
                                                     user=self.user)

    def unlabel_resource(self, this_resource, this_label):
        """
        Remove one label from a resource

        Users are allowed to label any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert isinstance(this_label, basestring)

        # remove leading and trailing spaces
        label_string = UserLabels.clean_label(this_label)

        UserResourceLabels.objects.filter(resource=this_resource,
                                          label__exact=label_string,
                                          user=self.user).delete()

    def clear_resource_labels(self, this_resource):
        """
        Clear all labels for a resource
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

        UserResourceLabels.objects.filter(resource=this_resource,
                                          user=self.user).delete()

    def remove_resource_label(self, this_label):
        """
        clear a label from the labeling system.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_label, basestring)
        UserResourceLabels.objects.filter(label=this_label, user=self.user)\
                                  .delete()

    ##########################################
    # general flagging of resources
    ##########################################

    def flag_resource(self, this_resource, this_flagcode):
        """
        flag a resource with a specific flag code from FlagCodes

        Users are allowed to flag any resource, including resources to which they do not have access.
        This is not an access control problem because flagging information is private.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert this_flagcode == FlagCodes.FAVORITE or this_flagcode == FlagCodes.MINE

        with transaction.atomic():  # empirically, get_or_create is not atomic.
            UserResourceFlags.objects.get_or_create(resource=this_resource,
                                                     kind=this_flagcode,
                                                     user=self.user)

    def unflag_resource(self, this_resource, this_flagcode):
        """
        unflag a resource with a specific flag.

        Users are allowed to flag any resource, including resources to which they do not have access.
        This is not an access control problem because flagging information is private.
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)
            assert this_flagcode == FlagCodes.FAVORITE or this_flagcode == FlagCodes.MINE

        UserResourceFlags.objects.filter(user=self.user,
                                          resource=this_resource,
                                          kind=this_flagcode).delete()

    def clear_all_flags(self, this_flagcode):
        """
        remove all flags of a specific kind for a user
        """
        UserResourceFlags.objects.filter(user=self.user,
                                          kind=this_flagcode)\
                                  .delete()

    ##########################################
    # favorite resources
    ##########################################

    def favorite_resource(self, this_resource):
        """
        Mark a resource as favorite.

        Users are allowed to flag any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.
        """
        self.flag_resource(this_resource, FlagCodes.FAVORITE)

    def unfavorite_resource(self, this_resource):
        """
        Clear favorite label for a resource

        Users are allowed to flag any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.
        """
        self.unflag_resource(this_resource, FlagCodes.FAVORITE)

    ##########################################
    # my resources
    ##########################################

    def claim_resource(self, this_resource):
        """
        Label a resource as 'MINE' (adds to my resources).

        Users are allowed to flag any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.
        """
        self.flag_resource(this_resource, FlagCodes.MINE)

    def unclaim_resource(self, this_resource):
        """
        Clear 'MINE' label for a resource (removes from my resources)

        Users are allowed to flag any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.
        """
        self.unflag_resource(this_resource, FlagCodes.MINE)

    ##########################################
    # routines that apply to all kinds of annotations
    ##########################################

    def clear_resource_all(self, this_resource):
        """
        Clear all annotations for a resource
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_resource, BaseResource)

        UserResourceLabels.objects\
                          .filter(resource=this_resource,
                                  user=self.user)\
                          .delete()
        UserResourceFlags.objects\
                         .filter(resource=this_resource,
                                 user=self.user)\
                         .delete()

    ##########################################
    # save unused labels
    ##########################################

    def save_label(self, this_label):
        """
        Save a label for use later.

        Users are allowed to label any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.
        """
        label_string = UserLabels.clean_label(this_label)    # remove leading and trailing spaces
        with transaction.atomic():  # empirically, get_or_create is not atomic.
            UserStoredLabels.objects.get_or_create(label=label_string, user=self.user)

    def unsave_label(self, this_label):
        """
        Remove the specified saved label.
        """
        # remove leading and trailing spaces
        label_string = UserLabels.clean_label(this_label)
        UserStoredLabels.objects.filter(label__exact=label_string, user=self.user).delete()
        # remove all uses of that label from resources.
        self.remove_resource_label(label_string)

    def clear_saved_labels(self):
        """
        Clear all saved labels for a user
        """
        UserStoredLabels.objects.filter(user=self.user).delete()

    @property
    def saved_labels(self):
        """
        Return a QuerySet of saved labels.
        """
        return UserStoredLabels.objects.filter(user=self.user).values_list('label', flat=True).distinct()


class ResourceLabels(models.Model):
    """
    For a BaseResource r, r.rlabels is this model. It contains functions relevant to resources.
    """
    resource = models.OneToOneField(BaseResource,
                                    editable=False,
                                    null=True,
                                    related_name='rlabels',
                                    related_query_name='rlabels',
                                    on_delete=models.CASCADE)

    def get_users(self):
        """
        Return a QuerySet of all users who have labeled this resource.
        """
        return User.objects.filter(Q(u2url__resource=self.resource) | Q(u2urf__resource=self.resource))

    def get_labels(self, this_user):
        """
        Return a QuerySet of all user assigned labels for a resource
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_user, User)

        labels = UserResourceLabels.objects\
                                   .values_list('label', flat=True)\
                                   .filter(user=this_user,
                                           resource=self.resource)\
                                   .order_by("label").all()
        return labels

    def is_flagged(self, this_user, this_flagcode):
        """
        Return True if this resource has been flagged by a given user
        """
        if __debug__:  # during testing only, check argument types and preconditions
            assert isinstance(this_user, User)
            assert this_flagcode == FlagCodes.FAVORITE or this_flagcode == FlagCodes.MINE

        return UserResourceFlags.objects.filter(user=this_user,
                                                 resource=self.resource,
                                                 kind=this_flagcode).exists()

    def is_favorite(self, this_user):
        """
        Return True if this resource has been favorited by a given user
        """
        return self.is_flagged(this_user, FlagCodes.FAVORITE)

    def is_mine(self, this_user):
        """
        Return True if this resource has been labeled as mine by a given user
        """
        return self.is_flagged(this_user, FlagCodes.MINE)

