import arrow
import os
import shutil
import errno
import tempfile
import mimetypes
import zipfile

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

from hs_core.hydroshare.date_util import hs_date_to_datetime, hs_date_to_datetime_iso


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
    contributors = []
    coverages = []
    relations = []
    sources = []
    language = None
    rights = None
    creation_date = None
    modification_date = None
    language = None

    def __init__(self):
        pass


class ResourceCreator(object):
    # Only record elements essential for identifying the user
    # as the user needs to exist in the HydroShare database
    # to have any real meaning.  We really only need the URI,
    # but it is also helpful to have name and e-mail in case
    # we ever want to implement disambiguation logic.
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


class ResourceContributor(object):
    # Only record elements essential for identifying the user
    # as the user needs to exist in the HydroShare database
    # to have any real meaning.  We really only need the URI,
    # but it is also helpful to have name and e-mail in case
    # we ever want to implement disambiguation logic.
    uri = None
    name = None
    email = None

    def __init__(self):
        pass

    def __str__(self):
        msg = "ResourceCreator {uri}, name: {name}, "
        msg += "email: {email}"
        msg = msg.format(uri=self.uri,
                         name=self.name,
                         email=self.email)
        return msg.format(msg)

    def __unicode__(self):
        return unicode(str(self))


class ResourceRights(object):
    uri = None
    statement = None

    def __init__(self):
        pass

    def __str__(self):
        msg = "ResourceRights {uri}, statement: {statement}"
        msg = msg.format(uri=self.uri,
                         statement=self.statement)
        return msg.format(msg)

    def __unicode__(self):
        return unicode(str(self))


class ResourceCoverage(object):
    pass


class ResourceCoveragePeriod(ResourceCoverage):
    """
    Time period resource coverage.
    """
    name = None # Optional
    start_date = None
    end_date = None
    scheme = None

    def __str__(self):
        msg = "ResourceCoveragePeriod start_date: {start_date}, "
        msg += "end_date: {end_date}, scheme: {scheme}"
        msg = msg.format(start_date=self.start_date, end_date=self.end_date,
                         scheme=self.scheme)
        return msg.format(msg)

    def __unicode__(self):
        return unicode(str(self))

    def __init__(self, value_str):
        kvp = value_str.split(';')
        for pair in kvp:
            (key, value) = pair.split('=')
            key = key.strip()
            value = value.strip()
            if key == 'start':
                try:
                    self.start_date = hs_date_to_datetime_iso(value)
                except Exception as e:
                    msg = "Unable to parse start date {0}, error: {1}".format(value,
                                                                              str(e))
                    raise ResourceMetaException(msg)
            elif key == 'end':
                try:
                    self.end_date = hs_date_to_datetime_iso(value)
                except Exception as e:
                    msg = "Unable to parse end date {0}, error: {1}".format(value,
                                                                            str(e))
                    raise ResourceMetaException(msg)
            elif key == 'scheme':
                self.scheme = value
            elif key == 'name':
                self.name = value

        if self.start_date is None:
            msg = "Period coverage '{0}' does not contain start date.".format(value_str)
            raise ResourceMetaException(msg)
        if self.end_date is None:
            msg = "Period coverage '{0}' does not contain end date.".format(value_str)
            raise ResourceMetaException(msg)
        if self.scheme is None:
            msg = "Period coverage '{0}' does not contain scheme.".format(value_str)
            raise ResourceMetaException(msg)


