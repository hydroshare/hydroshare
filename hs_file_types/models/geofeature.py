import os
import logging
import shutil
import zipfile
import xmltodict
from lxml import etree

from osgeo import ogr, osr

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.html import strip_tags
from django.template import Template, Context

from dominate.tags import legend, table, tbody, tr, th, div

from hs_core.models import Title, CoreMetaData
from hs_core.hydroshare import utils
from hs_core.forms import CoverageTemporalForm


from hs_geographic_feature_resource.models import GeographicFeatureMetaDataMixin, \
    OriginalCoverage, GeometryInformation, FieldInformation

from base import AbstractFileMetaData, AbstractLogicalFile

UNKNOWN_STR = "unknown"


class GeoFeatureFileMetaData(GeographicFeatureMetaDataMixin, AbstractFileMetaData):
    # the metadata element models are from the geographic feature resource type app
    model_app_label = 'hs_geographic_feature_resource'

    def get_metadata_elements(self):
        elements = super(GeoFeatureFileMetaData, self).get_metadata_elements()
        elements += [self.originalcoverage, self.geometryinformation]
        elements += list(self.fieldinformations.all())
        return elements

    @classmethod
    def get_metadata_model_classes(cls):
        metadata_model_classes = super(GeoFeatureFileMetaData, cls).get_metadata_model_classes()
        metadata_model_classes['originalcoverage'] = OriginalCoverage
        metadata_model_classes['geometryinformation'] = GeometryInformation
        metadata_model_classes['fieldinformation'] = FieldInformation
        return metadata_model_classes

    def get_html(self):
        """overrides the base class function"""

        html_string = super(GeoFeatureFileMetaData, self).get_html()
        html_string += self.geometryinformation.get_html()
        if self.spatial_coverage:
            html_string += self.spatial_coverage.get_html()
        if self.originalcoverage:
            html_string += self.originalcoverage.get_html()
        if self.temporal_coverage:
            html_string += self.temporal_coverage.get_html()

        html_string += self._get_field_informations_html()
        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def _get_field_informations_html(self):
        root_div = div(cls="col-md-12 col-sm-12 pull-left", style="margin-bottom:40px;")
        with root_div:
            legend('Field Information')
            with table(style="width: 100%;"):
                with tbody():
                    with tr(cls='row'):
                        th('Name')
                        th('Type')
                        th('Width')
                        th('Precision')

                    for field_info in self.fieldinformations.all():
                        field_info.get_html(pretty=False)

        return root_div.render()

    def get_html_forms(self, datatset_name_form=True):
        """overrides the base class function to generate html needed for metadata editing"""

        root_div = div("{% load crispy_forms_tags %}")
        with root_div:
            super(GeoFeatureFileMetaData, self).get_html_forms()
            with div(cls="col-lg-6 col-xs-12"):
                div("{% crispy geometry_information_form %}")
            with div(cls="col-lg-6 col-xs-12 col-md-pull-6", style="margin-top:40px;"):
                div("{% crispy spatial_coverage_form %}")
            with div(cls="col-lg-6 col-xs-12"):
                div("{% crispy original_coverage_form %}")

        template = Template(root_div.render())
        context_dict = dict()

        context_dict["geometry_information_form"] = self.get_geometry_information_form()
        update_action = "/hsapi/_internal/GeoFeatureLogicalFile/{0}/{1}/{2}/update-file-metadata/"
        create_action = "/hsapi/_internal/GeoFeatureLogicalFile/{0}/{1}/add-file-metadata/"
        temp_cov_form = self.get_temporal_coverage_form()
        if self.temporal_coverage:
            form_action = update_action.format(self.logical_file.id, "coverage",
                                               self.temporal_coverage.id)
            temp_cov_form.action = form_action
        else:
            form_action = create_action.format(self.logical_file.id, "coverage")
            temp_cov_form.action = form_action

        context_dict["temp_form"] = temp_cov_form
        context_dict['original_coverage_form'] = self.get_original_coverage_form()
        context_dict['spatial_coverage_form'] = self.get_spatial_coverage_form()
        context = Context(context_dict)
        rendered_html = template.render(context)
        rendered_html += self._get_field_informations_html()

        return rendered_html

    def get_geometry_information_form(self):
        return GeometryInformation.get_html_form(resource=None, element=self.geometryinformation,
                                                 file_type=True, allow_edit=False)

    def get_original_coverage_form(self):
        return OriginalCoverage.get_html_form(resource=None, element=self.originalcoverage,
                                              file_type=True, allow_edit=False)

    @classmethod
    def validate_element_data(cls, request, element_name):
        """overriding the base class method"""

        # the only metadata that we are allowing for editing is the temporal coverage
        element_name = element_name.lower()
        if element_name != 'coverage' or 'start' not in request.POST:
            err_msg = 'Data for temporal coverage is missing'
            return {'is_valid': False, 'element_data_dict': None, "errors": err_msg}

        element_form = CoverageTemporalForm(data=request.POST)

        if element_form.is_valid():
            return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
        else:
            return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}

    def get_xml(self, pretty_print=True):
        """Generates ORI+RDF xml for this aggregation metadata"""

        # get the xml root element and the xml element to which contains all other elements
        RDF_ROOT, container_to_add_to = super(GeoFeatureFileMetaData, self)._get_xml_containers()
        if self.geometryinformation:
            self.geometryinformation.add_to_xml_container(container_to_add_to)

        for fieldinfo in self.fieldinformations.all():
            fieldinfo.add_to_xml_container(container_to_add_to)

        if self.originalcoverage:
            self.originalcoverage.add_to_xml_container(container_to_add_to)

        return CoreMetaData.XML_HEADER + '\n' + etree.tostring(RDF_ROOT, pretty_print=pretty_print)


class GeoFeatureLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(GeoFeatureFileMetaData, related_name="logical_file")
    data_type = "GeographicFeature"
    verbose_content_Type = "Geographic Feature (ESRI Shapefiles)"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .zip or .shp file can be set to this logical file group"""
        # See Shapefile format:
        # http://resources.arcgis.com/en/help/main/10.2/index.html#//005600000003000000
        return (".zip", ".shp", ".shx", ".dbf", ".prj",
                ".sbx", ".sbn", ".cpg", ".xml", ".fbn",
                ".fbx", ".ain", ".aih", ".atx", ".ixs",
                ".mxs")

    @classmethod
    def get_main_file_type(cls):
        """The main file type for this aggregation"""
        return ".shp"

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are the followings"""
        return [".shp", ".shx", ".dbf", ".prj",
                ".sbx", ".sbn", ".cpg", ".xml", ".fbn",
                ".fbx", ".ain", ".aih", ".atx", ".ixs",
                ".mxs"
                ]

    @classmethod
    def create(cls):
        """this custom method MUST be used to create an instance of this class"""
        feature_metadata = GeoFeatureFileMetaData.objects.create(keywords=[])
        return cls.objects.create(metadata=feature_metadata)

    @staticmethod
    def get_aggregation_display_name():
        return 'Geographic Feature Content: The multiple files that are part of a geographic ' \
               'shapefile'

    @staticmethod
    def get_aggregation_type_name():
        return "GeographicFeatureAggregation"

    @property
    def supports_resource_file_move(self):
        """resource files that are part of this logical file can't be moved"""
        return False

    @property
    def supports_resource_file_add(self):
        """doesn't allow a resource file to be added"""
        return False

    @property
    def supports_resource_file_rename(self):
        """resource files that are part of this logical file can't be renamed"""
        return False

    @property
    def supports_delete_folder_on_zip(self):
        """does not allow the original folder to be deleted upon zipping of that folder"""
        return False

    @classmethod
    def check_files_for_aggregation_type(cls, files):
        """Checks if the specified files can be used to set this aggregation type
        :param  files: a list of ResourceFile objects

        :return If the files meet the requirements of this aggregation type, then returns this
        aggregation class name, otherwise empty string.
        """

        if _check_if_shape_files(files, temp_files=False):
            return cls.__name__
        else:
            return ""

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=None):
        """ Creates a GeoFeatureLogicalFile (aggregation) from a .shp or a .zip resource file,
        or a folder """

        log = logging.getLogger()
        res_file, folder_path = cls._validate_set_file_type_inputs(resource, file_id, folder_path)

        try:
            meta_dict, shape_files, shp_res_files = extract_metadata_and_files(resource, res_file)
        except ValidationError as ex:
            log.exception(ex.message)
            raise ex

        # hold on to temp dir for final clean up
        temp_dir = os.path.dirname(shape_files[0])
        file_name = res_file.file_name
        # file name without the extension
        base_file_name = file_name[:-len(res_file.extension)]
        xml_file = ''
        for f in shape_files:
            if f.lower().endswith('.shp.xml'):
                xml_file = f
                break

        file_folder = res_file.file_folder
        file_type_success = False
        upload_folder = ''
        res_files_to_delete = []
        aggregation_folder_created = False
        create_new_folder = cls._check_create_aggregation_folder(
            selected_res_file=res_file, selected_folder=folder_path,
            aggregation_file_count=len(shape_files))

        msg = "GeoFeature aggregation. Error when creating aggregation. Error:{}"
        with transaction.atomic():
            # create a GeoFeature logical file object to be associated with
            # resource files
            logical_file = cls.initialize(base_file_name)
            try:
                if folder_path is None:
                    # we are here means aggregation is being created by selecting a file

                    if create_new_folder:
                        # create a folder for the geofeature file type using the base file
                        # name as the name for the new folder
                        upload_folder = cls._create_aggregation_folder(resource, file_folder,
                                                                       base_file_name)

                        log.info("Folder created:{}".format(upload_folder))
                        aggregation_folder_created = True

                        if res_file.extension.lower() == ".shp":
                            # selected file is a shp file - that means we didn't create any new
                            # files - we just need to copy all the existing files to a new folder
                            # and makes those copied files part of the new aggregation
                            tgt_folder = upload_folder
                            logical_file.copy_resource_files(resource, shp_res_files, tgt_folder)
                            res_files_to_delete.extend(shp_res_files)

                        else:
                            # selected file must be a zip file - add the extracted files to
                            # the resource and make those files part of the aggregation
                            logical_file.add_files_to_resource(
                                resource=resource, files_to_add=shape_files,
                                upload_folder=upload_folder)
                            res_files_to_delete.append(res_file)
                    else:
                        upload_folder = file_folder

                        # we need to upload files to the resource only if the selected file is a zip
                        # file - since we created new files by unzipping
                        if res_file.extension.lower() == ".zip":
                            # selected file must be a zip file- add the extracted files to the
                            # resource and make those files part of the aggregation
                            logical_file.add_files_to_resource(
                                resource=resource, files_to_add=shape_files,
                                upload_folder=upload_folder)
                            res_files_to_delete.append(res_file)
                        else:
                            # selected file must be a shp file - make all files in the folder part
                            # of the aggregation
                            logical_file.add_resource_files_in_folder(resource, upload_folder)
                else:
                    # user selected a folder to create aggregation
                    # make all the files in the selected folder as part of the aggregation
                    logical_file.add_resource_files_in_folder(resource, folder_path)

                log.info("GeoFeature aggregation - files were added to the aggregation.")
                add_metadata(resource, meta_dict, xml_file, logical_file)
                log.info("GeoFeature aggregation and resource level metadata updated.")
                reset_title = logical_file.dataset_name == base_file_name
                logical_file._finalize(user, resource, folder_created=aggregation_folder_created,
                                       res_files_to_delete=res_files_to_delete,
                                       reset_title=reset_title)

                file_type_success = True
            except Exception as ex:
                msg = "GeoFeature aggregation type. Error when creating aggregation type. Error:{}"
                msg = msg.format(ex.message)
                log.exception(msg)
            finally:
                # remove temp dir
                if os.path.isdir(temp_dir):
                    shutil.rmtree(temp_dir)

        if not file_type_success:
            aggregation_from_folder = folder_path is not None
            cls._cleanup_on_fail_to_create_aggregation(user, resource, upload_folder,
                                                       file_folder, aggregation_from_folder)
            raise ValidationError(msg)

    @classmethod
    def _validate_set_file_type_inputs(cls, resource, file_id=None, folder_path=None):
        res_file, folder_path = super(GeoFeatureLogicalFile, cls)._validate_set_file_type_inputs(
            resource, file_id, folder_path)
        if folder_path is None and res_file.extension.lower() not in ('.zip', '.shp'):
            # when a file is specified by the user for creating this file type it must be a
            # zip or shp file
            raise ValidationError("Not a valid geographic feature file.")
        return res_file, folder_path

    @classmethod
    def get_primary_resouce_file(cls, resource_files):
        """Gets a resource file that has extension .shp from the list of files *resource_files* """

        res_files = [f for f in resource_files if f.extension.lower() == '.shp']
        return res_files[0] if res_files else None

    def create_aggregation_xml_documents(self, create_map_xml=True):
        super(GeoFeatureLogicalFile, self).create_aggregation_xml_documents(create_map_xml)
        self.metadata.is_dirty = False
        self.metadata.save()


