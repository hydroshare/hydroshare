"""Declare critical models for Hydroshare hs_core app."""

import os.path
import json
import arrow
import logging
from uuid import uuid4
from languages_iso import languages as iso_languages
from dateutil import parser
from lxml import etree

from django_irods.icommands import SessionException

from django.contrib.postgres.fields import HStoreField
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.db import transaction
from django.dispatch import receiver
from django.utils.timezone import now
from django_irods.storage import IrodsStorage
from django.conf import settings
from django.core.files import File
from django.core.exceptions import ObjectDoesNotExist, ValidationError, \
    SuspiciousFileOperation, PermissionDenied
from django.forms.models import model_to_dict
from django.core.urlresolvers import reverse
from django.core.validators import URLValidator

from mezzanine.pages.models import Page
from mezzanine.core.managers import PublishedManager
from mezzanine.core.models import Ownable
from mezzanine.generic.fields import CommentsField, RatingField
from mezzanine.conf import settings as s
from mezzanine.pages.managers import PageManager

from dominate.tags import div, legend, table, tbody, tr, th, td, h4

from hs_core.irods import ResourceIRODSMixin, ResourceFileIRODSMixin
import unicodedata


def clean_for_xml(s):
    """
    Remove all control characters from a unicode string in preparation for XML inclusion

    * Convert \n\n+ to unicode paragraph
    * Convert \n alone to unicode RETURN (return SYMBOL)
    * Convert control characters to spaces if last character is not space.
    * Space-pad paragraph and NL symbols as necessary

    """
    CR = unichr(0x23CE)  # carriage return unicode SYMBOL
    PARA = unichr(0xB6)  # paragraph mark unicode SYMBOL
    output = ''
    next = None
    last = None
    for ch in s:
        cat = unicodedata.category(ch)
        ISCONTROL = cat[0] == 'C'
        ISSPACE = cat[0] == 'Z'
        ISNEWLINE = (ord(ch) == 10)
        if next:
            if ISNEWLINE:  # linux '\n'
                next = PARA  # upgrade to two+ returns
            elif ISSPACE or ISCONTROL:
                pass  # ignore spaces in newline sequence
            else:
                if last != ' ':
                    output += ' '
                output += next + ' ' + ch
                next = None
                last = ch
        else:
            if ISNEWLINE:
                next = CR
            elif ISSPACE:
                if last != ' ':
                    output += ch
                    last = ch
            elif ISCONTROL:
                if last != ' ':
                    output += ' '
                    last = ' '
            else:
                output += ch
                last = ch
    return output


class GroupOwnership(models.Model):
    """Define lookup table allowing django auth users to own django auth groups."""

    group = models.ForeignKey(Group)
    owner = models.ForeignKey(User)


def get_user(request):
    """Authorize user based on API key if it was passed, otherwise just use the request's user.

    NOTE: The API key portion has been removed with TastyPie and will be restored when the
    new API is built.

    :param request:
    :return: django.contrib.auth.User
    """
    if request.user.is_authenticated():
        return User.objects.get(pk=request.user.pk)
    else:
        return request.user


def validate_user_url(value):
    """Validate that a URL is a valid URL for a hydroshare user."""
    err_message = '%s is not a valid url for hydroshare user' % value
    if value:
        url_parts = value.split('/')
        if len(url_parts) != 6:
            raise ValidationError(err_message)
        if url_parts[3] != 'user':
            raise ValidationError(err_message)

        try:
            user_id = int(url_parts[4])
        except ValueError:
            raise ValidationError(err_message)

        # check the user exists for the provided user id
        if not User.objects.filter(pk=user_id).exists():
            raise ValidationError(err_message)


class ResourcePermissionsMixin(Ownable):
    """Mix in can_* permission helper functions between users and resources."""

    creator = models.ForeignKey(User,
                                related_name='creator_of_%(app_label)s_%(class)s',
                                help_text='This is the person who first uploaded the resource',
                                )

    class Meta:
        """Define meta properties for ResourcePermissionsMixin, make abstract."""

        abstract = True

    @property
    def permissions_store(self):
        """Use PERMISSIONS_DB constant. Unsure what 's' is here."""
        return s.PERMISSIONS_DB

    def can_add(self, request):
        """Pass through can_change to determine if user can make changes to a resource."""
        return self.can_change(request)

    def can_delete(self, request):
        """Use utils.authorize method to determine if user can delete a resource."""
        # have to do import locally to avoid circular import
        from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
        return authorize(request, self.short_id,
                         needed_permission=ACTION_TO_AUTHORIZE.DELETE_RESOURCE,
                         raises_exception=False)[1]

    def can_change(self, request):
        """Use utils.authorize method to determine if user can change a resource."""
        # have to do import locally to avoid circular import
        from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
        return authorize(request, self.short_id,
                         needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                         raises_exception=False)[1]

    def can_view(self, request):
        """Use utils.authorize method to determine if user can view a resource."""
        # have to do import locally to avoid circular import
        from hs_core.views.utils import authorize, ACTION_TO_AUTHORIZE
        return authorize(request, self.short_id,
                         needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA,
                         raises_exception=False)[1]


def page_permissions_page_processor(request, page):
    """Return a dict describing permissions for current user."""
    from hs_access_control.models import PrivilegeCodes

    cm = page.get_content_model()
    can_change_resource_flags = False
    is_owner_user = False
    is_edit_user = False
    is_view_user = False
    if request.user.is_authenticated():
        if request.user.uaccess.can_change_resource_flags(cm):
            can_change_resource_flags = True

        is_owner_user = cm.raccess.owners.filter(pk=request.user.pk).exists()
        if not is_owner_user:
            is_edit_user = cm.raccess.edit_users.filter(pk=request.user.pk).exists()
            if not is_edit_user:
                is_view_user = cm.raccess.view_users.filter(pk=request.user.pk).exists()

    owners = cm.raccess.owners.all()
    editors = cm.raccess.get_users_with_explicit_access(PrivilegeCodes.CHANGE,
                                                        include_group_granted_access=False)
    viewers = cm.raccess.get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                                        include_group_granted_access=False)
    edit_groups = cm.raccess.edit_groups
    view_groups = cm.raccess.view_groups.exclude(pk__in=edit_groups)

    if request.user.is_authenticated():
        for owner in owners:
            owner.can_undo = request.user.uaccess.can_undo_share_resource_with_user(cm, owner)

        for viewer in viewers:
            viewer.can_undo = request.user.uaccess.can_undo_share_resource_with_user(cm, viewer)

        for editor in editors:
            editor.can_undo = request.user.uaccess.can_undo_share_resource_with_user(cm, editor)

        for view_grp in view_groups:
            view_grp.can_undo = request.user.uaccess.can_undo_share_resource_with_group(cm,
                                                                                        view_grp)

        for edit_grp in edit_groups:
            edit_grp.can_undo = request.user.uaccess.can_undo_share_resource_with_group(cm,
                                                                                        edit_grp)
    else:
        for owner in owners:
            owner.can_undo = False
        for viewer in viewers:
            viewer.can_undo = False
        for editor in editors:
            editor.can_undo = False
        for view_grp in view_groups:
            view_grp.can_undo = False
        for edit_grp in edit_groups:
            edit_grp.can_undo = False

    if cm.metadata.relations.all().filter(type='isReplacedBy').exists():
        is_replaced_by = cm.metadata.relations.all().filter(type='isReplacedBy').first().value
    else:
        is_replaced_by = ''

    if cm.metadata.relations.all().filter(type='isVersionOf').exists():
        is_version_of = cm.metadata.relations.all().filter(type='isVersionOf').first().value
    else:
        is_version_of = ''

    show_manage_access = False
    if not cm.raccess.published and \
            (is_owner_user or (cm.raccess.shareable and (is_view_user or is_edit_user))):
        show_manage_access = True

    return {
        'resource_type': cm._meta.verbose_name,
        'bag': cm.bags.first(),
        "edit_users": editors,
        "view_users": viewers,
        "owners": owners,
        "edit_groups": edit_groups,
        "view_groups": view_groups,
        "is_owner_user": is_owner_user,
        "is_edit_user": is_edit_user,
        "is_view_user": is_view_user,
        "can_change_resource_flags": can_change_resource_flags,
        "is_replaced_by": is_replaced_by,
        "is_version_of": is_version_of,
        "show_manage_access": show_manage_access
    }


class AbstractMetaDataElement(models.Model):
    """Define abstract class for all metadata elements."""

    term = None

    object_id = models.PositiveIntegerField()
    # see the following link the reason for having the related_name setting
    # for the content_type attribute
    # https://docs.djangoproject.com/en/1.6/topics/db/models/#abstract-related-name
    content_type = models.ForeignKey(ContentType, related_name="%(app_label)s_%(class)s_related")
    content_object = GenericForeignKey('content_type', 'object_id')

    @property
    def metadata(self):
        """Return content object that describes metadata."""
        return self.content_object

    @classmethod
    def create(cls, **kwargs):
        """Pass through kwargs to object.create method."""
        return cls.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        """Pass through kwargs to update specific metadata object."""
        element = cls.objects.get(id=element_id)
        for key, value in kwargs.iteritems():
                setattr(element, key, value)
        element.save()
        return element

    @classmethod
    def remove(cls, element_id):
        """Pass through element id to objects.get and then delete() method.

        Could not name this method as 'delete' since the parent 'Model' class has such a method
        """
        element = cls.objects.get(id=element_id)
        element.delete()

    class Meta:
        """Define meta properties for AbstractMetaDataElement class."""

        abstract = True


class HSAdaptorEditInline(object):
    """Define permissions-based helper to determine if user can edit adapter field.

    Adaptor class added for Django inplace editing to honor HydroShare user-resource permissions
    """

    @classmethod
    def can_edit(cls, adaptor_field):
        """Define permissions-based helper to determine if user can edit adapter field."""
        obj = adaptor_field.obj
        cm = obj.get_content_model()
        return cm.can_change(adaptor_field.request)