class ResourceCoveragePoint(ResourceCoverage):
    """
    Point geographic resource coverage.
    """
    name = None # Optional
    east = None
    north = None
    units = None
    elevation = None # Optional
    zunits = None # Optional
    projection = None # Optional

    def __str__(self):
        msg = "ResourceCoveragePoint north: {north}, "
        msg += "east: {east}, units: {units}"
        msg = msg.format(north=self.north, east=self.east,
                         units=self.units)
        return msg.format(msg)

    def __unicode__(self):
        return unicode(str(self))

    def __init__(self, value_str):
        kvp = value_str.split(';')
        for pair in kvp:
            (key, value) = pair.split('=')
            key = key.strip()
            value = value.strip()
            if key == 'name':
                self.name = value
            elif key == 'east':
                try:
                    self.east = float(value)
                except Exception as e:
                    msg = "Unable to parse easting {0}, error: {1}".format(value,
                                                                           str(e))
                    raise ResourceMetaException(msg)
            elif key == 'north':
                try:
                    self.north = float(value)
                except Exception as e:
                    msg = "Unable to parse northing {0}, error: {1}".format(value,
                                                                            str(e))
                    raise ResourceMetaException(msg)
            elif key == 'units':
                self.units = value
            elif key == 'projection':
                self.projection = value
            elif key == 'elevation':
                try:
                    self.elevation = float(value)
                except Exception as e:
                    msg = "Unable to parse elevation {0}, error: {1}".format(value,
                                                                             str(e))
                    raise ResourceMetaException(msg)
            elif key == 'zunits':
                self.zunits = value

        if self.east is None:
            msg = "Point coverage '{0}' does not contain an easting.".format(value_str)
            raise ResourceMetaException(msg)
        if self.north is None:
            msg = "Point coverage '{0}' does not contain a northing.".format(value_str)
            raise ResourceMetaException(msg)
        if self.units is None:
            msg = "Point coverage '{0}' does not contain units information.".format(value_str)
            raise ResourceMetaException(msg)


class ResourceCoverageBox(ResourceCoverage):
    """
    Box geographic resource coverage.
    """
    name = None # Optional
    northlimit = None
    eastlimit = None
    southlimit = None
    westlimit = None
    units = None
    projection = None # Optional
    uplimit = None # Optional
    downlimit = None # Optional
    zunits = None # Only present if uplimit or downlimit is present

    def __str__(self):
        msg = "ResourceCoverageBox northlimit: {northlimit}, "
        msg += "eastlimit: {eastlimit}, southlimit: {southlimit}, "
        msg += "westlimit: {westlimit}, units: {units}"
        msg = msg.format(northlimit=self.northlimit, eastlimit=self.eastlimit,
                         southlimit=self.southlimit, westlimit=self.westlimit,
                         units=self.units)
        return msg.format(msg)

    def __unicode__(self):
        return unicode(str(self))

    def __init__(self, value_str):
        kvp = value_str.split(';')
        for pair in kvp:
            (key, value) = pair.split('=')
            key = key.strip()
            value = value.strip()
            if key == 'name':
                self.name = value
            elif key == 'eastlimit':
                try:
                    self.eastlimit = float(value)
                except Exception as e:
                    msg = "Unable to parse east limit {0}, error: {1}".format(value,
                                                                              str(e))
                    raise ResourceMetaException(msg)
            elif key == 'northlimit':
                try:
                    self.northlimit = float(value)
                except Exception as e:
                    msg = "Unable to parse north limit {0}, error: {1}".format(value,
                                                                               str(e))
                    raise ResourceMetaException(msg)
            elif key == 'southlimit':
                try:
                    self.southlimit = float(value)
                except Exception as e:
                    msg = "Unable to parse south limit {0}, error: {1}".format(value,
                                                                               str(e))
                    raise ResourceMetaException(msg)
            elif key == 'westlimit':
                try:
                    self.westlimit = float(value)
                except Exception as e:
                    msg = "Unable to parse west limit {0}, error: {1}".format(value,
                                                                              str(e))
                    raise ResourceMetaException(msg)
            elif key == 'units':
                self.units = value
            elif key == 'projection':
                self.projection = value
            elif key == 'uplimit':
                try:
                    self.uplimit = float(value)
                except Exception as e:
                    msg = "Unable to parse uplimit {0}, error: {1}".format(value,
                                                                           str(e))
                    raise ResourceMetaException(msg)
            elif key == 'downlimit':
                try:
                    self.downlimit = float(value)
                except Exception as e:
                    msg = "Unable to parse downlimit {0}, error: {1}".format(value,
                                                                             str(e))
                    raise ResourceMetaException(msg)
            elif key == 'zunits':
                self.zunits = value

        if self.zunits is None and (self.uplimit is not None or self.downlimit is not None):
            msg = "Point coverage '{0}' contains uplimit or downlimit but does not contain zunits.".format(value_str)
            raise ResourceMetaException(msg)


