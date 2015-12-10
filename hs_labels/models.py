__author__ = 'Alva'

# This model supports user labeling of resources in various ways.
# For a User u, this instantiates a subobject u.ulabels (like u.uaccess)
# that contains all the labeling functions.
#
# Functions include:
# - u.ulabels.label_resource(r, label)
#   instantiates a label for a resource. Resources can have multiple labels.
# - u.ulabels.unlabel_resource(r, label)
#   removes a label; there can be many labels.
# - u.ulabels.clear_resource_labels(r)
#   removes all labels for a resource
# - u.ulabels.favorite_resource(r)
#   favorites a resource
# - u.ulabels.unfavorite_resource(r)
#   removes a favorite
# - u.ulabels.file_resource(r, folder_name)
#   adds a folder name for a resource
# - u.ulabels.unfile_resource(r)
#   remove folder name
#
# and the reporting functions
# - u.ulabels.labeled_resources
#   A queryset of resources that are labeled.
# - u.ulabels.filed_resources (trivial, not yet implemented, available tomorrow)
#   A queryset of resources that are filed in folders
# - u.ulabels.favorite_resources (trivial, not yet implemented, available tomorrow)
#   A queryset of resources that have been favorited
# - u.ulabels.get_resources_with_label(label)
#   Get a queryset of resources possessing a specific label.
# - u.ulabels.get_resources_in_folder(folder)
#   Get a queryset of resources in a specific folder.

# For a BaseResource r, this also adds a subobject rlabels that reports on labels for resources
# -	r.rlabels.get_folder(u)
# - r.rlabels.get_labels(u)
# - r.rlabels.is_favorite(u) (trivial, not yet implemented, tomorrow)

import re

from django.contrib.auth.models import User
from django.db import models

from hs_core.models import BaseResource

######################################
######################################
# Labeling and annotation subsystem
######################################
######################################

# A "label" is something that is assigned by a person other than the original creator.
# It is not part of metadata. Labels include
# 1) making something a favorite.
# 2) assigning a folder
# 3) assigning a keyword

######################################
# Exceptions specific to access control:
# b) Usage Exception: bad parameters
######################################


class HSLException(Exception):
    """
    Generic Base Exception class for HSLLabel class.

    *This exception is a generic base class and is never directly raised.*
    See subclass HSLUsageException for details.
    """
    pass


class HSLUsageException(HSLException):
    """
    Exception class for parameter usage problems.

    This exception is raised when a routine is called with invalid parameters.
    This includes references to non-existent resources, groups, and users.

    This is typically a programming error and should be entered into
    issue tracker and resolved.

    *Catching this exception is not recommended.*
    """
    def __str__(self):
        return repr("HS Usage Exception: " + self.message)



####################################
####################################
# The labeling system allows
# a) labeling of resources.
# b) assigning folders to resources.
# c) marking public resources to be "of interest"
####################################
####################################


####################################
# privileges are numeric codes 1-4
####################################
class LabelCodes(object):
    """
    Label codes describe the kinds of labels that a user can create for a thing:

        * 1 or LabelCodes.LABEL:
            a regular label for the object.

        * 2 or LabelCodes.FOLDER:
            a folder for the object.

        * 3 or LabelCodes.FAVORITE:
            marks the object as a favorite.

        * 4 or LabelCodes.MINE:
            marks the object to be included in my resources


    """
    LABEL = 1
    FOLDER = 2
    FAVORITE = 3
    MINE = 4

    LABEL_CHOICES = (
        (LABEL, 'Label'),
        (FOLDER, 'Folder'),
        (FAVORITE, 'Favorite'),
        (MINE, 'Mine'),
    )

####################################
# user access to resources
####################################


