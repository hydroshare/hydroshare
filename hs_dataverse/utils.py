import json
import xml.etree.ElementTree as ET
import re
import copy
from datetime import datetime
from pyDataverse.api import Api
import os
from django.conf import settings
import googlemaps
import time
import requests
from hs_core.models import BaseResource
import tempfile
from django_irods import icommands
from hs_core.hydroshare import get_party_data_from_user
from hs_core.hydroshare.hs_bagit import create_bag_files
from hs_core.tasks import create_bag_by_irods
from django.template import Context, Template


# global variables
false = False
true = True


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


# get owners. An owner is a user. see https://docs.djangoproject.com/en/3.0/ref/contrib/auth/
def get_owner_data(resource):
    """
    gets the owner metadata for the given resource, and returns it in a dict

    :param resource: the hydroshare resource to get owner_data from
    :return: a dict containing owner data
    """
    owners = list(resource.raccess.owners)
    if len(owners) == 0:
        owner_dict = {
            'username': '',
            'first_name': '',
            'last_name': '',
            'email': '',
            'organization': ''
        }
    else:
        for o in owners:
            party = get_party_data_from_user(o)

            owner_dict = {
                'username': format(o.username),
                'first_name': format(o.first_name),
                'last_name': format(o.last_name),
                'email': format(o.email),
                'organization': format(party['organization'])
            }
    return owner_dict


def get_other_metadata(res, rid):
    """
    gets the other metadata for the given resource, and returns it in a dict.
    other metadata includes extended metadata, funding agency data, contributors, language, doi

    :param resource: the hydroshare resource to get other metadata from
    :return: a dict containing other metadata
    """
    # read extended metadata as key/value pairs
    ext_metadata = ''
    for key, value in list(res.extra_metadata.items()):
        ext_metadata = ext_metadata + key + ': ' + value + ', '

    # get funding agency data
    funding_agency_names = []
    award_numbers = []

    for a in res.metadata.funding_agencies.all():
        funding_agency_names.append(a.agency_name)
        award_numbers.append(a.award_number)

    # get list of contributors
    contributors = []
    for c in res.metadata.contributors.all():
        contributors.append(str(c))

    # if the resource is published, set the doi and update booleans in dict.
    doi = ''
    if res.raccess.public:
        public = True
    else:
        public = False

    if res.raccess.published:
        published = True
        doi = res.doi
    else:
        published = False

    other_metadata_dict = {
        'rid': rid,
        'public': public,
        'published': published,
        'doi': doi,
        'extended_metadata_notes': ext_metadata,
        'language': str(res.metadata.language),
        'funding_agency_names': funding_agency_names,
        'award_numbers': award_numbers,
        'contributors': contributors
    }

    return other_metadata_dict