def extract_metadata_and_files(resource, res_file, file_type=True):
    """
    validates shape files and extracts metadata

    :param resource: an instance of BaseResource
    :param res_file: an instance of ResourceFile
    :param file_type: A flag to control if extraction being done for file type or resource type
    :return: a dict of extracted metadata, a list file paths of shape related files on the
    temp directory, a list of resource files retrieved from iRODS for this processing
    """
    shape_files, shp_res_files = get_all_related_shp_files(resource, res_file, file_type=file_type)
    temp_dir = os.path.dirname(shape_files[0])
    if not _check_if_shape_files(shape_files):
        if res_file.extension.lower() == '.shp':
            err_msg = "One or more dependent shape files are missing at location: " \
                      "{folder_path} or one or more files are not of shape file type."
            err_msg = err_msg.format(folder_path=res_file.short_path)
        else:
            err_msg = "One or more dependent shape files are missing in the selected zip file " \
                      "or one or more files are not of shape file type."
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        raise ValidationError(err_msg)

    shp_file = ''
    for f in shape_files:
        if f.lower().endswith('.shp'):
            shp_file = f
            break
    try:
        meta_dict = extract_metadata(shp_file_full_path=shp_file)
        return meta_dict, shape_files, shp_res_files
    except Exception as ex:
        # remove temp dir
        if os.path.isdir(temp_dir):
            shutil.rmtree(temp_dir)
        if file_type:
            msg = "GeoFeature file type. Error when setting file type. Error:{}"
        else:
            msg = "Failed to parse the .shp file. Error{}"

        msg = msg.format(ex.message)
        raise ValidationError(msg)


