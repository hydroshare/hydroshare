import csv
import logging
import sqlite3
import tempfile
import os

from dateutil import parser
from hsextract.utils.s3 import s3_client as s3


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
            # TODO: check that each of the core tables has the necessary
            # columns

            # check that the uploaded file has all the tables from ODM2Core and
            # the CV tables
            cur = con.cursor()
            odm2_core_table_names = [
                'People',
                'Affiliations',
                'SamplingFeatures',
                'ActionBy',
                'Organizations',
                'Methods',
                'FeatureActions',
                'Actions',
                'RelatedActions',
                'Results',
                'Variables',
                'Units',
                'Datasets',
                'DatasetsResults',
                'ProcessingLevels',
                'TaxonomicClassifiers',
                'CV_VariableType',
                'CV_VariableName',
                'CV_Speciation',
                'CV_SiteType',
                'CV_ElevationDatum',
                'CV_MethodType',
                'CV_UnitsType',
                'CV_Status',
                'CV_Medium',
                'CV_AggregationStatistic',
            ]
            # check the tables exist
            for table_name in odm2_core_table_names:
                cur.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type=? AND name=?", ("table", table_name))
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
                    err_message += " Table '{}' has no records.".format(
                        table_name)
                    log.info(err_message)
                    return err_message
        return None
    except sqlite3.Error as e:
        sqlite_err_msg = str(e.args[0])
        log.error(sqlite_err_msg)
        return sqlite_err_msg
    except Exception as e:
        log.error(str(e))
        return str(e)


def validate_csv_file(csv_file_path):
    err_message = "Uploaded file is not a valid timeseries csv file."
    log = logging.getLogger()
    with open(csv_file_path, 'r') as fl_obj:
        csv_reader = csv.reader(fl_obj, delimiter=',')
        # read the first row
        header = next(csv_reader)
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
        date_data_error = False
        data_row_count = 0
        for row in csv_reader:
            # check that data row has the same number of columns as the header
            if len(row) != len(header):
                err_message += " Number of columns in the header is not same as the data columns."
                log.error(err_message)
                return err_message
            # check that the first column data is of type datetime
            try:
                # some numeric values (e.g., 20080101, 1.602652223413681) are recognized by the
                # the parser as valid date value - we don't allow any such
                # value as valid date
                float(row[0])
                date_data_error = True
            except ValueError:
                try:
                    parser.parse(row[0])
                except ValueError:
                    date_data_error = True

            if date_data_error:
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
            data_row_count += 1

        if data_row_count < 2:
            err_message += " There needs to be at least two rows of data."
            log.error(err_message)
            return err_message

    return None


def create_cv_lookup_models(sql_cur):
    table_names = [
        'CV_VariableType',
        'CV_VariableName',
        'CV_Speciation',
        'CV_SiteType',
        'CV_ElevationDatum',
        'CV_MethodType',
        'CV_UnitsType',
        'CV_Status',
        'CV_Medium',
        'CV_AggregationStatistic',
    ]
    term_names = []

    for table_name in table_names:
        sql_cur.execute("SELECT Term, Name FROM {}".format(table_name))
        table_rows = sql_cur.fetchall()
        rows = []
        for row in table_rows:
            rows.append({"Term": row['Term'], "Name": row["Name"]})
        term_names.append({table_name: rows})
    return term_names


