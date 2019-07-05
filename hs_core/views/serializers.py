
from collections import namedtuple

from django.contrib.auth.models import Group, User
from rest_framework import serializers

from hs_core.hydroshare import utils
from hs_core import hydroshare
from .utils import validate_json, validate_user, validate_group
from hs_access_control.models import PrivilegeCodes
from drf_yasg.utils import swagger_serializer_method

RESOURCE_TYPES = [rtype.__name__ for rtype in utils.get_resource_types()]
CONTENT_TYPES = [ctype.__name__ for ctype in utils.get_content_types()]


class StringListField(serializers.ListField):
    child = serializers.CharField()


class ResourceUpdateRequestValidator(serializers.Serializer):
    title = serializers.CharField(required=False)
    metadata = serializers.CharField(validators=[validate_json], required=False)
    extra_metadata = serializers.CharField(validators=[validate_json], required=False)
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
            ), default='CompositeResource')


class ResourceTypesSerializer(serializers.Serializer):
    resource_type = serializers.CharField(max_length=100, required=True,
                                          validators=[lambda x: x in RESOURCE_TYPES],
                                          help_text='list of resource types')


class ContentTypesSerializer(serializers.Serializer):
    content_type = serializers.CharField(max_length=100, required=True,
                                          validators=[lambda x: x in CONTENT_TYPES],
                                          help_text='list of content types')


class TaskStatusSerializer(serializers.Serializer):
    bag_status = serializers.CharField(help_text='Status of task, i.e. "Not Ready" ')
    task_id = serializers.CharField(help_text="The task id to be used to check task status")


class ResourceListRequestValidator(serializers.Serializer):
    creator = serializers.CharField(min_length=1, required=False,
                                    help_text='The first author (name or email)')
    author = serializers.CharField(required=False,
                                   help_text='Comma separated list of authors (name or email)')
    group = serializers.CharField(min_length=1, required=False, validators=[validate_group],
                                  help_text='A group name (requires edit_permissions=True)')
    user = serializers.CharField(min_length=1, required=False, validators=[validate_user],
                                 help_text='Viewable by user (name or email)')
    owner = serializers.CharField(min_length=1, required=False, validators=[validate_user],
                                  help_text='Owned by user (name or email)')
    from_date = serializers.DateField(required=False, default=None,
                                      help_text='to get a list of resources created on or after '
                                                'this date')
    to_date = serializers.DateField(required=False, default=None,
                                    help_text='to get a list of resources created on or before '
                                              'this date')
    subject = serializers.CharField(required=False,
                                    help_text='Comma separated list of subjects')
    full_text_search = serializers.CharField(required=False,
                                             help_text='get a list of resources with this text')
    edit_permission = serializers.BooleanField(required=False, default=False,
                                               help_text='filter by edit permissions of '
                                                         'user/group/owner')
    published = serializers.BooleanField(required=False, default=False,
                                         help_text='filter by published resources')
    type = serializers.MultipleChoiceField(choices=RESOURCE_TYPES, required=False, default=None,
                                           help_text='to get a list of resources of the specified '
                                                     'resource types')
    coverage_type = serializers.ChoiceField(choices=['box', 'point'], required=False,
                                            help_text='to get a list of resources that fall within '
                                                      'the specified spatial coverage boundary')
    north = serializers.CharField(required=False,
                                  help_text='north coordinate of spatial coverage. This parameter '
                                            'is required if *coverage_type* has been specified')
    south = serializers.CharField(required=False,
                                  help_text='south coordinate of spatial coverage. This parameter '
                                            'is required if *coverage_type* has been specified '
                                            'with a value of box')
    east = serializers.CharField(required=False,
                                 help_text='east coordinate of spatial coverage. This parameter '
                                           'is required if *coverage_type* has been specified')
    west = serializers.CharField(required=False,
                                 help_text='west coordinate of spatial coverage. This parameter '
                                           'is required if *coverage_type* has been specified with '
                                           'a value of box')
    include_obsolete = serializers.BooleanField(required=False, default=False,
                                                help_text='Include repleaced resources')


