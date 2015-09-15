import arrow
import os
import shutil
import errno
import tempfile
import mimetypes
import zipfile
import datetime
import re

import pytz
from foresite import utils, Aggregation, AggregatedResource, RdfLibSerializer
import rdflib
from rdflib import URIRef
from rdflib import Namespace
from rdflib import Graph
#from rdflib.namespace import DC, DCTERMS

import bagit

from mezzanine.conf import settings

from hs_core.models import Bags, ResourceFile
from django_irods.storage import IrodsStorage
from django_irods.icommands import SessionException


# TODO: Should go in utils
HS_DATE_PATT = "^(?P<year>[0-9]{4})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})"
HS_DATE_PATT += "T(?P<hour>[0-9]{2}):(?P<minute>[0-9]{2}):(?P<second>[0-9]{2})"
HS_DATE_PATT += "T(?P<tz>\S+)$"
HS_DATE_RE = re.compile(HS_DATE_PATT)

def hs_date_to_datetime(datestr):
    """
    Parse HydroShare (HS) formatted date from a String to a datetime.datetime.
     Note: We use a weird TZ format, that does not appear to be ISO 8601
     compliant, e.g.: 2015-06-03T09:29:00T-00003
    :param datestr: String representing the date in HS format
    :return: datetime.datetime with timezone set to UTC
    """
    m = HS_DATE_RE.match(datestr)
    if m is None:
        msg = "Unable to parse creation date {0}.".format(datestr)
        raise HsBagitException(msg)
    ret_date = datetime.datetime(year=int(m.group('year')),
                                 month=int(m.group('month')),
                                 day=int(m.group('day')),
                                 hour=int(m.group('hour')),
                                 minute=int(m.group('minute')),
                                 second=int(m.group('second')),
                                 tzinfo=pytz.utc)
    return ret_date


class ResourceMeta(object):
    root_uri = None
    # From resource map
    id = None
    res_type = None
    title = None
    files = []
    # From resource metadata
    abstract = None
    keywords = []
    creators = []
    language = None
    rights_uri = None
    creation_date = None
    modification_date = None

    def __init__(self):
        pass


class ResourceCreator(object):
    uri = None
    name = None
    order = None
    email = None

    def __init__(self):
        pass

    def __str__(self):
        msg = "ResourceCreator {uri}, name: {name}, "
        msg += "order: {order}, email: {email}"
        msg = msg.format(uri=self.uri,
                         name=self.name,
                         order=self.order,
                         email=self.email)
        return msg.format(msg)

    def __unicode__(self):
        return unicode(str(self))


class HsBagitException(Exception):
    pass


def delete_bag(resource):
    """
    delete the resource bag

    Parameters:
    :param resource: the resource to delete the bag for.
    :return: none
    """
    res_id = resource.short_id
    istorage = IrodsStorage()

    # delete resource directory first to remove all generated bag-related files for the resource
    istorage.delete(res_id)

    # the resource bag may not exist due to on-demand bagging
    bagname = 'bags/{res_id}.zip'.format(res_id=res_id)
    if istorage.exists(bagname):
        # delete the resource bag
        istorage.delete(bagname)

    # delete the bags table
    for bag in resource.bags.all():
        bag.delete()