def extract_metadata(sqlite_file_name):
    """
    Extracts metadata from the sqlite file *sqlite_file_name
    :param sqlite_file_name: path of the sqlite file
    :return: extracted_metadata as dictionary
    """
    temp_dir = tempfile.gettempdir()
    local_copy = os.path.join(temp_dir, os.path.basename(sqlite_file_name))
    bucket, key = sqlite_file_name.split("/", 1)
    s3.download_file(bucket, key, local_copy)
    with sqlite3.connect(local_copy) as con:
        # get the records in python dictionary format
        con.row_factory = sqlite3.Row
        cur = con.cursor()

        as_json = {}

        # term_names = create_cv_lookup_models(cur)

        # as_json.update({"term_names": term_names})

        # extract abstract and title
        cur.execute("SELECT DataSetTitle, DataSetAbstract FROM DataSets")
        dataset = cur.fetchone()
        # update title element
        if dataset["DataSetTitle"]:
            # TODO strip() all at the end?
            as_json.update({'title': dataset["DataSetTitle"]})

        # create abstract/description element
        if dataset["DataSetAbstract"]:
            as_json.update({'abstract': dataset["DataSetAbstract"]})

        # extract keywords/subjects
        # these are the comma separated values in the VariableNameCV column of the Variables
        # table
        cur.execute("SELECT VariableID, VariableNameCV FROM Variables")
        variables = cur.fetchall()
        keyword_list = []
        for variable in variables:
            keywords = variable["VariableNameCV"].split(",")
            keyword_list = keyword_list + keywords
        as_json.update({'subjects': keyword_list})

        # find the contributors for metadata
        creators, contributors = _extract_creators_contributors(cur)
        as_json.update({'creators': creators})
        as_json.update({'contributors': contributors})

        # extract coverage data
        coverage = _extract_coverage_metadata(cur)
        as_json.update(coverage)

        cur.execute("SELECT * FROM Results")
        results = cur.fetchall()
        time_series_results = []
        for result in results:
            result_json = {}
            result_json["series_id"] = result["ResultUUID"]
            variable_elements = extract_variable_elements(cur, result)
            result_json.update({"variable": variable_elements})

            processinglevel_elements = extract_processinglevel_elements(
                cur, result)
            result_json.update({'processing_level': processinglevel_elements})

            timeseriesresult_elements = extract_timeseriesresult_elements(
                cur, result)
            result_json.update(timeseriesresult_elements)

            # query FeatureActions
            cur.execute("SELECT * FROM FeatureActions WHERE FeatureActionID=?",
                        (result["FeatureActionID"],))
            feature_action = cur.fetchone()

            site_elements = extract_site_elements(cur, result, feature_action)
            result_json.update({'site': site_elements})

            method_elements = extract_method_elements(
                cur, result, feature_action)
            result_json.update({'method': method_elements})
            time_series_results.append(result_json)

        as_json["time_series_results"] = time_series_results
        as_json["content_files"] = [sqlite_file_name]
        return as_json


def extract_timeseriesresult_elements(cur, result):
    # extract data for TimeSeriesResult element
    # Start with Results table
    data_dict = {}
    # data_dict['series_ids'] = [result["ResultUUID"]]
    if result["StatusCV"] is not None:
        data_dict["status"] = result["StatusCV"]
    else:
        data_dict["status"] = ""
    data_dict["sample_medium"] = result["SampledMediumCV"]
    data_dict["value_count"] = result["ValueCount"]

    cur.execute("SELECT * FROM Units WHERE UnitsID=?", (result["UnitsID"],))
    unit = cur.fetchone()
    data_dict['unit'] = {}
    data_dict['unit']['type'] = unit["UnitsTypeCV"]
    data_dict['unit']['name'] = unit["UnitsName"]
    data_dict['unit']['abbreviation'] = unit["UnitsAbbreviation"]

    cur.execute(
        "SELECT AggregationStatisticCV FROM TimeSeriesResults WHERE " "ResultID=?", (result["ResultID"],))
    ts_result = cur.fetchone()
    data_dict["aggregation_statistic"] = ts_result["AggregationStatisticCV"]

    return data_dict


def extract_processinglevel_elements(cur, result):
    # extract processinglevel element data
    # Start with Results table to -> ProcessingLevels table
    cur.execute("SELECT * FROM ProcessingLevels WHERE ProcessingLevelID=?",
                (result["ProcessingLevelID"],))
    pro_level = cur.fetchone()
    data_dict = {}
    # data_dict['series_ids'] = [result["ResultUUID"]]
    data_dict['processing_level_code'] = pro_level["ProcessingLevelCode"]
    if pro_level["Definition"]:
        data_dict["definition"] = pro_level["Definition"]

    if pro_level["Explanation"]:
        data_dict["explanation"] = pro_level["Explanation"]

    return data_dict


def extract_method_elements(cur, result, feature_action):
    # extract method element data
    # Start with Results table -> FeatureActions table to -> Actions table to ->
    # Method table
    cur.execute("SELECT MethodID from Actions WHERE ActionID=?",
                (feature_action["ActionID"],))
    action = cur.fetchone()
    cur.execute("SELECT * FROM Methods WHERE MethodID=?",
                (action["MethodID"],))
    method = cur.fetchone()

    data_dict = {}
    # data_dict['series_ids'] = [result["ResultUUID"]]
    data_dict['method_code'] = method["MethodCode"]
    data_dict["method_name"] = method["MethodName"]
    data_dict['method_type'] = method["MethodTypeCV"]

    if method["MethodDescription"]:
        data_dict["method_description"] = method["MethodDescription"]

    if method["MethodLink"]:
        data_dict["method_link"] = method["MethodLink"]

    return data_dict


