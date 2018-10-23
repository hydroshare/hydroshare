import requests
import base64

from django.db import models, transaction
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.http import HttpResponse

from mezzanine.pages.page_processors import processor_for

from hs_core.models import BaseResource, ResourceManager, resource_processor, \
    CoreMetaData, AbstractMetaDataElement
from .utils import get_SupportedResTypes_choices, get_SupportedSharingStatus_choices, get_image_type

from hs_file_types.utils import get_SupportedAggTypes_choices


class ToolResource(BaseResource):
    objects = ResourceManager('ToolResource')

    discovery_content_type = 'Web App'  # used during discovery

    class Meta:
        proxy = True
        verbose_name = 'Web App Resource'

    @classmethod
    def get_approved_apps(cls):
        webapp_resources = cls.objects.all()

        final_resource_list = []
        for resource in webapp_resources:
            if resource.metadata.approved:
                final_resource_list.append(resource)

        return final_resource_list

    @classmethod
    def get_supported_upload_file_types(cls):
        # no file types are supported
        return ()

    @classmethod
    def allow_multiple_file_upload(cls):
        # no file can be uploaded
        return False

    @classmethod
    def can_have_multiple_files(cls):
        # resource can't have any files
        return False

    @property
    def metadata(self):
        md = ToolMetaData()
        return self._get_metadata(md)

    @property
    def can_be_published(self):
        return False


processor_for(ToolResource)(resource_processor)


class SupportedFileExtensions(AbstractMetaDataElement):
    term = 'SupportedFileExtensions'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # SupportedFileExtensions element is not repeatable
        unique_together = ("content_type", "object_id")


class AppHomePageUrl(AbstractMetaDataElement):
    term = 'AppHomePageUrl'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # AppHomePageUrl element is not repeatable
        unique_together = ("content_type", "object_id")


class TestingProtocolUrl(AbstractMetaDataElement):
    # should be a link to a page that gives repeatable steps to fully test the app

    term = 'TestingProtocolUrl'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # TestingProtocolUrl element is not repeatable
        unique_together = ("content_type", "object_id")


class HelpPageUrl(AbstractMetaDataElement):
    # should be a link to a page that gives full help documentation
    term = 'HelpPageUrl'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # HelpPageUrl element is not repeatable
        unique_together = ("content_type", "object_id")


class SourceCodeUrl(AbstractMetaDataElement):
    # preferably a GitHub or Bitbucket page
    term = 'SourceCodeUrl'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # SourceCodeUrl element is not repeatable
        unique_together = ("content_type", "object_id")


class IssuesPageUrl(AbstractMetaDataElement):
    # preferably a GitHub or Bitbucket page
    term = 'IssuesPageUrl'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # SourceCodeUrl element is not repeatable
        unique_together = ("content_type", "object_id")


class MailingListUrl(AbstractMetaDataElement):
    # preferably a GitHub or Bitbucket page
    term = 'MailingListUrl'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # MailingListUrl element is not repeatable
        unique_together = ("content_type", "object_id")


class Roadmap(AbstractMetaDataElement):
    ''' should include information about why the app was developed, what's the development status,
    future development plans, links to github issues, etc. - How we hope things will progress, etc
    '''
    term = 'Roadmap'
    value = models.TextField(blank=True, default='')

    class Meta:
        # MailingListUrl element is not repeatable
        unique_together = ("content_type", "object_id")


class ShowOnOpenWithList(AbstractMetaDataElement):
    # Option to show or not show the icon on a landing page with the "open app" button.
    term = 'ShowOnOpenWithList'
    value = models.BooleanField(default=False)

    class Meta:
        # ShowOnOpenWithList element is not repeatable
        unique_together = ("content_type", "object_id")


class RequestUrlBase(AbstractMetaDataElement):
    term = 'RequestUrlBase'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # RequestUrlBase element is not repeatable
        unique_together = ("content_type", "object_id")


class RequestUrlBaseAggregation(AbstractMetaDataElement):
    term = 'RequestUrlBaseAggregation'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # RequestUrlBaseAggregation element is not repeatable
        unique_together = ("content_type", "object_id")


