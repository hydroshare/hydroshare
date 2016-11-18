import os
import sqlite3
import shutil
import logging
import csv
from dateutil import parser
import tempfile

from django.dispatch import receiver

from hs_core.signals import pre_create_resource, pre_add_files_to_resource, \
    pre_delete_file_from_resource, post_add_files_to_resource, post_create_resource, \
    pre_metadata_element_create, pre_metadata_element_update
from hs_core.hydroshare import utils, delete_resource_file_only
from hs_app_timeseries.models import TimeSeriesResource, CVVariableType, CVVariableName, \
    CVSpeciation, CVSiteType, CVElevationDatum, CVMethodType, CVUnitsType, CVStatus, CVMedium, \
    CVAggregationStatistic, TimeSeriesMetaData
from forms import SiteValidationForm, VariableValidationForm, MethodValidationForm, \
    ProcessingLevelValidationForm, TimeSeriesResultValidationForm, UTCOffSetValidationForm


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
    fed_res_fnames = kwargs['fed_res_file_names']

    if files or fed_res_fnames:
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
    uploaded_file = kwargs['files'][0]
    validate_files_dict = kwargs['validate_files']
    user = kwargs['user']

    # extract metadata from the just uploaded file
    uploaded_file_to_process = None
    uploaded_file_ext = ''
    for res_file in resource.files.all():
        _, res_file_name, uploaded_file_ext = utils.get_resource_file_name_and_extension(res_file)
        if res_file_name == uploaded_file.name:
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
            _process_uploaded_sqlite_file(user, resource, res_file, validate_files_dict,
                                          delete_existing_metadata=False)
        elif file_ext == '.csv':
            _process_uploaded_csv_file(resource, res_file, validate_files_dict, user,
                                       delete_existing_metadata=False)


def _process_uploaded_csv_file(resource, res_file, validate_files_dict, user,
                               delete_existing_metadata=True):
    # get the csv file from iRODS to a temp directory
    fl_obj_name = utils.get_file_from_irods(res_file)
    validate_err_message = _validate_csv_file(resource, fl_obj_name)
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
            _create_cv_lookup_models(cur, resource.metadata, 'CV_VariableType', CVVariableType)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_VariableName', CVVariableName)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_Speciation', CVSpeciation)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_SiteType', CVSiteType)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_ElevationDatum',
                                     CVElevationDatum)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_MethodType', CVMethodType)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_UnitsType', CVUnitsType)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_Status', CVStatus)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_Medium', CVMedium)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_AggregationStatistic',
                                     CVAggregationStatistic)

        # save some data from the csv file
        with open(fl_obj_name, 'r') as fl_obj:
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

            TimeSeriesMetaData.objects.filter(id=resource.metadata.id).update(
                value_counts=value_counts)

            # create the temporal coverage element
            resource.metadata.create_element('coverage', type='period',
                                             value={'start': start_date_str, 'end': end_date_str})

        # cleanup the temp sqlite file directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

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
        validate_err_message = _validate_odm2_db_file(fl_obj_name)
        if not validate_err_message:
            # first delete relevant existing metadata elements
            if delete_existing_metadata:
                TimeSeriesMetaData.objects.filter(id=resource.metadata.id).update(is_dirty=False)
                _delete_extracted_metadata(resource)
            extract_err_message = _extract_metadata(resource, fl_obj_name)
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
                utils.resource_modified(resource, user)

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


