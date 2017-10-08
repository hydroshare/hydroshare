import os
import shutil
import logging
import csv
from dateutil import parser

from django.dispatch import receiver

from hs_core.signals import pre_create_resource, pre_add_files_to_resource, \
    pre_delete_file_from_resource, post_add_files_to_resource, post_create_resource, \
    pre_metadata_element_create, pre_metadata_element_update
from hs_core.hydroshare import utils, delete_resource_file_only
from hs_app_timeseries.models import TimeSeriesResource, TimeSeriesMetaData
from forms import SiteValidationForm, VariableValidationForm, MethodValidationForm, \
    ProcessingLevelValidationForm, TimeSeriesResultValidationForm, UTCOffSetValidationForm

from hs_file_types.models.timeseries import extract_metadata, validate_odm2_db_file, \
    extract_cv_metadata_from_blank_sqlite_file, validate_csv_file

FILE_UPLOAD_ERROR_MESSAGE = "(Uploaded file was not added to the resource)"


@receiver(pre_create_resource, sender=TimeSeriesResource)
def resource_pre_create_handler(sender, **kwargs):
    # if needed more actions can be taken here before the TimeSeries resource is created
    pass


@receiver(pre_add_files_to_resource, sender=TimeSeriesResource)
def pre_add_files_to_resource_handler(sender, **kwargs):
    # file upload is not allowed if the resource already
    # has either a sqlite file or a csv file
    resource = kwargs['resource']
    files = kwargs['files']
    validate_files_dict = kwargs['validate_files']
    source_names = kwargs['source_names']

    if __debug__:
        assert(isinstance(source_names, list))

    if files or source_names:
        if resource.has_sqlite_file or resource.has_csv_file:
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'Resource already has the necessary content files.'


@receiver(pre_delete_file_from_resource, sender=TimeSeriesResource)
def pre_delete_file_from_resource_handler(sender, **kwargs):
    # if any of the content files (sqlite or csv) is deleted then reset the 'is_dirty' attribute
    # for all extracted metadata to False
    resource = kwargs['resource']

    def reset_metadata_elements_is_dirty(elements):
        # filter out any non-dirty element
        elements = [element for element in elements if element.is_dirty]
        for element in elements:
            element.is_dirty = False
            element.save()

    if resource.metadata.is_dirty:
        TimeSeriesMetaData.objects.filter(id=resource.metadata.id).update(is_dirty=False)
        # metadata object is_dirty attribute for some reason can't be set using the following
        # 2 lines of code
        # resource.metadata.is_dirty=False
        # resource.metadata.save()

        reset_metadata_elements_is_dirty(resource.metadata.sites.all())
        reset_metadata_elements_is_dirty(resource.metadata.variables.all())
        reset_metadata_elements_is_dirty(resource.metadata.methods.all())
        reset_metadata_elements_is_dirty(resource.metadata.processing_levels.all())
        reset_metadata_elements_is_dirty(resource.metadata.time_series_results.all())
        reset_metadata_elements_is_dirty(resource.metadata.cv_variable_types.all())
        reset_metadata_elements_is_dirty(resource.metadata.cv_variable_names.all())
        reset_metadata_elements_is_dirty(resource.metadata.cv_speciations.all())
        reset_metadata_elements_is_dirty(resource.metadata.cv_elevation_datums.all())
        reset_metadata_elements_is_dirty(resource.metadata.cv_site_types.all())
        reset_metadata_elements_is_dirty(resource.metadata.cv_method_types.all())
        reset_metadata_elements_is_dirty(resource.metadata.cv_units_types.all())
        reset_metadata_elements_is_dirty(resource.metadata.cv_statuses.all())
        reset_metadata_elements_is_dirty(resource.metadata.cv_aggregation_statistics.all())