class RequestUrlBaseFile(AbstractMetaDataElement):
    term = 'RequestUrlBaseFile'
    value = models.CharField(max_length=1024, blank=True, default="")

    class Meta:
        # RequestUrlBaseFile element is not repeatable
        unique_together = ("content_type", "object_id")


class ToolVersion(AbstractMetaDataElement):
    term = 'AppVersion'
    value = models.CharField(max_length=128, blank=True)

    class Meta:
        # ToolVersion element is not repeatable
        unique_together = ("content_type", "object_id")


class SupportedResTypeChoices(models.Model):
    description = models.CharField(max_length=128)

    def __unicode__(self):
        return self.description


class SupportedResTypes(AbstractMetaDataElement):
    term = 'SupportedResTypes'
    supported_res_types = models.ManyToManyField(SupportedResTypeChoices,
                                                 blank=True,
                                                 related_name="associated_with")

    class Meta:
        # SupportedResTypes element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_supported_res_types_str(self):
        return ','.join([parameter.description for parameter in self.supported_res_types.all()])

    @classmethod
    def _add_supported_res_type(cls, meta_instance, supported_res_types):

        for res_type in supported_res_types:
            # there are two possibilities for res_type_str values:
            # list of string (during normal create or update) or
            # integer (during creating new version of the resource)
            if isinstance(res_type, int):
                # "copy res" or "create a new version"
                qs = SupportedResTypeChoices.objects.filter(id=res_type)
                if not qs.exists():
                    raise ObjectDoesNotExist('Resource type object {0} is not supported').format(
                        res_type)
                meta_instance.supported_res_types.add(qs[0])

            elif isinstance(res_type, basestring):
                # create or update res
                qs = SupportedResTypeChoices.objects.filter(description__iexact=res_type)
                if qs.exists():
                    meta_instance.supported_res_types.add(qs[0])
                else:
                    meta_instance.supported_res_types.create(description=res_type)
            else:
                raise ValidationError("No supported_res_types parameter "
                                      "was found in the **kwargs list")

    @classmethod
    def _validate_supported_res_types(cls, supported_res_types):
        for res_type in supported_res_types:
            if isinstance(res_type, basestring) \
                    and res_type not in [res_type_choice[0]
                                         for res_type_choice in get_SupportedResTypes_choices()]:
                raise ValidationError('Invalid supported_res_types:%s' % res_type)

    @classmethod
    def create(cls, **kwargs):
        if 'supported_res_types' in kwargs:
            cls._validate_supported_res_types(kwargs['supported_res_types'])

            metadata_obj = kwargs['content_object']
            new_meta_instance = SupportedResTypes.objects.create(content_object=metadata_obj)

            cls._add_supported_res_type(new_meta_instance, kwargs['supported_res_types'])
            return new_meta_instance
        else:
            raise ValidationError("No supported_res_types parameter was found in the **kwargs list")

    @classmethod
    def update(cls, element_id, **kwargs):
        meta_instance = SupportedResTypes.objects.get(id=element_id)

        if 'supported_res_types' in kwargs:
            cls._validate_supported_res_types(kwargs['supported_res_types'])

            meta_instance.supported_res_types.clear()
            cls._add_supported_res_type(meta_instance, kwargs['supported_res_types'])
            meta_instance.save()
        else:
            raise ValidationError("No supported_res_types parameter was found in the **kwargs list")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("SupportedResTypes element can't be deleted.")


class SupportedAggTypeChoices(models.Model):
    description = models.CharField(max_length=128)

    def __unicode__(self):
        return self.description


