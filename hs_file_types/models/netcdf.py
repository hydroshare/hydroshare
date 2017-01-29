import os
import re
import shutil
import logging
import netCDF4

from django.core.files.uploadedfile import UploadedFile
from django.db import models
from django.contrib.postgres.fields import HStoreField, ArrayField
from django.core.exceptions import ValidationError
from django.db import models, transaction

from hs_core.hydroshare import utils
from hs_core.hydroshare.resource import delete_resource_file

from base import AbstractLogicalFile
from hs_file_types.nc_functions import nc_utils, nc_meta, nc_dump
from hs_file_types.forms import VariableValidationForm


class MetaDataManager(models.Manager):
    def __init__(self, file_metadata_type=None, *args, **kwargs):
        self.file_metadata_type = file_metadata_type
        super(MetaDataManager, self).__init__(*args, **kwargs)

    def create(self, *args, **kwargs):
        if self.file_metadata_type is None:
            kwargs.pop('file_metadata_type', None)
        return super(MetaDataManager, self).create(*args, **kwargs)

    def get_queryset(self):
        qs = super(MetaDataManager, self).get_queryset()
        if self.file_metadata_type:
            qs = qs.filter(file_metadata_type=self.file_metadata_type)
        return qs


class BaseFileMetaData(models.Model):
    file_metadata_type = models.CharField(max_length=100, default="Generic")
    # kye/value metadata
    extra_metadata = HStoreField(default={})
    keywords = ArrayField(models.CharField(max_length=100, null=True, blank=True), default=[])

    def delete_all_elements(self):
        self.extra_metadata = {}
        self.keywords = []
        self.save()

    @classmethod
    def get_metadata_element_classes(cls):
        return {'coverage': Coverage}

    @classmethod
    def get_supported_element_names(cls):
        return ['coverage']


class MetaDataElementManager(models.Manager):

    def __init__(self, element_type=None, *args, **kwargs):
        self.element_type = element_type
        super(MetaDataElementManager, self).__init__(*args, **kwargs)

    def create(self, *args, **kwargs):
        if self.element_type is None:
            kwargs.pop('element_type', None)
        return super(MetaDataElementManager, self).create(*args, **kwargs)

    def get_queryset(self):
        qs = super(MetaDataElementManager, self).get_queryset()
        if self.element_type:
            qs = qs.filter(element_type=self.element_type)
        return qs


class BaseMetaDataElement(models.Model):
    element_type = models.CharField(max_length=100, default="Generic")
    data = HStoreField(default={})
    metadata = models.ForeignKey(BaseFileMetaData)

    @classmethod
    def validate(cls, update_or_create='create', **kwargs):
        # here need to validate the dict. This needs to be used for
        # creating and updating
        data = kwargs.get('data', None)
        if data is None:
            raise ValidationError("Value for data attribute is missing")
        if not isinstance(data, dict):
            raise ValidationError("Value for data attribute must be a dict")
        metadata = kwargs.get('metadata', None)
        if metadata is None or not isinstance(metadata, BaseFileMetaData):
            raise ValidationError("Value for metadata attribute is missing")

    @classmethod
    def create(cls, **kwargs):
        return cls.objects.create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        element = BaseMetaDataElement.objects.get(id=element_id)
        element.data = kwargs['data']
        element.save()


class Coverage(BaseMetaDataElement):
    objects = MetaDataElementManager("Coverage")

    class Meta:
        verbose_name = "Coverage"
        proxy = True

    # TODO: Implement rest of this class similar to OriginalCoverage (below) and based on
    # the 'Coverage' element in hs_core