def export_bag(rid, options):
    """
    exports the bag for the resource with the given resource id, contained in self (self.res)
    :param rid: the resource id of the resource
    :param options: any additional command line arguments to be included
    :return: a temporary directory containing the temporary files of metadata from the resource's bag
    """
    requests.packages.urllib3.disable_warnings()
    try:
        # database handle
        resource = BaseResource.objects.get(short_id=rid)

        # instance with proper subclass type and access
        res = resource.get_content_model()
        assert res, (resource, resource.content_model)
        if (res.discovery_content_type != 'Composite'):
            print("resource type '{}' is not supported. Aborting.".format(res.discovery_content_type))
            exit(1)

        # create temporary directory
        mkdir = tempfile.mkdtemp(prefix=rid, suffix='_dataverse_tempdir', dir='/tmp')

        # file handle
        istorage = res.get_irods_storage()
        root_exists = istorage.exists(res.root_path)
        if root_exists:
            scimeta_path = os.path.join(res.root_path, 'data',
                                         'resourcemetadata.xml')
            scimeta_exists = istorage.exists(scimeta_path)

            if scimeta_exists:
                if icommands.ACTIVE_SESSION:
                    session = icommands.ACTIVE_SESSION
                else:
                    raise KeyError('settings must have irods_global_session set')

                args = ('-')  # redirect to stdout
                fd = session.run_safe('iget', None, scimeta_path, *args)

                contents = b""
                BUFSIZE = 4096
                block = fd.stdout.read(BUFSIZE)
                while block != b"":
                    contents += block
                    block = fd.stdout.read(BUFSIZE)

                _, mkfile_path = tempfile.mkstemp(prefix='resourcemetadata.xml', dir=mkdir)
                with open(mkfile_path, 'wb') as mkfile:
                    mkfile.write(contents)
            else:
                print("resource metadata {} not found".format(scimeta_path))

            bag_exists = istorage.exists(res.bag_path)
            dirty = res.getAVU('metadata_dirty')
            modified = res.getAVU('bag_modified')

            # make sure that the metadata file syncs with the database
            if dirty or not scimeta_exists or options['generate_metadata']:
                try:
                    create_bag_files(res)
                except ValueError as e:
                    print(("{}: value error encountered: {}".format(rid, str(e))))
                    return
                res.setAVU('metadata_dirty', 'false')
                res.setAVU('bag_modified', 'true')

            if modified or not bag_exists or options['generate_bag']:
                create_bag_by_irods(rid)
                res.setAVU('bag_modified', 'false')

                if icommands.ACTIVE_SESSION:
                    session = icommands.ACTIVE_SESSION
                else:
                    raise KeyError('settings must have irods_global_session set')

                dir = '/'.join([res.root_path, 'data/contents'])
                istorage = res.get_irods_storage()
                data = istorage.listdir(dir)

                for file in data[1]:
                    bag_data_path = '/'.join([res.root_path, 'data/contents', file])
                    args = ('-')  # redirect to stdout
                    fd = session.run_safe('iget', None, bag_data_path, *args)

                    contents = b""
                    block = fd.stdout.read(BUFSIZE)
                    while block != b"":
                        # Do stuff with byte.
                        contents += block
                        block = fd.stdout.read(BUFSIZE)
                        _, mkfile_path = tempfile.mkstemp(prefix=file, dir=mkdir)
                    with open(mkfile_path, 'wb') as mkfile:
                        mkfile.write(contents)

            owner_dict = get_owner_data(resource)
            _, mkfile_path = tempfile.mkstemp(prefix='ownerdata.json', dir=mkdir)
            with open(mkfile_path, 'w') as mkfile:
                json.dump(owner_dict, mkfile)

            other_metadata_dict = get_other_metadata(res, rid)
            _, mkfile_path = tempfile.mkstemp(prefix='other_metadata.json', dir=mkdir)
            with open(mkfile_path, 'w') as mkfile:
                json.dump(other_metadata_dict, mkfile)

        else:
            print("Resource with id {} does not exist in iRODS".format(rid))
    except BaseResource.DoesNotExist:
        print("Resource with id {} NOT FOUND in Django".format(rid))

    # before returning the temporary directory, rename all the files by
    # removing the extra characters inserted by mkstemp()
    for file in os.listdir(mkdir):
        file_path = '/'.join([mkdir, file])
        os.rename(file_path, file_path[:-8])  # remove last 8 characters generated by tempfile
        file_path = file_path[:-8]

    return mkdir