class ResourceListItemSerializer(serializers.Serializer):
    resource_type = serializers.CharField(max_length=100)
    resource_title = serializers.CharField(max_length=200)
    resource_id = serializers.CharField(max_length=100)
    abstract = serializers.CharField()
    authors = serializers.ListField()
    creator = serializers.CharField(max_length=100)
    doi = serializers.CharField(max_length=200)
    date_created = serializers.DateTimeField(format='%m-%d-%Y')
    date_last_updated = serializers.DateTimeField(format='%m-%d-%Y')
    public = serializers.BooleanField()
    discoverable = serializers.BooleanField()
    shareable = serializers.BooleanField()
    coverages = serializers.JSONField(required=False)
    immutable = serializers.BooleanField()
    published = serializers.BooleanField()
    bag_url = serializers.URLField()
    science_metadata_url = serializers.URLField()
    resource_map_url = serializers.URLField()
    resource_url = serializers.URLField()


class ResourceCreatedSerializer(serializers.Serializer):
    resource_type = serializers.CharField(max_length=100)
    resource_id = serializers.CharField(max_length=100)
    message = serializers.CharField()


class ResourceFileSerializer(serializers.Serializer):
    file_name = serializers.CharField(max_length=200, help_text='The filename, including the path')
    url = serializers.URLField(help_text='The url to download the file')
    size = serializers.IntegerField(help_text='The size of the file')
    content_type = serializers.CharField(max_length=255, help_text='The content type of the file')
    logical_file_type = serializers.CharField(max_length=255)


class GroupPrivilegeSerializer(serializers.Serializer):
    status = serializers.CharField(help_text='The status of the request')
    name = serializers.CharField(help_text="The name of the shared group")
    privileg_granted = serializers.ChoiceField(help_text="The privilege to grant",
                                               choices=PrivilegeCodes.CHOICES,
                                               default=PrivilegeCodes.NONE)
    group_pic = serializers.CharField(help_text="Url of the group picture")
    current_user_privilege = serializers.ChoiceField(help_text="Logged in user's permissions",
                                                     choices=PrivilegeCodes.CHOICES,
                                                     default=PrivilegeCodes.NONE)
    error_msg = serializers.CharField(help_text="Description of error")


class UserPrivilegeSerializer(serializers.Serializer):
    status = serializers.CharField(help_text='The status of the request')
    username = serializers.CharField(help_text="The username name of the shared user")
    name = serializers.CharField(help_text="The full name name of the shared user")
    privileg_granted = serializers.ChoiceField(help_text="The privilege to grant",
                                               choices=PrivilegeCodes.CHOICES,
                                               default=PrivilegeCodes.NONE)
    current_user_privilege = serializers.ChoiceField(help_text="Logged in user's permissions",
                                                     choices=PrivilegeCodes.CHOICES,
                                                     default=PrivilegeCodes.NONE)
    profile_pic = serializers.CharField(help_text="Url of the user's profile picture")
    is_current_user = serializers.BooleanField(help_text="Indicates whether the currently logged "
                                                         "in user made ther permission request")
    error_msg = serializers.CharField(help_text="Description of error")


class ResourceType(object):
    def __init__(self, resource_type):
        self.resource_type = resource_type


class ContentType(object):
    def __init__(self, content_type):
        self.content_type = content_type


ResourceListItem = namedtuple('ResourceListItem',
                              ['resource_type',
                               'resource_id',
                               'resource_title',
                               'abstract',
                               'authors',
                               'creator',
                               'doi',
                               'public',
                               'discoverable',
                               'shareable',
                               'immutable',
                               'published',
                               'date_created',
                               'date_last_updated',
                               'bag_url',
                               'coverages',
                               'science_metadata_url',
                               'resource_map_url',
                               'resource_url',
                               'content_types'])

ResourceFileItem = namedtuple('ResourceFileItem',
                              ['url',
                               'file_name',
                               'size',
                               'content_type',
                               'logical_file_type'])


class UserAuthenticateRequestValidator(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class AccessRulesRequestValidator(serializers.Serializer):
    public = serializers.BooleanField(default=False)


class ResourceFileValidator(serializers.Serializer):
    file = serializers.FileField()

    @swagger_serializer_method(serializer_or_field=file)
    def get_file(self, obj):
        return ResourceFileValidator().data