def add_metadata(resource, metadata_dict, xml_file, logical_file=None):
    """
    creates/updates metadata at resource and file level
    :param resource: an instance of BaseResource
    :param metadata_dict: dict containing extracted metadata
    :param xml_file: file path (on temp directory) of the xml file that is part of the
    geo feature files
    :param logical_file: an instance of GeoFeatureLogicalFile if metadata needs to be part of the
    logical file
    :return:
    """
    # populate resource and logical file level metadata
    target_obj = logical_file if logical_file is not None else resource

    if "coverage" in metadata_dict.keys():
        coverage_dict = metadata_dict["coverage"]['Coverage']
        target_obj.metadata.coverages.all().filter(type='box').delete()
        target_obj.metadata.create_element('coverage',
                                           type=coverage_dict['type'],
                                           value=coverage_dict['value'])
    originalcoverage_dict = metadata_dict["originalcoverage"]['originalcoverage']
    if target_obj.metadata.originalcoverage is not None:
        target_obj.metadata.originalcoverage.delete()
    target_obj.metadata.create_element('originalcoverage', **originalcoverage_dict)
    field_info_array = metadata_dict["field_info_array"]
    target_obj.metadata.fieldinformations.all().delete()
    for field_info in field_info_array:
        field_info_dict = field_info["fieldinformation"]
        target_obj.metadata.create_element('fieldinformation', **field_info_dict)
    geometryinformation_dict = metadata_dict["geometryinformation"]
    if target_obj.metadata.geometryinformation is not None:
        target_obj.metadata.geometryinformation.delete()
    target_obj.metadata.create_element('geometryinformation', **geometryinformation_dict)
    if xml_file:
        shp_xml_metadata_list = parse_shp_xml(xml_file)
        for shp_xml_metadata in shp_xml_metadata_list:
            if 'description' in shp_xml_metadata:
                # overwrite existing description metadata - at the resource level
                if not resource.metadata.description:
                    abstract = shp_xml_metadata['description']['abstract']
                    resource.metadata.create_element('description',
                                                     abstract=abstract)
            elif 'title' in shp_xml_metadata:
                title = shp_xml_metadata['title']['value']
                title_element = resource.metadata.title
                if title_element.value.lower() == 'untitled resource':
                    resource.metadata.update_element('title', title_element.id, value=title)
                if logical_file is not None:
                    logical_file.dataset_name = title
                    logical_file.save()
            elif 'subject' in shp_xml_metadata:
                # append new keywords to existing keywords - at the resource level
                existing_keywords = [subject.value.lower() for
                                     subject in resource.metadata.subjects.all()]
                keyword = shp_xml_metadata['subject']['value']
                if keyword.lower() not in existing_keywords:
                    resource.metadata.create_element('subject', value=keyword)
                # add keywords at the logical file level
                if logical_file is not None:
                    if keyword not in logical_file.metadata.keywords:
                        logical_file.metadata.keywords += [keyword]
                        logical_file.metadata.save()