class OriginalCoverage(BaseMetaDataElement):
    objects = MetaDataElementManager("OriginalCoverage")

    class Meta:
        verbose_name = "Original Coverage"
        proxy = True

    @classmethod
    def validate(cls, update_or_create='create',  **kwargs):
        # here need to validate the dict. This needs to be used for
        # creating and updating
        super(OriginalCoverage, cls).validate(**kwargs)
        metadata = kwargs['metadata']
        element_type = kwargs['element_type']
        # Make sure we are not creating more than one element of this type
        if update_or_create == 'create':
            if BaseMetaDataElement.objects.filter(metadata=metadata,
                                                  element_type=element_type).exists():
                raise ValidationError("Original Coverage element already exists.")

        data = kwargs['data']
        # TODO: need to validate the value for each of the limits are within correct range
        # TODO: Do all these validation using form validation (see VariableFormValidation
        # implemented for the Variable element
        for key in ('northlimit', 'southlimit', 'eastlimit', 'westlimit'):
            if key not in data:
                raise ValidationError("Value for '{key}' is missing.".format(key=key))
            else:
                try:
                    float(data[key])
                except ValueError:
                    raise ValidationError("Value for '{key}' must be numeric.".format(key=key))

        if 'units' not in data:
            raise ValidationError("Value for 'units' is missing.")
        if not data['units'].strip():
            raise ValidationError("Value for 'units' is missing.")

        for key in ('projection', 'projection_string_type', 'projection_string_text', 'datum'):
            if key in data:
                if not data[key].strip():
                    if key != 'datum':
                        raise ValidationError("Value for '{key}' is missing.".format(key=key))
                if key == 'projection_string_type':
                    if data[key] not in ('WKT String', 'Proj4 String'):
                        raise ValidationError("Invalid value found for 'projection_string_type' "
                                              "attribute")

    @classmethod
    def create(cls, **kwargs):
        cls.validate(**kwargs)
        return super(OriginalCoverage, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        cls.validate(update_or_create='update', **kwargs)
        super(OriginalCoverage, cls).update(element_id, **kwargs)

    @property
    def northlimit(self):
        return self.data.get('northlimit', None)


class Variable(BaseMetaDataElement):
    objects = MetaDataElementManager("Variable")

    class Meta:
        verbose_name = "Variable"
        proxy = True

    @classmethod
    def validate(cls, update_or_create='create', **kwargs):
        # here need to validate the dict. This needs to be used for
        # creating and updating
        super(Variable, cls).validate(**kwargs)
        data = kwargs['data']
        variable_form = VariableValidationForm(data=data)
        if not variable_form.is_valid():
            raise ValidationError(variable_form.errors)

    @classmethod
    def create(cls, **kwargs):
        cls.validate(**kwargs)
        return super(Variable, cls).create(**kwargs)

    @classmethod
    def update(cls, element_id, **kwargs):
        cls.validate(update_or_create='update', **kwargs)
        super(Variable, cls).update(element_id, **kwargs)

    @property
    def name(self):
        return self.data['name']

    @property
    def shape(self):
        return self.data['shape']

    @property
    def unit(self):
        return self.data['unit']

    @property
    def type(self):
        return self.data['type']

    @property
    def descriptive_name(self):
        return self.data.get('descriptive_name', None)

    @property
    def method(self):
        return self.data.get('method', None)

    @property
    def missing_value(self):
        return self.data.get('missing_value', None)


class NetCDFFileMetaData(BaseFileMetaData):
    objects = MetaDataManager('NetCDFFileMetaData')

    class Meta:
        proxy = True

    def create_element(self, element_name, **kwargs):
        if element_name.lower() not in self.get_supported_element_names():
            raise ValidationError("{} is not a supported metadata element.".format(element_name))

        kwargs['element_type'] = element_name
        kwargs['metadata'] = self
        return self.get_metadata_element_classes()[element_name.lower()].create(**kwargs)

    def update_element(self, element_id, **kwargs):
        element = BaseMetaDataElement.objects.get(id=element_id)
        kwargs['element_type'] = element.element_type
        kwargs['metadata'] = self
        return self.get_metadata_element_classes()[element.element_type.lower()].update(
            element_id, **kwargs)

    @classmethod
    def get_metadata_element_classes(cls):
        classes = super(NetCDFFileMetaData, cls).get_metadata_element_classes()
        classes['originalcoverage'] = OriginalCoverage
        classes['variable'] = Variable
        return classes

    @property
    def original_coverage(self):
        return OriginalCoverage.objects.filter(metadata=self).first()

    @property
    def variables(self):
        return Variable.objects.filter(metadata=self).all()

    @classmethod
    def get_supported_element_names(cls):
        element_names = super(NetCDFFileMetaData, cls).get_supported_element_names()
        element_names.append('originalcoverage')
        element_names.append('variable')
        return element_names


class NetCDFLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(NetCDFFileMetaData, related_name="logical_file")
    data_type = "NetCDF data"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .nc file can be set to this logical file group"""
        return [".nc"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are: .nc and .txt"""
        return [".nc", ".txt"]

    @classmethod
    def create(cls):
        """this custom method MUST be used to create an instance of this class"""
        netcdf_metadata = NetCDFFileMetaData.objects.create(file_metadata_type='NetCDFFileMetaData')
        return cls.objects.create(metadata=netcdf_metadata)

    @classmethod
    def set_file_type(cls, resource, file_id, user):
        """
            Sets a tif or zip raster resource file to GeoRasterFile type
            :param resource: an instance of resource type CompositeResource
            :param file_id: id of the resource file to be set as GeoRasterFile type
            :param user: user who is setting the file type
            :return:
            """

        # had to import it here to avoid import loop
        from hs_core.views.utils import create_folder

        log = logging.getLogger()

        # get the file from irods
        res_file = utils.get_resource_file_by_id(resource, file_id)

        # base file name (no path included)
        file_name = utils.get_resource_file_name_and_extension(res_file)[1]
        # file name without the extension
        nc_file_name = file_name.split(".")[0]
        resource_metadata = []
        file_type_metadata = []
        files_to_add_to_resource = []
        if res_file is not None and res_file.has_generic_logical_file:
            # get the file from irods to temp dir
            temp_file = utils.get_file_from_irods(res_file)
            temp_dir = os.path.dirname(temp_file)
            files_to_add_to_resource.append(temp_file)
            # file validation and metadata extraction
            nc_dataset = nc_utils.get_nc_dataset(temp_file)
            if isinstance(nc_dataset, netCDF4.Dataset):
                # Extract the metadata from netcdf file
                try:
                    res_md_dict = nc_meta.get_nc_meta_dict(temp_file)
                    res_dublin_core_meta = res_md_dict['dublin_core_meta']
                    res_type_specific_meta = res_md_dict['type_specific_meta']
                except:
                    res_dublin_core_meta = {}
                    res_type_specific_meta = {}

                # add creator:
                if res_dublin_core_meta.get('creator_name'):
                    name = res_dublin_core_meta['creator_name']
                    email = res_dublin_core_meta.get('creator_email', '')
                    url = res_dublin_core_meta.get('creator_url', '')
                    creator = {'creator': {'name': name, 'email': email, 'homepage': url}}
                    resource_metadata.append(creator)

                # add contributor:
                if res_dublin_core_meta.get('contributor_name'):
                    name_list = res_dublin_core_meta['contributor_name'].split(',')
                    for name in name_list:
                        contributor = {'contributor': {'name': name}}
                        resource_metadata.append(contributor)

                # add title
                if resource.metadata.title.value.lower() == 'untitled resource':
                    if res_dublin_core_meta.get('title'):
                        res_title = {'title': {'value': res_dublin_core_meta['title']}}
                        resource_metadata.append(res_title)

                # add description
                if resource.metadata.description is None:
                    if res_dublin_core_meta.get('description'):
                        description = {'description': {'abstract': res_dublin_core_meta['description']}}
                        resource_metadata.append(description)

                # add keywords
                if res_dublin_core_meta.get('subject'):
                    keywords = res_dublin_core_meta['subject'].split(',')
                    for keyword in keywords:
                        resource_metadata.append({'subject': {'value': keyword}})

                # add source
                if res_dublin_core_meta.get('source'):
                    source = {'source': {'derived_from': res_dublin_core_meta['source']}}
                    resource_metadata.append(source)

                # add relation
                if res_dublin_core_meta.get('references'):
                    relation = {'relation': {'type': 'cites',
                                             'value': res_dublin_core_meta['references']}}
                    resource_metadata.append(relation)

                # TODO: Need to first implment a Coverage element based on HStore field
                # add coverage - period
                # if res_dublin_core_meta.get('period'):
                #     period = {
                #         'coverage': {'type': 'period', 'value': res_dublin_core_meta['period']}}
                #     file_type_metadata.append(period)

                # add coverage - box
                # if res_dublin_core_meta.get('box'):
                #     box = {'coverage': {'type': 'box', 'value': res_dublin_core_meta['box']}}
                #     file_type_metadata.append(box)

                # add rights
                # TODO: Should we be overriding the resource level rights metadata each time a
                # .nc file set to NetCDF file type?
                # if res_dublin_core_meta.get('rights'):
                #     raw_info = res_dublin_core_meta.get('rights')
                #     b = re.search("(?P<url>https?://[^\s]+)", raw_info)
                #     url = b.group('url') if b else ''
                #     statement = raw_info.replace(url, '') if url else raw_info
                #     rights = {'rights': {'statement': statement, 'url': url}}
                #     resource_metadata.append(rights)

                # Save extended meta to metadata variable
                for var_name, var_meta in res_type_specific_meta.items():
                    meta_info = {}
                    for element, value in var_meta.items():
                        if value != '':
                            meta_info[element] = value
                    file_type_metadata.append({'variable': {'data': meta_info}})

                # Save extended meta to original spatial coverage
                if res_dublin_core_meta.get('original-box'):
                    coverage_data = res_dublin_core_meta['original-box']
                    if res_dublin_core_meta.get('projection-info'):
                        coverage_data['projection_string_type'] = res_dublin_core_meta[
                            'projection-info']['type']
                        coverage_data['projection_string_text'] = res_dublin_core_meta[
                            'projection-info']['text']
                        coverage_data['datum'] = res_dublin_core_meta['projection-info']['datum']

                    ori_cov = {'originalcoverage': {'data': coverage_data}}
                    file_type_metadata.append(ori_cov)

                    # create the ncdump text file
                    if nc_dump.get_nc_dump_string_by_ncdump(temp_file):
                        dump_str = nc_dump.get_nc_dump_string_by_ncdump(temp_file)
                    else:
                        dump_str = nc_dump.get_nc_dump_string(temp_file)

                    if dump_str:
                        # refine dump_str first line
                        first_line = list('netcdf {0} '.format(nc_file_name))
                        first_line_index = dump_str.index('{')
                        dump_str_list = first_line + list(dump_str)[first_line_index:]
                        dump_str = "".join(dump_str_list)
                        dump_file_name = nc_file_name + '_header_info.txt'
                        dump_file = os.path.join(temp_dir, dump_file_name)
                        with open(dump_file, 'w') as dump_file_obj:
                            dump_file_obj.write(dump_str)

                        files_to_add_to_resource.append(dump_file)
                        # # write dump_str to temporary file
                        # io = StringIO.StringIO()
                        # io.write(dump_str)
                        # dump_file_name = nc_file_name + '_header_info.txt'
                        # dump_file = InMemoryUploadedFile(io, None, dump_file_name, 'text', io.len,
                        #                                  None)
                        # files.append(dump_file)

                    with transaction.atomic():
                        # first delete the raster file that we retrieved from irods
                        # for setting it to raster file type
                        delete_resource_file(resource.short_id, res_file.id, user)
                        # create a geo raster logical file object to be associated with resource files
                        logical_file = cls.create()
                        # by default set the dataset_name attribute of the logical file to the
                        # name of the file selected to set file type
                        logical_file.dataset_name = file_name
                        logical_file.save()

                        try:
                            # create a folder for the raster file type using the base file name as the
                            # name for the new folder
                            new_folder_path = 'data/contents/{}'.format(file_name)
                            # To avoid folder creation failure when there is already matching
                            # directory path, first check that the folder does not exist
                            # If folder path exists then change the folder name by adding a number
                            # to the end
                            istorage = resource.get_irods_storage()
                            counter = 0
                            new_file_name = file_name
                            while istorage.exists(os.path.join(resource.short_id, new_folder_path)):
                                new_file_name = file_name + "_{}".format(counter)
                                new_folder_path = 'data/contents/{}'.format(new_file_name)
                                counter += 1

                            fed_file_full_path = ''
                            if resource.resource_federation_path:
                                fed_file_full_path = os.path.join(resource.root_path,
                                                                  new_folder_path)

                            create_folder(resource.short_id, new_folder_path)
                            log.info("Folder created:{}".format(new_folder_path))

                            # add all new files to the resource
                            for f in files_to_add_to_resource:
                                uploaded_file = UploadedFile(file=open(f, 'rb'),
                                                             name=os.path.basename(f))
                                new_res_file = utils.add_file_to_resource(
                                    resource, uploaded_file, folder=new_file_name,
                                    fed_res_file_name_or_path=fed_file_full_path
                                )
                                # make each resource file we added as part of the logical file
                                logical_file.add_resource_file(new_res_file)

                            log.info("NetCDF file type - new files were added to the resource.")
                        except Exception as ex:
                            msg = "NetCDF file type. Error when setting file type. Error:{}"
                            msg = msg.format(ex.message)
                            log.exception(msg)
                            raise ex
                        finally:
                            # remove temp dir
                            if os.path.isdir(temp_dir):
                                shutil.rmtree(temp_dir)

                        log.info("NetCDF file type was created.")

                        # use the extracted metadata to populate resource metadata
                        for element in resource_metadata:
                            # here k is the name of the element
                            # v is a dict of all element attributes/field names and field values
                            k, v = element.items()[0]
                            resource.metadata.create_element(k, **v)

                        log.info("Resource - metadata was saved to DB")

                        # use the extracted metadata to populate file metadata
                        for element in file_type_metadata:
                            # here k is the name of the element
                            # v is a dict of all element attributes/field names and field values
                            k, v = element.items()[0]
                            logical_file.metadata.create_element(k, **v)
                        log.info("NetCDF file type - metadata was saved to DB")
            else:
                err_msg = "Not a valid NetCDF file. File type file validation failed."
                log.info(err_msg)
                # remove temp dir
                if os.path.isdir(temp_dir):
                    shutil.rmtree(temp_dir)
                raise ValidationError(err_msg)

    @property
    def supports_resource_file_move(self):
        """resource files that are part of this logical file can't be moved"""
        return False

    @property
    def supports_resource_file_rename(self):
        """resource files that are part of this logical file can't be renamed"""
        return False

    @property
    def supports_delete_folder_on_zip(self):
        """does not allow the original folder to be deleted upon zipping of that folder"""
        return False