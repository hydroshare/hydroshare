"""
 This model supports user labeling of resources in various ways.
 For a User u, this instantiates a subobject u.ulabels (like u.uaccess)
 that contains all the labeling functions.

 Functions include:
 - u.ulabels.label_resource(r, label)
   instantiates a label for a resource. Resources can have multiple labels.

 - u.ulabels.unlabel_resource(r, label)
   removes a label; there can be many labels.

 - u.ulabels.clear_resource_labels(r)
   removes all labels for a resource

 - u.ulabels.favorite_resource(r)
   favorites a resource

 - u.ulabels.unfavorite_resource(r)
   removes a favorite

 and the reporting functions

 - u.ulabels.labeled_resources
   A queryset of resources that are labeled.

 - u.ulabels.favorite_resources
   A queryset of resources that have been favorited

 - u.ulabels.get_resources_with_label(label)
   Get a queryset of resources possessing a specific label.


 For a BaseResource r, this also adds a subobject rlabels that reports on labels for resources

 - r.rlabels.get_labels(u)
 - r.rlabels.get_users()
 - r.rlabels.is_favorite(u)
 - r.rlabels.is_mine(u)
"""

import re

from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q

from hs_core.models import BaseResource


class FlagCodes(object):
    """
    Flag codes describe the meanings of per-user flags for a resource.
    * 1 or FlagCodes.FAVORITE:
      marked as a favorite
    * 2 or FlagCodes.MINE:
      marked as being part of my_resources.
    """
    FAVORITE = 1
    MINE = 2
    FLAG_CHOICES = (
        (FAVORITE, 'Favorite'),
        (MINE, 'Mine'),
    )


class UserResourceLabels(models.Model):
    """ Labels of a user for a resource
    This model stores labels of an individual user, like an access
    control list
    """
    # provenance of label start
    start = models.DateTimeField(editable=False, auto_now=True)

    user = models.ForeignKey(User, null=False, editable=False,
                             related_name='u2url',  # unused but must be defined and unique
                             help_text='user assigning a label')

    resource = models.ForeignKey(BaseResource, null=False, editable=False,
                                 related_name='r2url',  # unused but must be defined and unique
                                 help_text='resource to which a label applies')

    label = models.TextField(null=False)


