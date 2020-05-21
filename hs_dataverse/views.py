from django.http import HttpResponse
import json
import xml.etree.ElementTree as ET
import re
import copy
from datetime import datetime
from pyDataverse.api import Api

# global variables

false = False
true = True

# helper functions

# if the given string contains a url, returns it. Otherwise, returns the
# generic hydroshare url
def find_url(string):
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:"\
        "[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^"\
        "\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, string)
    if len([x[0] for x in url]) == 0:
        return alternative_url
    else:
        return [x[0] for x in url][0]

# Create your views here.

def datatest(request):
    return HttpResponse("<h1>data test</h1>\n", 200)

def upload_dataset(request):
    # parse the xml metadata file as an etree
    with open("template.json", "r") as read_file:
    data = json.load(read_file)

    fields = data['datasetVersion']['metadataBlocks']['citation']['fields']
    geofields = data['datasetVersion']['metadataBlocks']['geospatial']['fields']

    tree = ET.parse('resourcemetadata.xml')
    root = tree.getroot()

    # declare all necessary tags for xpath queries
    title_tag = "{http://purl.org/dc/elements/1.1/}title"

    creator_tag = "{http://purl.org/dc/elements/1.1/}creator"
    creator_description_tag = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}De"\
        "scription"
    name_tag = "{http://hydroshare.org/terms/}name"
    org_tag = '{http://hydroshare.org/terms/}organization'
    email_tag = '{http://hydroshare.org/terms/}email'

    hs_identifier_tag = '{http://hydroshare.org/terms/}hydroShareIdentifier'

    abstract_tag = '{http://purl.org/dc/terms/}abstract'

    awardinfo_tag = '{http://hydroshare.org/terms/}awardInfo'
    awardinfo_description_tag = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'\
        'Description'
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

    # declare dictionaries to fill in data and insert into json, for fields
    # with multiple values
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
          "value": "AuthorAffiliation1"
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

    # use xpath to find and store the metadata fields dataverse will accept
    title = root.find(".//%s" % title_tag).text
    abstract = root.find(".//%s" % abstract_tag).text

    author_vals = []
    for creator in root.findall(".//%s" % creator_tag):
        author_vals.append(copy.deepcopy(author_dict))

    contact_vals = []
    for i, author in enumerate(author_vals):
        author['authorName']['value'] = root.find(
            ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, name_tag)).text
        author['authorAffiliation']['value'] = root.find(
            ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, org_tag)).text

        if i == 0:  # use the first author as the contact person for the dataset
            contact = contact_dict
            contact['datasetContactName']['value'] = root.find(
                ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, name_tag)).text
            contact['datasetContactAffiliation']['value'] = root.find(
                ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, org_tag)).text
            contact['datasetContactEmail']['value'] = root.find(
                ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, email_tag)).text
            contact_vals.append(contact)

    alternative_url = root.find(".//%s" % hs_identifier_tag).text

    keyword_vals = []
    for keyword in root.findall(".//%s" % keyword_tag):
        keyword_vals.append(copy.deepcopy(keyword_dict))

    for i, keyword in enumerate(keyword_vals):
        keyword['keywordValue']['value'] = root.find(".//%s[%s]" % (keyword_tag, i + 1)).text


    subject = ['Earth and Environmental Sciences']

    deposit_date_text = root.find(".//%s/%s/%s" % (date_tag, created_tag, value_tag)).text
    [deposit_date, deposit_time] = deposit_date_text.split('T')

    last_modified_date_text = root.find(".//%s/%s/%s" % (date_tag, modified_tag, value_tag)).text
    [last_modified_date, last_modified_time] = deposit_date_text.split('T')


    # Get the start period and parse the strings into numerical date values
    period_text = root.find(".//%s/%s" % (period_tag, value_tag)).text
    [start_period, end_period, scheme] = period_text.split()
    start_period = re.sub('start=', '', start_period)
    end_period = re.sub('end=', '', end_period)
    [start_period_date, start_period_time] = start_period.split('T')
    [end_period_date, end_period_time] = end_period.split('T')

    related_publications = root.findall(".//%s/%s//*" % (relation_tag, description_tag))
    print('related_publications:', related_publications[0].text, related_publications[1].text)

    related_publications_vals = []
    related_resources = []
    for i, related_publication in enumerate(root.findall(".//%s/%s//*" % (relation_tag, description_tag))):
        related_publications_vals.append(copy.deepcopy(related_publications_dict))
        related_publications_vals[i]['publicationCitation']['value'] = related_publication.text
        related_publications_vals[i]['publicationURL']['value'] = find_url(related_publication.text)

        related_resources.append(related_publication.text)

    # Assign the dataverse metadata fields with these extracted hydroshare
    # fields
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

    # create a json file to store the dataverse metdata
    with open('data.json', 'w') as outfile:
        json.dump(data, outfile, indent=2)

    # read the json file nad call the pydataverse api to create the dataset
    # at the given location

    # server url
    base_url = 'https://dataverse.harvard.edu'

    # api-token
    api_token = 'c57020c2-d954-48da-be47-4e06785ceba0'

    # parent given here
    dv = 'mydv'

    api = Api(base_url, api_token)

    with open('data.json') as json_file:
        metadata = json.load(json_file)
    r = api.create_dataset(dv, json.dumps(metadata))
