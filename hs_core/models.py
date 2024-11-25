"""Declare critical models for Hydroshare hs_core app."""
import copy
import json
import logging
import os.path
import re
import sys
import unicodedata
import urllib.parse
from uuid import uuid4

import arrow
import requests
from dateutil import parser
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.fields import (GenericForeignKey,
                                                GenericRelation)
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import HStoreField
from django.core.exceptions import (ObjectDoesNotExist, PermissionDenied,
                                    SuspiciousFileOperation, ValidationError)
from django.core.files import File
from django.core.validators import URLValidator
from django.db import models, transaction
from django.db.models import Q, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.urls import reverse
from django.utils.timezone import now
from dominate.tags import div, h4, legend, table, tbody, td, th, tr
from lxml import etree
from markdown import markdown
from mezzanine.conf import settings as s
from mezzanine.core.managers import PublishedManager
from mezzanine.core.models import Ownable
from mezzanine.generic.fields import CommentsField, RatingField
from mezzanine.pages.managers import PageManager
from mezzanine.pages.models import Page
from nameparser import HumanName
from pyld import jsonld
from rdflib import BNode, Literal, URIRef
from rdflib.namespace import DC, DCTERMS, RDF
from spam_patterns.worst_patterns_re import patterns

from django_irods.icommands import SessionException
from django_irods.storage import IrodsStorage
from hs_core.enums import (CrossRefSubmissionStatus, CrossRefUpdate,
                           RelationTypes)
from hs_core.irods import ResourceFileIRODSMixin, ResourceIRODSMixin

from .hs_rdf import (HSTERMS, RDFS1, RDF_MetaData_Mixin, RDF_Term_MixIn,
                     rdf_terms)
from .languages_iso import languages as iso_languages

from django_tus.signals import tus_upload_finished_signal


def clean_abstract(original_string):
    """Clean abstract for XML inclusion.

    This function takes an original string and removes any illegal XML characters
    from it. It uses regular expressions to identify and remove the illegal characters.

    Args:
        original_string (str): The original string to be cleaned.

    Returns:
        str: The cleaned string with illegal XML characters removed.

    Raises:
        ValidationError: If there is an error cleaning the abstract.

    """
    # https://stackoverflow.com/a/64570125
    try:
        illegal_unichrs = [(0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F),
                           (0x7F, 0x84), (0x86, 0x9F),
                           (0xFDD0, 0xFDDF), (0xFFFE, 0xFFFF)]
        if sys.maxunicode >= 0x10000:  # not narrow build
            illegal_unichrs.extend([(0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF),
                                    (0x3FFFE, 0x3FFFF), (0x4FFFE, 0x4FFFF),
                                    (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
                                    (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF),
                                    (0x9FFFE, 0x9FFFF), (0xAFFFE, 0xAFFFF),
                                    (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
                                    (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF),
                                    (0xFFFFE, 0xFFFFF), (0x10FFFE, 0x10FFFF)])

        illegal_ranges = [fr'{chr(low)}-{chr(high)}' for (low, high) in illegal_unichrs]
        xml_illegal_character_regex = '[' + ''.join(illegal_ranges) + ']'
        illegal_xml_chars_re = re.compile(xml_illegal_character_regex)
        filtered_string = illegal_xml_chars_re.sub('', original_string)
        return filtered_string
    except (KeyError, TypeError) as ex:
        raise ValidationError(f"Error cleaning abstract: {ex}")


def clean_for_xml(s):
    """
    Remove all control characters from a unicode string in preparation for XML inclusion

    * Convert \n\n+ to unicode paragraph
    * Convert \n alone to unicode RETURN (return SYMBOL)
    * Convert control characters to spaces if last character is not space.
    * Space-pad paragraph and NL symbols as necessary

    """
    # https://www.w3.org/TR/REC-xml/#sec-line-ends
    CR = chr(0x23CE)  # carriage return unicode SYMBOL
    PARA = chr(0xB6)  # paragraph mark unicode SYMBOL
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

    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)


def get_user(request):
    """Authorize user based on API key if it was passed, otherwise just use the request's user.

    NOTE: The API key portion has been removed with TastyPie and will be restored when the
    new API is built.

    :param request:
    :return: django.contrib.auth.User
    """
    if not hasattr(request, 'user'):
        raise PermissionDenied
    if request.user.is_authenticated:
        return User.objects.get(pk=request.user.pk)
    else:
        return request.user


class UserValidationError(ValidationError):
    pass


def validate_hydroshare_user_id(value):
    """Validate that a hydroshare_user_id is valid for a hydroshare user."""
    err_message = '%s is not a valid id for hydroshare user' % value
    if value:
        try:
            value = int(value)
        except ValueError:
            raise ValidationError(err_message)

        # check the user exists for the provided user id
        if not User.objects.filter(pk=value).exists():
            raise UserValidationError(err_message)


def validate_user_url(value):
    """Validate that a URL is a valid URL for a hydroshare user."""
    err_message = '%s is not a valid url for hydroshare user' % value
    if value:
        url_parts = value.split('/')
        if len(url_parts) != 4:
            raise ValidationError(err_message)
        if url_parts[1] != 'user':
            raise ValidationError(err_message)

        try:
            user_id = int(url_parts[2])
        except ValueError:
            raise ValidationError(err_message)

        # check the user exists for the provided user id
        if not User.objects.filter(pk=user_id).exists():
            raise ValidationError(err_message)


class ResourcePermissionsMixin(Ownable):
    """Mix in can_* permission helper functions between users and resources."""

    creator = models.ForeignKey(User, on_delete=models.CASCADE,
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
        from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize
        return authorize(request, self,
                         needed_permission=ACTION_TO_AUTHORIZE.DELETE_RESOURCE,
                         raises_exception=False)[1]

    def can_change(self, request):
        """Use utils.authorize method to determine if user can change a resource."""
        # have to do import locally to avoid circular import
        from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize
        return authorize(request, self,
                         needed_permission=ACTION_TO_AUTHORIZE.EDIT_RESOURCE,
                         raises_exception=False)[1]

    def can_view(self, request):
        """Use utils.authorize method to determine if user can view a resource."""
        # have to do import locally to avoid circular import
        from hs_core.views.utils import ACTION_TO_AUTHORIZE, authorize
        return authorize(request, self,
                         needed_permission=ACTION_TO_AUTHORIZE.VIEW_METADATA,
                         raises_exception=False)[1]


# Build a JSON serializable object with user data
def get_access_object(user, user_type, user_access):
    from hs_core.templatetags.hydroshare_tags import best_name
    access_object = None
    picture = None

    if not hasattr(user, 'viewable_contributions'):
        user.viewable_contributions = 0

    if user_type == "user":
        if user.userprofile.picture:
            picture = user.userprofile.picture.url

        access_object = {
            "user_type": user_type,
            "access": user_access,
            "id": user.id,
            "pictureUrl": picture,
            "best_name": best_name(user),
            "user_name": user.username,
            "can_undo": user.can_undo,
            # Data used to populate profile badge:
            "email": user.email,
            "organization": user.userprofile.organization,
            "title": user.userprofile.title,
            "viewable_contributions": user.viewable_contributions if user.is_active else None,
            "subject_areas": user.userprofile.subject_areas,
            "identifiers": user.userprofile.identifiers,
            "state": user.userprofile.state,
            "country": user.userprofile.country,
            "joined": user.date_joined.strftime("%d %b, %Y"),
            "is_active": user.is_active
        }
    elif user_type == "group":
        if user.gaccess.picture:
            picture = user.gaccess.picture.url

        access_object = {
            "user_type": user_type,
            "access": user_access,
            "id": user.id,
            "pictureUrl": picture,
            "best_name": user.name,
            "user_name": None,
            "can_undo": user.can_undo
        }

    return access_object


def page_permissions_page_processor(request, page):
    """Return a dict describing permissions for current user."""
    from hs_access_control.models.privilege import PrivilegeCodes
    from hs_core.hydroshare.utils import get_remaining_user_quota, convert_file_size_to_unit

    cm = page.get_content_model()
    can_change_resource_flags = False
    self_access_level = None
    if request.user.is_authenticated:
        if request.user.uaccess.can_change_resource_flags(cm):
            can_change_resource_flags = True

        # this will get resource access privilege even for admin user
        user_privilege = cm.raccess.get_effective_user_privilege(request.user)
        if user_privilege == PrivilegeCodes.OWNER:
            self_access_level = 'owner'
        elif user_privilege == PrivilegeCodes.CHANGE:
            self_access_level = 'edit'
        elif user_privilege == PrivilegeCodes.VIEW:
            self_access_level = 'view'

    owners = cm.raccess.owners.all()
    editors = cm.raccess.get_users_with_explicit_access(PrivilegeCodes.CHANGE,
                                                        include_group_granted_access=False)
    viewers = cm.raccess.get_users_with_explicit_access(PrivilegeCodes.VIEW,
                                                        include_group_granted_access=False)
    edit_groups = cm.raccess.edit_groups
    view_groups = cm.raccess.view_groups.exclude(pk__in=edit_groups)

    last_changed_by = cm.last_changed_by

    if request.user.is_authenticated:
        for owner in owners:
            owner.can_undo = request.user.uaccess.can_undo_share_resource_with_user(cm, owner)
            owner.viewable_contributions = request.user.uaccess.can_view_resources_owned_by(owner)

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
        if last_changed_by.is_active:
            last_changed_by.viewable_contributions = request.user.uaccess.can_view_resources_owned_by(last_changed_by)

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
    last_changed_by.can_undo = False

    users_json = []

    for usr in owners:
        users_json.append(get_access_object(usr, "user", "owner"))

    for usr in editors:
        users_json.append(get_access_object(usr, "user", "edit"))

    for usr in viewers:
        users_json.append(get_access_object(usr, "user", "view"))

    for usr in edit_groups:
        users_json.append(get_access_object(usr, "group", "edit"))

    for usr in view_groups:
        users_json.append(get_access_object(usr, "group", "view"))

    if last_changed_by.is_active:
        lcb_access_level = cm.raccess.get_effective_user_privilege(last_changed_by)
        if lcb_access_level == PrivilegeCodes.OWNER:
            lcb_access_level = 'owner'
        elif lcb_access_level == PrivilegeCodes.CHANGE:
            lcb_access_level = 'edit'
        elif lcb_access_level == PrivilegeCodes.VIEW:
            lcb_access_level = 'view'
    else:
        lcb_access_level = 'none'

    last_changed_by = json.dumps(get_access_object(last_changed_by, "user", lcb_access_level))

    users_json = json.dumps(users_json)

    is_replaced_by = cm.get_relation_version_res_url(RelationTypes.isReplacedBy)
    is_version_of = cm.get_relation_version_res_url(RelationTypes.isVersionOf)

    permissions_allow_copy = False
    if request.user.is_authenticated:
        permissions_allow_copy = request.user.uaccess.can_view_resource(cm)

    show_manage_access = False
    is_owner = self_access_level == 'owner'
    is_edit = self_access_level == 'edit'
    is_view = self_access_level == 'view'
    if is_owner or (cm.raccess.shareable and (is_view or is_edit)):
        show_manage_access = True

    max_file_size = getattr(settings, 'FILE_UPLOAD_MAX_SIZE', 25 * 1024**3)
    remaining_quota = get_remaining_user_quota(cm.quota_holder, "MB")
    remaining_quota = remaining_quota * 1024**2 if remaining_quota else 0

    # https://docs.djangoproject.com/en/3.2/ref/settings/#data-upload-max-memory-size
    max_chunk_size = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 2.5 * 1024**2)

    max_number_of_files_in_single_local_upload = getattr(settings, 'MAX_NUMBER_OF_FILES_IN_SINGLE_LOCAL_UPLOAD', 50)
    parallel_uploads_limit = getattr(settings, 'PARALLEL_UPLOADS_LIMIT', 10)

    companion_url = getattr(settings, 'COMPANION_URL', 'https://companion.hydroshare.org/')
    uppy_upload_endpoint = getattr(settings, 'UPPY_UPLOAD_ENDPOINT', 'https://hydroshare.org/hsapi/tus/')

    # get the session id for the current user
    if request.user.is_authenticated:
        try:
            session = request.session.session_key
        except SessionException:
            session = None

    return {
        'resource_type': cm._meta.verbose_name,
        "users_json": users_json,
        "owners": owners,
        "self_access_level": self_access_level,
        "permissions_allow_copy": permissions_allow_copy,
        "can_change_resource_flags": can_change_resource_flags,
        "is_replaced_by": is_replaced_by,
        "is_version_of": is_version_of,
        "show_manage_access": show_manage_access,
        "last_changed_by": last_changed_by,
        "remaining_quota": remaining_quota,
        "max_file_size": max_file_size,
        "max_chunk_size": max_chunk_size,
        "max_number_of_files_in_single_local_upload": max_number_of_files_in_single_local_upload,
        "parallel_uploads_limit": parallel_uploads_limit,
        "companion_url": companion_url,
        "uppy_upload_endpoint": uppy_upload_endpoint,
        "hs_s_id": session
    }


class AbstractMetaDataElement(models.Model, RDF_Term_MixIn):
    """Define abstract class for all metadata elements."""

    object_id = models.PositiveIntegerField()
    # see the following link the reason for having the related_name setting
    # for the content_type attribute
    # https://docs.djangoproject.com/en/1.6/topics/db/models/#abstract-related-name
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                     related_name="%(app_label)s_%(class)s_related")
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        """Return unicode for python 3 compatibility in templates"""
        return self.__unicode__()

    @property
    def metadata(self):
        """Return content object that describes metadata."""
        return self.content_object

    @property
    def dict(self):
        return {self.__class__.__name__: model_to_dict(self)}

    @classmethod
    def create(cls, **kwargs):
        """Pass through kwargs to object.create method."""
        return cls.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        """Pass through kwargs to update specific metadata object."""
        element = cls.objects.get(id=element_id)
        for key, value in list(kwargs.items()):
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


