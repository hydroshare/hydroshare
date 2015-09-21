import os, sys

import rdflib
from rdflib import URIRef
from rdflib import Graph

from django.core.files.uploadedfile import UploadedFile
from django.db import IntegrityError

from hs_core.hydroshare.utils import get_resource_types
from hs_core.hydroshare.date_util import hs_date_to_datetime, hs_date_to_datetime_iso

from hs_core.hydroshare.utils import resource_pre_create_actions
from hs_core.hydroshare.utils import ResourceFileSizeException, ResourceFileValidationException
from hs_core.hydroshare import create_resource
from hs_core.models import BaseResource


class HsSerializationException(Exception):
    pass


class HsDeserializationException(HsSerializationException):
    pass


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
    :return:
    :raises: HsDeserializationException if an error occurred.
    """
    # Get resource metadata
    resource_files = None
    try:
        rm = GenericResourceMeta.read_metadata_from_resource_bag(bag_content_path)
        res_files = [os.path.join(bag_content_path, f) for f in rm.files]
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
        owner_uri = rm.get_owner_uri().strip()
        owner_pk = os.path.basename(owner_uri)
        # Override for testing
        owner_pk = 1

        resource_id = None
        if preserve_uuid:
            resource_id = rm.id

        kwargs = {}
        # if rm.creation_date:
        #     # This has no effect
        #     kwargs['created'] = rm.creation_date
        resource = create_resource(resource_type=rm.res_type,
                                   owner=owner_pk,
                                   title=rm.title,
                                   keywords=rm.keywords,
                                   metadata=metadata,
                                   files=resource_files,
                                   content=rm.title,
                                   short_id=resource_id,
                                   **kwargs)
    except Exception as ex:
        raise HsDeserializationException(ex.message)

    # Add additional metadata
    assert(resource is not None)
    rm.write_metadata_to_resource(resource)


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

    bag_content_path = None
    root_uri = None
    res_meta_path = None
    _rmeta_graph = None

    def __init__(self):
        pass

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
                mod_ser_name = "{root}.serialization".format(root=rt_root)
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
        if not os.path.isfile(rmap_path):
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
        rmeta_path = os.path.join(self.bag_content_path, self.res_meta_path)
        if not os.path.isfile(rmeta_path):
            raise GenericResourceMeta.ResourceMetaException("Resource metadata {0} does not exist".format(rmeta_path))
        if not os.access(rmeta_path, os.R_OK):
            raise GenericResourceMeta.ResourceMetaException("Unable to read resource metadata {0}".format(rmeta_path))

        self._rmeta_graph = Graph()
        self._rmeta_graph.parse(rmeta_path)

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')
        res_uri = URIRef(self.root_uri)

        # Make sure title matches that from resource map
        title_lit = self._rmeta_graph.value(res_uri, rdflib.namespace.DC.title)
        if title_lit is not None:
            title = str(title_lit)
            if title != self.title:
                msg = "Title from resource metadata {0} "
                msg += "does not match title from resource map {1}".format(title, self.title)
                raise GenericResourceMeta.ResourceMetaException(msg)

        # Get abstract
        for s, p, o in self._rmeta_graph.triples((None, rdflib.namespace.DCTERMS.abstract, None)):
            self.abstract = o
        if self.abstract:
            print("\t\tAbstract: {0}".format(self.abstract))

        # Get creators
        for s, p, o in self._rmeta_graph.triples((None, rdflib.namespace.DC.creator, None)):
            creator = GenericResourceMeta.ResourceCreator()
            creator.uri = o
            # Get name
            name_lit = self._rmeta_graph.value(o, hsterms.name)
            if name_lit is None:
                msg = "Name for creator {0} was not found.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            creator.name = str(name_lit)
            # Get order
            order_lit = self._rmeta_graph.value(o, hsterms.creatorOrder)
            if order_lit is None:
                msg = "Order for creator {0} was not found.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            creator.order = int(str(order_lit))
            # Get email
            email_lit = self._rmeta_graph.value(o, hsterms.email)
            if email_lit is None:
                msg = "E-mail for creator {0} was not found.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            creator.email = str(email_lit)

            self.creators.append(creator)

        for c in self.creators:
            print("\t\tCreator: {0}".format(str(c)))

        # Get contributors
        for s, p, o in self._rmeta_graph.triples((None, rdflib.namespace.DC.contributor, None)):
            contributor = GenericResourceMeta.ResourceContributor()
            contributor.uri = o
            # Get name
            name_lit = self._rmeta_graph.value(o, hsterms.name)
            if name_lit is None:
                msg = "Name for contributor {0} was not found.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            contributor.name = str(name_lit)
            # Get email
            email_lit = self._rmeta_graph.value(o, hsterms.email)
            if email_lit is None:
                msg = "E-mail for contributor {0} was not found.".format(o)
                raise GenericResourceMeta.ResourceMetaException(msg)
            contributor.email = str(email_lit)

            self.contributors.append(contributor)

        for c in self.contributors:
            print("\t\tContributor: {0}".format(str(c)))

        # Get creation date
        for s, p, o in self._rmeta_graph.triples((None, None, rdflib.namespace.DCTERMS.created)):
            created_lit = self._rmeta_graph.value(s, rdflib.namespace.RDF.value)
            if created_lit is None:
                msg = "Resource metadata {0} does not contain a creation date.".format(rmeta_path)
                raise GenericResourceMeta.ResourceMetaException(msg)
            try:
                self.creation_date = hs_date_to_datetime(str(created_lit))
            except Exception as e:
                msg = "Unable to parse creation date {0}, error: {1}".format(str(created_lit),
                                                                             str(e))
                raise GenericResourceMeta.ResourceMetaException(msg)

        print("\t\tCreation date: {0}".format(str(self.creation_date)))

        # Get modification date
        for s, p, o in self._rmeta_graph.triples((None, None, rdflib.namespace.DCTERMS.modified)):
            modified_lit = self._rmeta_graph.value(s, rdflib.namespace.RDF.value)
            if modified_lit is None:
                msg = "Resource metadata {0} does not contain a modification date.".format(rmeta_path)
                raise GenericResourceMeta.ResourceMetaException(msg)
            try:
                self.modification_date = hs_date_to_datetime(str(modified_lit))
            except Exception as e:
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
                msg = "Resource metadata {0} does not contain rights URI.".format(rmeta_path)
                raise GenericResourceMeta.ResourceMetaException(msg)
            resource_rights.uri = str(rights_uri)
            # Rights statement
            rights_stmt_lit = self._rmeta_graph.value(o, hsterms.rightsStatement)
            if rights_stmt_lit is None:
                msg = "Resource metadata {0} does not contain rights statement.".format(rmeta_path)
                raise GenericResourceMeta.ResourceMetaException(msg)
            resource_rights.statement = str(rights_stmt_lit)

        if resource_rights is None:
            msg = "Resource metadata {0} does not contain rights.".format(rmeta_path)
            raise GenericResourceMeta.ResourceMetaException(msg)

        self.rights = resource_rights

        print("\t\tRights: {0}".format(self.rights))

        # Get keywords
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

    def get_owner_uri(self):
        """
        Return the creator with the lowest order.

        :return: String representing the URI of the owner of the resource.
        """
        min_order = sys.maxint
        owner_uri = None
        for c in self.creators:
            if c.order < min_order:
                min_order = c.order
                owner_uri = c.uri
                break
        return owner_uri

    def write_metadata_to_resource(self, resource):
        """
        Write metadata to resource

        :param resource: HydroShare resource instance
        """
        if self.abstract:
            resource.metadata.create_element('description', abstract=self.abstract)
        if self.rights:
            try:
                resource.metadata.create_element('rights', statement=self.rights.statement)
            except IntegrityError:
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
        if self.modification_date:
            res_modified_date = resource.metadata.dates.all().filter(type='modified')[0]
            res_modified_date.start_date = self.modification_date
            res_modified_date.save()
            # Update creation date representation provided by Mezzanine
            #   Get around calling save() on the resource, which will overwrite the modification
            #   date.
            BaseResource.objects.filter(id=resource.id).update(updated=self.modification_date)

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
        name = None  # Optional
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
                        raise GenericResourceMeta.ResourceMetaException(msg)
                elif key == 'end':
                    try:
                        self.end_date = hs_date_to_datetime_iso(value)
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
        name = None  # Optional
        east = None
        north = None
        units = None
        elevation = None  # Optional
        zunits = None  # Optional
        projection = None  # Optional

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
        name = None  # Optional
        northlimit = None
        eastlimit = None
        southlimit = None
        westlimit = None
        units = None
        projection = None  # Optional
        uplimit = None  # Optional
        downlimit = None  # Optional
        zunits = None  # Only present if uplimit or downlimit is present

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
        KNOWN_TYPES = {'isParentOf', 'isChildOf', 'isMemberOf', 'isDerivedFrom',
                       'hasBibliographicInfoIn', 'isRevisionHistoryFor',
                       'isCriticalReviewOf', 'isOverviewOf', 'isContentRatingFor',
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
                raise GenericResourceMeta.ResourceMetaException(msg)
            self.uri = uri
            self.relationship_type = relationship_type

    class ResourceSource(ResourceRelation):
        KNOWN_TYPES = {'isDerivedFrom'}

    class ResourceMetaException(Exception):
        pass
