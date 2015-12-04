import os
import heapq
import xml.sax
import urlparse

import rdflib
from rdflib import URIRef
from rdflib import Graph

from django.contrib.auth.models import User
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from django.db import transaction

from hs_core.hydroshare.utils import get_resource_types
from hs_core.hydroshare.date_util import hs_date_to_datetime, hs_date_to_datetime_iso, hs_date_to_datetime_notz,\
    HsDateException

from hs_core.hydroshare.utils import resource_pre_create_actions
from hs_core.hydroshare.utils import ResourceFileSizeException, ResourceFileValidationException
from hs_core.hydroshare import create_resource
from hs_core.models import BaseResource, validate_user_url
from hs_core.hydroshare.hs_bagit import create_bag_files


class HsSerializationException(Exception):
    pass


class HsDeserializationException(HsSerializationException):
    pass


class HsDeserializationDependencyException(HsDeserializationException):

    def __init__(self, dependency_resource_id, message):
        """
        :param dependency_resource_id: ID of resource that we depend on.
        :param message: Message to append onto standard string representation.
        """
        super(HsDeserializationDependencyException, self).__init__()

        self.dependency_resource_id = dependency_resource_id
        self.message = message

    def __str__(self):
        msg = "{classname} Resource dependency {rid} does not exist: {mesg}"
        msg = msg.format(classname=type(self).__name__,
                         rid=self.dependency_resource_id,
                         mesg=self.message)
        return msg

    def __unicode__(self):
        return unicode(str(self))


def _prepare_resource_files_for_creation(file_paths):
    res_files = []

    for fp in file_paths:
        fname = os.path.basename(fp)
        fsize = os.stat(fp).st_size
        fd = open(fp, 'rb')
        res_files.append(UploadedFile(file=fd, name=fname, size=fsize))

    return res_files


def create_resource_from_bag(bag_content_path, preserve_uuid=True):
    """
    Create resource from existing uncompressed BagIt archive.

    Follows roughly the same pattern as hs_core.views.create_resource().

    :param bag_content_path:
    :return: None if successful.  If the resource associated with the bag
    depends upon the existence of another resource in order for the dependant
    resource's metadata to be fully created, this function will return a
    Tuple<String, ResourceMeta, Resource>), where String is a string
    representing  the resource ID that the Bagged Resource depends on,
    ResourceMeta is a subclass of hs_core.serialization.GenericResourceMeta
    that represents the metadata of the newly created resource, and Resource
    is a subclass of hs_core.model.BaseResource representing the newly created
    resource. Once the dependant resource has been created, the caller is
    responsible for calling ResourceMeta.write_metadata_to_resource(Resource)
    to ensure that all metadata fields have been populated.

    :raises: HsDeserializationException if an error occurred.
    """
    # Get resource metadata
    resource_files = None
    rm = None
    try:
        rm = GenericResourceMeta.read_metadata_from_resource_bag(bag_content_path)
        # Filter resource files
        resource_files_filtered = []
        for f in rm.files:
            if rm.include_resource_file(f):
                resource_files_filtered.append(f)
        res_files = [os.path.join(bag_content_path, f) for f in resource_files_filtered]
        resource_files = _prepare_resource_files_for_creation(res_files)

    except GenericResourceMeta.ResourceMetaException as e:
        msg = "Error occurred while trying to create resource from bag path {0}. "
        msg += "Error was: {1}"
        msg = msg.format(bag_content_path, str(e))
        raise HsDeserializationException(msg)

    # Send pre-create resource signal
    try:
        if resource_files is None:
            resource_files = []

        page_url_dict, res_title, metadata = resource_pre_create_actions(resource_type=rm.res_type,
                                                                         files=resource_files,
                                                                         resource_title=rm.title,
                                                                         page_redirect_url_key=None)
    except ResourceFileSizeException as ex:
        raise HsDeserializationException(ex.message)

    except ResourceFileValidationException as ex:
        raise HsDeserializationException(ex.message)

    except Exception as ex:
        raise HsDeserializationException(ex.message)

    # Create the resource
    resource = None
    try:
        # Get user
        owner = rm.get_owner()
        print(owner.uri)
        print(owner.id)

        pk = owner.id
        if pk is not None:
            rm.owner_is_hs_user = True
        else:
            # Set owner to admin if user doesn't exist
            print("Owner user {0} does not exist, using user 1".format(pk))
            pk = 1
            rm.owner_is_hs_user = False

        resource_id = None
        if preserve_uuid:
            resource_id = rm.id

        kwargs = {}
        resource = create_resource(resource_type=rm.res_type,
                                   owner=pk,
                                   title=rm.title,
                                   keywords=rm.keywords,
                                   metadata=metadata,
                                   files=resource_files,
                                   content=rm.title,
                                   short_id=resource_id,
                                   **kwargs)
    except Exception as ex:
        import traceback
        traceback.print_exc()
        raise HsDeserializationException(ex.message)

    # Add additional metadata
    assert(resource is not None)

    try:
        rm.write_metadata_to_resource(resource)
        # Force bag files to be re-written
        create_bag_files(resource)
    except HsDeserializationDependencyException as e:
        return e.dependency_resource_id, rm, resource

    return None


