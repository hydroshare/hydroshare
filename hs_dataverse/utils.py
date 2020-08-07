import json
import xml.etree.ElementTree as ET
import re
import copy
from datetime import datetime
from pyDataverse.api import Api
import os
import sys
from django.conf import settings
import googlemaps
import time

# global variables

false = False
true = True

# helper functions


# if the given string contains a url, returns it. Otherwise, returns the
# generic hydroshare url
def find_url(string, alt_url):
    """ 
    Finds the url in string, otherwise returns alt_url 
    
    :param string: a string potentially containing a url
    :param alt_url: the alternative url to return if string doesn't have one
    :return: a url
    """
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/" + \
        ")(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>" + \
        "]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    if len([x[0] for x in url]) == 0:
        return alt_url
    else:
        return [x[0] for x in url][0]


def set_field(val):
    """ 
    returns the field_name of the text of the etree value val, or the empty string if null
    
    :param val: an etree element containing the field information
    :return: the string contained in val
    """
    if val is None or val.text is None:
        return 'None'
    else:
        return val.text


# utility functions

def create_metadata_dict(temp_dir):
    """ 
    creates a dict of all the resource's metadata, in the json format specified by dataverse

    :param temp_dir: the temporary directory containing the resource's bag metadata files
    :return: the metadata dict
    """
    # parse the xml metadata file as an etree
    with open(os.path.join(sys.path[0], "hs_dataverse",  "template.json"), "r") as read_file:
        data = json.load(read_file)

    fields = data['datasetVersion']['metadataBlocks']['citation']['fields']
    geofields = data['datasetVersion']['metadataBlocks']['geospatial']['fields']

    meta_path = '/'.join([temp_dir, 'resourcemetadata.xml'])
    tree = ET.parse(meta_path)
    os.remove(meta_path)
    root = tree.getroot()

    # define all the relevant tags from the metadata.xml document for parsing
    title_tag = "{http://purl.org/dc/elements/1.1/}title"

    creator_tag = "{http://purl.org/dc/elements/1.1/}creator"
    name_tag = "{http://hydroshare.org/terms/}name"
    org_tag = '{http://hydroshare.org/terms/}organization'
    email_tag = '{http://hydroshare.org/terms/}email'

    hs_identifier_tag = '{http://hydroshare.org/terms/}hydroShareIdentifier'

    abstract_tag = '{http://purl.org/dc/terms/}abstract'

    period_tag = '{http://purl.org/dc/terms/}period'
    value_tag = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value'

    date_tag = '{http://purl.org/dc/elements/1.1/}date'
    modified_tag = '{http://purl.org/dc/terms/}modified'
    created_tag = '{http://purl.org/dc/terms/}created'

    box_tag = '{http://purl.org/dc/terms/}box'
    spot_tag = '{http://purl.org/dc/terms/}point'

    source_tag = '{http://purl.org/dc/elements/1.1/}source'
    description_tag = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description'

    keyword_tag = '{http://purl.org/dc/elements/1.1/}subject'

    relation_tag = '{http://purl.org/dc/elements/1.1/}relation'

    # Define the dicts to be filled in for dataverse fields that accept multiple values
    other_id_dict = {
        "otherIdAgency": {
          "typeName": "otherIdAgency",
          "multiple": false,
          "typeClass": "primitive",
          "value": "HydroShare"
        },
        "otherIdValue": {
          "typeName": "otherIdValue",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        }
    }

    author_dict = {
        "authorName": {
          "typeName": "authorName",
          "multiple": false,
          "typeClass": "primitive",
          "value": "LastAuthor1, FirstAuthor1"
        },
        "authorAffiliation": {
          "typeName": "authorAffiliation",
          "multiple": false,
          "typeClass": "primitive",
        },
        "authorIdentifierScheme": {
          "typeName": "authorIdentifierScheme",
          "multiple": false,
          "typeClass": "controlledVocabulary",
          "value": "ORCID"
        },
        "authorIdentifier": {
          "typeName": "authorIdentifier",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        }
    }

    contact_dict = {
        "datasetContactName": {
          "typeName": "datasetContactName",
          "multiple": false,
          "typeClass": "primitive",
          "value": "LastContact1, FirstContact1"
        },
        "datasetContactAffiliation": {
          "typeName": "datasetContactAffiliation",
          "multiple": false,
          "typeClass": "primitive",
          "value": "ContactAffiliation1"
        },
        "datasetContactEmail": {
          "typeName": "datasetContactEmail",
          "multiple": false,
          "typeClass": "primitive",
          "value": "ContactEmail1@mailinator.com"
        }
    }

    keyword_dict = {
        "keywordValue": {
          "typeName": "keywordValue",
          "multiple": false,
          "typeClass": "primitive",
          "value": "KeywordTerm1"
        }
    }

    related_publications_dict = {
        "publicationCitation": {
          "typeName": "publicationCitation",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        },
        "publicationURL": {
          "typeName": "publicationURL",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        }
    }

    producer_dict = {
        "producerName": {
          "typeName": "producerName",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        },
        "producerAffiliation": {
          "typeName": "producerAffiliation",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        },
        "producerAbbreviation": {
          "typeName": "producerAbbreviation",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        },
        "producerURL": {
          "typeName": "producerURL",
          "multiple": false,
          "typeClass": "primitive",
          "value": "https://www.hydroshare.org/home/"
        },
        "producerLogoURL": {
          "typeName": "producerLogoURL",
          "multiple": false,
          "typeClass": "primitive",
          "value": "https://www.hydroshare.org/static/img/logo-lg.png"
        }
    }

    contributor_dict = {
        "contributorType": {
          "typeName": "contributorType",
          "multiple": false,
          "typeClass": "controlledVocabulary",
          "value": "Related Person"
        },
        "contributorName": {
          "typeName": "contributorName",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        }
    }

    grant_number_dict = {
        "grantNumberAgency": {
          "typeName": "grantNumberAgency",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        },
        "grantNumberValue": {
          "typeName": "grantNumberValue",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        }
    }

    distributor_dict = {
        "distributorName": {
          "typeName": "distributorName",
          "multiple": false,
          "typeClass": "primitive",
          "value": "HydroShare"
        },
        "distributorAffiliation": {
          "typeName": "distributorAffiliation",
          "multiple": false,
          "typeClass": "primitive",
          "value": "Consortium of Universities for the Advancement of Hydrological Science, Inc (CUAHSI)"
        },
        "distributorAbbreviation": {
          "typeName": "distributorAbbreviation",
          "multiple": false,
          "typeClass": "primitive",
          "value": "HydroShare"
        },
        "distributorURL": {
          "typeName": "distributorURL",
          "multiple": false,
          "typeClass": "primitive",
          "value": "http://www.hydroshare.org"
        },
        "distributorLogoURL": {
          "typeName": "distributorLogoURL",
          "multiple": false,
          "typeClass": "primitive",
          "value": "https://www.hydroshare.org/static/img/logo-lg.png"
        }
    }

    software_dict = {
        "softwareName": {
          "typeName": "softwareName",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        },
        "softwareVersion": {
          "typeName": "softwareVersion",
          "multiple": false,
          "typeClass": "primitive",
          "value": ""
        }
    }

    geo_coverage_dict = {
            "country": {
              "typeName": "country",
              "multiple": false,
              "typeClass": "controlledVocabulary",
              "value": ""
            },
            "state": {
              "typeName": "state",
              "multiple": false,
              "typeClass": "primitive",
              "value": ""
            },
            "city": {
              "typeName": "city",
              "multiple": false,
              "typeClass": "primitive",
              "value": ""
            },
            "otherGeographicCoverage": {
              "typeName": "otherGeographicCoverage",
              "multiple": false,
              "typeClass": "primitive",
              "value": ""
            }
    }

    bounding_box_dict = {
                "westLongitude": {
                  "typeName": "westLongitude",
                  "multiple": false,
                  "typeClass": "primitive",
                  "value": ''
                },
                "eastLongitude": {
                  "typeName": "eastLongitude",
                  "multiple": false,
                  "typeClass": "primitive",
                  "value": ''
                },
                "northLongitude": {
                  "typeName": "northLongitude",
                  "multiple": false,
                  "typeClass": "primitive",
                  "value": ''
                },
                "southLongitude": {
                  "typeName": "southLongitude",
                  "multiple": false,
                  "typeClass": "primitive",
                  "value": ''
                }
    }

    # Using the tags, extract fields into local variables
    title = set_field(root.find(".//%s" % title_tag))
    abstract = set_field(root.find(".//%s" % abstract_tag))

    alt_url = set_field(root.find(".//%s" % hs_identifier_tag))

    author_vals = []
    for creator in root.findall(".//%s" % creator_tag):
        author_vals.append(copy.deepcopy(author_dict))

    contact_vals = []
    for i, author in enumerate(author_vals):
        author['authorName']['value'] = set_field(root.find(
            ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, name_tag)))
        author['authorAffiliation']['value'] = set_field(root.find(
            ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, org_tag)))
        author['authorIdentifier']['value'] = find_url(set_field(root.find(
            ".//%s[%s]/%s" % (creator_tag, i + 1, description_tag))), alt_url)

        if i == 0:  # use the first author as the contact person for the dataset
            contact = copy.deepcopy(contact_dict)
            contact['datasetContactName']['value'] = set_field(root.find(
                ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, name_tag)))
            contact['datasetContactAffiliation']['value'] = set_field(root.find(
                ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, org_tag)))
            contact['datasetContactEmail']['value'] = set_field(root.find(
                ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, email_tag)))
            if contact['datasetContactName']['value'] == 'None':
                contact['datasetContactName']['value'] = 'Hydroshare'
            if contact['datasetContactEmail']['value'] == 'None':
                contact['datasetContactEmail']['value'] = 'help@cuahsi.org'
            contact_vals.append(contact)

    keyword_vals = []
    for keyword in root.findall(".//%s" % keyword_tag):
        keyword_vals.append(copy.deepcopy(keyword_dict))

    for i, keyword in enumerate(keyword_vals):
        keyword['keywordValue']['value'] = set_field(root.find(".//%s[%s]" % (keyword_tag, i + 1)))

    subject = ['Earth and Environmental Sciences']

    deposit_date_text = set_field(root.find(".//%s/%s/%s" % (date_tag, created_tag, value_tag)))
    if (deposit_date_text != 'None'):
        [deposit_date, deposit_time] = deposit_date_text.split('T')
    else:
        deposit_date = ''

    last_modified_date_text = set_field(root.find(".//%s/%s/%s" % (date_tag, modified_tag, value_tag)))
    if (last_modified_date_text != 'None'):
        [last_modified_date, last_modified_time] = deposit_date_text.split('T')
    else:
        last_modified_date = ''

    # Get the start period and parse the strings into numerical date values
    period_text = set_field(root.find(".//%s/%s" % (period_tag, value_tag)))
    if (period_text != 'None'):
        [name, start_period, end_period, scheme] = period_text.split('; ')
        start_period = re.sub('start=', '', start_period)
        end_period = re.sub('end=', '', end_period)
        [start_period_date, start_period_time] = start_period.split('T')
        [end_period_date, end_period_time] = end_period.split('T')

    else:
        start_period_date = ''
        end_period_date = ''

    related_publications_vals = []
    related_resources = []
    for i, related_publication in enumerate(root.findall(".//%s/%s//*" % (relation_tag, description_tag))):
        related_publications_vals.append(copy.deepcopy(related_publications_dict))
        related_publications_vals[i]['publicationCitation']['value'] = set_field(related_publication)
        related_publications_vals[i]['publicationURL']['value'] = find_url(set_field(related_publication), alt_url)

        related_resources.append(related_publication.text)

    related_materials = []
    for i, source in enumerate(root.findall(".//%s/%s//*" % (source_tag, description_tag))):
        related_materials.append(set_field(source))

    # use the google location services api to find the location
    maps_api_token = getattr(settings, 'MAPS_KEY', '')
    gmaps = googlemaps.Client(key=maps_api_token)

    geo_units = []
    bounding_box_vals = []
    geo_coverage_vals = []
    other_geo_info = ''

    old_geo_coverage_dict = geo_coverage_dict

    bounding_box_text = set_field(root.find('.//%s/%s' % (box_tag, value_tag)))
    if (bounding_box_text != 'None'):
        print('bounding_box_text:', bounding_box_text)
        [northlimit, eastlimit, southlimit, westlimit, units, projection] = bounding_box_text.split(';')
        northlimit = re.sub('northlimit=', '', northlimit)
        eastlimit = re.sub('eastlimit=', '', eastlimit)
        westlimit = re.sub('westlimit=', '', westlimit)
        southlimit = re.sub('southlimit=', '', southlimit)
        geo_units.append(re.sub('units=', '', units))

        for box in root.findall(".//%s" % box_tag):
            bounding_box_vals.append(copy.deepcopy(bounding_box_dict))

        for i, box in enumerate(bounding_box_vals):
            box['westLongitude']['value'] = westlimit
            box['eastLongitude']['value'] = eastlimit
            box['northLongitude']['value'] = northlimit
            box['southLongitude']['value'] = southlimit

    spot_text = set_field(root.find('.//%s/%s' % (spot_tag, value_tag)))
    if (spot_text != 'None'):
        [name, east, north, units, projection] = spot_text.split(';', 4)
        east = re.sub('east=', '', east)
        north = re.sub('north=', '', north)
        other_geo_info = re.sub('name=', '', name)
        geo_units.append(re.sub(' units=', '', units))
        reverse_geo_code_result = gmaps.reverse_geocode((north, east))
        if not reverse_geo_code_result:
            type_dict = {'types': []}
            reverse_geo_code_result.append({'address_components': [type_dict]})

        for box in root.findall(".//%s" % spot_tag):
            bounding_box_vals.append(copy.deepcopy(bounding_box_dict))

        # for point coordinates, westlimit == eastlimit, and northlimit == southlimit
        for i, box in enumerate(bounding_box_vals):
            box['westLongitude']['value'] = east
            box['eastLongitude']['value'] = east
            box['northLongitude']['value'] = north
            box['southLongitude']['value'] = north

        for comp in reverse_geo_code_result[0]['address_components']:
            if 'country' in comp['types']:
                geo_coverage_dict['country']['value'] = comp['long_name']
            if 'administrative_area_level_1' in comp['types']:
                geo_coverage_dict['state']['value'] = comp['long_name']
            if 'locality' in comp['types']:
                geo_coverage_dict['city']['value'] = comp['long_name']
    geo_coverage_dict['otherGeographicCoverage']['value'] = other_geo_info

    if (geo_coverage_dict != old_geo_coverage_dict):
        geo_coverage_vals.append(geo_coverage_dict)

    # Extract more fields using the extended metadata from other_metadata.json
    e = dict()
    with open('/'.join([temp_dir, 'other_metadata.json'])) as f:
        e = json.load(f)

    other_id_dict['otherIdValue']['value'] = str(e['rid'])

    notes_text = e['extended_metadata_notes']

    grant_vals = []
    for i, grant in enumerate(e['award_numbers']):
        grant_info = copy.deepcopy(grant_number_dict)
        grant_info['grantNumberAgency']['value'] = e['funding_agency_names'][i]
        grant_info['grantNumberValue']['value'] = e['award_numbers'][i]
        grant_vals.append(grant_info)

    contributor_vals = []
    for contributor in e['contributors']:
        c_dict = copy.deepcopy(contributor_dict)
        c_dict['contributorName']['value'] = contributor
        contributor_vals.append(c_dict)

    # Extract more fields using the owner data from ownerdata.json
    o = dict()
    with open('/'.join([temp_dir, 'ownerdata.json'])) as f:
        o = json.load(f)
    contact = copy.deepcopy(contact_dict)
    if 'username' in o:
        producer_dict['producerAbbreviation']['value'] = o['username']
    else:
        producer_dict['producerAbbreviation']['value'] = ''

    if 'first_name' in o and 'last_name' in o:
        producer_dict['producerName']['value'] = o['last_name'] + ', ' + o['first_name']
        contact['datasetContactName']['value'] = o['last_name'] + ', ' + o['first_name']
        depositor = o['last_name'] + ', ' + o['first_name']
    else:
        producer_dict['producerName']['value'] = ''
        contact['datasetContactName']['value'] = ''
        depositor = ''

    if 'organization' in o:
        producer_dict['producerAffiliation']['value'] = o['organization']
        contact['datasetContactAffiliation']['value'] = o['organization']
    else:
        producer_dict['producerAffiliation']['value'] = ''
        contact['datasetContactAffiliation']['value'] = ''

    if 'email' in o:
        contact['datasetContactEmail']['value'] = o['email']
    else:
        contact['datasetContactEmail']['value'] = ''
    if contact != contact_dict:
        contact_vals.append(contact)

    # update the json dict with the field values
    fields[0]['value'] = title

    fields[1]['value'] = alt_url

    fields[2]['value'] = [other_id_dict]

    fields[3]['value'] = author_vals
    fields[4]['value'] = contact_vals

    fields[5]['value'][0]['dsDescriptionValue']['value'] = abstract
    fields[5]['value'][0]['dsDescriptionDate']['value'] = last_modified_date

    fields[6]['value'] = subject

    fields[7]['value'] = keyword_vals

    fields[8]['value'] = related_publications_vals

    fields[9]['value'] = notes_text

    fields[10]['value'] = [producer_dict]

    fields[11]['value'] = contributor_vals

    fields[12]['value'] = grant_vals

    fields[13]['value'] = [distributor_dict]

    fields[14]['value'] = str(datetime.date(datetime.now()))  # distribution date

    fields[15]['value'] = depositor

    fields[16]['value'] = deposit_date

    fields[17]['value'][0]['timePeriodCoveredStart']['value'] = start_period_date
    fields[17]['value'][0]['timePeriodCoveredEnd']['value'] = end_period_date

    fields[18]['value'] = ['Composite Resource']

    fields[19]['value'] = [software_dict]

    fields[20]['value'] = related_materials  # related Material

    fields[21]['value'] = []  # related Datasets

    geofields[0]['value'] = geo_coverage_vals
    geofields[1]['value'] = geo_units
    geofields[2]['value'] = bounding_box_vals

    return data