class UserResourceLabels(models.Model):
    """ Labels of a user for a resource

    This model stores labels of an individual user, like an access
    control list; There are several kinds of labels documented in LabelCodes.
    These are similar in implementation but differ in semantics.
    """

    kind = models.IntegerField(choices=LabelCodes.LABEL_CHOICES,
                               editable=False,
                               default=LabelCodes.LABEL)
    # provenance of label start
    start = models.DateTimeField(editable=False, auto_now=True)

    # if end is non-null, then the label is no longer valid. Not absolutely sure we need this.
    # end  = models.DateTimeField(editable=False, null=True, auto_now=False)

    # Utilize an underlying class of User to hold labels for resources.
    # This creates an implicit query User.ulabels that represents all labels
    # for a user.
    ulabels = models.ForeignKey('UserLabels', null=True, editable=False,
                                related_name='ul2url',         # unused but must be defined and unique
                                help_text='user assigning a label')
    # There is a basic design question as to whether the target of a label should be a
    # Resource proper, or an annotation class that contains mainly methods for the resource.
    # Should this be 'BaseResource' or 'ResourceLabels'?
    rlabels = models.ForeignKey('ResourceLabels', null=True, editable=False,
                                related_name="rl2url",     # unused but must be defined and unique
                                help_text='resource to which a label applies')
    label = models.TextField()