def extract_variable_elements(cur, result):
    # extract variable element data
    # Start with Results table to -> Variables table
    cur.execute("SELECT * FROM Variables WHERE VariableID=?",
                (result["VariableID"],))
    variable = cur.fetchone()
    data_dict = {}
    # data_dict['series_ids'] = [result["ResultUUID"]]
    data_dict['variable_code'] = variable["VariableCode"]
    data_dict["variable_name"] = variable["VariableNameCV"]
    data_dict['variable_type'] = variable["VariableTypeCV"]
    data_dict["no_data_value"] = variable["NoDataValue"]
    if variable["VariableDefinition"]:
        data_dict["variable_definition"] = variable["VariableDefinition"]

    if variable["SpeciationCV"]:
        data_dict["speciation"] = variable["SpeciationCV"]

    return data_dict


def extract_site_elements(cur, result, feature_action):
    # extract site element data
    # Start with Results table to -> FeatureActions table -> SamplingFeatures table
    # check if we need to create multiple site elements
    cur.execute("SELECT * FROM SamplingFeatures WHERE SamplingFeatureID=?",
                (feature_action["SamplingFeatureID"],))
    sampling_feature = cur.fetchone()

    cur.execute("SELECT * FROM Sites WHERE SamplingFeatureID=?",
                (feature_action["SamplingFeatureID"],))
    site = cur.fetchone()
    data_dict = {}
    # data_dict['series_ids'] = [result["ResultUUID"]]
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

    return data_dict


def extract_cv_metadata_from_blank_sqlite_file(csv_file):
    """Extracts CV metadata from the blank sqlite file and populates the django metadata
    models - this function is applicable only in the case of a CSV file being used as the
    source of time series data
    :param  target: an instance of TimeSeriesLogicalFile
    """

    # save some data from the csv file
    # get the csv file from iRODS to a temp directory
    with open(csv_file, 'r') as fl_obj:
        csv_reader = csv.reader(fl_obj, delimiter=',')
        # read the first row - header
        header = next(csv_reader)
        # read the 1st data row
        start_date_str = next(csv_reader)[0]
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

        # create the temporal coverage element

        value_counts['coverage'] = {'type': 'period', 'value': {
            'start': start_date_str, 'end': end_date_str}}
        return value_counts


def _extract_creators_contributors(cur):
    # check if the AuthorList table exists
    authorlists_table_exists = False
    cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type=? AND name=?",
                ("table", "AuthorLists"))
    qry_result = cur.fetchone()
    if qry_result[0] > 0:
        authorlists_table_exists = True

    cur.execute("SELECT FeatureActionID FROM Results")
    results = cur.fetchall()
    authors_data_dict = {}
    author_ids_already_used = []
    contributors = []
    creators = []
    for result in results:
        cur.execute("SELECT ActionID FROM FeatureActions WHERE FeatureActionID=?", (result[
                    "FeatureActionID"],))
        feature_actions = cur.fetchall()
        for feature_action in feature_actions:
            cur.execute("SELECT ActionID FROM Actions WHERE ActionID=?",
                        (feature_action["ActionID"],))

            actions = cur.fetchall()
            for action in actions:
                # get the AffiliationID from the ActionsBy table for the
                # matching ActionID
                cur.execute(
                    "SELECT AffiliationID FROM ActionBy WHERE ActionID=?", (action["ActionID"],))
                actionby_rows = cur.fetchall()

                for actionby in actionby_rows:
                    # get the matching Affiliations records
                    cur.execute(
                        "SELECT * FROM Affiliations WHERE AffiliationID=?", (actionby["AffiliationID"],))
                    affiliation_rows = cur.fetchall()
                    for affiliation in affiliation_rows:
                        # get records from the People table
                        if affiliation['PersonID'] not in author_ids_already_used:
                            author_ids_already_used.append(
                                affiliation['PersonID'])
                            cur.execute(
                                "SELECT * FROM People WHERE PersonID=?", (affiliation['PersonID'],))
                            person = cur.fetchone()

                            # get person organization name - get only one
                            # organization name
                            organization = None
                            if affiliation['OrganizationID']:
                                cur.execute(
                                    "SELECT OrganizationName FROM Organizations WHERE " "OrganizationID=?",
                                    (affiliation["OrganizationID"],),
                                )
                                organization = cur.fetchone()

                            # create contributor metadata elements
                            person_name = person["PersonFirstName"]
                            if person['PersonMiddleName']:
                                person_name = person_name + " " + \
                                    person['PersonMiddleName']

                            person_name = person_name + \
                                " " + person['PersonLastName']
                            data_dict = {}
                            data_dict['name'] = person_name
                            if affiliation['PrimaryPhone']:
                                data_dict["phone"] = affiliation[
                                    "PrimaryPhone"]
                            if affiliation["PrimaryEmail"]:
                                data_dict["email"] = affiliation[
                                    "PrimaryEmail"]
                            if affiliation["PrimaryAddress"]:
                                data_dict["address"] = affiliation[
                                    "PrimaryAddress"]
                            if organization:
                                data_dict["organization"] = organization[0]

                            # check if this person is an author (creator)
                            author = None
                            if authorlists_table_exists:
                                cur.execute(
                                    "SELECT * FROM AuthorLists WHERE PersonID=?", (person['PersonID'],))
                                author = cur.fetchone()

                            if author:
                                # save the extracted creator data in the dictionary
                                # so that we can later sort it based on author order
                                # and then create the creator metadata elements
                                authors_data_dict[
                                    author["AuthorOrder"]] = data_dict
                            else:
                                contributors.append(data_dict)

    # TODO: extraction of creator data has not been tested as the sample database does not have
    #  any records in the AuthorLists table
    authors_data_dict_sorted_list = sorted(
        authors_data_dict, key=lambda key: authors_data_dict[key])
    creators = []
    for data_dict in authors_data_dict_sorted_list:
        creators.append(data_dict)

    return creators, contributors


