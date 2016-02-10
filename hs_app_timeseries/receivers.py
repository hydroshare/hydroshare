import os
import sqlite3

from django.core.exceptions import ValidationError
from django.dispatch import receiver

from hs_core.signals import *
from hs_core.hydroshare import utils
from hs_app_timeseries.models import TimeSeriesResource
from forms import SiteValidationForm, VariableValidationForm, MethodValidationForm, ProcessingLevelValidationForm, \
    TimeSeriesResultValidationForm


@receiver(pre_create_resource, sender=TimeSeriesResource)
def resource_pre_create_handler(sender, **kwargs):
    # if needed more actions can be taken here before the TimeSeries resource is created
    pass


@receiver(pre_add_files_to_resource, sender=TimeSeriesResource)
def pre_add_files_to_resource_handler(sender, **kwargs):
    # if needed more actions can be taken here before content file is added to a TimeSeries resource
    pass

@receiver(pre_delete_file_from_resource, sender=TimeSeriesResource)
def pre_delete_file_from_resource_handler(sender, **kwargs):
    # if needed more actions can be taken here before content file is deleted from a TimeSeries resource
    pass


@receiver(post_add_files_to_resource, sender=TimeSeriesResource)
def post_add_files_to_resource_handler(sender, **kwargs):
    resource = kwargs['resource']
    validate_files_dict = kwargs['validate_files']
    extract_metadata = kwargs['extract_metadata']
    user = kwargs['user']

    # extract metadata from the just uploaded file
    res_file = resource.files.all()[0] if resource.files.all() else None
    if res_file:
        # check if it a sqlite file
        fl_ext = os.path.splitext(res_file.resource_file.name)[1]
        if fl_ext == '.sqlite':
            validate_err_message = _validate_odm2_db_file(res_file.resource_file.file)
            if not validate_err_message:
                if extract_metadata:
                    # first delete relevant metadata elements
                    _delete_extracted_metadata(resource)
                    extract_err_message = _extract_metadata(resource, res_file.resource_file.file)
                    utils.resource_modified(resource, user)
                    if extract_err_message:
                        validate_files_dict['are_files_valid'] = False
                        validate_files_dict['message'] = extract_err_message + " (Failed to extract all metadata)"
            else:   # file validation failed
                # delete the invalid file just uploaded
                #file_name = os.path.basename(res_file.resource_file.name)
                #delete_resource_file(resource.short_id, file_name)
                validate_files_dict['are_files_valid'] = False
                if extract_metadata:
                    validate_err_message += " (Metadata was not extracted)"
                validate_files_dict['message'] = validate_err_message


@receiver(post_create_resource, sender=TimeSeriesResource)
def post_create_resource_handler(sender, **kwargs):
    resource = kwargs['resource']
    validate_files_dict = kwargs['validate_files']
    user = kwargs['user']

    res_file = resource.files.all()[0] if resource.files.all() else None
    if res_file:
        # check if it a sqlite file
        fl_ext = os.path.splitext(res_file.resource_file.name)[1]
        if fl_ext == '.sqlite':
            validate_err_message = _validate_odm2_db_file(res_file.resource_file.file)
            if not validate_err_message:
                extract_err_message = _extract_metadata(resource, res_file.resource_file.file)
                utils.resource_modified(resource, user)
                if extract_err_message:
                    validate_files_dict['are_files_valid'] = False
                    validate_files_dict['message'] = extract_err_message + " (Failed to extract all metadata)"
            else:
                validate_files_dict['are_files_valid'] = False
                validate_files_dict['message'] = validate_err_message + " (Metadata was not extracted)"


@receiver(pre_metadata_element_create, sender=TimeSeriesResource)
def metadata_element_pre_create_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

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

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}