def evaluate_json_template(template_path, temp_dir):
    """
    gets all of the resource's metadata, then puts it in the template
    in the json format specified by dataverse

    :param temp_dir: the temporary directory containing the resource's bag metadata files
    :return: the metadata dict
    """
    # parse the xml metadata file as an etree
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

    # Using the tags, extract fields into local variables
    title = set_field(root.find(".//%s" % title_tag))
    abstract = set_field(root.find(".//%s" % abstract_tag))

    alt_url = set_field(root.find(".//%s" % hs_identifier_tag))

    author_dict = {'name': '', 'affiliation': '', 'id_scheme': '', 'identifier': ''}
    authors = []
    for creator in root.findall(".//%s" % creator_tag):
        authors.append(copy.deepcopy(author_dict))

    contact_dict = {'name': '', 'affiliation': '', 'email': ''}
    contacts = []
    for i, author in enumerate(authors):
        author['name'] = set_field(root.find(
            ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, name_tag)))
        author['affiliation'] = set_field(root.find(
            ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, org_tag)))
        author['id_scheme'] = 'ORCID'
        author['identifier'] = find_url(set_field(root.find(
            ".//%s[%s]/%s" % (creator_tag, i + 1, description_tag))), alt_url)

        if i == 0:  # use the first author as the contact person for the dataset
            contact = copy.deepcopy(contact_dict)
            contact['name'] = set_field(root.find(
                ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, name_tag)))
            contact['affiliation'] = set_field(root.find(
                ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, org_tag)))
            contact['email'] = set_field(root.find(
                ".//%s[%s]/%s/%s" % (creator_tag, i + 1, description_tag, email_tag)))
            if contact['name'] == 'None':
                contact['name'] = 'Hydroshare'
            if contact['email'] == 'None':
                contact['email'] = 'help@cuahsi.org'
            contacts.append(contact)

    keywords = []
    for i, keyword in enumerate(root.findall(".//%s" % keyword_tag)):
        keyword = set_field(root.find(".//%s[%s]" % (keyword_tag, i + 1)))
        keywords.append(keyword)

    subject = 'Earth and Environmental Sciences'

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

    related_publication_dict = {'citation': '', 'url': ''}
    related_publications = []
    related_resources = []
    for i, related_publication in enumerate(root.findall(".//%s/%s//*" % (relation_tag, description_tag))):
        related_publications.append(copy.deepcopy(related_publication_dict))
        related_publications[i]['citation'] = set_field(related_publication)
        related_publications[i]['url'] = find_url(set_field(related_publication), alt_url)

        related_resources.append(related_publication.text)

    related_materials = []
    for i, source in enumerate(root.findall(".//%s/%s//*" % (source_tag, description_tag))):
        related_materials.append(set_field(source))

    # use the google location services api to find the location
    maps_api_token = getattr(settings, 'MAPS_KEY', '')
    gmaps = googlemaps.Client(key=maps_api_token)

    geo_info = {'country': '', 'state': '', 'city': '', 'other': ''}
    geo_units = []
    bounding_box = {'north': '', 'south': '', 'east': '', 'west': ''}

    bounding_box_text = set_field(root.find('.//%s/%s' % (box_tag, value_tag)))
    if (bounding_box_text != 'None'):
        [northlimit, eastlimit, southlimit, westlimit, units, projection] = bounding_box_text.split(';')
        bounding_box['north'] = re.sub('northlimit=', '', northlimit)
        bounding_box['east'] = re.sub('eastlimit=', '', eastlimit)
        bounding_box['west'] = re.sub('westlimit=', '', westlimit)
        bounding_box['south'] = re.sub('southlimit=', '', southlimit)
        geo_units.append(re.sub('units=', '', units))

    spot_text = set_field(root.find('.//%s/%s' % (spot_tag, value_tag)))
    if (spot_text != 'None'):
        [name, east, north, units, projection] = spot_text.split(';', 4)
        # for point coordinates, westlimit == eastlimit, and northlimit == southlimit
        bounding_box['east'] = re.sub('east=', '', east)
        bounding_box['west'] = re.sub('east=', '', east)
        bounding_box['north'] = re.sub('north=', '', north)
        bounding_box['south'] = re.sub('north=', '', north)
        geo_units.append(re.sub(' units=', '', units))
        reverse_geo_code_result = gmaps.reverse_geocode((bounding_box['north'], bounding_box['east']))
        if not reverse_geo_code_result:
            type_dict = {'types': []}
            reverse_geo_code_result.append({'address_components': [type_dict]})

        for comp in reverse_geo_code_result[0]['address_components']:
            if 'country' in comp['types']:
                geo_info['country'] = comp['long_name']
            if 'administrative_area_level_1' in comp['types']:
                geo_info['state'] = comp['long_name']
            if 'locality' in comp['types']:
                geo_info['city'] = comp['long_name']
        geo_info['other'] = re.sub('name=', '', name)

    # Extract more fields using the extended metadata from other_metadata.json
    e = dict()
    with open('/'.join([temp_dir, 'other_metadata.json'])) as f:
        e = json.load(f)

    notes = e['extended_metadata_notes']
    rid = e['rid']

    grant_dict = {'name': '', 'number': ''}
    grant_info = []
    for i, grant in enumerate(e['award_numbers']):
        g = copy.deepcopy(grant_dict)
        g['name'] = e['funding_agency_names'][i]
        g['number'] = e['award_numbers'][i]
        grant_info.append(g)

    contributors = []
    for contributor in e['contributors']:
        contributors.append(contributor)

    # Extract more fields using the owner data from ownerdata.json
    o = dict()
    with open('/'.join([temp_dir, 'ownerdata.json'])) as f:
        o = json.load(f)
    contact = copy.deepcopy(contact_dict)
    producer_dict = {'name': '', 'abreviation': '', 'affiliation': ''}
    if 'username' in o:
        producer_dict['abbreviation'] = o['username']
    else:
        producer_dict['abbreviation'] = ''

    if 'first_name' in o and 'last_name' in o:
        producer_dict['name'] = o['last_name'] + ', ' + o['first_name']
        contact['name'] = o['last_name'] + ', ' + o['first_name']
        depositor = o['last_name'] + ', ' + o['first_name']
    else:
        producer_dict['name'] = ''
        contact['name'] = ''
        depositor = ''

    if 'organization' in o:
        producer_dict['affiliation'] = o['organization']
        contact['affiliation'] = o['organization']
    else:
        producer_dict['affiliation'] = ''
        contact['affiliation'] = ''

    if 'email' in o:
        contact['email'] = o['email']
    else:
        contact['email'] = ''
    if contact != contact_dict:
        contacts.append(contact)

    with open(template_path, 'r') as f:
        template = Template(f.read())
    context = Context({'title': title,
                       'alt_url': alt_url,
                       'rid': rid,
                       'authors': authors,
                       'contacts': contacts,
                       'abstract': abstract,
                       'modified_date': last_modified_date,
                       'subject': subject,
                       'keywords': keywords,
                       'related_publications': related_publications,
                       'notes': notes,
                       'producers': [producer_dict],
                       'contributors': contributors,
                       'grant_info': grant_info,
                       'distribution_date': str(datetime.date(datetime.now())),
                       'depositor': depositor,
                       'deposit_date': deposit_date,
                       'start_period_date': start_period_date,
                       'end_period_date': end_period_date,
                       'related_materials': related_materials,
                       'geo_info': geo_info,
                       'geo_units': geo_units,
                       'bounding_box': bounding_box})

    return template.render(context)