def _extract_metadata(resource, sqlite_file_name):
    err_message = "Not a valid ODM2 SQLite file"
    log = logging.getLogger()
    try:
        con = sqlite3.connect(sqlite_file_name)
        with con:
            # get the records in python dictionary format
            con.row_factory = sqlite3.Row
            cur = con.cursor()

            # populate the lookup CV tables that are needed later for metadata editing
            _create_cv_lookup_models(cur, resource.metadata, 'CV_VariableType', CVVariableType)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_VariableName', CVVariableName)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_Speciation', CVSpeciation)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_SiteType', CVSiteType)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_ElevationDatum', CVElevationDatum)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_MethodType', CVMethodType)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_UnitsType', CVUnitsType)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_Status', CVStatus)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_Medium', CVMedium)
            _create_cv_lookup_models(cur, resource.metadata, 'CV_AggregationStatistic',
                                     CVAggregationStatistic)

            # read data from necessary tables and create metadata elements
            # extract core metadata

            # extract abstract and title
            cur.execute("SELECT DataSetTitle, DataSetAbstract FROM DataSets")
            dataset = cur.fetchone()
            # update title element
            if dataset["DataSetTitle"]:
                resource.metadata.update_element('title', element_id=resource.metadata.title.id,
                                                 value=dataset["DataSetTitle"])

            # create abstract/description element
            if dataset["DataSetAbstract"]:
                resource.metadata.create_element('description', abstract=dataset["DataSetAbstract"])

            # extract keywords/subjects
            # these are the comma separated values in the VariableNameCV column of the Variables
            # table
            cur.execute("SELECT VariableID, VariableNameCV FROM Variables")
            variables = cur.fetchall()
            keyword_list = []
            for variable in variables:
                keywords = variable["VariableNameCV"].split(",")
                keyword_list = keyword_list + keywords

            # use set() to remove any duplicate keywords
            for kw in set(keyword_list):
                resource.metadata.create_element("subject", value=kw)

            # find the contributors for metadata
            _extract_creators_contributors(resource, cur)

            # extract coverage data
            _extract_coverage_metadata(resource, cur)

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
                if is_create_multiple_site_elements or len(resource.metadata.sites) == 0:
                    cur.execute("SELECT * FROM SamplingFeatures WHERE SamplingFeatureID=?",
                                (feature_action["SamplingFeatureID"],))
                    sampling_feature = cur.fetchone()

                    cur.execute("SELECT * FROM Sites WHERE SamplingFeatureID=?",
                                (feature_action["SamplingFeatureID"],))
                    site = cur.fetchone()
                    if not any(sampling_feature["SamplingFeatureCode"] == s.site_code for s
                               in resource.metadata.sites):

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
                        resource.metadata.create_element('site', **data_dict)
                    else:
                        _update_element_series_ids(resource.metadata.sites[0], result["ResultUUID"])
                else:
                    _update_element_series_ids(resource.metadata.sites[0], result["ResultUUID"])

                # extract variable element data
                # Start with Results table to -> Variables table
                if is_create_multiple_variable_elements or len(resource.metadata.variables) == 0:
                    cur.execute("SELECT * FROM Variables WHERE VariableID=?",
                                (result["VariableID"],))
                    variable = cur.fetchone()
                    if not any(variable["VariableCode"] == v.variable_code for v
                               in resource.metadata.variables):

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
                        resource.metadata.create_element('variable', **data_dict)
                    else:
                        _update_element_series_ids(resource.metadata.variables[0],
                                                   result["ResultUUID"])
                else:
                    _update_element_series_ids(resource.metadata.variables[0], result["ResultUUID"])

                # extract method element data
                # Start with Results table -> FeatureActions table to -> Actions table to ->
                # Method table
                if is_create_multiple_method_elements or len(resource.metadata.methods) == 0:
                    cur.execute("SELECT MethodID from Actions WHERE ActionID=?",
                                (feature_action["ActionID"],))
                    action = cur.fetchone()
                    cur.execute("SELECT * FROM Methods WHERE MethodID=?", (action["MethodID"],))
                    method = cur.fetchone()
                    if not any(method["MethodCode"] == m.method_code for m
                               in resource.metadata.methods):

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
                        resource.metadata.create_element('method', **data_dict)
                    else:
                        _update_element_series_ids(resource.metadata.methods[0],
                                                   result["ResultUUID"])
                else:
                    _update_element_series_ids(resource.metadata.methods[0], result["ResultUUID"])

                # extract processinglevel element data
                # Start with Results table to -> ProcessingLevels table
                if is_create_multiple_processinglevel_elements \
                        or len(resource.metadata.processing_levels) == 0:
                    cur.execute("SELECT * FROM ProcessingLevels WHERE ProcessingLevelID=?",
                                (result["ProcessingLevelID"],))
                    pro_level = cur.fetchone()
                    if not any(pro_level["ProcessingLevelCode"] == p.processing_level_code for p
                               in resource.metadata.processing_levels):

                        data_dict = {}
                        data_dict['series_ids'] = [result["ResultUUID"]]
                        data_dict['processing_level_code'] = pro_level["ProcessingLevelCode"]
                        if pro_level["Definition"]:
                            data_dict["definition"] = pro_level["Definition"]

                        if pro_level["Explanation"]:
                            data_dict["explanation"] = pro_level["Explanation"]

                        # create processinglevel element
                        resource.metadata.create_element('processinglevel', **data_dict)
                    else:
                        _update_element_series_ids(resource.metadata.processing_levels[0],
                                                   result["ResultUUID"])
                else:
                    _update_element_series_ids(resource.metadata.processing_levels[0],
                                               result["ResultUUID"])

                # extract data for TimeSeriesResult element
                # Start with Results table
                if is_create_multiple_timeseriesresult_elements \
                        or len(resource.metadata.time_series_results) == 0:
                    data_dict = {}
                    data_dict['series_ids'] = [result["ResultUUID"]]
                    data_dict["status"] = result["StatusCV"]
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
                    resource.metadata.create_element('timeseriesresult', **data_dict)
                else:
                    _update_element_series_ids(resource.metadata.time_series_results[0],
                                               result["ResultUUID"])

            return None

    except sqlite3.Error as ex:
        sqlite_err_msg = str(ex.args[0])
        log.error(sqlite_err_msg)
        return sqlite_err_msg
    except Exception as ex:
        log.error(ex.message)
        return err_message