class GenericResourceMeta(object):
    """
    Lightweight class for representing core metadata of Resources, including the
    ability to read metadata from an un-compressed BagIt archive.

    To support derived resource types, each resource type will have to provide an
    implementation of hs_core.serialization.GenericResourceMeta. For example for
    RasterResource, the implementation would need to be defined in the class
    hs_geo_raster_resource.serialization.RasterResourceMeta (code for class name
    resolution and class loading is already defined in the factory method
    read_metadata_from_resource_bag()). Such derived classes would need to define
    properties to represent resource-specific metadata fields as well override two
    functions: _read_resource_metadata(), and write_metadata_to_resource() (after
    first calling the super class's implementation). I plan to write
    resource-specific GenericResourceMeta implementations after I get your
    comments and suggestions on this approach.
    """
    def __init__(self):
        self.root_uri = None
        # From resource map
        self.id = None
        self.res_type = None
        self.title = None
        self.files = []
        # From resource metadata
        self.abstract = None
        self.keywords = []
        self._creatorsHeap = []
        self.contributors = []
        self.coverages = []
        self.relations = []
        self.sources = []
        self.language = None
        self.rights = None
        self.creation_date = None
        self.modification_date = None

        self.owner_is_hs_user = True
        self.bag_content_path = None
        self.root_uri = None
        self.res_meta_path = None  # Path of resourcemetadata.xml within bag
        self.rmeta_path = None  # Path of resourcemetadata.xml on file system
        self._rmeta_graph = None

    def add_creator(self, creator):
        """
        Add creator to the list of creators, sorting by creator order.
        :param creator: ResourceCreator object
        :return: None
        """
        heapq.heappush(self._creatorsHeap, (creator.order, creator))

    def get_creators(self):
        """

        :return: List of creators sorted by order.
        """
        local_heap = list(self._creatorsHeap)
        return [heapq.heappop(local_heap)[1] for i in range(len(local_heap))]

    @staticmethod
    def include_resource_file(resource_filename):
        """
        :param resource_filename: Name of resource filename.
        :return: True if resource_filename should be included.
        """
        return True

    @classmethod
    def read_metadata_from_resource_bag(cls, bag_content_path):
        """
        Factory method for getting resource-specific metadata from an exploded BagIt archive.
        To work with this factory, each HydroShare resource type must implement
        a class that extends GenericResourceMeta stored in the following package/module:
        ${RESOURCE_PACKAGE}.serialization.${RESOURCE_NAME}Meta.  For example,
        the "RasterResource", with package "hs_geo_raster_resource" must implement its
        subclass as hs_geo_raster_resource.serialization.RasterResourceMeta.

        :param bag_content_path: String representing path of exploded bag
        content.

        :return: An instance of GenericResourceMeta specific to the resource type with all
        metadata read from the exploded bag.

        :raises: ResourceMetaException if metadata cannot be found or do not appear
         as expected.
        """

        # Read resource map so that we know the resource type
        (root_uri, res_meta_path, res_meta) = cls._read_resource_map(bag_content_path)

        # Iterate over HydroShare resource types
        res_types = get_resource_types()
        for rt in res_types:
            rt_name = rt.__name__
            if rt_name == res_meta['type']:
                # Instantiate metadata class for resource type
                rt_root = rt.__module__.split('.')[0]
                rt_meta = "{0}Meta".format(rt_name)
                print("rt_meta: {0}".format(rt_meta))
                mod_ser_name = "{root}.serialization".format(root=rt_root)
                print("mod_ser_name: {0}".format(mod_ser_name))
                instance = None
                try:
                    # Use __import__ to make sure mod_ser is compiled on import (else we can't import it)
                    mod_ser = __import__(mod_ser_name, globals(), locals(), [rt_meta])
                    metadata_class = getattr(mod_ser, rt_meta)
                    instance = metadata_class()
                except AttributeError as ae:
                    msg = "Unable to instantiate metadata deserializer for resource type {0}, "
                    msg += "based on resource bag {1}"
                    msg = msg.format(res_meta['type'], bag_content_path)
                    raise GenericResourceMeta.ResourceMetaException(msg)

                assert(instance is not None)

                # Populate core metadata
                instance.id = res_meta['id']
                instance.res_type = res_meta['type']
                instance.title = res_meta['title']
                instance.files = res_meta['files']

                # Read additional metadata
                instance.bag_content_path = bag_content_path
                instance.res_meta_path = res_meta_path
                instance.root_uri = root_uri
                instance._read_resource_metadata()

                return instance
        return None

    @classmethod
    def _read_resource_map(cls, bag_content_path):
        """
        Read resource metadata out of the resourcemap.xml of the exploded bag path

        :param bag_content_path: String representing path of exploded bag
        content.

        :return: Tuple<String, String, dict> representing: root URI of the resource metadata,
         path of the resourcemetadata.xml within the bag, dictionary containing metadata from resource map.

        :raises: ResourceMetaException if metadata cannot be found or do not appear
         as expected.
        """
        rmap_path = os.path.join(bag_content_path, 'data', 'resourcemap.xml')
        if not os.path.exists(rmap_path):
            raise GenericResourceMeta.ResourceMetaException("Resource map {0} does not exist".format(rmap_path))
        if not os.access(rmap_path, os.R_OK):
            raise GenericResourceMeta.ResourceMetaException("Unable to read resource map {0}".format(rmap_path))

        res_meta = {}

        g = Graph()
        g.parse(rmap_path)
        # Get resource ID
        for s, p, o in g.triples((None, None, None)):
            if s.endswith("resourcemap.xml") and p == rdflib.namespace.DC.identifier:
                res_meta['id'] = o
        if res_meta['id'] is None:
            msg = "Unable to determine resource ID from resource map {0}".format(rmap_path)
            raise GenericResourceMeta.ResourceMetaException(msg)
        print("Resource ID is {0}".format(res_meta['id']))

        # Build URI reference for #aggregation section of resource map
        res_root_uri = "http://www.hydroshare.org/resource/{res_id}".format(res_id=res_meta['id'])
        root_uri = res_root_uri
        res_agg_subj = "{res_root_url}/data/resourcemap.xml#aggregation".format(res_root_url=res_root_uri)
        res_agg = URIRef(res_agg_subj)

        # Get resource type
        type_lit = g.value(res_agg, rdflib.namespace.DCTERMS.type)
        if type_lit is None:
            raise GenericResourceMeta.ResourceMetaException("No resource type found in resource map {0}".format(rmap_path))
        res_meta['type'] = str(type_lit)
        print("\tType is {0}".format(res_meta['type']))

        # Get resource title
        title_lit = g.value(res_agg, rdflib.namespace.DC.title)
        if title_lit is None:
            raise GenericResourceMeta.ResourceMetaException("No resource title found in resource map {0}".format(rmap_path))
        res_meta['title'] = str(title_lit)
        print("\tTitle is {0}".format(res_meta['title']))

        # Get list of files in resource
        res_meta['files'] = []
        res_root_uri_withslash = res_root_uri + '/'
        res_meta_path = None
        ore = rdflib.namespace.Namespace('http://www.openarchives.org/ore/terms/')
        for s, p, o in g.triples((res_agg, ore.aggregates, None)):
            if o.endswith('resourcemetadata.xml'):
                if res_meta_path is not None and o != res_meta_path:
                    msg = "More than one resource metadata URI found. "
                    msg += "(first: {first}, second: {second}".format(first=res_meta_path,
                                                                      second=o)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                res_meta_path = o.split(res_root_uri_withslash)[1]
                continue

            res_meta['files'].append(o.split(res_root_uri_withslash)[1])

        if res_meta_path is None:
            raise GenericResourceMeta.ResourceMetaException("No resource metadata found in resource map {0}".format(rmap_path))

        print("\tResource metadata path {0}".format(res_meta_path))

        for uri in res_meta['files']:
            print("\tContents: {0}".format(uri))

        return (root_uri, res_meta_path, res_meta)

    def _read_resource_metadata(self):
        """
        Read resource metadata out of the resourcemetadata.xml of the exploded bag path

        :return: None
        """
        self.rmeta_path = os.path.join(self.bag_content_path, self.res_meta_path)
        if not os.path.exists(self.rmeta_path):
            raise GenericResourceMeta.ResourceMetaException("Resource metadata {0} does not exist".format(self.rmeta_path))
        if not os.access(self.rmeta_path, os.R_OK):
            raise GenericResourceMeta.ResourceMetaException("Unable to read resource metadata {0}".format(self.rmeta_path))

        # Parse metadata using RDFLib
        self._rmeta_graph = Graph()
        self._rmeta_graph.parse(self.rmeta_path)

        # Also parse using SAX so that we can capture certain metadata elements
        # in the same order in which they appear in the RDF+XML serialization.
        SAX_parse_results = GenericResourceSAXHandler()
        xml.sax.parse(self.rmeta_path, SAX_parse_results)

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')
        res_uri = URIRef(self.root_uri)

        # Make sure title matches that from resource map
        title_lit = self._rmeta_graph.value(res_uri, rdflib.namespace.DC.title)
        if title_lit is not None:
            title = str(title_lit)
            if title != self.title:
                msg = "Title from resource metadata {0} "
                msg += "does not match title from resource map {1}, using {2}."
                msg = msg.format(title, self.title, title)
                self.title = title
                print("Warning {0}".format(msg))

        # Get abstract
        for s, p, o in self._rmeta_graph.triples((None, rdflib.namespace.DCTERMS.abstract, None)):
            self.abstract = o
        if self.abstract:
            print("\t\tAbstract: {0}".format(self.abstract))

        # Get creators
        for s, p, o in self._rmeta_graph.triples((None, rdflib.namespace.DC.creator, None)):
            creator = GenericResourceMeta.ResourceCreator()
            creator.set_uri(o)
            # Get order
            order_lit = self._rmeta_graph.value(o, hsterms.creatorOrder)
            if order_lit is None:
                msg = "Order for creator {0} was not found.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            creator.order = int(str(order_lit))
            # Get name
            name_lit = self._rmeta_graph.value(o, hsterms.name)
            if name_lit is None:
                msg = "Name for creator {0} was not found.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            creator.name = str(name_lit)
            # Get email
            email_lit = self._rmeta_graph.value(o, hsterms.email)
            if email_lit is not None:
                creator.email = str(email_lit)
            # Get organization
            org_lit = self._rmeta_graph.value(o, hsterms.organization)
            if org_lit is not None:
                creator.organization = str(org_lit)
            # Get address
            addy_lit = self._rmeta_graph.value(o, hsterms.address)
            if addy_lit is not None:
                creator.address = str(addy_lit)
            # Get phone
            phone_lit = self._rmeta_graph.value(o, hsterms.phone)
            if phone_lit is not None:
                phone_raw = str(phone_lit).split(':')
                if len(phone_raw) > 1:
                    creator.phone = phone_raw[1]
                else:
                    creator.phone = phone_raw[0]
            # Get homepage
            homepage_lit = self._rmeta_graph.value(o, hsterms.homepage)
            if homepage_lit is not None:
                creator.homepage = str(homepage_lit)

            self.add_creator(creator)

        for c in self.get_creators():
            print("\t\tCreator: {0}".format(str(c)))

        # Get contributors
        if SAX_parse_results:
            # Use contributors from SAX parser
            self.contributors = list(SAX_parse_results.contributors)
        else:
            # Get contributors from RDF
            for s, p, o in self._rmeta_graph.triples((None, rdflib.namespace.DC.contributor, None)):
                contributor = GenericResourceMeta.ResourceContributor()
                contributor.set_uri(o)
                # Get name
                name_lit = self._rmeta_graph.value(o, hsterms.name)
                if name_lit is None:
                    msg = "Name for contributor {0} was not found.".format(o)
                    raise GenericResourceMeta.ResourceMetaException(msg)
                contributor.name = str(name_lit)
                # Get email
                email_lit = self._rmeta_graph.value(o, hsterms.email)
                if email_lit is not None:
                    contributor.email = str(email_lit)
                # Get organization
                org_lit = self._rmeta_graph.value(o, hsterms.organization)
                if org_lit is not None:
                    contributor.organization = str(org_lit)
                # Get address
                addy_lit = self._rmeta_graph.value(o, hsterms.address)
                if addy_lit is not None:
                    contributor.address = str(addy_lit)
                # Get phone
                phone_lit = self._rmeta_graph.value(o, hsterms.phone)
                if phone_lit is not None:
                    phone_raw = str(phone_lit).split(':')
                    if len(phone_raw) > 1:
                        contributor.phone = phone_raw[1]
                    else:
                        contributor.phone = phone_raw[0]
                # Get homepage
                homepage_lit = self._rmeta_graph.value(o, hsterms.homepage)
                if homepage_lit is not None:
                    contributor.homepage = str(homepage_lit)

                self.contributors.append(contributor)

        for c in self.contributors:
            print("\t\tContributor: {0}".format(str(c)))

        # Get creation date
        for s, p, o in self._rmeta_graph.triples((None, None, rdflib.namespace.DCTERMS.created)):
            created_lit = self._rmeta_graph.value(s, rdflib.namespace.RDF.value)
            if created_lit is None:
                msg = "Resource metadata {0} does not contain a creation date.".format(self.rmeta_path)
                raise GenericResourceMeta.ResourceMetaException(msg)
            try:
                self.creation_date = hs_date_to_datetime(str(created_lit))
            except HsDateException:
                try:
                    self.creation_date = hs_date_to_datetime_iso(str(created_lit))
                except HsDateException as e:
                    msg = "Unable to parse creation date {0}, error: {1}".format(str(created_lit),
                                                                                 str(e))
                    raise GenericResourceMeta.ResourceMetaException(msg)

        print("\t\tCreation date: {0}".format(str(self.creation_date)))

        # Get modification date
        for s, p, o in self._rmeta_graph.triples((None, None, rdflib.namespace.DCTERMS.modified)):
            modified_lit = self._rmeta_graph.value(s, rdflib.namespace.RDF.value)
            if modified_lit is None:
                msg = "Resource metadata {0} does not contain a modification date.".format(self.rmeta_path)
                raise GenericResourceMeta.ResourceMetaException(msg)
            try:
                self.modification_date = hs_date_to_datetime(str(modified_lit))
            except HsDateException:
                try:
                    self.modification_date = hs_date_to_datetime_iso(str(modified_lit))
                except HsDateException as e:
                    msg = "Unable to parse modification date {0}, error: {1}".format(str(modified_lit),
                                                                                     str(e))
                    raise GenericResourceMeta.ResourceMetaException(msg)

        print("\t\tModification date: {0}".format(str(self.modification_date)))

        # Get rights
        resource_rights = None
        for s, p, o in self._rmeta_graph.triples((None, rdflib.namespace.DC.rights, None)):
            resource_rights = GenericResourceMeta.ResourceRights()
            # License URI
            rights_uri = self._rmeta_graph.value(o, hsterms.URL)
            if rights_uri is None:
                msg = "Resource metadata {0} does not contain rights URI.".format(self.rmeta_path)
                raise GenericResourceMeta.ResourceMetaException(msg)
            resource_rights.uri = str(rights_uri)
            # Rights statement
            rights_stmt_lit = self._rmeta_graph.value(o, hsterms.rightsStatement)
            if rights_stmt_lit is None:
                msg = "Resource metadata {0} does not contain rights statement.".format(self.rmeta_path)
                raise GenericResourceMeta.ResourceMetaException(msg)
            resource_rights.statement = str(rights_stmt_lit)

        if resource_rights is None:
            msg = "Resource metadata {0} does not contain rights.".format(self.rmeta_path)
            raise GenericResourceMeta.ResourceMetaException(msg)

        self.rights = resource_rights

        print("\t\tRights: {0}".format(self.rights))

        # Get keywords
        if SAX_parse_results:
            # Use keywords from SAX parser
            self.keywords = list(SAX_parse_results.subjects)
        else:
            # Get keywords from RDF
            for s, p, o in self._rmeta_graph.triples((None, rdflib.namespace.DC.subject, None)):
                self.keywords.append(str(o))

        print("\t\tKeywords: {0}".format(str(self.keywords)))

        # Get language
        lang_lit = self._rmeta_graph.value(res_uri, rdflib.namespace.DC.language)
        if lang_lit is None:
            self.language = 'eng'
        else:
            self.language = str(lang_lit)

        print("\t\tLanguage: {0}".format(self.language))

        # Get coverage (box)
        for s, p, o in self._rmeta_graph.triples((None, None, rdflib.namespace.DCTERMS.box)):
            coverage_lit = self._rmeta_graph.value(s, rdflib.namespace.RDF.value)
            if coverage_lit is None:
                msg = "Coverage value not found for {0}.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            coverage = GenericResourceMeta.ResourceCoverageBox(str(coverage_lit))
            self.coverages.append(coverage)

        # Get coverage (point)
        for s, p, o in self._rmeta_graph.triples((None, None, rdflib.namespace.DCTERMS.point)):
            coverage_lit = self._rmeta_graph.value(s, rdflib.namespace.RDF.value)
            if coverage_lit is None:
                msg = "Coverage value not found for {0}.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            coverage = GenericResourceMeta.ResourceCoveragePoint(str(coverage_lit))
            self.coverages.append(coverage)

        # Get coverage (period)
        for s, p, o in self._rmeta_graph.triples((None, None, rdflib.namespace.DCTERMS.period)):
            coverage_lit = self._rmeta_graph.value(s, rdflib.namespace.RDF.value)
            if coverage_lit is None:
                msg = "Coverage value not found for {0}.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            coverage = GenericResourceMeta.ResourceCoveragePeriod(str(coverage_lit))
            self.coverages.append(coverage)

        print("\t\tCoverages: ")
        for c in self.coverages:
            print("\t\t\t{0}".format(str(c)))

        # Get relations
        for s, p, o in self._rmeta_graph.triples((None, rdflib.namespace.DC.relation, None)):
            for pred, obj in self._rmeta_graph.predicate_objects(o):
                relation = GenericResourceMeta.ResourceRelation(obj, pred)
                self.relations.append(relation)

        print("\t\tRelations: ")
        for r in self.relations:
            print("\t\t\t{0}".format(str(r)))

        # Get sources
        for s, p, o in self._rmeta_graph.triples((None, rdflib.namespace.DC.source, None)):
            for pred, obj in self._rmeta_graph.predicate_objects(o):
                source = GenericResourceMeta.ResourceSource(obj, pred)
                self.sources.append(source)

        print("\t\tSources: ")
        for r in self.sources:
            print("\t\t\t{0}".format(str(r)))

    def get_owner(self):
        """
        Return the creator with the lowest order.

        :return: ResourceCreator object representing the owner of the resource.
        """
        return self._creatorsHeap[0][1]

    def set_resource_modification_date(self, resource):
        if self.modification_date:
            res_modified_date = resource.metadata.dates.all().filter(type='modified')[0]
            res_modified_date.start_date = self.modification_date
            res_modified_date.save()
            # Update creation date representation provided by Mezzanine
            #   Get around calling save() on the resource, which will overwrite the modification
            #   date.
            BaseResource.objects.filter(id=resource.id).update(updated=self.modification_date)

    @transaction.atomic
    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: HydroShare resource instance
        """
        for c in self.get_creators():
            if isinstance(c, GenericResourceMeta.ResourceCreator):
                # Set creator metadata, from bag metadata, to be used in create or update as needed (see below)
                kwargs = {'order': c.order, 'name': c.name,
                          'organization': c.organization,
                          'email': c.email, 'address': c.address,
                          'phone': c.phone, 'homepage': c.homepage,
                          'researcherID': c.researcherID,
                          'researchGateID': c.researchGateID}
                if c.rel_uri:
                    # HydroShare user URIs are stored as relative not absolute URIs
                    kwargs['description'] = c.rel_uri
                else:
                    kwargs['description'] = None

                if self.owner_is_hs_user and c.order == 1:
                    # Use metadata from bag for owner if the owner is a HydroShare user
                    # (because the metadata were inheritted from the user profile when we
                    # called create_resource above)

                    # Find the owner in the creators metadata
                    owner_metadata = resource.metadata.creators.filter(order=1).first()
                    if owner_metadata is None:
                        msg = "Unable to find owner metadata for created resource {0}".format(resource.short_id)
                        raise GenericResourceMeta.ResourceMetaException(msg)
                    # Update owner's creator metadata entry with what came from the bag metadata
                    resource.metadata.update_element('Creator', owner_metadata.id, **kwargs)
                else:
                    # For the non-owner creators, just create new metadata elements for them.
                    resource.metadata.create_element('creator', **kwargs)
            else:
                msg = "Creators with type {0} are not supported"
                msg = msg.format(c.__class__.__name__)
                raise TypeError(msg)
        for c in self.contributors:
            # Add contributors
            if isinstance(c, GenericResourceMeta.ResourceContributor):
                kwargs = {'name': c.name, 'organization': c.organization,
                          'description': c.uri,
                          'email': c.email, 'address': c.address,
                          'phone': c.phone, 'homepage': c.homepage,
                          'researcherID': c.researcherID,
                          'researchGateID': c.researchGateID}
                resource.metadata.create_element('contributor', **kwargs)
            else:
                msg = "Contributor with type {0} are not supported"
                msg = msg.format(c.__class__.__name__)
                raise TypeError(msg)
        if self.abstract:
            resource.metadata.create_element('description', abstract=self.abstract)
        if self.rights:
            resource.metadata.update_element('rights', resource.metadata.rights.id,
                                             statement=self.rights.statement)
        if self.language:
            resource.metadata.update_element('language', resource.metadata.language.id,
                                             code=self.language)
        if self.creation_date:
            res_created_date = resource.metadata.dates.all().filter(type='created')[0]
            res_created_date.start_date = self.creation_date
            res_created_date.save()
            # Update creation date representation provided by Mezzanine
            resource.created = self.creation_date
            resource.save()
        if len(self.coverages) > 0:
            resource.metadata.coverages.all().delete()
            for c in self.coverages:
                kwargs = {}
                if isinstance(c, GenericResourceMeta.ResourceCoveragePeriod):
                    kwargs['type'] = 'period'
                    val = {}
                    val['name'] = c.name
                    # val['start'] = c.start_date.isoformat()
                    # val['end'] = c.end_date.isoformat()
                    # Cast temporal coverages to month/day/year format as this is how they are stored as strings
                    #  in the metadata tables.
                    val['start'] = c.start_date.strftime('%m/%d/%Y')
                    val['end'] = c.end_date.strftime('%m/%d/%Y')
                    val['scheme'] = c.scheme
                    kwargs['value'] = val
                    resource.metadata.create_element('coverage', **kwargs)
                elif isinstance(c, GenericResourceMeta.ResourceCoveragePoint):
                    kwargs['type'] = 'point'
                    val = {}
                    val['name'] = c.name
                    val['east'] = c.east
                    val['north'] = c.north
                    val['units'] = c.units
                    val['elevation'] = c.elevation
                    val['zunits'] = c.zunits
                    val['projection'] = c.projection
                    kwargs['value'] = val
                    resource.metadata.create_element('coverage', **kwargs)
                elif isinstance(c, GenericResourceMeta.ResourceCoverageBox):
                    kwargs['type'] = 'box'
                    val = {}
                    val['name'] = c.name
                    val['northlimit'] = c.northlimit
                    val['eastlimit'] = c.eastlimit
                    val['southlimit'] = c.southlimit
                    val['westlimit'] = c.westlimit
                    val['units'] = c.units
                    val['projection'] = c.projection
                    val['uplimit'] = c.uplimit
                    val['downlimit'] = c.downlimit
                    val['zunits'] = c.zunits
                    kwargs['value'] = val
                    resource.metadata.create_element('coverage', **kwargs)
                else:
                    msg = "Coverages with type {0} are not supported"
                    msg = msg.format(c.__class__.__name__)
                    raise TypeError(msg)
        if len(self.relations) > 0:
            resource.metadata.relations.all().delete()
            for r in self.relations:
                if isinstance(r, GenericResourceMeta.ResourceRelation):
                    kwargs = {'type': r.relationship_type,
                              'value': r.uri}
                    resource.metadata.create_element('relation', **kwargs)
                else:
                    msg = "Relations with type {0} are not supported"
                    msg = msg.format(r.__class__.__name__)
                    raise TypeError(msg)
        if len(self.sources) > 0:
            resource.metadata.sources.all().delete()
            for s in self.sources:
                if isinstance(s, GenericResourceMeta.ResourceSource):
                    kwargs = {'derived_from': s.uri}
                    resource.metadata.create_element('source', **kwargs)
                else:
                    msg = "Sources with type {0} are not supported"
                    msg = msg.format(s.__class__.__name__)
                    raise TypeError(msg)

        # Update modification date last
        self.set_resource_modification_date(resource)

    class ResourceContributor(object):

        def __init__(self):
            # HydroShare user ID of user specified by self.url (set by self.set_uri)
            self.id = None
            # Relative version of self.uri (applies only to HydroShare user URIs; set by self.set_uri)
            self.rel_uri = None

            self.uri = None
            self.name = None
            self.organization = None  # Optional
            self.email = None  # Optional
            self.address = None  # Optional
            self.phone = None  # Optional
            self.homepage = None  # Optional
            self.researcherID = None  # Optional
            self.researchGateID = None  # Optional

        def __str__(self):
            msg = "ResourceContributor {uri}, name: {name}, "
            msg += "email: {email}"
            msg = msg.format(uri=self.uri,
                             name=self.name,
                             email=self.email)
            return msg

        def __unicode__(self):
            return unicode(str(self))

        def set_uri(self, uri):
            """
            Set URI for contributor and parse user ID from URI

            :param uri: String representing the user URI (e.g. http://www.hydroshare.org/user/3/)

            :raise: GenericResourceMeta.ResourceMetaException if the user URI is malformed.
            """
            # Make sure this is a HydroShare user URI
            is_hs_user_uri = False
            try:
                validate_user_url(uri)
                is_hs_user_uri = True
            except ValidationError:
                pass

            if is_hs_user_uri:
                # Parse URI
                parsed_uri = urlparse.urlparse(uri)
                # Set rel_uri
                self.rel_uri = parsed_uri.path

                # Separate out the user ID for HydroShare users
                contributor_pk = os.path.basename(self.rel_uri.strip('/'))
                pk = None
                try:
                    pk = int(contributor_pk)
                except ValueError:
                    msg = "User ID {0} is not an integer. User URI was {1}."
                    raise GenericResourceMeta.ResourceMetaException(msg)

                assert(pk is not None)
                self.id = pk

            self.uri = uri


    class ResourceCreator(ResourceContributor):
        """

        Fields beyond URI are ignored for creators that are HydroShare users (i.e. have valid URI).
        """

        def __init__(self):
            super(GenericResourceMeta.ResourceCreator, self).__init__()
            self.order = None

        def __str__(self):
            msg = "ResourceCreator {uri}, name: {name}, "
            msg += "order: {order}, email: {email}"
            msg = msg.format(uri=self.uri,
                             name=self.name,
                             order=self.order,
                             email=self.email)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class ResourceRights(object):

        def __init__(self):
            self.uri = None
            self.statement = None

        def __str__(self):
            msg = "ResourceRights {uri}, statement: {statement}"
            msg = msg.format(uri=self.uri,
                             statement=self.statement)
            return msg

        def __unicode__(self):
            return unicode(str(self))

    class ResourceCoverage(object):
        pass

    class ResourceCoveragePeriod(ResourceCoverage):
        """
        Time period resource coverage.
        """

        def __str__(self):
            msg = "ResourceCoveragePeriod start_date: {start_date}, "
            msg += "end_date: {end_date}, scheme: {scheme}"
            msg = msg.format(start_date=self.start_date, end_date=self.end_date,
                             scheme=self.scheme)
            return msg

        def __unicode__(self):
            return unicode(str(self))

        def __init__(self, value_str):
            self.name = None  # Optional
            self.start_date = None
            self.end_date = None
            self.scheme = None

            kvp = value_str.split(';')
            for pair in kvp:
                (key, value) = pair.split('=')
                key = key.strip()
                value = value.strip()
                if key == 'start':
                    try:
                        self.start_date = hs_date_to_datetime_iso(value)
                    except Exception as e:
                        try:
                            self.start_date = hs_date_to_datetime_notz(value)
                        except Exception as e:
                            msg = "Unable to parse start date {0}, error: {1}".format(value,
                                                                                      str(e))
                            raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'end':
                    try:
                        self.end_date = hs_date_to_datetime_iso(value)
                    except Exception as e:
                        try:
                            self.end_date = hs_date_to_datetime_notz(value)
                        except Exception as e:
                            msg = "Unable to parse end date {0}, error: {1}".format(value,
                                                                                    str(e))
                            raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'scheme':
                    self.scheme = value
                elif key == 'name':
                    self.name = value

            if self.start_date is None:
                msg = "Period coverage '{0}' does not contain start date.".format(value_str)
                raise GenericResourceMeta.ResourceMetaException(msg)
            if self.end_date is None:
                msg = "Period coverage '{0}' does not contain end date.".format(value_str)
                raise GenericResourceMeta.ResourceMetaException(msg)
            if self.scheme is None:
                msg = "Period coverage '{0}' does not contain scheme.".format(value_str)
                raise GenericResourceMeta.ResourceMetaException(msg)

    class ResourceCoveragePoint(ResourceCoverage):
        """
        Point geographic resource coverage.
        """

        def __str__(self):
            msg = "ResourceCoveragePoint north: {north}, "
            msg += "east: {east}, units: {units}"
            msg = msg.format(north=self.north, east=self.east,
                             units=self.units)
            return msg

        def __unicode__(self):
            return unicode(str(self))

        def __init__(self, value_str):
            self.name = None  # Optional
            self.east = None
            self.north = None
            self.units = None
            self.elevation = None  # Optional
            self.zunits = None  # Optional
            self.projection = None  # Optional

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
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'north':
                    try:
                        self.north = float(value)
                    except Exception as e:
                        msg = "Unable to parse northing {0}, error: {1}".format(value,
                                                                                str(e))
                        raise GenericResourceMeta.ResourceMetaException(msg)
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
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'zunits':
                    self.zunits = value

            if self.east is None:
                msg = "Point coverage '{0}' does not contain an easting.".format(value_str)
                raise GenericResourceMeta.ResourceMetaException(msg)
            if self.north is None:
                msg = "Point coverage '{0}' does not contain a northing.".format(value_str)
                raise GenericResourceMeta.ResourceMetaException(msg)
            if self.units is None:
                msg = "Point coverage '{0}' does not contain units information.".format(value_str)
                raise GenericResourceMeta.ResourceMetaException(msg)

    class ResourceCoverageBox(ResourceCoverage):
        """
        Box geographic resource coverage.
        """

        def __str__(self):
            msg = "ResourceCoverageBox northlimit: {northlimit}, "
            msg += "eastlimit: {eastlimit}, southlimit: {southlimit}, "
            msg += "westlimit: {westlimit}, units: {units}"
            msg = msg.format(northlimit=self.northlimit, eastlimit=self.eastlimit,
                             southlimit=self.southlimit, westlimit=self.westlimit,
                             units=self.units)
            return msg

        def __unicode__(self):
            return unicode(str(self))

        def __init__(self, value_str):
            self.name = None  # Optional
            self.northlimit = None
            self.eastlimit = None
            self.southlimit = None
            self.westlimit = None
            self.units = None
            self.projection = None  # Optional
            self.uplimit = None  # Optional
            self.downlimit = None  # Optional
            self.zunits = None  # Only present if uplimit or downlimit is present

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
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'northlimit':
                    try:
                        self.northlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse north limit {0}, error: {1}".format(value,
                                                                                   str(e))
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'southlimit':
                    try:
                        self.southlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse south limit {0}, error: {1}".format(value,
                                                                                   str(e))
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'westlimit':
                    try:
                        self.westlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse west limit {0}, error: {1}".format(value,
                                                                                  str(e))
                        raise GenericResourceMeta.ResourceMetaException(msg)
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
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'downlimit':
                    try:
                        self.downlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse downlimit {0}, error: {1}".format(value,
                                                                                 str(e))
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'zunits':
                    self.zunits = value

            if self.zunits is None and (self.uplimit is not None or self.downlimit is not None):
                msg = "Point coverage '{0}' contains uplimit or downlimit but "
                msg += "does not contain zunits."
                msg = msg.format(value_str)
                raise GenericResourceMeta.ResourceMetaException(msg)

    class ResourceRelation(object):
        KNOWN_TYPES = {'isParentOf', 'isExecutedBy', 'isHostedBy', 'isCopiedFrom', 'isCreatedBy',
                       'isPartOf', 'isVersionOf', 'isDataFor', 'cites'}

        def __str__(self):
            msg = "{classname} {relationship_type}: {uri}"
            msg = msg.format(classname=type(self).__name__,
                             relationship_type=self.relationship_type,
                             uri=self.uri)
            return msg

        def __unicode__(self):
            return unicode(str(self))

        def __init__(self, uri, relationship_uri):
            self.uri = None
            self.relationship_type = None

            relationship_type = os.path.basename(relationship_uri)
            if relationship_type not in self.KNOWN_TYPES:
                msg = "Relationship uri {0} is not known.".format(relationship_uri)
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.uri = uri
            self.relationship_type = relationship_type

    class ResourceSource(ResourceRelation):
        KNOWN_TYPES = {'isDerivedFrom'}

    class ResourceMetaException(Exception):
        pass


class GenericResourceSAXHandler(xml.sax.ContentHandler):
    def __init__(self):
        xml.sax.ContentHandler.__init__(self)

        # Content
        self.subjects = []
        self.contributors = []

        # State variables
        self._get_subject = False
        self._subject = None
        self._get_contributor = False
        self._get_contributor_details = False
        self._get_contributor_name = False
        self._contributor_name = None
        self._get_contributor_organization = False
        self._contributor_organization = None
        self._get_contributor_email = False
        self._contributor_email = None
        self._get_contributor_address = False
        self._contributor_address = None

    def characters(self, content):
        if self._get_subject:
            self._subject.append(content)

        elif self._get_contributor_name:
            if len(self.contributors) < 1:
                msg = "Error: haven't yet encountered contributor, "
                msg += "yet trying to store contributor name."
                raise xml.sax.SAXException(msg)
            self._contributor_name.append(content)

        elif self._get_contributor_organization:
            if len(self.contributors) < 1:
                msg = "Error: haven't yet encountered contributor, "
                msg += "yet trying to store contributor organization."
                raise xml.sax.SAXException(msg)
            self._contributor_organization.append(content)

        elif self._get_contributor_email:
            if len(self.contributors) < 1:
                msg = "Error: haven't yet encountered contributor, "
                msg += "yet trying to store contributor email."
                raise xml.sax.SAXException(msg)
            self._contributor_email.append(content)

        elif self._get_contributor_address:
            if len(self.contributors) < 1:
                msg = "Error: haven't yet encountered contributor, "
                msg += "yet trying to store contributor address."
                raise xml.sax.SAXException(msg)
            self._contributor_address.append(content)

    def startElement(self, name, attrs):
        if name == 'dc:subject':
            if self._get_subject:
                raise xml.sax.SAXException("Error: nested dc:subject elements.")
            self._get_subject = True
            self._subject = []

        elif name == 'dc:contributor':
            if self._get_contributor:
                raise xml.sax.SAXException("Error: nested dc:contributor elements.")
            self._get_contributor = True

        elif name == 'rdf:Description':
            if self._get_contributor:
                if self._get_contributor_details:
                    msg = "Error: nested rdf:Description elements within dc:contributor element."
                    raise xml.sax.SAXException(msg)
                # Create new contributor
                contributor = GenericResourceMeta.ResourceContributor()
                if attrs.has_key('rdf:about'):
                    contributor.set_uri(attrs.getValue('rdf:about'))
                self.contributors.append(contributor)
                self._get_contributor_details = True

        elif name == 'hsterms:name':
            if self._get_contributor_details:
                if self._get_contributor_name:
                    raise xml.sax.SAXException("Error: nested hsterms:name elements within dc:contributor.")
                self._get_contributor_name = True
                self._contributor_name = []

        elif name == 'hsterms:organization':
            if self._get_contributor_details:
                if self._get_contributor_organization:
                    raise xml.sax.SAXException("Error: nested hsterms:organization elements within dc:contributor.")
                self._get_contributor_organization = True
                self._contributor_organization = []

        elif name == 'hsterms:email':
            if self._get_contributor_details:
                if self._get_contributor_email:
                    raise xml.sax.SAXException("Error: nested hsterms:email elements within dc:contributor.")
                self._get_contributor_email = True
                self._contributor_email = []

        elif name == 'hsterms:address':
            if self._get_contributor_details:
                if self._get_contributor_address:
                    raise xml.sax.SAXException("Error: nested hsterms:address elements within dc:contributor.")
                self._get_contributor_address = True
                self._contributor_address = []

        elif name == 'hsterms:phone':
            if self._get_contributor_details:
                if not attrs.has_key('rdf:resource'):
                    msg = "Error: hsterms:phone within dc:contributor element has no phone number."
                    raise xml.sax.SAXException(msg)
                phone_raw = str(attrs.getValue('rdf:resource')).split(':')
                if len(phone_raw) > 1:
                    self.contributors[-1].phone = phone_raw[1]
                else:
                    self.contributors[-1].phone = phone_raw[0]

    def endElement(self, name):
        if name == 'dc:subject':
            if not self._get_subject:
                msg = "Error: close dc:subject tag without corresponding open tag."
                raise xml.sax.SAXException(msg)
            self.subjects.append("".join(self._subject))
            self._subject = None
            self._get_subject = False

        elif name == 'dc:contributor':
            if not self._get_contributor:
                msg = "Error: close dc:contributor tag without corresponding open tag."
                raise xml.sax.SAXException(msg)
            self._get_contributor = False

        elif name == 'rdf:Description':
            if self._get_contributor:
                if not self._get_contributor_details:
                    msg = "Error: close rdf:Description tag without corresponding open tag "
                    msg += "within dc:contributor."
                    raise xml.sax.SAXException(msg)
                self._get_contributor_details = False

        elif name == 'hsterms:name':
            if self._get_contributor_details:
                if not self._get_contributor_name:
                    msg = "Error: close hsterms:name tag without corresponding open tag "
                    msg += "within dc:contributor."
                    raise xml.sax.SAXException(msg)
                self.contributors[-1].name = "".join(self._contributor_name)
                self._contributor_name = None
                self._get_contributor_name = False

        elif name == 'hsterms:organization':
            if self._get_contributor_details:
                if not self._get_contributor_organization:
                    msg = "Error: close hsterms:organization tag without corresponding open tag "
                    msg += "within dc:contributor."
                    raise xml.sax.SAXException(msg)
                self.contributors[-1].organization = "".join(self._contributor_organization)
                self._contributor_organization = None
                self._get_contributor_organization = False

        elif name == 'hsterms:email':
            if self._get_contributor_details:
                if not self._get_contributor_email:
                    msg = "Error: close hsterms:email tag without corresponding open tag "
                    msg += "within dc:contributor."
                    raise xml.sax.SAXException(msg)
                self.contributors[-1].email = "".join(self._contributor_email)
                self._contributor_email = None
                self._get_contributor_email = False

        elif name == 'hsterms:address':
            if self._get_contributor_details:
                if not self._get_contributor_address:
                    msg = "Error: close hsterms:address tag without corresponding open tag "
                    msg += "within dc:contributor."
                    raise xml.sax.SAXException(msg)
                self.contributors[-1].address = "".join(self._contributor_address)
                self._contributor_address = None
                self._get_contributor_address = False