def create_bag_files(resource):
    """
    create and update all files needed by bagit operation that is conducted on iRODS server; no bagit operation
    is performed, only files that will be included in the bag are created or updated.

    Parameters:
    :param resource: A resource whose files will be created or updated to be included in the resource bag.

    :return: istorage, an IrodsStorage object,that will be used by subsequent operation to create a bag on demand as needed.
    """
    from . import utils as hs_core_utils
    DATE_FORMAT = "YYYY-MM-DDThh:mm:ssTZD"
    istorage=IrodsStorage()

    dest_prefix = getattr(settings, 'BAGIT_TEMP_LOCATION', '/tmp/hydroshare/')
    bagit_path = os.path.join(dest_prefix, resource.short_id, arrow.get(resource.updated).format("YYYY.MM.DD.HH.mm.ss"))

    for d in (dest_prefix, bagit_path):
        try:
            os.makedirs(d)
        except OSError as ex:
            if ex.errno == errno.EEXIST:
                shutil.rmtree(d)
                os.makedirs(d)
            else:
                raise Exception(ex.message)

    # an empty visualization directory will not be put into the zipped bag file by ibun command, so creating an empty
    # visualization directory to be put into the zip file as done by the two statements below does not work. However,
    # if visualization directory has content to be uploaded, it will work. This is to be implemented as part of the
    # resource model in the future. The following two statements are placeholders serving as reminder
    # to_file_name = '{res_id}/data/visualization/'.format(res_id=resource.short_id)
    # istorage.saveFile('', to_file_name, create_directory=True)

    # create resourcemetadata.xml and upload it to iRODS
    from_file_name = '{path}/resourcemetadata.xml'.format(path=bagit_path)
    with open(from_file_name, 'w') as out:
        out.write(resource.metadata.get_xml())

    to_file_name = '{res_id}/data/resourcemetadata.xml'.format(res_id=resource.short_id)
    istorage.saveFile(from_file_name, to_file_name, True)

    # make the resource map
    current_site_url = hs_core_utils.current_site_url()
    hs_res_url = '{hs_url}/resource/{res_id}/data'.format(hs_url=current_site_url, res_id=resource.short_id)
    metadata_url = os.path.join(hs_res_url, 'resourcemetadata.xml')
    res_map_url = os.path.join(hs_res_url, 'resourcemap.xml')

    ##make the resource map:
    # utils.namespaces['hsterms'] = Namespace('{hs_url}/hsterms/'.format(hs_url=current_site_url))
    # utils.namespaceSearchOrder.append('hsterms')
    utils.namespaces['citoterms'] = Namespace('http://purl.org/spar/cito/')
    utils.namespaceSearchOrder.append('citoterms')

    ag_url = os.path.join(hs_res_url, 'resourcemap.xml#aggregation')
    a = Aggregation(ag_url)

    #Set properties of the aggregation
    a._dc.title = resource.title
    a._dcterms.type = resource._meta.object_name
    a._citoterms.isDocumentedBy = metadata_url
    a._ore.isDescribedBy = res_map_url

    #Create a description of the metadata document that describes the whole resource and add it to the aggregation
    resMetaFile = AggregatedResource(metadata_url)
    resMetaFile._dc.title = "Dublin Core science metadata document describing the HydroShare resource"
    resMetaFile._citoterms.documents = ag_url
    resMetaFile._ore.isAggregatedBy = ag_url
    resMetaFile._dc.format = "application/rdf+xml"


    #Create a description of the content file and add it to the aggregation
    files = ResourceFile.objects.filter(object_id=resource.id)
    resFiles = []
    for n, f in enumerate(files):
        filename = os.path.basename(f.resource_file.name)
        resFiles.append(AggregatedResource(os.path.join('{hs_url}/resource/{res_id}/data/contents/{file_name}'.format(
            hs_url=current_site_url, res_id=resource.short_id, file_name=filename))))

        resFiles[n]._ore.isAggregatedBy = ag_url
        resFiles[n]._dc.format = hs_core_utils.get_file_mime_type(filename)

    #Add the resource files to the aggregation
    a.add_resource(resMetaFile)
    for f in resFiles:
        a.add_resource(f)

    #Register a serializer with the aggregation.  The registration creates a new ResourceMap, which needs a URI
    serializer = RdfLibSerializer('xml')
    resMap = a.register_serialization(serializer, res_map_url)
    resMap._dc.identifier = resource.short_id  #"resource_identifier"

    #Fetch the serialization
    remdoc = a.get_serialization()

    # change the namespace for the 'creator' element from 'dcterms' to 'dc'
    xml_string = remdoc.data.replace('dcterms:creator', 'dc:creator')

    # create resourcemap.xml and upload it to iRODS
    from_file_name = os.path.join(bagit_path, 'resourcemap.xml')
    with open(from_file_name, 'w') as out:
        out.write(xml_string)
    to_file_name = os.path.join(resource.short_id, 'data', 'resourcemap.xml')
    istorage.saveFile(from_file_name, to_file_name, False)

    shutil.rmtree(bagit_path)

    return istorage


def create_bag_by_irods(resource_id, istorage = None):
    """
    create a resource bag on iRODS side by running the bagit rule followed by ibun zipping operation

    Parameters:
    :param resource_id: the resource uuid that is used to look for the resource to create the bag for.
           istorage: IrodsStorage object that is used to call irods bagit rule operation and zipping up operation

    :return: none
    """
    if not istorage:
        istorage = IrodsStorage()

    # only proceed when the resource is not deleted potentially by another request when being downloaded
    if istorage.exists(resource_id):
        # call iRODS bagit rule here
        irods_dest_prefix = "/" + settings.IRODS_ZONE + "/home/" + settings.IRODS_USERNAME
        irods_bagit_input_path = os.path.join(irods_dest_prefix, resource_id)
        bagit_input_path = "*BAGITDATA='{path}'".format(path=irods_bagit_input_path)
        bagit_input_resource = "*DESTRESC='{def_res}'".format(def_res=settings.IRODS_DEFAULT_RESOURCE)
        bagit_rule_file = getattr(settings, 'IRODS_BAGIT_RULE', 'hydroshare/irods/ruleGenerateBagIt_HS.r')

        try:
            # call iRODS run and ibun command to create and zip the bag,
            # ignore SessionException for now as a workaround which could be raised
            # from potential race conditions when multiple ibun commands try to create the same zip file or
            # the very same resource gets deleted by another request when being downloaded
            istorage.runBagitRule(bagit_rule_file, bagit_input_path, bagit_input_resource)
            istorage.zipup(irods_bagit_input_path, 'bags/{res_id}.zip'.format(res_id=resource_id))
        except SessionException:
            pass


