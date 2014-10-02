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
from mezzanine.generic.fields import CommentsField
from mezzanine.conf import settings as s
from mezzanine.generic.models import Keyword, AssignedKeyword
import os.path
from django_irods.storage import IrodsStorage
# from dublincore.models import QualifiedDublinCoreElement
from dublincore import models as dc
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from languages_iso import languages as iso_languages
from dateutil import parser
from django.utils import simplejson as json

class GroupOwnership(models.Model):
    group = models.ForeignKey(Group)
    owner = models.ForeignKey(User)


def get_user(request):
    """authorize user based on API key if it was passed, otherwise just use the request's user.

    :param request:
    :return: django.contrib.auth.User
    """

    from tastypie.models import ApiKey

    if 'api_key' in request.REQUEST:
        api_key = ApiKey.objects.get(key=request.REQUEST['api_key'])
        return api_key.user
    elif request.user.is_authenticated():
        return User.objects.get(pk=request.user.pk)
    else:
        return request.user

class ResourcePermissionsMixin(Ownable):
    creator = models.ForeignKey(User,
                                related_name='creator_of_%(app_label)s_%(class)s',
                                help_text='This is the person who first uploaded the resource',
                                )

    public = models.BooleanField(
        help_text='If this is true, the resource is viewable and downloadable by anyone',
        default=True
    )
    # DO WE STILL NEED owners?
    owners = models.ManyToManyField(User,
                                    related_name='owns_%(app_label)s_%(class)s',
                                    help_text='The person who uploaded the resource'
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
        return self.can_change(request)

    def can_change(self, request):
        user = get_user(request)

        if user.is_authenticated():
            if not self.user:
                ret = user.is_superuser
            elif user.pk == self.creator.pk:
                ret = True
            elif user.pk in { o.pk for o in self.owners.all() }:
                ret = True
            elif self.edit_users.filter(pk=user.pk).exists():
                ret = True
            elif self.edit_groups.filter(pk__in=set(g.pk for g in user.groups.all())):
                ret = True
            else:
                ret = False
        else:
            ret = False

        return ret


    def can_view(self, request):
        user = get_user(request)

        if self.public:
            return True
        if user.is_authenticated():
            if not self.user:
                ret = user.is_superuser
            elif user.pk == self.creator.pk:
                ret = True
            elif user.pk in { o.pk for o in self.owners.all() }:
                ret = True
            elif self.view_users.filter(pk=user.pk).exists():
                ret = True
            elif self.view_groups.filter(pk__in=set(g.pk for g in user.groups.all())):
                ret = True
            else:
                ret = False
        else:
            ret = False

        return ret




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
        "can_edit": (user in set(page.edit_users.all())) \
                    or (len(set(page.edit_groups.all()).intersection(set(user.groups.all()))) > 0)
    }

class AbstractMetaDataElement(models.Model):
    term = None

    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)
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

class ExternalProfileLink(models.Model):
    type = models.CharField(max_length=50)
    url = models.URLField()

    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ("type", "url", "content_type")

