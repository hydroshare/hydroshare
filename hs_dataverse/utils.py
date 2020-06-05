from django.http import HttpResponse
import json
import xml.etree.ElementTree as ET
import re
import copy
from datetime import datetime
from pyDataverse.api import Api
import os
import sys

# global variables

false = False
true = True


# helper functions

# if the given string contains a url, returns it. Otherwise, returns the
# generic hydroshare url
def find_url(string):
    regex = r'(https?://[^\s]+)'
    url = re.findall(regex, string)
    if len([x[0] for x in url]) == 0:
        return alternative_url
    else:
        return [x[0] for x in url][0]

# returns the field_name of the text of the etree value val, or the empty string if null 
def set_field(val):
    if val == None:
        return 'None'
    else:
        return val.text


# utility functions

# uploads a dataset to the specified dataverse location, using the data specified in the file resourcemetadata.xml
def upload_dataset(base_url, api_token, dv):
    # parse the xml metadata file as an etree
    with open(os.path.join(sys.path[0], "hs_dataverse",  "template.json"), "r") as read_file:
        data = json.load(read_file)

    fields = data['datasetVersion']['metadataBlocks']['citation']['fields']
    geofields = data['datasetVersion']['metadataBlocks']['geospatial']['fields']

    tree = ET.parse('resourcemetadata.xml')
    root = tree.getroot()

    # define all the relevant tags from the metadata.xml document for parsing
    title_tag = "{http://purl.org/dc/elements/1.1/}title"

    creator_tag = "{http://purl.org/dc/elements/1.1/}creator"
    creator_description_tag = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description"
    name_tag = "{http://hydroshare.org/terms/}name"
    org_tag = '{http://hydroshare.org/terms/}organization'
    email_tag = '{http://hydroshare.org/terms/}email'

    hs_identifier_tag = '{http://hydroshare.org/terms/}hydroShareIdentifier'

    abstract_tag = '{http://purl.org/dc/terms/}abstract'

    awardinfo_tag = '{http://hydroshare.org/terms/}awardInfo'
    awardinfo_description_tag = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description'
    funding_agency_name_tag = '{http://hydroshare.org/terms/}fundingAgencyName'
    award_title_tag = '{http://hydroshare.org/terms/}awardTitle'
    award_number_tag = '{http://hydroshare.org/terms/}awardNumber'

    period_tag = '{http://purl.org/dc/terms/}period'
    value_tag = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value'

    date_tag = '{http://purl.org/dc/elements/1.1/}date'
    modified_tag = '{http://purl.org/dc/terms/}modified'
    created_tag = '{http://purl.org/dc/terms/}created'

    source_tag = '{http://purl.org/dc/elements/1.1/}source'
    description_tag = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description'
    derived_tag = '{http://hydroshare.org/terms/}isDerivedFrom'

    keyword_tag = '{http://purl.org/dc/elements/1.1/}subject'

    relation_tag = '{http://purl.org/dc/elements/1.1/}relation'
    hosted_by_tag = '{http://hydroshare.org/terms/}isHostedBy'

    # Define the dicts to be filled in for dataverse fields that accept multpile values
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
          "value": "RelatedPublicationCitation1"
        },
        "publicationURL": {
          "typeName": "publicationURL",
          "multiple": false,
          "typeClass": "primitive",
          "value": "http://RelatedPublicationURL1.org"
        }
    }

    producor_dict = {
        "producerName": {
          "typeName": "producerName",
          "multiple": false,
          "typeClass": "primitive",
          "value": "LastProducer1, FirstProducer1"
        },
        "producerAffiliation": {
          "typeName": "producerAffiliation",
          "multiple": false,
          "typeClass": "primitive",
          "value": "ProducerAffiliation1"
        },
        "producerAbbreviation": {
          "typeName": "producerAbbreviation",
          "multiple": false,
          "typeClass": "primitive",
          "value": "ProducerAbbreviation1"
        },
        "producerURL": {
          "typeName": "producerURL",
          "multiple": false,
          "typeClass": "primitive",
          "value": "http://ProducerURL1.org"
        },
        "producerLogoURL": {
          "typeName": "producerLogoURL",
          "multiple": false,
          "typeClass": "primitive",
          "value": "http://ProducerLogoURL1.org"
        }
      }

    contributor_dict = {
        "contributorType": {
          "typeName": "contributorType",
          "multiple": false,
          "typeClass": "controlledVocabulary",
          "value": "Data Collector"
        },
        "contributorName": {
          "typeName": "contributorName",
          "multiple": false,
          "typeClass": "primitive",
          "value": "LastContributor1, FirstContributor1"
        }
    }

    grant_number_dict = {
        "grantNumberAgency": {
          "typeName": "grantNumberAgency",
          "multiple": false,
          "typeClass": "primitive",
          "value": "GrantInformationGrantAgency1"
        },
        "grantNumberValue": {
          "typeName": "grantNumberValue",
          "multiple": false,
          "typeClass": "primitive",
          "value": "GrantInformationGrantNumber1"
        }
    }

    distributor_dict = {
        "distributorName": {
          "typeName": "distributorName",
          "multiple": false,
          "typeClass": "primitive",
          "value": "LastDistributor1, FirstDistributor1"
        },
        "distributorAffiliation": {
          "typeName": "distributorAffiliation",
          "multiple": false,
          "typeClass": "primitive",
          "value": "DistributorAffiliation1"
        },
        "distributorAbbreviation": {
          "typeName": "distributorAbbreviation",
          "multiple": false,
          "typeClass": "primitive",
          "value": "DistributorAbbreviation1"
        },
        "distributorURL": {
          "typeName": "distributorURL",
          "multiple": false,
          "typeClass": "primitive",
          "value": "http://DistributorURL1.org"
        },
        "distributorLogoURL": {
          "typeName": "distributorLogoURL",
          "multiple": false,
          "typeClass": "primitive",
          "value": "http://DistributorLogoURL1.org"
        }
    }

    software_dict = {
        "softwareName": {
          "typeName": "softwareName",
          "multiple": false,
          "typeClass": "primitive",
          "value": "SoftwareName1"
        },
        "softwareVersion": {
          "typeName": "softwareVersion",
          "multiple": false,
          "typeClass": "primitive",
          "value": "SoftwareVersion1"
        }
    }

    # Using the tags, extract fields into local variables
    title = set_field(root.find(".//%s" % title_tag))
    abstract = set_field(root.find(".//%s" % abstract_tag))

    author_vals = []
    for creator in root.findall(".//%s" % creator_tag):
        author_vals.append(copy.deepcopy(author_dict))

    contact_vals = []
    for i, author in enumerate(author_vals):
        author['authorName']['value'] = set_field(root.find(
            ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, name_tag)))
        author['authorAffiliation']['value'] = set_field(root.find(
            ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, org_tag)))

        if i == 0:  # use the first author as the contact person for the dataset
            contact = contact_dict
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

    alternative_url = set_field(root.find(".//%s" % hs_identifier_tag))

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
        depoist_date = ''

    last_modified_date_text = set_field(root.find(".//%s/%s/%s" % (date_tag, modified_tag, value_tag)))
    if (last_modified_date_text != 'None'):
        [last_modified_date, last_modified_time] = deposit_date_text.split('T')
    else:
        last_modified_date = ''

    # Get the start period and parse the strings into numerical date values
    period_text = set_field(root.find(".//%s/%s" % (period_tag, value_tag)))
    if (period_text != 'None'):
        [start_period, end_period, scheme] = period_text.split()
        start_period = re.sub('start=', '', start_period)
        end_period = re.sub('end=', '', end_period)
        [start_period_date, start_period_time] = start_period.split('T')
        [end_period_date, end_period_time] = end_period.split('T')
    else:
        start_period_date = ''
        end_period_date = ''

    related_publications = root.findall(".//%s/%s//*" % (relation_tag, description_tag))

    related_publications_vals = []
    related_resources = []
    for i, related_publication in enumerate(root.findall(".//%s/%s//*" % (relation_tag, description_tag))):
        related_publications_vals.append(copy.deepcopy(related_publications_dict))
        related_publications_vals[i]['publicationCitation']['value'] = set_field(related_publication)
        related_publications_vals[i]['publicationURL']['value'] = find_url(set_field(related_publication))

        related_resources.append(related_publication.text)


    # update the json dict with the field values
    fields[0]['value'] = title

    fields[1]['value'] = alternative_url

    fields[2]['value'] = author_vals
    fields[3]['value'] = contact_vals

    fields[4]['value'][0]['dsDescriptionValue']['value'] = abstract
    fields[4]['value'][0]['dsDescriptionDate']['value'] = last_modified_date

    fields[5]['value'] = subject

    fields[6]['value'] = keyword_vals

    fields[7]['value'] = related_publications_vals

    fields[8]['value'] = 'notes'

    fields[9]['value'] = [producor_dict]

    fields[10]['value'] = '1003-01-01'

    fields[11]['value'] = [contributor_dict]

    fields[12]['value'] = [grant_number_dict]

    fields[13]['value'] = [distributor_dict]

    fields[14]['value'] = str(datetime.date(datetime.now()))  # distribution date

    fields[15]['value'] = 'depositor'

    fields[16]['value'] = deposit_date

    fields[17]['value'][0]['timePeriodCoveredStart']['value'] = start_period_date
    fields[17]['value'][0]['timePeriodCoveredEnd']['value'] = end_period_date

    fields[18]['value'] = ['kind of data']

    fields[19]['value'] = [software_dict]

    fields[20]['value'] = ['related_papers']

    fields[21]['value'] = related_resources

    geofields[2]['value'][0]['westLongitude']['value'] = "1"
    geofields[2]['value'][0]['eastLongitude']['value'] = "2"
    geofields[2]['value'][0]['northLongitude']['value'] = "3"
    geofields[2]['value'][0]['southLongitude']['value'] = "4"


    #  dump the json file as 'data.json'
    with open('data.json', 'w') as outfile:
        json.dump(data, outfile, indent=2)

    with open('data.json', 'r') as json_file:
        metadata = json.load(json_file)

    api = Api(base_url, api_token)

    query_str = '/dataverses/' + dv + '/contents'
    params = {}
    resp = api.get_request(query_str, params=params, auth=True)

    # extracting response data in json format
    dv_data = resp.json()

    num_dv = len(dv_data[u'data'])
    print(num_dv)
    # print all titles
    for i in range(0, num_dv):
        if((dv_data[u'data'][i][u'type'] == 'dataverse')):
            print("Dataverse: " + dv_data[u'data'][i][u'title'])
        if((dv_data[u'data'][i][u'type'] == 'dataset')):
            print("Dataset: " + dv_data[u'data'][i][u'identifier'])

    r = api.create_dataset(dv, json.dumps(metadata))
   
    # now delete the dataset, as to not fill up the datverse while testing 
    r_dict = json.loads(r.text)
    persistent_id = r_dict['data']['persistentId']
    r2 = api.delete_dataset(persistent_id, is_pid=True, auth=True)