@receiver(post_add_files_to_resource, sender=TimeSeriesResource)
def post_add_files_to_resource_handler(sender, **kwargs):
    resource = kwargs['resource']
    files = kwargs['files']
    validate_files_dict = kwargs['validate_files']
    user = kwargs['user']
    source_names = kwargs['source_names']

    if __debug__:
        assert(isinstance(source_names, list))

    if files:
        file_name = files[0].name
    elif source_names:
        file_name = os.path.basename(source_names[0])

    # extract metadata from the just uploaded file
    uploaded_file_to_process = None
    uploaded_file_ext = ''
    for res_file in resource.files.all():
        _, res_file_name, uploaded_file_ext = utils.get_resource_file_name_and_extension(res_file)
        if res_file_name == file_name:
            uploaded_file_to_process = res_file
            break

    if uploaded_file_to_process:
        if uploaded_file_ext == ".sqlite":
            _process_uploaded_sqlite_file(user, resource, uploaded_file_to_process,
                                          validate_files_dict,
                                          delete_existing_metadata=True)

        elif uploaded_file_ext == ".csv":
            _process_uploaded_csv_file(resource, uploaded_file_to_process, validate_files_dict,
                                       user, delete_existing_metadata=True)


@receiver(post_create_resource, sender=TimeSeriesResource)
def post_create_resource_handler(sender, **kwargs):
    resource = kwargs['resource']
    validate_files_dict = kwargs['validate_files']
    user = kwargs['user']

    # extract metadata from the just uploaded file
    res_file = resource.files.all().first()
    if res_file:
        # check if the uploaded file is a sqlite file or csv file
        file_ext = utils.get_resource_file_name_and_extension(res_file)[2]
        if file_ext == '.sqlite':
            # metadata can exist at this point if a timeseries resource is created
            # using REST API since the API caller can pass metadata information. Before
            # metadata can be extracted from the sqlite file and populated to database, existing
            # metadata needs to be deleted.
            _process_uploaded_sqlite_file(user, resource, res_file, validate_files_dict,
                                          delete_existing_metadata=True)
        elif file_ext == '.csv':
            _process_uploaded_csv_file(resource, res_file, validate_files_dict, user,
                                       delete_existing_metadata=False)
        # since we are extracting metadata after resource creation
        # metadata xml files need to be regenerated - so need to set the
        # dirty bag flags
        utils.set_dirty_bag_flag(resource)


def _process_uploaded_csv_file(resource, res_file, validate_files_dict, user,
                               delete_existing_metadata=True):
    # get the csv file from iRODS to a temp directory
    fl_obj_name = utils.get_file_from_irods(res_file)
    validate_err_message = validate_csv_file(fl_obj_name)
    if not validate_err_message:
        # first delete relevant existing metadata elements
        if delete_existing_metadata:
            TimeSeriesMetaData.objects.filter(id=resource.metadata.id).update(is_dirty=False)
            _delete_extracted_metadata(resource)

        # delete the sqlite file if it exists
        _delete_resource_file(resource, ".sqlite")

        # add the blank sqlite file
        resource.add_blank_sqlite_file(user)

        # populate CV metadata django models from the blank sqlite file
        extract_cv_metadata_from_blank_sqlite_file(resource)

    else:  # file validation failed
        # delete the invalid file just uploaded
        delete_resource_file_only(resource, res_file)
        validate_files_dict['are_files_valid'] = False
        validate_err_message += "{}".format(FILE_UPLOAD_ERROR_MESSAGE)
        validate_files_dict['message'] = validate_err_message

    # cleanup the temp csv file
    if os.path.exists(fl_obj_name):
        shutil.rmtree(os.path.dirname(fl_obj_name))


def _process_uploaded_sqlite_file(user, resource, res_file, validate_files_dict,
                                  delete_existing_metadata=True):
    # check if it a sqlite file
    fl_ext = utils.get_resource_file_name_and_extension(res_file)[2]

    if fl_ext == '.sqlite':
        # get the file from iRODS to a temp directory
        fl_obj_name = utils.get_file_from_irods(res_file)
        validate_err_message = validate_odm2_db_file(fl_obj_name)
        if not validate_err_message:
            # first delete relevant existing metadata elements
            if delete_existing_metadata:
                TimeSeriesMetaData.objects.filter(id=resource.metadata.id).update(is_dirty=False)
                _delete_extracted_metadata(resource)
            extract_err_message = extract_metadata(resource, fl_obj_name)
            if extract_err_message:
                # delete the invalid file
                delete_resource_file_only(resource, res_file)
                # cleanup any extracted metadata
                _delete_extracted_metadata(resource)
                validate_files_dict['are_files_valid'] = False
                extract_err_message += "{}".format(FILE_UPLOAD_ERROR_MESSAGE)
                validate_files_dict['message'] = extract_err_message
            else:
                # set metadata is_dirty to False
                TimeSeriesMetaData.objects.filter(id=resource.metadata.id).update(is_dirty=False)
                # delete the csv file if it exists
                _delete_resource_file(resource, ".csv")
                utils.resource_modified(resource, user, overwrite_bag=False)

        else:   # file validation failed
            # delete the invalid file just uploaded
            delete_resource_file_only(resource, res_file)
            validate_files_dict['are_files_valid'] = False
            validate_err_message += "{}".format(FILE_UPLOAD_ERROR_MESSAGE)
            validate_files_dict['message'] = validate_err_message

        # cleanup the temp file
        if os.path.exists(fl_obj_name):
            shutil.rmtree(os.path.dirname(fl_obj_name))
    else:
        # delete the invalid file
        delete_resource_file_only(resource, res_file)
        validate_files_dict['are_files_valid'] = False
        err_message = "The uploaded file not a sqlite file. {}"
        err_message += err_message.format(FILE_UPLOAD_ERROR_MESSAGE)
        validate_files_dict['message'] = err_message