class Party(AbstractMetaDataElement):
    description = models.URLField(null=True, blank=True)
    name = models.CharField(max_length=100)
    organization = models.CharField(max_length=200, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    phone = models.CharField(max_length=25, null=True, blank=True)
    homepage = models.URLField(null=True, blank=True)
    researcherID = models.URLField(null=True, blank=True)
    researchGateID = models.URLField(null=True, blank=True)
    external_links = generic.GenericRelation(ExternalProfileLink)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True

    @classmethod
    def create(cls,**kwargs):
        element_name = cls.__name__
        if 'name' in kwargs:
            if 'metadata_obj' in kwargs:
                if not isinstance(kwargs['metadata_obj'], CoreMetaData) and not issubclass(kwargs['metadata_obj'], CoreMetaData):
                    raise ValidationError("%s metadata element can't be created for metadata type:%s" %(element_name, type(kwargs['metadata_obj'])))

                metadata_obj = kwargs['metadata_obj']
                metadata_type = ContentType.objects.get_for_model(metadata_obj)
                if element_name == 'Creator':
                    party = Creator.objects.filter(object_id=metadata_obj.id, content_type=metadata_type).last()
                    creator_order = 1
                    if party:
                        creator_order = party.order + 1
                    party = Creator.objects.create(name=kwargs['name'], order=creator_order, content_object=metadata_obj)
                else:
                    party = Contributor.objects.create(name=kwargs['name'], content_object=metadata_obj)

                if 'profile_links' in kwargs:
                    links = kwargs['profile_links']
                    for link in links:
                        cls._create_profile_link(party, link)
            else:
                raise ValidationError("Metadata container object for which metadata element 'Creator' to be created is missing.")

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
                    if kwargs['order'] == 0:
                        kwargs['order'] = 1

                    if party.order != kwargs['order']:
                        resource_creators = Creator.objects.filter(object_id=party.object_id, content_type__pk=party.content_type.id).all()

                        if kwargs['order'] > len(resource_creators):
                            kwargs['order'] = len(resource_creators)

                        for res_cr in resource_creators:
                            if party.order > kwargs['order']:
                                if res_cr.order < party.order:
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
    abstract = models.CharField(max_length=500)

    def __unicode__(self):
        return self.abstract

    class Meta:
        unique_together = ("content_type", "object_id")

    @classmethod
    def create(cls, **kwargs):
        if 'abstract' in kwargs:
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
                # no need to check if a description element already exists
                # the Meta settings 'unique_together' will enforce that we have only one description element per resource
                description = Description.objects.create(abstract=kwargs['abstract'], content_object=metadata_obj)
                return description
            else:
                raise ValidationError('Metadata instance for which description element to be created is missing.')
        else:
            raise ValidationError("Abstract of the description element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        description = Description.objects.get(id=element_id)
        if description:
            if 'abstract' in kwargs:
                description.abstract = kwargs['abstract']
                description.save()
            else:
                raise ValidationError('Abstract for description element is missing.')
        else:
            raise ObjectDoesNotExist("No description element was found for the provided id:%s" % element_id)

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
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
                title = Title.objects.create(value=kwargs['value'], content_object=metadata_obj)
                return title
            else:
                raise ValidationError('Metadata instance for which title element to be created is missing.')
        else:
            raise ValidationError("Value of the title element is missing.")

    @classmethod
    def update(cls, element_id, **kwargs):
        title = Title.objects.get(id=element_id)
        if title:
            if 'value' in kwargs:
                title.value = kwargs['value']
                title.save()
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
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
                type = Type.objects.create(url=kwargs['url'], content_object=metadata_obj)
                return type
            else:
                raise ValidationError('Metadata instance for which type element to be created is missing.')
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
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
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
                raise ValidationError('Metadata instance for which date element to be created is missing.')
        else:
            raise ValidationError("Type of date element is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        dt = Date.objects.get(id=element_id)
        metadata_obj = kwargs['metadata_obj']
        if dt:
            if 'start_date' in kwargs:
                try:
                    start_dt = parser.parse(str(kwargs['start_date']))
                except TypeError:
                    raise TypeError("Not a valid date value.")
                if dt.type == 'created':
                    raise ValidationError("Resource creation date can't be changed")
                elif dt.type == 'modified':
                    dt.start_date = metadata_obj.resource.updated
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
    )

    term = 'Relation'
    type = models.CharField(max_length=100, choices=SOURCE_TYPES)
    value = models.CharField(max_length=500)

    @classmethod
    def create(cls, **kwargs):
        if 'type' in kwargs:
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
                metadata_type = ContentType.objects.get_for_model(metadata_obj)
                rel = Relation.objects.filter(type= kwargs['type'], object_id=metadata_obj.id, content_type=metadata_type).first()
                if rel:
                    raise ValidationError('Relation type:%s already exists.' % kwargs['type'])
                if 'value' in kwargs:
                    rel = Relation.objects.create(type=kwargs['type'], value=kwargs['value'], content_object=metadata_obj)
                    return rel
                else:
                    raise ValidationError('Value for relation element is missing.')
            else:
                raise ValidationError('Metadata instance for which relation element to be created is missing.')
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
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
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
                raise ValidationError('Metadata instance for which date element to be created is missing.')
        else:
            raise ValidationError("Name of identifier element is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        idf = Identifier.objects.get(id=element_id)
        if idf:
            if 'name' in kwargs:
                if idf.name.lower() != kwargs['name'].lower():
                    if idf.name.lower() == 'hydroshareidentifier':
                        raise  ValidationError("Identifier name 'hydroshareIdentifier' can't be changed.")

                    if idf.name.lower() == 'doi':
                        raise  ValidationError("Identifier name 'DOI' can't be changed.")

                    # check this new identifier name not already exists
                    if Identifier.objects.filter(name__iexact=kwargs['name'], object_id=idf.object_id,
                                              content_type__pk=idf.content_type.id).count()> 0:
                        raise ValidationError('Identifier name:%s already exists.' % kwargs['name'])

                    idf.name = kwargs['name']

            if 'url' in kwargs:
                if idf.url.lower() != kwargs['url'].lower():
                    if idf.url.lower().find('http://hydroshare.org/resource') == 0:
                        raise  ValidationError("Hydroshare identifier url value can't be changed.")
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
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
                if 'url' in kwargs:
                    if not metadata_obj.resource.public and metadata_obj.resource.published_and_frozen:
                        raise ValidationError("Publisher element can't be created for a resource that is not shared nor published.")
                    if kwargs['name'].lower() == 'hydroshare':
                        if not  metadata_obj.resource.files.all():
                            raise ValidationError("Hydroshare can't be the publisher for a resource that has no content files.")
                        else:
                            kwargs['name'] = 'HydroShare'
                            kwargs['url'] = 'http://hydroshare.org'
                    pub = Publisher.objects.create(name=kwargs['name'], url=kwargs['url'], content_object=metadata_obj)
                    return pub
                else:
                    raise ValidationError('URL for the publisher is missing.')
            else:
                raise ValidationError('Metadata instance for which publisher element to be created is missing.')
        else:
            raise ValidationError("Name of publisher is missing.")


    @classmethod
    def update(cls, element_id, **kwargs):
        pub = Publisher.objects.get(id=element_id)
        if 'metadata_obj' in kwargs:
            metadata_obj = kwargs['metadata_obj']
        else:
            raise ValidationError('Metadata instance for which publisher element to be updated is missing.')

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
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
                metadata_type = ContentType.objects.get_for_model(metadata_obj)
                lang = Language.objects.filter(object_id=metadata_obj.id, content_type=metadata_type).first()
                if lang:
                    raise ValidationError('Language element already exists.')
            else:
                raise ValidationError('Metadata instance for which langauge element to be created is missing.')

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
         _value = "{'name':coverage name value here, 'start':start date value, 'end':end date value, 'scheme':'W3C-DTF}"

     For coverage type: point
         _value = "{'name':coverage name value here, 'east':east coordinate value, 'north':north coordinate value}"

     For coverage type: box
         _value = "{'name':coverage name value here, 'northlimit':northenmost coordinate value,
                    'eastlimit':easternmost coordinate value, 'southlimit':southernmost coordinate value,
                    'westlimit':westernmost coordinate value}"
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
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
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
                        if not 'name' in kwargs['value']:
                            raise ValidationError("Coverage name attribute is missing.")

                        cls._validate_coverage_type_value_attributes(kwargs['type'], kwargs['value'])

                        if kwargs['type']== 'period':
                            value_dict = {k: v for k, v in kwargs['value'].iteritems() if k in ('name', 'start', 'end')}
                        elif kwargs['type']== 'point':
                            value_dict = {k: v for k, v in kwargs['value'].iteritems() if k in ('name', 'east', 'north')}
                        elif kwargs['type']== 'box':
                            value_dict = {k: v for k, v in kwargs['value'].iteritems()
                                          if k in ('name','northlimit', 'eastlimit', 'southlimit', 'westlimit')}

                        value_json = json.dumps(value_dict)
                        cov = Coverage.objects.create(type=kwargs['type'], _value=value_json,
                                                      content_object=metadata_obj)
                        return cov
                    else:
                        raise ValidationError('Invalid coverage value format.')
                else:
                    raise ValidationError('Coverage value is missing.')
            else:
                raise ValidationError('Metadata instance for which date element to be created is missing.')
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
                if  not isinstance(kwargs['value'], dict):
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
                    for item_name in ('east', 'north'):
                        if item_name in kwargs['value']:
                            value_dict[item_name] = kwargs['value'][item_name]
                elif cov.type == 'box':
                    for item_name in ('northlimit', 'eastlimit', 'southlimit', 'westlimit'):
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
        if coverage_type== 'period':
            if not 'start' in value_dict or not 'end' in value_dict:
                raise ValidationError("For coverage of type 'period' values for start date and end date needed.")
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
        elif coverage_type== 'point':
            if not 'east' in value_dict or not 'north' in value_dict:
                raise ValidationError("For coverage of type 'period' values for both start date and end date are needed.")
        elif coverage_type== 'box':
            for value_item in ['name','northlimit', 'eastlimit', 'southlimit', 'westlimit']:
                if not value_item in value_dict:
                    raise ValidationError("For coverage of type 'box' values for one or more bounding box limits is missing.")

class Format(AbstractMetaDataElement):
    term = 'Format'
    value = models.CharField(max_length=50)

    def __unicode__(self):
        return self.value

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs:
            # check the format doesn't already exists - format values need to be unique per resource
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
                metadata_type = ContentType.objects.get_for_model(metadata_obj)
                format = Format.objects.filter(value__iexact= kwargs['value'], object_id=metadata_obj.id, content_type=metadata_type).first()
                if format:
                    raise ValidationError('Format:%s already exists' % kwargs['value'])

                format = Format.objects.create(value=kwargs['value'], content_object=metadata_obj)
                return format
            else:
                raise ValidationError('Metadata instance for which format element to be created is missing.')
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
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
                metadata_type = ContentType.objects.get_for_model(metadata_obj)
                sub = Subject.objects.filter(value__iexact= kwargs['value'], object_id=metadata_obj.id, content_type=metadata_type).first()
                if sub:
                    raise ValidationError('Subject:%s already exists for this resource.' % kwargs['value'])

                sub = Subject.objects.create(value=kwargs['value'], content_object=metadata_obj)
                return sub
            else:
                raise ValidationError('Metadata instance for which subject element to be created is missing.')
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
                                             content_type__pk=sub.content_type.id).count()> 0:
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
            if 'metadata_obj' in kwargs:
                metadata_obj = kwargs['metadata_obj']
                metadata_type = ContentType.objects.get_for_model(metadata_obj)
                src = Source.objects.filter(derived_from= kwargs['derived_from'], object_id=metadata_obj.id, content_type=metadata_type).first()
                if src:
                    raise ValidationError('Source:%s already exists for this resource.' % kwargs['derived_from'])

                src = Source.objects.create(derived_from=kwargs['derived_from'], content_object=metadata_obj)
                return src
            else:
                raise ValidationError('Metadata instance for which source element to be created is missing.')
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
        if 'metadata_obj' in kwargs:
            metadata_obj = kwargs['metadata_obj']
        else:
            raise ValidationError('Metadata instance for which rights element to be created is missing.')

        # in order to create a Rights element we need to have either a value for the statement field or a value for the url field
        if 'statement' in kwargs and 'url' in kwargs:
            rights = Rights.objects.create(statement=kwargs['statement'], url=kwargs['url'],  content_object=metadata_obj)
            return rights
        elif 'url' in kwargs:
            rights = Rights.objects.create(url=kwargs['url'],  content_object=metadata_obj)
            return rights
        elif 'statement' in kwargs:
            rights = Rights.objects.create(statement=kwargs['statement'],  content_object=metadata_obj)
            return rights
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
    last_changed_by = models.ForeignKey(User,
                                        help_text='The person who last changed the resource',
                                        related_name='last_changed_%(app_label)s_%(class)s',
                                        null=True
    )
    dublin_metadata = generic.GenericRelation(
        'dublincore.QualifiedDublinCoreElement',
        help_text='The dublin core metadata of the resource'
    )
    files = generic.GenericRelation('hs_core.ResourceFile', help_text='The files associated with this resource')
    bags = generic.GenericRelation('hs_core.Bags', help_text='The bagits created from versions of this resource')
    short_id = models.CharField(max_length=32, default=lambda: uuid4().hex, db_index=True)
    doi = models.CharField(max_length=1024, blank=True, null=True, db_index=True,
                           help_text='Permanent identifier. Never changes once it\'s been set.')
    comments = CommentsField()

    # this is to establish a relationship between a resource and
    # any metadata container object (e.g., CoreMetaData object)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    # this property needs to be overriden by any specific resource type
    # that needs additional metadata elements on top of core metadata data elements
    @property
    def metadata(self):
        md = CoreMetaData() # only this line needs to be changed when you override
        return self._get_metadata(md)

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

    class Meta:
        abstract = True
        unique_together = ("content_type", "object_id")

def get_path(instance, filename):
    return os.path.join(instance.content_object.short_id, filename)

class ResourceFile(models.Model):
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)

    content_object = generic.GenericForeignKey('content_type', 'object_id')
    resource_file = models.FileField(upload_to=get_path, storage=IrodsStorage() if getattr(settings,'USE_IRODS', False) else DefaultStorage())