class Party(AbstractMetaDataElement):
    """Define party model to define a person."""

    description = models.URLField(null=True, blank=True, validators=[validate_user_url])
    name = models.CharField(max_length=100, null=True, blank=True)
    organization = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    phone = models.CharField(max_length=25, null=True, blank=True)
    homepage = models.URLField(null=True, blank=True)
    # to store one or more external identifier (Google Scholar, ResearchGate, ORCID etc)
    # each identifier is stored as a key/value pair {name:link}
    identifiers = HStoreField(default={})

    # list of identifier currently supported
    supported_identifiers = {'ResearchGateID': 'https://www.researchgate.net/',
                             'ORCID': 'https://orcid.org/',
                             'GoogleScholarID': 'https://scholar.google.com/',
                             'ResearcherID': 'https://www.researcherid.com/'}

    def __unicode__(self):
        """Return name field for unicode representation."""
        return self.name

    class Meta:
        """Define meta properties for Party class."""

        abstract = True

    @classmethod
    def get_post_data_with_identifiers(cls, request, as_json=True):
        identifier_names = request.POST.getlist('identifier_name')
        identifier_links = request.POST.getlist('identifier_link')
        identifiers = {}
        if identifier_links and identifier_names:
            if len(identifier_names) != len(identifier_links):
                raise Exception("Invalid data for identifiers")
            identifiers = dict(zip(identifier_names, identifier_links))
            if len(identifier_names) != len(identifiers.keys()):
                raise Exception("Invalid data for identifiers")

            if as_json:
                identifiers = json.dumps(identifiers)

        post_data_dict = request.POST.dict()
        post_data_dict['identifiers'] = identifiers

        return post_data_dict

    @classmethod
    def create(cls, **kwargs):
        """Define custom create method for Party model."""
        element_name = cls.__name__

        identifiers = kwargs.get('identifiers', '')
        if identifiers:
            identifiers = cls.validate_identifiers(identifiers)
            kwargs['identifiers'] = identifiers

        metadata_obj = kwargs['content_object']
        metadata_type = ContentType.objects.get_for_model(metadata_obj)
        if element_name == 'Creator':
            party = Creator.objects.filter(object_id=metadata_obj.id,
                                           content_type=metadata_type).last()
            creator_order = 1
            if party:
                creator_order = party.order + 1

            if ('name' not in kwargs or kwargs['name'] is None) and \
                    ('organization' not in kwargs or kwargs['organization'] is None):
                raise ValidationError(
                    "Either an organization or name is required for a creator element")

            if 'name' in kwargs and kwargs['name'] is not None:
                if len(kwargs['name'].strip()) == 0:
                    if 'organization' in kwargs and kwargs['organization'] is not None:
                        if len(kwargs['organization'].strip()) == 0:
                            raise ValidationError(
                                "Either the name or organization must not be blank for the creator "
                                "element")

            kwargs['order'] = creator_order
            party = super(Party, cls).create(**kwargs)
        else:
            party = super(Party, cls).create(**kwargs)

        return party

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update method for Party model."""
        element_name = cls.__name__
        creator_order = None
        if 'description' in kwargs:
            party = cls.objects.get(id=element_id)
            if party.description is not None and kwargs['description'] is not None:
                if len(party.description.strip()) > 0 and len(kwargs['description'].strip()) > 0:
                    if party.description != kwargs['description']:
                        raise ValidationError("HydroShare user identifier can't be changed.")

        if 'order' in kwargs and element_name == 'Creator':
            creator_order = kwargs['order']
            if creator_order <= 0:
                creator_order = 1
            del kwargs['order']

        identifiers = kwargs.get('identifiers', '')
        if identifiers:
            identifiers = cls.validate_identifiers(identifiers)
            kwargs['identifiers'] = identifiers

        party = super(Party, cls).update(element_id, **kwargs)

        if isinstance(party, Creator) and creator_order is not None:
            if party.order != creator_order:
                resource_creators = Creator.objects.filter(
                    object_id=party.object_id, content_type__pk=party.content_type.id).all()

                if creator_order > len(resource_creators):
                    creator_order = len(resource_creators)

                for res_cr in resource_creators:
                    if party.order > creator_order:
                        if res_cr.order < party.order and not res_cr.order < creator_order:
                            res_cr.order += 1
                            res_cr.save()
                    else:
                        if res_cr.order > party.order:
                            res_cr.order -= 1
                            res_cr.save()

                party.order = creator_order
                party.save()

    @classmethod
    def remove(cls, element_id):
        """Define custom remove method for Party model."""
        party = cls.objects.get(id=element_id)

        # if we are deleting a creator, then we have to update the order attribute of remaining
        # creators associated with a resource
        # make sure we are not deleting all creators of a resource
        if isinstance(party, Creator):
            if Creator.objects.filter(object_id=party.object_id,
                                      content_type__pk=party.content_type.id).count() == 1:
                raise ValidationError("The only creator of the resource can't be deleted.")

            creators_to_update = Creator.objects.filter(
                object_id=party.object_id,
                content_type__pk=party.content_type.id).exclude(order=party.order).all()

            for cr in creators_to_update:
                if cr.order > party.order:
                    cr.order -= 1
                    cr.save()
        party.delete()

    @classmethod
    def validate_identifiers(cls, identifiers):
        """Validates optional identifiers for user/creator/contributor
        :param  identifiers: identifier data as a json string or as a dict
        """

        if not isinstance(identifiers, dict):
            if identifiers:
                # validation form can populate the dict(kwargs) with key 'identifiers" with
                # value of empty string if data passed to the validation form did not had this
                # key. In that case no need to convert the string to dict
                try:
                    identifiers = json.loads(identifiers)
                except ValueError:
                    raise ValidationError("Value for identifiers not in the correct format")
        # identifiers = kwargs['identifiers']
        if identifiers:
            # validate the identifiers are one of the supported ones
            for name in identifiers:
                if name not in cls.supported_identifiers:
                    raise ValidationError("Invalid data found for identifiers. "
                                          "{} not a supported identifier.". format(name))
            # validate identifier values - check for duplicate links
            links = [l.lower() for l in identifiers.values()]
            if len(links) != len(set(links)):
                raise ValidationError("Invalid data found for identifiers. "
                                      "Duplicate identifier links found.")

            for link in links:
                validator = URLValidator()
                try:
                    validator(link)
                except ValidationError:
                    raise ValidationError("Invalid data found for identifiers. "
                                          "Identifier link must be a URL.")

            # validate identifier keys - check for duplicate names
            names = [n.lower() for n in identifiers.keys()]
            if len(names) != len(set(names)):
                raise ValidationError("Invalid data found for identifiers. "
                                      "Duplicate identifier names found")

            # validate that the links for the known identifiers are valid
            for id_name in cls.supported_identifiers:
                id_link = identifiers.get(id_name, '')
                if id_link:
                    if not id_link.startswith(cls.supported_identifiers[id_name]) \
                            or len(id_link) <= len(cls.supported_identifiers[id_name]):
                        raise ValidationError("URL for {} is invalid".format(id_name))
        return identifiers


class Contributor(Party):
    """Extend Party model with the term of 'Contributor'."""

    term = 'Contributor'


class Creator(Party):
    """Extend Party model with the term of 'Creator' and a proper ordering."""

    term = "Creator"
    order = models.PositiveIntegerField()

    class Meta:
        """Define meta properties for Creator class."""

        ordering = ['order']


class Description(AbstractMetaDataElement):
    """Define Description metadata element model."""

    term = 'Description'
    abstract = models.TextField()

    def __unicode__(self):
        """Return abstract field for unicode representation."""
        return self.abstract

    class Meta:
        """Define meta properties for Description model."""

        unique_together = ("content_type", "object_id")

    @classmethod
    def update(cls, element_id, **kwargs):
        """Create custom update method for Description model."""
        element = Description.objects.get(id=element_id)
        resource = element.metadata.resource
        if resource.resource_type == "TimeSeriesResource":
            element.metadata.is_dirty = True
            element.metadata.save()

        super(Description, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        """Create custom remove method for Description model."""
        raise ValidationError("Description element of a resource can't be deleted.")


class Title(AbstractMetaDataElement):
    """Define Title metadata element model."""

    term = 'Title'
    value = models.CharField(max_length=300)

    def __unicode__(self):
        """Return value field for unicode representation."""
        return self.value

    class Meta:
        """Define meta properties for Title class."""

        unique_together = ("content_type", "object_id")

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update function for Title class."""
        element = Title.objects.get(id=element_id)
        resource = element.metadata.resource
        if resource.resource_type == "TimeSeriesResource":
            element.metadata.is_dirty = True
            element.metadata.save()

        super(Title, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        """Define custom remove function for Title class."""
        raise ValidationError("Title element of a resource can't be deleted.")


class Type(AbstractMetaDataElement):
    """Define Type metadata element model."""

    term = 'Type'
    url = models.URLField()

    def __unicode__(self):
        """Return url field for unicode representation."""
        return self.url

    class Meta:
        """Define meta properties for Type class."""

        unique_together = ("content_type", "object_id")

    @classmethod
    def remove(cls, element_id):
        """Define custom remove function for Type model."""
        raise ValidationError("Type element of a resource can't be deleted.")


class Date(AbstractMetaDataElement):
    """Define Date metadata model."""

    DATE_TYPE_CHOICES = (
        ('created', 'Created'),
        ('modified', 'Modified'),
        ('valid', 'Valid'),
        ('available', 'Available'),
        ('published', 'Published')
    )

    term = 'Date'
    type = models.CharField(max_length=20, choices=DATE_TYPE_CHOICES)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)

    def __unicode__(self):
        """Return either {type} {start} or {type} {start} {end} for unicode representation."""
        if self.end_date:
            return "{type} {start} {end}".format(type=self.type, start=self.start_date,
                                                 end=self.end_date)
        return "{type} {start}".format(type=self.type, start=self.start_date)

    class Meta:
        """Define meta properties for Date class."""

        unique_together = ("type", "content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        """Define custom create method for Date model."""
        if 'type' in kwargs:
            if not kwargs['type'] in dict(cls.DATE_TYPE_CHOICES).keys():
                raise ValidationError('Invalid date type:%s' % kwargs['type'])

            # get matching resource
            metadata_obj = kwargs['content_object']
            resource = BaseResource.objects.filter(object_id=metadata_obj.id).first()

            if kwargs['type'] != 'valid':
                if 'end_date' in kwargs:
                    del kwargs['end_date']

            if 'start_date' in kwargs:
                if isinstance(kwargs['start_date'], basestring):
                    kwargs['start_date'] = parser.parse(kwargs['start_date'])
            if kwargs['type'] == 'published':
                if not resource.raccess.published:
                    raise ValidationError("Resource is not published yet.")
            elif kwargs['type'] == 'available':
                if not resource.raccess.public:
                    raise ValidationError("Resource has not been made public yet.")
            elif kwargs['type'] == 'valid':
                if 'end_date' in kwargs:
                    if isinstance(kwargs['end_date'], basestring):
                        kwargs['end_date'] = parser.parse(kwargs['end_date'])
                    if kwargs['start_date'] > kwargs['end_date']:
                        raise ValidationError("For date type valid, end date must be a date "
                                              "after the start date.")

            return super(Date, cls).create(**kwargs)

        else:
            raise ValidationError("Type of date element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update model for Date model."""
        dt = Date.objects.get(id=element_id)

        if 'start_date' in kwargs:
            if isinstance(kwargs['start_date'], basestring):
                kwargs['start_date'] = parser.parse(kwargs['start_date'])
            if dt.type == 'created':
                raise ValidationError("Resource creation date can't be changed")
            elif dt.type == 'modified':
                dt.start_date = now().isoformat()
                dt.save()
            elif dt.type == 'valid':
                if 'end_date' in kwargs:
                    if isinstance(kwargs['end_date'], basestring):
                        kwargs['end_date'] = parser.parse(kwargs['end_date'])
                    if kwargs['start_date'] > kwargs['end_date']:
                        raise ValidationError("For date type valid, end date must be a date "
                                              "after the start date.")
                    dt.start_date = kwargs['start_date']
                    dt.end_date = kwargs['end_date']
                    dt.save()
                else:
                    if dt.end_date:
                        if kwargs['start_date'] > dt.end_date:
                            raise ValidationError("For date type valid, end date must be a date "
                                                  "after the start date.")
                    dt.start_date = kwargs['start_date']
                    dt.save()
            else:
                dt.start_date = kwargs['start_date']
                dt.save()
        elif dt.type == 'modified':
            dt.start_date = now().isoformat()
            dt.save()

    @classmethod
    def remove(cls, element_id):
        """Define custom remove method for Date model."""
        dt = Date.objects.get(id=element_id)

        if dt.type in ['created', 'modified']:
            raise ValidationError("Date element of type:%s can't be deleted." % dt.type)

        dt.delete()


class Relation(AbstractMetaDataElement):
    """Define Relation custom metadata model."""

    SOURCE_TYPES = (
        ('isHostedBy', 'Hosted By'),
        ('isCopiedFrom', 'Copied From'),
        ('isPartOf', 'Part Of'),
        ('hasPart', 'Has Part'),
        ('isExecutedBy', 'Executed By'),
        ('isCreatedBy', 'Created By'),
        ('isVersionOf', 'Version Of'),
        ('isReplacedBy', 'Replaced By'),
        ('isDataFor', 'Data For'),
        ('cites', 'Cites'),
        ('isDescribedBy', 'Described By'),
    )

    # HS_RELATION_TERMS contains hydroshare custom terms that are not Dublin Core terms
    HS_RELATION_TERMS = ('isHostedBy', 'isCopiedFrom', 'isExecutedBy', 'isCreatedBy', 'isDataFor',
                         'cites', 'isDescribedBy')

    term = 'Relation'
    type = models.CharField(max_length=100, choices=SOURCE_TYPES)
    value = models.CharField(max_length=500)

    def __str__(self):
        """Return {type} {value} for string representation."""
        return "{type} {value}".format(type=self.type, value=self.value)

    def __unicode__(self):
        """Return {type} {value} for unicode representation (deprecated)."""
        return "{type} {value}".format(type=self.type, value=self.value)

    @classmethod
    def create(cls, **kwargs):
        """Define custom create method for Relation class."""
        if 'type' not in kwargs:
            ValidationError("Type of relation element is missing.")
        if 'value' not in kwargs:
            ValidationError("Value of relation element is missing.")

        if not kwargs['type'] in dict(cls.SOURCE_TYPES).keys():
            raise ValidationError('Invalid relation type:%s' % kwargs['type'])

        # ensure isHostedBy and isCopiedFrom are mutually exclusive
        metadata_obj = kwargs['content_object']
        metadata_type = ContentType.objects.get_for_model(metadata_obj)

        # avoid creating duplicate element (same type and same value)
        if Relation.objects.filter(type=kwargs['type'],
                                   value=kwargs['value'],
                                   object_id=metadata_obj.id,
                                   content_type=metadata_type).exists():
            raise ValidationError('Relation element of the same type '
                                  'and value already exists.')

        if kwargs['type'] == 'isHostedBy' and \
           Relation.objects.filter(type='isCopiedFrom', object_id=metadata_obj.id,
                                   content_type=metadata_type).exists():
            raise ValidationError('Relation type:%s cannot be created since '
                                  'isCopiedFrom relation already exists.' % kwargs['type'])
        elif kwargs['type'] == 'isCopiedFrom' and \
                Relation.objects.filter(type='isHostedBy', object_id=metadata_obj.id,
                                        content_type=metadata_type).exists():
            raise ValidationError('Relation type:%s cannot be created since '
                                  'isHostedBy relation already exists.' % kwargs['type'])

        return super(Relation, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update method for Relation class."""
        if 'type' not in kwargs:
            ValidationError("Type of relation element is missing.")
        if 'value' not in kwargs:
            ValidationError("Value of relation element is missing.")

        if not kwargs['type'] in dict(cls.SOURCE_TYPES).keys():
            raise ValidationError('Invalid relation type:%s' % kwargs['type'])

        # ensure isHostedBy and isCopiedFrom are mutually exclusive
        rel = Relation.objects.get(id=element_id)
        if rel.type != kwargs['type']:
            if kwargs['type'] == 'isHostedBy' and \
                Relation.objects.filter(type='isCopiedFrom', object_id=rel.object_id,
                                        content_type__pk=rel.content_type.id).exists():
                raise ValidationError('Relation type:%s cannot be updated since '
                                      'isCopiedFrom relation already exists.' % rel.type)
            elif kwargs['type'] == 'isCopiedFrom' and \
                Relation.objects.filter(type='isHostedBy', object_id=rel.object_id,
                                        content_type__pk=rel.content_type.id).exists():
                raise ValidationError('Relation type:%s cannot be updated since '
                                      'isHostedBy relation already exists.' % rel.type)

        # avoid changing this relation to an existing relation of same type and same value
        metadata_obj = kwargs['content_object']
        metadata_type = ContentType.objects.get_for_model(metadata_obj)
        qs = Relation.objects.filter(type=kwargs['type'],
                                     value=kwargs['value'],
                                     object_id=metadata_obj.id,
                                     content_type=metadata_type)

        if qs.exists() and qs.first() != rel:
            # this update will create a duplicate relation element
            raise ValidationError('A relation element of the same type and value already exists.')

        super(Relation, cls).update(element_id, **kwargs)


class Identifier(AbstractMetaDataElement):
    """Create Identifier custom metadata element."""

    term = 'Identifier'
    name = models.CharField(max_length=100)
    url = models.URLField(unique=True)

    def __unicode__(self):
        """Return {name} {url} for unicode representation."""
        return "{name} {url}".format(name=self.name, url=self.url)

    @classmethod
    def create(cls, **kwargs):
        """Define custom create method for Identifier model."""
        if 'name' in kwargs:
            metadata_obj = kwargs['content_object']
            # get matching resource
            resource = BaseResource.objects.filter(object_id=metadata_obj.id).first()
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            # check the identifier name doesn't already exist - identifier name
            # needs to be unique per resource
            idf = Identifier.objects.filter(name__iexact=kwargs['name'],
                                            object_id=metadata_obj.id,
                                            content_type=metadata_type).first()
            if idf:
                raise ValidationError('Identifier name:%s already exists' % kwargs['name'])
            if kwargs['name'].lower() == 'doi':
                if not resource.doi:
                    raise ValidationError("Identifier of 'DOI' type can't be created for a "
                                          "resource that has not been assigned a DOI yet.")

            return super(Identifier, cls).create(**kwargs)

        else:
            raise ValidationError("Name of identifier element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update method for Identifier model."""
        idf = Identifier.objects.get(id=element_id)

        if 'name' in kwargs:
            if idf.name.lower() != kwargs['name'].lower():
                if idf.name.lower() == 'hydroshareidentifier':
                    if 'migration' not in kwargs:
                        raise ValidationError("Identifier name 'hydroshareIdentifier' can't "
                                              "be changed.")

                if idf.name.lower() == 'doi':
                    raise ValidationError("Identifier name 'DOI' can't be changed.")

                # check this new identifier name not already exists
                if Identifier.objects.filter(name__iexact=kwargs['name'], object_id=idf.object_id,
                                             content_type__pk=idf.content_type.id).count() > 0:
                    if 'migration' not in kwargs:
                        raise ValidationError('Identifier name:%s already exists.'
                                              % kwargs['name'])

        if 'url' in kwargs:
            if idf.url.lower() != kwargs['url'].lower():
                if idf.name.lower() == 'hydroshareidentifier':
                    if 'migration' not in kwargs:
                        raise ValidationError("Hydroshare identifier url value can't be changed.")

                # check this new identifier url not already exists
                if Identifier.objects.filter(url__iexact=kwargs['url'], object_id=idf.object_id,
                                             content_type__pk=idf.content_type.id).count() > 0:
                    raise ValidationError('Identifier URL:%s already exists.' % kwargs['url'])

        super(Identifier, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        """Define custom remove method for Idenfitier method."""
        idf = Identifier.objects.get(id=element_id)

        # get matching resource
        resource = BaseResource.objects.filter(object_id=idf.content_object.id).first()
        if idf.name.lower() == 'hydroshareidentifier':
            raise ValidationError("Hydroshare identifier:%s can't be deleted." % idf.name)

        if idf.name.lower() == 'doi':
            if resource.doi:
                raise ValidationError("Hydroshare identifier:%s can't be deleted for a resource "
                                      "that has been assigned a DOI." % idf.name)
        idf.delete()


class Publisher(AbstractMetaDataElement):
    """Define Publisher custom metadata model."""

    term = 'Publisher'
    name = models.CharField(max_length=200)
    url = models.URLField()

    def __unicode__(self):
        """Return {name} {url} for unicode representation of Publisher model."""
        return "{name} {url}".format(name=self.name, url=self.url)

    class Meta:
        """Define meta properties for Publisher model."""

        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        """Define custom create method for Publisher model."""
        metadata_obj = kwargs['content_object']
        # get matching resource
        resource = BaseResource.objects.filter(object_id=metadata_obj.id).first()
        if not resource.raccess.published:
            raise ValidationError("Publisher element can't be created for a resource that "
                                  "is not yet published.")

        publisher_CUAHSI = "Consortium of Universities for the Advancement of Hydrologic " \
                           "Science, Inc. (CUAHSI)"

        if resource.files.all():
            # if the resource has content files, set CUAHSI as the publisher
            if 'name' in kwargs:
                if kwargs['name'].lower() != publisher_CUAHSI.lower():
                    raise ValidationError("Invalid publisher name")

            kwargs['name'] = publisher_CUAHSI
            if 'url' in kwargs:
                if kwargs['url'].lower() != 'https://www.cuahsi.org':
                    raise ValidationError("Invalid publisher URL")

            kwargs['url'] = 'https://www.cuahsi.org'
        else:
            # make sure we are not setting CUAHSI as publisher for a resource
            # that has no content files
            if 'name' in kwargs:
                if kwargs['name'].lower() == publisher_CUAHSI.lower():
                    raise ValidationError("Invalid publisher name")
            if 'url' in kwargs:
                if kwargs['url'].lower() == 'https://www.cuahsi.org':
                    raise ValidationError("Invalid publisher URL")

        return super(Publisher, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update method for Publisher model."""
        raise ValidationError("Publisher element can't be updated.")

    @classmethod
    def remove(cls, element_id):
        """Define custom remove method for Publisher model."""
        raise ValidationError("Publisher element can't be deleted.")


class Language(AbstractMetaDataElement):
    """Define language custom metadata model."""

    term = 'Language'
    code = models.CharField(max_length=3, choices=iso_languages)

    class Meta:
        """Define meta properties for Language model."""

        unique_together = ("content_type", "object_id")

    def __unicode__(self):
        """Return code field for unicode representation."""
        return self.code

    @classmethod
    def create(cls, **kwargs):
        """Define custom create method for Language model."""
        if 'code' in kwargs:
            # check the code is a valid code
            if not [t for t in iso_languages if t[0] == kwargs['code']]:
                raise ValidationError('Invalid language code:%s' % kwargs['code'])

            return super(Language, cls).create(**kwargs)
        else:
            raise ValidationError("Language code is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update method for Language model."""
        if 'code' in kwargs:
            # validate language code
            if not [t for t in iso_languages if t[0] == kwargs['code']]:
                raise ValidationError('Invalid language code:%s' % kwargs['code'])

            super(Language, cls).update(element_id, **kwargs)
        else:
            raise ValidationError('Language code is missing.')


class Coverage(AbstractMetaDataElement):
    """Define Coverage custom metadata element model."""

    COVERAGE_TYPES = (
        ('box', 'Box'),
        ('point', 'Point'),
        ('period', 'Period')
    )

    term = 'Coverage'
    type = models.CharField(max_length=20, choices=COVERAGE_TYPES)

    def __unicode__(self):
        """Return {type} {value} for unicode representation."""
        return "{type} {value}".format(type=self.type, value=self._value)

    class Meta:
        """Define meta properties for Coverage model."""

        unique_together = ("type", "content_type", "object_id")
    """
    _value field stores a json string. The content of the json
     string depends on the type of coverage as shown below. All keys shown in
     json string are required.

     For coverage type: period
         _value = "{'name':coverage name value here (optional), 'start':start date value,
         'end':end date value, 'scheme':'W3C-DTF}"

     For coverage type: point
         _value = "{'east':east coordinate value,
                    'north':north coordinate value,
                    'units:units applying to (east. north),
                    'name':coverage name value here (optional),
                    'elevation': coordinate in the vertical direction (optional),
                    'zunits': units for elevation (optional),
                    'projection': name of the projection (optional),
                    }"

     For coverage type: box
         _value = "{'northlimit':northenmost coordinate value,
                    'eastlimit':easternmost coordinate value,
                    'southlimit':southernmost coordinate value,
                    'westlimit':westernmost coordinate value,
                    'units:units applying to 4 limits (north, east, south & east),
                    'name':coverage name value here (optional),
                    'uplimit':uppermost coordinate value (optional),
                    'downlimit':lowermost coordinate value (optional),
                    'zunits': units for uplimit/downlimit (optional),
                    'projection': name of the projection (optional)}"
    """
    _value = models.CharField(max_length=1024)

    @property
    def value(self):
        """Return json representation of coverage values."""
        return json.loads(self._value)

    @classmethod
    def create(cls, **kwargs):
        """Define custom create method for Coverage model.

        data for the coverage value attribute must be provided as a dictionary
        Note that kwargs['_value'] is a JSON-serialized unicode string dictionary
        generated from django.forms.models.model_to_dict() which converts model values
        to dictionaries.
        """
        if 'type' in kwargs:
            # check the type doesn't already exists - we allow only one coverage type per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)

            if not kwargs['type'] in dict(cls.COVERAGE_TYPES).keys():
                raise ValidationError('Invalid coverage type:%s' % kwargs['type'])

            if kwargs['type'] == 'box':
                # check that there is not already a coverage of point type
                coverage = Coverage.objects.filter(type='point', object_id=metadata_obj.id,
                                                   content_type=metadata_type).first()
                if coverage:
                    raise ValidationError("Coverage type 'Box' can't be created when there "
                                          "is a coverage of type 'Point'")
            elif kwargs['type'] == 'point':
                # check that there is not already a coverage of box type
                coverage = Coverage.objects.filter(type='box', object_id=metadata_obj.id,
                                                   content_type=metadata_type).first()
                if coverage:
                    raise ValidationError("Coverage type 'Point' can't be created when "
                                          "there is a coverage of type 'Box'")

            value_arg_dict = None
            if 'value' in kwargs:
                value_arg_dict = kwargs['value']
            elif '_value' in kwargs:
                value_arg_dict = json.loads(kwargs['_value'])

            if value_arg_dict is not None:
                cls.validate_coverage_type_value_attributes(kwargs['type'], value_arg_dict)

                if kwargs['type'] == 'period':
                    value_dict = {k: v for k, v in value_arg_dict.iteritems()
                                  if k in ('name', 'start', 'end')}
                elif kwargs['type'] == 'point':
                    value_dict = {k: v for k, v in value_arg_dict.iteritems()
                                  if k in ('name', 'east', 'north', 'units', 'elevation',
                                           'zunits', 'projection')}
                elif kwargs['type'] == 'box':
                    value_dict = {k: v for k, v in value_arg_dict.iteritems()
                                  if k in ('units', 'northlimit', 'eastlimit', 'southlimit',
                                           'westlimit', 'name', 'uplimit', 'downlimit',
                                           'zunits', 'projection')}

                if kwargs['type'] == 'box' or kwargs['type'] == 'point':
                    if 'projection' not in value_dict:
                        value_dict['projection'] = 'WGS 84 EPSG:4326'

                value_json = json.dumps(value_dict)
                if 'value' in kwargs:
                    del kwargs['value']
                kwargs['_value'] = value_json
                return super(Coverage, cls).create(**kwargs)

            else:
                raise ValidationError('Coverage value is missing.')

        else:
            raise ValidationError("Type of coverage element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom create method for Coverage model.

        data for the coverage value attribute must be provided as a dictionary
        """
        cov = Coverage.objects.get(id=element_id)

        changing_coverage_type = False

        if 'type' in kwargs:
            changing_coverage_type = cov.type != kwargs['type']
            if 'value' in kwargs:
                cls.validate_coverage_type_value_attributes(kwargs['type'], kwargs['value'])
            else:
                raise ValidationError('Coverage value is missing.')

        if 'value' in kwargs:
            if changing_coverage_type:
                value_dict = {}
                cov.type = kwargs['type']
            else:
                value_dict = cov.value

            if 'name' in kwargs['value']:
                value_dict['name'] = kwargs['value']['name']

            if cov.type == 'period':
                for item_name in ('start', 'end'):
                    if item_name in kwargs['value']:
                        value_dict[item_name] = kwargs['value'][item_name]
            elif cov.type == 'point':
                for item_name in ('east', 'north', 'units', 'elevation', 'zunits', 'projection'):
                    if item_name in kwargs['value']:
                        value_dict[item_name] = kwargs['value'][item_name]
            elif cov.type == 'box':
                for item_name in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit',
                                  'uplimit', 'downlimit', 'zunits', 'projection'):
                    if item_name in kwargs['value']:
                        value_dict[item_name] = kwargs['value'][item_name]

            value_json = json.dumps(value_dict)
            del kwargs['value']
            kwargs['_value'] = value_json

        super(Coverage, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        """Define custom remove method for Coverage model."""
        raise ValidationError("Coverage element can't be deleted.")

    def add_to_xml_container(self, container):
        """Update etree SubElement container with coverage values."""
        NAMESPACES = CoreMetaData.NAMESPACES
        dc_coverage = etree.SubElement(container, '{%s}coverage' % NAMESPACES['dc'])
        cov_dcterm = '{%s}' + self.type
        dc_coverage_dcterms = etree.SubElement(dc_coverage,
                                               cov_dcterm % NAMESPACES['dcterms'])
        rdf_coverage_value = etree.SubElement(dc_coverage_dcterms,
                                              '{%s}value' % NAMESPACES['rdf'])
        if self.type == 'period':
            start_date = parser.parse(self.value['start'])
            end_date = parser.parse(self.value['end'])
            cov_value = 'start=%s; end=%s; scheme=W3C-DTF' % (start_date.isoformat(),
                                                              end_date.isoformat())

            if 'name' in self.value:
                cov_value = 'name=%s; ' % self.value['name'] + cov_value

        elif self.type == 'point':
            cov_value = 'east=%s; north=%s; units=%s' % (self.value['east'],
                                                         self.value['north'],
                                                         self.value['units'])
            if 'name' in self.value:
                cov_value = 'name=%s; ' % self.value['name'] + cov_value
            if 'elevation' in self.value:
                cov_value += '; elevation=%s' % self.value['elevation']
                if 'zunits' in self.value:
                    cov_value += '; zunits=%s' % self.value['zunits']
            if 'projection' in self.value:
                cov_value += '; projection=%s' % self.value['projection']

        else:
            # this is box type
            cov_value = 'northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s; units=%s' \
                        % (self.value['northlimit'], self.value['eastlimit'],
                           self.value['southlimit'], self.value['westlimit'],
                           self.value['units'])

            if 'name' in self.value:
                cov_value = 'name=%s; ' % self.value['name'] + cov_value
            if 'uplimit' in self.value:
                cov_value += '; uplimit=%s' % self.value['uplimit']
            if 'downlimit' in self.value:
                cov_value += '; downlimit=%s' % self.value['downlimit']
            if 'uplimit' in self.value or 'downlimit' in self.value:
                cov_value += '; zunits=%s' % self.value['zunits']
            if 'projection' in self.value:
                cov_value += '; projection=%s' % self.value['projection']

        rdf_coverage_value.text = cov_value

    @classmethod
    def validate_coverage_type_value_attributes(cls, coverage_type, value_dict):
        """Validate values based on coverage type."""
        if coverage_type == 'period':
            # check that all the required sub-elements exist
            if 'start' not in value_dict or 'end' not in value_dict:
                raise ValidationError("For coverage of type 'period' values for both start date "
                                      "and end date are needed.")
        elif coverage_type == 'point':
            # check that all the required sub-elements exist
            if 'east' not in value_dict or 'north' not in value_dict or 'units' not in value_dict:
                raise ValidationError("For coverage of type 'point' values for 'east', 'north' "
                                      "and 'units' are needed.")

            for value_item in ('east', 'north'):
                try:
                    value_dict[value_item] = float(value_dict[value_item])
                except TypeError:
                    raise ValidationError("Value for '{}' must be numeric".format(value_item))

            if value_dict['east'] < -180 or value_dict['east'] > 180:
                raise ValidationError("Value for East longitude should be "
                                      "in the range of -180 to 180")

            if value_dict['north'] < -90 or value_dict['north'] > 90:
                raise ValidationError("Value for North latitude should be "
                                      "in the range of -90 to 90")

        elif coverage_type == 'box':
            # check that all the required sub-elements exist
            for value_item in ['units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit']:
                if value_item not in value_dict:
                    raise ValidationError("For coverage of type 'box' values for one or more "
                                          "bounding box limits or 'units' is missing.")
                else:
                    if value_item != 'units':
                        try:
                            value_dict[value_item] = float(value_dict[value_item])
                        except TypeError:
                            raise ValidationError("Value for '{}' must be numeric"
                                                  .format(value_item))

            if value_dict['northlimit'] < -90 or value_dict['northlimit'] > 90:
                raise ValidationError("Value for North latitude should be "
                                      "in the range of -90 to 90")

            if value_dict['southlimit'] < -90 or value_dict['southlimit'] > 90:
                raise ValidationError("Value for South latitude should be "
                                      "in the range of -90 to 90")

            if (value_dict['northlimit'] < 0 and value_dict['southlimit'] < 0) or (
                    value_dict['northlimit'] > 0 and value_dict['southlimit'] > 0):
                if value_dict['northlimit'] < value_dict['southlimit']:
                    raise ValidationError("Value for North latitude must be greater than or "
                                          "equal to that of South latitude.")

            if value_dict['eastlimit'] < -180 or value_dict['eastlimit'] > 180:
                raise ValidationError("Value for East longitude should be "
                                      "in the range of -180 to 180")

            if value_dict['westlimit'] < -180 or value_dict['westlimit'] > 180:
                raise ValidationError("Value for West longitude should be "
                                      "in the range of -180 to 180")

            if (value_dict['eastlimit'] < 0 and value_dict['westlimit'] < 0) or (
                    value_dict['eastlimit'] > 0 and value_dict['westlimit'] > 0):
                if value_dict['eastlimit'] < value_dict['westlimit']:
                    raise ValidationError("Value for East longitude must be greater than or "
                                          "equal to that of West longitude.")

    def get_html(self, pretty=True):
        """Use the dominate module to generate element display HTML.

        This function should be used for displaying one spatial coverage element
        or one temporal coverage element
        """
        root_div = div(cls="col-xs-6 col-sm-6", style="margin-bottom:40px;")

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            if self.type == 'box' or self.type == 'point':
                legend('Spatial Coverage')
                with table(cls='custom-table'):
                    with tbody():
                        with tr():
                            get_th('Coordinate Reference System')
                            td(self.value['projection'])
                        with tr():
                            get_th('Coordinate Reference System Unit')
                            td(self.value['units'])

                h4('Extent')
                with table(cls='custom-table'):
                    if self.type == 'box':
                        with tbody():
                            with tr():
                                get_th('North')
                                td(self.value['northlimit'])
                            with tr():
                                get_th('West')
                                td(self.value['westlimit'])
                            with tr():
                                get_th('South')
                                td(self.value['southlimit'])
                            with tr():
                                get_th('East')
                                td(self.value['eastlimit'])
                    else:
                        with tr():
                            get_th('North')
                            td(self.value['north'])
                        with tr():
                            get_th('East')
                            td(self.value['east'])
            else:
                legend('Temporal Coverage')
                start_date = parser.parse(self.value['start'])
                end_date = parser.parse(self.value['end'])
                with table(cls='custom-table'):
                    with tbody():
                        with tr():
                            get_th('Start Date')
                            td(start_date.strftime('%m/%d/%Y'))
                        with tr():
                            get_th('End Date')
                            td(end_date.strftime('%m/%d/%Y'))

        return root_div.render(pretty=pretty)

    @classmethod
    def get_temporal_html_form(cls, resource, element=None, file_type=False, allow_edit=True):
        """Return CoverageTemporalForm for Coverage model."""
        from .forms import CoverageTemporalForm
        coverage_data_dict = dict()
        if element is not None:
            start_date = parser.parse(element.value['start'])
            end_date = parser.parse(element.value['end'])
            # change the date format to match with datepicker date format
            coverage_data_dict['start'] = start_date.strftime('%m/%d/%Y')
            coverage_data_dict['end'] = end_date.strftime('%m/%d/%Y')

        coverage_form = CoverageTemporalForm(initial=coverage_data_dict, allow_edit=allow_edit,
                                             res_short_id=resource.short_id if resource else None,
                                             element_id=element.id if element else None,
                                             file_type=file_type)
        return coverage_form

    @classmethod
    def get_spatial_html_form(cls, resource, element=None, allow_edit=True, file_type=False):
        """Return SpatialCoverageForm for Coverage model."""
        from .forms import CoverageSpatialForm
        coverage_data_dict = dict()

        if element is not None:
            coverage_data_dict['type'] = element.type
            coverage_data_dict['name'] = element.value.get('name', "")
            if element.type == 'box':
                coverage_data_dict['northlimit'] = element.value['northlimit']
                coverage_data_dict['eastlimit'] = element.value['eastlimit']
                coverage_data_dict['southlimit'] = element.value['southlimit']
                coverage_data_dict['westlimit'] = element.value['westlimit']
            else:
                coverage_data_dict['east'] = element.value['east']
                coverage_data_dict['north'] = element.value['north']
                coverage_data_dict['elevation'] = element.value.get('elevation', None)

        coverage_form = CoverageSpatialForm(initial=coverage_data_dict, allow_edit=allow_edit,
                                            res_short_id=resource.short_id if resource else None,
                                            element_id=element.id if element else None,
                                            file_type=file_type)
        return coverage_form


class Format(AbstractMetaDataElement):
    """Define Format custom metadata element model."""

    term = 'Format'
    value = models.CharField(max_length=150)

    class Meta:
        """Define meta properties for Format model."""

        unique_together = ("value", "content_type", "object_id")

    def __unicode__(self):
        """Return value field for unicode representation."""
        return self.value


class FundingAgency(AbstractMetaDataElement):
    """Define FundingAgency custom metadata element mode."""

    term = 'FundingAgency'
    agency_name = models.TextField(null=False)
    award_title = models.TextField(null=True, blank=True)
    award_number = models.TextField(null=True, blank=True)
    agency_url = models.URLField(null=True, blank=True)

    def __unicode__(self):
        """Return agency_name field for unicode representation."""
        return self.agency_name

    @classmethod
    def create(cls, **kwargs):
        """Define custom create method for FundingAgency model."""
        agency_name = kwargs.get('agency_name', None)
        if agency_name is None or len(agency_name.strip()) == 0:
            raise ValidationError("Agency name is missing")

        return super(FundingAgency, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update method for Agency model."""
        agency_name = kwargs.get('agency_name', None)
        if agency_name and len(agency_name.strip()) == 0:
            raise ValidationError("Agency name is missing")

        super(FundingAgency, cls).update(element_id, **kwargs)


class Subject(AbstractMetaDataElement):
    """Define Subject custom metadata element model."""

    term = 'Subject'
    value = models.CharField(max_length=100)

    class Meta:
        """Define meta properties for Subject model."""

        unique_together = ("value", "content_type", "object_id")

    def __unicode__(self):
        """Return value field for unicode representation."""
        return self.value

    @classmethod
    def create(cls, **kwargs):
        """Define custom create method for Subject model."""
        metadata_obj = kwargs['content_object']
        value = kwargs.get('value', None)
        if value is not None:
            if metadata_obj.subjects.filter(value__iexact=value).exists():
                raise ValidationError("Subject element already exists.")

        return super(Subject, cls).create(**kwargs)

    @classmethod
    def remove(cls, element_id):
        """Define custom remove method for Subject model."""
        sub = Subject.objects.get(id=element_id)

        if Subject.objects.filter(object_id=sub.object_id,
                                  content_type__pk=sub.content_type.id).count() == 1:
            raise ValidationError("The only subject element of the resource can't be deleted.")
        sub.delete()


class Source(AbstractMetaDataElement):
    """Define Source custom metadata element model."""

    term = 'Source'
    derived_from = models.CharField(max_length=300)

    class Meta:
        """Define meta properties for Source model."""

        unique_together = ("derived_from", "content_type", "object_id")

    def __unicode__(self):
        """Return derived_from field for unicode representation."""
        return self.derived_from


class Rights(AbstractMetaDataElement):
    """Define Rights custom metadata element model."""

    term = 'Rights'
    statement = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    def __unicode__(self):
        """Return either statement or statement + url for unicode representation."""
        value = ''
        if self.statement:
            value += self.statement + ' '
        if self.url:
            value += self.url

        return value

    class Meta:
        """Define meta properties for Rights model."""

        unique_together = ("content_type", "object_id")

    @classmethod
    def remove(cls, element_id):
        """Define custom remove method for Rights model."""
        raise ValidationError("Rights element of a resource can't be deleted.")


def short_id():
    """Generate a uuid4 hex to be used as a resource or element short_id."""
    return uuid4().hex


class ResourceManager(PageManager):
    """Extend mezzanine PageManager to manage Resource pages."""

    def __init__(self, resource_type=None, *args, **kwargs):
        """Extend mezzanine PageManager to manage Resource pages based on resource_type."""
        self.resource_type = resource_type
        super(ResourceManager, self).__init__(*args, **kwargs)

    def create(self, *args, **kwargs):
        """Create new mezzanine page based on resource_type."""
        if self.resource_type is None:
            kwargs.pop('resource_type', None)
        return super(ResourceManager, self).create(*args, **kwargs)

    def get_queryset(self):
        """Get mezzanine-like queryset based on resource_type."""
        qs = super(ResourceManager, self).get_queryset()
        if self.resource_type:
            qs = qs.filter(resource_type=self.resource_type)
        return qs


class AbstractResource(ResourcePermissionsMixin, ResourceIRODSMixin):
    """
    Create Abstract Class for all Resources.

    All hydroshare objects inherit from this mixin.  It defines things that must
    be present to be considered a hydroshare resource.  Additionally, all
    hydroshare resources should inherit from Page.  This gives them what they
    need to be represented in the Mezzanine CMS.

    In some cases, it is possible that the order of inheritence matters.  Best
    practice dictates that you list pages.Page first and then other classes:

        class MyResourceContentType(pages.Page, hs_core.AbstractResource):
            ...
    """

    content = models.TextField()  # the field added for use by Django inplace editing
    last_changed_by = models.ForeignKey(User,
                                        help_text='The person who last changed the resource',
                                        related_name='last_changed_%(app_label)s_%(class)s',
                                        null=True,
                                        )

    files = GenericRelation('hs_core.ResourceFile',
                            help_text='The files associated with this resource',
                            for_concrete_model=True)

    file_unpack_status = models.CharField(max_length=7,
                                          null=True, blank=True,
                                          choices=(('Pending', 'Pending'), ('Running', 'Running'),
                                                   ('Done', 'Done'), ('Error', 'Error'))
                                          )
    file_unpack_message = models.TextField(null=True, blank=True)

    # TODO: why are old versions saved?
    bags = GenericRelation('hs_core.Bags', help_text='The bagits created from versions of '
                                                     'this resource', for_concrete_model=True)
    short_id = models.CharField(max_length=32, default=short_id, db_index=True)
    doi = models.CharField(max_length=1024, null=True, blank=True, db_index=True,
                           help_text='Permanent identifier. Never changes once it\'s been set.')
    comments = CommentsField()
    rating = RatingField()

    # this is to establish a relationship between a resource and
    # any metadata container object (e.g., CoreMetaData object)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    extra_metadata = HStoreField(default={})

    # this field is for specific resource types to store extra key:value pairs
    # for internal use only
    # this field WILL NOT get recorded in bag and SHOULD NEVER be used for storing metadata
    extra_data = HStoreField(default={})

    # definition of resource logic
    @property
    def supports_folders(self):
        """Return whether folder operations are supported. Computed for polymorphic types."""
        return False

    @property
    def has_required_metadata(self):
        """Return True only if all required metadata is present."""
        if self.metadata is None or not self.metadata.has_all_required_elements():
            return False
        for f in self.logical_files:
            if not f.metadata.has_all_required_elements():
                return False
        return True

    @property
    def can_be_public_or_discoverable(self):
        """Return True if the resource can be set to public or discoverable.

        This is True if

        1. The resource has all metadata elements marked as required.
        2. The resource has all files that are considered required.

        and False otherwise
        """
        has_files = self.has_required_content_files()
        has_metadata = self.has_required_metadata
        return has_files and has_metadata

    def set_discoverable(self, value, user=None):
        """Set the discoverable flag for a resource.

        :param value: True or False
        :param user: user requesting the change, or None for changes that are not user requests.
        :raises ValidationError: if the current configuration cannot be set to desired state

        This sets the discoverable flag (self.raccess.discoverable) for a resource based
        upon application logic. It is part of AbstractResource because its result depends
        upon resource state, and not just access control.

        * This flag can only be set to True if the resource passes basic validations
          `has_required_metata` and `has_required_content_files`
        * setting `discoverable` to `False` also sets `public` to `False`
        * setting `discoverable` to `True` does not change `public`

        Thus, the setting public=True, discoverable=False is disallowed.

        If `user` is None, access control is not checked.  This happens when a resource has been
        invalidated outside of the control of a specific user. In this case, user can be None
        """
        # access control is separate from validation logic
        if user is not None and not user.uaccess.can_change_resource_flags(self):
            raise ValidationError("You don't have permission to change resource sharing status")

        # check that there is sufficient resource content
        has_metadata = self.has_required_metadata
        has_files = self.has_required_content_files()
        if value and not (has_metadata and has_files):

            if not has_metadata and not has_files:
                msg = "Resource does not have sufficient metadata and content files to be " + \
                    "discoverable"
                raise ValidationError(msg)
            elif not has_metadata:
                msg = "Resource does not have sufficient metadata to be discoverable"
                raise ValidationError(msg)
            elif not has_files:
                msg = "Resource does not have sufficient content files to be discoverable"
                raise ValidationError(msg)

        else:  # state change is allowed
            self.raccess.discoverable = value
            self.raccess.save()
            self.set_public(False)

    def set_public(self, value, user=None):
        """Set the public flag for a resource.

        :param value: True or False
        :param user: user requesting the change, or None for changes that are not user requests.
        :raises ValidationError: if the current configuration cannot be set to desired state

        This sets the public flag (self.raccess.public) for a resource based
        upon application logic. It is part of AbstractResource because its result depends
        upon resource state, and not just access control.

        * This flag can only be set to True if the resource passes basic validations
          `has_required_metata` and `has_required_content_files`
        * setting `public` to `True` also sets `discoverable` to `True`
        * setting `public` to `False` does not change `discoverable`
        * setting `public` to either also modifies the AVU isPublic for the resource.

        Thus, the setting public=True, discoverable=False is disallowed.

        If `user` is None, access control is not checked.  This happens when a resource has been
        invalidated outside of the control of a specific user. In this case, user can be None
        """
        # avoid import loop
        from hs_core.views.utils import run_script_to_update_hyrax_input_files

        # access control is separate from validation logic
        if user is not None and not user.uaccess.can_change_resource_flags(self):
            raise ValidationError("You don't have permission to change resource sharing status")

        old_value = self.raccess.public  # is this a change?

        # check that there is sufficient resource content
        has_metadata = self.has_required_metadata
        has_files = self.has_required_content_files()
        if value and not (has_metadata and has_files):

            if not has_metadata and not has_files:
                msg = "Resource does not have sufficient metadata and content files to be public"
                raise ValidationError(msg)

            elif not has_metadata:
                msg = "Resource does not have sufficient metadata to be public"
                raise ValidationError(msg)

            elif not has_files:
                msg = "Resource does not have sufficient content files to be public"
                raise ValidationError(msg)

        else:  # make valid state change
            self.raccess.public = value
            if value:  # can't be public without being discoverable
                self.raccess.discoverable = value
            self.raccess.save()

            # public changed state: set isPublic metadata AVU accordingly
            if value != old_value:
                self.setAVU("isPublic", self.raccess.public)

                # TODO: why does this only run when something becomes public?
                # TODO: Should it be run when a NetcdfResource becomes private?
                # Answer to TODO above: it is intentional not to run it when a target resource
                # becomes private for performance reasons. The nightly script run will clean up
                # to make sure all private resources are not available to hyrax server as well as
                # to make sure all resources files available to hyrax server are up to date with
                # the HydroShare iRODS data store.

                # run script to update hyrax input files when private netCDF resource becomes
                # public or private composite resource that includes netCDF files becomes public

                is_netcdf_to_public = False
                if self.resource_type == 'NetcdfResource':
                    is_netcdf_to_public = True
                elif self.resource_type == 'CompositeResource' and \
                        self.get_logical_files('NetCDFLogicalFile'):
                    is_netcdf_to_public = True

                if value and settings.RUN_HYRAX_UPDATE and is_netcdf_to_public:
                    run_script_to_update_hyrax_input_files(self.short_id)

    def set_require_download_agreement(self, user, value):
        """Set resource require_download_agreement flag to True or False.
        If require_download_agreement is True then user will be prompted to agree to resource
        rights statement before he/she can download resource files or bag.

        :param user: user requesting the change
        :param value: True or False
        :raises PermissionDenied: if the user lacks permission to change resource flag
        """
        if not user.uaccess.can_change_resource_flags(self):
            raise PermissionDenied("You don't have permission to change resource download agreement"
                                   " status")
        self.raccess.require_download_agreement = value
        self.raccess.save()

    def update_public_and_discoverable(self):
        """Update the settings of the public and discoverable flags for changes in metadata."""
        if self.raccess.discoverable and not self.can_be_public_or_discoverable:
            self.set_discoverable(False)  # also sets Public

    def get_url_of_path(self, path):
        """Return the URL of an arbtrary path in this resource.

        A GET of this URL simply returns the contents of the path.
        This URL is independent of federation.
        PUT, POST, and DELETE are not supported.
        path includes data/contents/

        This choice for a URL is dependent mainly upon conformance to DataOne URL standards
        that are also conformant to the format in resourcemap.xml. This url does not contain
        the site URL, which is prefixed when needed.

        This is based upon the resourcemap_urls.py entry:

            url(r'^resource/(?P<shortkey>[0-9a-f-]+)/data/contents/(?.+)/$',
                views.file_download_url_mapper,
                name='get_resource_file')

        """
        # must start with a / in order to concat with current_site_url.
        return '/' + os.path.join('resource', self.short_id, path)

    def get_public_path(self, path):
        """Return the public path for a specific path within the resource.
           This is the path that appears in public URLs.
           The input path includes data/contents/ as needed.
        """
        return os.path.join(self.short_id, path)

    def get_irods_path(self, path):
        """Return the irods path by which the given path is accessed.
           The input path includes data/contents/ as needed.
        """
        if self.is_federated:
            return os.path.join(self.resource_federation_path, self.get_public_path(path))
        else:
            return self.get_public_path(path)

    def set_quota_holder(self, setter, new_holder):
        """Set quota holder of the resource to new_holder who must be an owner.

        setter is the requesting user to transfer quota holder and setter must also be an owner
        """
        from hs_core.hydroshare.utils import validate_user_quota
        from hs_core.hydroshare.resource import update_quota_usage

        if __debug__:
            assert(isinstance(setter, User))
            assert(isinstance(new_holder, User))
        if not setter.uaccess.owns_resource(self) or \
                not new_holder.uaccess.owns_resource(self):
            raise PermissionDenied("Only owners can set or be set as quota holder for the resource")

        # QuotaException will be raised if new_holder does not have enough quota to hold this
        # new resource, in which case, set_quota_holder to the new user fails
        validate_user_quota(new_holder, self.size)
        attname = "quotaUserName"

        if setter.username != new_holder.username:
            # this condition check is needed to make sure attname exists as AVU before getting it
            oldqu = self.getAVU(attname)
            if oldqu:
                # have to remove the old AVU first before setting to the new one in order to trigger
                # quota micro-service PEP msiRemoveQuotaHolder so quota for old quota
                # holder will be reduced as a result of setting quota holder to a different user
                self.removeAVU(attname, oldqu)
        self.setAVU(attname, new_holder.username)
        update_quota_usage(res=self, user=setter)

    def get_quota_holder(self):
        """Get quota holder of the resource.

        return User instance of the quota holder for the resource or None if it does not exist
        """
        try:
            uname = self.getAVU("quotaUserName")
        except SessionException:
            # quotaUserName AVU does not exist, return None
            return None

        if uname:
            return User.objects.filter(username=uname).first()
        else:
            # quotaUserName AVU does not exist, return None
            return None

    def removeAVU(self, attribute, value):
        """Remove an AVU at the resource level.

        This avoids mistakes in setting AVUs by assuring that the appropriate root path
        is alway used.
        """
        istorage = self.get_irods_storage()
        root_path = self.root_path
        istorage.session.run("imeta", None, 'rm', '-C', root_path, attribute, value)

    def setAVU(self, attribute, value):
        """Set an AVU at the resource level.

        This avoids mistakes in setting AVUs by assuring that the appropriate root path
        is alway used.
        """
        if isinstance(value, bool):
            value = str(value).lower()  # normalize boolean values to strings
        istorage = self.get_irods_storage()
        root_path = self.root_path
        # has to create the resource collection directory if it does not exist already due to
        # the need for setting quota holder on the resource collection before adding files into
        # the resource collection in order for the real-time iRODS quota micro-services to work
        if not istorage.exists(root_path):
            istorage.session.run("imkdir", None, '-p', root_path)
        istorage.setAVU(root_path, attribute, value)

    def getAVU(self, attribute):
        """Get an AVU for a resource.

        This avoids mistakes in getting AVUs by assuring that the appropriate root path
        is alway used.
        """
        istorage = self.get_irods_storage()
        root_path = self.root_path
        value = istorage.getAVU(root_path, attribute)

        # Convert selected boolean attribute values to bool; non-existence implies False
        # "Private" is the appropriate response if "isPublic" is None
        if attribute == 'isPublic':
            if value is not None and value.lower() == 'true':
                return True
            else:
                return False

        # Convert selected boolean attribute values to bool; non-existence implies True
        # If bag_modified or metadata_dirty does not exist, then we do not know the
        # state of metadata files and/or bags. They may not exist. Thus we interpret
        # None as "true", which will generate the appropriate files if they do not exist.
        if attribute == 'bag_modified' or attribute == 'metadata_dirty':
            if value is None or value.lower() == 'true':
                return True
            else:
                return False

        # return strings for all other attributes
        else:
            return value

    @classmethod
    def scimeta_url(cls, resource_id):
        """ Get URL of the science metadata file resourcemetadata.xml """
        res = BaseResource.objects.get(short_id=resource_id)
        scimeta_path = res.scimeta_path
        scimeta_url = reverse('rest_download', kwargs={'path': scimeta_path})
        return scimeta_url

    # TODO: there are too many ways to get to the resourcemap.
    # 1. {id}/data/resourcemap.xml
    # 2. {id}/resmap
    # Choose one!
    @classmethod
    def resmap_url(cls, resource_id):
        """ Get URL of the resource map resourcemap.xml."""
        resmap_path = "{resource_id}/data/resourcemap.xml".format(resource_id=resource_id)
        resmap_url = reverse('rest_download', kwargs={'path': resmap_path})
        return resmap_url

    # TODO: this is inaccurate; resourcemap.xml != systemmetadata.xml
    @classmethod
    def sysmeta_path(cls, resource_id):
        """Get URL of resource map xml."""
        return "{resource_id}/data/resourcemap.xml".format(resource_id=resource_id)

    def delete(self, using=None):
        """Delete resource along with all of its metadata and data bag."""
        from hydroshare import hs_bagit
        for fl in self.files.all():
            if fl.logical_file is not None:
                # delete of metadata file deletes the logical file (one-to-one relation)
                # so no need for fl.logical_file.delete() and deleting of metadata file
                # object deletes (cascade delete) all the contained GenericRelated metadata
                # elements
                fl.logical_file.metadata.delete()
            # COUCH: delete of file objects now cascades.
            fl.delete()
        hs_bagit.delete_files_and_bag(self)
        # TODO: Pabitra - delete_all_elements() may not be needed in Django 1.8 and later
        self.metadata.delete_all_elements()
        self.metadata.delete()
        super(AbstractResource, self).delete()

    @property
    def metadata(self):
        """Return a pointer to the metadata object for this resource.

        This object can vary based upon resource type. Please override this function to
        return the appropriate object for each resource type.
        """
        md = CoreMetaData()  # only this line needs to be changed when you override
        return self._get_metadata(md)

    @property
    def first_creator(self):
        """Get first creator of resource from metadata."""
        first_creator = self.metadata.creators.filter(order=1).first()
        return first_creator

    def get_metadata_xml(self, pretty_print=True, include_format_elements=True):
        """Get metadata xml for Resource.

        Resource types that support file types
        must override this method. See Composite Resource
        type as an example
        """
        return self.metadata.get_xml(pretty_print=pretty_print,
                                     include_format_elements=include_format_elements)

    def _get_metadata(self, metatdata_obj):
        """Get resource metadata from content_object."""
        md_type = ContentType.objects.get_for_model(metatdata_obj)
        res_type = ContentType.objects.get_for_model(self)
        self.content_object = res_type.model_class().objects.get(id=self.id).content_object
        if self.content_object:
            return self.content_object
        else:
            metatdata_obj.save()
            self.content_type = md_type
            self.object_id = metatdata_obj.id
            self.save()
            return metatdata_obj

    def is_aggregation_xml_file(self, file_path):
        """Checks if the file path *file_path* is one of the aggregation related xml file paths

        :param  file_path: full file path starting with resource short_id
        :return True if file_path is one of the aggregation xml file paths else False

        This function is overridden for Composite Resource.
        """
        return False

    def extra_capabilites(self):
        """Return None. No-op method.

        This is not terribly well defined yet, but should return at least a JSON serializable
        object of URL endpoints where extra self-describing services exist and can be queried by
        the user in the form of { "name" : "endpoint" }
        """
        return None

    def parse_citation_name(self, name, first_author=False):
        """Return properly formatted citation name from metadata."""
        CREATOR_NAME_ERROR = "Failed to generate citation - invalid creator name."
        first_names = None
        if "," in name:
            name_parts = name.split(",")
            if len(name_parts) == 0:
                return CREATOR_NAME_ERROR
            elif len(name_parts) == 1:
                last_names = name_parts[0]
            elif len(name_parts) == 2:
                first_names = name_parts[1]
                first_names = first_names.split()
                last_names = name_parts[0]
            else:
                return CREATOR_NAME_ERROR
        else:
            name_parts = name.split()
            if len(name_parts) == 0:
                return CREATOR_NAME_ERROR
            elif len(name_parts) > 1:
                first_names = name_parts[:-1]
                last_names = name_parts[-1]
            else:
                last_names = name_parts[0]

        if first_names:
            initials_list = [i[0] for i in first_names]
            initials = u". ".join(initials_list) + "."
            if first_author:
                author_name = u"{last_name}, {initials}"
            else:
                author_name = u"{initials} {last_name}"
            author_name = author_name.format(last_name=last_names,
                                             initials=initials
                                             )
        else:
            author_name = u"{last_name}".format(last_name=last_names)

        return author_name + ", "

    def get_citation(self):
        """Get citation or citations from resource metadata."""
        citation_str_lst = []

        CITATION_ERROR = "Failed to generate citation."

        first_author = self.metadata.creators.all().filter(order=1)[0]
        if first_author.organization and not first_author.name:
            citation_str_lst.append(first_author.organization + ", ")
        else:
            citation_str_lst.append(self.parse_citation_name(first_author.name, first_author=True))

        other_authors = self.metadata.creators.all().filter(order__gt=1)
        for author in other_authors:
            if author.organization and not author.name:
                citation_str_lst.append(author.organization + ", ")
            elif author.name and len(author.name.strip()) != 0:
                citation_str_lst.append(self.parse_citation_name(author.name))

        # remove the last added comma and the space
        if len(citation_str_lst[-1]) > 2:
            citation_str_lst[-1] = citation_str_lst[-1][:-2]
        else:
            return CITATION_ERROR

        if self.metadata.dates.all().filter(type='published'):
            citation_date = self.metadata.dates.all().filter(type='published')[0]
        elif self.metadata.dates.all().filter(type='modified'):
            citation_date = self.metadata.dates.all().filter(type='modified')[0]
        else:
            return CITATION_ERROR

        citation_str_lst.append(" ({year}). ".format(year=citation_date.start_date.year))
        citation_str_lst.append(self.metadata.title.value)

        isPendingActivation = False
        if self.metadata.identifiers.all().filter(name="doi"):
            hs_identifier = self.metadata.identifiers.all().filter(name="doi")[0]
            if self.doi.find('pending') >= 0 or self.doi.find('failure') >= 0:
                isPendingActivation = True
        elif self.metadata.identifiers.all().filter(name="hydroShareIdentifier"):
            hs_identifier = self.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
        else:
            return CITATION_ERROR

        ref_rel = self.metadata.relations.all().filter(type='isHostedBy').first()
        repl_rel = self.metadata.relations.all().filter(type='isCopiedFrom').first()
        date_str = "%s/%s/%s" % (citation_date.start_date.month, citation_date.start_date.day,
                                 citation_date.start_date.year)
        if ref_rel:
            citation_str_lst.append(u", {ref_rel_value}, last accessed {creation_date}.".format(
                ref_rel_value=ref_rel.value,
                creation_date=date_str))
        elif repl_rel:
            citation_str_lst.append(u", {repl_rel_value}, accessed {creation_date}, replicated in "
                                    u"HydroShare at: {url}".format(repl_rel_value=repl_rel.value,
                                                                   creation_date=date_str,
                                                                   url=hs_identifier.url))
        else:
            citation_str_lst.append(", HydroShare, {url}".format(url=hs_identifier.url))

        if isPendingActivation:
            citation_str_lst.append(", DOI for this published resource is pending activation.")

        return ''.join(citation_str_lst)

    @classmethod
    def get_supported_upload_file_types(cls):
        """Get a list of permissible upload types.

        Subclasses override this function to allow only specific file types.
        Any version should return a tuple of those file extensions
        (ex: return (".csv", ".txt",))

        To disallow all file upload, return an empty tuple ( return ())

        By default all file types are supported

        This is called before creating a specific instance; hence it is a class method.
        """
        return (".*",)

    @classmethod
    def allow_multiple_file_upload(cls):
        """
        Return whether multiple files can be uploaded.

        Subclasses of BaseResource override this function to tailor file upload.
        To allow multiple files to be uploaded return True, otherwise return False

        Resource by default allows multiple file upload.
        """
        return True

    @classmethod
    def can_have_multiple_files(cls):
        """Return whether this kind of resource can contain multiple files.

        Subclasses of BaseResource override this function to tailor file upload.

        To allow resource to have only 1 file or no file, return False

        A resource by default can contain multiple files
        """
        return True

    def has_required_content_files(self):
        """Check whether a resource has the required content files.

        Any subclass of this class may need to override this function
        to apply specific requirements as it relates to resource content files
        """
        if len(self.get_supported_upload_file_types()) > 0:
            if self.files.all().count() > 0:
                return True
            else:
                return False
        else:
            return True

    @property
    def logical_files(self):
        """Get list of logical files for resource."""
        logical_files_list = []
        for res_file in self.files.all():
            if res_file.logical_file is not None:
                if res_file.logical_file not in logical_files_list:
                    logical_files_list.append(res_file.logical_file)
        return logical_files_list

    @property
    def non_logical_files(self):
        """Get list of non-logical files for resource."""
        non_logical_files_list = []
        for res_file in self.files.all():
            if res_file.logical_file is None:
                if res_file.logical_file not in non_logical_files_list:
                    non_logical_files_list.append(res_file)
        return non_logical_files_list

    @property
    def generic_logical_files(self):
        """Get list of generic logical files for resource."""
        generic_logical_files_list = []
        for res_file in self.files.all():
            if res_file.has_generic_logical_file:
                if res_file.logical_file not in generic_logical_files_list:
                    generic_logical_files_list.append(res_file.logical_file)
        return generic_logical_files_list

    def get_logical_files(self, logical_file_class_name):
        """Get a list of logical files (aggregations) for a specified logical file class name."""

        logical_files_list = [lf for lf in self.logical_files if
                              lf.type_name() == logical_file_class_name]

        return logical_files_list

    @property
    def has_logical_spatial_coverage(self):
        """Checks if any of the logical files has spatial coverage"""

        return any(lf.metadata.spatial_coverage is not None for lf in self.logical_files)

    @property
    def has_logical_temporal_coverage(self):
        """Checks if any of the logical files has temporal coverage"""

        return any(lf.metadata.temporal_coverage is not None for lf in self.logical_files)

    @property
    def supports_logical_file(self):
        """Check if resource allows associating resource file objects with logical file."""
        return False

    def set_default_logical_file(self):
        """Do nothing (noop).

        Sets an instance of default logical file type to any resource file objects of
        this instance of the resource that is not already associated with a logical file.
        Each specific resource type needs to override this function in order to to support logical
        file types
        """
        pass

    def supports_folder_creation(self, folder_full_path):
        """Check if resource supports creation of folder at the specified path."""
        return True

    def supports_rename_path(self, src_full_path, tgt_full_path):
        """Check if file/folder rename/move is allowed by this resource."""
        return True

    def supports_zip(self, folder_to_zip):
        """Check if resource supports the specified folder to be zipped."""
        return True

    def supports_unzip(self, file_to_unzip):
        """Check if resource supports the unzipping of the specified file."""
        return True

    def supports_delete_folder_on_zip(self, original_folder):
        """Check if resource allows the original folder to be deleted upon zip."""
        return True

    @property
    def storage_type(self):
        if not self.is_federated:
            return 'local'
        userpath = '/' + os.path.join(
            getattr(settings, 'HS_USER_IRODS_ZONE', 'hydroshareuserZone'),
            'home',
            getattr(settings, 'HS_LOCAL_PROXY_USER_IN_FED_ZONE', 'localHydroProxy'))
        if self.resource_federation_path == userpath:
            return 'user'
        else:
            return 'federated'

    def is_folder(self, folder_path):
        """Determine whether a given path (relative to resource root, including /data/contents/)
           is a folder or not. Returns False if the path does not exist.
        """
        path_split = folder_path.split('/')
        while path_split[-1] == '':
            path_split.pop()
        dir_path = u'/'.join(path_split[0:-1])

        # handles federation
        irods_path = os.path.join(self.root_path, dir_path)
        istorage = self.get_irods_storage()
        try:
            listing = istorage.listdir(irods_path)
        except SessionException:
            return False
        if path_split[-1] in listing[0]:  # folders
            return True
        else:
            return False

    class Meta:
        """Define meta properties for AbstractResource class."""

        abstract = True
        unique_together = ("content_type", "object_id")

    def check_relations(self, stop_on_error=False, log_errors=True,
                        echo_errors=False, return_errors=False):
        """Check for dangling relations due to deleted resource files.

        :param stop_on_error: whether to raise a ValidationError exception on first error
        :param log_errors: whether to log errors to Django log
        :param echo_errors: whether to print errors on stdout
        :param return_errors: whether to collect errors in an array and return them.
        """
        from hs_core.hydroshare.utils import get_resource_by_shortkey
        for r in self.metadata.relations.all():
            if r.value.startswith('http://www.hydroshare.org/resource/'):
                target = r.value[len('http://www.hydroshare.org/resource/'):].rstrip('/')
                try:
                    get_resource_by_shortkey(target, or_404=False)
                except BaseResource.DoesNotExist:
                    print("relation {} {} {} (this does not exist)"
                          .format(self.short_id, r.type, target))

    def fix_irods_user_paths(self, log_actions=True, echo_actions=False, return_actions=False):
        """Move iRODS user paths to the locations specified in settings.

        :param log_actions: whether to log actions to Django log
        :param echo_actions: whether to print actions on stdout
        :param return_actions: whether to collect actions in an array and return them.

        This is a temporary fix to the user resources, which are currently stored like
        federated resources but whose paths are dynamically determined. This function points
        the paths for user-level resources to where they are stored in the current environment,
        as specified in hydroshare/local_settings.py.

        * This only does something if the environment is not a production environment.
        * It is idempotent, in the sense that it can be repeated more than once without problems.
        * It must be done once whenever the django database is reloaded.
        * It does not check whether the paths exist afterward. This is done by check_irods_files.
        """
        logger = logging.getLogger(__name__)
        actions = []
        ecount = 0

        # location of the user files in production
        defaultpath = getattr(settings, 'HS_USER_ZONE_PRODUCTION_PATH',
                              '/hydroshareuserZone/home/localHydroProxy')
        # where resource should be found; this is equal to the default path in production
        userpath = '/' + os.path.join(
            getattr(settings, 'HS_USER_IRODS_ZONE', 'hydroshareuserZone'),
            'home',
            getattr(settings, 'HS_LOCAL_PROXY_USER_IN_FED_ZONE', 'localHydroProxy'))

        msg = "fix_irods_user_paths: user path is {}".format(userpath)
        if echo_actions:
            print(msg)
        if log_actions:
            logger.info(msg)
        if return_actions:
            actions.append(msg)

        # only take action if you find a path that is a default user path and not in production
        if self.resource_federation_path == defaultpath and userpath != defaultpath:
            msg = "fix_irods_user_paths: mapping existing user federation path {} to {}"\
                  .format(self.resource_federation_path, userpath)
            if echo_actions:
                print(msg)
            if log_actions:
                logger.info(msg)
            if return_actions:
                actions.append(msg)

            self.resource_federation_path = userpath
            self.save()
            for f in self.files.all():
                path = f.storage_path
                if path.startswith(defaultpath):
                    newpath = userpath + path[len(defaultpath):]
                    f.set_storage_path(newpath, test_exists=False)  # does implicit save
                    ecount += 1
                    msg = "fix_irods_user_paths: rewriting {} to {}".format(path, newpath)
                    if echo_actions:
                        print(msg)
                    if log_actions:
                        logger.info(msg)
                    if return_actions:
                        actions.append(msg)
                else:
                    msg = ("fix_irods_user_paths: ERROR: malformed path {} in resource" +
                           " {} should start with {}; cannot convert")\
                        .format(path, self.short_id, defaultpath)
                    if echo_actions:
                        print(msg)
                    if log_actions:
                        logger.error(msg)
                    if return_actions:
                        actions.append(msg)

        if ecount > 0:  # print information about the affected resource (not really an error)
            msg = "fix_irods_user_paths: affected resource {} type is {}, title is '{}'"\
                .format(self.short_id, self.resource_type, self.metadata.title.value)
            if log_actions:
                logger.info(msg)
            if echo_actions:
                print(msg)
            if return_actions:
                actions.append(msg)

        return actions, ecount  # empty unless return_actions=True

    def check_irods_files(self, stop_on_error=False, log_errors=True,
                          echo_errors=False, return_errors=False,
                          sync_ispublic=False, clean_irods=False, clean_django=False):
        """Check whether files in self.files and on iRODS agree.

        :param stop_on_error: whether to raise a ValidationError exception on first error
        :param log_errors: whether to log errors to Django log
        :param echo_errors: whether to print errors on stdout
        :param return_errors: whether to collect errors in an array and return them.
        :param sync_ispublic: whether to repair deviations between ResourceAccess.public
               and AVU isPublic
        :param clean_irods: whether to delete files in iRODs that are not in Django
        :param clean_django: whether to delete files in Django that are not in iRODs
        """
        from hs_core.hydroshare.resource import delete_resource_file

        logger = logging.getLogger(__name__)
        istorage = self.get_irods_storage()
        errors = []
        ecount = 0
        defaultpath = getattr(settings, 'HS_USER_ZONE_PRODUCTION_PATH',
                              '/hydroshareuserZone/home/localHydroProxy')

        # skip federated resources if not configured to handle these
        if self.is_federated and not settings.REMOTE_USE_IRODS:
            msg = "check_irods_files: skipping check of federated resource {} in unfederated mode"\
                .format(self.short_id)
            if echo_errors:
                print(msg)
            if log_errors:
                logger.info(msg)

        # skip resources that do not exist in iRODS
        elif not istorage.exists(self.root_path):
                msg = "root path {} does not exist in iRODS".format(self.root_path)
                ecount += 1
                if echo_errors:
                    print(msg)
                if log_errors:
                    logger.error(msg)
                if return_errors:
                    errors.append(msg)

        else:
            # Step 1: repair irods user file paths if necessary
            if clean_irods or clean_django:
                # fix user paths before check (required). This is an idempotent step.
                if self.resource_federation_path == defaultpath:
                    error2, ecount2 = self.fix_irods_user_paths(log_actions=log_errors,
                                                                echo_actions=echo_errors,
                                                                return_actions=False)
                    errors.extend(error2)
                    ecount += ecount2

            # Step 2: does every file here refer to an existing file in iRODS?
            for f in self.files.all():
                if not istorage.exists(f.storage_path):
                    ecount += 1
                    msg = "check_irods_files: django file {} does not exist in iRODS"\
                        .format(f.storage_path)
                    if clean_django:
                        delete_resource_file(self.short_id, f.short_path, self.creator,
                                             delete_logical_file=False)
                        msg += " (DELETED FROM DJANGO)"
                    if echo_errors:
                        print(msg)
                    if log_errors:
                        logger.error(msg)
                    if return_errors:
                        errors.append(msg)
                    if stop_on_error:
                        raise ValidationError(msg)

            # Step 3: does every iRODS file correspond to a record in files?
            error2, ecount2 = self.__check_irods_directory(self.file_path, logger,
                                                           stop_on_error=stop_on_error,
                                                           log_errors=log_errors,
                                                           echo_errors=echo_errors,
                                                           return_errors=return_errors,
                                                           clean=clean_irods)
            errors.extend(error2)
            ecount += ecount2

            # Step 4: check whether the iRODS public flag agrees with Django
            django_public = self.raccess.public
            irods_public = None
            try:
                irods_public = self.getAVU('isPublic')
            except SessionException as ex:
                msg = "cannot read isPublic attribute of {}: {}"\
                    .format(self.short_id, ex.stderr)
                ecount += 1
                if log_errors:
                    logger.error(msg)
                if echo_errors:
                    print(msg)
                if return_errors:
                    errors.append(msg)
                if stop_on_error:
                    raise ValidationError(msg)

            if irods_public is not None:
                # convert to boolean
                irods_public = str(irods_public).lower() == 'true'

            if irods_public is None or irods_public != django_public:
                ecount += 1
                if not django_public:  # and irods_public
                    msg = "check_irods_files: resource {} public in irods, private in Django"\
                        .format(self.short_id)
                    if sync_ispublic:
                        try:
                            self.setAVU('isPublic', 'false')
                            msg += " (REPAIRED IN IRODS)"
                        except SessionException as ex:
                            msg += ": (CANNOT REPAIR: {})"\
                                .format(ex.stderr)

                else:  # django_public and not irods_public
                    msg = "check_irods_files: resource {} private in irods, public in Django"\
                        .format(self.short_id)
                    if sync_ispublic:
                        try:
                            self.setAVU('isPublic', 'true')
                            msg += " (REPAIRED IN IRODS)"
                        except SessionException as ex:
                            msg += ": (CANNOT REPAIR: {})"\
                                .format(ex.stderr)

                if msg != '':
                    if echo_errors:
                        print(msg)
                    if log_errors:
                        logger.error(msg)
                    if return_errors:
                        errors.append(msg)
                    if stop_on_error:
                        raise ValidationError(msg)

        if ecount > 0:  # print information about the affected resource (not really an error)
            msg = "check_irods_files: affected resource {} type is {}, title is '{}'"\
                .format(self.short_id, self.resource_type, self.metadata.title.value)
            if log_errors:
                logger.error(msg)
            if echo_errors:
                print(msg)
            if return_errors:
                errors.append(msg)

        return errors, ecount  # empty unless return_errors=True

    def __check_irods_directory(self, dir, logger,
                                stop_on_error=False, log_errors=True,
                                echo_errors=False, return_errors=False,
                                clean=False):
        """List a directory and check files there for conformance with django ResourceFiles.

        :param stop_on_error: whether to raise a ValidationError exception on first error
        :param log_errors: whether to log errors to Django log
        :param echo_errors: whether to print errors on stdout
        :param return_errors: whether to collect errors in an array and return them.

        """
        errors = []
        ecount = 0
        istorage = self.get_irods_storage()
        try:
            listing = istorage.listdir(dir)
            for fname in listing[1]:  # files
                fullpath = os.path.join(dir, fname)
                found = False
                for f in self.files.all():
                    if f.storage_path == fullpath:
                        found = True
                        break
                if not found and not self.is_aggregation_xml_file(fullpath):
                    ecount += 1
                    msg = "check_irods_files: file {} in iRODs does not exist in Django"\
                        .format(fullpath)
                    if clean:
                        try:
                            istorage.delete(fullpath)
                            msg += " (DELETED FROM IRODS)"
                        except SessionException as ex:
                            msg += ": (CANNOT DELETE: {})"\
                                .format(ex.stderr)
                    if echo_errors:
                        print(msg)
                    if log_errors:
                        logger.error(msg)
                    if return_errors:
                        errors.append(msg)
                    if stop_on_error:
                        raise ValidationError(msg)

            for dname in listing[0]:  # directories
                error2, ecount2 = self.__check_irods_directory(os.path.join(dir, dname), logger,
                                                               stop_on_error=stop_on_error,
                                                               echo_errors=echo_errors,
                                                               log_errors=log_errors,
                                                               return_errors=return_errors,
                                                               clean=clean)
                errors.extend(error2)
                ecount += ecount2

        except SessionException:
            pass  # not an error not to have a file directory.
            # Non-existence of files is checked elsewhere.

        return errors, ecount  # empty unless return_errors=True


def get_path(instance, filename, folder=None):
    """Get a path from a ResourceFile, filename, and folder.

    :param instance: instance of ResourceFile to use
    :param filename: file name to use (without folder)
    :param folder: can override folder for ResourceFile instance

    The filename is only a single name. This routine converts it to an absolute
    path that can be federated or local.  The instance points to the Resource record,
    which contains the federation path. The folder in the instance will be used unless
    overridden.

    Note: this does not change the default behavior.
    Thus it can be used to compute a new path for file that
    one wishes to move.
    """
    if not folder:
        folder = instance.file_folder
    return get_resource_file_path(instance.resource, filename, folder)


# TODO: make this an instance method of BaseResource.
def get_resource_file_path(resource, filename, folder=None):
    """Determine storage path for a FileField based upon whether resource is federated.

    :param resource: resource containing the file.
    :param filename: name of file without folder.
    :param folder: folder of file

    The filename is only a single name. This routine converts it to an absolute
    path that can be federated or local. The resource contains information on how
    to do this.

    """
    # folder can be absolute pathname; strip qualifications off of folder if necessary
    if folder is not None and folder.startswith(resource.root_path):
        # TODO: does this now start with /?
        folder = folder[len(resource.root_path):]
    if folder == '':
        folder = None

    # retrieve federation path -- if any -- from Resource object containing the file
    if filename.startswith(resource.file_path):
        return filename

    # otherwise, it is an unqualified name.
    if folder is not None:
        # use subfolder
        return os.path.join(resource.file_path, folder, filename)
    else:
        # use root folder
        return os.path.join(resource.file_path, filename)


def path_is_allowed(path):
    """Check for suspicious paths containing '/../'."""
    if path == "":
        raise ValidationError("Empty file paths are not allowed")
    if '/../' in path:
        raise SuspiciousFileOperation("File paths cannot contain '/../'")
    if '/./' in path:
        raise SuspiciousFileOperation("File paths cannot contain '/./'")


class FedStorage(IrodsStorage):
    """Define wrapper class to fix Django storage object limitations for iRODS.

    The constructor of a Django storage object must have no arguments.
    This simple workaround accomplishes that.
    """

    def __init__(self):
        """Initialize method with no arguments for federated storage."""
        super(FedStorage, self).__init__("federated")


# TODO: revise path logic for rename_resource_file_in_django for proper path.
# TODO: utilize antibugging to check that paths are coherent after each operation.
class ResourceFile(ResourceFileIRODSMixin):
    """
    Represent a file in a resource.
    """
    class Meta:
        index_together = [['object_id', 'resource_file'],
                          ['object_id', 'fed_resource_file'],
                          ]
    # A ResourceFile is a sub-object of a resource, which can have several types.
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)
    content_object = GenericForeignKey('content_type', 'object_id')

    # This is used to direct uploads to a subfolder of the root folder for the resource.
    # See get_path and get_resource_file_path above.
    file_folder = models.CharField(max_length=4096, null=True)

    # This pair of FileFields deals with the fact that there are two kinds of storage
    resource_file = models.FileField(upload_to=get_path, max_length=4096,
                                     null=True, blank=True, storage=IrodsStorage())
    fed_resource_file = models.FileField(upload_to=get_path, max_length=4096,
                                         null=True, blank=True, storage=FedStorage())

    # DEPRECATED: utilize resfile.set_storage_path(path) and resfile.storage_path.
    # fed_resource_file_name_or_path = models.CharField(max_length=255, null=True, blank=True)
    # DEPRECATED: use native size routine
    # fed_resource_file_size = models.CharField(max_length=15, null=True, blank=True)

    # we are using GenericForeignKey to allow resource file to be associated with any
    # HydroShare defined LogicalFile types (e.g., GeoRasterFile, NetCdfFile etc)
    logical_file_object_id = models.PositiveIntegerField(null=True, blank=True)
    logical_file_content_type = models.ForeignKey(ContentType,
                                                  null=True, blank=True,
                                                  related_name="files")
    logical_file_content_object = GenericForeignKey('logical_file_content_type',
                                                    'logical_file_object_id')

    def __str__(self):
        """Return resource filename or federated resource filename for string representation."""
        if self.resource.resource_federation_path:
            return self.fed_resource_file.name
        else:
            return self.resource_file.name

    @classmethod
    def create(cls, resource, file, folder=None, source=None, move=False):
        """Create custom create method for ResourceFile model.

        Create takes arguments that are invariant of storage medium.
        These are turned into a path that is suitable for the medium.
        Federation must be initialized first at the resource level.

        :param resource: resource that contains the file.
        :param file: a File or a iRODS path to an existing file already copied.
        :param folder: the folder in which to store the file.
        :param source: an iRODS path in the same zone from which to copy the file.
        :param move: if True, move the file rather than copying.

        There are two main usages to this constructor:

        * uploading a file from a form or REST call:

                ResourceFile.create(r, File(...something...), folder=d)

        * copying a file internally from iRODS:

                ResourceFile.create(r, file_name, folder=d, source=s, move=True)
          or
                ResourceFile.create(r, file_name, folder=d, source=s, move=False)

        In this case, source is a full iRODS pathname of the place from which to copy or move
        the file. The default is to copy the file and leave a copy in place.

        A third form is less common and presumes that the file already exists in iRODS
        in the proper place:

        * pointing to an existing file:

                ResourceFile.create(r, file_name, folder=d)

        """
        # bind to appropriate resource
        kwargs = {}
        if __debug__:
            assert isinstance(resource, BaseResource)
        kwargs['content_object'] = resource

        kwargs['file_folder'] = folder

        # if file is an open file, use native copy by setting appropriate variables
        if isinstance(file, File):
            if resource.is_federated:
                kwargs['resource_file'] = None
                kwargs['fed_resource_file'] = file
            else:
                kwargs['resource_file'] = file
                kwargs['fed_resource_file'] = None

        else:  # if file is not an open file, then it's a basename (string)
            if file is None and source is not None:
                if __debug__:
                    assert(isinstance(source, basestring))
                # source is a path to an iRODS file to be copied here.
                root, newfile = os.path.split(source)  # take file from source path
                # newfile is where it should be copied to.
                target = get_resource_file_path(resource, newfile, folder=folder)
                istorage = resource.get_irods_storage()
                if not istorage.exists(source):
                    raise ValidationError("ResourceFile.create: source {} of copy not found"
                                          .format(source))
                if not move:
                    istorage.copyFiles(source, target)
                else:
                    istorage.moveFile(source, target)
                if not istorage.exists(target):
                    raise ValidationError("ResourceFile.create: copy to target {} failed"
                                          .format(target))
                if move and istorage.exists(source):
                    raise ValidationError("ResourceFile.create: move did not work")
            elif file is not None and source is None:
                # file points to an existing iRODS file
                # no need to verify whether the file exists in iRODS since the file
                # name is returned from iRODS ils list dir command which already
                # confirmed the file exists already in iRODS
                target = get_resource_file_path(resource, file, folder=folder)
            else:
                raise ValidationError(
                    "ResourceFile.create: exactly one of source or file must be specified")

            # we've copied or moved if necessary; now set the paths
            if resource.is_federated:
                kwargs['resource_file'] = None
                kwargs['fed_resource_file'] = target
            else:
                kwargs['resource_file'] = target
                kwargs['fed_resource_file'] = None

        # Actually create the file record
        # when file is a File, the file is copied to storage in this step
        # otherwise, the copy must precede this step.
        return ResourceFile.objects.create(**kwargs)

    # TODO: automagically handle orphaned logical files
    def delete(self):
        """Delete a resource file record and the file contents.

        model.delete does not cascade to delete files themselves,
        and these must be explicitly deleted.

        """
        if self.exists:
            if self.fed_resource_file:
                self.fed_resource_file.delete()
            if self.resource_file:
                self.resource_file.delete()
        super(ResourceFile, self).delete()

    @property
    def resource(self):
        """Return content_object representing the resource from a resource file."""
        return self.content_object

    # TODO: write unit test
    @property
    def size(self):
        """Return file size for federated or non-federated files."""
        if self.resource.resource_federation_path:
            if __debug__:
                assert self.resource_file.name is None or \
                    self.resource_file.name == ''
            try:
                return self.fed_resource_file.size
            except SessionException:
                logger = logging.getLogger(__name__)
                logger.warn("file {} not found".format(self.storage_path))
                return 0
        else:
            if __debug__:
                assert self.fed_resource_file.name is None or \
                    self.fed_resource_file.name == ''
            try:
                return self.resource_file.size
            except SessionException:
                logger = logging.getLogger(__name__)
                logger.warn("file {} not found".format(self.storage_path))
                return 0

    # TODO: write unit test
    @property
    def exists(self):
        """Check existence of files for both federated and non-federated."""
        istorage = self.resource.get_irods_storage()
        if self.resource.is_federated:
            if __debug__:
                assert self.resource_file.name is None or \
                    self.resource_file.name == ''
            return istorage.exists(self.fed_resource_file.name)
        else:
            if __debug__:
                assert self.fed_resource_file.name is None or \
                    self.fed_resource_file.name == ''
            return istorage.exists(self.resource_file.name)

    # TODO: write unit test
    @property
    def read(self):
        if self.resource.is_federated:
            return self.fed_resource_file.read
        else:
            return self.resource_file.read

    @property
    def storage_path(self):
        """Return the qualified name for a file in the storage hierarchy.

        This is a valid input to IrodsStorage for manipulating the file.
        The output depends upon whether the IrodsStorage instance is running
        in federated mode.

        """
        # instance.content_object can be stale after changes.
        # Re-fetch based upon key; bypass type system; it is not relevant
        resource = self.resource
        if resource.is_federated:  # false if None or empty
            if __debug__:
                assert self.resource_file.name is None or \
                    self.resource_file.name == ''
            return self.fed_resource_file.name
        else:
            if __debug__:
                assert self.fed_resource_file.name is None or \
                    self.fed_resource_file.name == ''
            return self.resource_file.name

    # ResourceFile API handles file operations
    def set_storage_path(self, path, test_exists=True):
        """Bind this ResourceFile instance to an existing file.

        :param path: the path of the object.
        :param test_exists: if True, test for path existence in iRODS

        Path can be absolute or relative.

            * absolute paths contain full irods path to local or federated object.
            * relative paths start with anything else and can start with optional folder

        :raises ValidationError: if the pathname is inconsistent with resource configuration.
        It is rather important that applications call this rather than simply calling
        resource_file = "text path" because it takes the trouble of making that path
        fully qualified so that IrodsStorage will work properly.

        This records file_folder for future possible uploads and searches.

        The heavy lifting in this routine is accomplished via path_is_acceptable and get_path,
        which together normalize the file name.  Regardless of whether the internal file name
        is qualified or not, this makes it fully qualified from the point of view of the
        IrodsStorage module.

        """
        folder, base = self.path_is_acceptable(path, test_exists=test_exists)
        self.file_folder = folder
        self.save()

        # self.content_object can be stale after changes. Re-fetch based upon key
        # bypass type system; it is not relevant
        resource = self.resource

        # switch FileFields based upon federation path
        if resource.is_federated:
            # uses file_folder; must come after that setting.
            self.fed_resource_file = get_path(self, base)
            self.resource_file = None
        else:
            self.fed_resource_file = None
            self.resource_file = get_path(self, base)
        self.save()

    @property
    def short_path(self):
        """Return the unqualified path to the file object.

        * This path is invariant of where the object is stored.

        * Thus, it does not change if the resource is moved.

        This is the path that should be used as a key to index things such as file type.
        """
        if self.resource.is_federated:
            folder, base = self.path_is_acceptable(self.fed_resource_file.name, test_exists=False)
        else:
            folder, base = self.path_is_acceptable(self.resource_file.name, test_exists=False)
        if folder is not None:
            return os.path.join(folder, base)
        else:
            return base

    def set_short_path(self, path):
        """Set a path to a given path, relative to resource root.

        There is some question as to whether the short path should be stored explicitly or
        derived as in short_path above. The latter is computationally expensive but results
        in a single point of truth.
        """
        folder, base = os.path.split(path)
        if folder == "":
            folder = None
        self.file_folder = folder  # must precede call to get_path
        if self.resource.is_federated:
            self.resource_file = None
            self.fed_resource_file = get_path(self, base)
        else:
            self.resource_file = get_path(self, base)
            self.fed_resource_file = None
        self.save()

    def parse(self):
        """Parse a path into folder and basename."""
        return self.path_is_acceptable(self.storage_path, test_exists=False)

    def path_is_acceptable(self, path, test_exists=True):
        """Determine whether a path is acceptable for this resource file.

        Called inside ResourceFile objects to check paths

        :param path: path to test
        :param test_exists: if True, test for path existence in iRODS

        """
        return ResourceFile.resource_path_is_acceptable(self.resource, path, test_exists)

    @classmethod
    def resource_path_is_acceptable(cls, resource, path, test_exists=True):
        """Determine whether a path is acceptable for this resource file.

        Called outside ResourceFile objects or before such an object exists

        :param path: path to test
        :param test_exists: if True, test for path existence in iRODS

        This has the side effect of returning the short path for the resource
        as a folder/filename pair.
        """
        if test_exists:
            storage = resource.get_irods_storage()
        locpath = os.path.join(resource.short_id, "data", "contents") + "/"
        relpath = path
        fedpath = resource.resource_federation_path
        if fedpath and relpath.startswith(fedpath + '/'):
            if test_exists and not storage.exists(path):
                raise ValidationError("Federated path does not exist in irods")
            plen = len(fedpath + '/')
            relpath = relpath[plen:]  # omit fed path

            # strip resource id from path
            if relpath.startswith(locpath):
                plen = len(locpath)
                relpath = relpath[plen:]  # omit local path
            else:
                raise ValidationError("Malformed federated resource path")
        elif path.startswith(locpath):
            # strip optional local path prefix
            if test_exists and not storage.exists(path):
                raise ValidationError("Local path does not exist in irods")
            plen = len(locpath)
            relpath = relpath[plen:]  # strip local prefix, omit /

        # now we have folder/file. We could have gotten this from the input, or
        # from stripping qualification folders. Note that this can contain
        # misnamed header content misinterpreted as a folder unless one tests
        # for existence
        if '/' in relpath:
            folder, base = os.path.split(relpath)
            abspath = get_resource_file_path(resource, base, folder=folder)
            if test_exists and not storage.exists(abspath):
                raise ValidationError("Local path does not exist in irods")
        else:
            folder = None
            base = relpath
            abspath = get_resource_file_path(resource, base, folder=folder)
            if test_exists and not storage.exists(abspath):
                raise ValidationError("Local path does not exist in irods")

        return folder, base

    # def rename(self, new_name):
    #     """ rename a file, setting all path variables appropriately """
    #     pass

    # def copy_irods(self, source_path, dest_path=None):
    #     """ copy an irods file into this FileField, setting all paths appropriately """
    #     pass

    # def move_irods(self, source_path, dest_path=None):
    #     """ move an irods file into this object, setting all paths appropriately """

    # classmethods do things that query or affect all files.

    @classmethod
    def get(cls, resource, file, folder=None):
        """Get a ResourceFile record via its short path."""
        if resource.resource_federation_path:
            return ResourceFile.objects.get(object_id=resource.id,
                                            fed_resource_file=get_resource_file_path(resource,
                                                                                     file,
                                                                                     folder))
        else:
            return ResourceFile.objects.get(object_id=resource.id,
                                            resource_file=get_resource_file_path(resource,
                                                                                 file,
                                                                                 folder))

    # TODO: move to BaseResource as instance method
    @classmethod
    def list_folder(cls, resource, folder, sub_folders=True):
        """List files (instances of ResourceFile) in a given folder.

        :param resource: resource for which to list the folder
        :param folder: folder listed as either short_path or fully qualified path
        :param sub_folders: if true files from sub folders of *folder* will be included in the list
        """
        file_folder_to_match = folder
        if folder is None:
            folder = resource.file_path
        elif not folder.startswith(resource.file_path):
            folder = os.path.join(resource.file_path, folder)
        else:
            file_folder_to_match = folder[len(resource.file_path) + 1:]

        if sub_folders:
            if resource.is_federated:
                return ResourceFile.objects.filter(
                    object_id=resource.id,
                    fed_resource_file__startswith=folder)
            else:
                return ResourceFile.objects.filter(
                    object_id=resource.id,
                    resource_file__startswith=folder)
        else:
            return ResourceFile.objects.filter(
                object_id=resource.id,
                file_folder=file_folder_to_match)

    # TODO: move to BaseResource as instance method
    @classmethod
    def create_folder(cls, resource, folder):
        """Create a folder for a resource."""
        # avoid import loop
        from hs_core.views.utils import create_folder
        path_is_allowed(folder)
        # TODO: move code from location used below to here
        create_folder(resource.short_id, os.path.join('data', 'contents', folder))

    # TODO: move to BaseResource as instance method
    @classmethod
    def remove_folder(cls, resource, folder, user):
        """Remove a folder for a resource."""
        # avoid import loop
        from hs_core.views.utils import remove_folder
        path_is_allowed(folder)
        # TODO: move code from location used below to here
        remove_folder(user, resource.short_id, os.path.join('data', 'contents', folder))

    @property
    def has_logical_file(self):
        """Check existence of logical file."""
        return self.logical_file is not None

    @property
    def get_or_create_logical_file(self):
        """
        Create a logical file on the fly if it does not exist

        This is a temporary fix just for release 1.14. It is expected that further
        work on logical files will make this unnecessary.
        """
        # prevent import loops
        from hs_file_types.models.generic import GenericLogicalFile
        if self.content_object.resource_type == "CompositeResource":
            if not self.has_logical_file:
                logical_file = GenericLogicalFile.create()
                self.logical_file_content_object = logical_file
                self.save()
                logger = logging.getLogger(__name__)
                logger.warn("auto-create logical file for {}".format(self.storage_path))
            return self.logical_file
        else:
            return None

    @property
    def logical_file(self):
        """Return content_object of logical file."""
        return self.logical_file_content_object

    @property
    def logical_file_type_name(self):
        """Return class name of logical file's content object."""
        return self.logical_file_content_object.__class__.__name__

    @property
    def aggregation_display_name(self):
        """Return a name for the logical file type (aggregation)- used in UI"""
        return self.logical_file.get_aggregation_display_name()

    @property
    def has_generic_logical_file(self):
        """Return True of logical file type's classname is 'GenericLogicalFile'."""
        return self.logical_file_type_name == "GenericLogicalFile"

    @property
    def metadata(self):
        """Return logical file metadata."""
        if self.logical_file is not None:
            return self.logical_file.metadata
        return None

    @property
    def mime_type(self):
        """Return MIME type of represented file."""
        from .hydroshare.utils import get_file_mime_type
        return get_file_mime_type(self.file_name)

    @property
    def extension(self):
        """Return extension of resource file."""
        _, file_ext = os.path.splitext(self.storage_path)
        return file_ext

    @property
    def dir_path(self):
        """Return directory path of resource file."""
        return os.path.dirname(self.storage_path)

    @property
    def full_path(self):
        """Return full path of resource file."""
        return self.storage_path

    @property
    def file_name(self):
        """Return filename of resource file."""
        return os.path.basename(self.storage_path)

    @property
    def url(self):
        """Return the URL of the file contained in this ResourceFile.

        A GET of this URL simply returns the file. This URL is independent of federation.
        PUT, POST, and DELETE are not supported.

        This choice for a URL is dependent mainly upon conformance to DataOne URL standards
        that are also conformant to the format in resourcemap.xml. This url does not contain
        the site URL, which is prefixed when needed.

        This is based upon the resourcemap_urls.py entry:

            url(r'^resource/(?P<shortkey>[0-9a-f-]+)/data/contents/(?.+)/$',
                views.file_download_url_mapper,
                name='get_resource_file')

        This url does NOT depend upon federation status.
        """
        return '/' + os.path.join('resource', self.public_path)

    @property
    def public_path(self):
        """ return the public path (unqualified iRODS path) for a resource.
            This corresponds to the iRODS path if the resource isn't federated.
        """
        return os.path.join(self.resource.short_id, 'data', 'contents', self.short_path)

    @property
    def irods_path(self):
        """ Return the irods path for accessing a file, including possible federation information.
            This consists of the resource id, /data/contents/, and the file path.
        """

        if self.resource.is_federated:
            return os.path.join(self.resource.resource_federation_path, self.public_path)
        else:
            return self.public_path


class Bags(models.Model):
    """Represent data bags format as django model."""

    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)

    content_object = GenericForeignKey('content_type', 'object_id', for_concrete_model=False)
    timestamp = models.DateTimeField(default=now, db_index=True)

    class Meta:
        """Define meta properties of Bags model."""

        ordering = ['-timestamp']

    def get_content_model(self):
        """Return content model of Bags' content object."""
        return self.content_object.get_content_model()


class PublicResourceManager(models.Manager):
    """Extend Django model Manager to allow for public resource access."""

    def get_queryset(self):
        """Extend Django model Manager to allow for public resource access."""
        return super(PublicResourceManager, self).get_queryset().filter(raccess__public=True)


class DiscoverableResourceManager(models.Manager):
    """Extend Django model Manager to filter for public or discoverable resources."""

    def get_queryset(self):
        """Extend Django model Manager to filter for public or discoverable resources."""
        return super(DiscoverableResourceManager, self).get_queryset().filter(
            Q(raccess__discoverable=True) |
            Q(raccess__public=True))


# remove RichText parent class from the parameters for Django inplace editing to work;
# otherwise, get internal edit error when saving changes
class BaseResource(Page, AbstractResource):
    """Combine mezzanine Page model and AbstractResource model to establish base resource."""

    resource_type = models.CharField(max_length=50, default="GenericResource")
    # this locked_time field is added for resource versioning locking representing
    # the time when the resource is locked for a new version action. A value of null
    # means the resource is not locked
    locked_time = models.DateTimeField(null=True, blank=True)
    # this resource_federation_path is added to record where a HydroShare resource is
    # stored. The default is empty string meaning the resource is stored in HydroShare
    # zone. If a resource is stored in a fedearated zone, the field should store the
    # federated root path in the format of /federated_zone/home/localHydroProxy

    # TODO: change to null=True, default=None to simplify logic elsewhere
    resource_federation_path = models.CharField(max_length=100, blank=True, default='')

    objects = PublishedManager()
    public_resources = PublicResourceManager()
    discoverable_resources = DiscoverableResourceManager()

    collections = models.ManyToManyField('BaseResource', related_name='resources')

    discovery_content_type = 'Generic'  # used during discovery

    class Meta:
        """Define meta properties for BaseResource model."""

        verbose_name = 'Generic'
        db_table = 'hs_core_genericresource'

    def can_add(self, request):
        """Pass through to abstract resource can_add function."""
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        """Pass through to abstract resource can_add function."""
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        """Pass through to abstract resource can_delete function."""
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        """Pass through to abstract resource can_view function."""
        return AbstractResource.can_view(self, request)

    def get_irods_storage(self):
        """Return either IrodsStorage or FedStorage."""
        if self.resource_federation_path:
            return FedStorage()
        else:
            return IrodsStorage()

    @property
    def is_federated(self):
        """Return existence of resource_federation_path."""
        return self.resource_federation_path is not None and \
            self.resource_federation_path != ''

    # Paths relative to the resource
    @property
    def root_path(self):
        """Return the root folder of the iRODS structure containing resource files.

        Note that this folder doesn't directly contain the resource files;
        They are contained in ./data/contents/* instead.
        """
        if self.is_federated:
            return os.path.join(self.resource_federation_path, self.short_id)
        else:
            return self.short_id

    @property
    def file_path(self):
        """Return the file path of the resource.

        This is the root path plus "data/contents".
        This is the root of the folder structure for resource files.
        """
        return os.path.join(self.root_path, "data", "contents")

    @property
    def scimeta_path(self):
        """ path to science metadata file (in iRODS) """
        return os.path.join(self.root_path, "data", "resourcemetadata.xml")

    @property
    def resmap_path(self):
        """ path to resource map file (in iRODS) """
        return os.path.join(self.root_path, "data", "resourcemap.xml")

    # @property
    # def sysmeta_path(self):
    #     """ path to system metadata file (in iRODS) """
    #     return os.path.join(self.root_path, "data", "systemmetadata.xml")

    @property
    def bag_path(self):
        """Return the unique iRODS path to the bag for the resource.

        Since this is a cache, it is stored in a different place than the resource files.
        """
        bagit_path = getattr(settings, 'IRODS_BAGIT_PATH', 'bags')
        bagit_postfix = getattr(settings, 'IRODS_BAGIT_POSTFIX', 'zip')
        if self.is_federated:
            return os.path.join(self.resource_federation_path, bagit_path,
                                self.short_id + '.' + bagit_postfix)
        else:
            return os.path.join(bagit_path, self.short_id + '.' + bagit_postfix)

    @property
    def bag_url(self):
        """Get bag url of resource data bag."""
        bagit_path = getattr(settings, 'IRODS_BAGIT_PATH', 'bags')
        bagit_postfix = getattr(settings, 'IRODS_BAGIT_POSTFIX', 'zip')
        bag_path = "{path}/{resource_id}.{postfix}".format(path=bagit_path,
                                                           resource_id=self.short_id,
                                                           postfix=bagit_postfix)
        istorage = self.get_irods_storage()
        bag_url = istorage.url(bag_path)
        return bag_url

    # URIs relative to resource
    # these are independent of federation strategy
    # TODO: utilize "reverse" abstraction to tie this to urls.py for robustness

    # add these one by one to avoid errors.

    # @property
    # def root_uri(self):
    #     pass

    # @property
    # def scimeta_uri(self):
    #     return os.path.join(self.root_uri, 'scimeta')

    # @property
    # def sysmeta_uri(self):
    #     return os.path.join(self.root_uri, 'sysmeta')

    # @property
    # def file_uri(self):
    #     return os.path.join(self.root_uri, 'files')

    # create crossref deposit xml for resource publication
    def get_crossref_deposit_xml(self, pretty_print=True):
        """Return XML structure describing crossref deposit."""
        # importing here to avoid circular import problem
        from hydroshare.resource import get_activated_doi

        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schemaLocation = 'http://www.crossref.org/schema/4.3.6 ' \
                         'http://www.crossref.org/schemas/crossref4.3.6.xsd'
        ns = "http://www.crossref.org/schema/4.3.6"
        ROOT = etree.Element('{%s}doi_batch' % ns, version="4.3.6", nsmap={None: ns},
                             attrib={"{%s}schemaLocation" % xsi: schemaLocation})

        # get the resource object associated with this metadata container object - needed
        # to get the verbose_name

        # create the head sub element
        head = etree.SubElement(ROOT, 'head')
        etree.SubElement(head, 'doi_batch_id').text = self.short_id
        etree.SubElement(head, 'timestamp').text = arrow.get(self.updated)\
            .format("YYYYMMDDHHmmss")
        depositor = etree.SubElement(head, 'depositor')
        etree.SubElement(depositor, 'depositor_name').text = 'HydroShare'
        etree.SubElement(depositor, 'email_address').text = settings.DEFAULT_SUPPORT_EMAIL
        # The organization that owns the information being registered.
        etree.SubElement(head, 'registrant').text = 'Consortium of Universities for the ' \
                                                    'Advancement of Hydrologic Science, Inc. ' \
                                                    '(CUAHSI)'

        # create the body sub element
        body = etree.SubElement(ROOT, 'body')
        # create the database sub element
        db = etree.SubElement(body, 'database')
        # create the database_metadata sub element
        db_md = etree.SubElement(db, 'database_metadata', language="en")
        # titles is required element for database_metadata
        titles = etree.SubElement(db_md, 'titles')
        etree.SubElement(titles, 'title').text = "HydroShare Resources"
        # create the dataset sub element, dataset_type can be record or collection, set it to
        # collection for HydroShare resources
        dataset = etree.SubElement(db, 'dataset', dataset_type="collection")
        ds_titles = etree.SubElement(dataset, 'titles')
        etree.SubElement(ds_titles, 'title').text = self.metadata.title.value
        # doi_data is required element for dataset
        doi_data = etree.SubElement(dataset, 'doi_data')
        res_doi = get_activated_doi(self.doi)
        idx = res_doi.find('10.4211')
        if idx >= 0:
            res_doi = res_doi[idx:]
        etree.SubElement(doi_data, 'doi').text = res_doi
        etree.SubElement(doi_data, 'resource').text = self.metadata.identifiers.all().filter(
            name='hydroShareIdentifier')[0].url

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + etree.tostring(
            ROOT, pretty_print=pretty_print)

    @property
    def size(self):
        """Return the total size of all data files in iRODS.

        This size does not include metadata. Just files. Specifically,
        resourcemetadata.xml, systemmetadata.xml are not included in this
        size estimate.

        Raises SessionException if iRODS fails.
        """
        # compute the total file size for the resource
        f_sizes = [f.size for f in self.files.all()]
        return sum(f_sizes)

    @property
    def verbose_name(self):
        """Return verbose name of content_model."""
        return self.get_content_model()._meta.verbose_name

    @property
    def discovery_content_type(self):
        """Return verbose name of content type."""
        return self.get_content_model().discovery_content_type

    @property
    def can_be_published(self):
        """Determine when data and metadata are complete enough for the resource to be published.

        The property can be overriden by specific resource type which is not appropriate for
        publication such as the Web App resource
        :return:
        """
        return self.can_be_public_or_discoverable

    @classmethod
    def get_supported_upload_file_types(cls):
        """Get supported upload types for a resource.

        This can be overridden to choose which types of file can be uploaded by a subclass.

        By default, all file types are supported
        """
        # TODO: this should be replaced by an instance method.
        return ('.*')

    @classmethod
    def can_have_multiple_files(cls):
        """Return True if multiple files can be uploaded.

        This can be overridden to choose how many files can be uploaded by a subclass.

        By default, uploads are not limited.
        """
        # TODO: this should be replaced by an instance method.
        return True

    @classmethod
    def can_have_files(cls):
        """Return whether the resource supports files at all.

        This can be overridden to choose whether files can be uploaded by a subclass.

        By default, uploads are allowed.
        """
        # TODO: this should be replaced by an instance method.
        return True

    def get_hs_term_dict(self):
        """Return a dict of HS Terms and their values.

        Will be used to parse webapp url templates

        NOTES FOR ANY SUBCLASS OF THIS CLASS TO OVERRIDE THIS FUNCTION:
        resource types that inherit this class should add/merge their resource-specific HS Terms
        into this dict
        """
        hs_term_dict = {}

        hs_term_dict["HS_RES_ID"] = self.short_id
        hs_term_dict["HS_RES_TYPE"] = self.resource_type

        return hs_term_dict


# TODO Deprecated
class GenericResource(BaseResource):
    """Define GenericResource model."""

    objects = ResourceManager('GenericResource')

    @property
    def supports_folders(self):
        """Return True always."""
        return True

    discovery_content_type = 'Generic'  # used during discovery

    class Meta:
        """Define meta properties for GenericResource model."""
        verbose_name = 'Generic'
        proxy = True


old_get_content_model = Page.get_content_model


def new_get_content_model(self):
    """Override mezzanine get_content_model function for pages for resources."""
    from hs_core.hydroshare.utils import get_resource_types
    content_model = self.content_model
    if content_model.endswith('resource'):
        rt = [rt for rt in get_resource_types() if rt._meta.model_name == content_model][0]
        return rt.objects.get(id=self.id)
    return old_get_content_model(self)


Page.get_content_model = new_get_content_model


# This model has a one-to-one relation with the AbstractResource model
class CoreMetaData(models.Model):
    """Define CoreMetaData model."""

    XML_HEADER = '''<?xml version="1.0"?>
<!DOCTYPE rdf:RDF PUBLIC "-//DUBLIN CORE//DCMES DTD 2002/07/31//EN"
"http://dublincore.org/documents/2002/07/31/dcmes-xml/dcmes-xml-dtd.dtd">'''

    NAMESPACES = {'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                  'rdfs1': "http://www.w3.org/2001/01/rdf-schema#",
                  'dc': "http://purl.org/dc/elements/1.1/",
                  'dcterms': "http://purl.org/dc/terms/",
                  'hsterms': "http://hydroshare.org/terms/"}

    id = models.AutoField(primary_key=True)

    _description = GenericRelation(Description)    # resource abstract
    _title = GenericRelation(Title)
    creators = GenericRelation(Creator)
    contributors = GenericRelation(Contributor)
    dates = GenericRelation(Date)
    coverages = GenericRelation(Coverage)
    formats = GenericRelation(Format)
    identifiers = GenericRelation(Identifier)
    _language = GenericRelation(Language)
    subjects = GenericRelation(Subject)
    sources = GenericRelation(Source)
    relations = GenericRelation(Relation)
    _rights = GenericRelation(Rights)
    _type = GenericRelation(Type)
    _publisher = GenericRelation(Publisher)
    funding_agencies = GenericRelation(FundingAgency)

    @property
    def resource(self):
        """Return base resource object that the metadata defines."""
        return BaseResource.objects.filter(object_id=self.id).first()

    @property
    def title(self):
        """Return the first title object from metadata."""
        return self._title.all().first()

    @property
    def description(self):
        """Return the first description object from metadata."""
        return self._description.all().first()

    @property
    def language(self):
        """Return the first _language object from metadata."""
        return self._language.all().first()

    @property
    def rights(self):
        """Return the first rights object from metadata."""
        return self._rights.all().first()

    @property
    def type(self):
        """Return the first _type object from metadata."""
        return self._type.all().first()

    @property
    def publisher(self):
        """Return the first _publisher object from metadata."""
        return self._publisher.all().first()

    @property
    def spatial_coverage(self):
        return self.coverages.exclude(type='period').first()

    @property
    def temporal_coverage(self):
        return self.coverages.filter(type='period').first()

    @property
    def serializer(self):
        """Return an instance of rest_framework Serializer for self
        Note: Subclass must override this property
        """
        from views.resource_metadata_rest_api import CoreMetaDataSerializer
        return CoreMetaDataSerializer(self)

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Parse the input *metadata* dict to needed format and store it in
        *parsed_metadata* list
        :param  metadata: a dict of metadata that needs to be parsed to get the metadata in the
        format needed for updating the metadata elements supported by generic resource type
        :param  parsed_metadata: a list of dicts that will be appended with parsed data
        """

        keys_to_update = metadata.keys()
        if 'title' in keys_to_update:
            parsed_metadata.append({"title": {"value": metadata.pop('title')}})

        if 'creators' in keys_to_update:
            if not isinstance(metadata['creators'], list):
                metadata['creators'] = json.loads(metadata['creators'])
            for creator in metadata.pop('creators'):
                parsed_metadata.append({"creator": creator})

        if 'contributors' in keys_to_update:
            if not isinstance(metadata['contributors'], list):
                metadata['contributors'] = json.loads(metadata['contributors'])
            for contributor in metadata.pop('contributors'):
                parsed_metadata.append({"contributor": contributor})

        if 'coverages' in keys_to_update:
            for coverage in metadata.pop('coverages'):
                parsed_metadata.append({"coverage": coverage})

        if 'dates' in keys_to_update:
            for date in metadata.pop('dates'):
                parsed_metadata.append({"date": date})

        if 'description' in keys_to_update:
            parsed_metadata.append({"description": {"abstract": metadata.pop('description')}})

        if 'language' in keys_to_update:
            parsed_metadata.append({"language": {"code": metadata.pop('language')}})

        if 'rights' in keys_to_update:
            parsed_metadata.append({"rights": {"statement": metadata.pop('rights')}})

        if 'sources' in keys_to_update:
            for source in metadata.pop('sources'):
                parsed_metadata.append({"source": source})

        if 'subjects' in keys_to_update:
            for subject in metadata.pop('subjects'):
                parsed_metadata.append({"subject": {"value": subject['value']}})

    @classmethod
    def get_supported_element_names(cls):
        """Return a list of supported metadata element names."""
        return ['Description',
                'Creator',
                'Contributor',
                'Coverage',
                'Format',
                'Rights',
                'Title',
                'Type',
                'Date',
                'Identifier',
                'Language',
                'Subject',
                'Source',
                'Relation',
                'Publisher',
                'FundingAgency']

    @classmethod
    def get_form_errors_as_string(cls, form):
        """Helper method to generate a string from form.errors
        :param  form: an instance of Django Form class
        """
        error_string = ", ".join(key + ":" + form.errors[key][0]
                                 for key in form.errors.keys())
        return error_string

    def set_dirty(self, flag):
        """Track whethrer metadata object is dirty.

        Subclasses that have the attribute to track whether metadata object is dirty
        should override this method to allow setting that attribute

        :param flag: a boolean value
        :return:
        """
        pass

    def has_all_required_elements(self):
        """Determine whether metadata has all required elements.

        This method needs to be overriden by any subclass of this class
        if they implement additional metadata elements that are required
        """
        if not self.title:
            return False
        elif self.title.value.lower() == 'untitled resource':
            return False

        if not self.description:
            return False
        elif len(self.description.abstract.strip()) == 0:
            return False

        if self.creators.count() == 0:
            return False

        if not self.rights:
            return False
        elif len(self.rights.statement.strip()) == 0:
            return False

        if self.subjects.count() == 0:
            return False

        return True

    def get_required_missing_elements(self):
        """Return a list of required missing metadata elements.

        This method needs to be overriden by any subclass of this class
        if they implement additional metadata elements that are required
        """
        missing_required_elements = []

        if not self.title:
            missing_required_elements.append('Title')
        elif self.title.value.lower() == 'untitled resource':
            missing_required_elements.append('Title')
        if not self.description:
            missing_required_elements.append('Abstract')
        if not self.rights:
            missing_required_elements.append('Rights')
        if self.subjects.count() == 0:
            missing_required_elements.append('Keywords')

        return missing_required_elements

    def delete_all_elements(self):
        """Delete all metadata elements.

        This method needs to be overriden by any subclass of this class if that class
        has additional metadata elements
        """
        if self.title:
            self.title.delete()
        if self.description:
            self.description.delete()
        if self.language:
            self.language.delete()
        if self.rights:
            self.rights.delete()
        if self.publisher:
            self.publisher.delete()
        if self.type:
            self.type.delete()

        self.creators.all().delete()
        self.contributors.all().delete()
        self.dates.all().delete()
        self.identifiers.all().delete()
        self.coverages.all().delete()
        self.formats.all().delete()
        self.subjects.all().delete()
        self.sources.all().delete()
        self.relations.all().delete()
        self.funding_agencies.all().delete()

    def copy_all_elements_from(self, src_md, exclude_elements=None):
        """Copy all metadata elements from another resource."""
        md_type = ContentType.objects.get_for_model(src_md)
        supported_element_names = src_md.get_supported_element_names()
        for element_name in supported_element_names:
            element_model_type = src_md._get_metadata_element_model_type(element_name)
            elements_to_copy = element_model_type.model_class().objects.filter(
                object_id=src_md.id, content_type=md_type).all()
            for element in elements_to_copy:
                element_args = model_to_dict(element)
                element_args.pop('content_type')
                element_args.pop('id')
                element_args.pop('object_id')
                if exclude_elements:
                    if not element_name.lower() in exclude_elements:
                        self.create_element(element_name, **element_args)
                else:
                    self.create_element(element_name, **element_args)

    # this method needs to be overriden by any subclass of this class
    # to allow updating of extended (resource specific) metadata
    def update(self, metadata, user):
        """Define custom update method for CoreMetaData model.

        :param metadata: a list of dicts - each dict in the format of {element_name: **kwargs}
        element_name must be in lowercase.
        example of a dict in metadata list:
            {'creator': {'name': 'John Howard', 'email: 'jh@gmail.com'}}
        :param  user: user who is updating metadata
        :return:
        """
        from forms import TitleValidationForm, AbstractValidationForm, LanguageValidationForm, \
            RightsValidationForm, CreatorValidationForm, ContributorValidationForm, \
            SourceValidationForm, RelationValidationForm

        validation_forms_mapping = {'title': TitleValidationForm,
                                    'description': AbstractValidationForm,
                                    'language': LanguageValidationForm,
                                    'rights': RightsValidationForm,
                                    'creator': CreatorValidationForm,
                                    'contributor': ContributorValidationForm,
                                    'source': SourceValidationForm,
                                    'relation': RelationValidationForm
                                    }
        # updating non-repeatable elements
        with transaction.atomic():
            for element_name in ('title', 'description', 'language', 'rights'):
                for dict_item in metadata:
                    if element_name in dict_item:
                        validation_form = validation_forms_mapping[element_name](
                            dict_item[element_name])
                        if not validation_form.is_valid():
                            err_string = self.get_form_errors_as_string(validation_form)
                            raise ValidationError(err_string)
                self.update_non_repeatable_element(element_name, metadata)
            for element_name in ('creator', 'contributor', 'coverage', 'source', 'relation',
                                 'subject'):
                subjects = []
                for dict_item in metadata:
                    if element_name in dict_item:
                        if element_name == 'subject':
                            subject_data = dict_item['subject']
                            if 'value' not in subject_data:
                                raise ValidationError("Subject value is missing")
                            subjects.append(dict_item['subject']['value'])
                            continue
                        if element_name == 'coverage':
                            # coverage metadata is not allowed for update for composite
                            # and time series resource
                            if self.resource.resource_type in ("CompositeResource",
                                                               "TimeSeriesResource"):
                                err_msg = "Coverage metadata can't be updated for {} resource"
                                err_msg = err_msg.format(self.resource.resource_type)
                                raise ValidationError(err_msg)
                            coverage_data = dict_item[element_name]
                            if 'type' not in coverage_data:
                                raise ValidationError("Coverage type data is missing")
                            if 'value' not in coverage_data:
                                raise ValidationError("Coverage value data is missing")
                            coverage_value_dict = coverage_data['value']
                            coverage_type = coverage_data['type']
                            Coverage.validate_coverage_type_value_attributes(coverage_type,
                                                                             coverage_value_dict)
                            continue
                        if element_name in ['creator', 'contributor']:
                            try:
                                party_data = dict_item[element_name]
                                if 'identifiers' in party_data:
                                    if isinstance(party_data['identifiers'], dict):
                                        # convert dict to json for form validation
                                        party_data['identifiers'] = json.dumps(
                                            party_data['identifiers'])
                            except Exception:
                                raise ValidationError("Invalid identifier data for "
                                                      "creator/contributor")
                            validation_form = validation_forms_mapping[element_name](
                                party_data)
                        else:
                            validation_form = validation_forms_mapping[element_name](
                                dict_item[element_name])

                        if not validation_form.is_valid():
                            err_string = self.get_form_errors_as_string(validation_form)
                            err_string += " element name:{}".format(element_name)
                            raise ValidationError(err_string)
                if subjects:
                    subjects_set = set([s.lower() for s in subjects])
                    if len(subjects_set) < len(subjects):
                        raise ValidationError("Duplicate subject values found")
                self.update_repeatable_element(element_name=element_name, metadata=metadata)

            # allow only updating or creating date element of type valid
            element_name = 'date'
            date_list = [date_dict for date_dict in metadata if element_name in date_dict]
            if len(date_list) > 0:
                for date_item in date_list:
                    if 'type' in date_item[element_name]:
                        if date_item[element_name]['type'] == 'valid':
                            self.dates.filter(type='valid').delete()
                            self.create_element(element_model_name=element_name,
                                                **date_item[element_name])
                            break

            # allow only updating or creating identifiers which does not have name value
            # 'hydroShareIdentifier'
            element_name = 'identifier'
            identifier_list = [id_dict for id_dict in metadata if element_name in id_dict]
            if len(identifier_list) > 0:
                for id_item in identifier_list:
                    if 'name' in id_item[element_name]:
                        if id_item[element_name]['name'].lower() != 'hydroshareidentifier':
                            self.identifiers.filter(name=id_item[element_name]['name']).delete()
                            self.create_element(element_model_name=element_name,
                                                **id_item[element_name])

    def get_xml(self, pretty_print=True, include_format_elements=True):
        """Get metadata XML rendering."""
        # importing here to avoid circular import problem
        from hydroshare.utils import current_site_url, get_resource_types

        RDF_ROOT = etree.Element('{%s}RDF' % self.NAMESPACES['rdf'], nsmap=self.NAMESPACES)
        # create the Description element -this is not exactly a dc element
        rdf_Description = etree.SubElement(RDF_ROOT, '{%s}Description' % self.NAMESPACES['rdf'])

        resource_uri = self.identifiers.all().filter(name='hydroShareIdentifier')[0].url
        rdf_Description.set('{%s}about' % self.NAMESPACES['rdf'], resource_uri)

        # get the resource object associated with this metadata container object - needed to
        # get the verbose_name
        resource = BaseResource.objects.filter(object_id=self.id).first()
        rt = [rt for rt in get_resource_types()
              if rt._meta.object_name == resource.resource_type][0]
        resource = rt.objects.get(id=resource.id)

        # create the title element
        if self.title:
            dc_title = etree.SubElement(rdf_Description, '{%s}title' % self.NAMESPACES['dc'])
            dc_title.text = self.title.value

        # create the type element
        if self.type:
            dc_type = etree.SubElement(rdf_Description, '{%s}type' % self.NAMESPACES['dc'])
            dc_type.set('{%s}resource' % self.NAMESPACES['rdf'], self.type.url)

        # create the Description element (we named it as Abstract to differentiate from the parent
        # "Description" element)
        if self.description:
            dc_description = etree.SubElement(rdf_Description,
                                              '{%s}description' % self.NAMESPACES['dc'])
            dc_des_rdf_Desciption = etree.SubElement(dc_description,
                                                     '{%s}Description' % self.NAMESPACES['rdf'])
            dcterms_abstract = etree.SubElement(dc_des_rdf_Desciption,
                                                '{%s}abstract' % self.NAMESPACES['dcterms'])
            dcterms_abstract.text = clean_for_xml(self.description.abstract)

        for agency in self.funding_agencies.all():
            hsterms_agency = etree.SubElement(rdf_Description,
                                              '{%s}awardInfo' % self.NAMESPACES['hsterms'])
            hsterms_agency_rdf_Description = etree.SubElement(hsterms_agency, '{%s}Description' %
                                                              self.NAMESPACES['rdf'])
            hsterms_name = etree.SubElement(hsterms_agency_rdf_Description,
                                            '{%s}fundingAgencyName' % self.NAMESPACES['hsterms'])
            hsterms_name.text = clean_for_xml(agency.agency_name)
            if agency.agency_url:
                hsterms_agency_rdf_Description.set('{%s}about' % self.NAMESPACES['rdf'],
                                                   agency.agency_url)
            if agency.award_title:
                hsterms_title = etree.SubElement(hsterms_agency_rdf_Description, '{%s}awardTitle' %
                                                 self.NAMESPACES['hsterms'])
                hsterms_title.text = clean_for_xml(agency.award_title)
            if agency.award_number:
                hsterms_number = etree.SubElement(hsterms_agency_rdf_Description,
                                                  '{%s}awardNumber' % self.NAMESPACES['hsterms'])
                hsterms_number.text = clean_for_xml(agency.award_number)

        # use all creators associated with this metadata object to
        # generate creator xml elements
        for creator in self.creators.all():
            self._create_person_element(etree, rdf_Description, creator)

        for contributor in self.contributors.all():
            self._create_person_element(etree, rdf_Description, contributor)

        for coverage in self.coverages.all():
            coverage.add_to_xml_container(rdf_Description)

        for dt in self.dates.all():
            dc_date = etree.SubElement(rdf_Description, '{%s}date' % self.NAMESPACES['dc'])
            dc_term = '{%s}' + dt.type
            dc_date_dcterms = etree.SubElement(dc_date, dc_term % self.NAMESPACES['dcterms'])
            rdf_date_value = etree.SubElement(dc_date_dcterms, '{%s}value' % self.NAMESPACES['rdf'])
            if dt.type != 'valid':
                rdf_date_value.text = dt.start_date.isoformat()
            else:
                if dt.end_date:
                    rdf_date_value.text = "start=%s; end=%s" % (dt.start_date.isoformat(),
                                                                dt.end_date.isoformat())
                else:
                    rdf_date_value.text = dt.start_date.isoformat()

        if include_format_elements:
            for fmt in self.formats.all():
                dc_format = etree.SubElement(rdf_Description, '{%s}format' % self.NAMESPACES['dc'])
                dc_format.text = fmt.value

        for res_id in self.identifiers.all():
            dc_identifier = etree.SubElement(rdf_Description,
                                             '{%s}identifier' % self.NAMESPACES['dc'])
            dc_id_rdf_Description = etree.SubElement(dc_identifier,
                                                     '{%s}Description' % self.NAMESPACES['rdf'])
            id_hsterm = '{%s}' + res_id.name
            hsterms_hs_identifier = etree.SubElement(dc_id_rdf_Description,
                                                     id_hsterm % self.NAMESPACES['hsterms'])
            hsterms_hs_identifier.text = res_id.url

        if self.language:
            dc_lang = etree.SubElement(rdf_Description, '{%s}language' % self.NAMESPACES['dc'])
            dc_lang.text = self.language.code

        if self.publisher:
            dc_publisher = etree.SubElement(rdf_Description,
                                            '{%s}publisher' % self.NAMESPACES['dc'])
            dc_pub_rdf_Description = etree.SubElement(dc_publisher,
                                                      '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_pub_name = etree.SubElement(dc_pub_rdf_Description,
                                                '{%s}publisherName' % self.NAMESPACES['hsterms'])
            hsterms_pub_name.text = self.publisher.name
            hsterms_pub_url = etree.SubElement(dc_pub_rdf_Description,
                                               '{%s}publisherURL' % self.NAMESPACES['hsterms'])
            hsterms_pub_url.set('{%s}resource' % self.NAMESPACES['rdf'], self.publisher.url)

        for rel in self.relations.all():
            dc_relation = etree.SubElement(rdf_Description, '{%s}relation' % self.NAMESPACES['dc'])
            dc_rel_rdf_Description = etree.SubElement(dc_relation,
                                                      '{%s}Description' % self.NAMESPACES['rdf'])
            if rel.type in Relation.HS_RELATION_TERMS:
                term_ns = self.NAMESPACES['hsterms']
            else:
                term_ns = self.NAMESPACES['dcterms']
            terms_type = etree.SubElement(dc_rel_rdf_Description, '{%s}%s' % (term_ns, rel.type))

            # check if the relation value starts with 'http://' or 'https://'
            if rel.value.lower().find('http://') == 0 or rel.value.lower().find('https://') == 0:
                terms_type.set('{%s}resource' % self.NAMESPACES['rdf'], rel.value)
            else:
                terms_type.text = rel.value

        for src in self.sources.all():
            dc_source = etree.SubElement(rdf_Description, '{%s}source' % self.NAMESPACES['dc'])
            dc_source_rdf_Description = etree.SubElement(dc_source,
                                                         '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_derived_from = etree.SubElement(
                dc_source_rdf_Description, '{%s}isDerivedFrom' % self.NAMESPACES['hsterms'])

            # if the source value starts with 'http://' or 'https://' add value as an attribute
            if src.derived_from.lower().find('http://') == 0 or \
                    src.derived_from.lower().find('https://') == 0:
                hsterms_derived_from.set('{%s}resource' % self.NAMESPACES['rdf'], src.derived_from)
            else:
                hsterms_derived_from.text = src.derived_from

        if self.rights:
            dc_rights = etree.SubElement(rdf_Description, '{%s}rights' % self.NAMESPACES['dc'])
            dc_rights_rdf_Description = etree.SubElement(dc_rights,
                                                         '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_statement = etree.SubElement(dc_rights_rdf_Description,
                                                 '{%s}rightsStatement' % self.NAMESPACES['hsterms'])
            hsterms_statement.text = clean_for_xml(self.rights.statement)
            if self.rights.url:
                hsterms_url = etree.SubElement(dc_rights_rdf_Description,
                                               '{%s}URL' % self.NAMESPACES['hsterms'])
                hsterms_url.set('{%s}resource' % self.NAMESPACES['rdf'], self.rights.url)

        for sub in self.subjects.all():
            dc_subject = etree.SubElement(rdf_Description, '{%s}subject' % self.NAMESPACES['dc'])
            if sub.value.lower().find('http://') == 0 or sub.value.lower().find('https://') == 0:
                dc_subject.set('{%s}resource' % self.NAMESPACES['rdf'], sub.value)
            else:
                dc_subject.text = sub.value

        # resource type related additional attributes
        rdf_Description_resource = etree.SubElement(RDF_ROOT,
                                                    '{%s}Description' % self.NAMESPACES['rdf'])
        rdf_Description_resource.set('{%s}about' % self.NAMESPACES['rdf'], self.type.url)
        rdfs1_label = etree.SubElement(rdf_Description_resource,
                                       '{%s}label' % self.NAMESPACES['rdfs1'])
        rdfs1_label.text = resource._meta.verbose_name
        rdfs1_isDefinedBy = etree.SubElement(rdf_Description_resource,
                                             '{%s}isDefinedBy' % self.NAMESPACES['rdfs1'])
        rdfs1_isDefinedBy.text = current_site_url() + "/terms"

        # encode extended key/value arbitrary metadata
        resource = BaseResource.objects.filter(object_id=self.id).first()
        for key, value in resource.extra_metadata.items():
            hsterms_key_value = etree.SubElement(
                rdf_Description, '{%s}extendedMetadata' % self.NAMESPACES['hsterms'])
            hsterms_key_value_rdf_Description = etree.SubElement(
                hsterms_key_value, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_key = etree.SubElement(hsterms_key_value_rdf_Description,
                                           '{%s}key' % self.NAMESPACES['hsterms'])
            hsterms_key.text = key
            hsterms_value = etree.SubElement(hsterms_key_value_rdf_Description,
                                             '{%s}value' % self.NAMESPACES['hsterms'])
            hsterms_value.text = value

        return self.XML_HEADER + '\n' + etree.tostring(RDF_ROOT, pretty_print=pretty_print)

    # TODO: (Pabitra, Dt:11/21/2016) need to delete this method and users of this method
    # need to use the same method from the hydroshare.utils.py
    def add_metadata_element_to_xml(self, root, md_element, md_fields):
        """Generate XML elements for a given metadata element.

        Helper function to generate xml elements for a given metadata element that belongs to
        'hsterms' namespace

        :param root: the xml document root element to which xml elements for the specified
        metadata element needs to be added
        :param md_element: the metadata element object. The term attribute of the metadata
        element object is used for naming the root xml element for this metadata element.
        If the root xml element needs to be named differently, then this needs to be a tuple
        with first element being the metadata element object and the second being the name
        for the root element. Example: md_element=self.Creat or    # the term attribute of the
        Creator object will be used md_element=(self.Creator, 'Author') # 'Author' will be used

        :param md_fields: a list of attribute names of the metadata element (if the name to be used
         in generating the xml element name is same as the attribute name then include the
         attribute name as a list item. if xml element name needs to be different from the
         attribute name then the list item must be a tuple with first element of the tuple being
         the attribute name and the second element being what will be used in naming the xml
         element) Example: [('first_name', 'firstName'), 'phone', 'email']
         # xml sub-elements names: firstName, phone, email
        """
        from lxml import etree

        if isinstance(md_element, tuple):
            element_name = md_element[1]
            md_element = md_element[0]
        else:
            element_name = md_element.term

        hsterms_newElem = etree.SubElement(root,
                                           "{{{ns}}}{new_element}"
                                           .format(ns=self.NAMESPACES['hsterms'],
                                                   new_element=element_name))
        hsterms_newElem_rdf_Desc = etree.SubElement(
            hsterms_newElem, "{{{ns}}}Description".format(ns=self.NAMESPACES['rdf']))
        for md_field in md_fields:
            if isinstance(md_field, tuple):
                field_name = md_field[0]
                xml_element_name = md_field[1]
            else:
                field_name = md_field
                xml_element_name = md_field

            if hasattr(md_element, field_name):
                attr = getattr(md_element, field_name)
                if attr:
                    field = etree.SubElement(hsterms_newElem_rdf_Desc,
                                             "{{{ns}}}{field}".format(ns=self.NAMESPACES['hsterms'],
                                                                      field=xml_element_name))
                    field.text = str(attr)

    def _create_person_element(self, etree, parent_element, person):
        """Create a metadata element for a person (Creator, Contributor, etc)."""
        # importing here to avoid circular import problem
        from hydroshare.utils import current_site_url

        if isinstance(person, Creator):
            dc_person = etree.SubElement(parent_element, '{%s}creator' % self.NAMESPACES['dc'])
        else:
            dc_person = etree.SubElement(parent_element, '{%s}contributor' % self.NAMESPACES['dc'])

        dc_person_rdf_Description = etree.SubElement(dc_person,
                                                     '{%s}Description' % self.NAMESPACES['rdf'])

        if person.name:
            hsterms_name = etree.SubElement(dc_person_rdf_Description,
                                            '{%s}name' % self.NAMESPACES['hsterms'])
            hsterms_name.text = person.name
        if person.description:
            dc_person_rdf_Description.set('{%s}about' % self.NAMESPACES['rdf'],
                                          current_site_url() + person.description)

        if isinstance(person, Creator):
            hsterms_creatorOrder = etree.SubElement(dc_person_rdf_Description,
                                                    '{%s}creatorOrder' % self.NAMESPACES['hsterms'])
            hsterms_creatorOrder.text = str(person.order)

        if person.organization:
            hsterms_organization = etree.SubElement(dc_person_rdf_Description,
                                                    '{%s}organization' % self.NAMESPACES['hsterms'])
            hsterms_organization.text = person.organization

        if person.email:
            hsterms_email = etree.SubElement(dc_person_rdf_Description,
                                             '{%s}email' % self.NAMESPACES['hsterms'])
            hsterms_email.text = person.email

        if person.address:
            hsterms_address = etree.SubElement(dc_person_rdf_Description,
                                               '{%s}address' % self.NAMESPACES['hsterms'])
            hsterms_address.text = person.address

        if person.phone:
            hsterms_phone = etree.SubElement(dc_person_rdf_Description,
                                             '{%s}phone' % self.NAMESPACES['hsterms'])
            hsterms_phone.set('{%s}resource' % self.NAMESPACES['rdf'], 'tel:' + person.phone)

        if person.homepage:
            hsterms_homepage = etree.SubElement(dc_person_rdf_Description,
                                                '{%s}homepage' % self.NAMESPACES['hsterms'])
            hsterms_homepage.set('{%s}resource' % self.NAMESPACES['rdf'], person.homepage)

        for name, link in person.identifiers.iteritems():
            hsterms_link_type = etree.SubElement(dc_person_rdf_Description,
                                                 '{%s}' % self.NAMESPACES['hsterms'] + name)
            hsterms_link_type.set('{%s}resource' % self.NAMESPACES['rdf'], link)

    def create_element(self, element_model_name, **kwargs):
        """Create any supported metadata element."""
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        element = model_type.model_class().create(**kwargs)
        return element

    def update_element(self, element_model_name, element_id, **kwargs):
        """Update metadata element."""
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        model_type.model_class().update(element_id, **kwargs)

    def delete_element(self, element_model_name, element_id):
        """Delete Metadata element."""
        model_type = self._get_metadata_element_model_type(element_model_name)
        model_type.model_class().remove(element_id)

    def _get_metadata_element_model_type(self, element_model_name):
        """Get type of metadata element based on model type."""
        element_model_name = element_model_name.lower()
        if not self._is_valid_element(element_model_name):
            raise ValidationError("Metadata element type:%s is not one of the "
                                  "supported in core metadata elements."
                                  % element_model_name)

        unsupported_element_error = "Metadata element type:%s is not supported." \
                                    % element_model_name
        try:
            model_type = ContentType.objects.get(app_label=self._meta.app_label,
                                                 model=element_model_name)
        except ObjectDoesNotExist:
            try:
                model_type = ContentType.objects.get(app_label='hs_core',
                                                     model=element_model_name)
            except ObjectDoesNotExist:
                raise ValidationError(unsupported_element_error)

        if not issubclass(model_type.model_class(), AbstractMetaDataElement):
            raise ValidationError(unsupported_element_error)

        return model_type

    def _is_valid_element(self, element_name):
        """Check whether metadata element is valid."""
        allowed_elements = [el.lower() for el in self.get_supported_element_names()]
        return element_name.lower() in allowed_elements

    def update_non_repeatable_element(self, element_name, metadata, property_name=None):
        """Update a non-repeatable metadata element.

        This helper function is to create/update a specific metadata element as specified by
        *element_name*
        :param element_name: metadata element class name (e.g. title)
        :param metadata: a list of dicts - each dict has data to update/create a specific metadata
        element (e.g. {'title': {'value': 'my resource title'}}
        :param property_name: name of the property/attribute name in this class or its sub class
        to access the metadata element instance of *metadata_element*. This is needed only when
        the property/attribute name differs from the element class name

            Example:
            class ModelProgramMetaData(CoreMetaData):
                _mpmetadata = GenericRelation(MpMetadata)

                @property
                def program(self):
                    return self._mpmetadata.all().first()

            For the above class to update the metadata element MpMetadata, this function needs to
            be called with element_name='mpmetadata' and property_name='program'
        :return:
        """
        for dict_item in metadata:
            if element_name in dict_item:
                if property_name is None:
                    element = getattr(self, element_name, None)
                else:
                    element = getattr(self, property_name, None)
                if element:
                    self.update_element(element_id=element.id,
                                        element_model_name=element_name,
                                        **dict_item[element_name])
                else:
                    self.create_element(element_model_name=element_name,
                                        **dict_item[element_name])

    def update_repeatable_element(self, element_name, metadata, property_name=None):
        """Update a repeatable metadata element.

        Creates new metadata elements of type *element_name*. Any existing metadata elements of
        matching type get deleted first.
        :param element_name: class name of the metadata element (e.g. creator)
        :param metadata: a list of dicts containing data for each of the metadata elements that
        needs to be created/updated as part of bulk update
        :param property_name: (Optional) the property/attribute name used in this instance of
        CoreMetaData (or its sub class) to access all the objects of type *element_type*
            Example:
            class MODFLOWModelInstanceMetaData(ModelInstanceMetaData):
                 _model_input = GenericRelation(ModelInput)

                @property
                def model_inputs(self):
                    return self._model_input.all()

            For the above class to update the metadata element ModelInput, this function needs to
            be called with element_name='modelinput' and property_name='model_inputs'. If in the
            above class instead of using the attribute name '_model_inputs' we have used
            'modelinputs' then this function needs to be called with element_name='modelinput' and
            no need to pass a value for the property_name.

        :return:
        """
        element_list = [element_dict for element_dict in metadata if element_name in element_dict]
        if len(element_list) > 0:
            if property_name is None:
                elements = getattr(self, element_name + 's')
            else:
                elements = getattr(self, property_name)

            elements.all().delete()
            for element in element_list:
                self.create_element(element_model_name=element_name, **element[element_name])


def resource_processor(request, page):
    """Return mezzanine page processor for resource page."""
    extra = page_permissions_page_processor(request, page)
    return extra


@receiver(post_save)
def resource_creation_signal_handler(sender, instance, created, **kwargs):
    """Return resource update signal handler for newly created resource.

    For now this is just a placeholder for some actions to be taken when a resource gets saved
    """
    if isinstance(instance, AbstractResource):
        if created:
            pass
        else:
            resource_update_signal_handler(sender, instance, created, **kwargs)


def resource_update_signal_handler(sender, instance, created, **kwargs):
    """Do nothing (noop)."""
    pass