class SupportedAggTypes(AbstractMetaDataElement):
    term = 'SupportedAggTypes'
    supported_agg_types = models.ManyToManyField(SupportedAggTypeChoices,
                                                 blank=True,
                                                 related_name="associated_with")

    class Meta:
        # SupportedAggTypes element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_supported_agg_types_str(self):
        return ','.join([parameter.description for parameter in self.supported_agg_types.all()])

    @classmethod
    def _add_supported_agg_type(cls, meta_instance, supported_agg_types):

        for agg_type in supported_agg_types:
            # there are two possibilities for agg_type_str values:
            # list of string (during normal create or update) or
            # integer (during creating new version of the aggregation)
            # TODO come back to this, probably only need one
            if isinstance(agg_type, int):
                # "copy agg" or "create a new version"
                qs = SupportedAggTypeChoices.objects.filter(id=agg_type)
                if not qs.exists():
                    raise ObjectDoesNotExist('Aggregation type object {0} is not supported').format(
                        agg_type)
                meta_instance.supported_agg_types.add(qs[0])

            elif isinstance(agg_type, basestring):
                # create or update agg
                qs = SupportedAggTypeChoices.objects.filter(description__iexact=agg_type)
                if qs.exists():
                    meta_instance.supported_agg_types.add(qs[0])
                else:
                    meta_instance.supported_agg_types.create(description=agg_type)
            else:
                raise ValidationError("No supported_agg_types parameter "
                                      "was found in the **kwargs list")

    @classmethod
    def _validate_supported_agg_types(cls, supported_agg_types):
        for agg_type in supported_agg_types:
            if isinstance(agg_type, basestring) \
                    and agg_type not in [agg_type_choice[0]
                                         for agg_type_choice in get_SupportedAggTypes_choices()]:
                raise ValidationError('Invalid supported_agg_types:%s' % agg_type)

    @classmethod
    def create(cls, **kwargs):
        if 'supported_agg_types' in kwargs:
            cls._validate_supported_agg_types(kwargs['supported_agg_types'])

            metadata_obj = kwargs['content_object']
            new_meta_instance = SupportedAggTypes.objects.create(content_object=metadata_obj)

            cls._add_supported_agg_type(new_meta_instance, kwargs['supported_agg_types'])
            return new_meta_instance
        else:
            raise ValidationError("No supported_agg_types parameter was found in the **kwargs list")

    @classmethod
    def update(cls, element_id, **kwargs):
        meta_instance = SupportedAggTypes.objects.get(id=element_id)

        if 'supported_agg_types' in kwargs:
            cls._validate_supported_agg_types(kwargs['supported_agg_types'])

            meta_instance.supported_agg_types.clear()
            cls._add_supported_agg_type(meta_instance, kwargs['supported_agg_types'])
            meta_instance.save()
        else:
            raise ValidationError("No supported_agg_types parameter was found in the **kwargs list")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("SupportedAggTypes element can't be deleted.")


class SupportedSharingStatusChoices(models.Model):
    description = models.CharField(max_length=128)

    def __unicode__(self):
        return self.description