def get_all_related_shp_files(resource, selected_resource_file, file_type):
    """
    This helper function copies all the related shape files to a temp directory
    and return a list of those temp file paths as well as a list of existing related
    resource file objects
    :param resource: an instance of BaseResource to which the *selecetd_resource_file* belongs
    :param selected_resource_file: an instance of ResourceFile selected by the user to set
    GeoFeaureFile type (the file must be a .shp or a .zip file)
    :param file_type: a flag (True/False) to control resource VS file type actions
    :return: a list of temp file paths for all related shape files, and a list of corresponding
     resource file objects
    """

    def collect_shape_resource_files(res_file):
        # compare without the file extension (-4)
        if res_file.short_path.lower().endswith('.shp.xml'):
            if selected_resource_file.short_path[:-4] == res_file.short_path[:-8]:
                shape_res_files.append(f)
        elif selected_resource_file.short_path[:-4] == res_file.short_path[:-4]:
            shape_res_files.append(res_file)

    shape_temp_files = []
    shape_res_files = []
    temp_dir = ''
    if selected_resource_file.extension.lower() == '.shp':
        for f in resource.files.all():
            if f.file_folder == selected_resource_file.file_folder:
                if f.extension.lower() == '.xml' and not f.file_name.lower().endswith('.shp.xml'):
                    continue
                if f.extension.lower() in GeoFeatureLogicalFile.get_allowed_storage_file_types():
                    collect_shape_resource_files(f)

        for f in shape_res_files:
            temp_file = utils.get_file_from_irods(f)
            if not temp_dir:
                temp_dir = os.path.dirname(temp_file)
            else:
                file_temp_dir = os.path.dirname(temp_file)
                dst_dir = os.path.join(temp_dir, os.path.basename(temp_file))
                shutil.copy(temp_file, dst_dir)
                shutil.rmtree(file_temp_dir)
                temp_file = dst_dir
            shape_temp_files.append(temp_file)

    elif selected_resource_file.extension.lower() == '.zip':
        temp_file = utils.get_file_from_irods(selected_resource_file)
        temp_dir = os.path.dirname(temp_file)
        if not zipfile.is_zipfile(temp_file):
            if os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir)
            raise ValidationError('Selected file is not a zip file')
        zf = zipfile.ZipFile(temp_file, 'r')
        zf.extractall(temp_dir)
        zf.close()
        for dirpath, _, filenames in os.walk(temp_dir):
            for name in filenames:
                if name == selected_resource_file.file_name:
                    # skip the user selected zip file
                    continue
                file_path = os.path.abspath(os.path.join(dirpath, name))
                shape_temp_files.append(file_path)

        shape_res_files.append(selected_resource_file)

    return shape_temp_files, shape_res_files


