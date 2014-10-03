from __future__ import absolute_import

from django.db.models import get_model, get_models
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from hs_core.models import AbstractResource
from dublincore.models import QualifiedDublinCoreElement
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User, Group
from django.core.serializers import get_serializer
from . import hs_bagit
#from hs_scholar_profile.models import *

import importlib
import json
from lxml import etree
import arrow

cached_resource_types = None

def get_resource_types():
    global cached_resource_types
    cached_resource_types = filter(lambda x: issubclass(x, AbstractResource), get_models()) if\
        not cached_resource_types else cached_resource_types

    return cached_resource_types


def get_resource_instance(app, model_name, pk, or_404=True):
    model = get_model(app, model_name)
    if or_404:
        return get_object_or_404(model, pk=pk)
    else:
        return model.objects.get(pk=pk)


def get_resource_by_shortkey(shortkey, or_404=True):
    models = get_resource_types()
    for model in models:
        m = model.objects.filter(short_id=shortkey)
        if m.exists():
            return m[0]
    if or_404:
        raise Http404(shortkey)
    else:
        raise ObjectDoesNotExist(shortkey)


def get_resource_by_doi(doi, or_404=True):
    models = get_resource_types()
    for model in models:
        m = model.objects.filter(doi=doi)
        if m.exists():
            return m[0]
    if or_404:
        raise Http404(doi)
    else:
        raise ObjectDoesNotExist(doi)


def user_from_id(user):
    if isinstance(user, User):
        return user

    try:
        tgt = User.objects.get(username=user)
    except ObjectDoesNotExist:
        try:
            tgt = User.objects.get(email=user)
        except ObjectDoesNotExist:
            try:
                tgt = User.objects.get(pk=int(user))
            except ValueError:
                raise Http404('User not found')
            except ObjectDoesNotExist:
                raise Http404('User not found')
    return tgt


def group_from_id(grp):
    if isinstance(grp, Group):
        return grp

    try:
        tgt = Group.objects.get(name=grp)
    except ObjectDoesNotExist:
        try:
            tgt = Group.objects.get(pk=int(grp))
        except TypeError:
            raise Http404('Group not found')
        except ObjectDoesNotExist:
            raise Http404('Group not found')
    return tgt


def serialize_science_metadata(res):
    js = get_serializer('json')()
    resd = json.loads(js.serialize([res]))[0]['fields']
    resd.update(json.loads(js.serialize([res.page_ptr]))[0]['fields'])

    resd['user'] = json.loads(js.serialize([res.user]))[0]['fields']
    resd['resource_uri'] = resd['short_id']
    resd['user']['resource_uri'] = '/u/' + resd['user']['username']
    resd['dublin_metadata'] = [dc['fields'] for dc in json.loads(js.serialize(res.dublin_metadata.all()))]
    resd['bags'] = [dc['fields'] for dc in json.loads(js.serialize(res.bags.all()))]
    resd['files'] = [dc['fields'] for dc in json.loads(js.serialize(res.files.all()))]
    return json.dumps(resd)


def serialize_system_metadata(res):
    js = get_serializer('json')()
    resd = json.loads(js.serialize([res]))[0]['fields']
    resd.update(json.loads(js.serialize([res.page_ptr]))[0]['fields'])

    resd['user'] = json.loads(js.serialize([res.user]))[0]['fields']
    resd['resource_uri'] = resd['short_id']
    resd['user']['resource_uri'] = '/u/' + resd['user']['username']
    resd['dublin_metadata'] = [dc['fields'] for dc in json.loads(js.serialize(res.dublin_metadata.all()))]
    resd['bags'] = [dc['fields'] for dc in json.loads(js.serialize(res.bags.all()))]
    resd['files'] = [dc['fields'] for dc in json.loads(js.serialize(res.files.all()))]
    return json.dumps(resd)

# Implementation by Pabitra

