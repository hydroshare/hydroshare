
__author__ = 'pabitra'

## Note: this module has been imported in the models.py in order to receive signals
## se the end of the models.py for the import of this module

from django.dispatch import receiver
from hs_core.signals import *
from hs_app_timeseries.models import TimeSeriesResource
from forms import *
import os
import sqlite3
import os

# check if the uploaded files are valid"
@receiver(pre_create_resource, sender=TimeSeriesResource)
def resource_pre_create_handler(sender, **kwargs):
    files = kwargs['files']
    validate_files_dict = kwargs['validate_files']

    # check if more than one file uploaded - only one file is allowed
    if len(files) > 1:
        validate_files_dict['are_files_valid'] = False
        validate_files_dict['message'] = 'Only one file can be uploaded.'
    elif len(files) == 1:
        # check file extension matches with the supported file types
        uploaded_file = files[0]
        file_ext = os.path.splitext(uploaded_file.name)[1]
        if file_ext not in TimeSeriesResource.get_supported_upload_file_types():
            validate_files_dict['are_files_valid'] = False
            validate_files_dict['message'] = 'Invalid file type.'

# check the file to be added is valid
@receiver(pre_add_files_to_resource, sender=TimeSeriesResource)
def pre_add_files_to_resource_handler(sender, **kwargs):
    # TODO: implement
    pass

# listen to resource post create signal to extract metadata
@receiver(post_create_resource, sender=TimeSeriesResource)
def post_create_resource_handler(sender, **kwargs):
    resource = kwargs['resource']

    res_file = resource.files.all()[0] if resource.files.all() else None
    if res_file:
        # check if it a sqlite file
        fl_ext = os.path.splitext(res_file.resource_file.name)[1]
        if fl_ext == '.sqlite':
            _extract_metadata(resource, res_file.resource_file.file)


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
    element_id = kwargs['element_id']
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
    try:
        con = sqlite3.connect(sqlite_file.name)

        with con:
            # get the records in python dictionary format
            con.row_factory = sqlite3.Row

            # read data from necessary tables and create metadata elements
            cur = con.cursor()

            ## extract core metadata ##

            # extract abstract and title
            cur.execute("SELECT DataSetTitle, DataSetAbstract FROM DataSets")
            dataset = cur.fetchone()
            # update title element
            if dataset["DataSetTitle"]:
                resource.metadata.update_element('title', element_id=resource.metadata.title.id, value=dataset["DataSetTitle"])
                resource.title = dataset["DataSetTitle"]
                resource.save()

            # create abstract/description element
            if dataset["DataSetAbstract"]:
                resource.metadata.create_element('description', abstract=dataset["DataSetAbstract"])

            # extract keywords/subjects
            # these are the comma separated values in the VariableNameCV column of the Variables table
            cur.execute("SELECT VariableNameCV FROM Variables")
            variable = cur.fetchone()
            keywords = variable["VariableNameCV"]
            keywords = variable["VariableNameCV"].split(",")
            for kw in keywords:
                resource.metadata.create_element("subject", value=kw)

            # find the contributors for metadata
            # contributors are People associated with the Actions that created the Result
            cur.execute("SELECT ActionID FROM Actions")
            actions = cur.fetchall()
            for action in actions:
                # get the AffiliationID from the ActionsBy table for the matching ActionID
                cur.execute("SELECT AffiliationID FROM ActionBy WHERE ActionID=?", (action["ActionID"],))
                actionby_rows = cur.fetchall()

                for actionby in actionby_rows:
                    # get the matching Affiliations records
                    cur.execute("SELECT * FROM Affiliations WHERE AffiliationID=?", (actionby["AffiliationID"],))
                    affiliation_rows = cur.fetchall()
                    for affiliation in affiliation_rows:
                        # get records from the People table
                        cur.execute("SELECT * FROM People WHERE PersonID=?", (affiliation['PersonID'],))
                        people = cur.fetchone()
                        # get person organization name - get only one organization name
                        organization = None
                        if affiliation['OrganizationID']:
                            cur.execute("SELECT OrganizationName FROM Organizations WHERE OrganizationID=?", (affiliation["OrganizationID"],))
                            organization = cur.fetchone()

                        # create contributor metadata elements
                        person_name = people["PersonFirstName"]
                        if people['PersonMiddleName']:
                            person_name = person_name + " " + people['PersonMiddleName']

                        person_name = person_name + " " + people['PersonLastName']
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

                        # create contributor metadata element
                        resource.metadata.create_element('contributor', **data_dict)

            # extract coverage data
            # get point coverage
            cur.execute("SELECT * FROM Sites")
            site = cur.fetchone()
            if site:
                if site["Latitude"] and site["Longitude"]:
                    value_dict = {'east': site["Latitude"], 'north': site["Longitude"], 'units': "Decimal degrees"}
                    # get spatial reference
                    if site["SpatialReferenceID"]:
                        cur.execute("SELECT * FROM SpatialReferences WHERE SpatialReferenceID=?", (site["SpatialReferenceID"],))
                        spatialref = cur.fetchone()
                        if spatialref:
                            if spatialref["SRSName"]:
                                value_dict["projection"] = spatialref["SRSName"]
                    resource.metadata.create_element('coverage', type='point', value=value_dict)

            # get period coverage
            # navigate from Results table to FeatureActions table to Actions table to find the date values
            cur.execute("SELECT FeatureActionID FROM Results")
            result = cur.fetchone()
            cur.execute("SELECT ActionID FROM FeatureActions WHERE FeatureActionID=?", (result["FeatureActionID"],))
            feature_action = cur.fetchone()
            cur.execute("SELECT BeginDateTime, EndDateTime FROM Actions WHERE ActionID=?", (feature_action["ActionID"],))
            action = cur.fetchone()

            # create coverage element
            value_dict = {"start": action["BeginDateTime"], "end": action["EndDateTime"]}
            resource.metadata.create_element('coverage', type='period', value=value_dict)

            ## extract extended metadata ##

            # extract site element data
            cur.execute("SELECT * FROM SamplingFeatures")
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
            cur.execute("SELECT * FROM Variables")
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
            cur.execute("SELECT * FROM Methods")
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
            cur.execute("SELECT * FROM ProcessingLevels")
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

    except sqlite3.Error, e:
        raise Exception("Error %s:" % e.args[0])