def create_bag(resource):
    """
    Modified to implement the new bagit workflow. The previous workflow was to create a bag from the current filesystem
    of the resource, then zip it up and add it to the resource. The new workflow is to delegate bagit and zip-up
    operations to iRODS, specifically, by executing an iRODS bagit rule to create bagit file hierarchy, followed by
    execution of an ibun command to zip up the bagit file hierarchy.

    Note, this procedure may take awhile.  It is highly advised that it be deferred to a Celery task.

    Parameters:
    :param resource: (subclass of AbstractResource) A resource to create a bag for.

    :return: the hs_core.models.Bags instance associated with the new bag.
    """

    istorage = create_bag_files(resource)

    # set bag_modified-true AVU pair for on-demand bagging.to indicate the resource bag needs to be created when user clicks on download button
    istorage.setAVU(resource.short_id, "bag_modified", "true")

    # link the zipped bag file in IRODS via bag_url for bag downloading
    b = Bags.objects.create(
        content_object=resource.baseresource,
        timestamp=resource.updated
    )

    return b


def read_bag(bag_path):
    """

    :param bag_path:
    :return:
    """
    #import pdb; pdb.set_trace()
    tmpdir = None
    unpacked_bag_path = None

    try:
        if not os.path.exists(bag_path):
            raise HsBagitException('Bag does not exist')
        if os.path.isdir(bag_path):
            unpacked_bag_path = bag_path
        else:
            mtype = mimetypes.guess_type(bag_path)
            if mtype[0] != 'application/zip':
                msg = "Expected bag to have MIME type application/zip, but it has {0} instead.".format(mtype[0])
                raise HsBagitException(msg)
            tmpdir = tempfile.mkdtemp()
            zfile = zipfile.ZipFile(bag_path)
            zroot = zfile.namelist()[0].split(os.sep)[0]
            zfile.extractall(tmpdir)
            unpacked_bag_path = os.path.join(tmpdir, zroot)

        bag = bagit.Bag(unpacked_bag_path)
        if not bag.is_valid():
            msg = "Bag is not valid"
            raise HsBagitException(msg)

    finally:
        if tmpdir:
            shutil.rmtree(tmpdir)


def read_resource_map(bag_content_path):
    """
    Attempt to read resource metadata out of the resourcemap.xml of the
     exploded bag path
    :param bag_content_path: String representing the filesystem path of
     exploded bag contents
    :return: Tuple of type (ResourceMeta, String) where String represents the
     relative path of the resourcemetadata.xml, within bag_content_path,
     from which further metadata can be read.
    :raises: HsBagitException if metadata cannot be found or do not appear
     as expected.
    """
    rmap_path = os.path.join(bag_content_path, 'data', 'resourcemap.xml')
    if not os.path.isfile(rmap_path):
        raise HsBagitException("Resource map {0} does not exist".format(rmap_path))
    if not os.access(rmap_path, os.R_OK):
        raise HsBagitException("Unable to read resource map {0}".format(rmap_path))

    res_meta = ResourceMeta()

    g = Graph()
    g.parse(rmap_path)
    # Get resource ID
    for s,p,o in g.triples((None, None, None)):
        if s.endswith("resourcemap.xml") and p == rdflib.namespace.DC.identifier:
            res_meta.id = o
    if res_meta.id is None:
        raise HsBagitException("Unable to determine resource ID from resource map {0}".format(rmap_path))
    print("Resource ID is {0}".format(res_meta.id))

    # Build URI reference for #aggregation section of resource map
    res_root_uri = "http://www.hydroshare.org/resource/{res_id}".format(res_id=res_meta.id)
    res_meta.root_uri = res_root_uri
    res_agg_subj = "{res_root_url}/data/resourcemap.xml#aggregation".format(res_root_url=res_root_uri)
    res_agg = URIRef(res_agg_subj)

    # Get resource type
    type_lit = g.value(res_agg, rdflib.namespace.DCTERMS.type)
    if type_lit is None:
        raise HsBagitException("No resource type found in resource map {0}".format(rmap_path))
    res_meta.res_type = str(type_lit)
    print("\tType is {0}".format(res_meta.res_type))

    # Get resource title
    title_lit = g.value(res_agg, rdflib.namespace.DC.title)
    if title_lit is None:
        raise HsBagitException("No resource title found in resource map {0}".format(rmap_path))
    res_meta.title = str(title_lit)
    print("\tTitle is {0}".format(res_meta.title))

    # Get list of files in resource
    res_root_uri_withslash = res_root_uri + '/'
    res_meta_path = None
    ore = rdflib.namespace.Namespace('http://www.openarchives.org/ore/terms/')
    for s,p,o in g.triples((res_agg, ore.aggregates, None)):
        if o.endswith('resourcemetadata.xml'):
            if res_meta_path is not None and o != res_meta_path:
                msg = "More than one resource metadata URI found. "
                msg += "(first: {first}, second: {second}".format(first=res_meta_path,
                                                                  second=o)
                raise HsBagitException(msg)
            res_meta_path = o.split(res_root_uri_withslash)[1]
            continue

        res_meta.files.append(o.split(res_root_uri_withslash)[1])

    if res_meta_path is None:
        raise HsBagitException("No resource metadata found in resource map {0}".format(rmap_path))

    print("\tResource metadata path {0}".format(res_meta_path))

    for uri in res_meta.files:
        print("\tContents: {0}".format(uri))

    return (res_meta, res_meta_path)