def serialize_science_metadata_xml(res):
    """
    Generates resource science metadata in xml format
    :param res: the resource object for which science metadata to be generated
    :return: a string as xml document
   """
    res_json = serialize_science_metadata(res)
    res_dict = json.loads(res_json)

    XML_HEADER = '''<?xml version="1.0"?>
<!DOCTYPE rdf:RDF PUBLIC "-//DUBLIN CORE//DCMES DTD 2002/07/31//EN"
"http://dublincore.org/documents/2002/07/31/dcmes-xml/dcmes-xml-dtd.dtd">'''

    NAMESPACES = {'rdf':"http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                   'dc': "http://purl.org/dc/elements/1.1/",
                   'dcterms':"http://purl.org/dc/terms/",
                   'hsterms': "http://hydroshare.org/terms/"}

    DUBLIN_METADATA = 'dublin_metadata'
    DATE_FORMAT = "YYYY-MM-DDThh:mm:ssTZD"
    HYDROSHARE_URL = 'http://hydroshare.org'

    # create the xml document root element
    RDF_ROOT = etree.Element('{%s}RDF' % NAMESPACES['rdf'], nsmap=NAMESPACES)
    rdf_Description = etree.SubElement(RDF_ROOT, '{%s}Description' % NAMESPACES['rdf'])

    # add the uri attribute to point to the resource location
    resource_uri = HYDROSHARE_URL + res_dict['resource_uri']
    rdf_Description.set('{%s}about' % NAMESPACES['rdf'], resource_uri)
    titles = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'T')
    dc_title = etree.SubElement(rdf_Description, '{%s}title' % NAMESPACES['dc'])
    if titles:
        dc_title.text = titles[0]['content']
    else:
        dc_title.text = res_dict['title']

    dc_type = etree.SubElement(rdf_Description, '{%s}type' % NAMESPACES['dc'])

    # add resource type definition url attribute
    # TODO: How to get the url for the resource type
    types = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'TYP')
    if types:
        dc_type.set('{%s}resource' % NAMESPACES['rdf'], types[0]['content'])
    else:
        dc_type.set('{%s}resource' % NAMESPACES['rdf'], res_dict['content_model'])

    dc_description = etree.SubElement(rdf_Description, '{%s}description' % NAMESPACES['dc'])
    dc_des_rdf_Desciption = etree.SubElement(dc_description, '{%s}Description' % NAMESPACES['rdf'])
    dcterms_abstract = etree.SubElement(dc_des_rdf_Desciption, '{%s}abstract' % NAMESPACES['dcterms'])
    abstracts = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'AB')
    if abstracts:
        dcterms_abstract.text = abstracts[0]['content']
    else:
        dcterms_abstract.text = res_dict['description']

    creators = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'CR')

    if creators:
        creator_count = 1
        for creator in creators:
            dc_creator = etree.SubElement(rdf_Description, '{%s}creator' % NAMESPACES['dc'])
            dc_creator_rdf_Description = etree.SubElement(dc_creator, '{%s}Description' % NAMESPACES['rdf'])

            # check if the user has an account in Hydroshare only if the dc element contains a valid email address
            user = None
            if _validate_email(creator['content']):
                try:
                    user = user_from_id(creator['content'])
                except:
                    pass

            hsterms_name = etree.SubElement(dc_creator_rdf_Description, '{%s}name' % NAMESPACES['hsterms'])

            if user:
                user_dict = _get_user_info(user)
                user_uri = HYDROSHARE_URL + user_dict['resource_uri']
                dc_creator_rdf_Description.set('{%s}about' % NAMESPACES['rdf'], user_uri)
                hsterms_name.text = user.get_full_name()
            else:
                hsterms_name.text = creator['content']

            hsterms_creatorOrder = etree.SubElement(dc_creator_rdf_Description, '{%s}creatorOrder' % NAMESPACES['hsterms'])
            hsterms_creatorOrder.text = str(creator_count)
            creator_count +=1

            # try:
            #     # TODO: retrieve a person object based on email address when email address gets implemented
            #     # correctly for Party model
            #     person = Person.objects.filter(uniqueCode = creator['content']).first()
            #     hsterms_name.text = person.name
            # except:
            #     person = None
            #
            # if person and person.organizations.all():
            #     hsterms_organization = etree.SubElement(dc_creator_rdf_Description, '{%s}organization' % NAMESPACES['hsterms'])
            #     hsterms_organization.text = person.organizations.all()[0].name

            if user:
                hsterms_email = etree.SubElement(dc_creator_rdf_Description, '{%s}email' % NAMESPACES['hsterms'])
                hsterms_email.text = user.email

            # TODO: when email address works for Person we will use the following and delete the above if block:
            # if user or person:
            #     hsterms_email = etree.SubElement(dc_creator_rdf_Description, '{%s}email' % NAMESPACES['hsterms'])
            #     hsterms_email.text = user.email if user else person.email_addresses.all()[0].email_address

            # if person:
            #     if person.mail_addresses.all():
            #         hsterms_address = etree.SubElement(dc_creator_rdf_Description, '{%s}address' % NAMESPACES['hsterms'])
            #         # pick the first address - not sure which one we should be using if there are more than one addresses
            #         hsterms_address.text = person.mail_addresses.all()[0].address
            #     if person.phone_numbers.all():
            #         hsterms_phone = etree.SubElement(dc_creator_rdf_Description, '{%s}phone' % NAMESPACES['hsterms'])
            #         # just pick the 1st one as we don't which one to use if there are more than one
            #         hsterms_phone.set('{%s}resource' % NAMESPACES['rdf'], 'tel:' + person.phone_numbers.all()[0].phone_number)
            #     if person.url:
            #         hsterms_homepage = etree.SubElement(dc_creator_rdf_Description, '{%s}homepage' % NAMESPACES['hsterms'])
            #         hsterms_homepage.set('{%s}resource' % NAMESPACES['rdf'], person.url)
            #     # TODO: not sure where to find researcherID and researcherGateID
            #     #scholar.external_identifiers.all()[0].identifierName


    contributors = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'CN')
    if contributors:
        for contributor in contributors:
            user = None
            if _validate_email(contributor['content']):
                try:
                    user = user_from_id(contributor['content'])
                except:
                    pass

            dc_contributor = etree.SubElement(rdf_Description, '{%s}contributor' % NAMESPACES['dc'])
            dc_contributor_rdf_Description = etree.SubElement(dc_contributor, '{%s}Description' % NAMESPACES['rdf'])
            hsterms_name = etree.SubElement(dc_contributor_rdf_Description, '{%s}name' % NAMESPACES['hsterms'])

            if user:
                user_dict = _get_user_info(user)
                user_uri = HYDROSHARE_URL + user_dict['resource_uri']
                dc_contributor_rdf_Description.set('{%s}about' % NAMESPACES['rdf'], user_uri)
                hsterms_name.text = user.get_full_name()
            else:
                hsterms_name.text = contributor['content']

            # try:
            #     # check if the contributor is a Person is in the Party model
            #     # TODO: retrieve a person object based on email address when email address gets implemented
            #     # correctly for Party model
            #     person = Person.objects.filter(uniqueCode = contributor['content']).first()
            #     hsterms_name.text = person.name
            # except:
            #     person = None
            #
            # if person and person.organizations.all():
            #     hsterms_organization = etree.SubElement(dc_creator_rdf_Description, '{%s}organization' % NAMESPACES['hsterms'])
            #     hsterms_organization.text = person.organizations.all()[0].name

            if user:
                hsterms_email = etree.SubElement(dc_contributor_rdf_Description, '{%s}email' % NAMESPACES['hsterms'])
                hsterms_email.text = user.email

            # TODO: when email address is implemented correctly for Person we will use the following code block and delete the above
            # if user or person:
            #     hsterms_email = etree.SubElement(dc_contributor_rdf_Description, '{%s}email' % NAMESPACES['hsterms'])
            #     hsterms_email.text = user.email if user else person.email_addresses.all()[0].email_address

    # coverage
    point_coverages = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'PT')
    if point_coverages:
        dc_coverage = etree.SubElement(rdf_Description, '{%s}coverage' % NAMESPACES['dc'])
        dc_coverage_dcterms_Point = etree.SubElement(dc_coverage, '{%s}Point' % NAMESPACES['dcterms'])
        rdf_point_value = etree.SubElement(dc_coverage_dcterms_Point, '{%s}value' % NAMESPACES['rdf'])
        rdf_point_value.text = point_coverages[0]['content']
    else:
        dc_coverage = etree.SubElement(rdf_Description, '{%s}coverage' % NAMESPACES['dc'])
        box_coverages = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'BX')
        if box_coverages:
            dc_coverage_dcterms_Box = etree.SubElement(dc_coverage, '{%s}Box' % NAMESPACES['dcterms'])
            rdf_box_value = etree.SubElement(dc_coverage_dcterms_Box, '{%s}value' % NAMESPACES['rdf'])
            rdf_box_value.text = box_coverages[0]['content']

    period_coverages = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'PD')
    if period_coverages:
        dc_coverage = etree.SubElement(rdf_Description, '{%s}coverage' % NAMESPACES['dc'])
        dc_coverage_dcterms_Period = etree.SubElement(dc_coverage, '{%s}Period' % NAMESPACES['dcterms'])
        rdf_period_value = etree.SubElement(dc_coverage_dcterms_Period, '{%s}value' % NAMESPACES['rdf'])
        rdf_period_value.text = period_coverages[0]['content']

    dc_date = etree.SubElement(rdf_Description, '{%s}date' % NAMESPACES['dc'])
    dc_date_dcterms_created = etree.SubElement(dc_date, '{%s}created' % NAMESPACES['dcterms'])
    rdf_created_value = etree.SubElement(dc_date_dcterms_created, '{%s}value' % NAMESPACES['rdf'])
    rdf_created_value.text = arrow.get(res_dict['created']).format(DATE_FORMAT)

    dc_date = etree.SubElement(rdf_Description, '{%s}date' % NAMESPACES['dc'])
    dc_date_dcterms_modified = etree.SubElement(dc_date, '{%s}modified' % NAMESPACES['dcterms'])
    rdf_modified_value = etree.SubElement(dc_date_dcterms_modified, '{%s}value' % NAMESPACES['rdf'])
    rdf_modified_value.text = arrow.get(res_dict['updated']).format(DATE_FORMAT)

    if res_dict.get('publish_date', None):
        dc_date = etree.SubElement(rdf_Description, '{%s}date' % NAMESPACES['dc'])
        dc_date_dcterms_published = etree.SubElement(dc_date, '{%s}published' % NAMESPACES['dcterms'])
        rdf_published_value = etree.SubElement(dc_date_dcterms_published, '{%s}value' % NAMESPACES['rdf'])
        rdf_published_value.text = arrow.get(res_dict['publish_date']).format(DATE_FORMAT)

    # format
    formats = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'FMT')
    if formats:
        for format in formats:
            dc_format = etree.SubElement(rdf_Description, '{%s}format' % NAMESPACES['dc'])
            dc_format.text = format['content']

    # identifier
    dc_identifier = etree.SubElement(rdf_Description, '{%s}identifier' % NAMESPACES['dc'])
    dc_id_rdf_Description = etree.SubElement(dc_identifier, '{%s}Description' % NAMESPACES['rdf'])
    hsterms_hs_identifier = etree.SubElement(dc_id_rdf_Description, '{%s}hydroshareIdentifier' % NAMESPACES['hsterms'] )
    hsterms_hs_identifier.text = resource_uri

    if res_dict.get('doi', None):
        dc_identifier = etree.SubElement(rdf_Description, '{%s}identifier' % NAMESPACES['dc'])
        dc_id_rdf_Description = etree.SubElement(dc_identifier, '{%s}Description' % NAMESPACES['rdf'])
        hsterms_DOI = etree.SubElement(dc_id_rdf_Description, '{%s}DOI' % NAMESPACES['hsterms'])
        hsterms_DOI.text = 'http://dx.doi.org/' + res_dict['doi']

    # language
    languages = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'LG')
    if languages:
        dc_lang = etree.SubElement(rdf_Description, '{%s}language' % NAMESPACES['dc'])
        dc_lang.text = languages[0]['content']

    # publisher
    if res_dict.get('publish_date', None):
        publishers = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'PBL')
        if publishers:
            dc_publisher = etree.SubElement(rdf_Description, '{%s}publisher' % NAMESPACES['dc'])
            dc_pub_rdf_Description = etree.SubElement(dc_publisher, '{%s}Description' % NAMESPACES['rdf'])
            hsterms_pub_name = etree.SubElement(dc_pub_rdf_Description, '{%s}publisherName' % NAMESPACES['hsterms'])
            hsterms_pub_name.text = "HydroShare"
            hsterms_pub_url = etree.SubElement(dc_pub_rdf_Description, '{%s}publisherURL' % NAMESPACES['hsterms'])
            hsterms_pub_url.set('{%s}resource' % NAMESPACES['rdf'], HYDROSHARE_URL)

    # relation
    relations = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'REL')
    if relations:
        for relation in relations:
            dc_relation = etree.SubElement(rdf_Description, '{%s}relation' % NAMESPACES['dc'])
            dc_rel_rdf_Description = etree.SubElement(dc_relation, '{%s}Description' % NAMESPACES['rdf'])
            if relation['qualifier'] == 'cities':
                dcterms_cites = etree.SubElement(dc_rel_rdf_Description, '{%s}cites' % NAMESPACES['dcterms'])
                dcterms_cites.set('{%s}resource' % NAMESPACES['rdf'], relation['content'])
            else:
                dcterms_data_for = etree.SubElement(dc_rel_rdf_Description, '{%s}isDataFor' % NAMESPACES['dcterms'])
                dcterms_data_for.text = relation['content']

    # source
    sources = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'SRC')
    if sources:
        for source in sources:
            dc_source = etree.SubElement(rdf_Description, '{%s}source' % NAMESPACES['dc'])
            dc_source_rdf_Description = etree.SubElement(dc_source, '{%s}Description' % NAMESPACES['rdf'])
            dcterms_derived_from = etree.SubElement(dc_source_rdf_Description, '{%s}isDerivedFrom' % NAMESPACES['dcterms'])
            dcterms_derived_from.set('{%s}resource' % NAMESPACES['rdf'], source['content'])

    # rights
    rights = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'RT')
    if rights:
        dc_rights = etree.SubElement(rdf_Description, '{%s}rights' % NAMESPACES['dc'])
        dc_rights_rdf_Description = etree.SubElement(dc_rights, '{%s}Description' % NAMESPACES['rdf'])
        hsterms_statement = etree.SubElement(dc_rights_rdf_Description, '{%s}rightsStatement' % NAMESPACES['hsterms'])
        hsterms_statement.text = rights[0]['content']
        # TODO: Once we have a rights data model it will be possible to get the url of the rights selected by the user

    # subject
    subjects = _get_dc_term_objects(res_dict[DUBLIN_METADATA], 'SUB')
    if subjects:
        for sub in subjects:
            dc_subject = etree.SubElement(rdf_Description, '{%s}subject' % NAMESPACES['dc'])
            dc_subject.text = sub['content']

    return XML_HEADER + '\n' + etree.tostring(RDF_ROOT, pretty_print=True)