def _check_if_shape_files(files, temp_files=True):
    """
    checks if the list of file temp paths in *files* are part of shape files
    must have all these file extensions: (shp, shx, dbf)
    :param files: list of files located in temp directory in django if temp_file is True, otherwise
    list of resource files are from django db
    :param  temp_files: a flag to treat list of files *files* as temp files or not
    :return: True/False
    """
    # Note: this is the original function (check_fn_for_shp) in geo feature resource receivers.py
    # used by is_shapefiles

    # at least needs to have 3 mandatory files: shp, shx, dbf
    if len(files) >= 3:
        # check that there are no files with same extension
        if temp_files:
            # files are on temp directory
            file_extensions = set([os.path.splitext(os.path.basename(f).lower())[1] for f in files])
        else:
            # files are in db
            file_extensions = set([f.extension.lower() for f in files])

        if len(file_extensions) != len(files):
            return False
        # check if there is the xml file
        xml_file = ''
        for f in files:
            if temp_files:
                # files are on temp directory
                if f.lower().endswith('.shp.xml'):
                    xml_file = f
            else:
                # files are in db
                if f.file_name.lower().endswith('.shp.xml'):
                    xml_file = f

        if temp_files:
            # files are on temp directory
            file_names = set([os.path.splitext(os.path.basename(f))[0] for f in files if
                              not f.lower().endswith('.shp.xml')])
        else:
            # files are in db
            file_names = set([os.path.splitext(os.path.basename(f.file_name))[0] for f in files if
                              not f.file_name.lower().endswith('.shp.xml')])
        if len(file_names) > 1:
            # file names are not the same
            return False

        # check if xml file name matches with other file names
        if xml_file:
            # -8 for '.shp.xml'
            if temp_files:
                # files are on temp directory
                xml_file_name = os.path.basename(xml_file)
            else:
                # files are in db
                xml_file_name = xml_file.file_name
            if xml_file_name[:-8] not in file_names:
                return False
        for ext in file_extensions:
            if ext not in GeoFeatureLogicalFile.get_allowed_storage_file_types():
                return False
        for ext in ('.shp', '.shx', '.dbf'):
            if ext not in file_extensions:
                return False
    else:
        return False

    # test if we can open the shp file
    if temp_files:
        # files are on temp directory
        shp_file = [f for f in files if f.lower().endswith('.shp')][0]
        driver = ogr.GetDriverByName('ESRI Shapefile')
        dataset = driver.Open(shp_file)
        if dataset is None:
            return False
        dataset = None

    return True


def extract_metadata(shp_file_full_path):
    """
    Collects metadata from a .shp file specified by *shp_file_full_path*
    :param shp_file_full_path:
    :return: returns a dict of collected metadata
    """

    try:
        metadata_dict = {}

        # wgs84 extent
        parsed_md_dict = parse_shp(shp_file_full_path)
        if parsed_md_dict["wgs84_extent_dict"]["westlimit"] != UNKNOWN_STR:
            wgs84_dict = parsed_md_dict["wgs84_extent_dict"]
            # if extent is a point, create point type coverage
            if wgs84_dict["westlimit"] == wgs84_dict["eastlimit"] \
               and wgs84_dict["northlimit"] == wgs84_dict["southlimit"]:
                coverage_dict = {"Coverage":
                                 {"type": "point",
                                  "value": {"east": wgs84_dict["eastlimit"],
                                            "north": wgs84_dict["northlimit"],
                                            "units": wgs84_dict["units"],
                                            "projection": wgs84_dict["projection"]}}}
            else:  # otherwise, create box type coverage
                coverage_dict = {"Coverage": {"type": "box",
                                              "value": parsed_md_dict["wgs84_extent_dict"]}}

            metadata_dict["coverage"] = coverage_dict

        # original extent
        original_coverage_dict = {}
        original_coverage_dict["originalcoverage"] = {"northlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["northlimit"],
                                                      "southlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["southlimit"],
                                                      "westlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["westlimit"],
                                                      "eastlimit":
                                                      parsed_md_dict
                                                      ["origin_extent_dict"]["eastlimit"],
                                                      "projection_string":
                                                      parsed_md_dict
                                                      ["origin_projection_string"],
                                                      "projection_name":
                                                      parsed_md_dict["origin_projection_name"],
                                                      "datum": parsed_md_dict["origin_datum"],
                                                      "unit": parsed_md_dict["origin_unit"]
                                                      }

        metadata_dict["originalcoverage"] = original_coverage_dict

        # field
        field_info_array = []
        field_name_list = parsed_md_dict["field_meta_dict"]['field_list']
        for field_name in field_name_list:
            field_info_dict_item = {}
            field_info_dict_item['fieldinformation'] = \
                parsed_md_dict["field_meta_dict"]["field_attr_dict"][field_name]
            field_info_array.append(field_info_dict_item)

        metadata_dict['field_info_array'] = field_info_array

        # geometry
        geometryinformation = {"featureCount": parsed_md_dict["feature_count"],
                               "geometryType": parsed_md_dict["geometry_type"]}

        metadata_dict["geometryinformation"] = geometryinformation
        return metadata_dict
    except:
        raise ValidationError("Parsing of shapefiles failed!")