@receiver(pre_metadata_element_create, sender=TimeSeriesResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    return _validate_metadata(request, element_name)


@receiver(pre_metadata_element_update, sender=TimeSeriesResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']
    return _validate_metadata(request, element_name)


def _validate_metadata(request, element_name):
    if element_name == "site":
        element_form = SiteValidationForm(request.POST)
    elif element_name == 'variable':
        element_form = VariableValidationForm(request.POST)
    elif element_name == 'method':
        element_form = MethodValidationForm(request.POST)
    elif element_name == 'processinglevel':
        element_form = ProcessingLevelValidationForm(request.POST)
    elif element_name == 'timeseriesresult':
        element_form = TimeSeriesResultValidationForm(request.POST)
    elif element_name == 'utcoffset':
        element_form = UTCOffSetValidationForm(request.POST)
    else:
        raise Exception("Invalid metadata element name:{}".format(element_name))

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None, "errors": element_form.errors}


def _delete_extracted_metadata(resource):
    resource.metadata.title.delete()
    if resource.metadata.description:
        resource.metadata.description.delete()

    TimeSeriesMetaData.objects.filter(id=resource.metadata.id).update(value_counts={})

    resource.metadata.creators.all().delete()
    resource.metadata.contributors.all().delete()
    resource.metadata.coverages.all().delete()
    resource.metadata.subjects.all().delete()
    resource.metadata.sources.all().delete()
    resource.metadata.relations.all().delete()
    resource.metadata.sites.delete()
    resource.metadata.variables.delete()
    resource.metadata.methods.delete()
    resource.metadata.processing_levels.delete()
    resource.metadata.time_series_results.delete()
    if resource.metadata.utc_offset:
        resource.metadata.utc_offset.delete()

    # delete CV lookup django tables
    resource.metadata.cv_variable_types.all().delete()
    resource.metadata.cv_variable_names.all().delete()
    resource.metadata.cv_speciations.all().delete()
    resource.metadata.cv_elevation_datums.all().delete()
    resource.metadata.cv_site_types.all().delete()
    resource.metadata.cv_method_types.all().delete()
    resource.metadata.cv_units_types.all().delete()
    resource.metadata.cv_statuses.all().delete()
    resource.metadata.cv_mediums.all().delete()
    resource.metadata.cv_aggregation_statistics.all().delete()

    # add the title element as "Untitled resource"
    res_title = 'Untitled resource'
    resource.metadata.create_element('title', value=res_title)

    # add back the resource creator as the creator in metadata
    if resource.creator.first_name:
        first_creator_name = "{first_name} {last_name}".format(
            first_name=resource.creator.first_name, last_name=resource.creator.last_name)
    else:
        first_creator_name = resource.creator.username

    first_creator_email = resource.creator.email

    resource.metadata.create_element('creator', name=first_creator_name, email=first_creator_email,
                                     order=1)


def _validate_csv_file(resource, uploaded_csv_file_name):
    err_message = "Uploaded file is not a valid timeseries csv file."
    log = logging.getLogger()
    with open(uploaded_csv_file_name, 'r') as fl_obj:
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


def _delete_resource_file(resource, file_ext):
    for res_file in resource.files.all():
        _, _, res_file_ext = utils.get_resource_file_name_and_extension(res_file)
        if res_file_ext == file_ext:
            delete_resource_file_only(resource, res_file)