def _extract_coverage_metadata(cur):
    # get point or box coverage
    cur.execute("SELECT * FROM Sites")
    sites = cur.fetchall()
    coverage = {}
    if len(sites) == 1:
        site = sites[0]
        if site["Latitude"] and site["Longitude"]:
            value_dict = {'east': site["Longitude"], 'north': site[
                "Latitude"], 'units': "Decimal degrees"}
            # get spatial reference
            if site["SpatialReferenceID"]:
                cur.execute(
                    "SELECT * FROM SpatialReferences WHERE SpatialReferenceID=?", (site["SpatialReferenceID"],))
                spatialref = cur.fetchone()
                if spatialref:
                    if spatialref["SRSName"]:
                        value_dict["projection"] = spatialref["SRSName"]
            coverage["spatial_coverage"] = {"type": "point", **value_dict}
    else:
        # in case of multiple sites we will create one coverage element of type
        # 'box'
        bbox = {
            'northlimit': -90,
            'southlimit': 90,
            'eastlimit': -180,
            'westlimit': 180,
            'projection': 'Unknown',
            'units': "Decimal degrees",
        }
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
                    cur.execute(
                        "SELECT * FROM SpatialReferences WHERE SpatialReferenceID=?", (site[
                                                                                       "SpatialReferenceID"],)
                    )
                    spatialref = cur.fetchone()
                    if spatialref:
                        if spatialref["SRSName"]:
                            bbox['projection'] = spatialref["SRSName"]

            if bbox['projection'] == 'Unknown':
                bbox['projection'] = 'WGS 84 EPSG:4326'
        coverage["spatial_coverage"] = {"type": "box", **bbox}

    # extract temporal coverage
    cur.execute(
        "SELECT MAX(ValueDateTime) AS 'EndDate', MIN(ValueDateTime) AS 'BeginDate' " "FROM TimeSeriesResultValues"
    )

    dates = cur.fetchone()
    begin_date = parser.parse(dates['BeginDate'])
    end_date = parser.parse(dates['EndDate'])

    # create coverage element
    coverage["period_coverage"] = {
        "start": begin_date.isoformat(), "end": end_date.isoformat()}

    return coverage


def extract_metadata_csv(csv_file_name):
    """Extracts CV metadata from a csv file"""
    metadata_dict = {}
    temp_dir = tempfile.gettempdir()
    local_copy = os.path.join(temp_dir, os.path.basename(csv_file_name))
    bucket, key = csv_file_name.split("/", 1)
    s3.download_file(bucket, key, local_copy)
    with open(local_copy, 'r') as fl_obj:
        csv_reader = csv.reader(fl_obj, delimiter=',')
        # read the first row - header
        header = next(csv_reader)
        # read the 1st data row
        start_date_str = next(csv_reader)[0]
        last_row = None
        data_row_count = 1
        for row in csv_reader:
            last_row = row
            data_row_count += 1
        end_date_str = last_row[0]

        # save the series names along with number of data points for each series
        # columns starting with the 2nd column are data series names
        time_series_results = []
        for data_col_name in header[1:]:
            time_series_results.append(
                {"series_id": data_col_name, "value_count": data_row_count})

        metadata_dict.update({"time_series_results": time_series_results})
        start_date = parser.parse(start_date_str)
        end_date = parser.parse(end_date_str)
        metadata_dict.update({"period_coverage": {
                             'start': start_date.isoformat(), 'end': end_date.isoformat()}})

    metadata_dict["content_files"] = [csv_file_name]

    return metadata_dict