@receiver(pre_metadata_element_update, sender=TimeSeriesResource)
def metadata_element_pre_update_handler(sender, **kwargs):
    element_name = kwargs['element_name'].lower()
    request = kwargs['request']

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

    if element_form.is_valid():
        return {'is_valid': True, 'element_data_dict': element_form.cleaned_data}
    else:
        return {'is_valid': False, 'element_data_dict': None}

"""
 Since each of the timeseries metadata element is required no need to listen to any delete signal
 The timeseries landing page should not have delete UI functionality for the resource specific metadata elements
"""


def _extract_metadata(resource, sqlite_file):
    err_message = "Not a valid ODM2 SQLite file"
    try:
        con = sqlite3.connect(sqlite_file.name)

        with con:
            # get the records in python dictionary format
            con.row_factory = sqlite3.Row

            # read data from necessary tables and create metadata elements
            cur = con.cursor()

            # check if the AuthorList table exists
            authorlists_table_exists = False
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type=? AND name=?", ("table", "AuthorLists"))
            qry_result =cur.fetchone()
            if qry_result[0] > 0:
                authorlists_table_exists = True

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
            # these are the comma separated values in the VariableNameCV column of the Variables table
            cur.execute("SELECT VariableNameCV FROM Variables")
            variable = cur.fetchone()
            keywords = variable["VariableNameCV"].split(",")
            for kw in keywords:
                resource.metadata.create_element("subject", value=kw)

            # find the contributors for metadata
            # contributors are People associated with the Actions that created the Result
            cur.execute("SELECT FeatureActionID FROM Results")
            results = cur.fetchall()
            authors_data_dict = {}
            for result in results:
                cur.execute("SELECT ActionID FROM FeatureActions WHERE FeatureActionID=?", (result["FeatureActionID"],))
                feature_actions = cur.fetchall()
                for feature_action in feature_actions:
                    cur.execute("SELECT ActionID FROM Actions WHERE ActionID=?", (feature_action["ActionID"],))

                    actions = cur.fetchall()
                    for action in actions:
                        # get the AffiliationID from the ActionsBy table for the matching ActionID
                        cur.execute("SELECT AffiliationID FROM ActionBy WHERE ActionID=?", (action["ActionID"],))
                        actionby_rows = cur.fetchall()

                        for actionby in actionby_rows:
                            # get the matching Affiliations records
                            cur.execute("SELECT * FROM Affiliations WHERE AffiliationID=?",
                                        (actionby["AffiliationID"],))
                            affiliation_rows = cur.fetchall()
                            for affiliation in affiliation_rows:
                                # get records from the People table
                                cur.execute("SELECT * FROM People WHERE PersonID=?", (affiliation['PersonID'],))
                                person = cur.fetchone()

                                # get person organization name - get only one organization name
                                organization = None
                                if affiliation['OrganizationID']:
                                    cur.execute("SELECT OrganizationName FROM Organizations WHERE OrganizationID=?",
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
                                    cur.execute("SELECT * FROM AuthorLists WHERE PersonID=?", (person['PersonID'],))
                                    author = cur.fetchone()

                                if author:
                                    # save the extracted creator data in the dictionary
                                    # so that we can later sort it based on author order
                                    # and then create the creator metadata elements
                                    authors_data_dict[author["AuthorOrder"]] = data_dict
                                else:
                                    # create contributor metadata element
                                    resource.metadata.create_element('contributor', **data_dict)

            # TODO: extraction of creator data has not been tested as the sample database does not have any records
            # in the AuthorLists table
            authors_data_dict_sorted_list = sorted(authors_data_dict, key=lambda key: authors_data_dict[key])
            for data_dict in authors_data_dict_sorted_list:
                # create creator metadata element
                resource.metadata.create_element('creator', **data_dict)

            # extract coverage data
            # get point coverage
            cur.execute("SELECT * FROM Sites")
            site = cur.fetchone()
            if site:
                if site["Latitude"] and site["Longitude"]:
                    value_dict = {'east': site["Longitude"], 'north': site["Latitude"], 'units': "Decimal degrees"}
                    # get spatial reference
                    if site["SpatialReferenceID"]:
                        cur.execute("SELECT * FROM SpatialReferences WHERE SpatialReferenceID=?",
                                    (site["SpatialReferenceID"],))
                        spatialref = cur.fetchone()
                        if spatialref:
                            if spatialref["SRSName"]:
                                value_dict["projection"] = spatialref["SRSName"]
                    resource.metadata.create_element('coverage', type='point', value=value_dict)

            # get period coverage
            # navigate from Results table to -> FeatureActions table to ->  Actions table to find the date values
            cur.execute("SELECT * FROM Results")
            result = cur.fetchone()
            cur.execute("SELECT ActionID FROM FeatureActions WHERE FeatureActionID=?", (result["FeatureActionID"],))
            feature_action = cur.fetchone()
            cur.execute("SELECT BeginDateTime, EndDateTime FROM Actions WHERE ActionID=?",
                        (feature_action["ActionID"],))
            action = cur.fetchone()

            # create coverage element
            value_dict = {"start": action["BeginDateTime"], "end": action["EndDateTime"]}
            resource.metadata.create_element('coverage', type='period', value=value_dict)

            # extract extended metadata

            # extract site element data
            # Start with Results table to -> FeatureActions table -> SamplingFeatures table
            cur.execute("SELECT * FROM FeatureActions WHERE FeatureActionID=?", (result["FeatureActionID"],))
            feature_action = cur.fetchone()
            cur.execute("SELECT * FROM SamplingFeatures WHERE SamplingFeatureID=?",
                        (feature_action["SamplingFeatureID"],))
            sampling_feature = cur.fetchone()
            data_dict = {}
            data_dict['site_code'] = sampling_feature["SamplingFeatureCode"]
            data_dict['site_name'] = sampling_feature["SamplingFeatureName"]
            if sampling_feature["Elevation_m"]:
                data_dict["elevation_m"] = sampling_feature["Elevation_m"]

            if sampling_feature["ElevationDatumCV"]:
                data_dict["elevation_datum"] = sampling_feature["ElevationDatumCV"]

            if site["SiteTypeCV"]:
                data_dict["site_type"] = site["SiteTypeCV"]

            # create site element
            resource.metadata.create_element('site', **data_dict)

            # extract variable element data
            # Start with Results table to -> Variables table
            cur.execute("SELECT * FROM Variables WHERE VariableID=?", (result["VariableID"],))
            variable = cur.fetchone()
            data_dict = {}
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

            # extract method element data
            # Start with Results table -> FeatureActions table to -> Actions table to -> Method table
            cur.execute("SELECT MethodID from Actions WHERE ActionID=?", (feature_action["ActionID"],))
            action = cur.fetchone()
            cur.execute("SELECT * FROM Methods WHERE MethodID=?", (action["MethodID"],))
            method = cur.fetchone()
            data_dict = {}
            data_dict['method_code'] = method["MethodCode"]
            data_dict["method_name"] = method["MethodName"]
            data_dict['method_type'] = method["MethodTypeCV"]

            if method["MethodDescription"]:
                data_dict["method_description"] = method["MethodDescription"]

            if method["MethodLink"]:
                data_dict["method_link"] = method["MethodLink"]

            # create method element
            resource.metadata.create_element('method', **data_dict)

            # extract processinglevel element data
            # Start with Results table to -> ProcessingLevels table
            cur.execute("SELECT * FROM ProcessingLevels WHERE ProcessingLevelID=?", (result["ProcessingLevelID"],))
            pro_level = cur.fetchone()
            data_dict = {}
            data_dict['processing_level_code'] = pro_level["ProcessingLevelCode"]
            if pro_level["Definition"]:
                data_dict["definition"] = pro_level["Definition"]

            if pro_level["Explanation"]:
                data_dict["explanation"] = pro_level["Explanation"]

            # create processinglevel element
            resource.metadata.create_element('processinglevel', **data_dict)

            # extract data for TimeSeriesResult element
            # Start with Results table
            data_dict = {}

            cur.execute("SELECT * FROM Results")
            result = cur.fetchone()
            data_dict["status"] = result["StatusCV"]
            data_dict["sample_medium"] = result["SampledMediumCV"]
            data_dict["value_count"] = result["ValueCount"]

            cur.execute("SELECT * FROM Units WHERE UnitsID=?", (result["UnitsID"],))
            unit = cur.fetchone()
            data_dict['units_type'] = unit["UnitsTypeCV"]
            data_dict['units_name'] = unit["UnitsName"]
            data_dict['units_abbreviation'] = unit["UnitsAbbreviation"]

            cur.execute("SELECT AggregationStatisticCV FROM TimeSeriesResults WHERE ResultID=?", (result["ResultID"],))
            ts_result = cur.fetchone()
            data_dict["aggregation_statistics"] = ts_result["AggregationStatisticCV"]

            # create the TimeSeriesResult element
            resource.metadata.create_element('timeseriesresult', **data_dict)
            return None

    except sqlite3.Error, e:
        sqlite_err_msg = str(e.args[0])
        return sqlite_err_msg
    except:
        return err_message


def _delete_extracted_metadata(resource):
    resource.metadata.title.delete()
    if resource.metadata.description:
        resource.metadata.description.delete()

    resource.metadata.creators.all().delete()
    resource.metadata.contributors.all().delete()
    resource.metadata.coverages.all().delete()
    resource.metadata.subjects.all().delete()
    resource.metadata.sources.all().delete()
    resource.metadata.relations.all().delete()

    # delete extended metadata elements
    if resource.metadata.site:
        resource.metadata.site.delete()

    if resource.metadata.variable:
        resource.metadata.variable.delete()

    if resource.metadata.method:
        resource.metadata.method.delete()

    if resource.metadata.processing_level:
        resource.metadata.processing_level.delete()

    if resource.metadata.time_series_result:
        resource.metadata.time_series_result.delete()

    # add the title element as "Untitled resource"
    res_title = 'Untitled resource'
    resource.metadata.create_element('title', value=res_title)

    # add back the resource creator as the creator in metadata
    if resource.creator.first_name:
        first_creator_name = "{first_name} {last_name}".format(first_name=resource.creator.first_name,
                                                               last_name=resource.creator.last_name)
    else:
        first_creator_name = resource.creator.username

    first_creator_email = resource.creator.email

    resource.metadata.create_element('creator', name=first_creator_name, email=first_creator_email, order=1)


def _validate_odm2_db_file(uploaded_file_sqlite_file):
    err_message = "Not a valid ODM2 SQLite file"
    try:
        con = sqlite3.connect(uploaded_file_sqlite_file.name)
        with con:
            # TODO: check that each of the core tables has the necessary columns

            # check that the uploaded file has all the tables from ODM2Core
            cur = con.cursor()
            odm2_core_table_names = ['People', 'Affiliations', 'SamplingFeatures', 'ActionBy', 'Organizations',
                                     'Methods', 'FeatureActions', 'Actions', 'RelatedActions', 'Results', 'Variables',
                                     'Units', 'Datasets', 'DatasetsResults', 'ProcessingLevels', 'TaxonomicClassifiers']
            # check the tables exist
            for table_name in odm2_core_table_names:
                cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type=? AND name=?", ("table", table_name))
                result = cur.fetchone()
                if result[0] <= 0:
                    return err_message

            # check that the tables have at least one record
            for table_name in odm2_core_table_names:
                if table_name == 'RelatedActions' or 'TaxonomicClassifiers':
                    continue
                cur.execute("SELECT COUNT(*) FROM " + table_name)
                result = cur.fetchone()
                if result[0] <= 0:
                    return err_message
        return None
    except sqlite3.Error, e:
        sqlite_err_msg = str(e.args[0])
        return err_message + '. ' + sqlite_err_msg