def upload_dataset(base_url, api_token, dv, temp_dir):
    """ 
    uploads a dataset to the specified dataverse location, using the data specified in the file resourcemetadata.xml
    
    :param base_url: the dataverse server url
    :param api_token: the dataverse api_token
    :param dv: the parent dataverse to upload the dataset to, either a dataverse name or id
    :param temp_dir: the temporary directory containing the resource's bag metadata files
    :return: nothing
    """
    metadata = create_metadata_dict(temp_dir)
    api = Api(base_url, api_token)

    query_str = '/dataverses/' + dv + '/contents'
    params = {}
    resp = api.get_request(query_str, params=params, auth=True)

    # extracting response data in json format
    dv_data = resp.json()

    num_dv = len(dv_data[u'data'])
    print(num_dv) # eventually, there should be a button which allows users to choose locations from among these
    # print all dataverse and dataset titles
    for i in range(0, num_dv):
        if((dv_data[u'data'][i][u'type'] == 'dataverse')):
            print("Dataverse: " + dv_data[u'data'][i][u'title'])
        if((dv_data[u'data'][i][u'type'] == 'dataset')):
            print("Dataset: " + dv_data[u'data'][i][u'identifier'])

    r = api.create_dataset(dv, json.dumps(metadata))
    print(r)
    print(r.text)

    r_dict = json.loads(r.text)
    persistent_id = r_dict['data']['persistentId']

    # before uploading all files in the temp directory, remove the datafiles
    data_files = ['ownerdata.json', 'other_metadata.json']
    for file in data_files:
        file_path = '/'.join([temp_dir, file])
        os.remove(file_path)

    # upload all files in the temp directory (the bag of resource files)
    for file in os.listdir(temp_dir):
        file_path = '/'.join([temp_dir, file])

        count = 0
        done = False
        while not done:
            try:
                api.upload_file(persistent_id, file_path)
                done = True
            except:
                count += 1
                if count >= 5:
                    done = True
                    print('Could not upload file: {}'.format(file))
                else:
                    time.sleep(7)

    # now delete the dataset, as to not fill up the datverse while testing
    # time.sleep(3)
    # r2 = api.delete_dataset(persistent_id, is_pid=True, auth=True)
    # print(r2)
    # print(r2.text)