class Bags(models.Model):
    object_id = models.PositiveIntegerField()
    content_type = models.ForeignKey(ContentType)

    content_object = generic.GenericForeignKey('content_type', 'object_id')
    bag = models.FileField(upload_to='bags', storage=IrodsStorage() if getattr(settings,'USE_IRODS', False) else DefaultStorage(), null=True) # actually never null
    timestamp = models.DateTimeField(default=now, db_index=True)

    class Meta:
        ordering = ['-timestamp']



class GenericResource(Page, RichText, AbstractResource):

    class Meta:
        verbose_name = 'Generic Hydroshare Resource'

    def can_add(self, request):
        return AbstractResource.can_add(self, request)

    def can_change(self, request):
        return AbstractResource.can_change(self, request)

    def can_delete(self, request):
        return AbstractResource.can_delete(self, request)

    def can_view(self, request):
        return AbstractResource.can_view(self, request)


# This model has a one-to-one relation with the AbstractResource model
class CoreMetaData(models.Model):
    #from django.contrib.sites.models import Site
    _domain = 'hydroshare.org'  #Site.objects.get_current() # this one giving error since the database does not have a related table called 'django_site'

    XML_HEADER = '''<?xml version="1.0"?>
<!DOCTYPE rdf:RDF PUBLIC "-//DUBLIN CORE//DCMES DTD 2002/07/31//EN"
"http://dublincore.org/documents/2002/07/31/dcmes-xml/dcmes-xml-dtd.dtd">'''

    NAMESPACES = {'rdf':"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                  'dc': "http://purl.org/dc/elements/1.1/",
                  'dcterms':"http://purl.org/dc/terms/",
                  'hsterms': "http://hydroshare.org/terms/"}

    DATE_FORMAT = "YYYY-MM-DDThh:mm:ssTZD"
    HYDROSHARE_URL = 'http://%s' % _domain

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
    _resource = generic.GenericRelation(GenericResource)

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
    def resource(self):
        return self._resource.all().first()

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

    def get_xml(self):
        from lxml import etree
        import arrow
        RDF_ROOT = etree.Element('{%s}RDF' % self.NAMESPACES['rdf'], nsmap=self.NAMESPACES)
        # create the Description element -this is not exactly a dc element
        rdf_Description = etree.SubElement(RDF_ROOT, '{%s}Description' % self.NAMESPACES['rdf'])

        resource_uri = self.HYDROSHARE_URL + '/resource/' + self.resource.short_id
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
                cov_value = 'name=%s; start=%s; end=%s; scheme=W3C-DTF' %(coverage.value['name'],
                                                          arrow.get(coverage.value['start'].format(self.DATE_FORMAT)),
                                                          arrow.get(coverage.value['start'].format(self.DATE_FORMAT)))
            elif coverage.type == 'point':
                cov_value = 'name=%s; east=%s; north=%s' %(coverage.value['name'],
                                                                           coverage.value['east'],
                                                                           coverage.value['north'])
            else: # this is box type
                cov_value = 'name=%s; northlimit=%s; eastlimit=%s; southlimit=%s; westlimit=%s' \
                            %(coverage.value['name'], coverage.value['northlimit'], coverage.value['eastlimit'],
                              coverage.value['southlimit'], coverage.value['westlimit'])

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

        return self.XML_HEADER + '\n' + etree.tostring(RDF_ROOT, pretty_print=True)

    def _create_person_element(self, etree, parent_element, person):
        if isinstance(person, Creator):
            dc_person = etree.SubElement(parent_element, '{%s}creator' % self.NAMESPACES['dc'])
        else:
            dc_person = etree.SubElement(parent_element, '{%s}contributor' % self.NAMESPACES['dc'])

        dc_person_rdf_Description = etree.SubElement(dc_person, '{%s}Description' % self.NAMESPACES['rdf'])

        hsterms_name = etree.SubElement(dc_person_rdf_Description, '{%s}name' % self.NAMESPACES['hsterms'])
        hsterms_name.text = person.name
        if person.description:
            dc_person_rdf_Description.set('{%s}about' % self.NAMESPACES['rdf'], person.description)

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

        if person.researcherID:
            hsterms_researcherID = etree.SubElement(dc_person_rdf_Description, '{%s}researcherID' % self.NAMESPACES['hsterms'])
            hsterms_researcherID.set('{%s}resource' % self.NAMESPACES['rdf'], person.researcherID)

        if person.researchGateID:
            hsterms_researchGateID = etree.SubElement(dc_person_rdf_Description, '{%s}researchGateID' % self.NAMESPACES['hsterms'])
            hsterms_researchGateID.set('{%s}resource' % self.NAMESPACES['rdf'], person.researcherID)

    def create_element(self, element_model_name, **kwargs):
        element_model_name = element_model_name.lower()
        if not self._is_valid_element(element_model_name):
            raise ValidationError("Metadata element type:%s is not one of the supported in core metadata elements."
                                  % element_model_name)

        model = ContentType.objects.get(model=element_model_name)
        if model:
            if issubclass(model.model_class(), AbstractMetaDataElement):
                kwargs['metadata_obj']= self
                element = model.model_class().create(**kwargs)
                element.save()
            else:
                raise ValidationError("Metadata element type:%s is not supported." % element_model_name)
        else:
            raise ValidationError("Metadata element type:%s is not supported." % element_model_name)

    def update_element(self, element_model_name, element_id, **kwargs):
        element_model_name = element_model_name.lower()
        model_type = ContentType.objects.get(model=element_model_name)
        if model_type:
            if issubclass(model_type.model_class(), AbstractMetaDataElement):
                kwargs['metadata_obj']= self
                model_type.model_class().update(element_id, **kwargs)
            else:
                raise ValidationError("Metadata element type:%s is not supported." % element_model_name)
        else:
            raise ValidationError("Metadata element type:%s is not supported." % element_model_name)

    def delete_element(self, element_model_name, element_id):
        element_model_name = element_model_name.lower()
        model_type = ContentType.objects.get(model=element_model_name)
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
    extra['dc'] = { m.term_name : m.content for m in extra['res'].dublin_metadata.all() }
    return extra

