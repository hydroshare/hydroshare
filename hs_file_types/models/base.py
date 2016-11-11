import json
from dateutil import parser

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from hs_core.models import AbstractMetaDataElement, Coverage
from django.contrib.postgres.fields import HStoreField

from hs_core.models import ResourceFile


class AbstractFileMetaData(models.Model):
    """ base class for HydroShare file type metadata """

    # one temporal coverage and one spatial coverage
    coverages = GenericRelation(Coverage)
    # kye/value metadata
    extra_metadata = HStoreField(default={})

    class Meta:
        abstract = True

    def delete_all_elements(self):
        self.coverages.all().delete()


    def get_html(self):
        # subclass must implement
        # returns a string representing html code for display of metadata in view mode
        raise NotImplementedError

    def has_all_required_elements(self):
        return True

    @classmethod
    def get_supported_element_names(cls):
        return ['Coverage']

    @property
    def has_metadata(self):
        if not self.coverages.all() and not self.extra_metadata:
            return False
        return True

    @property
    def spatial_coverage(self):
        return self.coverages.exclude(type='period').first()

    @property
    def temporal_coverage(self):
        return self.coverages.filter(type='period').first()

    def create_element(self, element_model_name, **kwargs):
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        element = model_type.model_class().create(**kwargs)
        if element_model_name.lower() == "coverage":
            resource = element.metadata.logical_file.resource
            _update_resource_coverage_element(resource)
        return element

    def update_element(self, element_model_name, element_id, **kwargs):
        model_type = self._get_metadata_element_model_type(element_model_name)
        kwargs['content_object'] = self
        model_type.model_class().update(element_id, **kwargs)
        if element_model_name.lower() == "coverage":
            element = model_type.model_class().objects.get(id=element_id)
            resource = element.metadata.logical_file.resource
            _update_resource_coverage_element(resource)

    def delete_element(self, element_model_name, element_id):
        model_type = self._get_metadata_element_model_type(element_model_name)
        model_type.model_class().remove(element_id)

    def _get_metadata_element_model_type(self, element_model_name):
        element_model_name = element_model_name.lower()
        if not self._is_valid_element(element_model_name):
            raise ValidationError("Metadata element type:%s is not one of the "
                                  "supported metadata elements."
                                  % element_model_name)

        unsupported_element_error = "Metadata element type:%s is not supported." \
                                    % element_model_name
        try:
            model_type = ContentType.objects.get(app_label='hs_geo_raster_resource',
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
        allowed_elements = [el.lower() for el in self.get_supported_element_names()]
        return element_name.lower() in allowed_elements

    @classmethod
    def validate_element_data(cls, request, element_name):
        raise NotImplementedError


class AbstractLogicalFile(models.Model):
    """ base class for HydroShare file types """

    # mime type of the dominant file in the group - not sure if we need this
    mime_type = models.CharField(max_length=1000, default='')
    # files associated with this logical file group
    files = GenericRelation(ResourceFile, content_type_field='logical_file_content_type',
                            object_id_field='logical_file_object_id')
    # the dataset name will allow us to identify a logical file group on user interface
    dataset_name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        abstract = True

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        # any file can be part of this logical file group - subclass needs to override this
        return [".*"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        # can store any file types in this logical file group - subclass needs to override this
        return [".*"]

    @classmethod
    def type_name(cls):
        return cls.__name__

    @property
    def has_metadata(self):
        return hasattr(self, 'metadata')

    @property
    def size(self):
        # get total size (in bytes) of all files in this file type
        return sum([f.size for f in self.files.all()])

    @property
    def resource(self):
        return self.files.all().first().resource

    def logical_delete(self, user):
        # deletes the logical file as well as all resource files associated with this logical file
        from hs_core.hydroshare.resource import delete_resource_file
        self.delete_metadata()
        # delete all resource files associated with this instance of logical file
        for f in self.files.all():
            delete_resource_file(f.resource.short_id, f.id, user,
                                 delete_logical_file=False)

        # delete logical file first then delete the associated metadata file object
        metadata = self.metadata
        super(AbstractLogicalFile, self).delete()
        metadata.delete()

    def delete_metadata(self):
        # delete all metadata associated with this file type
        if self.has_metadata:
            self.metadata.delete_all_elements()


def _update_resource_coverage_element(resource):
    # TODO: This needs to be unit tested
    # update resource spatial coverage
    bbox_value = {}
    spatial_coverages = [lf.metadata.spatial_coverage for lf in resource.logical_files
                         if lf.metadata.spatial_coverage is not None]

    cov_type = "point"
    if len(spatial_coverages) > 1:
        bbox_value = {'northlimit': -90, 'southlimit': 90, 'eastlimit': -180, 'westlimit': 180,
                      'projection': 'WGS 84 EPSG:4326', 'units': "Decimal degrees"}
        cov_type = 'box'
        for sp_cov in spatial_coverages:
            if sp_cov.type == "box":
                if bbox_value['northlimit'] < sp_cov.value['northlimit']:
                    bbox_value['northlimit'] = sp_cov.value['northlimit']
                if bbox_value['southlimit'] > sp_cov.value['southlimit']:
                    bbox_value['southlimit'] = sp_cov.value['southlimit']
                if bbox_value['eastlimit'] < sp_cov.value['eastlimit']:
                    bbox_value['eastlimit'] = sp_cov.value['eastlimit']
                if bbox_value['westlimit'] > sp_cov.value['westlimit']:
                    bbox_value['westlimit'] = sp_cov.value['westlimit']
            else:
                # point type coverage
                if bbox_value['northlimit'] < sp_cov.value['north']:
                    bbox_value['northlimit'] = sp_cov.value['north']
                if bbox_value['southlimit'] > sp_cov.value['north']:
                    bbox_value['southlimit'] = sp_cov.value['north']
                if bbox_value['eastlimit'] < sp_cov.value['east']:
                    bbox_value['eastlimit'] = sp_cov.value['east']
                if bbox_value['westlimit'] > sp_cov.value['east']:
                    bbox_value['westlimit'] = sp_cov.value['east']

    elif len(spatial_coverages) == 1:
        sp_cov = spatial_coverages[0]
        if sp_cov.type == "box":
            bbox_limits = ['northlimit', 'southlimit', 'eastlimit', 'westlimit']
            for limit in bbox_limits:
                if bbox_value[limit] < sp_cov.value[limit]:
                    bbox_value[limit] = sp_cov.value[limit]
        else:
            # point type coverage
            bbox_value = {'north': -90, 'east': -180,
                          'projection': 'WGS 84 EPSG:4326', 'units': "Decimal degrees"}
            if bbox_value['north'] < sp_cov.value['north']:
                bbox_value['north'] = sp_cov.value['north']
            if bbox_value['east'] < sp_cov.value['east']:
                bbox_value['east'] = sp_cov.value['east']

    if bbox_value:
        spatial_cov = resource.metadata.coverages.all().exclude(type='period').first()
        if spatial_cov:
            spatial_cov.type = cov_type
            spatial_cov._value = json.dumps(bbox_value)
            spatial_cov.save()
        else:
            resource.metadata.create_element("coverage", type=cov_type, value=bbox_value)

    # update resource temporal coverage
    temporal_coverages = [lf.metadata.temporal_coverage for lf in resource.logical_files
                         if lf.metadata.temporal_coverage is not None]

    date_data = {'start': None, 'end': None}
    for temp_cov in temporal_coverages:
        if date_data['start'] is None:
            date_data['start'] = temp_cov.value['start']
        else:
            if parser.parse(date_data['start']) > parser.parse(temp_cov.value['start']):
                date_data['start'] = temp_cov.value['start']

        if date_data['end'] is None:
            date_data['end'] = temp_cov.value['end']
        else:
            if parser.parse(date_data['end']) < parser.parse(temp_cov.value['end']):
                date_data['end'] = temp_cov.value['end']

    if date_data['start'] is not None and date_data['end'] is not None:
        temp_cov = resource.metadata.coverages.all().filter(type='period').first()
        if temp_cov:
            temp_cov._value = json.dumps(date_data)
            temp_cov.save()
        else:
            resource.metadata.create_element("coverage", type='period', value=date_data)