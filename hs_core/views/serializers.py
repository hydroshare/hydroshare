__author__ = 'Pabitra'

from collections import namedtuple

from django.contrib.auth.models import Group, User
from rest_framework import serializers

from hs_core.hydroshare import utils
from hs_core import hydroshare
from .utils import validate_json, validate_user_name,  validate_group_name

RESOURCE_TYPES = [rtype.__name__ for rtype in utils.get_resource_types()]

class StringListField(serializers.ListField):
    child = serializers.CharField()

class ResourceUpdateRequestValidator(serializers.Serializer):
    title = serializers.CharField(required=False)
    #metadata = serializers.CharField(validators=[validate_json], required=False)
    edit_users = serializers.CharField(required=False)
    edit_groups = serializers.CharField(required=False)
    view_users = serializers.CharField(required=False)
    view_groups = serializers.CharField(required=False)
    keywords = StringListField(required=False)
    abstract = serializers.CharField(required=False)

    def validate_edit_users(self, value):
        return self._validate_users(value)

    def validate_view_users(self, value):
        return self._validate_users(value)

    def validate_edit_groups(self, value):
        return self._validate_groups(value)

    def validate_view_groups(self, value):
        return self._validate_groups(value)

    def _validate_users(self, value):
        values = value.split(',')
        for value in values:
            if not User.objects.filter(username=value).exists():
                raise serializers.ValidationError("%s in not a valid user name." % value)
        return values

    def _validate_groups(self, value):
        values = value.split(',')
        for value in values:
            if not Group.objects.filter(name=value).exists():
                raise serializers.ValidationError("%s in not a valid group name." % value)
        return values


class ResourceCreateRequestValidator(ResourceUpdateRequestValidator):
    resource_type = serializers.ChoiceField(
            choices=zip(
                [x.__name__ for x in hydroshare.get_resource_types()],
                [x.__name__ for x in hydroshare.get_resource_types()]
            ), default='GenericResource')


class ResourceTypesSerializer(serializers.Serializer):
    resource_type = serializers.CharField(max_length=100, required=True, validators=[lambda x: x in RESOURCE_TYPES])


class ResourceListRequestValidator(serializers.Serializer):
    creator = serializers.CharField(min_length=1, required=False, validators=[validate_user_name])
    group = serializers.CharField(min_length=1, required=False, validators=[validate_group_name])
    user = serializers.CharField(min_length=1, required=False, validators=[validate_user_name])
    owner = serializers.CharField(min_length=1, required=False, validators=[validate_user_name])
    from_date = serializers.DateField(required=False, default=None)
    to_date = serializers.DateField(required=False, default=None)
    start = serializers.IntegerField(required=False, default=None)
    count = serializers.IntegerField(required=False, default=None)
    metadata = serializers.CharField(min_length=1, required=False, validators=[validate_json])
    full_text_search = serializers.CharField(required=False)
    edit_permission = serializers.BooleanField(required=False, default=False)
    published = serializers.BooleanField(required=False, default=False)
    type = serializers.MultipleChoiceField(choices=RESOURCE_TYPES, required=False, default=None)


class ResourceListItemSerializer(serializers.Serializer):
    resource_type = serializers.CharField(max_length=100)
    resource_title = serializers.CharField(max_length=200)
    resource_id = serializers.CharField(max_length=100)
    creator = serializers.CharField(max_length=100)
    date_created = serializers.DateTimeField(format='%m-%d-%Y')
    date_last_updated = serializers.DateTimeField(format='%m-%d-%Y')
    public = serializers.BooleanField()
    discoverable = serializers.BooleanField()
    shareable = serializers.BooleanField()
    immutable = serializers.BooleanField()
    published = serializers.BooleanField()
    bag_url = serializers.URLField()
    science_metadata_url = serializers.URLField()
    resource_url = serializers.URLField()


class ResourceFileSerializer(serializers.Serializer):
    url = serializers.URLField()
    size = serializers.IntegerField()
    content_type = serializers.CharField(max_length=255)


class ResourceType(object):
    def __init__(self, resource_type):
        self.resource_type = resource_type


ResourceListItem = namedtuple('ResourceListItem',
                              ['resource_type',
                               'resource_id',
                               'resource_title',
                               'creator',
                               'public',
                               'discoverable',
                               'shareable',
                               'immutable',
                               'published',
                               'date_created',
                               'date_last_updated',
                               'bag_url',
                               'science_metadata_url',
                               'resource_url'])

ResourceFileItem = namedtuple('ResourceFileItem',
                              ['url',
                               'size',
                               'content_type'])


class UserAuthenticateRequestValidator(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class AccessRulesRequestValidator(serializers.Serializer):
    public = serializers.BooleanField(default=False)

