import os

import rdflib
from rdflib import URIRef
from rdflib import Graph

from hs_core.hydroshare.date_util import hs_date_to_datetime, hs_date_to_datetime_iso


class ResourceMeta(object):
    """
    Lightweight class for representing core metadata of Resources, including the
     ability to read metadata from an un-compressed BagIt archive.
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
    _res_meta_path = None

    def __init__(self):
        pass

    def read_metadata_from_bag(self, bag_content_path):
        self.bag_content_path = bag_content_path
        self._read_resource_map()
        self._read_resource_metadata()

    def _read_resource_map(self):
        """
        Read resource metadata out of the resourcemap.xml of the exploded bag path
        :raises: ResourceMetaException if metadata cannot be found or do not appear
         as expected.
        """
        rmap_path = os.path.join(self.bag_content_path, 'data', 'resourcemap.xml')
        if not os.path.isfile(rmap_path):
            raise ResourceMeta.ResourceMetaException("Resource map {0} does not exist".format(rmap_path))
        if not os.access(rmap_path, os.R_OK):
            raise ResourceMeta.ResourceMetaException("Unable to read resource map {0}".format(rmap_path))

        g = Graph()
        g.parse(rmap_path)
        # Get resource ID
        for s, p, o in g.triples((None, None, None)):
            if s.endswith("resourcemap.xml") and p == rdflib.namespace.DC.identifier:
                self.id = o
        if self.id is None:
            msg = "Unable to determine resource ID from resource map {0}".format(rmap_path)
            raise ResourceMeta.ResourceMetaException(msg)
        print("Resource ID is {0}".format(self.id))

        # Build URI reference for #aggregation section of resource map
        res_root_uri = "http://www.hydroshare.org/resource/{res_id}".format(res_id=self.id)
        self.root_uri = res_root_uri
        res_agg_subj = "{res_root_url}/data/resourcemap.xml#aggregation".format(res_root_url=res_root_uri)
        res_agg = URIRef(res_agg_subj)

        # Get resource type
        type_lit = g.value(res_agg, rdflib.namespace.DCTERMS.type)
        if type_lit is None:
            raise ResourceMeta.ResourceMetaException("No resource type found in resource map {0}".format(rmap_path))
        self.res_type = str(type_lit)
        print("\tType is {0}".format(self.res_type))

        # Get resource title
        title_lit = g.value(res_agg, rdflib.namespace.DC.title)
        if title_lit is None:
            raise ResourceMeta.ResourceMetaException("No resource title found in resource map {0}".format(rmap_path))
        self.title = str(title_lit)
        print("\tTitle is {0}".format(self.title))

        # Get list of files in resource
        res_root_uri_withslash = res_root_uri + '/'
        res_meta_path = None
        ore = rdflib.namespace.Namespace('http://www.openarchives.org/ore/terms/')
        for s, p, o in g.triples((res_agg, ore.aggregates, None)):
            if o.endswith('resourcemetadata.xml'):
                if res_meta_path is not None and o != res_meta_path:
                    msg = "More than one resource metadata URI found. "
                    msg += "(first: {first}, second: {second}".format(first=res_meta_path,
                                                                      second=o)
                    raise ResourceMeta.ResourceMetaException(msg)
                res_meta_path = o.split(res_root_uri_withslash)[1]
                continue

            self.files.append(o.split(res_root_uri_withslash)[1])

        if res_meta_path is None:
            raise ResourceMeta.ResourceMetaException("No resource metadata found in resource map {0}".format(rmap_path))

        print("\tResource metadata path {0}".format(res_meta_path))

        for uri in self.files:
            print("\tContents: {0}".format(uri))

        self._res_meta_path = res_meta_path

    def _read_resource_metadata(self):
        """
        Read resource metadata out of the resourcemetadata.xml of the exploded bag path

        :return: None
        """
        rmeta_path = os.path.join(self.bag_content_path, self._res_meta_path)
        if not os.path.isfile(rmeta_path):
            raise ResourceMeta.ResourceMetaException("Resource metadata {0} does not exist".format(rmeta_path))
        if not os.access(rmeta_path, os.R_OK):
            raise ResourceMeta.ResourceMetaException("Unable to read resource metadata {0}".format(rmeta_path))

        g = Graph()
        g.parse(rmeta_path)

        hsterms = rdflib.namespace.Namespace('http://hydroshare.org/terms/')
        res_uri = URIRef(self.root_uri)

        # Make sure title matches that from resource map
        title_lit = g.value(res_uri, rdflib.namespace.DC.title)
        if title_lit is not None:
            title = str(title_lit)
            if title != self.title:
                msg = "Title from resource metadata {0} "
                msg += "does not match title from resource map {1}".format(title, self.title)
                raise ResourceMeta.ResourceMetaException(msg)

        # Get abstract
        for s, p, o in g.triples((None, rdflib.namespace.DCTERMS.abstract, None)):
            self.abstract = o
        if self.abstract:
            print("\t\tAbstract: {0}".format(self.abstract))

        # Get creators
        for s, p, o in g.triples((None, rdflib.namespace.DC.creator, None)):
            creator = ResourceMeta.ResourceCreator()
            creator.uri = o
            # Get name
            name_lit = g.value(o, hsterms.name)
            if name_lit is None:
                msg = "Name for creator {0} was not found.".format(o)
                raise ResourceMeta.ResourceMetaException(msg)
            creator.name = str(name_lit)
            # Get order
            order_lit = g.value(o, hsterms.creatorOrder)
            if order_lit is None:
                msg = "Order for creator {0} was not found.".format(o)
                raise ResourceMeta.ResourceMetaException(msg)
            creator.order = str(order_lit)
            # Get email
            email_lit = g.value(o, hsterms.email)
            if email_lit is None:
                msg = "E-mail for creator {0} was not found.".format(o)
                raise ResourceMeta.ResourceMetaException(msg)
            creator.email = str(email_lit)

            self.creators.append(creator)

        for c in self.creators:
            print("\t\tCreator: {0}".format(str(c)))

        # Get contributors
        for s, p, o in g.triples((None, rdflib.namespace.DC.contributor, None)):
            contributor = ResourceMeta.ResourceContributor()
            contributor.uri = o
            # Get name
            name_lit = g.value(o, hsterms.name)
            if name_lit is None:
                msg = "Name for contributor {0} was not found.".format(o)
                raise ResourceMeta.ResourceMetaException(msg)
            contributor.name = str(name_lit)
            # Get email
            email_lit = g.value(o, hsterms.email)
            if email_lit is None:
                msg = "E-mail for contributor {0} was not found.".format(o)
                raise ResourceMeta.ResourceMetaException(msg)
            contributor.email = str(email_lit)

            self.contributors.append(contributor)

        for c in self.contributors:
            print("\t\tContributor: {0}".format(str(c)))

        # Get creation date
        for s, p, o in g.triples((None, None, rdflib.namespace.DCTERMS.created)):
            created_lit = g.value(s, rdflib.namespace.RDF.value)
            if created_lit is None:
                msg = "Resource metadata {0} does not contain a creation date.".format(rmeta_path)
                raise ResourceMeta.ResourceMetaException(msg)
            try:
                self.creation_date = hs_date_to_datetime(str(created_lit))
            except Exception as e:
                msg = "Unable to parse creation date {0}, error: {1}".format(str(created_lit),
                                                                             str(e))
                raise ResourceMeta.ResourceMetaException(msg)

        print("\t\tCreation date: {0}".format(str(self.creation_date)))

        # Get modification date
        for s, p, o in g.triples((None, None, rdflib.namespace.DCTERMS.modified)):
            modified_lit = g.value(s, rdflib.namespace.RDF.value)
            if modified_lit is None:
                msg = "Resource metadata {0} does not contain a modification date.".format(rmeta_path)
                raise ResourceMeta.ResourceMetaException(msg)
            try:
                self.modification_date = hs_date_to_datetime(str(modified_lit))
            except Exception as e:
                msg = "Unable to parse modification date {0}, error: {1}".format(str(modified_lit),
                                                                                 str(e))
                raise ResourceMeta.ResourceMetaException(msg)

        print("\t\tModification date: {0}".format(str(self.modification_date)))

        # Get rights
        resource_rights = None
        for s, p, o in g.triples((None, rdflib.namespace.DC.rights, None)):
            resource_rights = ResourceMeta.ResourceRights()
            # License URI
            rights_uri = g.value(o, hsterms.URL)
            if rights_uri is None:
                msg = "Resource metadata {0} does not contain rights URI.".format(rmeta_path)
                raise ResourceMeta.ResourceMetaException(msg)
            resource_rights.uri = str(rights_uri)
            # Rights statement
            rights_stmt_lit = g.value(o, hsterms.rightsStatement)
            if rights_stmt_lit is None:
                msg = "Resource metadata {0} does not contain rights statement.".format(rmeta_path)
                raise ResourceMeta.ResourceMetaException(msg)
            resource_rights.statement = str(rights_stmt_lit)

        if resource_rights is None:
            msg = "Resource metadata {0} does not contain rights.".format(rmeta_path)
            raise ResourceMeta.ResourceMetaException(msg)

        self.rights = resource_rights

        print("\t\tRights: {0}".format(self.rights))

        # Get keywords
        for s, p, o in g.triples((None, rdflib.namespace.DC.subject, None)):
            self.keywords.append(str(o))

        print("\t\tKeywords: {0}".format(str(self.keywords)))

        # Get language
        lang_lit = g.value(res_uri, rdflib.namespace.DC.language)
        if lang_lit is None:
            self.language = 'eng'
        else:
            self.language = str(lang_lit)

        print("\t\tLanguage: {0}".format(self.language))

        # Get coverage (box)
        for s, p, o in g.triples((None, None, rdflib.namespace.DCTERMS.box)):
            coverage_lit = g.value(s, rdflib.namespace.RDF.value)
            if coverage_lit is None:
                msg = "Coverage value not found for {0}.".format(o)
                raise ResourceMeta.ResourceMetaException(msg)
            coverage = ResourceMeta.ResourceCoverageBox(str(coverage_lit))
            self.coverages.append(coverage)

        # Get coverage (point)
        for s, p, o in g.triples((None, None, rdflib.namespace.DCTERMS.point)):
            coverage_lit = g.value(s, rdflib.namespace.RDF.value)
            if coverage_lit is None:
                msg = "Coverage value not found for {0}.".format(o)
                raise ResourceMeta.ResourceMetaException(msg)
            coverage = ResourceMeta.ResourceCoveragePoint(str(coverage_lit))
            self.coverages.append(coverage)

        # Get coverage (period)
        for s, p, o in g.triples((None, None, rdflib.namespace.DCTERMS.period)):
            coverage_lit = g.value(s, rdflib.namespace.RDF.value)
            if coverage_lit is None:
                msg = "Coverage value not found for {0}.".format(o)
                raise ResourceMeta.ResourceMetaException(msg)
            coverage = ResourceMeta.ResourceCoveragePeriod(str(coverage_lit))
            self.coverages.append(coverage)

        print("\t\tCoverages: ")
        for c in self.coverages:
            print("\t\t\t{0}".format(str(c)))

        # Get relations
        for s, p, o in g.triples((None, rdflib.namespace.DC.relation, None)):
            for pred, obj in g.predicate_objects(o):
                relation = ResourceMeta.ResourceRelation(obj, pred)
                self.relations.append(relation)

        print("\t\tRelations: ")
        for r in self.relations:
            print("\t\t\t{0}".format(str(r)))

        # Get sources
        for s, p, o in g.triples((None, rdflib.namespace.DC.source, None)):
            for pred, obj in g.predicate_objects(o):
                source = ResourceMeta.ResourceSource(obj, pred)
                self.sources.append(source)

        print("\t\tSources: ")
        for r in self.sources:
            print("\t\t\t{0}".format(str(r)))

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
                        raise ResourceMeta.ResourceMetaException(msg)
                elif key == 'end':
                    try:
                        self.end_date = hs_date_to_datetime_iso(value)
                    except Exception as e:
                        msg = "Unable to parse end date {0}, error: {1}".format(value,
                                                                                str(e))
                        raise ResourceMeta.ResourceMetaException(msg)
                elif key == 'scheme':
                    self.scheme = value
                elif key == 'name':
                    self.name = value

            if self.start_date is None:
                msg = "Period coverage '{0}' does not contain start date.".format(value_str)
                raise ResourceMeta.ResourceMetaException(msg)
            if self.end_date is None:
                msg = "Period coverage '{0}' does not contain end date.".format(value_str)
                raise ResourceMeta.ResourceMetaException(msg)
            if self.scheme is None:
                msg = "Period coverage '{0}' does not contain scheme.".format(value_str)
                raise ResourceMeta.ResourceMetaException(msg)

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
                        raise ResourceMeta.ResourceMetaException(msg)
                elif key == 'north':
                    try:
                        self.north = float(value)
                    except Exception as e:
                        msg = "Unable to parse northing {0}, error: {1}".format(value,
                                                                                str(e))
                        raise ResourceMeta.ResourceMetaException(msg)
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
                        raise ResourceMeta.ResourceMetaException(msg)
                elif key == 'zunits':
                    self.zunits = value

            if self.east is None:
                msg = "Point coverage '{0}' does not contain an easting.".format(value_str)
                raise ResourceMeta.ResourceMetaException(msg)
            if self.north is None:
                msg = "Point coverage '{0}' does not contain a northing.".format(value_str)
                raise ResourceMeta.ResourceMetaException(msg)
            if self.units is None:
                msg = "Point coverage '{0}' does not contain units information.".format(value_str)
                raise ResourceMeta.ResourceMetaException(msg)

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
                        raise ResourceMeta.ResourceMetaException(msg)
                elif key == 'northlimit':
                    try:
                        self.northlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse north limit {0}, error: {1}".format(value,
                                                                                   str(e))
                        raise ResourceMeta.ResourceMetaException(msg)
                elif key == 'southlimit':
                    try:
                        self.southlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse south limit {0}, error: {1}".format(value,
                                                                                   str(e))
                        raise ResourceMeta.ResourceMetaException(msg)
                elif key == 'westlimit':
                    try:
                        self.westlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse west limit {0}, error: {1}".format(value,
                                                                                  str(e))
                        raise ResourceMeta.ResourceMetaException(msg)
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
                        raise ResourceMeta.ResourceMetaException(msg)
                elif key == 'downlimit':
                    try:
                        self.downlimit = float(value)
                    except Exception as e:
                        msg = "Unable to parse downlimit {0}, error: {1}".format(value,
                                                                                 str(e))
                        raise ResourceMeta.ResourceMetaException(msg)
                elif key == 'zunits':
                    self.zunits = value

            if self.zunits is None and (self.uplimit is not None or self.downlimit is not None):
                msg = "Point coverage '{0}' contains uplimit or downlimit but "
                msg += "does not contain zunits."
                msg = msg.format(value_str)
                raise ResourceMeta.ResourceMetaException(msg)

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
                raise ResourceMeta.ResourceMetaException(msg)
            self.uri = uri
            self.relationship_type = relationship_type

    class ResourceSource(ResourceRelation):
        KNOWN_TYPES = {'isDerivedFrom'}

    class ResourceMetaException(Exception):
        pass