def _extract_creators_contributors(resource, cur):
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
                                    resource.metadata.create_element('contributor', **data_dict)

    # TODO: extraction of creator data has not been tested as the sample database does not have
    # any records in the AuthorLists table
    authors_data_dict_sorted_list = sorted(authors_data_dict,
                                           key=lambda key: authors_data_dict[key])
    for data_dict in authors_data_dict_sorted_list:
        # create creator metadata element
        resource.metadata.create_element('creator', **data_dict)


def _extract_coverage_metadata(resource, cur):
    # get point or box coverage
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

            resource.metadata.create_element('coverage', type='point', value=value_dict)
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

        resource.metadata.create_element('coverage', type='box', value=bbox)

    cur.execute("SELECT * FROM Results")
    results = cur.fetchall()
    min_begin_date = None
    max_end_date = None
    for result in results:
        cur.execute("SELECT ActionID FROM FeatureActions WHERE FeatureActionID=?",
                    (result["FeatureActionID"],))
        feature_action = cur.fetchone()
        cur.execute("SELECT BeginDateTime, EndDateTime FROM Actions WHERE ActionID=?",
                    (feature_action["ActionID"],))
        action = cur.fetchone()
        if min_begin_date is None:
            min_begin_date = action["BeginDateTime"]
        elif min_begin_date > action["BeginDateTime"]:
            min_begin_date = action["BeginDateTime"]

        if max_end_date is None:
            max_end_date = action["EndDateTime"]
        elif max_end_date < action["EndDateTime"]:
            max_end_date = action["EndDateTime"]

    # create coverage element
    value_dict = {"start": min_begin_date, "end": max_end_date}
    resource.metadata.create_element('coverage', type='period', value=value_dict)


def _create_cv_lookup_models(sql_cur, metadata_obj, table_name, model_class):
    sql_cur.execute("SELECT Term, Name FROM {}".format(table_name))
    table_rows = sql_cur.fetchall()
    for row in table_rows:
        model_class.objects.create(metadata=metadata_obj, term=row['Term'], name=row['Name'])


def _update_element_series_ids(element, series_id):
    element.series_ids = element.series_ids + [series_id]
    element.save()


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


def _validate_odm2_db_file(uploaded_sqlite_file_name):
    err_message = "Uploaded file is not a valid ODM2 SQLite file."
    log = logging.getLogger()
    try:
        con = sqlite3.connect(uploaded_sqlite_file_name)
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


def _delete_resource_file(resource, file_ext):
    for res_file in resource.files.all():
        _, _, res_file_ext = utils.get_resource_file_name_and_extension(res_file)
        if res_file_ext == file_ext:
            delete_resource_file_only(resource, res_file)