class ResourceRelation(object):
    KNOWN_TYPES = {'isParentOf', 'isChildOf', 'isMemberOf', 'isDerivedFrom',
                   'hasBibliographicInfoIn', 'isRevisionHistoryFor',
                   'isCriticalReviewOf','isOverviewOf', 'isContentRatingFor',
                   'isTermsandConditionsFor', 'isDataFor', 'isPartOf',
                   'isExecutedBy', 'isDataFor', 'isVersionOf'}

    uri = None
    relationship_type = None

    def __str__(self):
        msg = "{classname} {relationship_type}: {uri}"
        msg = msg.format(classname=type(self).__name__,
                         relationship_type=self.relationship_type,
                         uri=self.uri)
        return msg.format(msg)

    def __unicode__(self):
        return unicode(str(self))

    def __init__(self, uri, relationship_uri):
        relationship_type = os.path.basename(relationship_uri)
        if relationship_type not in self.KNOWN_TYPES:
            msg = "Relationship uri {0} is not known.".format(relationship_uri)
            raise ResourceMetaException(msg)
        self.uri = uri
        self.relationship_type = relationship_type


class ResourceSource(ResourceRelation):
    KNOWN_TYPES = {'isDerivedFrom'}


class ResourceMetaException(Exception):
    pass


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
    :raises: ResourceMetaException if metadata cannot be found or do not appear
     as expected.
    """
    rmap_path = os.path.join(bag_content_path, 'data', 'resourcemap.xml')
    if not os.path.isfile(rmap_path):
        raise ResourceMetaException("Resource map {0} does not exist".format(rmap_path))
    if not os.access(rmap_path, os.R_OK):
        raise ResourceMetaException("Unable to read resource map {0}".format(rmap_path))

    res_meta = ResourceMeta()

    g = Graph()
    g.parse(rmap_path)
    # Get resource ID
    for s,p,o in g.triples((None, None, None)):
        if s.endswith("resourcemap.xml") and p == rdflib.namespace.DC.identifier:
            res_meta.id = o
    if res_meta.id is None:
        raise ResourceMetaException("Unable to determine resource ID from resource map {0}".format(rmap_path))
    print("Resource ID is {0}".format(res_meta.id))

    # Build URI reference for #aggregation section of resource map
    res_root_uri = "http://www.hydroshare.org/resource/{res_id}".format(res_id=res_meta.id)
    res_meta.root_uri = res_root_uri
    res_agg_subj = "{res_root_url}/data/resourcemap.xml#aggregation".format(res_root_url=res_root_uri)
    res_agg = URIRef(res_agg_subj)

    # Get resource type
    type_lit = g.value(res_agg, rdflib.namespace.DCTERMS.type)
    if type_lit is None:
        raise ResourceMetaException("No resource type found in resource map {0}".format(rmap_path))
    res_meta.res_type = str(type_lit)
    print("\tType is {0}".format(res_meta.res_type))

    # Get resource title
    title_lit = g.value(res_agg, rdflib.namespace.DC.title)
    if title_lit is None:
        raise ResourceMetaException("No resource title found in resource map {0}".format(rmap_path))
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
                raise ResourceMetaException(msg)
            res_meta_path = o.split(res_root_uri_withslash)[1]
            continue

        res_meta.files.append(o.split(res_root_uri_withslash)[1])

    if res_meta_path is None:
        raise ResourceMetaException("No resource metadata found in resource map {0}".format(rmap_path))

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
        raise ResourceMetaException("Resource metadata {0} does not exist".format(rmeta_path))
    if not os.access(rmeta_path, os.R_OK):
        raise ResourceMetaException("Unable to read resource metadata {0}".format(rmeta_path))

    g = Graph()
    g.parse(rmeta_path)

    hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')
    res_uri = URIRef(res_meta.root_uri)

    # Make sure title matches that from resource map
    title_lit = g.value(res_uri, rdflib.namespace.DC.title)
    if title_lit is not None:
        title = str(title_lit)
        if title != res_meta.title:
            msg = "Title from resource metadata {0} "
            msg += "does not match title from resource map {1}".format(title, res_meta.title)
            raise ResourceMetaException(msg)

    # Get abstract
    for s,p,o in g.triples((None, rdflib.namespace.DCTERMS.abstract, None)):
        res_meta.abstract = o
    if res_meta.abstract:
        print("\t\tAbstract: {0}".format(res_meta.abstract))

    # Get creators
    for s,p,o in g.triples((None, rdflib.namespace.DC.creator, None)):
        creator = ResourceCreator()
        creator.uri = o
        # Get name
        name_lit = g.value(o, hsterms.name)
        if name_lit is None:
            msg = "Name for creator {0} was not found.".format(o)
            raise ResourceMetaException(msg)
        creator.name = str(name_lit)
        # Get order
        order_lit = g.value(o, hsterms.creatorOrder)
        if order_lit is None:
            msg = "Order for creator {0} was not found.".format(o)
            raise ResourceMetaException(msg)
        creator.order = str(order_lit)
        # Get email
        email_lit = g.value(o, hsterms.email)
        if email_lit is None:
            msg = "E-mail for creator {0} was not found.".format(o)
            raise ResourceMetaException(msg)
        creator.email = str(email_lit)

        res_meta.creators.append(creator)

    for c in res_meta.creators:
        print("\t\tCreator: {0}".format(str(c)))

    # Get contributors
    for s,p,o in g.triples((None, rdflib.namespace.DC.contributor, None)):
        contributor = ResourceContributor()
        contributor.uri = o
        # Get name
        name_lit = g.value(o, hsterms.name)
        if name_lit is None:
            msg = "Name for contributor {0} was not found.".format(o)
            raise ResourceMetaException(msg)
        contributor.name = str(name_lit)
        # Get email
        email_lit = g.value(o, hsterms.email)
        if email_lit is None:
            msg = "E-mail for contributor {0} was not found.".format(o)
            raise ResourceMetaException(msg)
        contributor.email = str(email_lit)

        res_meta.contributors.append(contributor)

    for c in res_meta.contributors:
        print("\t\tContributor: {0}".format(str(c)))

    # Get creation date
    for s,p,o in g.triples((None, None, rdflib.namespace.DCTERMS.created)):
        created_lit = g.value(s, rdflib.namespace.RDF.value)
        if created_lit is None:
            msg = "Resource metadata {0} does not contain a creation date.".format(rmeta_path)
            raise ResourceMetaException(msg)
        try:
            res_meta.creation_date = hs_date_to_datetime(str(created_lit))
        except Exception as e:
            msg = "Unable to parse creation date {0}, error: {1}".format(str(created_lit),
                                                                         str(e))
            raise ResourceMetaException(msg)

    print("\t\tCreation date: {0}".format(str(res_meta.creation_date)))

    # Get modification date
    for s,p,o in g.triples((None, None, rdflib.namespace.DCTERMS.modified)):
        modified_lit = g.value(s, rdflib.namespace.RDF.value)
        if modified_lit is None:
            msg = "Resource metadata {0} does not contain a modification date.".format(rmeta_path)
            raise ResourceMetaException(msg)
        try:
            res_meta.modification_date = hs_date_to_datetime(str(modified_lit))
        except Exception as e:
            msg = "Unable to parse modification date {0}, error: {1}".format(str(modified_lit),
                                                                             str(e))
            raise ResourceMetaException(msg)

    print("\t\tModification date: {0}".format(str(res_meta.modification_date)))

    # Get rights
    resource_rights = None
    for s,p,o in g.triples((None, rdflib.namespace.DC.rights, None)):
        resource_rights = ResourceRights()
        # License URI
        rights_uri = g.value(o, hsterms.URL)
        if rights_uri is None:
            msg = "Resource metadata {0} does not contain rights URI.".format(rmeta_path)
            raise ResourceMetaException(msg)
        resource_rights.uri = str(rights_uri)
        # Rights statement
        rights_stmt_lit = g.value(o, hsterms.rightsStatement)
        if rights_stmt_lit is None:
            msg = "Resource metadata {0} does not contain rights statement.".format(rmeta_path)
            raise ResourceMetaException(msg)
        resource_rights.statement = str(rights_stmt_lit)

    if resource_rights is None:
        msg = "Resource metadata {0} does not contain rights.".format(rmeta_path)
        raise ResourceMetaException(msg)

    res_meta.rights = resource_rights

    print("\t\tRights: {0}".format(res_meta.rights))

    # Get keywords
    for s,p,o in g.triples((None, rdflib.namespace.DC.subject, None)):
        res_meta.keywords.append(str(o))

    print("\t\tKeywords: {0}".format(str(res_meta.keywords)))

    # Get language
    lang_lit = g.value(res_uri, rdflib.namespace.DC.language)
    if lang_lit is None:
        res_meta.language = 'eng'
    else:
        res_meta.language = str(lang_lit)

    print("\t\tLanguage: {0}".format(res_meta.language))

    # Get coverage (box)
    for s,p,o in g.triples((None, None, rdflib.namespace.DCTERMS.box)):
        coverage_lit = g.value(s, rdflib.namespace.RDF.value)
        if coverage_lit is None:
            msg = "Coverage value not found for {0}.".format(o)
            raise ResourceMetaException(msg)
        coverage = ResourceCoverageBox(str(coverage_lit))
        res_meta.coverages.append(coverage)

    # Get coverage (point)
    for s,p,o in g.triples((None, None, rdflib.namespace.DCTERMS.point)):
        coverage_lit = g.value(s, rdflib.namespace.RDF.value)
        if coverage_lit is None:
            msg = "Coverage value not found for {0}.".format(o)
            raise ResourceMetaException(msg)
        coverage = ResourceCoveragePoint(str(coverage_lit))
        res_meta.coverages.append(coverage)

    # Get coverage (period)
    for s,p,o in g.triples((None, None, rdflib.namespace.DCTERMS.period)):
        coverage_lit = g.value(s, rdflib.namespace.RDF.value)
        if coverage_lit is None:
            msg = "Coverage value not found for {0}.".format(o)
            raise ResourceMetaException(msg)
        coverage = ResourceCoveragePeriod(str(coverage_lit))
        res_meta.coverages.append(coverage)

    print("\t\tCoverages: ")
    for c in res_meta.coverages:
        print("\t\t\t{0}".format(str(c)))

    # Get relations
    for s,p,o in g.triples((None, rdflib.namespace.DC.relation, None)):
        for pred, obj in g.predicate_objects(o):
            relation = ResourceRelation(obj, pred)
            res_meta.relations.append(relation)

    print("\t\tRelations: ")
    for r in res_meta.relations:
        print("\t\t\t{0}".format(str(r)))

    # Get sources
    for s,p,o in g.triples((None, rdflib.namespace.DC.source, None)):
        for pred, obj in g.predicate_objects(o):
            source = ResourceSource(obj, pred)
            res_meta.sources.append(source)

    print("\t\tSources: ")
    for r in res_meta.sources:
        print("\t\t\t{0}".format(str(r)))


def read_bag_meta(bag_content_path):
    (res_meta, res_meta_path) = read_resource_map(bag_content_path)
    read_resource_metadata(bag_content_path, res_meta_path, res_meta)