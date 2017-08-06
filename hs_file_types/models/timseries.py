# import os
# import shutil
import logging
import sqlite3

from django.db import models, transaction
# from django.core.exceptions import ValidationError
# from django.core.files.uploadedfile import UploadedFile
from hs_app_timeseries.models import TimeSeriesMetaDataMixin

from base import AbstractFileMetaData, AbstractLogicalFile


class TimeSeriesFileMetaData(TimeSeriesMetaDataMixin, AbstractFileMetaData):
    # the metadata element models are from the timeseries resource type app
    model_app_label = 'hs_app_timeseries'

    def get_metadata_elements(self):
        elements = super(TimeSeriesFileMetaData, self).get_metadata_elements()
        elements += list(self.sites)
        elements += list(self.variables)
        elements += list(self.methods)
        elements += list(self.processing_levels)
        elements += list(self.time_series_results)
        elements += [self.utc_offset]
        return elements


class TimeSeriesLogicalFile(AbstractLogicalFile):
    metadata = models.OneToOneField(TimeSeriesFileMetaData, related_name="logical_file")
    data_type = "TimeSeries"

    @classmethod
    def get_allowed_uploaded_file_types(cls):
        """only .csv and .sqlite file can be set to this logical file group"""
        return [".csv", ".sqlite"]

    @classmethod
    def get_allowed_storage_file_types(cls):
        """file types allowed in this logical file group are: .csv and .sqlite"""
        return [".csv", ".sqlite"]

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

            # create abstract/description element
            if dataset["DataSetAbstract"]:
                if logical_file is None or resource.metadata.description is None:
                    resource.metadata.create_element('description',
                                                     abstract=dataset["DataSetAbstract"])

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
                        target_obj.metadata.create_element('site', **data_dict)
                    else:
                        _update_element_series_ids(target_obj.metadata.sites[0],
                                                   result["ResultUUID"])
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
                        _update_element_series_ids(target_obj.metadata.variables[0],
                                                   result["ResultUUID"])
                else:
                    _update_element_series_ids(target_obj.metadata.variables[0],
                                               result["ResultUUID"])

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
                        target_obj.metadata.create_element('method', **data_dict)
                    else:
                        _update_element_series_ids(target_obj.metadata.methods[0],
                                                   result["ResultUUID"])
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
                        _update_element_series_ids(target_obj.metadata.processing_levels[0],
                                                   result["ResultUUID"])
                else:
                    _update_element_series_ids(target_obj.metadata.processing_levels[0],
                                               result["ResultUUID"])

                # extract data for TimeSeriesResult element
                # Start with Results table
                if is_create_multiple_timeseriesresult_elements \
                        or len(target_obj.metadata.time_series_results) == 0:
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

        target_obj.metadata.create_element('coverage', type='box', value=bbox)

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
    target_obj.metadata.create_element('coverage', type='period', value=value_dict)


def _update_element_series_ids(element, series_id):
    element.series_ids = element.series_ids + [series_id]
    element.save()