class SupportedSharingStatus(AbstractMetaDataElement):
    term = 'SupportedSharingStatus'
    sharing_status = models.ManyToManyField(SupportedSharingStatusChoices,
                                            blank=True,
                                            related_name="associated_with")

    class Meta:
        # SupportedSharingStatus element is not repeatable
        unique_together = ("content_type", "object_id")

    def get_sharing_status_str(self):
        return ', '.join([parameter.description for parameter in self.sharing_status.all()])

    @classmethod
    def _add_sharing_status(cls, meta_instance, sharing_status_list):
        for sharing_status in sharing_status_list:
            # there are two possibilities for res_type_str values:
            # list of string (during normal create or update) or
            # integer (during creating new version of the resource)
            if isinstance(sharing_status, int):
                # "copy res" or "create a new version"
                qs = SupportedSharingStatusChoices.objects.filter(id=sharing_status)
                if not qs.exists():
                    raise ObjectDoesNotExist('Sharing status {0} is not supported').format(
                        sharing_status)
                meta_instance.sharing_status.add(qs[0])
            elif isinstance(sharing_status, basestring):
                # create or update res
                qs = SupportedSharingStatusChoices.objects. \
                    filter(description__iexact=sharing_status)
                if qs.exists():
                    meta_instance.sharing_status.add(qs[0])
                else:
                    meta_instance.sharing_status.create(description=sharing_status)
            else:
                raise ValidationError("No sharing_status parameter "
                                      "was found in the **kwargs list")

    @classmethod
    def _validate_sharing_status(cls, sharing_status_list):
        for sharing_status in sharing_status_list:
            if isinstance(sharing_status, basestring) and \
                    sharing_status not in [sharing_status_choice_tuple[0]
                                           for sharing_status_choice_tuple in
                                           get_SupportedSharingStatus_choices()]:
                raise ValidationError('Invalid sharing_status:%s' % sharing_status)

    @classmethod
    def create(cls, **kwargs):
        if 'sharing_status' in kwargs:
            cls._validate_sharing_status(kwargs["sharing_status"])

            metadata_obj = kwargs['content_object']
            new_meta_instance = SupportedSharingStatus.objects.create(content_object=metadata_obj)

            cls._add_sharing_status(new_meta_instance, kwargs['sharing_status'])
            return new_meta_instance
        else:
            raise ValidationError("No sharing_status parameter was found in the **kwargs list")

    @classmethod
    def update(cls, element_id, **kwargs):
        meta_instance = SupportedSharingStatus.objects.get(id=element_id)
        if 'sharing_status' in kwargs:
            cls._validate_sharing_status(kwargs["sharing_status"])

            meta_instance.sharing_status.clear()

            cls._add_sharing_status(meta_instance, kwargs['sharing_status'])
            meta_instance.save()
        else:
            raise ValidationError("No sharing_status parameter "
                                  "was found in the **kwargs list")

    @classmethod
    def remove(cls, element_id):
        raise ValidationError("SupportedSharingStatus element can't be deleted.")


class ToolIcon(AbstractMetaDataElement):
    term = 'ToolIcon'
    value = models.CharField(max_length=1024, blank=True, default="")
    data_url = models.TextField(blank=True, default="")

    @classmethod
    def _validate_tool_icon(cls, url):
        try:
            response = requests.get(url, verify=False)
        except Exception as ex:
            raise ValidationError("Failed to read data from given url: {0}".format(ex.message))
        if response.status_code != 200:
            raise HttpResponse("Failed to read data from given url. HTTP_code {0}".
                               format(response.status_code))
        image_size_mb = float(response.headers["content-length"])
        if image_size_mb > 1000000:  # 1mb
            raise ValidationError("Icon image size should be less than 1MB.")
        image_type = get_image_type(h=response.content)
        if image_type not in ["png", "gif", "jpeg"]:
            raise ValidationError("Supported icon image types are png, gif and jpeg")
        base64_string = base64.b64encode(response.content)
        data_url = "data:image/{image_type};base64,{base64_string}". \
            format(image_type=image_type, base64_string=base64_string)
        return data_url

    @classmethod
    def create(cls, **kwargs):
        if 'value' in kwargs and "data_url" not in kwargs:
            url = kwargs["value"]
            data_url = cls._validate_tool_icon(url)

            metadata_obj = kwargs['content_object']
            new_meta_instance = ToolIcon.objects.create(content_object=metadata_obj)
            new_meta_instance.value = url
            new_meta_instance.data_url = data_url
            new_meta_instance.save()
            return new_meta_instance
        elif "data_url" in kwargs:
            metadata_obj = kwargs['content_object']
            new_meta_instance = ToolIcon.objects.create(content_object=metadata_obj)
            new_meta_instance.value = kwargs["value"] if "value" in kwargs else ""
            new_meta_instance.data_url = kwargs["data_url"]
            new_meta_instance.save()
            return new_meta_instance
        else:
            raise ValidationError("No value parameter was found in the **kwargs list")

    @classmethod
    def update(cls, element_id, **kwargs):
        meta_instance = ToolIcon.objects.get(id=element_id)
        if 'value' in kwargs:
            url = kwargs["value"]
            data_url = cls._validate_tool_icon(url)
            meta_instance.value = url
            meta_instance.data_url = data_url
            meta_instance.save()
        else:
            raise ValidationError("No value parameter was found in the **kwargs list")

    class Meta:
        # ToolIcon element is not repeatable
        unique_together = ("content_type", "object_id")