#def serialize_resource_map(res):
#    pass
    #serializer = get_serializer(res)
    #bundle = serializer.build_bundle(obj=res)
    #return serializer.serialize(None, serializer.full_dehydrate(bundle), 'application/json')

#def get_serializer(resource):
#    pass
    #tastypie_module = resource._meta.app_label + '.api'        # the module name should follow this convention
    #tastypie_name = resource._meta.object_name + 'Resource'    # the classname of the Resource seralizer
    #tastypie_api = importlib.import_module(tastypie_module)    # import the module
    #return getattr(tastypie_api, tastypie_name)()        # make an instance of the tastypie resource


def resource_modified(resource, by_user=None):
    resource.last_changed_by = by_user
    QualifiedDublinCoreElement.objects.filter(term='DM', object_id=resource.pk).delete()
    QualifiedDublinCoreElement.objects.create(
        term='DM',
        content=now().isoformat(),
        content_object=resource
            )
    resource.save()
    hs_bagit.create_bag(resource)

def _get_dc_term_objects(resource_dc_elements, term):
    return [cr_dict for cr_dict in resource_dc_elements if cr_dict['term'] == term]

def _get_user_info(user):
    from hs_core.api import UserResource

    ur = UserResource()
    ur_bundle = ur.build_bundle(obj=user)
    return json.loads(ur.serialize(None, ur.full_dehydrate(ur_bundle), 'application/json'))

def _validate_email( email ):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email( email )
        return True
    except ValidationError:
        return False