class UserStoredLabels(models.Model):
    """ Storage class for persistent labels that are reusable across different kinds of objects
    """
    ulabels = models.ForeignKey('UserLabels', null=True, help_text='user who stored the label', related_name='ul2usl')
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
                                null=False,
                                related_name='ulabels',  # induced field in User class.
                                related_query_name='ulabels')

    ##########################################
    ##########################################
    # PUBLIC FUNCTIONS: resources
    ##########################################
    ##########################################

    ##########################################
    # get various aspects of labeling
    ##########################################

    @property
    def labeled_resources(self):
        """
        Get a list of resources labeled by a user.

        This list eliminates duplicates.

        :return: List of resource objects labeled by user.
        """
        return BaseResource.objects.filter(rlabels__rl2url__ulabels=self,
                                           rlabels__rl2url__kind=LabelCodes.LABEL).distinct()

    @property
    def filed_resources(self):
        """
        Get a list of resources filed by a user.

        This list eliminates duplicates.

        :return: List of resource objects assigned to folders by a user.
        """
        return BaseResource.objects.filter(rlabels__rl2url__ulabels=self,
                                           rlabels__rl2url__kind=LabelCodes.FOLDER).distinct()

    @property
    def favorited_resources(self):
        """
        Get a list of resources favorited by a user.

        This list eliminates duplicates.

        :return: List of resource objects marked as favorite by a user.
        """
        return BaseResource.objects.filter(rlabels__rl2url__ulabels=self,
                                           rlabels__rl2url__kind=LabelCodes.FAVORITE).distinct()

    @property
    def my_resources(self):
        """
        Get a list of resources marked as mine (add to my resources) by a user.

        This list eliminates duplicates.

        :return: List of resource objects marked as mine by a user.
        """
        return BaseResource.objects.filter(rlabels__rl2url__ulabels=self,
                                           rlabels__rl2url__kind=LabelCodes.MINE).distinct()

    # TODO: use access control to include accessible resources in this list.
    @property
    def resources_of_interest(self):
        """
        Get a list of resources the user has marked in any way.

        :return: List of resource objects that a user has marked.
        """
        return BaseResource.objects.filter(rlabels__rl2url__ulabels=self).distinct()

    def get_resources_with_label(self, this_label):
        """
        Get a list of resources with a specific label
        """
        if not isinstance(this_label, basestring):
            raise HSLUsageException("Label is not text")

        label_string = UserLabels.clean_label(this_label)                 # remove leading and trailing spaces

        return BaseResource.objects.filter(rlabels__rl2url__ulabels=self,
                                           rlabels__rl2url__kind=LabelCodes.LABEL,
                                           rlabels__rl2url__label__exact=label_string)\
                                        .distinct()\
                                        .order_by('rlabels__rl2url__label')
    @property
    def user_labels(self):
        return UserResourceLabels.objects.values_list('label', flat=True)\
                                 .filter(ulabels=self, kind=LabelCodes.LABEL)\
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
        assign a label to a resource

        :param this_resource: Resource to be assigned a label.
        :param this_label: Label to assign to resource

        Users are allowed to label any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.
        """

        # check for user error
        if not isinstance(this_resource, BaseResource):
            raise HSLUsageException("Target is not a resource")
        label_resource = this_resource.rlabels

        if not isinstance(this_label, basestring):
            raise HSLUsageException("Label is not text")

        # remove leading and trailing spaces
        label_string = UserLabels.clean_label(this_label)

        # This logic implicitly limits one to one record per resource and requester.
        UserResourceLabels.objects.get_or_create(rlabels=label_resource,
                                                 kind=LabelCodes.LABEL,
                                                 label=label_string,
                                                 ulabels=self)

    def unlabel_resource(self, this_resource, this_label):
        """ Remove one label from a resource

        :param this_resource: BaseResource from which to remove a label
        :param this_label: The label to remove. Only that labels will be removed.
        :return: none
        """
        # check for user error
        if not isinstance(this_resource, BaseResource):
            raise HSLUsageException("Target is not a resource")
        label_resource = this_resource.rlabels

        if not isinstance(this_label, basestring):
            raise HSLUsageException("Label is not text")

        # remove leading and trailing spaces
        label_string = UserLabels.clean_label(this_label)

        UserResourceLabels.objects.filter(rlabels=label_resource,
                                          label__exact=label_string,
                                          kind=LabelCodes.LABEL,
                                          ulabels=self).delete()

    def clear_resource_labels(self, this_resource):
        """ Clear all labels for a resource

        :param this_resource: BaseResource for which to clear all labels
        :return: none.
        """
        # check for user error
        if not isinstance(this_resource, BaseResource):
            raise HSLUsageException("Target is not a resource")
        label_resource = this_resource.rlabels
        UserResourceLabels.objects.filter(rlabels=label_resource,
                                          ulabels=self,
                                          kind=LabelCodes.LABEL).delete()

    ##########################################
    # filed resources
    ##########################################

    @staticmethod
    def clean_folder(name):
        folder_string = re.sub('/+', r'/', name)         # no doubled //
        folder_string = re.sub(r'^(/|\s)+', r'', folder_string)   # no leading /
        folder_string = re.sub(r'(/|\s)+$', r'', folder_string)   # no trailing /
        folder_string = re.sub(r'\s+', r' ', folder_string)       # collapse multiple whitespace, including tabs
        folder_string = re.sub(r'\s*/\s*', r'/', folder_string)   # no whitespace around /'s
        return folder_string

    def file_resource(self, this_resource, this_folder):
        """
        Specify a file folder for a resource.

        :param this_resource: Resource to share.
        :param this_folder: Folder name to assign to resource
        :return: None

        Users are allowed to file any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.

        There can only be one folder for a resource. If an attempt is made to set two;
        the first is overridden with the second.
        """

        # check for user error
        if not isinstance(this_resource, BaseResource):
            raise HSLUsageException("Target is not a resource")
        label_resource = this_resource.rlabels

        if not isinstance(this_folder, basestring):
            raise HSLUsageException("Folder is not text")

        # remove leading and trailing whitespace
        folder_string = UserLabels.clean_folder(this_folder)

        if folder_string == "":
            raise HSLUsageException("Cannot assign an empty folder name")

        # proceed to change the record if present
        # This logic implicitly limits one to one record per resource and user.
        try:
            record = UserResourceLabels.objects.get(rlabels=label_resource,
                                                    kind=LabelCodes.FOLDER,
                                                    ulabels=self)
            record.label = folder_string
            record.save()

        # only create label if it does not exist. No duplicates.
        except UserResourceLabels.DoesNotExist:
            # create a new label record
            UserResourceLabels(rlabels=label_resource,
                               kind=LabelCodes.FOLDER,
                               label=folder_string,
                               ulabels=self).save()

    def unfile_resource(self, this_resource):
        """ Clear all folders for a resource

        :param this_resource: BaseResource for which to clear all folder names

        """
        # check for user error
        if not isinstance(this_resource, BaseResource):
            raise HSLUsageException("Target is not a resource")
        label_resource = this_resource.rlabels
        UserResourceLabels.objects.filter(ulabels=self,
                                          rlabels=label_resource,
                                          kind=LabelCodes.FOLDER).delete()


    ##########################################
    # favorite resources
    ##########################################

    def favorite_resource(self, this_resource):
        """
        Mark a resource as favorite.

        :param this_resource: Resource to mark as favorite

        Users are allowed to file any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.

        There can only be one folder for a resource. If an attempt is made to set two;
        the first is overridden with the second.
        """

        # check for user error
        if not isinstance(this_resource, BaseResource):
            raise HSLUsageException("Target is not a resource")
        label_resource = this_resource.rlabels

        # proceed to change the record if present
        # This logic implicitly limits one to one record per resource and user.

        UserResourceLabels.objects.get_or_create(rlabels=label_resource,
                                                 kind=LabelCodes.FAVORITE,
                                                 ulabels=self)

    def unfavorite_resource(self, this_resource):
        """ Clear favorite label for a resource

        :param this_resource: BaseResource for which to clear favorite label

        """
        # check for user error
        if not isinstance(this_resource, BaseResource):
            raise HSLUsageException("Target is not a resource")
        label_resource = this_resource.rlabels
        UserResourceLabels.objects.filter(ulabels=self,
                                          rlabels=label_resource,
                                          kind=LabelCodes.FAVORITE).delete()


    ##########################################
    # my resources
    ##########################################

    def claim_resource(self, this_resource):
        """
        Label a resource as mine (add to my resources).

        :param this_resource: Resource to label as mine (add to my resources).

        """

        # check for user error
        if not isinstance(this_resource, BaseResource):
            raise HSLUsageException("Target is not a resource")
        label_resource = this_resource.rlabels

        # proceed to change the record if present
        # This logic implicitly limits one to one record per resource and user.

        UserResourceLabels.objects.get_or_create(rlabels=label_resource,
                                                 kind=LabelCodes.MINE,
                                                 ulabels=self)

    def unclaim_resource(self, this_resource):
        """ Clear 'mine' label for a resource (removes from my resources)

        :param this_resource: BaseResource for which to clear mine label

        """
        # check for user error
        if not isinstance(this_resource, BaseResource):
            raise HSLUsageException("Target is not a resource")
        label_resource = this_resource.rlabels
        UserResourceLabels.objects.filter(ulabels=self,
                                          rlabels=label_resource,
                                          kind=LabelCodes.MINE).delete()

    ##########################################
    # routines that apply to all kinds of annotations
    ##########################################

    def clear_resource_all(self, this_resource):
        """ Clear all annotations for a resource

        :param this_resource: BaseResource for which to clear all annotations

        """
        # check for user error
        if not isinstance(this_resource, BaseResource):
            raise HSLUsageException("Target is not a resource")
        label_resource = this_resource.rlabels
        UserResourceLabels.objects.filter(rlabels=label_resource,
                                          ulabels=self).delete()

    ##########################################
    # handling of folder hierarchies
    ##########################################

    @property
    def resource_folders(self):
        """
        Get a list of resource folders in use
        :return: List of folders with resources in them.
        """
        return UserResourceLabels.objects.values_list('label', flat=True)\
                                 .filter(ulabels=self, kind=LabelCodes.FOLDER)\
                                 .distinct().order_by('label')

    def get_resources_in_folder(self, this_folder):
        """
        Get a list of resources in a specific folder
        :param this_folder: folder for which to report
        :type this_folder: basestring
        :return: QuerySet of BaseResource references.
        :rtype: QuerySet
        """
        if not isinstance(this_folder, basestring):
            raise HSLUsageException("Label is not text")

        # remove leading and trailing spaces
        label_string = UserLabels.clean_folder(this_folder)

        return BaseResource.objects.filter(rlabels__rl2url__ulabels=self,
                                           rlabels__rl2url__kind=LabelCodes.FOLDER,
                                           rlabels__rl2url__label__exact=label_string)\
                                    .distinct()\
                                    .order_by('rlabels__rl2url__label')

    @property
    def resource_top_folders(self):
        """
        Get a list of top-level folders for a resource.
        :return: List of top-level folders as strings

        """
        top = {}
        folders = self.resource_folders
        for f in folders:
            # use dict as a set to eliminate duplicates
            top[f.split('/')[0]] = 1
        f2 = top.keys()
        f2.sort()
        return f2

    def get_resource_subfolders(self, this_folder):
        """
        Get a list of resources with a specific label
        """
        if this_folder is None:
            this_folder = ""

        if not isinstance(this_folder, basestring):
            raise HSLUsageException("Folder is not text")

        # remove leading and trailing spaces
        folder_string = UserLabels.clean_folder(this_folder)

        subs = UserResourceLabels.objects\
                                 .filter(ulabels=self,
                                         kind=LabelCodes.FOLDER,
                                         label__startswith=folder_string)\
                                 .values_list('label', flat=True)\
                                 .distinct()\
                                 .order_by('label')
        # instantiate query
        subs = list(subs)
        if folder_string != r'':
            subs = [r[len(folder_string)+1:] for r in subs]

        output = list()
        for s in subs:
            if s.find("/")>=0:
                t = s[:s.find("/")]
                if t != "":
                    output.append(t)
            else:
                if s != "":
                    output.append(s)

        output = filter(lambda x: x != '', output)
        return output

    @property
    def resource_hierarchy(self):
        """
        Compute a polymorphic nested dictionary of folders and resources.

        :return: a dict structure that mimics the structure of directories; see below.

        This routine computes a complex dictionary object that describes the
        whole folder hierarchy for a user. It is not particularly useful in views due
        to the need for recursion to parse it. The structure consists of 'folders' and
        'resources' keys, where folders is a nested structure of folders, while
        'resources' is a list of resources.

        For example, for one resource x, filed in folder 'foo/bar', it will return
            { 'folders': { 'foo': {'folders': {'bar': {'resources': [x]}}}}
        This structure is recursive in the sense that x['folders'][y] has the same structure as x.

        Note that resources are returned in random order and must be sorted to taste.
        """
        folders = self.resource_folders
        output = {}
        for f in folders:
            path = f.split(r'/')
            ptr = output
            for p in path:
                if u'folders' not in ptr:
                    ptr[u'folders']={p : {}}
                if p not in ptr[u'folders']:
                    ptr[u'folders'][p] = {}
                ptr = ptr[u'folders'][p]
            # now the cursor is set to contain files.
            ptr[u'resources'] = list(self.get_resources_in_folder(str(f)))
        return output

    @staticmethod
    def __hierarchy_sequence(folder, thing, level=0):
        """
        Return an iterable list describing the folder hierarchy.

        :param thing: the output of resource_hierarchy
        :param level: recursion level: for indentation
        :return: a list of lists that describe the folder hierarchy as a linear iterable.

        This routine is used in views to create a linear iterable that can be used to depict
        the folder hierarchy as an HTML table.
        """
        output = []
        record = [folder, level]
        if 'resources' in thing:
            record += [thing[u'resources']]
        else:
            record += [[]]
        output += [record]
        if 'folders' in thing:
            for k in thing['folders']:
                output += UserLabels.__hierarchy_sequence(k, thing['folders'][k], level+1)
        return output

    @property
    def resource_sequence(self):
        """
        Return nested list of resource folders and objects
        :return: complex nested list
        """
        hier = self.resource_hierarchy
        # throw away (unfiled) record
        return UserLabels.__hierarchy_sequence("(unfiled)", hier, 0)[1:]

    ##########################################
    # save unused labels
    ##########################################

    def save_label(self, this_label):
        """
        Save a label for use later.

        :param this_label: Label to save
        :return: None

        Users are allowed to label any resource, including resources to which they do not have access.
        This is not an access control problem because labeling information is private.
        """

        # check for user error
        if not isinstance(this_label, basestring):
            raise HSLUsageException("Label is not text")

        label_string = UserLabels.clean_label(this_label)    # remove leading and trailing spaces

        # This logic implicitly limits one to one record per resource and requester.
        try:
            UserStoredLabels.objects.get(label__exact=label_string, ulabels=self)
            # if this succeeds, resource is already labeled with this label_string.

        # only create label if it does not exist. No duplicates.
        except UserStoredLabels.DoesNotExist:
            # create a new label record
            UserStoredLabels(label=label_string, ulabels=self).save()

    def unsave_label(self, this_label):
        """ Remove the specified saved label

        :param this_label: The label to remove. Only that labels will be removed.

        """
        # check for user input error
        if not isinstance(this_label, basestring):
            raise HSLUsageException("Label is not text")

        # remove leading and trailing spaces
        label_string = UserLabels.clean_label(this_label)

        UserStoredLabels.objects.filter(label__exact=label_string, ulabels=self).delete()

    def clear_saved_labels(self):
        """
        Clear all saved labels for a user

        """
        UserStoredLabels.objects.filter(ulabels=self).delete()

    @property
    def saved_labels(self):
        """
        :return: a list of strings that constitute the saved labels
        """
        return UserStoredLabels.objects.filter(ulabels=self).values_list('label', flat=True).distinct()


class ResourceLabels(models.Model):
    """ Resource model for labeling.

    This model is injected into the BaseResource as the related name "rlabels".
    Thus for a BaseResource r, r.rlabels is this model.
    """
    #############################################
    # model variables
    #############################################

    resource = models.OneToOneField(BaseResource,
                                    editable=False,
                                    null=False,
                                    related_name='rlabels',  # induced field of BaseResource
                                    related_query_name='rlabels')

    #############################################
    # workalike queries adapt to old access control system
    #############################################

    def get_users(self):
        """
        Return a list of all users who have labeled this resource.

        :return: QuerySet that evaluates to all users holding resource.
        """
        return User.objects.filter(ulabels__ul2url__rlabels=self)

    def get_folder(self, this_user):
        """ return the folder for a resource, or null if no folder

        :return: string folder name with '/'s embedded.
        """
        if not isinstance(this_user, User):
            raise HSLUsageException("Target is not a user")
        user_labels = this_user.ulabels

        try:
            folder = UserResourceLabels.objects.values_list("label", flat=True)\
                                       .get(ulabels=user_labels,
                                            kind=LabelCodes.FOLDER,
                                            rlabels=self)
            return folder

        except UserResourceLabels.DoesNotExist:
            return None

    def get_labels(self, this_user):
        """ return the folder for a resource, or null if no folder

        :return: string folder name with '/'s embedded.
        """
        if not isinstance(this_user, User):
            raise HSLUsageException("Target is not a user")
        user_labels = this_user.ulabels

        labels = UserResourceLabels.objects\
                                   .values_list('label', flat=True)\
                                   .filter(ulabels=user_labels,
                                           kind=LabelCodes.LABEL,
                                           rlabels=self)\
                                   .order_by("label").all()
        return labels

    def is_favorite(self, this_user):
        """ return True if this resource has been favorited by a given user

        :return: True or False
        """
        if not isinstance(this_user, User):
            raise HSLUsageException("Target is not a user")
        user_labels = this_user.ulabels

        try:
            UserResourceLabels.objects.get(ulabels=user_labels,
                                           rlabels=self,
                                           kind=LabelCodes.FAVORITE)
            return True

        except UserResourceLabels.DoesNotExist:
            return False

    def is_mine(self, this_user):
        """ return True if this resource has been labeled as mine by a given user

        :return: True or False
        """
        if not isinstance(this_user, User):
            raise HSLUsageException("Target is not a user")
        user_labels = this_user.ulabels

        try:
            UserResourceLabels.objects.get(ulabels=user_labels,
                                           rlabels=self,
                                           kind=LabelCodes.MINE)
            return True

        except UserResourceLabels.DoesNotExist:
            return False