def upload_dataset(base_url, api_token, dv, temp_dir):
    """
    uploads a dataset to the specified dataverse location, using the data specified in the file resourcemetadata.xml

    :param base_url: the dataverse server url
    :param api_token: the dataverse api_token
    :param dv: the parent dataverse to upload the dataset to, either a dataverse name or id
    :param temp_dir: the temporary directory containing the resource's bag metadata files
    :return: nothing
    """

    x = evaluate_json_template('hs_dataverse/templates/template.json', temp_dir)
    metadata = json.loads(x)
    api = Api(base_url, api_token)

    # query_str = '/dataverses/' + dv + '/contents'
    # params = {}
    # resp = api.get_request(query_str, params=params, auth=True)
    #
    # extracting response data in json format
    # dv_data = resp.json()
    #
    # num_dv = len(dv_data[u'data'])
    # eventually, there should be a button which allows users to choose locations from among these
    # print all dataverse and dataset titles
    # for i in range(0, num_dv):
    #    if((dv_data[u'data'][i][u'type'] == 'dataverse')):
    #        print("Dataverse: " + dv_data[u'data'][i][u'title'])
    #    if((dv_data[u'data'][i][u'type'] == 'dataset')):
    #        print("Dataset: " + dv_data[u'data'][i][u'identifier'])

    r = api.create_dataset(dv, json.dumps(metadata))
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
                os.remove(file_path)
                done = True
            except:
                count += 1
                if count >= 5:
                    done = True
                    print('Could not upload file: {}'.format(file))
                else:
                    time.sleep(7)
