from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django import forms
from django.utils.timezone import now
from mezzanine.pages.models import Page, RichText
from mezzanine.pages.page_processors import processor_for
from uuid import uuid4
from mezzanine.core.models import Ownable
from mezzanine.generic.fields import CommentsField, RatingField
from mezzanine.generic.fields import KeywordsField
from mezzanine.conf import settings as s
import os.path
from django_irods.storage import IrodsStorage
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from languages_iso import languages as iso_languages
from dateutil import parser
import json


class GroupOwnership(models.Model):
    group = models.ForeignKey(Group)
    owner = models.ForeignKey(User)


def get_user(request):
    """authorize user based on API key if it was passed, otherwise just use the request's user.

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
    creator = models.ForeignKey(User,
                                related_name='creator_of_%(app_label)s_%(class)s',
                                help_text='This is the person who first uploaded the resource',
                                )

    public = models.BooleanField(
        help_text='If this is true, the resource is viewable and downloadable by anyone',
        default=True
    )

    owners = models.ManyToManyField(User,
                                    related_name='owns_%(app_label)s_%(class)s',
                                    help_text='The person who has total ownership of the resource'
    )
    frozen = models.BooleanField(
        help_text='If this is true, the resource should not be modified',
        default=False
    )
    do_not_distribute = models.BooleanField(
        help_text='If this is true, the resource owner has to designate viewers',
        default=False
    )
    discoverable = models.BooleanField(
        help_text='If this is true, it will turn up in searches.',
        default=True
    )
    published_and_frozen = models.BooleanField(
        help_text="Once this is true, no changes can be made to the resource",
        default=False
    )

    view_users = models.ManyToManyField(User,
                                        related_name='user_viewable_%(app_label)s_%(class)s',
                                        help_text='This is the set of Hydroshare Users who can view the resource',
                                        null=True, blank=True)

    view_groups = models.ManyToManyField(Group,
                                         related_name='group_viewable_%(app_label)s_%(class)s',
                                         help_text='This is the set of Hydroshare Groups who can view the resource',
                                         null=True, blank=True)

    edit_users = models.ManyToManyField(User,
                                        related_name='user_editable_%(app_label)s_%(class)s',
                                        help_text='This is the set of Hydroshare Users who can edit the resource',
                                        null=True, blank=True)

    edit_groups = models.ManyToManyField(Group,
                                         related_name='group_editable_%(app_label)s_%(class)s',
                                         help_text='This is the set of Hydroshare Groups who can edit the resource',
                                         null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def permissions_store(self):
        return s.PERMISSIONS_DB

    def can_add(self, request):
        return self.can_change(request)

    def can_delete(self, request):
        user = get_user(request)
        if user.is_authenticated():
            if user.is_superuser or self.owners.filter(pk=user.pk).exists():
                return True
            else:
                return False
        else:
            return False


    def can_change(self, request):
        user = get_user(request)

        if user.is_authenticated():
            if user.is_superuser:
                return True
            elif self.owners.filter(pk=user.pk).exists():
                return True
            elif self.edit_users.filter(pk=user.pk).exists():
                return True
            elif self.edit_groups.filter(pk__in=set(g.pk for g in user.groups.all())):
                return True
            else:
                return False
        else:
            return False

    def can_view(self, request):
        user = get_user(request)

        if self.public:
            return True
        if user.is_authenticated():
            if user.is_superuser:
                return True
            elif self.owners.filter(pk=user.pk).exists():
                return True
            elif self.edit_users.filter(pk=user.pk).exists():
                return True
            elif self.view_users.filter(pk=user.pk).exists():
                return True
            elif self.edit_groups.filter(pk__in=set(g.pk for g in user.groups.all())):
                return True
            elif self.view_groups.filter(pk__in=set(g.pk for g in user.groups.all())):
                return True
            else:
                return False
        else:
            return False

# this should be used as the page processor for anything with pagepermissionsmixin
# page_processor_for(MyPage)(ga_resources.views.page_permissions_page_processor)
def page_permissions_page_processor(request, page):
    page = page.get_content_model()
    user = get_user(request)

    return {
        "edit_groups": set(page.edit_groups.all()),
        "view_groups": set(page.view_groups.all()),
        "edit_users": set(page.edit_users.all()),
        "view_users": set(page.view_users.all()),
        "owners": set(page.owners.all()),
        "can_edit": (user in set(page.edit_users.all())) \
                    or (len(set(page.edit_groups.all()).intersection(set(user.groups.all()))) > 0)
    }

class AbstractMetaDataElement(models.Model):
    term = None

    object_id = models.PositiveIntegerField()
    # see the following link the reason for having the related_name setting for the content_type attribute
    # https://docs.djangoproject.com/en/1.6/topics/db/models/#abstract-related-name
    content_type = models.ForeignKey(ContentType, related_name="%(app_label)s_%(class)s_related")
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    @property
    def metadata(self):
        return self.content_object

    @classmethod
    def create(cls, **kwargs):
        raise NotImplementedError("Please implement this method")

    @classmethod
    def update(cls, element_id, **kwargs):
        raise NotImplementedError("Please implement this method")

    # could not name this method as 'delete' since the parent 'Model' class has such a method
    @classmethod
    def remove(cls, element_id):
        raise NotImplementedError("Please implement this method")

    class Meta:
        abstract = True

# Adaptor class added for Django inplace editing to honor HydroShare user-resource permissions
class HSAdaptorEditInline(object):
    @classmethod
    def can_edit(cls, adaptor_field):
        #from hs_core.views.utils import authorize
        user = adaptor_field.request.user
        can_edit = False
        if user.is_anonymous():
            pass
        elif user.is_superuser:
            can_edit = True
        else:
            obj = adaptor_field.obj
            cm = obj.get_content_model()
            #_, can_edit, _ = authorize(adaptor_field.request, res_id, edit=True, full=True) - need to know res_id
            can_edit = (user in set(cm.edit_users.all())) or (len(set(cm.edit_groups.all()).intersection(set(user.groups.all()))) > 0)
        return can_edit

class ExternalProfileLink(models.Model):
    type = models.CharField(max_length=50)
    url = models.URLField()

    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ("type", "url", "object_id")

class Party(AbstractMetaDataElement):
    description = models.URLField(null=True, blank=True, validators=[validate_user_url])
    name = models.CharField(max_length=100)
    organization = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    phone = models.CharField(max_length=25, null=True, blank=True)
    homepage = models.URLField(null=True, blank=True)
    external_links = generic.GenericRelation(ExternalProfileLink)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True

    @classmethod
    def create(cls,**kwargs):
        element_name = cls.__name__
        if 'name' in kwargs:
            if not isinstance(kwargs['content_object'], CoreMetaData) and not issubclass(kwargs['content_object'], CoreMetaData):
                raise ValidationError("%s metadata element can't be created for metadata type:%s" %(element_name, type(kwargs['content_object'])))

            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            if element_name == 'Creator':
                party = Creator.objects.filter(object_id=metadata_obj.id, content_type=metadata_type).last()
                creator_order = 1
                if party:
                    creator_order = party.order + 1
                if len(kwargs['name'].strip()) == 0:
                    raise ValidationError("Invalid name for the %s." % element_name.lower())

                party = Creator.objects.create(name=kwargs['name'], order=creator_order, content_object=metadata_obj)
            else:
                party = Contributor.objects.create(name=kwargs['name'], content_object=metadata_obj)

            if 'profile_links' in kwargs:
                links = kwargs['profile_links']
                for link in links:
                    cls._create_profile_link(party, link)

            for key, value in kwargs.iteritems():
                if key in ('description', 'organization', 'email', 'address', 'phone', 'homepage'):
                    setattr(party, key, value)

            party.save()
            return party
        else:
            raise ValidationError("Name for the %s is missing." % element_name.lower())

    @classmethod
    def update(cls, element_id, **kwargs):
        element_name = cls.__name__
        if element_name == 'Creator':
            party = Creator.objects.get(id=element_id)
        else:
            party = Contributor.objects.get(id=element_id)

        if party:
            if 'name' in kwargs:
                party.name = kwargs['name']

            if 'description' in kwargs:
                party.description = kwargs['description']

            if 'organization' in kwargs:
                party.organization = kwargs['organization']

            if 'email' in kwargs:
                party.email = kwargs['email']

            if 'address' in kwargs:
                party.address = kwargs['address']

            if 'phone' in kwargs:
                party.phone = kwargs['phone']

            if 'homepage' in kwargs:
                party.homepage = kwargs['homepage']

            if 'researcherID' in kwargs:
                party.researcherID = kwargs['researcherID']

            if 'researchGateID' in kwargs:
                party.researchGateID = kwargs['researchGateID']

            # updating the order of a creator needs updating the order attribute of all other creators
            # of the same resource
            if 'order' in kwargs:
                if isinstance(party, Creator):
                    if kwargs['order'] <= 0:
                        kwargs['order'] = 1

                    if party.order != kwargs['order']:
                        resource_creators = Creator.objects.filter(object_id=party.object_id, content_type__pk=party.content_type.id).all()

                        if kwargs['order'] > len(resource_creators):
                            kwargs['order'] = len(resource_creators)

                        for res_cr in resource_creators:
                            if party.order > kwargs['order']:
                                if res_cr.order < party.order and not res_cr.order < kwargs['order']:
                                    res_cr.order += 1
                                    res_cr.save()

                            else:
                                if res_cr.order > party.order:
                                    res_cr.order -= 1
                                    res_cr.save()


                        party.order = kwargs['order']

            #either create or update external profile links
            if 'profile_links' in kwargs:
                links = kwargs['profile_links']
                for link in links:
                    if 'link_id' in link: # need to update an existing profile link
                        cls._update_profile_link(party, link)
                    elif 'type' in link and 'url' in link:  # add a new profile link
                        cls._create_profile_link(party, link)
            party.save()
        else:
            raise ObjectDoesNotExist("No %s was found for the provided id:%s" % (element_name, kwargs['id']))

    @classmethod
    def remove(cls, element_id):
        element_name = cls.__name__
        if element_name == 'Creator':
            party = Creator.objects.get(id=element_id)
        else:
            party = Contributor.objects.get(id=element_id)

        # if we are deleting a creator, then we have to update the order attribute of remaining
        # creators associated with a resource
        if party:
            # make sure we are not deleting all creators of a resource
            if isinstance(party, Creator):
                if Creator.objects.filter(object_id=party.object_id, content_type__pk=party.content_type.id).count()== 1:
                    raise ValidationError("The only creator of the resource can't be deleted.")

                creators_to_update = Creator.objects.filter(
                    object_id=party.object_id, content_type__pk=party.content_type.id).exclude(order=party.order).all()

                for cr in creators_to_update:
                    if cr.order > party.order:
                        cr.order -= 1
                        cr.save()
            party.delete()
        else:
            raise ObjectDoesNotExist("No %s element was found for id:%d." % (element_name, element_id))

    @classmethod
    def _create_profile_link(cls, party, link):
        if 'type' in link and 'url' in link:
            # check that the type is unique for the party
            if party.external_links.filter(type=link['type']).count() > 0:
                raise ValidationError("External profile link type:%s already exists "
                                      "for this %s" % (link['type'], type(party).__name__))

            if party.external_links.filter(url=link['url']).count() > 0:
                raise ValidationError("External profile link url:%s already exists "
                                      "for this %s" % (link['url'], type(party).__name__))

            p_link = ExternalProfileLink(type=link['type'], url=link['url'], content_object=party)
            p_link.save()
        else:
            raise ValidationError("Invalid %s profile link data." % type(party).__name__)

    @classmethod
    def _update_profile_link(cls, party, link):
        """
        if the link dict contains only key 'link_id' then the link will be deleted
        otherwise the link will be updated
        """
        p_link = ExternalProfileLink.objects.get(id=link['link_id'])
        if p_link:
            if not 'type' in link and not 'url' in link:
                # delete the link
                p_link.delete()
            else:
                if 'type' in link:
                    # check that the type is unique for the party
                    if p_link.type != link['type']:
                        if party.external_links.filter(type=link['type']).count() > 0:
                            raise ValidationError("External profile link type:%s "
                                                  "already exists for this %s" % (link['type'], type(party).__name__))
                        else:
                            p_link.type = link['type']
                if 'url' in link:
                    # check that the url is unique for the party
                    if p_link.url != link['url']:
                        if party.external_links.filter(url=link['url']).count() > 0:
                            raise ValidationError("External profile link url:%s already exists "
                                                  "for this %s" % (link['url'], type(party).__name__))
                        else:
                            p_link.url = link['url']

                p_link.save()
        else:
            raise ObjectDoesNotExist("%s external link does not exist "
                                     "for ID:%s" % (type(party).__name__,link['link_id']))

class Contributor(Party):
    term = 'Contributor'



# Example of repeatable metadata element
class Creator(Party):
    term = "Creator"
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']


class Description(AbstractMetaDataElement):
    term = 'Description'
    abstract = models.TextField()

    def __unicode__(self):
        return self.abstract

    class Meta:
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        if 'abstract' in kwargs:

            # no need to check if a description element already exists
            # the Meta settings 'unique_together' will enforce that we have only one description element per resource
            return Description.objects.create(**kwargs)

        else:
            raise ValidationError("Abstract of the description element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        description = Description.objects.get(id=element_id)
        if description:
            if 'abstract' in kwargs:
                if len(kwargs['abstract'].strip()) > 0:
                    description.abstract = kwargs['abstract']
                    description.save()
                else:
                    raise ValidationError('A value for the description/abstract element is missing.')
            else:
                raise ValidationError('A value for description/abstract element is missing.')
        else:
            raise ObjectDoesNotExist("No description/abstract element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Description element of a resource can't be deleted.")

class Title(AbstractMetaDataElement):
    term = 'Title'
    value = models.CharField(max_length=300)

    def __unicode__(self):
        return self.value

    class Meta:
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            return Title.objects.create(**kwargs)

        else:
            raise ValidationError("Value of the title element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        title = Title.objects.get(id=element_id)
        if title:
            if 'value' in kwargs:
                title.value = kwargs['value']
                title.save()
                # This way of updating the resource title field does not work
                # so updating code is in in resource.py
                # res = title.content_object.resource
                # res.title = title.value
                # res.save()
            else:
                raise ValidationError('Value for title is missing.')
        else:
            raise ValidationError("No title element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Title element of a resource can't be deleted.")

class Type(AbstractMetaDataElement):
    term = 'Type'
    url = models.URLField()

    def __unicode__(self):
        return self.value

    class Meta:
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        if 'url' in kwargs:
            return Type.objects.create(**kwargs)
        else:
            raise ValidationError("URL of the type element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        type = Type.objects.get(id=element_id)
        if type:
            if 'url' in kwargs:
                type.url = kwargs['url']
                type.save()
            else:
                raise ValidationError('URL for type element is missing.')
        else:
            raise ObjectDoesNotExist("No type element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Type element of a resource can't be deleted.")

class Date(AbstractMetaDataElement):
    DATE_TYPE_CHOICES=(
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

    @classmethod
    def create(cls, **kwargs):
        if 'type' in kwargs:
            # check the type doesn't already exists - we allow only one date type per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            dt = Date.objects.filter(type= kwargs['type'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if dt:
                raise ValidationError('Date type:%s already exists' % kwargs['type'])
            if not kwargs['type'] in ['created', 'modified', 'valid', 'available', 'published']:
                raise ValidationError('Invalid date type:%s' % kwargs['type'])

            if kwargs['type'] == 'published':
                if not metadata_obj.resource.published_and_frozen:
                    raise ValidationError("Resource is not published yet.")

            if kwargs['type'] == 'available':
                if not metadata_obj.resource.public:
                    raise ValidationError("Resource has not been shared yet.")

            if 'start_date' in kwargs:
                try:
                    start_dt = parser.parse(str(kwargs['start_date']))
                except TypeError:
                    raise TypeError("Not a valid date value.")
            else:
                raise ValidationError('Date value is missing.')

            # end_date is used only for date type 'valid'
            if kwargs['type'] == 'valid':
                if 'end_date' in kwargs:
                    try:
                        end_dt = parser.parse(str(kwargs['end_date']))
                    except TypeError:
                        raise TypeError("Not a valid end date value.")
                    dt = Date.objects.create(type=kwargs['type'], start_date=start_dt, end_date=end_dt, content_object=metadata_obj)
                else:
                    dt = Date.objects.create(type=kwargs['type'], start_date=start_dt, content_object=metadata_obj)
            else:
                dt = Date.objects.create(type=kwargs['type'], start_date=start_dt, content_object=metadata_obj)

            return dt

        else:
            raise ValidationError("Type of date element is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        dt = Date.objects.get(id=element_id)
        if dt:
            if 'start_date' in kwargs:
                try:
                    start_dt = parser.parse(str(kwargs['start_date']))
                except TypeError:
                    raise TypeError("Not a valid date value.")
                if dt.type == 'created':
                    raise ValidationError("Resource creation date can't be changed")
                elif dt.type == 'modified':
                    dt.start_date = now().isoformat()
                    dt.save()
                elif dt.type == 'valid':
                    if 'end_date' in kwargs:
                        try:
                            end_dt = parser.parse(str(kwargs['end_date']))
                        except TypeError:
                            raise TypeError("Not a valid date value.")
                        dt.start_date = start_dt
                        dt.end_date = end_dt
                        dt.save()
                    else:
                        dt.start_date = start_dt
                        dt.save()
                else:
                    dt.start_date = start_dt
                    dt.save()
            elif dt.type == 'modified':
                dt.start_date = now().isoformat()
                dt.save()
            else:
                raise ValidationError("Date value is missing.")
        else:
            raise ObjectDoesNotExist("No date element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        dt = Date.objects.get(id=element_id)
        if dt:
            if dt.type in ['created', 'modified']:
                raise ValidationError("Date element of type:%s can't be deleted." % dt.type)

            dt.delete()
        else:
            raise ObjectDoesNotExist("No date element was found for id:%d." % element_id)

class Relation(AbstractMetaDataElement):
    SOURCE_TYPES= (
        ('isPartOf', 'Part Of'),
        ('isExecutedBy', 'Executed By'),
        ('isCreatedBy', 'Created By'),
        ('isVersionOf', 'Version Of'),
        ('isDataFor', 'Data For'),
        ('cites', 'Cites'),
    )

    term = 'Relation'
    type = models.CharField(max_length=100, choices=SOURCE_TYPES)
    value = models.CharField(max_length=500)

    @classmethod
    def create(cls, **kwargs):
        if 'type' in kwargs:
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            rel = Relation.objects.filter(type= kwargs['type'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if rel:
                raise ValidationError('Relation type:%s already exists.' % kwargs['type'])
            if 'value' in kwargs:
                return Relation.objects.create(type=kwargs['type'], value=kwargs['value'], content_object=metadata_obj)

            else:
                raise ValidationError('Value for relation element is missing.')
        else:
            raise ObjectDoesNotExist("Type of relation element is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        rel = Relation.objects.get(id=element_id)
        if rel:
            if 'type' in kwargs:
                if rel.type != kwargs['type']:
                    # check this new relation type not already exists
                    if Relation.objects.filter(type=kwargs['type'], object_id=rel.object_id,
                                              content_type__pk=rel.content_type.id).count()> 0:
                        raise ValidationError( 'Relation type:%s already exists.' % kwargs['type'])
                    else:
                        rel.type = kwargs['type']

            if 'value' in kwargs:
                rel.value = kwargs['value']
            rel.save()
        else:
            raise ObjectDoesNotExist("No relation element exists for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        rel = Relation.objects.get(id=element_id)
        if rel:
            rel.delete()
        else:
            raise ObjectDoesNotExist("No relation element exists for id:%d." % element_id)

class Identifier(AbstractMetaDataElement):
    term = 'Identifier'
    name = models.CharField(max_length=100)
    url = models.URLField(unique=True)

    @classmethod
    def create(cls, **kwargs):
        if 'name' in kwargs:
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            # check the identifier name doesn't already exist - identifier name needs to be unique per resource
            idf = Identifier.objects.filter(name__iexact= kwargs['name'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if idf:
                raise ValidationError('Identifier name:%s already exists' % kwargs['name'])
            if kwargs['name'].lower() == 'doi':
                if not metadata_obj.resource.doi:
                    raise ValidationError("Identifier of 'DOI' type can't be created for a resource that has not been assign a DOI yet.")

            if 'url' in kwargs:
                idf = Identifier.objects.create(name=kwargs['name'], url=kwargs['url'], content_object=metadata_obj)
                return idf
            else:
                raise ValidationError('URL for the identifier is missing.')

        else:
            raise ValidationError("Name of identifier element is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        idf = Identifier.objects.get(id=element_id)
        if idf:
            if 'name' in kwargs:
                if idf.name.lower() != kwargs['name'].lower():
                    if idf.name.lower() == 'hydroshareidentifier':
                        if not 'migration' in kwargs:
                            raise ValidationError("Identifier name 'hydroshareIdentifier' can't be changed.")

                    if idf.name.lower() == 'doi':
                        raise ValidationError("Identifier name 'DOI' can't be changed.")

                    # check this new identifier name not already exists
                    if Identifier.objects.filter(name__iexact=kwargs['name'], object_id=idf.object_id,
                                              content_type__pk=idf.content_type.id).count()> 0:
                        if not 'migration' in kwargs:
                            raise ValidationError('Identifier name:%s already exists.' % kwargs['name'])

                    idf.name = kwargs['name']

            if 'url' in kwargs:
                if idf.url.lower() != kwargs['url'].lower():
                    if idf.name.lower() == 'hydroshareidentifier':
                        if not 'migration' in kwargs:
                            raise  ValidationError("Hydroshare identifier url value can't be changed.")

                    # if idf.url.lower().find('http://hydroshare.org/resource') == 0:
                    #     raise  ValidationError("Hydroshare identifier url value can't be changed.")
                    # check this new identifier name not already exists
                    if Identifier.objects.filter(url__iexact=kwargs['url'], object_id=idf.object_id,
                                                 content_type__pk=idf.content_type.id).count()> 0:
                        raise ValidationError('Identifier URL:%s already exists.' % kwargs['url'])

                    idf.url = kwargs['url']

            idf.save()
        else:
            raise ObjectDoesNotExist( "No identifier element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        idf = Identifier.objects.get(id=element_id)
        if idf:
            if idf.name.lower() == 'hydroshareidentifier':
                raise ValidationError("Hydroshare identifier:%s can't be deleted." % idf.name)

            if idf.name.lower() == 'doi':
                if idf.content_object.resource.doi:
                    raise ValidationError("Hydroshare identifier:%s can't be deleted for a resource that has been assigned a DOI." % idf.name)
            idf.delete()
        else:
            raise ObjectDoesNotExist("No identifier element was found for id:%d." % element_id)


class Publisher(AbstractMetaDataElement):
    term = 'Publisher'
    name = models.CharField(max_length=200)
    url = models.URLField()

    class Meta:
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        if 'name' in kwargs:
            metadata_obj = kwargs['content_object']
            if 'url' in kwargs:
                if not metadata_obj.resource.public and metadata_obj.resource.published_and_frozen:
                    raise ValidationError("Publisher element can't be created for a resource that is not shared nor published.")
                if kwargs['name'].lower() == 'hydroshare':
                    if not  metadata_obj.resource.files.all():
                        raise ValidationError("Hydroshare can't be the publisher for a resource that has no content files.")
                    else:
                        kwargs['name'] = 'HydroShare'
                        kwargs['url'] = 'http://hydroshare.org'
                return Publisher.objects.create(name=kwargs['name'], url=kwargs['url'], content_object=metadata_obj)
            else:
                raise ValidationError('URL for the publisher is missing.')
        else:
            raise ValidationError("Name of publisher is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        pub = Publisher.objects.get(id=element_id)
        metadata_obj = kwargs['content_object']

        if metadata_obj.resource.frozen:
            raise ValidationError("Resource metadata can't be edited when the resource is in frozen state.")

        if metadata_obj.resource.published_and_frozen:
            raise ValidationError("Resource metadata can't be edited once the resource has been published.")

        if pub:
            if 'name' in kwargs:
                if pub.name.lower() != kwargs['name'].lower():
                    if pub.name.lower() == 'hydroshare':
                        if metadata_obj.resource.files.all():
                            raise ValidationError("Publisher 'HydroShare' can't be changed for a resource that has content files.")
                    elif kwargs['name'].lower() == 'hydroshare':
                        if not metadata_obj.resource.files.all():
                            raise ValidationError("'HydroShare' can't be a publisher for a resource that has no content files.")

                    if metadata_obj.resource.files.all():
                        pub.name = 'HydroShare'
                    else:
                        pub.name = kwargs['name']

            if 'url' in kwargs:
                if pub.url != kwargs['url']:
                    # make sure we are not changing the url for hydroshare publisher
                    if pub.name.lower() == 'hydroshare':
                        pub.url = 'http://hydroshare.org'
                    else:
                        pub.url = kwargs['url']
            pub.save()
        else:
            raise ObjectDoesNotExist("No publisher element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        pub = Publisher.objects.get(id=element_id)

        if pub.content_object.resource.frozen:
            raise ValidationError("Resource metadata can't be edited when the resource is in frozen state.")

        if pub.content_object.resource.published_and_frozen:
            raise ValidationError("Resource metadata can't be edited once the resource has been published.")

        if pub.content_object.resource.public:
            raise ValidationError("Resource publisher can't be deleted for shared resource.")

        if pub:
            if pub.name.lower() == 'hydroshare':
                if pub.content_object.resource.files.all():
                    raise ValidationError("Publisher HydroShare can't be deleted for a resource that has content files.")
            if pub.content_object.resource.public:
                raise ValidationError("Publisher can't be deleted for a public resource.")
            pub.delete()
        else:
            raise ObjectDoesNotExist("No publisher element was found for id:%d." % element_id)

class Language(AbstractMetaDataElement):
    term = 'Language'
    code = models.CharField(max_length=3, choices=iso_languages )

    def __unicode__(self):
        return self.code

    @classmethod
    def create(cls, **kwargs):
        if 'code' in kwargs:
            # check the code doesn't already exists - format values need to be unique per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            lang = Language.objects.filter(object_id=metadata_obj.id, content_type=metadata_type).first()
            if lang:
                raise ValidationError('Language element already exists.')

            # check the code is a valid code
            if not [t for t in iso_languages if t[0]==kwargs['code']]:
                raise ValidationError('Invalid language code:%s' % kwargs['code'])

            lang = Language.objects.create(code=kwargs['code'], content_object=metadata_obj)
            return lang
        else:
            raise ValidationError("Language code is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        lang = Language.objects.get(id=element_id)
        if lang:
            if 'code' in kwargs:
                # validate code
                if not [t for t in iso_languages if t[0]==kwargs['code']]:
                    raise ValidationError('Invalid language code:%s' % kwargs['code'])

                if lang.code != kwargs['code']:
                    # check this new language not already exists
                    if Language.objects.filter(code=kwargs['code'], object_id=lang.object_id,
                                             content_type__pk=lang.content_type.id).count()> 0:
                        raise ValidationError('Language:%s already exists.' % kwargs['code'])

                lang.code = kwargs['code']
                lang.save()
            else:
                raise ValidationError('Language code is missing.')
        else:
            raise ObjectDoesNotExist("No language element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        lang = Language.objects.get(id=element_id)
        if lang:
            lang.delete()
        else:
            raise ObjectDoesNotExist("No language element was found for id:%d." % element_id)

class Coverage(AbstractMetaDataElement):
    COVERAGE_TYPES = (
        ('box', 'Box'),
        ('point', 'Point'),
        ('period', 'Period')
    )

    term = 'Coverage'
    type = models.CharField(max_length=20, choices=COVERAGE_TYPES)
    """
    _value field stores a json string. The content of the json
     string depends on the type of coverage as shown below. All keys shown in json string are required.

     For coverage type: period
         _value = "{'name':coverage name value here (optional), 'start':start date value, 'end':end date value, 'scheme':'W3C-DTF}"

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
        print self._value
        return json.loads(self._value)

    @classmethod
    def create(cls, **kwargs):
        # TODO: validate coordinate values
        if 'type' in kwargs:
            # check the type doesn't already exists - we allow only one coverage type per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            coverage = Coverage.objects.filter(type= kwargs['type'], object_id=metadata_obj.id,
                                               content_type=metadata_type).first()
            if coverage:
                raise ValidationError('Coverage type:%s already exists' % kwargs['type'])

            if not kwargs['type'] in ['box', 'point', 'period']:
                raise ValidationError('Invalid coverage type:%s' % kwargs['type'])

            if kwargs['type'] == 'box':
                # check that there is not already a coverage of point type
                coverage = Coverage.objects.filter(type= 'point', object_id=metadata_obj.id,
                                                   content_type=metadata_type).first()
                if coverage:
                    raise ValidationError("Coverage type 'Box' can't be created when there is a coverage of type 'Point'")
            elif kwargs['type'] == 'point':
                # check that there is not already a coverage of box type
                coverage = Coverage.objects.filter(type= 'box', object_id=metadata_obj.id,
                                                   content_type=metadata_type).first()
                if coverage:
                    raise ValidationError("Coverage type 'Point' can't be created when there is a coverage of type 'Box'")

            if 'value' in kwargs:
                if isinstance(kwargs['value'], dict):
                    # if not 'name' in kwargs['value']:
                    #     raise ValidationError("Coverage name attribute is missing.")

                    cls._validate_coverage_type_value_attributes(kwargs['type'], kwargs['value'])

                    if kwargs['type'] == 'period':
                        value_dict = {k: v for k, v in kwargs['value'].iteritems() if k in ('name', 'start', 'end')}
                    elif kwargs['type']== 'point':
                        value_dict = {k: v for k, v in kwargs['value'].iteritems()
                                      if k in ('name', 'east', 'north', 'units', 'elevation', 'zunits', 'projection')}
                    elif kwargs['type']== 'box':
                        value_dict = {k: v for k, v in kwargs['value'].iteritems()
                                      if k in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit', 'name',
                                               'uplimit', 'downlimit', 'zunits', 'projection')}

                    value_json = json.dumps(value_dict)
                    cov = Coverage.objects.create(type=kwargs['type'], _value=value_json,
                                                  content_object=metadata_obj)
                    return cov
                else:
                    raise ValidationError('Invalid coverage value format.')
            else:
                raise ValidationError('Coverage value is missing.')

        else:
            raise ValidationError("Type of coverage element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        # TODO: validate coordinate values
        cov = Coverage.objects.get(id=element_id)
        changing_coverage_type = False
        if cov:
            if 'type' in kwargs:
                if cov.type != kwargs['type']:
                    # check this new coverage type not already exists
                    if Coverage.objects.filter(type=kwargs['type'], object_id=cov.object_id,
                                               content_type__pk=cov.content_type.id).count()> 0:
                        raise ValidationError('Coverage type:%s already exists.' % kwargs['type'])
                    else:
                        if 'value' in kwargs:
                            if isinstance(kwargs['value'], dict):
                                cls._validate_coverage_type_value_attributes(kwargs['type'], kwargs['value'])
                            else:
                                raise ValidationError('Invalid coverage value format.')
                        else:
                            raise ValidationError('Coverage value is missing.')

                        changing_coverage_type = True

            if 'value' in kwargs:
                if not isinstance(kwargs['value'], dict):
                    raise ValidationError('Invalid coverage value format.')

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
                    for item_name in ('units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit', 'uplimit',
                                      'downlimit', 'zunits', 'projection'):
                        if item_name in kwargs['value']:
                            value_dict[item_name] = kwargs['value'][item_name]

                value_json = json.dumps(value_dict)
                cov._value = value_json
            cov.save()
        else:
            raise ObjectDoesNotExist("No coverage element was found for the provided id:%s" % element_id)


    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Coverage element can't be deleted.")

    @classmethod
    def _validate_coverage_type_value_attributes(cls, coverage_type, value_dict):
        if coverage_type == 'period':
            # check that all the required sub-elements exist
            if not 'start' in value_dict or not 'end' in value_dict:
                raise ValidationError("For coverage of type 'period' values for both start date and end date are needed.")
            else:
                # validate the date values
                try:
                    start_dt = parser.parse(value_dict['start'])
                except TypeError:
                    raise TypeError("Invalid start date. Not a valid date value.")
                try:
                    end_dt = parser.parse(value_dict['end'])
                except TypeError:
                    raise TypeError("Invalid end date. Not a valid date value.")
        elif coverage_type == 'point':
            # check that all the required sub-elements exist
            if not 'east' in value_dict or not 'north' in value_dict or not 'units' in value_dict:
                raise ValidationError("For coverage of type 'point' values for 'east', 'north' and 'units' are needed.")
        elif coverage_type == 'box':
            # check that all the required sub-elements exist
            for value_item in ['units', 'northlimit', 'eastlimit', 'southlimit', 'westlimit']:
                if not value_item in value_dict:
                    raise ValidationError("For coverage of type 'box' values for one or more bounding box limits or 'units' is missing.")

class Format(AbstractMetaDataElement):
    term = 'Format'
    value = models.CharField(max_length=150)

    def __unicode__(self):
        return self.value

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            # check the format doesn't already exists - format values need to be unique per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            format = Format.objects.filter(value__iexact= kwargs['value'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if format:
                raise ValidationError('Format:%s already exists' % kwargs['value'])

            return Format.objects.create(**kwargs)

        else:
            raise ValidationError("Format value is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        format = Format.objects.get(id=element_id)
        if format:
            if 'value' in kwargs:
                if format.value != kwargs['value']:
                    # check this new format not already exists
                    if Format.objects.filter(value=kwargs['value'], object_id=format.object_id,
                                             content_type__pk=format.content_type.id).count()> 0:
                        raise ValidationError('Format:%s already exists.' % kwargs['value'])

                format.value = kwargs['value']
                format.save()
            else:
                raise ValidationError('Value for format is missing.')
        else:
            raise ObjectDoesNotExist("No format element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        format = Format.objects.get(id=element_id)
        if format:
            format.delete()
        else:
            raise ObjectDoesNotExist("No format element was found for id:%d." % element_id)

class Subject(AbstractMetaDataElement):
    term = 'Subject'
    value = models.CharField(max_length=100)

    def __unicode__(self):
        return self.value

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            # check the subject doesn't already exists - subjects need to be unique per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            sub = Subject.objects.filter(value__iexact=kwargs['value'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if sub:
                raise ValidationError('Subject:%s already exists for this resource.' % kwargs['value'])

            return Subject.objects.create(**kwargs)

        else:
            raise ValidationError("Subject value is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        sub = Subject.objects.get(id=element_id)
        if sub:
            if 'value' in kwargs:
                if sub.value != kwargs['value']:
                    # check this new subject not already exists
                    if Subject.objects.filter(value__iexact=kwargs['value'], object_id=sub.object_id,
                                             content_type__pk=sub.content_type.id).count() > 0:
                        raise ValidationError('Subject:%s already exists for this resource.' % kwargs['value'])

                sub.value = kwargs['value']
                sub.save()
            else:
                raise ValidationError('Value for subject is missing.')
        else:
            raise ObjectDoesNotExist("No format element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        sub = Subject.objects.get(id=element_id)
        if sub:
            if Subject.objects.filter(object_id=sub.object_id,
                                      content_type__pk=sub.content_type.id).count() == 1:
                raise ValidationError("The only subject element of the resource con't be deleted.")
            sub.delete()
        else:
            raise ObjectDoesNotExist("No subject element was found for id:%d." % element_id)

class Source(AbstractMetaDataElement):
    term = 'Source'
    derived_from = models.CharField(max_length=300)

    def __unicode__(self):
        return self.derived_from

    @classmethod
    def create(cls, **kwargs):
        if 'derived_from' in kwargs:
            # check the source doesn't already exists - source needs to be unique per resource
            metadata_obj = kwargs['content_object']
            metadata_type = ContentType.objects.get_for_model(metadata_obj)
            src = Source.objects.filter(derived_from=kwargs['derived_from'], object_id=metadata_obj.id, content_type=metadata_type).first()
            if src:
                raise ValidationError('Source:%s already exists for this resource.' % kwargs['derived_from'])

            return Source.objects.create(**kwargs)

        else:
            raise ValidationError("Source data is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        src = Source.objects.get(id=element_id)
        if src:
            if 'derived_from' in kwargs:
                if src.derived_from != kwargs['derived_from']:
                    # check this new derived_from not already exists
                    if Source.objects.filter(derived_from__iexact=kwargs['derived_from'], object_id=src.object_id,
                                              content_type__pk=src.content_type.id).count()> 0:
                        raise ValidationError('Source:%s already exists for this resource.' % kwargs['value'])

                src.derived_from = kwargs['derived_from']
                src.save()
            else:
                raise ValidationError('Value for source is missing.')
        else:
            raise ObjectDoesNotExist("No source element was found for the provided id:%s" % element_id)

    @classmethod
    def remove(cls, element_id):
        src = Source.objects.get(id=element_id)
        if src:
            src.delete()
        else:
            raise ObjectDoesNotExist("No source element was found for id:%d." % element_id)

class Rights(AbstractMetaDataElement):
    term = 'Rights'
    statement = models.TextField(null=True, blank=True)
    url = models.URLField(null=True, blank=True)

    class Meta:
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        # the Meta class setting "unique-tigether' enforces that we have only one rights element per resource
        metadata_obj = kwargs['content_object']

        # in order to create a Rights element we need to have either a value for the statement field or a value for the url field
        if 'statement' in kwargs and 'url' in kwargs:
            return Rights.objects.create(statement=kwargs['statement'], url=kwargs['url'],  content_object=metadata_obj)

        elif 'url' in kwargs:
            return Rights.objects.create(url=kwargs['url'],  content_object=metadata_obj)

        elif 'statement' in kwargs:
            return Rights.objects.create(statement=kwargs['statement'],  content_object=metadata_obj)

        else:
            raise ValidationError("Statement and/or URL of rights is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        rights = Rights.objects.get(id=element_id)
        if rights:
            if 'statement' in kwargs:
                rights.statement = kwargs['statement']
            if 'url' in kwargs:
                rights.url = kwargs['url']
            rights.save()
        else:
            raise ObjectDoesNotExist("No rights element was found for the provided id:%s" % element_id)


    @classmethod
    def remove(cls, element_id):
        raise ValidationError("Rights element of a resource can't be deleted.")



def short_id():
    return uuid4().hex


from mezzanine.pages.managers import PageManager
class ResourceManager(PageManager):

    def __init__(self, resource_type=None, *args, **kwargs):
        self.resource_type = resource_type
        super(ResourceManager, self).__init__(*args, **kwargs)

    def create(self, *args, **kwargs):
        if self.resource_type is None:
            kwargs.pop('resource_type')
        return super(ResourceManager, self).create(*args, **kwargs)

    def get_queryset(self):
        qs = super(ResourceManager, self).get_queryset()
        if self.resource_type:
            qs = qs.filter(resource_type=self.resource_type)
        return qs


class AbstractResource(ResourcePermissionsMixin):
    """
    All hydroshare objects inherit from this mixin.  It defines things that must
    be present to be considered a hydroshare resource.  Additionally, all
    hydroshare resources should inherit from Page.  This gives them what they
    need to be represented in the Mezzanine CMS.

    In some cases, it is possible that the order of inheritence matters.  Best
    practice dictates that you list pages.Page first and then other classes:

        class MyResourceContentType(pages.Page, hs_core.AbstractResource):
            ...
    """

    content = models.TextField() # the field added for use by Django inplace editing
    last_changed_by = models.ForeignKey(User,
                                        help_text='The person who last changed the resource',
                                        related_name='last_changed_%(app_label)s_%(class)s',
                                        null=True
    )

    # dublin_metadata = generic.GenericRelation(
    #     'dublincore.QualifiedDublinCoreElement',
    #     help_text='The dublin core metadata of the resource'
    # )

    files = generic.GenericRelation('hs_core.ResourceFile', help_text='The files associated with this resource', for_concrete_model=False)
    bags = generic.GenericRelation('hs_core.Bags', help_text='The bagits created from versions of this resource', for_concrete_model=False)
    short_id = models.CharField(max_length=32, default=short_id, db_index=True)
    doi = models.CharField(max_length=1024, blank=True, null=True, db_index=True,
                           help_text='Permanent identifier. Never changes once it\'s been set.')
    comments = CommentsField()
    rating = RatingField()

    # this is to establish a relationship between a resource and
    # any metadata container object (e.g., CoreMetaData object)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    #keywords = KeywordsField(verbose_name="Keywords", for_concrete_model=False)

    @classmethod
    def bag_url(cls, resource_id):
        bagit_path = getattr(settings, 'IRODS_BAGIT_PATH', 'bags')
        bagit_postfix = getattr(settings, 'IRODS_BAGIT_POSTFIX', 'zip')

        bag_path = "{path}/{resource_id}.{postfix}".format(path=bagit_path,
                                                           resource_id=resource_id,
                                                           postfix=bagit_postfix)
        istorage = IrodsStorage()
        bag_url = istorage.url(bag_path)

        return bag_url

    def delete(self, using=None):
        from hydroshare import hs_bagit

        for fl in self.files.all():
            fl.resource_file.delete()

        hs_bagit.delete_bag(self)

        self.metadata.delete_all_elements()
        self.metadata.delete()

        super(AbstractResource, self).delete()

    # this property needs to be overriden by any specific resource type
    # that needs additional metadata elements on top of core metadata data elements
    @property
    def metadata(self):
        md = CoreMetaData() # only this line needs to be changed when you override
        return self._get_metadata(md)

    @property
    def first_creator(self):
        first_creator = self.metadata.creators.filter(order=1).first()
        return first_creator

    def _get_metadata(self, metatdata_obj):
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

    def extra_capabilites(self):
        """This is not terribly well defined yet, but should return at the least a JSON serializable object of URL
        endpoints where extra self-describing services exist and can be queried by the user in the form of
        { "name" : "endpoint" }
        """
        return None

    def get_citation(self):
        citation = ''

        CREATOR_NAME_ERROR = "Failed to generate citation - invalid creator name."
        CITATION_ERROR = "Failed to generate citation."

        first_author = self.metadata.creators.all().filter(order=1)[0]
        name_parts = first_author.name.split()
        if len(name_parts) == 0:
            citation = CREATOR_NAME_ERROR
            return citation

        if len(name_parts) > 2:
            citation = "{last_name}, {first_initial}.{middle_initial}.".format(last_name=name_parts[-1],
                                                                              first_initial=name_parts[0][0],
                                                                              middle_initial=name_parts[1][0]) + ", "
        else:
            citation = "{last_name}, {first_initial}.".format(last_name=name_parts[-1],
                                                              first_initial=name_parts[0][0]) + ", "

        other_authors = self.metadata.creators.all().filter(order__gt=1)
        for author in other_authors:
            name_parts = author.name.split()
            if len(name_parts) == 0:
                citation = CREATOR_NAME_ERROR
                return citation

            if len(name_parts) > 2:
                citation += "{first_initial}.{middle_initial}.{last_name}".format(first_initial=name_parts[0][0],
                                                                                  middle_initial=name_parts[1][0],
                                                                                  last_name=name_parts[-1]) + ", "
            else:
                citation += "{first_initial}.{last_name}".format(first_initial=name_parts[0][0],
                                                                 last_name=name_parts[-1]) + ", "

        #  remove the last added comma and the space
        if len(citation) > 2:
            citation = citation[:-2]
        else:
            return CITATION_ERROR

        if self.metadata.dates.all().filter(type='published'):
            citation_date = self.metadata.dates.all().filter(type='published')[0]
        elif self.metadata.dates.all().filter(type='modified'):
            citation_date = self.metadata.dates.all().filter(type='modified')[0]
        else:
            return CITATION_ERROR

        citation += " ({year}). ".format(year=citation_date.start_date.year)
        citation += self.title
        citation += ", HydroShare, "

        if self.metadata.identifiers.all().filter(name="doi"):
            hs_identifier = self.metadata.identifiers.all().filter(name="doi")[0]
        elif self.metadata.identifiers.all().filter(name="hydroShareIdentifier"):
            hs_identifier = self.metadata.identifiers.all().filter(name="hydroShareIdentifier")[0]
        else:
            return CITATION_ERROR

        citation += "{url}".format(url=hs_identifier.url)

        return citation

    @property
    def can_be_public(self):
        if self.metadata.has_all_required_elements():
            return True

        return False

    @classmethod
    def get_supported_upload_file_types(cls):
        # NOTES FOR ANY SUBCLASS OF THIS CLASS TO OVERRIDE THIS FUNCTION:
        # to allow only specific file types return a tuple of those file extensions (ex: return (".csv", ".txt",))
        # to not allow any file upload, return a empty tuple ( return ())

        # by default all file types are supported
        return (".*",)


    @classmethod
    def can_have_multiple_files(cls):
        # NOTES FOR ANY SUBCLASS OF THIS CLASS TO OVERRIDE THIS FUNCTION:
        # to allow resource to have only 1 file or no file, return False

        # resource by default can have multiple files
        return True


    class Meta:
        abstract = True
        unique_together = ("content_type", "object_id")

def get_path(instance, filename):
    return os.path.join(instance.content_object.short_id, 'data', 'contents', filename)

class ResourceFile(models.Model):
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)

    content_object = generic.GenericForeignKey('content_type', 'object_id')
    resource_file = models.FileField(upload_to=get_path, max_length=500, storage=IrodsStorage() if getattr(settings,'USE_IRODS', False) else DefaultStorage())

class Bags(models.Model):
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)

    content_object = generic.GenericForeignKey('content_type', 'object_id', for_concrete_model=False)
    timestamp = models.DateTimeField(default=now, db_index=True)

    class Meta:
        ordering = ['-timestamp']


# remove RichText parent class from the parameters for Django inplace editing to work; otherwise, get internal edit error when saving changes
class BaseResource(Page, AbstractResource):

    resource_type = models.CharField(max_length=50, default="GenericResource")

    class Meta:
        verbose_name = 'Generic'
        db_table = 'hs_core_genericresource'

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)


    @classmethod
    def get_supported_upload_file_types(cls):
        # all file types are supported
        return ('.*')

    @classmethod
    def can_have_multiple_files(cls):
        return True

    @classmethod
    def can_have_files(cls):
        return True


class GenericResource(BaseResource):
    objects = ResourceManager('GenericResource')

    class Meta:
        proxy = True

# This model has a one-to-one relation with the AbstractResource model
class CoreMetaData(models.Model):
    #from django.contrib.sites.models import Site
    #_domain = 'hydroshare.org'  #Site.objects.get_current() # this one giving error since the database does not have a related table called 'django_site'

    XML_HEADER = '''<?xml version="1.0"?>
<!DOCTYPE rdf:RDF PUBLIC "-//DUBLIN CORE//DCMES DTD 2002/07/31//EN"
"http://dublincore.org/documents/2002/07/31/dcmes-xml/dcmes-xml-dtd.dtd">'''

    NAMESPACES = {'rdf':"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                  'dc': "http://purl.org/dc/elements/1.1/",
                  'dcterms':"http://purl.org/dc/terms/",
                  'hsterms': "http://hydroshare.org/terms/"}

    DATE_FORMAT = "YYYY-MM-DDThh:mm:ssTZD"
    #HYDROSHARE_URL = 'http://%s' % _domain

    id = models.AutoField(primary_key=True)

    _description = generic.GenericRelation(Description)    # resource abstract
    _title = generic.GenericRelation(Title)
    creators = generic.GenericRelation(Creator)
    contributors = generic.GenericRelation(Contributor)
    dates = generic.GenericRelation(Date)
    coverages = generic.GenericRelation(Coverage)
    formats = generic.GenericRelation(Format)
    identifiers = generic.GenericRelation(Identifier)
    _language = generic.GenericRelation(Language)
    subjects = generic.GenericRelation(Subject)
    sources = generic.GenericRelation(Source)
    relations = generic.GenericRelation(Relation)
    _rights = generic.GenericRelation(Rights)
    _type = generic.GenericRelation(Type)
    _publisher = generic.GenericRelation(Publisher)

    @property
    def title(self):
        return self._title.all().first()

    @property
    def description(self):
        return self._description.all().first()

    @property
    def language(self):
        return self._language.all().first()

    @property
    def rights(self):
        return self._rights.all().first()

    @property
    def type(self):
        return self._type.all().first()

    @property
    def publisher(self):
        return self._publisher.all().first()

    @classmethod
    def get_supported_element_names(cls):
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
                'Publisher']

    # this method needs to be overriden by any subclass of this class
    # if they implement additional metadata elements that are required
    def has_all_required_elements(self):
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

        # if self.coverages.count() == 0:
        #     return False

        if self.subjects.count() == 0:
            return False

        return True

    # this method needs to be overriden by any subclass of this class
    # if they implement additional metadata elements that are required
    def get_required_missing_elements(self):
        missing_required_elements = []

        if not self.title:
            missing_required_elements.append('Title')
        if not self.description:
            missing_required_elements.append('Abstract')
        if not self.rights:
            missing_required_elements.append('Rights')
        if self.subjects.count() == 0:
            missing_required_elements.append('Keywords')

        return missing_required_elements

    # this method needs to be overriden by any subclass of this class
    def delete_all_elements(self):
        if self.title: self.title.delete()
        if self.description: self.description.delete()
        if self.language: self.language.delete()
        if self.rights: self.rights.delete()
        if self.publisher: self.publisher.delete()
        if self.type: self.type.delete()

        self.creators.all().delete()
        self.contributors.all().delete()
        self.dates.all().delete()
        self.identifiers.all().delete()
        self.coverages.all().delete()
        self.formats.all().delete()
        self.subjects.all().delete()
        self.sources.all().delete()
        self.relations.all().delete()

    def get_xml(self, pretty_print=True):
        from lxml import etree
        import arrow
        RDF_ROOT = etree.Element('{%s}RDF' % self.NAMESPACES['rdf'], nsmap=self.NAMESPACES)
        # create the Description element -this is not exactly a dc element
        rdf_Description = etree.SubElement(RDF_ROOT, '{%s}Description' % self.NAMESPACES['rdf'])

        #resource_uri = self.HYDROSHARE_URL + '/resource/' + self.resource.short_id
        resource_uri = self.identifiers.all().filter(name='hydroShareIdentifier')[0].url
        rdf_Description.set('{%s}about' % self.NAMESPACES['rdf'], resource_uri)

        # create the title element
        if self.title:
            dc_title = etree.SubElement(rdf_Description, '{%s}title' % self.NAMESPACES['dc'])
            dc_title.text = self.title.value

        # create the type element
        if self.type:
            dc_type = etree.SubElement(rdf_Description, '{%s}type' % self.NAMESPACES['dc'])
            dc_type.set('{%s}resource' % self.NAMESPACES['rdf'], self.type.url)

        # create the Description element (we named it as Abstract to differentiate from the parent "Description" element)
        if self.description:
            dc_description = etree.SubElement(rdf_Description, '{%s}description' % self.NAMESPACES['dc'])
            dc_des_rdf_Desciption = etree.SubElement(dc_description, '{%s}Description' % self.NAMESPACES['rdf'])
            dcterms_abstract = etree.SubElement(dc_des_rdf_Desciption, '{%s}abstract' % self.NAMESPACES['dcterms'])
            dcterms_abstract.text = self.description.abstract

        # use all creators associated with this metadata object to
        # generate creator xml elements
        for creator in self.creators.all():
            self._create_person_element(etree, rdf_Description, creator)

        for contributor in self.contributors.all():
            self._create_person_element(etree, rdf_Description, contributor)

        for coverage in self.coverages.all():
            dc_coverage = etree.SubElement(rdf_Description, '{%s}coverage' % self.NAMESPACES['dc'])
            cov_dcterm = '{%s}' + coverage.type
            dc_coverage_dcterms = etree.SubElement(dc_coverage, cov_dcterm % self.NAMESPACES['dcterms'])
            rdf_coverage_value = etree.SubElement(dc_coverage_dcterms, '{%s}value' % self.NAMESPACES['rdf'])
            if coverage.type == 'period':
                cov_value = 'start=%s; end=%s; scheme=W3C-DTF' % (arrow.get(coverage.value['start'].format(self.DATE_FORMAT)),
                                                          arrow.get(coverage.value['end'].format(self.DATE_FORMAT)))
                if 'name' in coverage.value:
                    cov_value = 'name=%s; ' % coverage.value['name'] + cov_value

            elif coverage.type == 'point':
                cov_value = 'east=%s; north=%s; units=%s' % (coverage.value['east'], coverage.value['north'],
                                                  coverage.value['units'])
                if 'name' in coverage.value:
                    cov_value = 'name=%s; ' % coverage.value['name'] + cov_value
                if 'elevation' in coverage.value:
                    cov_value = cov_value + '; elevation=%s' % coverage.value['elevation']
                    if 'zunits' in coverage.value:
                        cov_value = cov_value + '; zunits=%s' % coverage.value['zunits']
                if 'projection' in coverage.value:
                    cov_value = cov_value + '; projection=%s' % coverage.value['projection']

            else: # this is box type
                cov_value = 'northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s; units=%s' \
                            %(coverage.value['northlimit'], coverage.value['eastlimit'],
                              coverage.value['southlimit'], coverage.value['westlimit'], coverage.value['units'])

                if 'name' in coverage.value:
                    cov_value = 'name=%s; ' % coverage.value['name'] + cov_value
                if 'uplimit' in coverage.value:
                    cov_value = cov_value + '; uplimit=%s' % coverage.value['uplimit']
                if 'downlimit' in coverage.value:
                    cov_value = cov_value + '; downlimit=%s' % coverage.value['downlimit']
                if 'uplimit' in coverage.value or 'downlimit' in coverage.value:
                    cov_value = cov_value + '; zunits=%s' % coverage.value['zunits']
                if 'projection' in coverage.value:
                    cov_value = cov_value + '; projection=%s' % coverage.value['projection']

            rdf_coverage_value.text = cov_value

        for dt in self.dates.all():
            dc_date = etree.SubElement(rdf_Description, '{%s}date' % self.NAMESPACES['dc'])
            dc_term = '{%s}'+ dt.type
            dc_date_dcterms = etree.SubElement(dc_date, dc_term % self.NAMESPACES['dcterms'])
            rdf_date_value = etree.SubElement(dc_date_dcterms, '{%s}value' % self.NAMESPACES['rdf'])
            if dt.type != 'valid':
                rdf_date_value.text = arrow.get(dt.start_date).format(self.DATE_FORMAT)
            else:
                if dt.end_date:
                    rdf_date_value.text = "start=%s; end=%s" % (arrow.get(dt.start_date).format(self.DATE_FORMAT), arrow.get(dt.end_date).format(self.DATE_FORMAT))
                else:
                    rdf_date_value.text = arrow.get(dt.start_date).format(self.DATE_FORMAT)

        for fmt in self.formats.all():
            dc_format = etree.SubElement(rdf_Description, '{%s}format' % self.NAMESPACES['dc'])
            dc_format.text = fmt.value

        for res_id in self.identifiers.all():
            dc_identifier = etree.SubElement(rdf_Description, '{%s}identifier' % self.NAMESPACES['dc'])
            dc_id_rdf_Description = etree.SubElement(dc_identifier, '{%s}Description' % self.NAMESPACES['rdf'])
            id_hsterm = '{%s}' + res_id.name
            hsterms_hs_identifier = etree.SubElement(dc_id_rdf_Description, id_hsterm % self.NAMESPACES['hsterms'])
            hsterms_hs_identifier.text = res_id.url

        if self.language:
            dc_lang = etree.SubElement(rdf_Description, '{%s}language' % self.NAMESPACES['dc'])
            dc_lang.text = self.language.code

        if self.publisher:
            dc_publisher = etree.SubElement(rdf_Description, '{%s}publisher' % self.NAMESPACES['dc'])
            dc_pub_rdf_Description = etree.SubElement(dc_publisher, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_pub_name = etree.SubElement(dc_pub_rdf_Description, '{%s}publisherName' % self.NAMESPACES['hsterms'])
            hsterms_pub_name.text = self.publisher.name
            hsterms_pub_url = etree.SubElement(dc_pub_rdf_Description, '{%s}publisherURL' % self.NAMESPACES['hsterms'])
            hsterms_pub_url.set('{%s}resource' % self.NAMESPACES['rdf'], self.publisher.url)

        for rel in self.relations.all():
            dc_relation = etree.SubElement(rdf_Description, '{%s}relation' % self.NAMESPACES['dc'])
            dc_rel_rdf_Description = etree.SubElement(dc_relation, '{%s}Description' % self.NAMESPACES['rdf'])
            rel_dcterm = '{%s}' + rel.type
            dcterms_type = etree.SubElement(dc_rel_rdf_Description, rel_dcterm % self.NAMESPACES['dcterms'])
            # check if the relation value starts with 'http://' or 'https://'
            if rel.value.lower().find('http://') == 0 or rel.value.lower().find('https://') == 0:
                dcterms_type.set('{%s}resource' % self.NAMESPACES['rdf'], rel.value)
            else:
                dcterms_type.text = rel.value

        for src in self.sources.all():
            dc_source = etree.SubElement(rdf_Description, '{%s}source' % self.NAMESPACES['dc'])
            dc_source_rdf_Description = etree.SubElement(dc_source, '{%s}Description' % self.NAMESPACES['rdf'])
            dcterms_derived_from = etree.SubElement(dc_source_rdf_Description, '{%s}isDerivedFrom' % self.NAMESPACES['dcterms'])
            # if the source value starts with 'http://' or 'https://' add value as an attribute
            if src.derived_from.lower().find('http://') == 0 or src.derived_from.lower().find('https://') == 0:
                dcterms_derived_from.set('{%s}resource' % self.NAMESPACES['rdf'], src.derived_from)
            else:
                dcterms_derived_from.text = src.derived_from

        if self.rights:
            dc_rights = etree.SubElement(rdf_Description, '{%s}rights' % self.NAMESPACES['dc'])
            dc_rights_rdf_Description = etree.SubElement(dc_rights, '{%s}Description' % self.NAMESPACES['rdf'])
            hsterms_statement = etree.SubElement(dc_rights_rdf_Description, '{%s}rightsStatement' % self.NAMESPACES['hsterms'])
            hsterms_statement.text = self.rights.statement
            if self.rights.url:
                hsterms_url = etree.SubElement(dc_rights_rdf_Description, '{%s}URL' % self.NAMESPACES['hsterms'])
                hsterms_url.set('{%s}resource' % self.NAMESPACES['rdf'], self.rights.url)

        for sub in self.subjects.all():
            dc_subject = etree.SubElement(rdf_Description, '{%s}subject' % self.NAMESPACES['dc'])
            if sub.value.lower().find('http://') == 0 or sub.value.lower().find('https://') == 0:
                dc_subject.set('{%s}resource' % self.NAMESPACES['rdf'], sub.value)
            else:
                dc_subject.text = sub.value

        return self.XML_HEADER + '\n' + etree.tostring(RDF_ROOT, pretty_print=pretty_print)

    def add_metadata_element_to_xml(self, root, md_element, md_fields):
        from lxml import etree

        hsterms_newElem = etree.SubElement(root,
                                           "{{{ns}}}{new_element}".format(ns=self.NAMESPACES['hsterms'], new_element=md_element.term))
        hsterms_newElem_rdf_Desc = etree.SubElement(hsterms_newElem,
                                                    "{{{ns}}}Description".format(ns=self.NAMESPACES['rdf']))
        for md_field in md_fields:
            if hasattr(md_element, md_field):
                attr = getattr(md_element, md_field)
                if attr:
                    field = etree.SubElement(hsterms_newElem_rdf_Desc,
                                             "{{{ns}}}{field}".format(ns=self.NAMESPACES['hsterms'],
                                                                  field=md_field))
                    field.text = str(attr)

    def _create_person_element(self, etree, parent_element, person):

        # importing here to avoid circular import problem
        from hydroshare.utils import current_site_url

        if isinstance(person, Creator):
            dc_person = etree.SubElement(parent_element, '{%s}creator' % self.NAMESPACES['dc'])
        else:
            dc_person = etree.SubElement(parent_element, '{%s}contributor' % self.NAMESPACES['dc'])

        dc_person_rdf_Description = etree.SubElement(dc_person, '{%s}Description' % self.NAMESPACES['rdf'])

        hsterms_name = etree.SubElement(dc_person_rdf_Description, '{%s}name' % self.NAMESPACES['hsterms'])
        hsterms_name.text = person.name
        if person.description:
            dc_person_rdf_Description.set('{%s}about' % self.NAMESPACES['rdf'], current_site_url() + person.description)

        if isinstance(person, Creator):
            hsterms_creatorOrder = etree.SubElement(dc_person_rdf_Description, '{%s}creatorOrder' % self.NAMESPACES['hsterms'])
            hsterms_creatorOrder.text = str(person.order)

        if person.organization:
            hsterms_organization = etree.SubElement(dc_person_rdf_Description, '{%s}organization' % self.NAMESPACES['hsterms'])
            hsterms_organization.text = person.organization

        if person.email:
            hsterms_email = etree.SubElement(dc_person_rdf_Description, '{%s}email' % self.NAMESPACES['hsterms'])
            hsterms_email.text = person.email

        if person.address:
            hsterms_address = etree.SubElement(dc_person_rdf_Description, '{%s}address' % self.NAMESPACES['hsterms'])
            hsterms_address.text = person.address

        if person.phone:
            hsterms_phone = etree.SubElement(dc_person_rdf_Description, '{%s}phone' % self.NAMESPACES['hsterms'])
            hsterms_phone.set('{%s}resource' % self.NAMESPACES['rdf'], 'tel:' + person.phone)

        if person.homepage:
            hsterms_homepage = etree.SubElement(dc_person_rdf_Description, '{%s}homepage' % self.NAMESPACES['hsterms'])
            hsterms_homepage.set('{%s}resource' % self.NAMESPACES['rdf'], person.homepage)

        for link in person.external_links.all():
            hsterms_link_type = etree.SubElement(dc_person_rdf_Description, '{%s}' % self.NAMESPACES['hsterms'] + link.type)
            hsterms_link_type.set('{%s}resource' % self.NAMESPACES['rdf'], link.url)

    def create_element(self, element_model_name, **kwargs):
        element_model_name = element_model_name.lower()
        if not self._is_valid_element(element_model_name):
            raise ValidationError("Metadata element type:%s is not one of the supported in core metadata elements."
                                  % element_model_name)

        try:
            model_type = ContentType.objects.get(app_label=self._meta.app_label, model=element_model_name)
        except ObjectDoesNotExist:
            model_type = ContentType.objects.get(app_label='hs_core', model=element_model_name)

        if model_type:
            if issubclass(model_type.model_class(), AbstractMetaDataElement):
                kwargs['content_object'] = self
                element = model_type.model_class().create(**kwargs)
                element.save()
                return element
            else:
                raise ValidationError("Metadata element type:%s is not supported." % element_model_name)
        else:
            raise ValidationError("Metadata element type:%s is not supported." % element_model_name)

    def update_element(self, element_model_name, element_id, **kwargs):
        element_model_name = element_model_name.lower()
        try:
            model_type = ContentType.objects.get(app_label=self._meta.app_label, model=element_model_name)
        except ObjectDoesNotExist:
            model_type = ContentType.objects.get(app_label='hs_core', model=element_model_name)

        if model_type:
            if issubclass(model_type.model_class(), AbstractMetaDataElement):
                kwargs['content_object']= self
                model_type.model_class().update(element_id, **kwargs)
            else:
                raise ValidationError("Metadata element type:%s is not supported." % element_model_name)
        else:
            raise ValidationError("Metadata element type:%s is not supported." % element_model_name)

    def delete_element(self, element_model_name, element_id):
        element_model_name = element_model_name.lower()
        try:
            model_type = ContentType.objects.get(app_label=self._meta.app_label, model=element_model_name)
        except ObjectDoesNotExist:
            model_type = ContentType.objects.get(app_label='hs_core', model=element_model_name)

        if model_type:
            if issubclass(model_type.model_class(), AbstractMetaDataElement):
                model_type.model_class().remove(element_id)
            else:
                raise ValidationError("Metadata element type:%s is not supported." % element_model_name)
        else:
            raise ValidationError("Metadata element type:%s is not supported." % element_model_name)

    def _is_valid_element(self, element_name):
        allowed_elements = [el.lower() for el in self.get_supported_element_names()]
        return element_name.lower() in allowed_elements

def resource_processor(request, page):
    extra = page_permissions_page_processor(request, page)
    extra['res'] = page.get_content_model()
    #extra['dc'] = { m.term_name : m.content for m in extra['res'].dublin_metadata.all() }
    return extra


@receiver(post_save)
def resource_creation_signal_handler(sender, instance, created, **kwargs):
    """Create initial dublin core elements"""
    if isinstance(instance, AbstractResource):
        if created:
            pass
            # from hs_core.hydroshare import utils
            # import json
            # instance.metadata.create_element('title', value=instance.title)
            # if instance.content:
            #     instance.metadata.create_element('description', abstract=instance.content)
            # else:
            #     instance.metadata.create_element('description', abstract=instance.description)

            # TODO: With the current VM the get_user_info() method fails. So we can't get the resource uri for
            # the user now.
            # creator_dict = users.get_user_info(instance.creator)
            # instance.metadata.create_element('creator', name=instance.creator.get_full_name(),
            #                                  email=instance.creator.email,
            #                                  description=creator_dict['resource_uri'])

            #instance.metadata.create_element('creator', name=instance.creator.get_full_name(), email=instance.creator.email)

            # TODO: The element 'Type' can't be created as we do not have an URI for specific resource types yet

            # instance.metadata.create_element('date', type='created', start_date=instance.created)
            # instance.metadata.create_element('date', type='modified', start_date=instance.updated)

            # res_json = utils.serialize_science_metadata(instance)
            # res_dict = json.loads(res_json)
            #instance.metadata.create_element('identifier', name='hydroShareIdentifier', url='http://hydroshare.org/resource{0}{1}'.format('/', instance.short_id))
            instance.set_slug('resource{0}{1}'.format('/', instance.short_id))
        else:
            resource_update_signal_handler(sender, instance, created, **kwargs)

    if isinstance(AbstractResource, sender):
        if created:
            instance.dublin_metadata.create(term='T', content=instance.title)
            instance.dublin_metadata.create(term='CR', content=instance.user.username)
            if instance.last_updated_by:
                instance.dublin_metadata.create(term='CN', content=instance.last_updated_by.username)
            instance.dublin_metadata.create(term='DT', content=instance.created)
            if instance.content:
                instance.dublin_metadata.create(term='AB', content=instance.content)
        else:
            resource_update_signal_handler(sender, instance, created, **kwargs)


def resource_update_signal_handler(sender, instance, created, **kwargs):
    """Add dublin core metadata based on the person who just updated the resource. Handle publishing too..."""

@receiver(post_save, sender=User)
def user_creation_signal_handler(sender, instance, created, **kwargs):
    if created:
        if not instance.is_staff:
            instance.is_staff = True
            instance.save()
            instance.groups.add(Group.objects.get(name='Hydroshare Author'))

# this import statement is necessary in models.py to receive signals
# any hydroshare app that needs to listen to signals from hs_core also needs to
# implement the appropriate signal handlers in receivers.py and then include this import statement
# in the app's models.py as the last line of code
import receivers