def parse_shp(shp_file_path):
    """
    :param shp_file_path: full file path fo the .shp file

    output dictionary format
    shp_metadata_dict["origin_projection_string"]: original projection string
    shp_metadata_dict["origin_projection_name"]: origin_projection_name
    shp_metadata_dict["origin_datum"]: origin_datum
    shp_metadata_dict["origin_unit"]: origin_unit
    shp_metadata_dict["field_meta_dict"]["field_list"]: list [fieldname1, fieldname2...]
    shp_metadata_dict["field_meta_dict"]["field_attr_dic"]:
       dict {"fieldname": dict {
                             "fieldName":fieldName,
                             "fieldTypeCode":fieldTypeCode,
                             "fieldType":fieldType,
                             "fieldWidth:fieldWidth,
                             "fieldPrecision:fieldPrecision"
                              }
             }
    shp_metadata_dict["feature_count"]: feature count
    shp_metadata_dict["geometry_type"]: geometry_type
    shp_metadata_dict["origin_extent_dict"]:
    dict{"west": east, "north":north, "east":east, "south":south}
    shp_metadata_dict["wgs84_extent_dict"]:
    dict{"west": east, "north":north, "east":east, "south":south}
    """

    shp_metadata_dict = {}
    # read shapefile
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataset = driver.Open(shp_file_path)

    # get layer
    layer = dataset.GetLayer()
    # get spatialRef from layer
    spatialRef_from_layer = layer.GetSpatialRef()

    if spatialRef_from_layer is not None:
        shp_metadata_dict["origin_projection_string"] = str(spatialRef_from_layer)
        prj_name = spatialRef_from_layer.GetAttrValue('projcs')
        if prj_name is None:
            prj_name = spatialRef_from_layer.GetAttrValue('geogcs')
        shp_metadata_dict["origin_projection_name"] = prj_name

        shp_metadata_dict["origin_datum"] = spatialRef_from_layer.GetAttrValue('datum')
        shp_metadata_dict["origin_unit"] = spatialRef_from_layer.GetAttrValue('unit')
    else:
        shp_metadata_dict["origin_projection_string"] = UNKNOWN_STR
        shp_metadata_dict["origin_projection_name"] = UNKNOWN_STR
        shp_metadata_dict["origin_datum"] = UNKNOWN_STR
        shp_metadata_dict["origin_unit"] = UNKNOWN_STR

    field_list = []
    filed_attr_dic = {}
    field_meta_dict = {"field_list": field_list, "field_attr_dict": filed_attr_dic}
    shp_metadata_dict["field_meta_dict"] = field_meta_dict
    # get Attributes
    layerDefinition = layer.GetLayerDefn()
    for i in range(layerDefinition.GetFieldCount()):
        fieldName = layerDefinition.GetFieldDefn(i).GetName()
        field_list.append(fieldName)
        attr_dict = {}
        field_meta_dict["field_attr_dict"][fieldName] = attr_dict

        attr_dict["fieldName"] = fieldName
        fieldTypeCode = layerDefinition.GetFieldDefn(i).GetType()
        attr_dict["fieldTypeCode"] = fieldTypeCode
        fieldType = layerDefinition.GetFieldDefn(i).GetFieldTypeName(fieldTypeCode)
        attr_dict["fieldType"] = fieldType
        fieldWidth = layerDefinition.GetFieldDefn(i).GetWidth()
        attr_dict["fieldWidth"] = fieldWidth
        fieldPrecision = layerDefinition.GetFieldDefn(i).GetPrecision()
        attr_dict["fieldPrecision"] = fieldPrecision

    # get layer extent
    layer_extent = layer.GetExtent()

    # get feature count
    featureCount = layer.GetFeatureCount()
    shp_metadata_dict["feature_count"] = featureCount

    # get a feature from layer
    feature = layer.GetNextFeature()

    # get geometry from feature
    geom = feature.GetGeometryRef()

    # get geometry name
    shp_metadata_dict["geometry_type"] = geom.GetGeometryName()

    # reproject layer extent
    # source SpatialReference
    source = spatialRef_from_layer
    # target SpatialReference
    target = osr.SpatialReference()
    target.ImportFromEPSG(4326)

    # create two key points from layer extent
    left_upper_point = ogr.Geometry(ogr.wkbPoint)
    left_upper_point.AddPoint(layer_extent[0], layer_extent[3])  # left-upper
    right_lower_point = ogr.Geometry(ogr.wkbPoint)
    right_lower_point.AddPoint(layer_extent[1], layer_extent[2])  # right-lower

    # source map always has extent, even projection is unknown
    shp_metadata_dict["origin_extent_dict"] = {}
    shp_metadata_dict["origin_extent_dict"]["westlimit"] = layer_extent[0]
    shp_metadata_dict["origin_extent_dict"]["northlimit"] = layer_extent[3]
    shp_metadata_dict["origin_extent_dict"]["eastlimit"] = layer_extent[1]
    shp_metadata_dict["origin_extent_dict"]["southlimit"] = layer_extent[2]

    # reproject to WGS84
    shp_metadata_dict["wgs84_extent_dict"] = {}

    if source is not None:
        # define CoordinateTransformation obj
        transform = osr.CoordinateTransformation(source, target)
        # project two key points
        left_upper_point.Transform(transform)
        right_lower_point.Transform(transform)
        shp_metadata_dict["wgs84_extent_dict"]["westlimit"] = left_upper_point.GetX()
        shp_metadata_dict["wgs84_extent_dict"]["northlimit"] = left_upper_point.GetY()
        shp_metadata_dict["wgs84_extent_dict"]["eastlimit"] = right_lower_point.GetX()
        shp_metadata_dict["wgs84_extent_dict"]["southlimit"] = right_lower_point.GetY()
        shp_metadata_dict["wgs84_extent_dict"]["projection"] = "WGS 84 EPSG:4326"
        shp_metadata_dict["wgs84_extent_dict"]["units"] = "Decimal degrees"
    else:
        shp_metadata_dict["wgs84_extent_dict"]["westlimit"] = UNKNOWN_STR
        shp_metadata_dict["wgs84_extent_dict"]["northlimit"] = UNKNOWN_STR
        shp_metadata_dict["wgs84_extent_dict"]["eastlimit"] = UNKNOWN_STR
        shp_metadata_dict["wgs84_extent_dict"]["southlimit"] = UNKNOWN_STR
        shp_metadata_dict["wgs84_extent_dict"]["projection"] = UNKNOWN_STR
        shp_metadata_dict["wgs84_extent_dict"]["units"] = UNKNOWN_STR

    return shp_metadata_dict