class ToolMetaData(CoreMetaData):
    _url_base = GenericRelation(RequestUrlBase)
    _url_base_aggregation = GenericRelation(RequestUrlBaseAggregation)
    _url_base_file = GenericRelation(RequestUrlBaseFile)
    _version = GenericRelation(ToolVersion)
    _supported_res_types = GenericRelation(SupportedResTypes)
    _supported_agg_types = GenericRelation(SupportedAggTypes)
    _tool_icon = GenericRelation(ToolIcon)
    _supported_sharing_status = GenericRelation(SupportedSharingStatus)
    _supported_file_extensions = GenericRelation(SupportedFileExtensions)
    _homepage_url = GenericRelation(AppHomePageUrl)

    approved = models.BooleanField(default=False)
    testing_protocol_url = GenericRelation(TestingProtocolUrl)
    help_page_url = GenericRelation(HelpPageUrl)
    source_code_url = GenericRelation(SourceCodeUrl)
    issues_page_url = GenericRelation(IssuesPageUrl)
    mailing_list_url = GenericRelation(MailingListUrl)
    roadmap = GenericRelation(Roadmap)
    show_on_open_with_list = GenericRelation(ShowOnOpenWithList)

    @property
    def resource(self):
        return ToolResource.objects.filter(object_id=self.id).first()

    @property
    def url_base(self):
        return self._url_base.first()

    @property
    def url_base_aggregation(self):
        return self._url_base_aggregation.first()

    @property
    def url_base_file(self):
        return self._url_base_file.first()

    @property
    def version(self):
        return self._version.first()

    @property
    def supported_resource_types(self):
        return self._supported_res_types.first()

    @property
    def supported_aggregation_types(self):
        return self._supported_agg_types.first()

    @property
    def supported_sharing_status(self):
        return self._supported_sharing_status.first()

    @property
    def supported_file_extensions(self):
        return self._supported_file_extensions.first()

    @property
    def app_home_page_url(self):
        return self._homepage_url.first()

    @property
    def app_icon(self):
        return self._tool_icon.first()

    @property
    def serializer(self):
        """Return an instance of rest_framework Serializer for self """
        from serializers import ToolMetaDataSerializer
        return ToolMetaDataSerializer(self)

    @classmethod
    def parse_for_bulk_update(cls, metadata, parsed_metadata):
        """Overriding the base class method"""

        CoreMetaData.parse_for_bulk_update(metadata, parsed_metadata)
        keys_to_update = metadata.keys()
        if 'requesturlbase' in keys_to_update:
            parsed_metadata.append({"requesturlbase": metadata.pop('requesturlbase')})

        if 'requesturlbaseaggregation' in keys_to_update:
            parsed_metadata.append(
                {"requesturlbaseaggregation": metadata.pop('requesturlbaseaggregation')})

        if 'requesturlbasefile' in keys_to_update:
            parsed_metadata.append({"requesturlbasefile": metadata.pop('requesturlbasefile')})

        if 'toolversion' in keys_to_update:
            parsed_metadata.append({"toolversion": metadata.pop('toolversion')})

        if 'toolicon' in keys_to_update:
            parsed_metadata.append({"toolicon": metadata.pop('toolicon')})

        if 'supportedfileextensions' in keys_to_update:
            parsed_metadata.append({"supportedfileextensions": metadata.pop(
                'supportedfileextensions')})

        if 'apphomepageurl' in keys_to_update:
            parsed_metadata.append({"apphomepageurl": metadata.pop('apphomepageurl')})

        if 'supportedrestypes' in keys_to_update:
            parsed_metadata.append({"supportedrestypes": metadata.pop('supportedrestypes')})

        if 'supportedaggtypes' in keys_to_update:
            parsed_metadata.append({"supportedaggtypes": metadata.pop('supportedaggtypes')})

        if 'supportedsharingstatus' in keys_to_update:
            parsed_metadata.append(
                {"supportedsharingstatus": metadata.pop('supportedsharingstatus')})

    @classmethod
    def get_supported_element_names(cls):
        elements = super(ToolMetaData, cls).get_supported_element_names()
        elements.append('RequestUrlBase')
        elements.append('RequestUrlBaseAggregation')
        elements.append('RequestUrlBaseFile')
        elements.append('ToolVersion')
        elements.append('SupportedResTypes')
        elements.append('SupportedAggTypes')
        elements.append('ToolIcon')
        elements.append('SupportedSharingStatus')
        elements.append('SupportedFileExtensions')
        elements.append('AppHomePageUrl')
        elements.append('TestingProtocolUrl')
        elements.append('SourceCodeUrl')
        elements.append('HelpPageUrl')
        elements.append('MailingListUrl')
        elements.append('IssuesPageUrl')
        elements.append('Roadmap')
        elements.append('ShowOnOpenWithList')
        return elements

    def has_all_required_elements(self):
        if self.get_required_missing_elements():
            return False
        return True

    def get_required_missing_elements(self):  # show missing required meta
        missing_required_elements = super(ToolMetaData, self).get_required_missing_elements()

        # At least one of the two metadata must exist: Home Page URL or App-launching URL Pattern
        if not self._launching_pattern_exists() \
                and not self._value_exists(self.app_home_page_url):
            missing_required_elements.append('App Home Page URL or an App-launching URL '
                                             'Pattern')
        else:
            # If Supported Res Type is selected, app-launching URL pattern must be present
            if self.supported_resource_types \
                    and self.supported_resource_types.supported_res_types.count() > 0:
                if not self._launching_pattern_exists():
                    missing_required_elements.append('An App-launching URL Pattern')

            # if Supported Res Type presents, Supported Sharing Status must present, not vice versa
            if self.supported_resource_types \
                    and self.supported_resource_types.supported_res_types.count() > 0:
                if not self.supported_sharing_status \
                        or not self.supported_sharing_status.sharing_status.count() > 0:
                    missing_required_elements.append('Supported Sharing Status')

        return missing_required_elements

    def _launching_pattern_exists(self):
        return self._value_exists(self.url_base) \
            or self._value_exists(self.url_base_file) \
            or self._value_exists(self.url_base_aggregation)

    def _value_exists(self, field):
        return field and field.value

    def delete_all_elements(self):
        super(ToolMetaData, self).delete_all_elements()
        self._url_base.all().delete()
        self._url_base_aggregation.all().delete()
        self._url_base_file.all().delete()
        self._version.all().delete()
        self._supported_res_types.all().delete()
        self._supported_agg_types.all().delete()
        self._tool_icon.all().delete()
        self._supported_sharing_status.all().delete()
        self._supported_file_extensions.all().delete()
        self._homepage_url.all().delete()

        self.testing_protocol_url.all().delete()
        self.help_page_url.all().delete()
        self.source_code_url.all().delete()
        self.issues_page_url.all().delete()
        self.mailing_list_url.all().delete()
        self.roadmap.all().delete()
        self.show_on_open_with_list.all().delete()

    def update(self, metadata, user):
        # overriding the base class update method for bulk update of metadata

        from forms import SupportedResTypesValidationForm, SupportedSharingStatusValidationForm, \
            UrlValidationForm, VersionValidationForm, ToolIconValidationForm, \
            SupportedAggTypesValidationForm, SupportedFileExtensionsValidationForm, \
            AppResourceLevelUrlValidationForm, AppAggregationLevelUrlValidationForm, \
            AppFileLevelUrlValidationForm

        # update any core metadata
        super(ToolMetaData, self).update(metadata, user)

        # update resource specific metadata

        def validate_form(form):
            if not form.is_valid():
                err_string = self.get_form_errors_as_string(form)
                raise ValidationError(err_string)

        with transaction.atomic():
            for dict_item in metadata:
                if 'supportedrestypes' in dict_item:
                    validation_form = SupportedResTypesValidationForm(
                        dict_item['supportedrestypes'])
                    validate_form(validation_form)
                    self.create_element('supportedrestypes', **dict_item['supportedrestypes'])
                elif 'supportedaggtypes' in dict_item:
                    validation_form = SupportedAggTypesValidationForm(
                        dict_item['supportedaggtypes'])
                    validate_form(validation_form)
                    self.create_element('supportedaggtypes', **dict_item['supportedaggtypes'])
                elif 'supportedsharingstatus' in dict_item:
                    validation_form = SupportedSharingStatusValidationForm(
                        dict_item['supportedsharingstatus'])
                    validate_form(validation_form)
                    self.create_element('supportedsharingstatus',
                                        **dict_item['supportedsharingstatus'])
                elif 'requesturlbase' in dict_item:
                    validation_form = AppResourceLevelUrlValidationForm(dict_item['requesturlbase'])
                    validate_form(validation_form)
                    request_url = self.url_base
                    if request_url is not None:
                        self.update_element('requesturlbase', request_url.id,
                                            value=dict_item['requesturlbase'])
                    else:
                        self.create_element('requesturlbase', value=dict_item['requesturlbase'])
                elif 'requesturlbaseaggregation' in dict_item:
                    validation_form = AppAggregationLevelUrlValidationForm(
                        dict_item['requesturlbaseaggregation'])
                    validate_form(validation_form)
                    request_url = self.url_base_aggregation
                    if request_url is not None:
                        self.update_element('requesturlbaseaggregation', request_url.id,
                                            value=dict_item['requesturlbaseaggregation'])
                    else:
                        self.create_element('requesturlbaseaggregation',
                                            value=dict_item['requesturlbaseaggregation'])
                elif 'requesturlbasefile' in dict_item:
                    validation_form = AppFileLevelUrlValidationForm(dict_item['requesturlbasefile'])
                    validate_form(validation_form)
                    request_url = self.url_base_file
                    if request_url is not None:
                        self.update_element('requesturlbasefile', request_url.id,
                                            value=dict_item['requesturlbasefile'])
                    else:
                        self.create_element('requesturlbasefile',
                                            value=dict_item['requesturlbasefile'])
                elif 'toolversion' in dict_item:
                    validation_form = VersionValidationForm(dict_item['toolversion'])
                    validate_form(validation_form)
                    tool_version = self.version
                    if tool_version is not None:
                        self.update_element('toolversion', tool_version.id,
                                            **dict_item['toolversion'])
                    else:
                        self.create_element('toolversion', **dict_item['toolversion'])
                elif 'toolicon' in dict_item:
                    validation_form = ToolIconValidationForm(dict_item['toolicon'])
                    validate_form(validation_form)
                    tool_icon = self.app_icon
                    if tool_icon is not None:
                        self.update_element('toolicon', tool_icon.id, **dict_item['toolicon'])
                    else:
                        self.create_element('toolicon', **dict_item['toolicon'])
                elif 'supportedfileextensions' in dict_item:
                    validation_form = SupportedFileExtensionsValidationForm(
                        dict_item['supportedfileextensions'])
                    validate_form(validation_form)
                    supported_file_extensions = self.supported_file_extensions
                    if supported_file_extensions is not None:
                        self.update_element('supportedfileextensions', supported_file_extensions.id,
                                            **dict_item['supportedfileextensions'])
                    else:
                        self.create_element('supportedfileextensions',
                                            **dict_item['supportedfileextensions'])
                elif 'apphomepageurl' in dict_item:
                    validation_form = UrlValidationForm(dict_item['apphomepageurl'])
                    validate_form(validation_form)
                    app_url = self.app_home_page_url
                    if app_url is not None:
                        self.update_element('apphomepageurl', app_url.id,
                                            **dict_item['apphomepageurl'])
                    else:
                        self.create_element('apphomepageurl', **dict_item['apphomepageurl'])

    def __str__(self):
        return self.title.value

    class Meta:
        verbose_name = "Application Approval"
        verbose_name_plural = "Application Approvals"