class UserResourceFlags(models.Model):
    """ Flag of a user for a resource

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
                             help_text='user assigning a flag')
    resource = models.ForeignKey(BaseResource, null=False, editable=False,
                                 related_name="r2urf",  # unused but must be defined and unique
                                 help_text='resource to which a flag applies')


class UserStoredLabels(models.Model):
    """ Storage class for persistent labels that are reusable across different kinds of objects
    """
    user = models.ForeignKey(User, null=True, help_text='user who stored the label', related_name='ul2usl')
    label = models.TextField(help_text='label to be stored by user')


class UserLabels(models.Model):
    """
    Projection class puts methods and content inside basic User object
    so that one can access things easily from that context.
    This model is injected into the BaseResource as the related name "ulabels".
    Thus for an User u, u.ulabels is this model.
    """

    user = models.OneToOneField(User,
                                editable=False,
                                null=True,
                                related_name='ulabels',  # induced field in User class.
                                related_query_name='ulabels',
                                on_delete=models.CASCADE)

    @property
    def labeled_resources(self):
        """
        Get a list of resources labeled by a user.

        This list eliminates duplicates.

        :return: List of resource objects labeled by user.
        """
        return BaseResource.objects.filter(r2url__user=self.user).distinct()

    @property
    def favorited_resources(self):
        """
        Get a list of resources favorited by a user.

        This list eliminates duplicates.

        :return: List of resource objects flagged as favorite by a user.
        """
        return BaseResource.objects.filter(r2urf__user=self.user,
                                           r2urf__kind=FlagCodes.FAVORITE).distinct()

    @property
    def my_resources(self):
        """
        Get a list of resources marked as mine (add to my resources) by a user.

        This list eliminates duplicates.

        :return: List of resource objects flagged as mine by a user.
        """
        return BaseResource.objects.filter(r2urf__user=self.user,
                                           r2urf__kind=FlagCodes.MINE).distinct()

    @property
    def resources_of_interest(self):
        """
        Get a list of resources the user has marked in any way.

        :return: List of resource objects that a user has marked.
        """
        return BaseResource.objects.filter(Q(r2url__user=self.user) | Q(r2urf__user=self.user)).distinct()

    def get_resources_with_label(self, this_label):
        """
        Get a list of resources with a specific label
        """

        # remove leading and trailing spaces
        label_string = UserLabels.clean_label(this_label)

        return BaseResource.objects.filter(r2url__user=self.user,
                                           r2url__label__exact=label_string)\
                                    .distinct()\
                                    .order_by('r2url__label')

    @property
    def user_labels(self):
        return UserResourceLabels.objects.values_list('label', flat=True)\
                                 .filter(user=self.user)\
                                 .distinct().order_by('label')

    @staticmethod
    def clean_label(name):
        label_string = re.sub('/', r'', name)                   # no /'s
        label_string = label_string.strip()                     # no leading or trailing whitespace
        label_string = re.sub(r'\s+', r' ', label_string)       # collapse multiple whitespace, including tabs
        return label_string

    def label_resource(self, this_resource, this_label):
        """
        assign a label to a resource

        :param this_resource: Resource to be assigned a label.
        :param this_label: Label to assign to resource

        Users are allowed to label any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.
        """

        # remove leading and trailing spaces
        label_string = UserLabels.clean_label(this_label)
        UserResourceLabels.objects.get_or_create(resource=this_resource,
                                                 label=label_string,
                                                 user=self.user)

    def unlabel_resource(self, this_resource, this_label):
        """ Remove one label from a resource

        :param this_resource: BaseResource from which to remove a label
        :param this_label: The label to remove. Only that labels will be removed.
        :return: none
        """

        # remove leading and trailing spaces
        label_string = UserLabels.clean_label(this_label)
        UserResourceLabels.objects.filter(resource=this_resource,
                                          label__exact=label_string,
                                          user=self.user).delete()

    def clear_resource_labels(self, this_resource):
        """ Clear all labels for a resource

        :param this_resource: BaseResource for which to clear all labels
        :return: none.
        """

        UserResourceLabels.objects.filter(resource=this_resource,
                                          user=self.user).delete()

    def remove_resource_label(self, this_label):
        """
        clear the specified label from all assigned resources
        """
        UserResourceLabels.objects.filter(label__exact=this_label, user=self.user).delete()

    def favorite_resource(self, this_resource):
        """
        Flag a resource as favorite.

        :param this_resource: Resource to flag as favorite

        Users are allowed to file any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.

        Resource gets flagged as favorite if it is not already flagged as favorite
        """
        # stopgap hot patch for emergent duplicate record problem.
        try:
            UserResourceFlags.objects.get_or_create(resource=this_resource,
                                                    kind=FlagCodes.FAVORITE,
                                                    user=self.user)
        except UserResourceFlags.MultipleObjectsReturned:
            pass

    def unfavorite_resource(self, this_resource):
        """ Clear favorite flag for a resource

        :param this_resource: BaseResource for which to clear favorite flag

        """
        UserResourceFlags.objects.filter(user=self.user,
                                         resource=this_resource,
                                         kind=FlagCodes.FAVORITE).delete()

    def claim_resource(self, this_resource):
        """
        Flag a resource as mine (add to my resources).

        :param this_resource: Resource to flag as mine (add to my resources).

        Resource gets flagged as mine if it is not already flagged as mine
        """
        try:
            UserResourceFlags.objects.get_or_create(resource=this_resource,
                                                    kind=FlagCodes.MINE,
                                                    user=self.user)
        except UserResourceFlags.MultipleObjectsReturned:
            pass

    def unclaim_resource(self, this_resource):
        """ Clear 'mine' flag for a resource (removes from my resources)

        :param this_resource: BaseResource for which to clear mine flag

        """
        UserResourceFlags.objects\
                         .filter(user=self.user,
                                 resource=this_resource,
                                 kind=FlagCodes.MINE)\
                         .delete()

    def clear_resource_all(self, this_resource):
        """ Clear all annotations for a resource

        :param this_resource: BaseResource for which to clear all annotations

        """
        UserResourceLabels.objects\
                          .filter(resource=this_resource,
                                  user=self.user)\
                          .delete()
        UserResourceFlags.objects\
                         .filter(resource=this_resource,
                                 user=self.user)\
                         .delete()

    def save_label(self, this_label):
        """
        Save a label for use later.

        :param this_label: Label to save

        Users are allowed to label any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.
        """

        # remove leading and trailing spaces
        label_string = UserLabels.clean_label(this_label)

        # This logic implicitly limits one to one record per resource and requester.
        try:
            UserStoredLabels.objects.get(label__exact=label_string, user=self.user)
            # if this succeeds, resource is already labeled with this label_string.

        # only create label if it does not exist. No duplicates.
        except UserStoredLabels.DoesNotExist:
            # create a new label record
            UserStoredLabels(label=label_string, user=self.user).save()

    def unsave_label(self, this_label):
        """ Remove the specified saved label

        :param this_label: The label to remove. Only that labels will be removed.

        """

        # remove leading and trailing spaces
        label_string = UserLabels.clean_label(this_label)
        UserStoredLabels.objects.filter(label__exact=label_string, user=self.user).delete()

        # remove the same label from all assigned resources
        self.remove_resource_label(this_label)

    def clear_saved_labels(self):
        """
        Clear all saved labels for a user

        """
        UserStoredLabels.objects.filter(user=self.user).delete()

    @property
    def saved_labels(self):
        """
        :return: a list of strings that constitute the saved labels
        """
        return UserStoredLabels.objects.filter(user=self.user).values_list('label', flat=True).distinct()


class ResourceLabels(models.Model):
    """ Resource model for labeling.

    This model is injected into the BaseResource as the related name "rlabels".
    Thus for a BaseResource r, r.rlabels is this model.
    """

    resource = models.OneToOneField(BaseResource,
                                    editable=False,
                                    null=True,
                                    related_name='rlabels',  # induced field of BaseResource
                                    related_query_name='rlabels',
                                    on_delete=models.CASCADE)

    def get_users(self):
        """
        Return a list of all users who have labeled this resource.

        :return: QuerySet that evaluates to all users holding resource.
        """
        return User.objects.filter(Q(u2url__resource=self.resource) | Q(u2urf__resource=self.resource))

    def get_labels(self, this_user):
        """
        get a list of all user assigned labels for a resource

        :return: QuerySet that evaluates to a list of labels (strings)
        """
        labels = UserResourceLabels.objects\
                                   .values_list('label', flat=True)\
                                   .filter(user=this_user,
                                           resource=self.resource)\
                                   .order_by("label").all()
        return labels

    def is_favorite(self, this_user):
        """ return True if this resource has been flagged as favorite by a given user

        :return: True or False
        """
        # This is a dirty hack: change get to filter to avoid duplicate exception
        return UserResourceFlags.objects.filter(user=this_user,
                                                resource=self.resource,
                                                kind=FlagCodes.FAVORITE).exists()

    def is_mine(self, this_user):
        """ return True if this resource has been flagged as mine by a given user

        :return: True or False
        """
        # This is a dirty hack: change get to filter to avoid duplicate exception
        return UserResourceFlags.objects.filter(user=this_user,
                                                resource=self.resource,
                                                kind=FlagCodes.MINE).exists()