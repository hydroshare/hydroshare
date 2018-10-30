import os
import shutil
import logging
import sqlite3
from lxml import etree
import csv
from dateutil import parser
import tempfile

from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.template import Template, Context

from dominate.tags import div, legend, strong, form, select, option, hr, button, input, p, \
    textarea, span

from hs_core.hydroshare import utils
from hs_core.models import CoreMetaData

from hs_app_timeseries.models import TimeSeriesMetaDataMixin, AbstractCVLookupTable
from hs_app_timeseries.forms import SiteValidationForm, VariableValidationForm, \
    MethodValidationForm, ProcessingLevelValidationForm, TimeSeriesResultValidationForm, \
    UTCOffSetValidationForm

from base import AbstractFileMetaData, AbstractLogicalFile


class CVVariableType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', related_name="cv_variable_types")


class CVVariableName(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', related_name="cv_variable_names")


class CVSpeciation(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', related_name="cv_speciations")


class CVElevationDatum(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', related_name="cv_elevation_datums")


class CVSiteType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', related_name="cv_site_types")


class CVMethodType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', related_name="cv_method_types")


class CVUnitsType(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', related_name="cv_units_types")


class CVStatus(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', related_name="cv_statuses")


class CVMedium(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', related_name="cv_mediums")


class CVAggregationStatistic(AbstractCVLookupTable):
    metadata = models.ForeignKey('TimeSeriesFileMetaData', related_name="cv_aggregation_statistics")


class TimeSeriesFileMetaData(TimeSeriesMetaDataMixin, AbstractFileMetaData):
    # the metadata element models are from the timeseries resource type app
    model_app_label = 'hs_app_timeseries'
    # this is to store abstract
    abstract = models.TextField(null=True, blank=True)

    def get_metadata_elements(self):
        elements = super(TimeSeriesFileMetaData, self).get_metadata_elements()
        elements += list(self.sites)
        elements += list(self.variables)
        elements += list(self.methods)
        elements += list(self.processing_levels)
        elements += list(self.time_series_results)
        if self.utc_offset is not None:
            elements += [self.utc_offset]
        return elements

    def get_html(self, **kwargs):
        """overrides the base class function"""

        series_id = kwargs.get('series_id', None)
        if series_id is None:
            series_id = self.series_ids_with_labels.keys()[0]
        elif series_id not in self.series_ids_with_labels.keys():
            raise ValidationError("Series id:{} is not a valid series id".format(series_id))

        html_string = super(TimeSeriesFileMetaData, self).get_html()
        if self.abstract:
            abstract_div = div(cls="col-xs-12 content-block")
            with abstract_div:
                legend("Abstract")
                p(self.abstract)
            html_string += abstract_div.render()
        if self.spatial_coverage:
            html_string += self.spatial_coverage.get_html()

        if self.temporal_coverage:
            html_string += self.temporal_coverage.get_html()

        series_selection_div = self.get_series_selection_html(selected_series_id=series_id)
        with series_selection_div:
            div_meta_row = div(cls="row")
            with div_meta_row:
                # create 1st column of the row
                with div(cls="col-md-6 col-xs-12"):
                    # generate html for display of site element
                    site = self.get_element_by_series_id(series_id=series_id, elements=self.sites)
                    if site:
                        legend("Site")
                        site.get_html()

                    # generate html for variable element
                    variable = self.get_element_by_series_id(series_id=series_id,
                                                             elements=self.variables)
                    if variable:
                        legend("Variable")
                        variable.get_html()

                    # generate html for method element
                    method = self.get_element_by_series_id(series_id=series_id,
                                                           elements=self.methods)
                    if method:
                        legend("Method")
                        method.get_html()

                # create 2nd column of the row
                with div(cls="col-md-6 col-xs-12"):
                    # generate html for processing_level element
                    if self.processing_levels:
                        legend("Processing Level")
                        pro_level = self.get_element_by_series_id(series_id=series_id,
                                                                  elements=self.processing_levels)
                        if pro_level:
                            pro_level.get_html()

                    # generate html for timeseries_result element
                    if self.time_series_results:
                        legend("Time Series Result")
                        ts_result = self.get_element_by_series_id(series_id=series_id,
                                                                  elements=self.time_series_results)
                        if ts_result:
                            ts_result.get_html()

        html_string += series_selection_div.render()
        template = Template(html_string)
        context = Context({})
        return template.render(context)

    def get_html_forms(self, dataset_name_form=True, temporal_coverage=True, **kwargs):
        """overrides the base class function"""

        series_id = kwargs.get('series_id', None)
        if series_id is None:
            series_id = self.series_ids_with_labels.keys()[0]
        elif series_id not in self.series_ids_with_labels.keys():
            raise ValidationError("Series id:{} is not a valid series id".format(series_id))

        root_div = div("{% load crispy_forms_tags %}")
        with root_div:
            self.get_update_sqlite_file_html_form()
            super(TimeSeriesFileMetaData, self).get_html_forms(temporal_coverage=False)
            self.get_abstract_form()
            if self.spatial_coverage:
                self.spatial_coverage.get_html()

            if self.temporal_coverage:
                self.temporal_coverage.get_html()

            series_selection_div = self.get_series_selection_html(selected_series_id=series_id)
            with series_selection_div:
                with div(cls="row"):
                    with div(cls="col-sm-6 col-xs-12 time-series-forms hs-coordinates-picker",
                             id="site-filetype", data_coordinates_type="point"):
                        with form(id="id-site-file-type",
                                  action="{{ site_form.action }}",
                                  method="post", enctype="multipart/form-data"):
                            div("{% crispy site_form %}")
                            with div(cls="row", style="margin-top:10px;"):
                                with div(cls="col-md-offset-10 col-xs-offset-6 "
                                             "col-md-2 col-xs-6"):
                                    button("Save changes", type="button",
                                           cls="btn btn-primary pull-right",
                                           style="display: none;")
                    with div(cls="col-sm-6 col-xs-12 time-series-forms",
                             id="processinglevel-filetype"):
                        with form(id="id-processinglevel-file-type",
                                  action="{{ processinglevel_form.action }}",
                                  method="post", enctype="multipart/form-data"):
                            div("{% crispy processinglevel_form %}")
                            with div(cls="row", style="margin-top:10px;"):
                                with div(cls="col-md-offset-10 col-xs-offset-6 "
                                             "col-md-2 col-xs-6"):
                                    button("Save changes", type="button",
                                           cls="btn btn-primary pull-right",
                                           style="display: none;")
                with div(cls="row"):
                    with div(cls="col-sm-6 col-xs-12 time-series-forms", id="variable-filetype"):
                        with form(id="id-variable-file-type",
                                  action="{{ variable_form.action }}",
                                  method="post", enctype="multipart/form-data"):
                            div("{% crispy variable_form %}")
                            with div(cls="row", style="margin-top:10px;"):
                                with div(cls="col-md-offset-10 col-xs-offset-6 "
                                             "col-md-2 col-xs-6"):
                                    button("Save changes", type="button",
                                           cls="btn btn-primary pull-right",
                                           style="display: none;")

                    with div(cls="col-sm-6 col-xs-12 time-series-forms",
                             id="timeseriesresult-filetype"):
                        with form(id="id-timeseriesresult-file-type",
                                  action="{{ timeseriesresult_form.action }}",
                                  method="post", enctype="multipart/form-data"):
                            div("{% crispy timeseriesresult_form %}")
                            with div(cls="row", style="margin-top:10px;"):
                                with div(cls="col-md-offset-10 col-xs-offset-6 "
                                             "col-md-2 col-xs-6"):
                                    button("Save changes", type="button",
                                           cls="btn btn-primary pull-right",
                                           style="display: none;")

                with div(cls="row"):
                    with div(cls="col-sm-6 col-xs-12 time-series-forms", id="method-filetype"):
                        with form(id="id-method-file-type",
                                  action="{{ method_form.action }}",
                                  method="post", enctype="multipart/form-data"):
                            div("{% crispy method_form %}")
                            with div(cls="row", style="margin-top:10px;"):
                                with div(cls="col-md-offset-10 col-xs-offset-6 "
                                             "col-md-2 col-xs-6"):
                                    button("Save changes", type="button",
                                           cls="btn btn-primary pull-right",
                                           style="display: none;")
                    if self.logical_file.has_csv_file:
                        with div(cls="col-sm-6 col-xs-12 time-series-forms",
                                 id="utcoffset-filetype"):
                            with form(id="id-utcoffset-file-type",
                                      action="{{ utcoffset_form.action }}",
                                      method="post", enctype="multipart/form-data"):
                                div("{% crispy utcoffset_form %}")
                                with div(cls="row", style="margin-top:10px;"):
                                    with div(cls="col-md-offset-10 col-xs-offset-6 "
                                                 "col-md-2 col-xs-6"):
                                        button("Save changes", type="button",
                                               cls="btn btn-primary pull-right",
                                               style="display: none;")

        template = Template(root_div.render(pretty=True))
        context_dict = dict()
        context_dict["site_form"] = create_site_form(self.logical_file, series_id)
        context_dict["variable_form"] = create_variable_form(self.logical_file, series_id)
        context_dict["method_form"] = create_method_form(self.logical_file, series_id)
        context_dict["processinglevel_form"] = create_processing_level_form(self.logical_file,
                                                                            series_id)
        context_dict["timeseriesresult_form"] = create_timeseries_result_form(self.logical_file,
                                                                              series_id)
        if self.logical_file.has_csv_file:
            context_dict['utcoffset_form'] = create_utcoffset_form(self.logical_file, series_id)
        context = Context(context_dict)
        return template.render(context)

    def get_series_selection_html(self, selected_series_id, pretty=True):
        """Generates html needed to display series selection dropdown box and the
        associated form"""

        root_div = div(id="div-series-selection-file_type", cls="content-block col-xs-12 col-sm-12",
                       style="margin-top:10px;")
        heading = "Select a timeseries to see corresponding metadata (Number of time series:{})"
        if self.series_names:
            time_series_count = len(self.series_names)
        else:
            time_series_count = self.time_series_results.count()
        heading = heading.format(str(time_series_count))
        with root_div:
            strong(heading)
            action_url = "/hsapi/_internal/{logical_file_id}/series_id/resource_mode/"
            action_url += "get-timeseries-file-metadata/"
            action_url = action_url.format(logical_file_id=self.logical_file.id)
            with form(id="series-selection-form-file_type", action=action_url, method="get",
                      enctype="multipart/form-data"):
                with select(cls="form-control", id="series_id_file_type"):
                    for series_id, label in self.series_ids_with_labels.items():
                        display_text = label[:120] + "..."
                        if series_id == selected_series_id:
                            option(display_text, value=series_id, selected="selected", title=label)
                        else:
                            option(display_text, value=series_id, title=label)
            hr()
        return root_div

    def get_update_sqlite_file_html_form(self):
        form_action = "/hsapi/_internal/{}/update-sqlite-file/".format(self.id)
        style = "display:none;"
        is_dirty = 'False'
        can_update_sqlite_file = 'False'
        if self.logical_file.can_update_sqlite_file:
            can_update_sqlite_file = 'True'
        if self.is_dirty:
            style = "margin-bottom:10px"
            is_dirty = 'True'
        root_div = div(id="div-sqlite-file-update", cls="row", style=style)

        with root_div:
            with div(cls="col-sm-12"):
                with div(cls="alert alert-warning alert-dismissible", role="alert"):
                    strong("SQLite file needs to be synced with metadata changes.")
                    if self.series_names:
                        # this is the case of CSV file based time series file type
                        with div():
                            with strong():
                                span("NOTE:", style="color:red;")
                                span("New resource specific metadata elements can't be created "
                                     "after you update the SQLite file.")
                    input(id="metadata-dirty", type="hidden", value=is_dirty)
                    input(id="can-update-sqlite-file", type="hidden",
                          value=can_update_sqlite_file)
                    with form(action=form_action, method="post", id="update-sqlite-file"):
                        button("Update SQLite File", type="button", cls="btn btn-primary",
                               id="id-update-sqlite-file")

        return root_div

    def get_abstract_form(self):
        form_action = "/hsapi/_internal/{}/update-timeseries-abstract/"
        form_action = form_action.format(self.logical_file.id)
        root_div = div(cls="col-xs-12")
        if self.abstract:
            abstract = self.abstract
        else:
            abstract = ''
        with root_div:
            with form(action=form_action, id="filetype-abstract",
                      method="post", enctype="multipart/form-data"):
                div("{% csrf_token %}")
                with div(cls="form-group"):
                    with div(cls="control-group"):
                        legend('Abstract')
                        with div(cls="controls"):
                            textarea(abstract,
                                     cls="form-control input-sm textinput textInput",
                                     id="file_abstract", cols=40, rows=5,
                                     name="abstract")
                with div(cls="row", style="margin-top:10px;"):
                    with div(cls="col-md-offset-10 col-xs-offset-6 col-md-2 col-xs-6"):
                        button("Save changes", cls="btn btn-primary pull-right btn-form-submit",
                               style="display: none;", type="button")
        return root_div

    @classmethod
    def validate_element_data(cls, request, element_name):
        """overriding the base class method"""

        if element_name.lower() not in [el_name.lower() for el_name
                                        in cls.get_supported_element_names()]:
            err_msg = "{} is nor a supported metadata element for Time Series file type"
            err_msg = err_msg.format(element_name)
            return {'is_valid': False, 'element_data_dict': None, "errors": err_msg}

        validation_forms_mapping = {'site': SiteValidationForm,
                                    'variable': VariableValidationForm,
                                    'method': MethodValidationForm,
                                    'processinglevel': ProcessingLevelValidationForm,
                                    'timeseriesresult': TimeSeriesResultValidationForm,
                                    'utcoffset': UTCOffSetValidationForm}
        element_name = element_name.lower()
        if element_name not in validation_forms_mapping:
            raise ValidationError("Invalid metadata element name:{}".format(element_name))

        element_validation_form = validation_forms_mapping[element_name](request.POST)

        if element_validation_form.is_valid():
            return {'is_valid': True, 'element_data_dict': element_validation_form.cleaned_data}
        else:
            return {'is_valid': False, 'element_data_dict': None,
                    "errors": element_validation_form.errors}

    def get_xml(self, pretty_print=True):
        """Generates ORI+RDF xml for this aggregation metadata"""

        # get the xml root element and the xml element to which contains all other elements
        RDF_ROOT, container_to_add_to = super(TimeSeriesFileMetaData, self)._get_xml_containers()
        NAMESPACES = CoreMetaData.NAMESPACES
        if self.abstract:
            dc_description = etree.SubElement(container_to_add_to,
                                              '{%s}description' % NAMESPACES['dc'])
            dc_des_rdf_Desciption = etree.SubElement(dc_description,
                                                     '{%s}Description' % NAMESPACES['rdf'])
            dcterms_abstract = etree.SubElement(dc_des_rdf_Desciption,
                                                '{%s}abstract' % NAMESPACES['dcterms'])
            dcterms_abstract.text = self.abstract

        add_to_xml_container_helper(self, container_to_add_to)
        return CoreMetaData.XML_HEADER + '\n' + etree.tostring(RDF_ROOT, encoding='UTF-8',
                                                               pretty_print=pretty_print)


class TimeSeriesLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(TimeSeriesFileMetaData, related_name="logical_file")
    data_type = "TimeSeries"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .csv and .sqlite file can be set to this logical file group"""
        return [".csv", ".sqlite"]

    @classmethod
    def get_main_file_type(cls):
        """The main file type for this aggregation"""
        return ".sqlite"

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are: .csv and .sqlite"""
        return [".csv", ".sqlite"]

    @staticmethod
    def get_aggregation_display_name():
        return 'Time Series Content: One or more time series held in an ODM2 format SQLite ' \
               'file and optional source comma separated (.csv) files'

    @staticmethod
    def get_aggregation_type_name():
        return "TimeSeriesAggregation"

    # used in discovery faceting to aggregate native and composite content types
    @staticmethod
    def get_discovery_content_type():
        """Return a human-readable content type for discovery.
        This must agree between Composite Types and native types.
        """
        return "Time Series"

    @classmethod
    def create(cls):
        """this custom method MUST be used to create an instance of this class"""
        ts_metadata = TimeSeriesFileMetaData.objects.create(keywords=[])
        return cls.objects.create(metadata=ts_metadata)

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

    @property
    def has_sqlite_file(self):
        for res_file in self.files.all():
            if res_file.extension == '.sqlite':
                return True
        return False

    @property
    def has_csv_file(self):
        for res_file in self.files.all():
            if res_file.extension == '.csv':
                return True
        return False

    @property
    def can_add_blank_sqlite_file(self):
        """use this property as a guard to decide when to add a blank SQLIte file
        to the resource
        """
        if self.has_sqlite_file:
            return False
        if not self.has_csv_file:
            return False

        return True

    @property
    def can_update_sqlite_file(self):
        """guard property to determine when the sqlite file can be updated as result of
        metadata changes
        """
        return self.has_sqlite_file and self.metadata.has_all_required_elements()

    def update_sqlite_file(self, user):
        # get sqlite resource file
        sqlite_file_to_update = None
        for res_file in self.files.all():
            if res_file.extension == '.sqlite':
                sqlite_file_to_update = res_file
                break
        if sqlite_file_to_update is None:
            raise Exception("Logical file has no SQLite file. Invalid operation.")
        sqlite_file_update(self, sqlite_file_to_update, user)

    @classmethod
    def check_files_for_aggregation_type(cls, files):
        """Checks if the specified files can be used to set this aggregation type
        :param  files: a list of ResourceFile objects

        :return If the files meet the requirements of this aggregation type, then returns this
        aggregation class name, otherwise empty string.
        """
        if len(files) != 1:
            # no files or more than 1 file
            return ""

        if files[0].extension not in cls.get_allowed_uploaded_file_types():
            return ""

        return cls.__name__

    @classmethod
    def set_file_type(cls, resource, user, file_id=None, folder_path=None):
        """ Creates a TimeSeriesLogicalFile (aggregation) from a sqlite or a csv resource file, or
        a folder
        """

        log = logging.getLogger()
        res_file, folder_path = cls._validate_set_file_type_inputs(resource, file_id, folder_path)

        # get the file from irods to temp dir
        temp_res_file = utils.get_file_from_irods(res_file)
        # hold on to temp dir for final clean up
        temp_dir = os.path.dirname(temp_res_file)
        if res_file.extension == '.sqlite':
            validate_err_message = validate_odm2_db_file(temp_res_file)
        else:
            # file must be a csv file
            validate_err_message = validate_csv_file(temp_res_file)

        if validate_err_message is not None:
            log.error(validate_err_message)
            # remove temp dir
            if os.path.isdir(temp_dir):
                shutil.rmtree(temp_dir)
            raise ValidationError(validate_err_message)

        file_name = res_file.file_name
        # file name without the extension - used for naming the new aggregation folder
        base_file_name = file_name[:-len(res_file.extension)]
        file_folder = res_file.file_folder
        aggregation_folder_created = False
        res_files_to_delete = []
        # determine if we need to create a new folder for the aggregation
        create_new_folder = cls._check_create_aggregation_folder(
            selected_res_file=res_file, selected_folder=folder_path,
            aggregation_file_count=1)
        file_type_success = False
        upload_folder = ''
        msg = "TimeSeries aggregation type. Error when creating. Error:{}"
        with transaction.atomic():
            # create a TimeSerisLogicalFile object to be associated with resource file
            logical_file = cls.initialize(base_file_name)

            try:
                if folder_path is None:
                    # we are here means aggregation is being created by selecting a file
                    # create a folder for the timeseries file type using the base file
                    # name as the name for the new folder if the file is not in a folder already
                    if create_new_folder:
                        # create a folder for the raster file type using the base file name
                        # as the name for the new folder
                        upload_folder = cls._create_aggregation_folder(resource, file_folder,
                                                                       base_file_name)

                        log.info("Folder created:{}".format(upload_folder))
                        aggregation_folder_created = True
                        tgt_folder = upload_folder
                        files_to_copy = [res_file]
                        logical_file.copy_resource_files(resource, files_to_copy,
                                                         tgt_folder)
                        res_files_to_delete.append(res_file)
                    else:
                        # selected file is already in a folder
                        upload_folder = file_folder
                        # make the selected file part of the aggregation
                        logical_file.add_resource_file(res_file)
                else:
                    # folder has been selected for creating the aggregation
                    upload_folder = folder_path
                    # make the selected file part of the aggregation
                    logical_file.add_resource_file(res_file)

                # add a blank ODM2 sqlite file to the resource and make it part of the aggregation
                # if we creating aggregation from a csv file
                if res_file.extension.lower() == '.csv':
                    new_sqlite_file = add_blank_sqlite_file(resource, upload_folder)
                    logical_file.add_resource_file(new_sqlite_file)

                info_msg = "TimeSeries aggregation type - {} file was added to the aggregation."
                info_msg = info_msg.format(res_file.extension[1:])
                log.info(info_msg)
                # extract metadata if we are creating aggregation form a sqlite file
                if res_file.extension.lower() == ".sqlite":
                    extract_err_message = extract_metadata(resource, temp_res_file, logical_file)
                    if extract_err_message:
                        raise ValidationError(extract_err_message)
                    log.info("Metadata was extracted from sqlite file.")
                else:
                    # populate CV metadata django models from the blank sqlite file
                    extract_cv_metadata_from_blank_sqlite_file(logical_file)

                reset_title = logical_file.dataset_name == base_file_name
                logical_file._finalize(user, resource, folder_created=aggregation_folder_created,
                                       res_files_to_delete=res_files_to_delete,
                                       reset_title=reset_title)

                file_type_success = True
            except Exception as ex:
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

    def get_copy(self):
        """Overrides the base class method"""

        copy_of_logical_file = super(TimeSeriesLogicalFile, self).get_copy()
        copy_of_logical_file.metadata.abstract = self.metadata.abstract
        copy_of_logical_file.metadata.value_counts = self.metadata.value_counts
        copy_of_logical_file.metadata.is_dirty = self.metadata.is_dirty
        copy_of_logical_file.metadata.save()
        copy_of_logical_file.save()

        copy_cv_terms(src_metadata=self.metadata, tgt_metadata=copy_of_logical_file.metadata)
        return copy_of_logical_file

    @classmethod
    def get_primary_resouce_file(cls, resource_files):
        """Gets a resource file that has extension .sqlite or .csv from the list of files
        *resource_files*
        """

        res_files = [f for f in resource_files if f.extension.lower() == '.sqlite' or
                     f.extension.lower() == '.csv']
        return res_files[0] if res_files else None

    @classmethod
    def _validate_set_file_type_inputs(cls, resource, file_id=None, folder_path=None):
        res_file, folder_path = super(TimeSeriesLogicalFile, cls)._validate_set_file_type_inputs(
            resource, file_id, folder_path)
        if folder_path is None and res_file.extension.lower() not in ('.sqlite', '.csv'):
            # when a file is specified by the user for creating this file type it must be a
            # sqlite or csv file
            raise ValidationError("Not a valid timeseries file.")
        return res_file, folder_path


def copy_cv_terms(src_metadata, tgt_metadata):
    """copy CV related metadata items from the source metadata *src_metadata*
    to the target metadata *tgt_metadata*
    This is a helper function to support resource copy or version creation
    :param  src_metadata: an instance of TimeSeriesMetaData or TimeSeriesFileMetaData from which
    cv related metadata items to copy from
    :param  tgt_metadata: an instance of TimeSeriesMetaData or TimeSeriesFileMetaData to which
    cv related metadata items to copy to
    Note: src_metadata and tgt_metadata must be of the same type
    """

    # create CV terms
    def copy_cv_terms(cv_class, cv_terms_to_copy):
        for cv_term in cv_terms_to_copy:
            cv_class.objects.create(metadata=tgt_metadata, name=cv_term.name,
                                    term=cv_term.term,
                                    is_dirty=cv_term.is_dirty)

    if type(src_metadata) != type(tgt_metadata):
        raise ValidationError("Source metadata and target metadata objects must be of the "
                              "same type")

    if not isinstance(src_metadata, TimeSeriesFileMetaData):
        from hs_app_timeseries.models import CVElevationDatum as R_CVElevationDatum, \
            CVMedium as R_CVMedium, CVMethodType as R_CVMethodType, \
            CVAggregationStatistic as R_CVAggregationStatistic, CVSpeciation as R_CVSpeciation, \
            CVVariableType as R_CVVariableType, CVVariableName as R_CVVariableName, \
            CVSiteType as R_CVSiteType, CVStatus as R_CVStatus, CVUnitsType as R_CVUnitsType
        cv_variable_type = R_CVVariableType
        cv_variable_name = R_CVVariableName
        cv_speciation = R_CVSpeciation
        cv_elevation_datum = R_CVElevationDatum
        cv_site_type = R_CVSiteType
        cv_method_type = R_CVMethodType
        cv_units_type = R_CVUnitsType
        cv_status = R_CVStatus
        cv_medium = R_CVMedium
        cv_aggr_statistics = R_CVAggregationStatistic
    else:
        cv_variable_type = CVVariableType
        cv_variable_name = CVVariableName
        cv_speciation = CVSpeciation
        cv_elevation_datum = CVElevationDatum
        cv_site_type = CVSiteType
        cv_method_type = CVMethodType
        cv_units_type = CVUnitsType
        cv_status = CVStatus
        cv_medium = CVMedium
        cv_aggr_statistics = CVAggregationStatistic

    copy_cv_terms(cv_variable_type, src_metadata.cv_variable_types.all())
    copy_cv_terms(cv_variable_name, src_metadata.cv_variable_names.all())
    copy_cv_terms(cv_speciation, src_metadata.cv_speciations.all())
    copy_cv_terms(cv_elevation_datum, src_metadata.cv_elevation_datums.all())
    copy_cv_terms(cv_site_type, src_metadata.cv_site_types.all())
    copy_cv_terms(cv_method_type, src_metadata.cv_method_types.all())
    copy_cv_terms(cv_units_type, src_metadata.cv_units_types.all())
    copy_cv_terms(cv_status, src_metadata.cv_statuses.all())
    copy_cv_terms(cv_medium, src_metadata.cv_mediums.all())
    copy_cv_terms(cv_aggr_statistics, src_metadata.cv_aggregation_statistics.all())

    # set all cv terms is_dirty to false
    cv_terms = list(tgt_metadata.cv_variable_names.all()) + \
        list(tgt_metadata.cv_variable_types.all()) + \
        list(tgt_metadata.cv_speciations.all()) + \
        list(tgt_metadata.cv_site_types.all()) + \
        list(tgt_metadata.cv_elevation_datums.all()) + \
        list(tgt_metadata.cv_method_types.all()) + \
        list(tgt_metadata.cv_units_types.all()) + \
        list(tgt_metadata.cv_statuses.all()) + \
        list(tgt_metadata.cv_mediums.all()) + \
        list(tgt_metadata.cv_aggregation_statistics.all())
    for cv_term in cv_terms:
        cv_term.is_dirty = False
        cv_term.save()


def validate_odm2_db_file(sqlite_file_path):
    """
    Validates if the sqlite file *sqlite_file_path* is a valid ODM2 sqlite file
    :param sqlite_file_path: path of the sqlite file to be validated
    :return: If validation fails then an error message string is returned otherwise None is
    returned
    """
    err_message = "Uploaded file is not a valid ODM2 SQLite file."
    log = logging.getLogger()
    try:
        con = sqlite3.connect(sqlite_file_path)
        with con:

            # TODO: check that each of the core tables has the necessary columns

            # check that the uploaded file has all the tables from ODM2Core and the CV tables
            cur = con.cursor()
            odm2_core_table_names = ['People', 'Affiliations', 'SamplingFeatures', 'ActionBy',
                                     'Organizations', 'Methods', 'FeatureActions', 'Actions',
                                     'RelatedActions', 'Results', 'Variables', 'Units', 'Datasets',
                                     'DatasetsResults', 'ProcessingLevels', 'TaxonomicClassifiers',
                                     'CV_VariableType', 'CV_VariableName', 'CV_Speciation',
                                     'CV_SiteType', 'CV_ElevationDatum', 'CV_MethodType',
                                     'CV_UnitsType', 'CV_Status', 'CV_Medium',
                                     'CV_AggregationStatistic']
            # check the tables exist
            for table_name in odm2_core_table_names:
                cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type=? AND name=?",
                            ("table", table_name))
                result = cur.fetchone()
                if result[0] <= 0:
                    err_message += " Table '{}' is missing.".format(table_name)
                    log.info(err_message)
                    return err_message

            # check that the tables have at least one record
            for table_name in odm2_core_table_names:
                if table_name == 'RelatedActions' or table_name == 'TaxonomicClassifiers':
                    continue
                cur.execute("SELECT COUNT(*) FROM " + table_name)
                result = cur.fetchone()
                if result[0] <= 0:
                    err_message += " Table '{}' has no records.".format(table_name)
                    log.info(err_message)
                    return err_message
        return None
    except sqlite3.Error, e:
        sqlite_err_msg = str(e.args[0])
        log.error(sqlite_err_msg)
        return sqlite_err_msg
    except Exception, e:
        log.error(e.message)
        return e.message


def validate_csv_file(csv_file_path):
    err_message = "Uploaded file is not a valid timeseries csv file."
    log = logging.getLogger()
    with open(csv_file_path, 'r') as fl_obj:
        csv_reader = csv.reader(fl_obj, delimiter=',')
        # read the first row
        header = csv_reader.next()
        header = [el.strip() for el in header]
        if any(len(h) == 0 for h in header):
            err_message += " Column heading is missing."
            log.error(err_message)
            return err_message

        # check that there are at least 2 headings
        if len(header) < 2:
            err_message += " There needs to be at least 2 columns of data."
            log.error(err_message)
            return err_message

        # check the header has only string values
        for hdr in header:
            try:
                float(hdr)
                err_message += " Column heading must be a string."
                log.error(err_message)
                return err_message
            except ValueError:
                pass

        # check that there are no duplicate column headings
        if len(header) != len(set(header)):
            err_message += " There are duplicate column headings."
            log.error(err_message)
            return err_message

        # process data rows
        for row in csv_reader:
            # check that data row has the same number of columns as the header
            if len(row) != len(header):
                err_message += " Number of columns in the header is not same as the data columns."
                log.error(err_message)
                return err_message
            # check that the first column data is of type datetime
            try:
                parser.parse(row[0])
            except Exception:
                err_message += " Data for the first column must be a date value."
                log.error(err_message)
                return err_message

            # check that the data values (2nd column onwards) are of numeric
            for data_value in row[1:]:
                try:
                    float(data_value)
                except ValueError:
                    err_message += " Data values must be numeric."
                    log.error(err_message)
                    return err_message

    return None


def add_blank_sqlite_file(resource, upload_folder):
    """add the blank SQLite file to the resource to the specified folder **upload_folder**
    :param  upload_folder: folder to which the blank sqlite file needs to be uploaded
    :return the uploaded resource file object - an instance of ResourceFile
    """

    log = logging.getLogger()

    # add the sqlite file to the resource
    odm2_sqlite_file_name = 'ODM2.sqlite'
    odm2_sqlite_file = 'hs_app_timeseries/files/{}'.format(odm2_sqlite_file_name)

    try:
        uploaded_file = UploadedFile(file=open(odm2_sqlite_file, 'rb'),
                                     name=os.path.basename(odm2_sqlite_file))
        new_res_file = utils.add_file_to_resource(
            resource, uploaded_file, folder=upload_folder
        )

        log.info("Blank SQLite file was added.")
        return new_res_file
    except Exception as ex:
        log.exception("Error when adding the blank SQLite file. Error:{}".format(ex.message))
        raise ex


def extract_metadata(resource, sqlite_file_name, logical_file=None):
    """
    Extracts metadata from the sqlite file *sqlite_file_name" and adds metadata at the resource
    and/or file level
    :param resource: an instance of BaseResource
    :param sqlite_file_name: path of the sqlite file
    :param logical_file: an instance of TimeSeriesLogicalFile if metadata needs to be part of the
    logical file
    :return:
    """
    err_message = "Not a valid ODM2 SQLite file"
    log = logging.getLogger()
    target_obj = logical_file if logical_file is not None else resource
    try:
        con = sqlite3.connect(sqlite_file_name)
        with con:
            # get the records in python dictionary format
            con.row_factory = sqlite3.Row
            cur = con.cursor()

            # populate the lookup CV tables that are needed later for metadata editing
            target_obj.metadata.create_cv_lookup_models(cur)

            # read data from necessary tables and create metadata elements
            # extract core metadata

            # extract abstract and title
            cur.execute("SELECT DataSetTitle, DataSetAbstract FROM DataSets")
            dataset = cur.fetchone()
            # update title element
            if dataset["DataSetTitle"]:
                if logical_file is None \
                        or resource.metadata.title.value.lower() == 'untitled resource':
                    resource.metadata.update_element('title', element_id=resource.metadata.title.id,
                                                     value=dataset["DataSetTitle"])
                if logical_file is not None:
                    logical_file.dataset_name = dataset["DataSetTitle"].strip()
                    logical_file.save()

            # create abstract/description element
            if dataset["DataSetAbstract"]:
                if logical_file is None or resource.metadata.description is None:
                    resource.metadata.create_element('description',
                                                     abstract=dataset["DataSetAbstract"])
                if logical_file is not None:
                    logical_file.metadata.abstract = dataset["DataSetAbstract"].strip()
                    logical_file.metadata.save()

            # extract keywords/subjects
            # these are the comma separated values in the VariableNameCV column of the Variables
            # table
            cur.execute("SELECT VariableID, VariableNameCV FROM Variables")
            variables = cur.fetchall()
            keyword_list = []
            for variable in variables:
                keywords = variable["VariableNameCV"].split(",")
                keyword_list = keyword_list + keywords

            if logical_file is None:
                # use set() to remove any duplicate keywords
                for kw in set(keyword_list):
                    resource.metadata.create_element("subject", value=kw)
            else:
                # file type
                logical_file.metadata.keywords = list(set(keyword_list))
                logical_file.metadata.save()
                # update resource level keywords
                resource_keywords = [subject.value.lower() for subject in
                                     resource.metadata.subjects.all()]
                for kw in logical_file.metadata.keywords:
                    if kw.lower() not in resource_keywords:
                        resource.metadata.create_element('subject', value=kw)

            # find the contributors for metadata
            file_type = logical_file is not None
            _extract_creators_contributors(resource, cur, file_type=file_type)

            # extract coverage data
            _extract_coverage_metadata(resource, cur, logical_file)

            # extract extended metadata
            cur.execute("SELECT * FROM Sites")
            sites = cur.fetchall()
            is_create_multiple_site_elements = len(sites) > 1

            cur.execute("SELECT * FROM Variables")
            variables = cur.fetchall()
            is_create_multiple_variable_elements = len(variables) > 1

            cur.execute("SELECT * FROM Methods")
            methods = cur.fetchall()
            is_create_multiple_method_elements = len(methods) > 1

            cur.execute("SELECT * FROM ProcessingLevels")
            processing_levels = cur.fetchall()
            is_create_multiple_processinglevel_elements = len(processing_levels) > 1

            cur.execute("SELECT * FROM TimeSeriesResults")
            timeseries_results = cur.fetchall()
            is_create_multiple_timeseriesresult_elements = len(timeseries_results) > 1

            cur.execute("SELECT * FROM Results")
            results = cur.fetchall()
            for result in results:
                # extract site element data
                # Start with Results table to -> FeatureActions table -> SamplingFeatures table
                # check if we need to create multiple site elements
                cur.execute("SELECT * FROM FeatureActions WHERE FeatureActionID=?",
                            (result["FeatureActionID"],))
                feature_action = cur.fetchone()
                if is_create_multiple_site_elements or len(target_obj.metadata.sites) == 0:
                    cur.execute("SELECT * FROM SamplingFeatures WHERE SamplingFeatureID=?",
                                (feature_action["SamplingFeatureID"],))
                    sampling_feature = cur.fetchone()

                    cur.execute("SELECT * FROM Sites WHERE SamplingFeatureID=?",
                                (feature_action["SamplingFeatureID"],))
                    site = cur.fetchone()
                    if not any(sampling_feature["SamplingFeatureCode"] == s.site_code for s
                               in target_obj.metadata.sites):

                        data_dict = {}
                        data_dict['series_ids'] = [result["ResultUUID"]]
                        data_dict['site_code'] = sampling_feature["SamplingFeatureCode"]
                        data_dict['site_name'] = sampling_feature["SamplingFeatureName"]
                        if sampling_feature["Elevation_m"]:
                            data_dict["elevation_m"] = sampling_feature["Elevation_m"]

                        if sampling_feature["ElevationDatumCV"]:
                            data_dict["elevation_datum"] = sampling_feature["ElevationDatumCV"]

                        if site["SiteTypeCV"]:
                            data_dict["site_type"] = site["SiteTypeCV"]

                        data_dict["latitude"] = site["Latitude"]
                        data_dict["longitude"] = site["Longitude"]

                        # create site element
                        target_obj.metadata.create_element('site', **data_dict)
                    else:
                        matching_site = [s for s in target_obj.metadata.sites if
                                         s.site_code == sampling_feature["SamplingFeatureCode"]][0]
                        _update_element_series_ids(matching_site, result["ResultUUID"])
                else:
                    _update_element_series_ids(target_obj.metadata.sites[0], result["ResultUUID"])

                # extract variable element data
                # Start with Results table to -> Variables table
                if is_create_multiple_variable_elements or len(target_obj.metadata.variables) == 0:
                    cur.execute("SELECT * FROM Variables WHERE VariableID=?",
                                (result["VariableID"],))
                    variable = cur.fetchone()
                    if not any(variable["VariableCode"] == v.variable_code for v
                               in target_obj.metadata.variables):

                        data_dict = {}
                        data_dict['series_ids'] = [result["ResultUUID"]]
                        data_dict['variable_code'] = variable["VariableCode"]
                        data_dict["variable_name"] = variable["VariableNameCV"]
                        data_dict['variable_type'] = variable["VariableTypeCV"]
                        data_dict["no_data_value"] = variable["NoDataValue"]
                        if variable["VariableDefinition"]:
                            data_dict["variable_definition"] = variable["VariableDefinition"]

                        if variable["SpeciationCV"]:
                            data_dict["speciation"] = variable["SpeciationCV"]

                        # create variable element
                        target_obj.metadata.create_element('variable', **data_dict)
                    else:
                        matching_variable = [v for v in target_obj.metadata.variables if
                                             v.variable_code == variable["VariableCode"]][0]
                        _update_element_series_ids(matching_variable, result["ResultUUID"])

                else:
                    _update_element_series_ids(target_obj.metadata.variables[0],
                                               result["ResultUUID"])

                # extract method element data
                # Start with Results table -> FeatureActions table to -> Actions table to ->
                # Method table
                if is_create_multiple_method_elements or len(target_obj.metadata.methods) == 0:
                    cur.execute("SELECT MethodID from Actions WHERE ActionID=?",
                                (feature_action["ActionID"],))
                    action = cur.fetchone()
                    cur.execute("SELECT * FROM Methods WHERE MethodID=?", (action["MethodID"],))
                    method = cur.fetchone()
                    if not any(method["MethodCode"] == m.method_code for m
                               in target_obj.metadata.methods):

                        data_dict = {}
                        data_dict['series_ids'] = [result["ResultUUID"]]
                        data_dict['method_code'] = method["MethodCode"]
                        data_dict["method_name"] = method["MethodName"]
                        data_dict['method_type'] = method["MethodTypeCV"]

                        if method["MethodDescription"]:
                            data_dict["method_description"] = method["MethodDescription"]

                        if method["MethodLink"]:
                            data_dict["method_link"] = method["MethodLink"]

                        # create method element
                        target_obj.metadata.create_element('method', **data_dict)
                    else:
                        matching_method = [m for m in target_obj.metadata.methods if
                                           m.method_code == method["MethodCode"]][0]
                        _update_element_series_ids(matching_method, result["ResultUUID"])
                else:
                    _update_element_series_ids(target_obj.metadata.methods[0], result["ResultUUID"])

                # extract processinglevel element data
                # Start with Results table to -> ProcessingLevels table
                if is_create_multiple_processinglevel_elements \
                        or len(target_obj.metadata.processing_levels) == 0:
                    cur.execute("SELECT * FROM ProcessingLevels WHERE ProcessingLevelID=?",
                                (result["ProcessingLevelID"],))
                    pro_level = cur.fetchone()
                    if not any(pro_level["ProcessingLevelCode"] == p.processing_level_code for p
                               in target_obj.metadata.processing_levels):

                        data_dict = {}
                        data_dict['series_ids'] = [result["ResultUUID"]]
                        data_dict['processing_level_code'] = pro_level["ProcessingLevelCode"]
                        if pro_level["Definition"]:
                            data_dict["definition"] = pro_level["Definition"]

                        if pro_level["Explanation"]:
                            data_dict["explanation"] = pro_level["Explanation"]

                        # create processinglevel element
                        target_obj.metadata.create_element('processinglevel', **data_dict)
                    else:
                        matching_pro_level = [p for p in target_obj.metadata.processing_levels if
                                              p.processing_level_code == pro_level[
                                                  "ProcessingLevelCode"]][0]
                        _update_element_series_ids(matching_pro_level, result["ResultUUID"])
                else:
                    _update_element_series_ids(target_obj.metadata.processing_levels[0],
                                               result["ResultUUID"])

                # extract data for TimeSeriesResult element
                # Start with Results table
                if is_create_multiple_timeseriesresult_elements \
                        or len(target_obj.metadata.time_series_results) == 0:
                    data_dict = {}
                    data_dict['series_ids'] = [result["ResultUUID"]]
                    if result["StatusCV"] is not None:
                        data_dict["status"] = result["StatusCV"]
                    else:
                        data_dict["status"] = ""
                    data_dict["sample_medium"] = result["SampledMediumCV"]
                    data_dict["value_count"] = result["ValueCount"]

                    cur.execute("SELECT * FROM Units WHERE UnitsID=?", (result["UnitsID"],))
                    unit = cur.fetchone()
                    data_dict['units_type'] = unit["UnitsTypeCV"]
                    data_dict['units_name'] = unit["UnitsName"]
                    data_dict['units_abbreviation'] = unit["UnitsAbbreviation"]

                    cur.execute("SELECT AggregationStatisticCV FROM TimeSeriesResults WHERE "
                                "ResultID=?", (result["ResultID"],))
                    ts_result = cur.fetchone()
                    data_dict["aggregation_statistics"] = ts_result["AggregationStatisticCV"]

                    # create the TimeSeriesResult element
                    target_obj.metadata.create_element('timeseriesresult', **data_dict)
                else:
                    _update_element_series_ids(target_obj.metadata.time_series_results[0],
                                               result["ResultUUID"])

            return None

    except sqlite3.Error as ex:
        sqlite_err_msg = str(ex.args[0])
        log.error(sqlite_err_msg)
        return sqlite_err_msg
    except Exception as ex:
        log.error(ex.message)
        return err_message


def extract_cv_metadata_from_blank_sqlite_file(target):
    """extracts CV metadata from the blank sqlite file and populates the django metadata
    models - this function is applicable only in the case of a CSV file being used as the
    source of time series data
    :param  target: an instance of TimeSeriesResource or TimeSeriesLogicalFile
    """

    # find the csv file
    csv_res_file = None
    for f in target.files.all():
        if f.extension == ".csv":
            csv_res_file = f
            break
    if csv_res_file is None:
        raise Exception("No CSV file was found")

    # copy the blank sqlite file to a temp directory
    temp_dir = tempfile.mkdtemp()
    odm2_sqlite_file_name = 'ODM2.sqlite'
    odm2_sqlite_file = 'hs_app_timeseries/files/{}'.format(odm2_sqlite_file_name)
    target_temp_sqlite_file = os.path.join(temp_dir, odm2_sqlite_file_name)
    shutil.copy(odm2_sqlite_file, target_temp_sqlite_file)

    con = sqlite3.connect(target_temp_sqlite_file)
    with con:
        # get the records in python dictionary format
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        # populate the lookup CV tables that are needed later for metadata editing
        target.metadata.create_cv_lookup_models(cur)

    # save some data from the csv file
    # get the csv file from iRODS to a temp directory
    temp_csv_file = utils.get_file_from_irods(csv_res_file)
    with open(temp_csv_file, 'r') as fl_obj:
        csv_reader = csv.reader(fl_obj, delimiter=',')
        # read the first row - header
        header = csv_reader.next()
        # read the 1st data row
        start_date_str = csv_reader.next()[0]
        last_row = None
        data_row_count = 1
        for row in csv_reader:
            last_row = row
            data_row_count += 1
        end_date_str = last_row[0]

        # save the series names along with number of data points for each series
        # columns starting with the 2nd column are data series names
        value_counts = {}
        for data_col_name in header[1:]:
            value_counts[data_col_name] = str(data_row_count)

        metadata_obj = target.metadata
        metadata_obj.value_counts = value_counts
        metadata_obj.save()

        # create the temporal coverage element
        target.metadata.create_element('coverage', type='period',
                                       value={'start': start_date_str, 'end': end_date_str})

    # cleanup the temp sqlite file directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    # cleanup the temp csv file
    if os.path.exists(temp_csv_file):
        shutil.rmtree(os.path.dirname(temp_csv_file))


def _extract_creators_contributors(resource, cur, file_type=False):
    # check if the AuthorList table exists
    authorlists_table_exists = False
    cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type=? AND name=?",
                ("table", "AuthorLists"))
    qry_result = cur.fetchone()
    if qry_result[0] > 0:
        authorlists_table_exists = True

    # contributors are People associated with the Actions that created the Result
    cur.execute("SELECT * FROM People")
    people = cur.fetchall()
    is_create_multiple_author_elements = len(people) > 1

    cur.execute("SELECT FeatureActionID FROM Results")
    results = cur.fetchall()
    authors_data_dict = {}
    author_ids_already_used = []
    for result in results:
        if is_create_multiple_author_elements or (len(resource.metadata.creators.all()) == 1 and
                                                  len(resource.metadata.contributors.all()) == 0):
            cur.execute("SELECT ActionID FROM FeatureActions WHERE FeatureActionID=?",
                        (result["FeatureActionID"],))
            feature_actions = cur.fetchall()
            for feature_action in feature_actions:
                cur.execute("SELECT ActionID FROM Actions WHERE ActionID=?",
                            (feature_action["ActionID"],))

                actions = cur.fetchall()
                for action in actions:
                    # get the AffiliationID from the ActionsBy table for the matching ActionID
                    cur.execute("SELECT AffiliationID FROM ActionBy WHERE ActionID=?",
                                (action["ActionID"],))
                    actionby_rows = cur.fetchall()

                    for actionby in actionby_rows:
                        # get the matching Affiliations records
                        cur.execute("SELECT * FROM Affiliations WHERE AffiliationID=?",
                                    (actionby["AffiliationID"],))
                        affiliation_rows = cur.fetchall()
                        for affiliation in affiliation_rows:
                            # get records from the People table
                            if affiliation['PersonID'] not in author_ids_already_used:
                                author_ids_already_used.append(affiliation['PersonID'])
                                cur.execute("SELECT * FROM People WHERE PersonID=?",
                                            (affiliation['PersonID'],))
                                person = cur.fetchone()

                                # get person organization name - get only one organization name
                                organization = None
                                if affiliation['OrganizationID']:
                                    cur.execute("SELECT OrganizationName FROM Organizations WHERE "
                                                "OrganizationID=?",
                                                (affiliation["OrganizationID"],))
                                    organization = cur.fetchone()

                                # create contributor metadata elements
                                person_name = person["PersonFirstName"]
                                if person['PersonMiddleName']:
                                    person_name = person_name + " " + person['PersonMiddleName']

                                person_name = person_name + " " + person['PersonLastName']
                                data_dict = {}
                                data_dict['name'] = person_name
                                if affiliation['PrimaryPhone']:
                                    data_dict["phone"] = affiliation["PrimaryPhone"]
                                if affiliation["PrimaryEmail"]:
                                    data_dict["email"] = affiliation["PrimaryEmail"]
                                if affiliation["PrimaryAddress"]:
                                    data_dict["address"] = affiliation["PrimaryAddress"]
                                if organization:
                                    data_dict["organization"] = organization[0]

                                # check if this person is an author (creator)
                                author = None
                                if authorlists_table_exists:
                                    cur.execute("SELECT * FROM AuthorLists WHERE PersonID=?",
                                                (person['PersonID'],))
                                    author = cur.fetchone()

                                if author:
                                    # save the extracted creator data in the dictionary
                                    # so that we can later sort it based on author order
                                    # and then create the creator metadata elements
                                    authors_data_dict[author["AuthorOrder"]] = data_dict
                                else:
                                    # create contributor metadata element
                                    if not file_type:
                                        resource.metadata.create_element('contributor', **data_dict)
                                    elif not resource.metadata.contributors.filter(
                                            name=data_dict['name']).exists():
                                        resource.metadata.create_element('contributor', **data_dict)

    # TODO: extraction of creator data has not been tested as the sample database does not have
    # any records in the AuthorLists table
    authors_data_dict_sorted_list = sorted(authors_data_dict,
                                           key=lambda key: authors_data_dict[key])
    for data_dict in authors_data_dict_sorted_list:
        # create creator metadata element
        if not file_type:
            resource.metadata.create_element('creator', **data_dict)
        elif not resource.metadata.creators.filter(name=data_dict['name']).exists():
            resource.metadata.create_element('creator', **data_dict)


def _extract_coverage_metadata(resource, cur, logical_file=None):
    # get point or box coverage
    target_obj = logical_file if logical_file is not None else resource
    cur.execute("SELECT * FROM Sites")
    sites = cur.fetchall()
    if len(sites) == 1:
        site = sites[0]
        if site["Latitude"] and site["Longitude"]:
            value_dict = {'east': site["Longitude"], 'north': site["Latitude"],
                          'units': "Decimal degrees"}
            # get spatial reference
            if site["SpatialReferenceID"]:
                cur.execute("SELECT * FROM SpatialReferences WHERE SpatialReferenceID=?",
                            (site["SpatialReferenceID"],))
                spatialref = cur.fetchone()
                if spatialref:
                    if spatialref["SRSName"]:
                        value_dict["projection"] = spatialref["SRSName"]

            target_obj.metadata.create_element('coverage', type='point', value=value_dict)
    else:
        # in case of multiple sites we will create one coverage element of type 'box'
        bbox = {'northlimit': -90, 'southlimit': 90, 'eastlimit': -180, 'westlimit': 180,
                'projection': 'Unknown', 'units': "Decimal degrees"}
        for site in sites:
            if site["Latitude"]:
                if bbox['northlimit'] < site["Latitude"]:
                    bbox['northlimit'] = site["Latitude"]
                if bbox['southlimit'] > site["Latitude"]:
                    bbox['southlimit'] = site["Latitude"]

            if site["Longitude"]:
                if bbox['eastlimit'] < site['Longitude']:
                    bbox['eastlimit'] = site['Longitude']

                if bbox['westlimit'] > site['Longitude']:
                    bbox['westlimit'] = site['Longitude']

            if bbox['projection'] == 'Unknown':
                if site["SpatialReferenceID"]:
                    cur.execute("SELECT * FROM SpatialReferences WHERE SpatialReferenceID=?",
                                (site["SpatialReferenceID"],))
                    spatialref = cur.fetchone()
                    if spatialref:
                        if spatialref["SRSName"]:
                            bbox['projection'] = spatialref["SRSName"]

            if bbox['projection'] == 'Unknown':
                bbox['projection'] = 'WGS 84 EPSG:4326'

        target_obj.metadata.create_element('coverage', type='box', value=bbox)

    # extract temporal coverage
    cur.execute("SELECT MAX(ValueDateTime) AS 'EndDate', MIN(ValueDateTime) AS 'BeginDate' "
                "FROM TimeSeriesResultValues")

    dates = cur.fetchone()
    begin_date = dates['BeginDate']
    end_date = dates['EndDate']

    # create coverage element
    value_dict = {"start": begin_date, "end": end_date}
    target_obj.metadata.create_element('coverage', type='period', value=value_dict)


def _update_element_series_ids(element, series_id):
    element.series_ids = element.series_ids + [series_id]
    element.save()


def create_utcoffset_form(target, selected_series_id):
    """
    Creates an instance of UTCOffSetForm
    :param target: an instance of TimeSeriesResource or TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of UTCOffSetForm
    """
    from hs_app_timeseries.forms import UTCOffSetForm
    if isinstance(target, TimeSeriesLogicalFile):
        res_short_id = None
        file_type = True
        target_id = target.id
    else:
        res_short_id = target.short_id
        file_type = False
        target_id = target.short_id
    utc_offset = target.metadata.utc_offset
    utcoffset_form = UTCOffSetForm(instance=utc_offset,
                                   res_short_id=res_short_id,
                                   element_id=utc_offset.id if utc_offset else None,
                                   selected_series_id=selected_series_id,
                                   file_type=file_type)
    if utc_offset is not None:
        utcoffset_form.action = _get_element_update_form_action('utcoffset', target_id,
                                                                utc_offset.id, file_type=file_type)
    else:
        utcoffset_form.action = _get_element_create_form_action('utcoffset', target_id,
                                                                file_type=file_type)
    return utcoffset_form


def create_site_form(target, selected_series_id):
    """
    Creates an instance of SiteForm
    :param target: an instance of TimeSeriesResource or TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of SiteForm
    """
    from hs_app_timeseries.forms import SiteForm
    if isinstance(target, TimeSeriesLogicalFile):
        res_short_id = None
        file_type = True
        target_id = target.id
    else:
        res_short_id = target.short_id
        file_type = False
        target_id = target.short_id

    if target.metadata.sites:
        site = target.metadata.sites.filter(
            series_ids__contains=[selected_series_id]).first()
        site_form = SiteForm(instance=site, res_short_id=res_short_id,
                             element_id=site.id if site else None,
                             cv_site_types=target.metadata.cv_site_types.all(),
                             cv_elevation_datums=target.metadata.cv_elevation_datums.all(),
                             show_site_code_selection=len(target.metadata.series_names) > 0,
                             available_sites=target.metadata.sites,
                             selected_series_id=selected_series_id,
                             file_type=file_type)

        if site is not None:
            site_form.action = _get_element_update_form_action('site', target_id, site.id,
                                                               file_type=file_type)
            site_form.number = site.id

            site_form.set_dropdown_widgets(site_form.initial['site_type'],
                                           site_form.initial['elevation_datum'])
        else:
            site_form.action = _get_element_create_form_action('site', target_id,
                                                               file_type=file_type)
            site_form.set_dropdown_widgets()

    else:
        # this case can happen only in case of CSV upload
        site_form = SiteForm(instance=None, res_short_id=res_short_id,
                             element_id=None,
                             cv_site_types=target.metadata.cv_site_types.all(),
                             cv_elevation_datums=target.metadata.cv_elevation_datums.all(),
                             selected_series_id=selected_series_id,
                             file_type=file_type)

        site_form.action = _get_element_create_form_action('site', target_id, file_type=file_type)
        site_form.set_dropdown_widgets()
    return site_form


def create_variable_form(target, selected_series_id):
    """
    Creates an instance of VariableForm
    :param target: an instance of TimeSeriesResource or TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of VariableForm
    """
    from hs_app_timeseries.forms import VariableForm
    if isinstance(target, TimeSeriesLogicalFile):
        res_short_id = None
        file_type = True
        target_id = target.id
    else:
        res_short_id = target.short_id
        file_type = False
        target_id = target.short_id

    if target.metadata.variables:
        variable = target.metadata.variables.filter(
            series_ids__contains=[selected_series_id]).first()
        variable_form = VariableForm(
            instance=variable, res_short_id=res_short_id,
            element_id=variable.id if variable else None,
            cv_variable_types=target.metadata.cv_variable_types.all(),
            cv_variable_names=target.metadata.cv_variable_names.all(),
            cv_speciations=target.metadata.cv_speciations.all(),
            show_variable_code_selection=len(target.metadata.series_names) > 0,
            available_variables=target.metadata.variables,
            selected_series_id=selected_series_id,
            file_type=file_type)

        if variable is not None:
            variable_form.action = _get_element_update_form_action('variable', target_id,
                                                                   variable.id, file_type=file_type)
            variable_form.number = variable.id

            variable_form.set_dropdown_widgets(variable_form.initial['variable_type'],
                                               variable_form.initial['variable_name'],
                                               variable_form.initial['speciation'])
        else:
            # this case can only happen in case of csv upload
            variable_form.action = _get_element_create_form_action('variable', target_id,
                                                                   file_type=file_type)
            variable_form.set_dropdown_widgets()
    else:
        # this case can happen only in case of CSV upload
        variable_form = VariableForm(instance=None, res_short_id=res_short_id,
                                     element_id=None,
                                     cv_variable_types=target.metadata.cv_variable_types.all(),
                                     cv_variable_names=target.metadata.cv_variable_names.all(),
                                     cv_speciations=target.metadata.cv_speciations.all(),
                                     available_variables=target.metadata.variables,
                                     selected_series_id=selected_series_id,
                                     file_type=file_type)

        variable_form.action = _get_element_create_form_action('variable', target_id,
                                                               file_type=file_type)
        variable_form.set_dropdown_widgets()

    return variable_form


def create_method_form(target, selected_series_id):
    """
    Creates an instance of MethodForm
    :param target: an instance of TimeSeriesResource or TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of MethodForm
    """

    from hs_app_timeseries.forms import MethodForm

    if isinstance(target, TimeSeriesLogicalFile):
        res_short_id = None
        file_type = True
        target_id = target.id
    else:
        res_short_id = target.short_id
        file_type = False
        target_id = target.short_id

    if target.metadata.methods:
        method = target.metadata.methods.filter(
            series_ids__contains=[selected_series_id]).first()
        method_form = MethodForm(instance=method, res_short_id=res_short_id,
                                 element_id=method.id if method else None,
                                 cv_method_types=target.metadata.cv_method_types.all(),
                                 show_method_code_selection=len(target.metadata.series_names) > 0,
                                 available_methods=target.metadata.methods,
                                 selected_series_id=selected_series_id,
                                 file_type=file_type)

        if method is not None:
            method_form.action = _get_element_update_form_action('method', target_id, method.id,
                                                                 file_type=file_type)
            method_form.number = method.id
            method_form.set_dropdown_widgets(method_form.initial['method_type'])
        else:
            # this case can only happen in case of csv upload
            method_form.action = _get_element_create_form_action('method', target_id,
                                                                 file_type=file_type)
            method_form.set_dropdown_widgets()
    else:
        # this case can happen only in case of CSV upload
        method_form = MethodForm(instance=None, res_short_id=res_short_id,
                                 element_id=None,
                                 cv_method_types=target.metadata.cv_method_types.all(),
                                 selected_series_id=selected_series_id, file_type=file_type)

        method_form.action = _get_element_create_form_action('method', target_id,
                                                             file_type=file_type)
        method_form.set_dropdown_widgets()
    return method_form


def create_processing_level_form(target, selected_series_id):
    """
    Creates an instance of ProcessingLevelForm
    :param target: an instance of TimeSeriesResource or TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of ProcessingLevelForm
    """
    from hs_app_timeseries.forms import ProcessingLevelForm

    if isinstance(target, TimeSeriesLogicalFile):
        res_short_id = None
        file_type = True
        target_id = target.id
    else:
        res_short_id = target.short_id
        file_type = False
        target_id = target.short_id

    if target.metadata.processing_levels:
        pro_level = target.metadata.processing_levels.filter(
            series_ids__contains=[selected_series_id]).first()
        processing_level_form = ProcessingLevelForm(
            instance=pro_level,
            res_short_id=res_short_id,
            element_id=pro_level.id if pro_level else None,
            show_processing_level_code_selection=len(target.metadata.series_names) > 0,
            available_processinglevels=target.metadata.processing_levels,
            selected_series_id=selected_series_id,
            file_type=file_type)

        if pro_level is not None:
            processing_level_form.action = _get_element_update_form_action('processinglevel',
                                                                           target_id,
                                                                           pro_level.id,
                                                                           file_type=file_type)
            processing_level_form.number = pro_level.id
        else:
            processing_level_form.action = _get_element_create_form_action('processinglevel',
                                                                           target_id,
                                                                           file_type=file_type)
    else:
        # this case can happen only in case of CSV upload
        processing_level_form = ProcessingLevelForm(instance=None, res_short_id=res_short_id,
                                                    element_id=None,
                                                    selected_series_id=selected_series_id,
                                                    file_type=file_type)
        processing_level_form.action = _get_element_create_form_action('processinglevel', target_id,
                                                                       file_type=file_type)

    return processing_level_form


def create_timeseries_result_form(target, selected_series_id):
    """
    Creates an instance of ProcessingLevelForm
    :param target: an instance of TimeSeriesResource or TimeSeriesLogicalFile
    :param selected_series_id: id of the selected time series
    :return: an instance of ProcessingLevelForm
    """
    from hs_app_timeseries.forms import TimeSeriesResultForm
    if isinstance(target, TimeSeriesLogicalFile):
        res_short_id = None
        file_type = True
        target_id = target.id
    else:
        res_short_id = target.short_id
        file_type = False
        target_id = target.short_id

    time_series_result = target.metadata.time_series_results.filter(
        series_ids__contains=[selected_series_id]).first()
    timeseries_result_form = TimeSeriesResultForm(
        instance=time_series_result,
        res_short_id=res_short_id,
        element_id=time_series_result.id if time_series_result else None,
        cv_sample_mediums=target.metadata.cv_mediums.all(),
        cv_units_types=target.metadata.cv_units_types.all(),
        cv_aggregation_statistics=target.metadata.cv_aggregation_statistics.all(),
        cv_statuses=target.metadata.cv_statuses.all(),
        selected_series_id=selected_series_id,
        file_type=file_type)

    if time_series_result is not None:
        timeseries_result_form.action = _get_element_update_form_action('timeseriesresult',
                                                                        target_id,
                                                                        time_series_result.id,
                                                                        file_type=file_type)
        timeseries_result_form.number = time_series_result.id
        timeseries_result_form.set_dropdown_widgets(timeseries_result_form.initial['sample_medium'],
                                                    timeseries_result_form.initial['units_type'],
                                                    timeseries_result_form.initial[
                                                        'aggregation_statistics'],
                                                    timeseries_result_form.initial['status'])
    else:
        series_ids = target.metadata.series_ids_with_labels
        if series_ids and selected_series_id is not None:
            selected_series_label = series_ids[selected_series_id]
        else:
            selected_series_label = ''
        ts_result_value_count = None
        if target.metadata.series_names and selected_series_id is not None:
            sorted_series_names = sorted(target.metadata.series_names)
            selected_series_name = sorted_series_names[int(selected_series_id)]
            ts_result_value_count = int(target.metadata.value_counts[selected_series_name])
        timeseries_result_form.set_dropdown_widgets()
        timeseries_result_form.set_series_label(selected_series_label)
        timeseries_result_form.set_value_count(ts_result_value_count)
        timeseries_result_form.action = _get_element_create_form_action('timeseriesresult',
                                                                        target_id,
                                                                        file_type=file_type)
    return timeseries_result_form


def sqlite_file_update(instance, sqlite_res_file, user):
    """updates the sqlite file on metadata changes
    :param  instance: an instance of either TimeSeriesLogicalFile or TimeSeriesResource
    """

    if not instance.metadata.is_dirty:
        return
    is_file_type = isinstance(instance, TimeSeriesLogicalFile)
    if not is_file_type:
        # adding the blank sqlite file is necessary only in case of TimeSeriesResource
        if not instance.has_sqlite_file and instance.can_add_blank_sqlite_file:
            add_blank_sqlite_file(instance, upload_folder=None)
        # instance.add_blank_sqlite_file(user)

    log = logging.getLogger()

    sqlite_file_to_update = sqlite_res_file
    # retrieve the sqlite file from iRODS and save it to temp directory
    temp_sqlite_file = utils.get_file_from_irods(sqlite_file_to_update)

    if instance.has_csv_file and instance.metadata.series_names:
        instance.metadata.populate_blank_sqlite_file(temp_sqlite_file, user)
    else:
        try:
            con = sqlite3.connect(temp_sqlite_file)
            with con:
                # get the records in python dictionary format
                con.row_factory = sqlite3.Row
                cur = con.cursor()
                # update dataset table for changes in title and abstract
                instance.metadata.update_datasets_table(con, cur)
                if not is_file_type:
                    # here we are updating sqlite file time series resource

                    # update people related tables (People, Affiliations, Organizations, ActionBy)
                    # using updated creators/contributors in django db

                    # insert record to People table
                    people_data = instance.metadata.update_people_table_insert(con, cur)

                    # insert record to Organizations table
                    instance.metadata.update_organizations_table_insert(con, cur)

                    # insert record to Affiliations table
                    instance.metadata.update_affiliations_table_insert(con, cur, people_data)

                    # insert record to ActionBy table
                    instance.metadata.update_actionby_table_insert(con, cur, people_data)

                # since we are allowing user to set the UTC offset in case of CSV file
                # upload we have to update the actions table
                if instance.metadata.utc_offset is not None:
                    instance.metadata.update_utcoffset_related_tables(con, cur)

                # update resource/file specific metadata
                instance.metadata.update_variables_table(con, cur)
                instance.metadata.update_methods_table(con, cur)
                instance.metadata.update_processinglevels_table(con, cur)
                instance.metadata.update_sites_related_tables(con, cur)
                instance.metadata.update_results_related_tables(con, cur)

                # update CV terms related tables
                instance.metadata.update_CV_tables(con, cur)

                # push the updated sqlite file to iRODS
                utils.replace_resource_file_on_irods(temp_sqlite_file, sqlite_file_to_update,
                                                     user)
                metadata = instance.metadata
                if is_file_type:
                    instance.create_aggregation_xml_documents(create_map_xml=False)
                metadata.is_dirty = False
                metadata.save()
                log.info("SQLite file update was successful.")
        except sqlite3.Error as ex:
            sqlite_err_msg = str(ex.args[0])
            log.error("Failed to update SQLite file. Error:{}".format(sqlite_err_msg))
            raise Exception(sqlite_err_msg)
        except Exception as ex:
            log.exception("Failed to update SQLite file. Error:{}".format(ex.message))
            raise ex
        finally:
            if os.path.exists(temp_sqlite_file):
                shutil.rmtree(os.path.dirname(temp_sqlite_file))


def add_to_xml_container_helper(target_obj, container):
    """Generates xml+rdf representation of all metadata elements associated with the *target_obj*
    :param  target_obj: either an instance of TimeSeriesMetaData or TimeSeriesFileMetaData
    :param  container: xml container element to which xml nodes need to be added
    """

    for time_series_result in target_obj.time_series_results:
        ts_result_root_container = time_series_result.add_to_xml_container(
            container=container)
        # generate xml for 'site' element
        sites = [site for site in target_obj.sites if time_series_result.series_ids[0] in
                 site.series_ids]
        if sites:
            site = sites[0]
            site.add_to_xml_container(container=ts_result_root_container)

        # generate xml for 'variable' element
        variables = [variable for variable in target_obj.variables if
                     time_series_result.series_ids[0] in variable.series_ids]
        if variables:
            variable = variables[0]
            variable.add_to_xml_container(container=ts_result_root_container)

        # generate xml for 'method' element
        methods = [method for method in target_obj.methods if time_series_result.series_ids[0] in
                   method.series_ids]
        if methods:
            method = methods[0]
            method.add_to_xml_container(container=ts_result_root_container)

        # generate xml for 'processing_level' element
        processing_levels = [processing_level for processing_level in target_obj.processing_levels
                             if time_series_result.series_ids[0] in processing_level.series_ids]
        if processing_levels:
            processing_level = processing_levels[0]
            processing_level.add_to_xml_container(container=ts_result_root_container)


def _get_element_update_form_action(element_name, target_id, element_id, file_type=False):
    if not file_type:
        # TimeSeries resource level metadata update
        # target_id is resource short_id
        action = "/hsapi/_internal/{res_id}/{element_name}/{element_id}/update-metadata/"
        return action.format(res_id=target_id, element_name=element_name, element_id=element_id)
    else:
        # Time series file type metadata update
        # target_id is logical file object id
        action = "/hsapi/_internal/TimeSeriesLogicalFile/{logical_file_id}/{element_name}/" \
                 "{element_id}/update-file-metadata/"
        return action.format(logical_file_id=target_id, element_name=element_name,
                             element_id=element_id)


def _get_element_create_form_action(element_name, target_id, file_type=False):
    if not file_type:
        # TimeSeries resource level metadata update
        # target_id is resource short_id
        action = "/hsapi/_internal/{res_id}/{element_name}/create-metadata/"
        return action.format(res_id=target_id, element_name=element_name)
    else:
        # Time series file type metadata update
        # target_id is logical file object id
        action = "/hsapi/_internal/TimeSeriesLogicalFile/{logical_file_id}/{element_name}/" \
                 "add-file-metadata/"
        return action.format(logical_file_id=target_id, element_name=element_name)