class PartyValidationError(ValidationError):
    pass


class Party(AbstractMetaDataElement):
    """Define party model to define a person."""

    hydroshare_user_id = models.IntegerField(null=True, blank=True, validators=[validate_hydroshare_user_id])
    name = models.CharField(max_length=100, null=True, blank=True)
    organization = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    phone = models.CharField(max_length=25, null=True, blank=True)
    homepage = models.URLField(null=True, blank=True)

    # flag to track if a creator/contributor is an active hydroshare user
    # this flag is set by the system based on the field 'hydoshare_user_id'
    is_active_user = models.BooleanField(default=False)

    # to store one or more external identifier (Google Scholar, ResearchGate, ORCID etc)
    # each identifier is stored as a key/value pair {name:link}
    identifiers = HStoreField(default=dict)

    # list of identifiers currently supported
    supported_identifiers = {'ResearchGateID':
                             re.compile(r'^https:\/\/www\.researchgate\.net\/profile\/[^\s]+$'),
                             'ORCID':
                             re.compile(r'^https:\/\/orcid\.org\/[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{4}$'),
                             'GoogleScholarID':
                             re.compile(r'^https:\/\/scholar\.google\.com\/citations\?.*user=[^\s]+$'),
                             'ResearcherID':
                             'https://www.researcherid.com/'}

    def __unicode__(self):
        """Return name field for unicode representation."""
        return self.name

    class Meta:
        """Define meta properties for Party class."""

        abstract = True

    def rdf_triples(self, subject, graph):
        party_type = self.get_class_term()
        party = BNode()
        graph.add((subject, party_type, party))
        for field_term, field_value in self.get_field_terms_and_values(['identifiers', 'is_active_user']):
            # TODO: remove this once we are no longer concerned with backwards compatibility
            if field_term == HSTERMS.hydroshare_user_id:
                graph.add((party, HSTERMS.description, field_value))
            graph.add((party, field_term, field_value))
        for k, v in self.identifiers.items():
            graph.add((party, getattr(HSTERMS, k), URIRef(v)))

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        """Default implementation that ingests by convention"""
        party_type = cls.get_class_term()
        for party in graph.objects(subject=subject, predicate=party_type):
            value_dict = {}
            identifiers = {}
            fields_by_term = {cls.get_field_term(field.name): field for field in cls._meta.fields}
            for _, p, o in graph.triples((party, None, None)):
                # TODO: remove this once we are no longer concerned with backwards compatibility
                if p == HSTERMS.description:
                    # parse the description into a hydroshare_user_id
                    p = HSTERMS.hydroshare_user_id
                    o = o.split('user/')[-1]
                    o = o.replace("/", "")
                if p not in fields_by_term:
                    identifiers[p.rsplit("/", 1)[1]] = str(o)
                else:
                    value_dict[fields_by_term[p].name] = str(o)
            if value_dict or identifiers:
                if identifiers:
                    cls.create(content_object=content_object, identifiers=identifiers, **value_dict)
                else:
                    cls.create(content_object=content_object, **value_dict)

    @classmethod
    def get_post_data_with_identifiers(cls, request, as_json=True):
        identifier_names = request.POST.getlist('identifier_name')
        identifier_links = request.POST.getlist('identifier_link')
        identifiers = {}
        if identifier_links and identifier_names:
            if len(identifier_names) != len(identifier_links):
                raise Exception("Invalid data for identifiers")
            identifiers = dict(list(zip(identifier_names, identifier_links)))
            if len(identifier_names) != len(list(identifiers.keys())):
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

        hs_user_id = kwargs.get('hydroshare_user_id', '')
        if hs_user_id:
            validate_hydroshare_user_id(hs_user_id)

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
                raise PartyValidationError(
                    "Either an organization or name is required for a creator element")

            if 'name' in kwargs and kwargs['name'] is not None:
                if len(kwargs['name'].strip()) == 0:
                    if 'organization' in kwargs and kwargs['organization'] is not None:
                        if len(kwargs['organization'].strip()) == 0:
                            raise PartyValidationError(
                                "Either the name or organization must not be blank for the creator "
                                "element")

            if 'order' not in kwargs or kwargs['order'] is None:
                kwargs['order'] = creator_order

        party = super(Party, cls).create(**kwargs)

        if party.hydroshare_user_id:
            user = User.objects.get(id=party.hydroshare_user_id)
            party.is_active_user = user.is_active
            party.save()
        return party

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update method for Party model."""
        element_name = cls.__name__
        creator_order = None
        if 'hydroshare_user_id' in kwargs:
            party = cls.objects.get(id=element_id)
            if party.hydroshare_user_id is not None and kwargs['hydroshare_user_id'] is not None:
                if party.hydroshare_user_id != kwargs['hydroshare_user_id']:
                    raise PartyValidationError("HydroShare user identifier can't be changed.")

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

        if party.hydroshare_user_id is not None:
            user = User.objects.get(id=party.hydroshare_user_id)
            party.is_active_user = user.is_active
        else:
            party.is_active_user = False
        party.save(update_fields=["is_active_user"])

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
                            res_cr.save(update_fields=["order"])
                    else:
                        if res_cr.order > party.order and res_cr.order <= creator_order:
                            res_cr.order -= 1
                            res_cr.save(update_fields=["order"])

                party.order = creator_order
                party.save(update_fields=["order"])

    @property
    def relative_uri(self):
        return f"/user/{self.hydroshare_user_id}/" if self.hydroshare_user_id else None

    @property
    def is_active(self):
        return self.is_active_user

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
                raise PartyValidationError("The only creator of the resource can't be deleted.")

            creators_to_update = Creator.objects.filter(
                object_id=party.object_id,
                content_type__pk=party.content_type.id).exclude(order=party.order).all()

            for cr in creators_to_update:
                if cr.order > party.order:
                    cr.order -= 1
                    cr.save(update_fields=["order"])
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
                    raise PartyValidationError("Value for identifiers not in the correct format")
        # identifiers = kwargs['identifiers']
        if identifiers:
            # validate the identifiers are one of the supported ones
            for name in identifiers:
                if name not in cls.supported_identifiers:
                    raise PartyValidationError("Invalid data found for identifiers. "
                                               "{} not a supported identifier.". format(name))
            # validate identifier values - check for duplicate links
            links = [link.lower() for link in list(identifiers.values())]
            if len(links) != len(set(links)):
                raise PartyValidationError("Invalid data found for identifiers. "
                                           "Duplicate identifier links found.")

            for link in links:
                validator = URLValidator()
                try:
                    validator(link)
                except ValidationError:
                    raise PartyValidationError("Invalid data found for identifiers. "
                                               "Identifier link must be a URL.")

            # validate identifier keys - check for duplicate names
            names = [n.lower() for n in list(identifiers.keys())]
            if len(names) != len(set(names)):
                raise PartyValidationError("Invalid data found for identifiers. "
                                           "Duplicate identifier names found")

            # validate that the links for the known identifiers are valid
            for id_name in cls.supported_identifiers:
                id_link = identifiers.get(id_name, '')
                if id_link:
                    regex = cls.supported_identifiers[id_name]
                    if not re.match(regex, id_link):
                        raise PartyValidationError("Invalid data found for identifiers. "
                                                   f"\'{id_link}\' is not a valid {id_name}.")
        return identifiers


@rdf_terms(DC.contributor)
class Contributor(Party):
    """Extend Party model with the term of 'Contributor'."""

    term = 'Contributor'


@rdf_terms(DC.creator, order=HSTERMS.creatorOrder)
class Creator(Party):
    """Extend Party model with the term of 'Creator' and a proper ordering."""

    term = "Creator"
    order = models.PositiveIntegerField()

    class Meta:
        """Define meta properties for Creator class."""

        ordering = ['order']


def validate_abstract(value):
    """
    Validates the abstract value by ensuring it can serialize as XML.

    Args:
        value (str): The abstract value to be validated.

    Raises:
        ValidationError: If there is an error parsing the abstract as XML.

    Returns:
        None
    """
    err_message = 'Error parsing abstract as XML.'
    if value:
        try:
            ROOT = etree.Element('root')
            body_node = etree.SubElement(ROOT, 'body')
            c_abstract = clean_abstract(value)
            etree.SubElement(body_node, 'description').text = c_abstract
        except Exception as ex:
            raise ValidationError(f'{err_message}, more info: {ex}')


@rdf_terms(DC.description, abstract=DCTERMS.abstract)
class Description(AbstractMetaDataElement):
    """Define Description metadata element model."""

    term = 'Description'
    abstract = models.TextField(validators=[validate_abstract])

    def __unicode__(self):
        """Return abstract field for unicode representation."""
        return self.abstract

    class Meta:
        """Define meta properties for Description model."""

        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        """Define custom update method for Description model."""
        kwargs['abstract'] = clean_abstract(kwargs['abstract'])
        return super(Description, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update method for Description model."""
        kwargs['abstract'] = clean_abstract(kwargs['abstract'])
        super(Description, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        """Create custom remove method for Description model."""
        raise ValidationError("Description element of a resource can't be deleted.")


@rdf_terms(DCTERMS.bibliographicCitation)
class Citation(AbstractMetaDataElement):
    """Define Citation metadata element model."""

    term = 'Citation'
    value = models.TextField()

    def __unicode__(self):
        """Return value field for unicode representation."""
        return self.value

    class Meta:
        """Define meta properties for Citation class."""

        unique_together = ("content_type", "object_id")

    @classmethod
    def update(cls, element_id, **kwargs):
        """Call parent update function for Citation class."""
        super(Citation, cls).update(element_id, **kwargs)

    @classmethod
    def remove(cls, element_id):
        """Call delete function for Citation class."""
        element = cls.objects.get(id=element_id)
        element.delete()

    def rdf_triples(self, subject, graph):
        graph.add((subject, self.get_class_term(), Literal(self.value)))

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        citation = graph.value(subject=subject, predicate=cls.get_class_term())
        if citation:
            Citation.create(value=citation.value, content_object=content_object)


@rdf_terms(DC.title)
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
    def remove(cls, element_id):
        """Define custom remove function for Title class."""
        raise ValidationError("Title element of a resource can't be deleted.")

    def rdf_triples(self, subject, graph):
        graph.add((subject, self.get_class_term(), Literal(self.value)))

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        title = graph.value(subject=subject, predicate=cls.get_class_term())
        if title:
            Title.create(value=title.value, content_object=content_object)


@rdf_terms(DC.type)
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

    def rdf_triples(self, subject, graph):
        graph.add((subject, self.get_class_term(), URIRef(self.url)))

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        url = graph.value(subject=subject, predicate=cls.get_class_term())
        if url:
            Type.create(url=str(url), content_object=content_object)


@rdf_terms(DC.date)
class Date(AbstractMetaDataElement):
    """Define Date metadata model."""

    DC_DATE_TYPE_CHOICES = (
        ('created', 'Created'),
        ('modified', 'Modified'),
        ('valid', 'Valid'),
        ('available', 'Available')
    )
    HS_DATE_TYPE_CHOICES = (
        ('reviewStarted', 'Review Started'),
        ('published', 'Published'),
    )
    DATE_TYPE_CHOICES = DC_DATE_TYPE_CHOICES + HS_DATE_TYPE_CHOICES

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

    def rdf_triples(self, subject, graph):
        date_node = BNode()
        graph.add((subject, self.get_class_term(), date_node))
        if self.type in [inner[0] for inner in self.DC_DATE_TYPE_CHOICES]:
            graph.add((date_node, RDF.type, getattr(DCTERMS, self.type)))
        else:
            graph.add((date_node, RDF.type, getattr(HSTERMS, self.type)))
        graph.add((date_node, RDF.value, Literal(self.start_date.isoformat())))

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        for _, _, date_node in graph.triples((subject, cls.get_class_term(), None)):
            type = graph.value(subject=date_node, predicate=RDF.type)
            value = graph.value(subject=date_node, predicate=RDF.value)
            if type and value:
                type = type.split('/')[-1]
                start_date = parser.parse(str(value))
                Date.create(type=type, start_date=start_date, content_object=content_object)

    @classmethod
    def create(cls, **kwargs):
        """Define custom create method for Date model."""
        if 'type' in kwargs:
            if not kwargs['type'] in list(dict(cls.DATE_TYPE_CHOICES).keys()):
                raise ValidationError('Invalid date type:%s' % kwargs['type'])

            # get matching resource
            metadata_obj = kwargs['content_object']
            resource = BaseResource.objects.filter(object_id=metadata_obj.id).first()

            if kwargs['type'] != 'valid':
                if 'end_date' in kwargs:
                    del kwargs['end_date']

            if 'start_date' in kwargs:
                if isinstance(kwargs['start_date'], str):
                    kwargs['start_date'] = parser.parse(kwargs['start_date'])
            if kwargs['type'] == 'published':
                if not resource.raccess.published:
                    raise ValidationError("Resource is not published yet.")
            if kwargs['type'] == 'reviewStarted':
                if resource.raccess.review_pending:
                    raise ValidationError("Review is already pending.")
            elif kwargs['type'] == 'available':
                if not resource.raccess.public:
                    raise ValidationError("Resource has not been made public yet.")
            elif kwargs['type'] == 'valid':
                if 'end_date' in kwargs:
                    if isinstance(kwargs['end_date'], str):
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
            if isinstance(kwargs['start_date'], str):
                kwargs['start_date'] = parser.parse(kwargs['start_date'])
            if dt.type == 'created':
                raise ValidationError("Resource creation date can't be changed")
            elif dt.type == 'modified':
                dt.start_date = now().isoformat()
                dt.save()
            elif dt.type == 'valid':
                if 'end_date' in kwargs:
                    if isinstance(kwargs['end_date'], str):
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


class AbstractRelation(AbstractMetaDataElement):
    """Define Abstract Relation class."""
    SOURCE_TYPES = ()
    term = 'Relation'
    type = models.CharField(max_length=100, choices=SOURCE_TYPES)
    value = models.TextField()

    def __str__(self):
        """Return {type} {value} for string representation."""
        return "{type} {value}".format(type=self.type, value=self.value)

    def __unicode__(self):
        """Return {type} {value} for unicode representation (deprecated)."""
        return "{type} {value}".format(type=self.type, value=self.value)

    @classmethod
    def get_supported_types(cls):
        return dict(cls.SOURCE_TYPES).keys()

    def type_description(self):
        return dict(self.SOURCE_TYPES)[self.type]

    @classmethod
    def create(cls, **kwargs):
        """Define custom create method for Relation class."""
        if 'type' not in kwargs:
            ValidationError("Type of relation element is missing.")
        if 'value' not in kwargs:
            ValidationError("Value of relation element is missing.")

        if not kwargs['type'] in list(dict(cls.SOURCE_TYPES).keys()):
            raise ValidationError('Invalid relation type:%s' % kwargs['type'])

        # ensure isHostedBy and isCopiedFrom are mutually exclusive
        metadata_obj = kwargs['content_object']
        metadata_type = ContentType.objects.get_for_model(metadata_obj)

        # avoid creating duplicate element (same type and same value)
        if cls.objects.filter(type=kwargs['type'],
                              value=kwargs['value'],
                              object_id=metadata_obj.id,
                              content_type=metadata_type).exists():
            raise ValidationError('Relation element of the same type '
                                  'and value already exists.')

        return super(AbstractRelation, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        """Define custom update method for Relation class."""
        if 'type' not in kwargs:
            ValidationError("Type of relation element is missing.")
        if 'value' not in kwargs:
            ValidationError("Value of relation element is missing.")

        if not kwargs['type'] in list(dict(cls.SOURCE_TYPES).keys()):
            raise ValidationError('Invalid relation type:%s' % kwargs['type'])

        # avoid changing this relation to an existing relation of same type and same value
        rel = cls.objects.get(id=element_id)
        metadata_obj = kwargs['content_object']
        metadata_type = ContentType.objects.get_for_model(metadata_obj)
        qs = cls.objects.filter(type=kwargs['type'],
                                value=kwargs['value'],
                                object_id=metadata_obj.id,
                                content_type=metadata_type)

        if qs.exists() and qs.first() != rel:
            # this update will create a duplicate relation element
            raise ValidationError('A relation element of the same type and value already exists.')

        super(AbstractRelation, cls).update(element_id, **kwargs)

    class Meta:
        abstract = True


@rdf_terms(DC.relation)
class Relation(AbstractRelation):
    """Define Relation custom metadata model."""

    SOURCE_TYPES = (
        (RelationTypes.isPartOf.value, 'The content of this resource is part of'),
        (RelationTypes.hasPart.value, 'This resource includes'),
        (RelationTypes.isExecutedBy.value, 'The content of this resource can be executed by'),
        (RelationTypes.isCreatedBy.value,
         'The content of this resource was created by a related App or software program'),
        (RelationTypes.isVersionOf.value, 'This resource updates and replaces a previous version'),
        (RelationTypes.isReplacedBy.value, 'This resource has been replaced by a newer version'),
        (RelationTypes.isDescribedBy.value, 'This resource is described by'),
        (RelationTypes.conformsTo.value, 'This resource conforms to established standard described by'),
        (RelationTypes.hasFormat.value, 'This resource has a related resource in another format'),
        (RelationTypes.isFormatOf.value, 'This resource is a different format of'),
        (RelationTypes.isRequiredBy.value, 'This resource is required by'),
        (RelationTypes.requires.value, 'This resource requires'),
        (RelationTypes.isReferencedBy.value, 'This resource is referenced by'),
        (RelationTypes.references.value, 'The content of this resource references'),
        (RelationTypes.replaces.value, 'This resource replaces'),
        (RelationTypes.source.value, 'The content of this resource is derived from'),
        (RelationTypes.isSimilarTo.value, 'The content of this resource is similar to')
    )

    # these are hydroshare custom terms that are not Dublin Core terms
    HS_RELATION_TERMS = (RelationTypes.isExecutedBy, RelationTypes.isCreatedBy, RelationTypes.isDescribedBy,
                         RelationTypes.isSimilarTo)
    NOT_USER_EDITABLE = (RelationTypes.isVersionOf, RelationTypes.isReplacedBy,
                         RelationTypes.isPartOf, RelationTypes.hasPart, RelationTypes.replaces)
    term = 'Relation'
    type = models.CharField(max_length=100, choices=SOURCE_TYPES)
    value = models.TextField()

    @classmethod
    def create(cls, **kwargs):
        return super(Relation, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        return super(Relation, cls).update(element_id, **kwargs)

    def rdf_triples(self, subject, graph):
        relation_node = BNode()
        graph.add((subject, self.get_class_term(), relation_node))
        if self.type in self.HS_RELATION_TERMS:
            graph.add((relation_node, getattr(HSTERMS, self.type), Literal(self.value)))
        else:
            graph.add((relation_node, getattr(DCTERMS, self.type), Literal(self.value)))

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        for _, _, relation_node in graph.triples((subject, cls.get_class_term(), None)):
            for _, p, o in graph.triples((relation_node, None, None)):
                type_term = p
                value = o
                break
            if type_term:
                type = type_term.split('/')[-1]
                value = str(value)
                Relation.create(type=type, value=value, content_object=content_object)


@rdf_terms(HSTERMS.geospatialRelation, text=HSTERMS.relation_name)
class GeospatialRelation(AbstractRelation):

    SOURCE_TYPES = (
        (RelationTypes.relation.value, 'The content of this resource is related to'),
    )

    term = 'GeospatialRelation'
    type = models.CharField(max_length=100, choices=SOURCE_TYPES)
    value = models.TextField()
    text = models.TextField(max_length=100)

    @classmethod
    def create(cls, **kwargs):
        return super(GeospatialRelation, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        return super(GeospatialRelation, cls).update(element_id, **kwargs)

    def rdf_triples(self, subject, graph):
        relation_node = BNode()
        graph.add((subject, self.get_class_term(), relation_node))
        graph.add((relation_node, getattr(DCTERMS, self.type), URIRef(self.value)))
        graph.add((relation_node, self.get_field_term("text"), Literal(self.text)))

    def update_from_geoconnex_response(self, json_response):
        relative_id = self.value.split("ref/").pop()
        contexts = json_response['@context']
        for context in contexts:
            compacted = jsonld.compact(json_response, context)
            try:
                name = compacted['schema:name']
            except KeyError:
                continue
            text = f"{name} [{relative_id}]"
            if self.text != text:
                self.text = text
                self.save()

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        for _, _, relation_node in graph.triples((subject, cls.get_class_term(), None)):
            type = value = name = None
            for _, p, o in graph.triples((relation_node, None, None)):
                if p == cls.get_field_term("text"):
                    name = o
                else:
                    type = p.split('/')[-1]
                    value = str(o)
            if name and value and type:
                GeospatialRelation.create(type=type, value=value, text=name, content_object=content_object)


@rdf_terms(DC.identifier)
class Identifier(AbstractMetaDataElement):
    """Create Identifier custom metadata element."""

    term = 'Identifier'
    name = models.CharField(max_length=100)
    url = models.URLField(unique=True)

    def __unicode__(self):
        """Return {name} {url} for unicode representation."""
        return "{name} {url}".format(name=self.name, url=self.url)

    def rdf_triples(self, subject, graph):
        identifier_node = BNode()
        graph.add((subject, self.get_class_term(), identifier_node))
        if self.name.lower() == 'doi':
            graph.add((identifier_node, HSTERMS.doi, URIRef(self.url)))
        else:
            graph.add((identifier_node, HSTERMS.hydroShareIdentifier, URIRef(self.url)))

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        for _, _, identifier_node in graph.triples((subject, cls.get_class_term(), None)):
            url = graph.value(subject=identifier_node, predicate=HSTERMS.doi)
            name = 'doi'
            if not url:
                name = 'hydroShareIdentifier'
                url = graph.value(subject=identifier_node, predicate=HSTERMS.hydroShareIdentifier)
                if url:
                    # overwrite hydroShareIdentifier url with this resource's url
                    url = content_object.rdf_subject()
            if url:
                Identifier.create(url=str(url), name=name, content_object=content_object)

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


@rdf_terms(DC.publisher, name=HSTERMS.publisherName, url=HSTERMS.publisherURL)
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
        if not resource:
            raise ValidationError("Resource not found")
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
            # that has no content files, unless it is a Collection
            if resource.resource_type.lower() != "collectionresource":
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


@rdf_terms(DC.language)
class Language(AbstractMetaDataElement):
    """Define language custom metadata model."""

    term = 'Language'
    code = models.CharField(max_length=7, choices=iso_languages)

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

    def rdf_triples(self, subject, graph):
        graph.add((subject, self.get_class_term(), Literal(self.code)))

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        code = graph.value(subject=subject, predicate=cls.get_class_term())
        if code:
            Language.create(code=str(code), content_object=content_object)


@rdf_terms(DC.coverage)
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

            if not kwargs['type'] in list(dict(cls.COVERAGE_TYPES).keys()):
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
                    value_dict = {k: v for k, v in list(value_arg_dict.items())
                                  if k in ('name', 'start', 'end')}
                elif kwargs['type'] == 'point':
                    value_dict = {k: v for k, v in list(value_arg_dict.items())
                                  if k in ('name', 'east', 'north', 'units', 'elevation',
                                           'zunits', 'projection')}
                elif kwargs['type'] == 'box':
                    value_dict = {k: v for k, v in list(value_arg_dict.items())
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
    def ingest_rdf(cls, graph, subject, content_object):
        for _, _, cov in graph.triples((subject, cls.get_class_term(), None)):
            type = graph.value(subject=cov, predicate=RDF.type)
            value = graph.value(subject=cov, predicate=RDF.value)
            type = type.split('/')[-1]
            value_dict = {}
            for key_value in value.split(";"):
                key_value = key_value.strip()
                k, v = key_value.split("=")
                if k in ['start', 'end']:
                    v = parser.parse(v).strftime("%Y/%m/%d %H:%M:%S")
                value_dict[k] = v
            Coverage.create(type=type, value=value_dict, content_object=content_object)

    def rdf_triples(self, subject, graph):
        coverage = BNode()
        graph.add((subject, self.get_class_term(), coverage))
        DCTERMS_type = getattr(DCTERMS, self.type)
        graph.add((coverage, RDF.type, DCTERMS_type))
        value_dict = {}
        for k, v in self.value.items():
            if k in ['start', 'end']:
                v = parser.parse(v).isoformat()
            value_dict[k] = v
        value_string = "; ".join(["=".join([key, str(val)]) for key, val in value_dict.items()])
        graph.add((coverage, RDF.value, Literal(value_string)))

    @classmethod
    def validate_coverage_type_value_attributes(cls, coverage_type, value_dict, use_limit_postfix=True):
        """Validate values based on coverage type."""
        def compute_longitude(key_name):
            if value_dict[key_name] <= -180 and value_dict[key_name] >= -360:
                value_dict[key_name] = value_dict[key_name] + 360
            elif value_dict[key_name] >= 180 and value_dict[key_name] <= 360:
                value_dict[key_name] = value_dict[key_name] - 360
            if value_dict[key_name] < -180 or value_dict[key_name] > 180:
                err_msg = "Invalid value for {}:{}. Value for {} longitude should be in the range of -180 to 180"
                err_msg = err_msg.format(key_name, value_dict[key_name], key_name)
                raise ValidationError(err_msg)

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

            compute_longitude(key_name='east')
            if value_dict['north'] < -90 or value_dict['north'] > 90:
                raise ValidationError("Value for North latitude should be "
                                      "in the range of -90 to 90")

        elif coverage_type == 'box':
            # check that all the required sub-elements exist
            box_key_names = {'north': 'north', 'east': 'east', 'south': 'south', 'west': 'west'}
            if use_limit_postfix:
                for key, value in box_key_names.items():
                    box_key_names[key] = f"{value}limit"
            required_keys = list(box_key_names.values()) + ['units']
            for value_item in required_keys:
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

            if value_dict[box_key_names['north']] < -90 or value_dict[box_key_names['north']] > 90:
                raise ValidationError("Value for North latitude should be "
                                      "in the range of -90 to 90")

            if value_dict[box_key_names['south']] < -90 or value_dict[box_key_names['south']] > 90:
                raise ValidationError("Value for South latitude should be "
                                      "in the range of -90 to 90")

            if (value_dict[box_key_names['north']] < 0 and value_dict[box_key_names['south']] < 0) or (
                    value_dict[box_key_names['north']] > 0 and value_dict[box_key_names['south']] > 0):
                if value_dict[box_key_names['north']] < value_dict[box_key_names['south']]:
                    raise ValidationError("Value for North latitude must be greater than or "
                                          "equal to that of South latitude.")

            compute_longitude(key_name=box_key_names['east'])
            compute_longitude(key_name=box_key_names['west'])

    def get_html(self, pretty=True):
        """Use the dominate module to generate element display HTML.

        This function should be used for displaying one spatial coverage element
        or one temporal coverage element
        """
        root_div = div(cls='content-block')

        def get_th(heading_name):
            return th(heading_name, cls="text-muted")

        with root_div:
            if self.type == 'box' or self.type == 'point':
                legend('Spatial Coverage')
                div('Coordinate Reference System', cls='text-muted')
                div(self.value['projection'])
                div('Coordinate Reference System Unit', cls='text-muted has-space-top')
                div(self.value['units'])
                h4('Extent', cls='space-top')
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


@rdf_terms(HSTERMS.awardInfo, agency_name=HSTERMS.fundingAgencyName, award_title=HSTERMS.awardTitle,
           award_number=HSTERMS.awardNumber, agency_url=HSTERMS.fundingAgencyURL)
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


@rdf_terms(DC.subject)
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

    def rdf_triples(self, subject, graph):
        graph.add((subject, self.get_class_term(), Literal(self.value)))

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        for _, _, o in graph.triples((subject, cls.get_class_term(), None)):
            Subject.create(value=str(o), content_object=content_object)


@rdf_terms(DC.rights, statement=HSTERMS.rightsStatement, url=HSTERMS.URL)
class Rights(AbstractMetaDataElement):
    """Define Rights custom metadata element model."""

    term = 'Rights'
    statement = models.TextField()
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
    last_changed_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                        help_text='The person who last changed the resource',
                                        related_name='last_changed_%(app_label)s_%(class)s',
                                        null=False,
                                        default=1
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

    short_id = models.CharField(max_length=32, default=short_id, db_index=True)
    doi = models.CharField(max_length=128, null=False, blank=True, db_index=True, default='',
                           help_text='Permanent identifier. Never changes once it\'s been set.')
    comments = CommentsField()
    rating = RatingField()

    # this is to establish a relationship between a resource and
    # any metadata container object (e.g., CoreMetaData object)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # key/value metadata (additional metadata)
    extra_metadata = HStoreField(default=dict)

    # this field is for resources to store extra key:value pairs as needed, e.g., bag checksum is stored as
    # "bag_checksum":value pair for published resources in order to meet the DataONE data distribution needs
    # for internal use only
    # this field WILL NOT get recorded in bag and SHOULD NEVER be used for storing metadata
    extra_data = HStoreField(default=dict)

    # for tracking number of times resource and its files have been downloaded
    download_count = models.PositiveIntegerField(default=0)
    bag_last_downloaded = models.DateTimeField(null=True, blank=True)
    # for tracking number of times resource has been viewed
    view_count = models.PositiveIntegerField(default=0)

    # for tracking when resourceFiles were last compared with irods
    files_checked = models.DateTimeField(null=True)
    repaired = models.DateTimeField(null=True)

    # allow resource that contains spam_patterns to be discoverable/public
    spam_allowlisted = models.BooleanField(default=False)

    quota_holder = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='quota_holder')

    def update_view_count(self):
        self.view_count += 1
        # using update query api to update instead of self.save() to avoid triggering solr realtime indexing
        type(self).objects.filter(id=self.id).update(view_count=self.view_count)

    def update_download_count(self):
        self.download_count += 1
        # using update query api to update instead of self.save() to avoid triggering solr realtime indexing
        type(self).objects.filter(id=self.id).update(download_count=self.download_count)

    # definition of resource logic
    @property
    def supports_folders(self):
        """Return whether folder operations are supported. Computed for polymorphic types."""
        return False

    @property
    def last_updated(self):
        """Return the last updated date stored in metadata"""
        for dt in self.metadata.dates.all():
            if dt.type == 'modified':
                return dt.start_date

    @property
    def has_required_metadata(self):
        """Return True only if all required metadata is present."""
        if self.metadata is None or not self.metadata.has_all_required_elements():
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
        if not has_files:
            return False

        has_metadata = self.has_required_metadata
        return has_metadata

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
            self.update_index()

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
        from hs_core.signals import post_raccess_change
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
            post_raccess_change.send(sender=self, resource=self)
            self.update_index()
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
                if self.resource_type == 'CompositeResource' and \
                        self.get_logical_files('NetCDFLogicalFile'):
                    is_netcdf_to_public = True

                if value and settings.RUN_HYRAX_UPDATE and is_netcdf_to_public:
                    run_script_to_update_hyrax_input_files(self.short_id)

    def set_published(self, value):
        """Set the published flag for a resource.

        :param value: True or False

        This sets the published flag (self.raccess.published)
        """
        from hs_core.signals import post_raccess_change

        self.raccess.published = value
        self.raccess.immutable = value
        if value:  # can't be published without being public
            self.raccess.public = value
        self.raccess.save()
        post_raccess_change.send(sender=self, resource=self)
        self.update_index()

    def update_index(self):
        """updates previous versions of a resource (self) in index"""
        prev_version_resource_relation_meta = Relation.objects.filter(type='isReplacedBy',
                                                                      value__contains=self.short_id).first()
        if prev_version_resource_relation_meta:
            prev_version_res = prev_version_resource_relation_meta.metadata.resource
            if prev_version_res.raccess.discoverable or prev_version_res.raccess.public:
                # saving to trigger index update for this previous version of resource
                prev_version_res.save()
            prev_version_res.update_index()

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

    def set_private_sharing_link(self, user, value):
        """Set resource 'allow_private_sharing' flag to True or False.
        If allow_private_sharing is True then any user including anonymous user will be able to use the resource url
        to view the resource (view mode).

        :param user: user requesting the change
        :param value: True or False
        :raises PermissionDenied: if the user lacks permission to change resource flag
        """
        if not user.uaccess.can_change_resource_flags(self):
            raise PermissionDenied("You don't have permission to change resource private link sharing "
                                   " status")
        self.raccess.allow_private_sharing = value
        self.raccess.save()

    def update_public_and_discoverable(self):
        """Update the settings of the public and discoverable flags for changes in metadata."""
        if self.raccess.discoverable and not self.can_be_public_or_discoverable:
            self.set_discoverable(False)  # also sets Public

    @property
    def absolute_url(self):
        return self.get_url_of_path('')

    def get_url_of_path(self, path):
        """Return the URL of an arbitrary path in this resource.

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
        url_encoded_path = urllib.parse.quote(path)
        return '/' + os.path.join('resource', self.short_id, url_encoded_path)

    def get_irods_path(self, path, prepend_short_id=True):
        """Return the irods path by which the given path is accessed.
           The input path includes data/contents/ as needed.
        """
        if prepend_short_id and not path.startswith(self.short_id):
            full_path = os.path.join(self.short_id, path)
        else:
            full_path = path

        return full_path

    def set_quota_holder(self, setter, new_holder):
        """Set quota holder of the resource to new_holder who must be an owner.

        setter is the requesting user to transfer quota holder and setter must also be an owner
        """
        from hs_core.hydroshare.utils import validate_user_quota

        if __debug__:
            assert (isinstance(setter, User))
            assert (isinstance(new_holder, User))
        if not setter.uaccess.owns_resource(self) or \
                not new_holder.uaccess.owns_resource(self):
            raise PermissionDenied("Only owners can set or be set as quota holder for the resource")

        # QuotaException will be raised if new_holder does not have enough quota to hold this
        # new resource, in which case, set_quota_holder to the new user fails
        validate_user_quota(new_holder, self.size)
        self.quota_holder = new_holder
        self.save()

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

    def delete(self, using=None, keep_parents=False):
        """Delete resource along with all of its metadata and data bag."""
        from .hydroshare import hs_bagit
        for fl in self.files.all():
            # COUCH: delete of file objects now cascades.
            fl.delete(delete_logical_file=True)
        self.metadata.delete()
        hs_bagit.delete_files_and_bag(self)
        super(AbstractResource, self).delete()

    @property
    def metadata(self):
        """Return the metadata object for this resource."""
        return self.content_object

    @classmethod
    def get_metadata_class(cls):
        return CoreMetaData

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

    def is_schema_json_file(self, file_path):
        """Determine whether a given file is a schema.json file.
        Note: this will return true for any file that ends with the schema.json ending
        We are taking the risk that user might create a file with the same filename ending
        """
        from hs_file_types.enums import AggregationMetaFilePath

        if file_path.endswith(AggregationMetaFilePath.SCHEMA_JSON_FILE_ENDSWITH):
            return True
        return False

    def is_collection_list_csv(self, file_path):
        """Determine if a given file is an internally-generated collection list
        """
        from hs_collection_resource.utils import CSV_FULL_NAME_TEMPLATE
        collection_list_filename = CSV_FULL_NAME_TEMPLATE.format(self.short_id)
        if collection_list_filename in file_path:
            return True
        return False

    def is_metadata_xml_file(self, file_path):
        """Determine whether a given file is metadata.
        Note: this will return true for any file that ends with the metadata endings
        We are taking the risk that user might create a file with the same filename ending
        """
        from hs_file_types.enums import AggregationMetaFilePath

        if not (file_path.endswith(AggregationMetaFilePath.METADATA_FILE_ENDSWITH)
                or file_path.endswith(AggregationMetaFilePath.RESMAP_FILE_ENDSWITH)):
            return False
        return True

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
            initials = ". ".join(initials_list) + "."
            if first_author:
                author_name = "{last_name}, {initials}"
            else:
                author_name = "{initials} {last_name}"
            author_name = author_name.format(last_name=last_names,
                                             initials=initials
                                             )
        else:
            author_name = "{last_name}".format(last_name=last_names)

        return author_name + ", "

    def get_custom_citation(self):
        """Get custom citation."""
        if self.metadata.citation.first() is None:
            return ''
        return str(self.metadata.citation.first())

    def get_citation(self, forceHydroshareURI=True):
        """Get citation or citations from resource metadata."""

        citation_str_lst = []

        CITATION_ERROR = "Failed to generate citation."

        creators = self.metadata.creators.all()
        first_author = [cr for cr in creators if cr.order == 1][0]
        if first_author.organization and not first_author.name:
            citation_str_lst.append(first_author.organization + ", ")
        else:
            citation_str_lst.append(self.parse_citation_name(first_author.name, first_author=True))

        other_authors = [cr for cr in creators if cr.order > 1]
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

        meta_dates = self.metadata.dates.all()
        published_date = [dt for dt in meta_dates if dt.type == "published"]
        citation_date = None
        if published_date:
            citation_date = published_date[0]
        else:
            modified_date = [dt for dt in meta_dates if dt.type == "modified"]
            if modified_date:
                citation_date = modified_date[0]

        if citation_date is None:
            return CITATION_ERROR

        citation_str_lst.append(" ({year}). ".format(year=citation_date.start_date.year))
        citation_str_lst.append(self.metadata.title.value)

        isPendingActivation = False
        identifiers = self.metadata.identifiers.all()
        doi = [idn for idn in identifiers if idn.name == "doi"]

        if doi and not forceHydroshareURI:
            hs_identifier = doi[0]
            if (self.doi.find(CrossRefSubmissionStatus.PENDING) >= 0
                    or self.doi.find(CrossRefSubmissionStatus.FAILURE) >= 0):
                isPendingActivation = True
        else:
            hs_identifier = [idn for idn in identifiers if idn.name == "hydroShareIdentifier"]
            if hs_identifier:
                hs_identifier = hs_identifier[0]
            else:
                return CITATION_ERROR

        citation_str_lst.append(", HydroShare, {url}".format(url=hs_identifier.url))

        if isPendingActivation and not forceHydroshareURI:
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
    def readme_file(self):
        """Returns a resource file that is at the root with a file name of either
        'readme.txt' or 'readme.md' (filename is case insensitive). If no such file then None
        is returned. If both files exist then resource file for readme.md is returned"""

        if self.files.filter(file_folder='').count() == 0:
            # no files exist at the root of the resource path - no need to check for readme file
            return None

        file_path_md = os.path.join(self.file_path, 'readme.md')
        file_path_txt = os.path.join(self.file_path, 'readme.txt')
        readme_res_file = self.files.filter(resource_file__iexact=file_path_md).first()
        if readme_res_file is None:
            readme_res_file = self.files.filter(resource_file__iexact=file_path_txt).first()

        return readme_res_file

    def get_readme_file_content(self):
        """Gets the content of the readme file. If both a readme.md and a readme.txt file exist,
        then the content of the readme.md file is returned, otherwise None

        Note: The user uploaded readme file if originally not encoded as utf-8, then any non-ascii
        characters in the file will be escaped when we return the file content.
        """
        readme_file = self.readme_file
        # check the file exists on irods

        if readme_file is None:
            return readme_file

        # check the file exists on irods
        if readme_file.exists:
            readme_file_content = readme_file.read().decode('utf-8', 'ignore')
            if readme_file.extension.lower() == '.md':
                markdown_file_content = markdown(readme_file_content)
                return {'content': markdown_file_content,
                        'file_name': readme_file.file_name, 'file_type': 'md'}
            else:
                return {'content': readme_file_content, 'file_name': readme_file.file_name}
        else:
            file_name = readme_file.file_name
            readme_file.delete()
            logger = logging.getLogger(__name__)
            log_msg = f"readme file ({file_name}) is missing on iRODS. Deleting the file from Django."
            logger.warning(log_msg)
            return None

    @property
    def logical_files(self):
        """Gets a generator to access each of the logical files of the resource.
        Note: Any derived class that supports logical file must override this function
        """

        # empty generator
        yield from ()

    @property
    def aggregation_types(self):
        """Gets a list of all aggregation types that currently exist in this resource
        Note: Any derived class that supports logical file must override this function
        """
        return []

    def get_logical_files(self, logical_file_class_name):
        """Get a list of logical files (aggregations) for a specified logical file class name.
        Note: Any derived class that supports logical file must override this function
        """
        return []

    @property
    def has_logical_spatial_coverage(self):
        """Checks if any of the logical files has spatial coverage
        Note: Any derived class that supports logical file must override this function
        """

        return False

    @property
    def has_logical_temporal_coverage(self):
        """Checks if any of the logical files has temporal coverage
        Note: Any derived class that supports logical file must override this function
        """

        return False

    @property
    def supports_logical_file(self):
        """Check if resource allows associating resource file objects with logical file."""
        return False

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
        return 'local'

    def is_folder(self, folder_path):
        """Determine whether a given path (relative to resource root, including /data/contents/)
           is a folder or not. Returns False if the path does not exist.
        """
        path_split = folder_path.split('/')
        while path_split[-1] == '':
            path_split.pop()
        dir_path = '/'.join(path_split[0:-1])

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


def get_path(instance, filename, folder=''):
    """Get a path from a ResourceFile, filename, and folder.

    :param instance: instance of ResourceFile to use
    :param filename: file name to use (without folder)
    :param folder: can override folder for ResourceFile instance

    The filename is only a single name. This routine converts it to an absolute
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
def get_resource_file_path(resource, filename, folder=''):
    """Determine storage path for a FileField

    :param resource: resource containing the file.
    :param filename: name of file without folder.
    :param folder: folder of file

    The filename is only a single name. This routine converts it to an absolute
    to do this.

    """
    # folder can be absolute pathname; strip qualifications off of folder if necessary
    # cannot only test folder string to start with resource.root_path, since a relative folder path
    # may start with the resource's uuid if the same resource bag is added into the same resource and unzipped
    # into the resource as in the bug reported in this issue: https://github.com/hydroshare/hydroshare/issues/2984

    res_data_content_path = os.path.join(resource.root_path, 'data', 'contents')
    if folder is not None and folder.startswith(res_data_content_path):
        # TODO: does this now start with /?
        # check if the folder is a path relative to the resource data content path, if yes, no need to strip out
        # resource.root_path
        istorage = resource.get_irods_storage()
        if not istorage.exists(os.path.join(res_data_content_path, folder)):
            # folder is not a path relative to res_data_content_path, but a path including resource root path,
            # strip out resource root path to make folder a relative path
            folder = folder[len(resource.root_path):]

    # retrieve federation path -- if any -- from Resource object containing the file
    if filename.startswith(resource.file_path):
        return filename

    # otherwise, it is an unqualified name.
    if folder:
        # use subfolder
        folder = folder.strip('/')
        return os.path.join(resource.file_path, folder, filename)

    else:
        # use root folder
        filename = filename.strip('/')
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
                          ]
    # A ResourceFile is a sub-object of a resource, which can have several types.
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    content_object = GenericForeignKey('content_type', 'object_id')

    # This is used to direct uploads to a subfolder of the root folder for the resource.
    # See get_path and get_resource_file_path above.
    file_folder = models.CharField(max_length=4096, null=False, default="")

    # This pair of FileFields deals with the fact that there are two kinds of storage
    resource_file = models.FileField(upload_to=get_path, max_length=4096, unique=True,
                                     storage=IrodsStorage())

    # we are using GenericForeignKey to allow resource file to be associated with any
    # HydroShare defined LogicalFile types (e.g., GeoRasterFile, NetCdfFile etc)
    logical_file_object_id = models.PositiveIntegerField(null=True, blank=True)
    logical_file_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE,
                                                  null=True, blank=True,
                                                  related_name="files")
    logical_file_content_object = GenericForeignKey('logical_file_content_type',
                                                    'logical_file_object_id')

    # these file metadata (size, modified_time, and checksum) values are retrieved from iRODS and stored in db
    # for performance reason so that we don't have to query iRODS for these values every time we need them
    _size = models.BigIntegerField(default=-1)
    _modified_time = models.DateTimeField(null=True, blank=True)
    _checksum = models.CharField(max_length=255, null=True, blank=True)

    # for tracking when size was last compared with irods
    filesize_cache_updated = models.DateTimeField(null=True)

    def __str__(self):
        return self.resource_file.name

    @classmethod
    def banned_symbols(cls):
        """returns a list of banned characters for file/folder name"""
        return r'\/:*?"<>|'

    @classmethod
    def system_meta_fields(cls):
        """returns a list of system metadata fields"""
        return ['_size', '_modified_time', '_checksum', 'filesize_cache_updated']

    @classmethod
    def create(cls, resource, file, folder='', source=None):
        """Create custom create method for ResourceFile model.

        Create takes arguments that are invariant of storage medium.
        These are turned into a path that is suitable for the medium.
        Federation must be initialized first at the resource level.

        :param resource: resource that contains the file.
        :param file: a File or a iRODS path to an existing file already copied.
        :param folder: the folder in which to store the file.
        :param source: an iRODS path in the same zone from which to copy the file.

        There are two main usages to this constructor:

        * uploading a file from a form or REST call:

                ResourceFile.create(r, File(...something...), folder=d)

        * copying a file internally from iRODS:

                ResourceFile.create(r, file_name, folder=d, source=s)

        In this case, source is a full iRODS pathname of the place from which to copy
        the file.

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
            filename = os.path.basename(file.name)
            if not ResourceFile.is_filename_valid(filename):
                raise SuspiciousFileOperation("Filename is not compliant with Hydroshare requirements")

            kwargs['resource_file'] = file

        else:  # if file is not an open file, then it's a basename (string)
            if file is None and source is not None:
                if __debug__:
                    assert (isinstance(source, str))
                # source is a path to an iRODS file to be copied here.
                root, newfile = os.path.split(source)  # take file from source path
                # newfile is where it should be copied to.
                target = get_resource_file_path(resource, newfile, folder=folder)
                istorage = resource.get_irods_storage()
                if not istorage.exists(source):
                    raise ValidationError("ResourceFile.create: source {} of copy not found"
                                          .format(source))
                istorage.copyFiles(source, target)
                if not istorage.exists(target):
                    raise ValidationError("ResourceFile.create: copy to target {} failed"
                                          .format(target))
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
            kwargs['resource_file'] = target

        # Actually create the file record
        # when file is a File, the file is copied to storage in this step
        # otherwise, the copy must precede this step.

        return ResourceFile.objects.create(**kwargs)

    # TODO: automagically handle orphaned logical files
    def delete(self, delete_logical_file=False):
        """Delete a resource file record and the file contents.
        :param  delete_logical_file: if True deletes logical file associated with resource file

        model.delete does not cascade to delete files themselves,
        and these must be explicitly deleted.
        """
        if self.exists:
            if delete_logical_file and self.logical_file is not None:
                # deleting logical file metadata deletes the logical file as well
                self.logical_file.metadata.delete()
            if self.resource_file:
                self.resource_file.delete()
        super(ResourceFile, self).delete()

    @property
    def resource(self):
        """Return content_object representing the resource from a resource file."""
        return self.content_object

    @property
    def size(self):
        """Return file size of the file.
        Calculates the size first if it has not been calculated yet."""
        if self._size < 0:
            self.calculate_size()
        return self._size

    @property
    def modified_time(self):
        """Return modified time of the file.
        If the modified time is not already set, then it is first retrieved from iRODS and stored in db.
        """
        # self._size != 0 -> file exists, or we have not set the size yet
        if not self._modified_time and self._size != 0:
            self.calculate_modified_time()
        return self._modified_time

    def calculate_modified_time(self, resource=None, save=True):
        """Updates modified time of the file in db.
        Retrieves the modified time from iRODS and stores it in db.
        """
        if resource is None:
            resource = self.resource

        file_path = self.resource_file.name

        try:
            self._modified_time = self.resource_file.storage.get_modified_time(file_path)
        except (SessionException, ValidationError):
            logger = logging.getLogger(__name__)
            logger.warning("file {} not found in iRODS".format(self.storage_path))
            self._modified_time = None
        if save:
            self.save(update_fields=["_modified_time"])

    @property
    def checksum(self):
        """Return checksum of the file.
        If the checksum is not already set, then it is first retrieved from iRODS and stored in db.
        """
        # self._size != 0 -> file exists, or we have not set the size yet
        if not self._checksum and self._size != 0:
            self.calculate_checksum()
        return self._checksum

    def calculate_checksum(self, resource=None, save=True):
        """Updates checksum of the file in db.
        Retrieves the checksum from iRODS and stores it in db.
        """
        if resource is None:
            resource = self.resource

        file_path = self.resource_file.name

        try:
            self._checksum = self.resource_file.storage.checksum(file_path, force_compute=False)
        except (SessionException, ValidationError):
            logger = logging.getLogger(__name__)
            logger.warning("file {} not found in iRODS".format(self.storage_path))
            self._checksum = None
        if save:
            self.save(update_fields=["_checksum"])

    # TODO: write unit test
    @property
    def exists(self):
        istorage = self.resource.get_irods_storage()
        return istorage.exists(self.resource_file.name)

    # TODO: write unit test
    def read(self):
        return self.resource_file.read()

    @property
    def storage_path(self):
        """Return the qualified name for a file in the storage hierarchy.

        This is a valid input to IrodsStorage for manipulating the file.
        The output depends upon whether the IrodsStorage instance is running

        """
        # instance.content_object can be stale after changes.
        # Re-fetch based upon key; bypass type system; it is not relevant
        resource = self.resource
        return self.get_storage_path(resource)

    def get_storage_path(self, resource):
        """Return the qualified name for a file in the storage hierarchy.
        Note: This is the preferred way to get the storage path for a file when we are trying to find
        the storage path for more than one file in a resource.
        """
        return self.resource_file.name

    def calculate_size(self, resource=None, save=True):
        """Reads the file size and saves to the DB"""
        if resource is None:
            resource = self.resource

        try:
            self._size = self.resource_file.size
            self.filesize_cache_updated = now()
        except (SessionException, ValidationError):
            logger = logging.getLogger(__name__)
            logger.warning("file {} not found in iRODS".format(self.storage_path))
            self._size = 0
        if save:
            self.save(update_fields=["_size", "filesize_cache_updated"])

    def set_system_metadata(self, resource=None, save=True):
        """Set system metadata (size, modified time, and checksum) for a file.
        This method should be called after a file is uploaded to iRODS and registered with Django.
        """

        self.calculate_size(resource=resource, save=save)
        if self._size > 0:
            # file exists in iRODS - get modified time and checksum
            self.calculate_modified_time(resource=resource, save=save)
            self.calculate_checksum(resource=resource, save=save)
        else:
            # file was not found in iRODS
            self._size = 0
            self._modified_time = None
            self._checksum = None
        if save:
            self.save(update_fields=self.system_meta_fields())

    # ResourceFile API handles file operations
    def set_storage_path(self, path, test_exists=True):
        """Bind this ResourceFile instance to an existing file.

        :param path: the path of the object.
        :param test_exists: if True, test for path existence in iRODS

        Path can be absolute or relative.

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

        # switch FileFields based upon federation path
        self.resource_file = get_path(self, base)
        self.save()

    @property
    def short_path(self):
        """Return the unqualified path to the file object.

        * This path is invariant of where the object is stored.

        * Thus, it does not change if the resource is moved.

        This is the path that should be used as a key to index things such as file type.
        """

        # use of self.resource generates a query
        return self.get_short_path(self.resource)

    def get_short_path(self, resource):
        """Return the unqualified path to the file object.

        * This path is invariant of where the object is stored.

        * Thus, it does not change if the resource is moved.

        This is the path that should be used as a key to index things such as file type.
        :param resource: the resource to which the file (self) belongs
        Note: This is the preferred way to get the short path for a file when we are trying to find short path
        for more than one file in a resource.
        """
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
        self.file_folder = folder  # must precede call to get_path

        self.resource_file = get_path(self, base)
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
        if path.startswith(locpath):
            # strip optional local path prefix
            if test_exists and not storage.exists(path):
                raise ValidationError("Local path ({}) does not exist in irods".format(path))
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
            folder = ''
            base = relpath
            abspath = get_resource_file_path(resource, base, folder=folder)
            if test_exists and not storage.exists(abspath):
                raise ValidationError("Local path does not exist in irods")

        return folder, base

    # classmethods do things that query or affect all files.

    @classmethod
    def check_for_preferred_name(cls, file_folder_name):
        """Checks if the file or folder name meets the preferred name requirements"""

        # remove anything that is not an alphanumeric, dash, underscore, or dot
        sanitized_name = re.sub(r'(?u)[^-\w.]', '', file_folder_name)

        if len(file_folder_name) != len(sanitized_name):
            # one or more symbols that are not allowed was found
            return False

        if '..' in file_folder_name:
            return False

        return True

    @classmethod
    def is_filename_valid(cls, filename):
        """Checks if the uploaded file has filename that complies to the hydroshare requirements
        :param  filename: Name of the file to check
        """
        return cls._is_folder_file_name_valid(name_to_check=filename)

    @classmethod
    def is_folder_name_valid(cls, folder_name):
        """Checks if the folder name complies to the hydroshare requirements
        :param  folder_name: Name of the folder to check
        """
        return cls._is_folder_file_name_valid(name_to_check=folder_name, file=False)

    @classmethod
    def _is_folder_file_name_valid(cls, name_to_check, file=True):
        """Helper method to check if a file/folder name is compliant with hydroshare requirements
        :param  name_to_check: Name of the file or folder to check
        :param  file: A flag to indicate if name_to_check is the filename
        """

        # space at the start or at the end is not allowed
        if len(name_to_check.strip()) != len(name_to_check):
            return False

        # check for banned symbols
        for symbol in cls.banned_symbols():
            if symbol in name_to_check:
                return False

        if name_to_check in (".", "..", "/"):
            # these represents special meaning in linux - current (.) dir, parent dir (..) and dir separator
            return False

        if not file:
            folders = name_to_check.split("/")
            for folder in folders:
                if len(folder.strip()) != len(folder):
                    return False
                if folder in (".", ".."):
                    # these represents special meaning in linux - current (.) dir and parent dir (..)
                    return False

        return True

    @classmethod
    def validate_new_path(cls, new_path):
        """Validates a new file/folder path that will be created for a resource
        :param  new_path: a file/folder path that is relative to the [res short_id]/data/contents
        """

        # strip trailing slashes (if any)
        path = str(new_path).strip().rstrip('/')
        if not path:
            raise SuspiciousFileOperation('Path cannot be empty')

        if path.startswith('/'):
            raise SuspiciousFileOperation(f"Path ({path}) must not start with '/'")

        if path in ('.', '..'):
            raise SuspiciousFileOperation(f"Path ({path}) must not be '.' or '..")

        if any(["./" in path, "../" in path, " /" in path, "/ " in path, path.endswith("/."), path.endswith("/..")]):
            raise SuspiciousFileOperation(f"Path ({path}) must not contain './', '../', '/.', or '/..'")

        return path

    @classmethod
    def get(cls, resource, file, folder=''):
        """Get a ResourceFile record via its short path."""
        resource_file_path = get_resource_file_path(resource, file, folder)
        f = ResourceFile.objects.filter(object_id=resource.id, resource_file=resource_file_path).first()
        if f:
            return f
        else:
            raise ObjectDoesNotExist(f'ResourceFile {resource_file_path} does not exist.')

    # TODO: move to BaseResource as instance method
    @classmethod
    def list_folder(cls, resource, folder, sub_folders=True):
        """List files (instances of ResourceFile) in a given folder.

        :param resource: resource for which to list the folder
        :param folder: folder listed as either short_path or fully qualified path
        :param sub_folders: if true files from sub folders of *folder* will be included in the list
        """
        file_folder_to_match = folder

        if not folder:
            folder = resource.file_path
        elif not folder.startswith(resource.file_path):
            folder = os.path.join(resource.file_path, folder)
        else:
            file_folder_to_match = folder[len(resource.file_path) + 1:]

        if sub_folders:
            # append trailing slash to match only this folder
            if not folder.endswith("/"):
                folder += "/"
            return ResourceFile.objects.filter(
                object_id=resource.id,
                resource_file__startswith=folder)
        else:
            return ResourceFile.objects.filter(
                object_id=resource.id,
                file_folder=file_folder_to_match)

    # TODO: move to BaseResource as instance method
    @classmethod
    def create_folder(cls, resource, folder, migrating_resource=False):
        """Create a folder for a resource."""
        # avoid import loop
        from hs_core.views.utils import create_folder
        path_is_allowed(folder)
        # TODO: move code from location used below to here
        create_folder(resource.short_id, os.path.join('data', 'contents', folder),
                      migrating_resource=migrating_resource)

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
        return self.logical_file_object_id is not None

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
        if self.has_logical_file:
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
        url_encoded_file_path = urllib.parse.quote(self.public_path)
        return '/' + os.path.join('resource', url_encoded_file_path)

    @property
    def public_path(self):
        """ return the public path (unqualified iRODS path) for a resource.
        """
        return os.path.join(self.resource.short_id, 'data', 'contents', self.short_path)

    @property
    def irods_path(self):
        """ Return the irods path for accessing a file, including possible federation information.
            This consists of the resource id, /data/contents/, and the file path.
        """

        return self.public_path


class RangedFileReader:
    """
    Wraps a file like object with an iterator that runs over part (or all) of
    the file defined by start and stop. Blocks of block_size will be returned
    from the starting position, up to, but not including the stop point.
    https://github.com/satchamo/django/commit/2ce75c5c4bee2a858c0214d136bfcd351fcde11d
    """
    block_size = getattr(settings, 'RANGED_FILE_READER_BLOCK_SIZE', 1024 * 1024)
    dump_size = getattr(settings, 'RANGED_FILE_READER_DUMP_SIZE', 1024 * 1024 * 1024)

    def __init__(self, file_like, start=0, stop=float("inf"), block_size=None):
        self.f = file_like
        self.block_size = block_size or self.block_size
        self.start = start
        self.stop = stop

    def __iter__(self):
        # self.f proc.stdout is an _io.BufferedReader object
        # so it will not have a seek method
        if self.f.seekable():
            self.f.seek(self.start)
        else:
            # if the file is not seekable, we read and discard
            # until we reach the start position
            remaining_to_dump = self.start
            while remaining_to_dump > 0:
                read_size = min(self.dump_size, remaining_to_dump)
                self.f.read(read_size)
                remaining_to_dump -= read_size
        position = self.start
        while position < self.stop:
            data = self.f.read(min(self.block_size, self.stop - position))
            if not data:
                break

            yield data
            position += self.block_size

    @staticmethod
    def parse_range_header(header, resource_size):
        """
        Parses a range header into a list of two-tuples (start, stop) where `start`
        is the starting byte of the range (inclusive) and `stop` is the ending byte
        position of the range (exclusive).
        Returns None if the value of the header is not syntatically valid.
        """
        if not header or '=' not in header:
            return None

        ranges = []
        units, range_ = header.split('=', 1)
        units = units.strip().lower()

        if units != "bytes":
            return None

        for val in range_.split(","):
            val = val.strip()
            if '-' not in val:
                return None

            if val.startswith("-"):
                # suffix-byte-range-spec: this form specifies the last N bytes of an
                # entity-body
                start = resource_size + int(val)
                if start < 0:
                    start = 0
                stop = resource_size
            else:
                # byte-range-spec: first-byte-pos "-" [last-byte-pos]
                start, stop = val.split("-", 1)
                start = int(start)
                # the +1 is here since we want the stopping point to be exclusive, whereas in
                # the HTTP spec, the last-byte-pos is inclusive
                stop = int(stop) + 1 if stop else resource_size
                if start >= stop:
                    return None

            ranges.append((start, stop))

        return ranges


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
            Q(raccess__discoverable=True)
            | Q(raccess__public=True))


# remove RichText parent class from the parameters for Django inplace editing to work;
# otherwise, get internal edit error when saving changes
class BaseResource(Page, AbstractResource):
    """Combine mezzanine Page model and AbstractResource model to establish base resource."""

    resource_type = models.CharField(max_length=50, default="GenericResource")
    # this locked_time field is added for resource versioning locking representing
    # the time when the resource is locked for a new version action. A value of null
    # means the resource is not locked
    locked_time = models.DateTimeField(null=True, blank=True)

    objects = PublishedManager()
    public_resources = PublicResourceManager()
    discoverable_resources = DiscoverableResourceManager()

    collections = models.ManyToManyField('BaseResource', related_name='resources')

    # used during discovery as well as in all other places in UI where resource type is displayed
    display_name = 'Generic'

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
        return IrodsStorage()

    # Paths relative to the resource
    @property
    def root_path(self):
        """Return the root folder of the iRODS structure containing resource files.

        Note that this folder doesn't directly contain the resource files;
        They are contained in ./data/contents/* instead.
        """
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

    @property
    def bag_checksum(self):
        """
        get checksum of resource bag. Currently only published resources have bag checksums computed and saved
        :return: checksum if bag checksum exists; empty string '' otherwise
        """
        extra_data = self.extra_data
        if 'bag_checksum' in extra_data and extra_data['bag_checksum']:
            return extra_data['bag_checksum'].strip('\n')
        else:
            return ''

    @bag_checksum.setter
    def bag_checksum(self, checksum):
        """
        Set bag checksum implemented as a property setter.
        :param checksum: checksum value to be set
        """
        if checksum:
            extra_data = self.extra_data
            extra_data['bag_checksum'] = checksum
            self.extra_data = extra_data
            self.save()
        else:
            return ValidationError("checksum to set on the bag of the resource {} is empty".format(self.short_id))

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
        """Return XML structure describing crossref deposit.
        The mapping of hydroshare resource metadata to crossref metadata has been implemented here as per
        the specification in this repo: https://github.com/hydroshare/hs_doi_deposit_metadata
        """
        # importing here to avoid circular import problem
        from .hydroshare.resource import get_activated_doi

        logger = logging.getLogger(__name__)

        def get_funder_id(funder_name):
            """Return funder_id for a given funder_name from Crossref funders registry.
            Crossref API Documentation: https://api.crossref.org/swagger-ui/index.html#/Funders/get_funders
            """

            # url encode the funder name for the query parameter
            words = funder_name.split()
            # filter out words that contain the char '.'
            words = [word for word in words if '.' not in word]
            encoded_words = [urllib.parse.quote(word) for word in words]
            # match all words in the funder name
            query = "+".join(encoded_words)
            # if we can't find a match in first 50 search records then we are not going to find a match
            max_record_count = 50
            email = settings.DEFAULT_DEVELOPER_EMAIL
            url = f"https://api.crossref.org/funders?query={query}&rows={max_record_count}&mailto={email}"
            funder_name = funder_name.lower()
            response = requests.get(url, verify=False)
            if response.status_code == 200:
                response_json = response.json()
                if response_json['status'] == 'ok':
                    items = response_json['message']['items']
                    for item in items:
                        if item['name'].lower() == funder_name:
                            return item['uri']
                        for alt_name in item['alt-names']:
                            if alt_name.lower() == funder_name:
                                return item['uri']
                    return ''
                return ''
            else:
                msg = "Failed to get funder_id for funder_name: '{}' from Crossref funders registry. " \
                      "Status code: {} for resource id: {}"
                msg = msg.format(funder_name, response.status_code, self.short_id)
                logger.error(msg)
                return ''

        def parse_creator_name(_creator):
            creator_name = _creator.name.strip()
            name = HumanName(creator_name)
            # both first name ane last name are required for crossref deposit
            if not name.first or not name.last:
                name_parts = creator_name.split()
                if not name.first:
                    name.first = name_parts[0]
                if not name.last:
                    name.last = name_parts[-1]
            return name.first, name.last

        def create_contributor_node(_creator, sequence="additional"):
            if _creator.name:
                first_name, last_name = parse_creator_name(_creator)
                creator_node = etree.SubElement(contributors_node, 'person_name', contributor_role="author",
                                                sequence=sequence)
                etree.SubElement(creator_node, 'given_name').text = first_name
                etree.SubElement(creator_node, 'surname').text = last_name
                orcid = _creator.identifiers.get('ORCID', "")
                if orcid:
                    etree.SubElement(creator_node, 'ORCID').text = orcid
            else:
                org = etree.SubElement(contributors_node, 'organization', contributor_role="author",
                                       sequence=sequence)
                org.text = _creator.organization

        def create_date_node(date, date_type):
            date_node = etree.SubElement(database_dates_node, date_type)
            etree.SubElement(date_node, 'month').text = str(date.month)
            etree.SubElement(date_node, 'day').text = str(date.day)
            etree.SubElement(date_node, 'year').text = str(date.year)

        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schemaLocation = 'http://www.crossref.org/schema/5.3.1 ' \
                         'http://www.crossref.org/schemas/crossref5.3.1.xsd'
        ns = "http://www.crossref.org/schema/5.3.1"
        fr = "http://www.crossref.org/fundref.xsd"
        ai = "http://www.crossref.org/AccessIndicators.xsd"
        ROOT = etree.Element('{%s}doi_batch' % ns, version="5.3.1", nsmap={None: ns, "xsi": xsi, "fr": fr, "ai": ai},
                             attrib={"{%s}schemaLocation" % xsi: schemaLocation})

        # get the resource object associated with this metadata container object - needed
        # to get the verbose_name

        # create the head sub element
        head_node = etree.SubElement(ROOT, 'head')
        etree.SubElement(head_node, 'doi_batch_id').text = self.short_id
        etree.SubElement(head_node, 'timestamp').text = arrow.now().format("YYYYMMDDHHmmss")
        depositor_node = etree.SubElement(head_node, 'depositor')
        etree.SubElement(depositor_node, 'depositor_name').text = 'HydroShare'
        etree.SubElement(depositor_node, 'email_address').text = settings.DEFAULT_SUPPORT_EMAIL
        # The organization that owns the information being registered.
        organization = 'Consortium of Universities for the Advancement of Hydrologic Science, Inc. (CUAHSI)'
        etree.SubElement(head_node, 'registrant').text = organization

        # create the body sub element
        body_node = etree.SubElement(ROOT, 'body')
        # create the database sub element
        db_node = etree.SubElement(body_node, 'database')
        # create the database_metadata sub element
        db_md_node = etree.SubElement(db_node, 'database_metadata', language="en")
        # titles is required element for database_metadata
        titles_node = etree.SubElement(db_md_node, 'titles')
        etree.SubElement(titles_node, 'title').text = "HydroShare Resources"
        # add publisher element to database_metadata
        pub_node = etree.SubElement(db_md_node, 'publisher')
        etree.SubElement(pub_node, 'publisher_name').text = "HydroShare"

        # create the dataset sub element, dataset_type can be record or collection, set it to
        # collection for HydroShare resources
        dataset_node = etree.SubElement(db_node, 'dataset', dataset_type="record")
        # create contributors sub element
        contributors_node = etree.SubElement(dataset_node, 'contributors')
        # creators are required element for contributors
        creators = self.metadata.creators.all()
        first_author = [cr for cr in creators if cr.order == 1][0]
        create_contributor_node(first_author, sequence="first")
        other_authors = [cr for cr in creators if cr.order > 1]
        for auth in other_authors:
            create_contributor_node(auth, sequence="additional")

        # create dataset title
        dataset_titles_node = etree.SubElement(dataset_node, 'titles')
        etree.SubElement(dataset_titles_node, 'title').text = self.metadata.title.value
        # create dataset date sub element
        database_dates_node = etree.SubElement(dataset_node, 'database_date')
        # create creation_date sub element
        create_date_node(date=self.created, date_type="creation_date")
        # create a publication_date sub element
        pub_date_meta = self.metadata.dates.all().filter(type='published').first()
        if pub_date_meta:
            # this is a published resource - generating crossref xml for updating crossref deposit
            pub_date = pub_date_meta.start_date
        else:
            # generating crossref xml for registering a new resource in crossref
            pub_date = self.updated

        create_date_node(date=pub_date, date_type="publication_date")
        # create update_date sub element
        create_date_node(date=self.updated, date_type="update_date")
        # create dataset description sub element
        c_abstract = clean_abstract(self.metadata.description.abstract)
        etree.SubElement(dataset_node, 'description').text = c_abstract
        # funder related elements
        funders = self.metadata.funding_agencies.all()
        if funders:
            funding_references = etree.SubElement(dataset_node, '{%s}program' % fr, name="fundref")
            for funder in funders:
                funder_group_node = etree.SubElement(funding_references, '{%s}assertion' % fr, name="fundgroup")
                funder_name_node = etree.SubElement(funder_group_node, '{%s}assertion' % fr, name="funder_name")
                funder_name_node.text = funder.agency_name
                # get funder_id from Crossref funders registry
                funder_id = get_funder_id(funder.agency_name)
                if not funder_id:
                    logger.warning(f"Funder id was not found in Crossref funder registry "
                                   f"for funder name: {funder.agency_name} for resource: {self.short_id}")
                if funder_id or funder.agency_url:
                    id_node = etree.SubElement(funder_name_node, '{%s}assertion' % fr, name="funder_identifier")
                    if funder_id:
                        id_node.text = funder_id
                    else:
                        id_node.text = funder.agency_url
                if funder.award_number:
                    award_node = etree.SubElement(funder_group_node, '{%s}assertion' % fr, name='award_number')
                    award_node.text = funder.award_number

        # create dataset license sub element
        dataset_licenses_node = etree.SubElement(dataset_node, '{%s}program' % ai, name="AccessIndicators")
        pub_date_str = pub_date.strftime("%Y-%m-%d")
        rights = self.metadata.rights
        license_node = etree.SubElement(dataset_licenses_node, '{%s}license_ref' % ai, applies_to="vor",
                                        start_date=pub_date_str)
        if rights.url:
            license_node.text = rights.url
        else:
            license_node.text = rights.statement

        # doi_data is required element for dataset
        doi_data_node = etree.SubElement(dataset_node, 'doi_data')
        res_doi = get_activated_doi(self.doi)
        idx = res_doi.find('10.4211')
        if idx >= 0:
            res_doi = res_doi[idx:]
        etree.SubElement(doi_data_node, 'doi').text = res_doi
        res_url = self.metadata.identifiers.all().filter(name='hydroShareIdentifier')[0].url
        etree.SubElement(doi_data_node, 'resource').text = res_url

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + etree.tostring(
            ROOT, encoding='UTF-8', pretty_print=pretty_print).decode()

    @property
    def size(self):
        """Return the total size of all data files in iRODS.

        This size does not include metadata. Just files. Specifically,
        resourcemetadata.xml, systemmetadata.xml are not included in this
        size estimate.

        Raises SessionException if iRODS fails.
        """
        # trigger file size read for files that haven't been set yet
        res_size = 0
        if self.files.count() > 0:
            for f in self.files.filter(_size__lt=0):
                f.calculate_size()
            # compute the total file size for the resource
            res_size_dict = self.files.aggregate(Sum('_size'))
            res_size = res_size_dict['_size__sum']

        return res_size

    @property
    def verbose_name(self):
        """Return verbose name of content_model."""
        return self.get_content_model()._meta.verbose_name

    @property
    def discovery_content_type(self):
        """Return name used for the content type in discovery/solr search."""
        return self.get_content_model().display_name

    @property
    def can_be_submitted_for_metadata_review(self):
        """Determine when data and metadata are complete enough for the resource to be published.

        The property can be overriden by specific resource type which is not appropriate for
        publication such as the Web App resource
        :return:
        """
        if self.raccess.published:
            return False

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
        hs_term_dict.update(self.extra_metadata.items())

        return hs_term_dict

    def replaced_by(self):
        """ return a list or resources that replaced this one """
        from hs_core.hydroshare import get_resource_by_shortkey

        replaced_by_resources = []

        def get_replaced_by(resource):
            replace_relation_meta = resource.metadata.relations.all().filter(type=RelationTypes.isReplacedBy).first()
            if replace_relation_meta is not None:
                version_citation = replace_relation_meta.value
                if '/resource/' in version_citation:
                    version_res_id = version_citation.split('/resource/')[-1]
                    try:
                        new_version_res = get_resource_by_shortkey(version_res_id, or_404=False)
                        replaced_by_resources.append(new_version_res)
                        get_replaced_by(new_version_res)
                    except BaseResource.DoesNotExist:
                        pass

        get_replaced_by(self)
        return replaced_by_resources

    def get_relation_version_res_url(self, rel_type):
        """Extracts the resource url from resource citation stored in relation metadata for resource
        versioning
        :param rel_type: type of relation (allowed types are: 'isVersionOf' and 'isReplacedBy')
        """
        relation_meta_obj = self.metadata.relations.filter(type=rel_type).first()
        if relation_meta_obj is not None:
            # get the resource url from resource citation
            version_res_url = relation_meta_obj.value.split(',')[-1]
            return version_res_url
        else:
            return ''

    @property
    def spam_patterns(self):
        # Compile a single regular expression that will match any individual
        # pattern from a given list of patterns, case-insensitive.
        # ( '|' is a special character in regular expressions. An expression
        # 'A|B' will match either 'A' or 'B' ).
        full_pattern = re.compile("|".join(patterns), re.IGNORECASE)

        if self.metadata:
            try:
                match = re.search(full_pattern, self.metadata.title.value)
                if match is not None:
                    return match
            except AttributeError:
                # no title
                pass

            try:
                for sub in self.metadata.subjects.all():
                    match = re.search(full_pattern, sub.value)
                    if match is not None:
                        return match
            except AttributeError:
                # no keywords
                pass

            try:
                match = re.search(full_pattern, self.metadata.description.abstract)
                if match is not None:
                    return match
            except AttributeError:
                # no abstract
                pass

        return None

    @property
    def show_in_discover(self):
        """
        return True if a resource should be exhibited
        A resource should be exhibited if it is at least discoverable
        and not replaced by anything that exists and is at least discoverable.
        """
        if not self.raccess.discoverable:
            return False  # not exhibitable

        replaced_by_resources = self.replaced_by()
        if any([res.raccess.discoverable for res in replaced_by_resources]):
            # there is a newer discoverable resource - so this resource should not be shown in discover
            return False

        if not self.spam_allowlisted and not self.raccess.published:
            if self.spam_patterns:
                return False

        return True

    def update_relation_meta(self):
        """Updates the citation stored in relation metadata for relation type
        'isReplacedBy', 'isPartOf' and 'hasPart' if needed"""

        from hs_core.hydroshare import get_resource_by_shortkey

        def _update_relation_meta(relation_meta_obj):
            relation_updated = False
            if relation_meta_obj.value and '/resource/' in relation_meta_obj.value:
                version_citation = relation_meta_obj.value
                version_res_id = version_citation.split('/resource/')[-1]
                try:
                    version_res = get_resource_by_shortkey(version_res_id, or_404=False)
                except BaseResource.DoesNotExist:
                    relation_meta_obj.delete()
                    relation_updated = True
                    return relation_updated
                current_version_citation = version_res.get_citation()
                if current_version_citation != version_citation:
                    relation_meta_obj.value = current_version_citation
                    relation_meta_obj.save()
                    relation_updated = True
            return relation_updated

        relations = self.metadata.relations.all()
        replace_relation = [rel for rel in relations if rel.type == RelationTypes.isReplacedBy]
        replace_relation_updated = False
        if replace_relation:
            replace_relation = replace_relation[0]
            replace_relation_updated = _update_relation_meta(replace_relation)

        part_of_relation_updated = False
        for part_of_relation in [rel for rel in relations if rel.type == RelationTypes.isPartOf]:
            if _update_relation_meta(part_of_relation):
                part_of_relation_updated = True

        has_part_relation_updated = False
        for has_part_relation in [rel for rel in relations if rel.type == RelationTypes.hasPart]:
            if _update_relation_meta(has_part_relation):
                has_part_relation_updated = True

        if any([replace_relation_updated, part_of_relation_updated, has_part_relation_updated]):
            self.setAVU("bag_modified", True)
            self.setAVU("metadata_dirty", True)

    def get_non_preferred_path_names(self):
        """Returns a list of file/folder paths that do not meet hydroshare file/folder preferred naming convention"""

        def find_non_preferred_folder_paths(dir_path):
            if not dir_path.startswith(self.file_path):
                dir_path = os.path.join(self.file_path, dir_path)

            folders, _, _ = istorage.listdir(dir_path)
            for folder in folders:
                if folder not in not_preferred_paths and not ResourceFile.check_for_preferred_name(folder):
                    folder_path = os.path.join(dir_path, folder)
                    folder_path = folder_path[len(self.file_path) + 1:]
                    not_preferred_paths.append(folder_path)
                subdir_path = os.path.join(dir_path, folder)
                find_non_preferred_folder_paths(subdir_path)

        not_preferred_paths = []
        istorage = self.get_irods_storage()
        # check for non-conforming file names
        for res_file in self.files.all():
            short_path = res_file.short_path
            _, file_name = os.path.split(short_path)
            if not ResourceFile.check_for_preferred_name(file_name):
                not_preferred_paths.append(short_path)

        # check for non-conforming folder names
        find_non_preferred_folder_paths(self.file_path)
        return not_preferred_paths

    def get_relative_path(self, dir_path):
        if dir_path.startswith(self.file_path):
            dir_path = dir_path[len(self.file_path) + 1:]
        return dir_path

    def update_crossref_deposit(self):
        """
        Update crossref deposit xml file for this published resource
        Used when metadata (abstract or funding agency) for a published resource is updated
        """
        from hs_core.tasks import update_crossref_meta_deposit

        if not self.raccess.published:
            err_msg = "Crossref deposit can be updated only for a published resource. "
            err_msg += f"Resource {self.short_id} is not a published resource."
            raise ValidationError(err_msg)

        if self.doi.endswith(self.short_id):
            # doi has no crossref status
            self.extra_data[CrossRefUpdate.UPDATE.value] = 'False'
            update_crossref_meta_deposit.apply_async((self.short_id,))

        # check for both 'pending' and 'update_pending' status in doi
        if CrossRefSubmissionStatus.PENDING in self.doi:
            # setting this flag will update the crossref deposit when the hourly celery task runs
            self.extra_data[CrossRefUpdate.UPDATE.value] = 'True'

        # if the resource crossref deposit is in a 'failure' or 'update_failure' state, then update of the
        # crossref deposit will be attempted when the hourly celery task runs
        self.save()


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
class CoreMetaData(models.Model, RDF_MetaData_Mixin):
    """Define CoreMetaData model."""

    XML_HEADER = '''<?xml version="1.0" encoding="UTF-8"?>'''

    NAMESPACES = {'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                  'rdfs1': "http://www.w3.org/2000/01/rdf-schema#",
                  'dc': "http://purl.org/dc/elements/1.1/",
                  'dcterms': "http://purl.org/dc/terms/",
                  'hsterms': "https://www.hydroshare.org/terms/"}

    id = models.AutoField(primary_key=True)

    _description = GenericRelation(Description)    # resource abstract
    _title = GenericRelation(Title)
    creators = GenericRelation(Creator)
    contributors = GenericRelation(Contributor)
    citation = GenericRelation(Citation)
    dates = GenericRelation(Date)
    coverages = GenericRelation(Coverage)
    formats = GenericRelation(Format)
    identifiers = GenericRelation(Identifier)
    _language = GenericRelation(Language)
    subjects = GenericRelation(Subject)
    relations = GenericRelation(Relation)
    geospatialrelations = GenericRelation(GeospatialRelation)
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
        return self._title.all()[0]

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
    def spatial_coverage_default_projection(self):
        return 'WGS 84 EPSG:4326'

    @property
    def spatial_coverage_default_units(self):
        return 'Decimal degrees'

    @property
    def serializer(self):
        """Return an instance of rest_framework Serializer for self
        Note: Subclass must override this property
        """
        from .views.resource_metadata_rest_api import CoreMetaDataSerializer
        return CoreMetaDataSerializer(self)

    def rdf_subject(self):
        from .hydroshare import current_site_url
        return URIRef("{}/resource/{}".format(current_site_url(), self.resource.short_id))

    def rdf_metadata_subject(self):
        from .hydroshare import current_site_url
        return URIRef("{}/resource/{}/data/resourcemetadata.xml".format(current_site_url(), self.resource.short_id))

    def rdf_type(self):
        return getattr(HSTERMS, self.resource.resource_type)

    def ignored_generic_relations(self):
        """Override to exclude generic relations from the rdf/xml.  This is built specifically for Format, which is the
        only AbstractMetadataElement that is on a metadata model and not included in the rdf/xml.  Returns a list
        of classes to be ignored"""
        return [Format]

    def ingest_metadata(self, graph):
        super(CoreMetaData, self).ingest_metadata(graph)
        subject = self.rdf_subject_from_graph(graph)
        extra_metadata = {}
        for o in graph.objects(subject=subject, predicate=HSTERMS.extendedMetadata):
            key = graph.value(subject=o, predicate=HSTERMS.key).value
            value = graph.value(subject=o, predicate=HSTERMS.value).value
            extra_metadata[key] = value
        res = self.resource
        res.extra_metadata = copy.deepcopy(extra_metadata)

        # delete ingested default citation
        citation_regex = re.compile("(.*) \(\d{4}\)\. (.*), http:\/\/(.*)\/[A-z0-9]{32}")  # noqa
        ingested_citation = self.citation.first()
        if ingested_citation and citation_regex.match(ingested_citation.value):
            self.citation.first().delete()

        res.save()

    def get_rdf_graph(self):
        graph = super(CoreMetaData, self).get_rdf_graph()

        subject = self.rdf_subject()

        # add any key/value metadata items
        if len(self.resource.extra_metadata) > 0:
            for key, value in self.resource.extra_metadata.items():
                extendedMetadata = BNode()
                graph.add((subject, HSTERMS.extendedMetadata, extendedMetadata))
                graph.add((extendedMetadata, HSTERMS.key, Literal(key)))
                graph.add((extendedMetadata, HSTERMS.value, Literal(value)))

        # if custom citation does not exist, use the default citation
        if not self.citation.first():
            graph.add((subject, DCTERMS.bibliographicCitation, Literal(
                self.resource.get_citation(forceHydroshareURI=False))))

        from .hydroshare import current_site_url
        TYPE_SUBJECT = URIRef("{}/terms/{}".format(current_site_url(), self.resource.resource_type))
        graph.add((TYPE_SUBJECT, RDFS1.label, Literal(self.resource.verbose_name)))
        graph.add((TYPE_SUBJECT, RDFS1.isDefinedBy, URIRef(HSTERMS)))
        return graph

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Parse the input *metadata* dict to needed format and store it in
        *parsed_metadata* list
        :param  metadata: a dict of metadata that needs to be parsed to get the metadata in the
        format needed for updating the metadata elements supported by resource type
        :param  parsed_metadata: a list of dicts that will be appended with parsed data
        """

        keys_to_update = list(metadata.keys())
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
            parsed_metadata.append({"rights": metadata.pop('rights')})

        if 'sources' in keys_to_update:
            for source in metadata.pop('sources'):
                parsed_metadata.append({"source": source})

        if 'subjects' in keys_to_update:
            for subject in metadata.pop('subjects'):
                parsed_metadata.append({"subject": {"value": subject['value']}})

        if 'funding_agencies' in keys_to_update:
            for agency in metadata.pop("funding_agencies"):
                # using fundingagency instead of funding_agency to be consistent with UI
                # add-metadata logic as well as the term for the metadata element.
                parsed_metadata.append({"fundingagency": agency})

        if 'relations' in keys_to_update:
            for relation in metadata.pop('relations'):
                parsed_metadata.append({"relation": relation})

        if 'geospatialrelations' in keys_to_update:
            for relation in metadata.pop('geospatialrelations'):
                parsed_metadata.append({"geospatialrelation": relation})

    @classmethod
    def get_supported_element_names(cls):
        """Return a list of supported metadata element names."""
        return ['Description',
                'Citation',
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
                'Relation',
                'GeospatialRelation',
                'Publisher',
                'FundingAgency']

    @classmethod
    def get_form_errors_as_string(cls, form):
        """Helper method to generate a string from form.errors
        :param  form: an instance of Django Form class
        """
        error_string = ", ".join(key + ":" + form.errors[key][0]
                                 for key in list(form.errors.keys()))
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

    def get_required_missing_elements(self, desired_state='discoverable'):
        """Return a list of required missing metadata elements.

        This method needs to be overriden by any subclass of this class
        if they implement additional metadata elements that are required
        """

        resource_states = ('discoverable', 'public', 'published')
        if desired_state not in resource_states:
            raise ValidationError(f"Desired resource state is not in: {','.join(resource_states)}")

        missing_required_elements = []
        if desired_state != 'published':
            if not self.title:
                missing_required_elements.append('Title (at least 30 characters)')
            elif self.title.value.lower() == 'untitled resource':
                missing_required_elements.append('Title (at least 30 characters)')
            if not self.description:
                missing_required_elements.append('Abstract (at least 150 characters)')
            if not self.rights:
                missing_required_elements.append('Rights')
            if self.subjects.count() == 0:
                missing_required_elements.append('Keywords (at least 3)')
        else:
            if not self.title or len(self.title.value) < 30:
                missing_required_elements.append('The title must be at least 30 characters.')
            if not self.description or len(self.description.abstract) < 150:
                missing_required_elements.append('The abstract must be at least 150 characters.')
            if self.subjects.count() < 3:
                missing_required_elements.append('You must include at least 3 keywords.')
        return missing_required_elements

    def get_recommended_missing_elements(self):
        """Return a list of recommended missing metadata elements.

        This method needs to be overriden by any subclass of this class
        if they implement additional metadata elements that are required
        """

        missing_recommended_elements = []
        if not self.funding_agencies.count():
            missing_recommended_elements.append('Funding Agency')
        if not self.resource.readme_file and self.resource.resource_type == "CompositeResource":
            missing_recommended_elements.append('Readme file containing variables, '
                                                'abbreviations/acronyms, and non-standard file formats')
        if not self.coverages.count():
            missing_recommended_elements.append('Coverage that describes locations that are related to the dataset')
        return missing_recommended_elements

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
        self.relations.all().delete()
        self.funding_agencies.all().delete()

    def copy_all_elements_from(self, src_md, exclude_elements=None):
        """Copy all metadata elements from another resource."""
        logger = logging.getLogger(__name__)
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
                try:
                    if exclude_elements:
                        if not element_name.lower() in exclude_elements:
                            self.create_element(element_name, **element_args)
                    else:
                        self.create_element(element_name, **element_args)
                except UserValidationError as uve:
                    logger.error(f"Error copying {element}: {str(uve)}")
                    element_args["hydroshare_user_id"] = None
                    del element_args["is_active_user"]
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
        from .forms import (AbstractValidationForm, ContributorValidationForm,
                            CreatorValidationForm, FundingAgencyValidationForm,
                            GeospatialRelationValidationForm,
                            LanguageValidationForm, RelationValidationForm,
                            RightsValidationForm, TitleValidationForm)

        validation_forms_mapping = {'title': TitleValidationForm,
                                    'description': AbstractValidationForm,
                                    'language': LanguageValidationForm,
                                    'rights': RightsValidationForm,
                                    'creator': CreatorValidationForm,
                                    'contributor': ContributorValidationForm,
                                    'relation': RelationValidationForm,
                                    'geospatialrelation': GeospatialRelationValidationForm,
                                    'fundingagency': FundingAgencyValidationForm
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
                                 'geospatialrelation', 'subject'):
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

            element_name = 'fundingagency'
            identifier_list = [id_dict for id_dict in metadata if element_name in id_dict]
            if len(identifier_list) > 0:
                for id_item in identifier_list:
                    validation_form = validation_forms_mapping[element_name](
                        id_item[element_name])
                    if not validation_form.is_valid():
                        err_string = self.get_form_errors_as_string(validation_form)
                        raise ValidationError(err_string)
                # update_repeatable_elements will append an 's' to element_name before getattr,
                # unless property_name is provided.  I'd like to remove English grammar rules from
                # our codebase, but in the interest of time, I'll just add a special case for
                # handling funding_agencies
                self.update_repeatable_element(element_name=element_name, metadata=metadata,
                                               property_name="funding_agencies")

    @property
    def resource_uri(self):
        return self.identifiers.all().filter(name='hydroShareIdentifier')[0].url

    def create_element(self, element_model_name, **kwargs):
        """Create any supported metadata element."""
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        element_model_name = element_model_name.lower()
        resource = self.resource
        if resource.raccess.published:
            if element_model_name == 'creator':
                raise ValidationError("{} can't be created for a published resource".format(element_model_name))
            elif element_model_name == 'identifier':
                name_value = kwargs.get('name', '')
                if name_value != 'doi':
                    # for published resource the 'name' attribute of the identifier must be set to 'doi'
                    raise ValidationError("For a published resource only a doi identifier can be created")
            elif element_model_name == 'date':
                date_type = kwargs.get('type', '')
                if date_type and date_type not in ('modified', 'published'):
                    raise ValidationError("{} date can't be created for a published resource".format(date_type))
        element = model_type.model_class().create(**kwargs)
        if resource.raccess.published:
            if element_model_name in ('fundingagency',):
                resource.update_crossref_deposit()
        return element

    def update_element(self, element_model_name, element_id, **kwargs):
        """Update metadata element."""
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        element_model_name = element_model_name.lower()
        resource = self.resource
        if resource.raccess.published:
            if element_model_name in ('title', 'creator', 'rights', 'identifier', 'format', 'publisher'):
                raise ValidationError("{} can't be updated for a published resource".format(element_model_name))
            elif element_model_name == 'date':
                date_type = kwargs.get('type', '')
                if date_type and date_type != 'modified':
                    raise ValidationError("{} date can't be updated for a published resource".format(date_type))
        model_type.model_class().update(element_id, **kwargs)
        if resource.raccess.published:
            if element_model_name in ('description', 'fundingagency',):
                resource.update_crossref_deposit()

    def delete_element(self, element_model_name, element_id):
        """Delete Metadata element."""
        model_type = self._get_metadata_element_model_type(element_model_name)
        element_model_name = element_model_name.lower()
        resource = self.resource
        if resource.raccess.published:
            if element_model_name not in ('subject', 'contributor', 'source', 'relation', 'fundingagency', 'format'):
                raise ValidationError("{} can't be deleted for a published resource".format(element_model_name))
        model_type.model_class().remove(element_id)
        if resource.raccess.published:
            if element_model_name in ('fundingagency',):
                resource.update_crossref_deposit()

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


class TaskNotification(models.Model):
    TASK_STATUS_CHOICES = (
        ('progress', 'Progress'),
        ('failed', 'Failed'),
        ('aborted', 'Aborted'),
        ('completed', 'Completed'),
        ('delivered', 'Delivered'),
    )
    created = models.DateTimeField(auto_now_add=True)
    username = models.CharField(max_length=150, blank=True, db_index=True)
    task_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=1000, blank=True)
    payload = models.CharField(max_length=1000, blank=True)
    status = models.CharField(max_length=20, choices=TASK_STATUS_CHOICES, default='progress')


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


@receiver(tus_upload_finished_signal)
def tus_upload_finished_handler(sender, **kwargs):
    from hs_core.views.utils import create_folder
    from rest_framework.exceptions import ValidationError as DRFValidationError
    """Handle the tus upload finished signal.

    Ingest the files from the TUS_DESTINATION_DIR into the resource.

    https://github.com/alican/django-tus/blob/master/django_tus/signals.py
    This signal provides the following keyword arguments:
    metadata
    filename
    upload_file_path
    file_size
    upload_url
    destination_folder
    """
    from hs_core import hydroshare
    logger = logging.getLogger(__name__)
    metadata = kwargs['metadata']
    tus_destination_folder = kwargs['destination_folder']
    hs_res_id = metadata['hs_res_id']
    original_filename = metadata['original_file_name']

    where_tus_put_it = os.path.join(tus_destination_folder, original_filename)

    if original_filename != kwargs['filename']:
        # rename the file
        chunk_file_path = os.path.join(tus_destination_folder, kwargs['filename'])
        os.rename(chunk_file_path, where_tus_put_it)

    # create a file object for the uploaded file
    file_obj = File(open(where_tus_put_it, 'rb'), name=original_filename)

    resource = hydroshare.utils.get_resource_by_shortkey(hs_res_id)

    eventual_relative_path = ''

    try:
        # see if there is a path within data/contents that the file should be uploaded to
        existing_path_in_resource = metadata.get('existing_path_in_resource', '')
        existing_path_in_resource = json.loads(existing_path_in_resource).get("path")
        if existing_path_in_resource:
            # in this case, we are uploading to an existing folder in the resource
            # existing_path_in_resource is a list of folder names
            # append them into a path
            for folder in existing_path_in_resource:
                eventual_relative_path += folder + '/'
    except Exception as ex:
        logger.info(f"Existing path in resource not found: {str(ex)}")

    # handle the case that a folder was uploaded instead of a single file
    # use the metadata.relativePath to rebuild the folder structure
    path_within_uploaded_folder = metadata.get('relativePath', '')
    # path_within_resource_contents will include the name of the file, so we need to remove it
    path_within_uploaded_folder = os.path.dirname(path_within_uploaded_folder)
    if path_within_uploaded_folder:
        eventual_relative_path += path_within_uploaded_folder
        file_folder = f'data/contents/{eventual_relative_path}'
        try:
            create_folder(res_id=hs_res_id, folder_path=file_folder)
        except DRFValidationError as ex:
            logger.info(f"Folder {file_folder} already exists for resource {hs_res_id}: {str(ex)}")

    try:
        hydroshare.utils.resource_file_add_pre_process(
            resource=resource,
            files=[file_obj],
            user=resource.creator,
            folder=eventual_relative_path,
        )
        hydroshare.utils.resource_file_add_process(
            resource=resource,
            files=[file_obj],
            user=resource.creator,
            folder=eventual_relative_path,
        )
        # remove the uploaded file
        os.remove(where_tus_put_it)
    except (hydroshare.utils.ResourceFileSizeException,
            hydroshare.utils.ResourceFileValidationException,
            Exception) as ex:
        logger.error(ex)