processor_for(GenericResource)(resource_processor)

@processor_for('resources')
def resource_listing_processor(request, page):
    owned_resources = list(GenericResource.objects.filter(owners__pk=request.user.pk))
    editable_resources = list(GenericResource.objects.filter(owners__pk=request.user.pk))
    viewable_resources = list(GenericResource.objects.filter(public=True))

    return locals()

@receiver(post_save)
def resource_creation_signal_handler(sender, instance, created, **kwargs):
    """Create initial dublin core elements"""
    if isinstance(instance, AbstractResource):
        if created:
            from hs_core.hydroshare import utils
            import json
            instance.metadata.create_element('title', value=instance.title)
            if instance.content:
                instance.metadata.create_element('description', abstract=instance.content)
            else:
                instance.metadata.create_element('description', abstract=instance.description)

            # TODO: With the current VM the get_user_info() method fails. So we can't get the resource uri for
            # the user now.
            # creator_dict = users.get_user_info(instance.creator)
            # instance.metadata.create_element('creator', name=instance.creator.get_full_name(),
            #                                  email=instance.creator.email,
            #                                  description=creator_dict['resource_uri'])

            instance.metadata.create_element('creator', name=instance.creator.get_full_name(), email=instance.creator.email)

            # TODO: The element 'Type' can't be created as we do not have an URI for specific resource types yet

            instance.metadata.create_element('date', type='created', start_date=instance.created)
            instance.metadata.create_element('date', type='modified', start_date=instance.updated)

            # res_json = utils.serialize_science_metadata(instance)
            # res_dict = json.loads(res_json)
            instance.metadata.create_element('identifier', name='hydroShareIdentifier', url='http://hydroshare.org/resource{0}{1}'.format('/', instance.short_id))

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