def read_resource_metadata(bag_content_path, res_meta_path, res_meta):
    """

    :param bag_content_path: String representing the filesystem path of
     exploded bag contents
    :param res_meta_path: String represents the relative path of the
     resourcemetadata.xml, within bag_content_path, from which further
     metadata can be read.
    :param res_meta: ResourceMeta representing resource metadata
    :return: None
    """
    rmeta_path = os.path.join(bag_content_path, res_meta_path)
    if not os.path.isfile(rmeta_path):
        raise HsBagitException("Resource metadata {0} does not exist".format(rmeta_path))
    if not os.access(rmeta_path, os.R_OK):
        raise HsBagitException("Unable to read resource metadata {0}".format(rmeta_path))

    g = Graph()
    g.parse(rmeta_path)

    hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')
    res_uri = URIRef(res_meta.root_uri)

    # Make sure title matches that from resource map
    title_lit = g.value(res_uri, rdflib.namespace.DC.title)
    title = str(title_lit)
    if title != res_meta.title:
        msg = "Title from resource metadata {0} "
        msg += "does not match title from resource map {1}".format(title, res_meta.title)
        raise HsBagitException(msg)

    # Get abstract
    for s,p,o in g.triples((None, rdflib.namespace.DCTERMS.abstract, None)):
        res_meta.abstract = o
    if res_meta.abstract:
        print("\t\tAbstract: {0}".format(res_meta.abstract))

    # Get creators
    for s,p,o in g.triples((None, rdflib.namespace.DC.creator, None)):
        creator = ResourceCreator()
        creator.uri = o
        print("\t\tSubject: {0}\npred: {1}\nobj: {2}\n".format(s, p, o))
        # Get name
        name_lit = g.value(o, hsterms.name)
        if name_lit is None:
            msg = "Name for creator {0} was not found.".format(o)
            raise HsBagitException(msg)
        creator.name = str(name_lit)
        # Get order
        order_lit = g.value(o, hsterms.creatorOrder)
        if order_lit is None:
            msg = "Order for creator {0} was not found.".format(o)
            raise HsBagitException(msg)
        creator.order = str(order_lit)
        # Get email
        email_lit = g.value(o, hsterms.email)
        if email_lit is None:
            msg = "E-mail for creator {0} was not found.".format(o)
            raise HsBagitException(msg)
        creator.email = str(email_lit)

        res_meta.creators.append(creator)

    for c in res_meta.creators:
        print("\t\tCreator: {0}".format(str(c)))

    # Get creation date
    for s,p,o in g.triples((None, None, rdflib.namespace.DCTERMS.created)):
        created_lit = g.value(s, rdflib.namespace.RDF.value)
        if created_lit is None:
            msg = "Resource metadata {0} does not contain a creation date.".format(rmeta_path)
            raise HsBagitException(msg)
        res_meta.creation_date = hs_date_to_datetime(str(created_lit))

    print("\t\tCreation date: {0}".format(str(res_meta.creation_date)))



def read_bag_meta(bag_content_path):
    (res_meta, res_meta_path) = read_resource_map(bag_content_path)
    read_resource_metadata(bag_content_path, res_meta_path, res_meta)