def parse_shp_xml(shp_xml_full_path):
    """
    Parse ArcGIS 10.X ESRI Shapefile Metadata XML. file to extract metadata for the following
    elements:
        title
        abstract
        keywords
    :param shp_xml_full_path: Expected fullpath to the .shp.xml file
    :return: a list of metadata dict
    """
    metadata = []

    try:
        if os.path.isfile(shp_xml_full_path):
            with open(shp_xml_full_path) as fd:
                xml_dict = xmltodict.parse(fd.read())

                dataIdInfo_dict = xml_dict['metadata']['dataIdInfo']
                if 'idCitation' in dataIdInfo_dict:
                    if 'resTitle' in dataIdInfo_dict['idCitation']:
                        if '#text' in dataIdInfo_dict['idCitation']['resTitle']:
                            title_value = dataIdInfo_dict['idCitation']['resTitle']['#text']
                        else:
                            title_value = dataIdInfo_dict['idCitation']['resTitle']

                        title_max_length = Title._meta.get_field('value').max_length
                        if len(title_value) > title_max_length:
                            title_value = title_value[:title_max_length-1]
                        title = {'title': {'value': title_value}}
                        metadata.append(title)

                if 'idAbs' in dataIdInfo_dict:
                    description_value = strip_tags(dataIdInfo_dict['idAbs'])
                    description = {'description': {'abstract': description_value}}
                    metadata.append(description)

                if 'searchKeys' in dataIdInfo_dict:
                    searchKeys_dict = dataIdInfo_dict['searchKeys']
                    if 'keyword' in searchKeys_dict:
                        keyword_list = []
                        if type(searchKeys_dict["keyword"]) is list:
                            keyword_list += searchKeys_dict["keyword"]
                        else:
                            keyword_list.append(searchKeys_dict["keyword"])
                        for k in keyword_list:
                            metadata.append({'subject': {'value': k}})

    except Exception:
        # Catch any exception silently and return an empty list
        # Due to the variant format of ESRI Shapefile Metadata XML
        # among different ArcGIS versions, an empty list will be returned
        # if any exception occurs
        metadata = []
    finally:
        return metadata
