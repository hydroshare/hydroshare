from django.contrib.contenttypes.fields import GenericRelation
from rdflib import Graph, BNode
from rdflib.collection import Collection
from rdflib.namespace import Namespace, NamespaceManager, DC, DCTERMS, RDF, RDFS
from rdflib.plugin import register
from rdflib.plugins.serializers.rdfxml import PrettyXMLSerializer, XMLLANG, OWL_NS, XMLBASE
from rdflib.plugins.serializers.xmlwriter import XMLWriter
from rdflib.serializer import Serializer
from rdflib.term import Literal, URIRef
from rdflib.py3compat import b
from rdflib.util import first

HSTERMS = Namespace("http://hydroshare.org/terms/")
RDFS1 = Namespace("http://www.w3.org/2000/01/rdf-schema#")

NAMESPACE_MANAGER = NamespaceManager(Graph())
NAMESPACE_MANAGER.bind('hsterms', HSTERMS, override=False)
NAMESPACE_MANAGER.bind("rdfs1", RDFS1, override=False)
NAMESPACE_MANAGER.bind('dc', DC, override=False)
NAMESPACE_MANAGER.bind('dcterms', DCTERMS, override=False)


class RDF_MetaData_Mixin(object):

    def rdf_subject(self):
        raise NotImplementedError("RDF_Metadata_Mixin implementations must implement rdf_subject")

    def ingest_metadata(self, graph):
        subject = self.rdf_subject()

        for s, p, o in graph.triples((subject, HSTERMS.extendedMetadata, None)):
            key = graph.value(subject=o, predicate=HSTERMS.key).value
            value = graph.value(subject=o, predicate=HSTERMS.value).value
            self.resource.extra_metadata[key] = value

        for field in self.__class__._meta.fields:
            if field.name in ['id', 'object_id', 'content_type', 'extra_metadata', 'is_dirty']:
                continue
            field_value = graph.value(subject=subject, predicate=getattr(HSTERMS, field.name))
            if field_value:
                setattr(self, field.name, field_value)

        generic_relations = list(filter(lambda f: isinstance(f, GenericRelation), type(self)._meta.virtual_fields))
        for generic_relation in generic_relations:
            generic_relation.related_model.ingest_rdf(graph, self)
        self.save()

    def get_rdf_graph(self):
        graph = Graph()
        graph.namespace_manager = NAMESPACE_MANAGER

        subject = self.rdf_subject()

        # add any key/value metadata items
        if len(self.resource.extra_metadata) > 0:
            for key, value in list(self.resource.extra_metadata.items()):
                extendedMetadata = BNode()
                graph.add((subject, HSTERMS.extendedMetadata, extendedMetadata))
                graph.add((extendedMetadata, HSTERMS.key, Literal(key)))
                graph.add((extendedMetadata, HSTERMS.value, Literal(value)))

        for field in self.__class__._meta.fields:
            if field.name in ['id', 'object_id', 'content_type', 'extra_metadata', 'is_dirty']:
                continue
            graph.add((subject, getattr(HSTERMS, field.name), Literal(field.value_from_object(self))))

        generic_relations = list(filter(lambda f: isinstance(f, GenericRelation), type(self)._meta.virtual_fields))
        for generic_relation in generic_relations:
            for f in getattr(self, getattr(generic_relation, 'name', None), None).all():
                f.rdf_triples(subject, graph)

        from .hydroshare import current_site_url
        TYPE_SUBJECT = getattr(Namespace("{}/terms/".format(current_site_url())), self.resource.__class__.__name__)
        graph.add((TYPE_SUBJECT, RDFS1.label, Literal(self.resource._meta.verbose_name)))
        graph.add((TYPE_SUBJECT, RDFS1.isDefinedBy, URIRef(HSTERMS)))
        return graph

    def get_xml(self, pretty_print=True, include_format_elements=True):
        """Generates ORI+RDF xml for this aggregation metadata"""

        # get the xml root element and the xml element to which contains all other elements
        g = self.get_rdf_graph()
        return g.serialize(format='hydro-xml').decode()


class RDF_Term_MixIn(object):
    """Provides methods for serializing a django model into and rdflib triples and deserializing from an rdflib Graph
     back to a django model.  This mixin is designed for django models that are generic relations of another django
     model which represents a group of metadata.

     Without any configuration, the rdf_triples(subject) method will add all fields on the model except
     for 'id', 'object_id', 'content_type' will be serialized as rdf triples.  If rdf_term is defined, it will be
     used as the predicate.  If rdf_term is not defined, one will be defined using the class name and the
     HSTERMS namespace.

     When a model requires an rdf-xml format that the default configuration will not provide, you may overwrite
     the rdf_triples method and the ingest_rdf method.  If you overwrite one, you must overwrite both or this mixin
     will not work correctly.
     """

    ignored_fields = ['id', 'object_id', 'content_type']

    def rdf_triples(self, subject, graph):
        """Default implementation that parses by convention."""
        term = self.rdf_term if hasattr(self, 'rdf_term') else getattr(HSTERMS, self.__class__.__name__)
        metadata_node = BNode()
        graph.add((subject, term, metadata_node))
        for field in self.__class__._meta.fields:
            if self.ignored_fields and field.name in self.ignored_fields:
                continue
            field_term_attr = field.name + '_rdf_term'
            if hasattr(self, field_term_attr):
                field_term = getattr(self, field_term_attr)
            else:
                field_term = getattr(HSTERMS, field.name)
            field_value = getattr(self, field.name)
            # urls should be a URIRef term, all others should be a Literal term
            if field_value and field_value != 'None':
                if isinstance(field_value, str) and field_value.startswith('http'):
                    field_value = URIRef(field_value)
                else:
                    field_value = Literal(field_value)
                graph.add((metadata_node, field_term, field_value))

    @classmethod
    def ingest_rdf(cls, graph, content_object):
        """Default implementation that ingests by convention"""
        term = cls.rdf_term if hasattr(cls, 'rdf_term') else getattr(HSTERMS, cls.__name__)
        value_dict = {}
        subject = content_object.rdf_subject()
        metadata_nodes = graph.objects(subject=subject, predicate=term)
        for metadata_node in metadata_nodes:
            for field in cls._meta.fields:
                if cls.ignored_fields and field.name in cls.ignored_fields:
                    continue
                field_term_attr = field.name + '_rdf_term'
                if hasattr(cls, field_term_attr):
                    field_term = getattr(cls, field_term_attr)
                else:
                    field_term = getattr(HSTERMS, field.name)
                val = graph.value(metadata_node, field_term)
                if val:
                    value_dict[field.name] = val.value if isinstance(val, Literal) else str(val)
            if value_dict:
                cls.create(content_object=content_object, **value_dict)


def rdf_terms(class_term, **field_terms):
    def decorator(obj):
        if class_term:
            obj.rdf_term = class_term
        for k, v in field_terms.items():
            if not hasattr(obj, k):
                raise Exception("field {} not found".format(k))
            setattr(obj, k + '_rdf_term', v)
        return obj
    return decorator


class HydroPrettyXMLSerializer(Serializer):
    """Same as PrettyXMLSerializer but with stripped out node ids"""

    def __init__(self, store, max_depth=3):
        super(HydroPrettyXMLSerializer, self).__init__(store)
        self.forceRDFAbout = set()

    def serialize(self, stream, base=None, encoding=None, **args):
        self.__serialized = {}
        store = self.store
        self.base = base
        self.max_depth = args.get("max_depth", 3)
        assert self.max_depth > 0, "max_depth must be greater than 0"

        self.nm = nm = store.namespace_manager
        self.writer = writer = XMLWriter(stream, nm, encoding)
        namespaces = {}

        possible = set(store.predicates()).union(
            store.objects(None, RDF.type))

        for predicate in possible:
            prefix, namespace, local = nm.compute_qname(predicate)
            namespaces[prefix] = namespace

        namespaces["rdf"] = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

        writer.push(RDF.RDF)

        if "xml_base" in args:
            writer.attribute(XMLBASE, args["xml_base"])

        writer.namespaces(iter(list(namespaces.items())))

        # Write out subjects that can not be inline
        for subject in store.subjects():
            if (None, None, subject) in store:
                if (subject, None, subject) in store:
                    self.subject(subject, 1)
            else:
                self.subject(subject, 1)

        # write out anything that has not yet been reached
        # write out BNodes last (to ensure they can be inlined where possible)
        bnodes = set()

        for subject in store.subjects():
            if isinstance(subject, BNode):
                bnodes.add(subject)
                continue
            self.subject(subject, 1)

        # now serialize only those BNodes that have not been serialized yet
        for bnode in bnodes:
            if bnode not in self.__serialized:
                self.subject(subject, 1)

        writer.pop(RDF.RDF)
        stream.write(b("\n"))

        # Set to None so that the memory can get garbage collected.
        self.__serialized = None

    def subject(self, subject, depth=1):
        store = self.store
        writer = self.writer

        if subject in self.forceRDFAbout:
            writer.push(RDF.Description)
            writer.attribute(RDF.about, self.relativize(subject))
            writer.pop(RDF.Description)
            self.forceRDFAbout.remove(subject)

        elif not subject in self.__serialized:
            self.__serialized[subject] = 1
            type = first(store.objects(subject, RDF.type))

            try:
                self.nm.qname(type)
            except:
                type = None

            element = type or RDF.Description
            writer.push(element)

            if isinstance(subject, BNode):
                def subj_as_obj_more_than(ceil):
                    return True
                    # more_than(store.triples((None, None, subject)), ceil)

            else:
                writer.attribute(RDF.about, self.relativize(subject))

            if (subject, None, None) in store:
                for predicate, object in store.predicate_objects(subject):
                    if not (predicate == RDF.type and object == type):
                        self.predicate(predicate, object, depth + 1)
            writer.pop(element)

        elif subject in self.forceRDFAbout:
            writer.push(RDF.Description)
            writer.attribute(RDF.about, self.relativize(subject))
            writer.pop(RDF.Description)
            self.forceRDFAbout.remove(subject)

    def predicate(self, predicate, object, depth=1):
        writer = self.writer
        store = self.store
        writer.push(predicate)

        if isinstance(object, Literal):
            if object.language:
                writer.attribute(XMLLANG, object.language)

            if object.datatype:
                writer.attribute(RDF.datatype, object.datatype)

            writer.text(object)

        elif object in self.__serialized or not (object, None, None) in store:

            if isinstance(object, BNode):
                pass
            else:
                writer.attribute(RDF.resource, self.relativize(object))

        else:
            if first(store.objects(object, RDF.first)):  # may not have type
                                                         # RDF.List

                self.__serialized[object] = 1

                # Warn that any assertions on object other than
                # RDF.first and RDF.rest are ignored... including RDF.List
                import warnings
                warnings.warn(
                    "Assertions on %s other than RDF.first " % repr(object) +
                    "and RDF.rest are ignored ... including RDF.List",
                    UserWarning, stacklevel=2)
                writer.attribute(RDF.parseType, "Collection")

                col = Collection(store, object)

                for item in col:

                    if isinstance(item, URIRef):
                        self.forceRDFAbout.add(item)
                    self.subject(item)

                    if not isinstance(item, URIRef):
                        self.__serialized[item] = 1
            else:
                if first(store.triples_choices(
                    (object, RDF.type, [OWL_NS.Class, RDFS.Class]))) \
                        and isinstance(object, URIRef):
                    writer.attribute(RDF.resource, self.relativize(object))

                elif depth <= self.max_depth:
                    self.subject(object, depth + 1)

                elif isinstance(object, BNode):

                    if not object in self.__serialized \
                            and (object, None, None) in store \
                            and len(list(store.subjects(object=object))) == 1:
                        # inline blank nodes if they haven't been serialized yet
                        # and are only referenced once (regardless of depth)
                        self.subject(object, depth + 1)

                else:
                    writer.attribute(RDF.resource, self.relativize(object))

        writer.pop(predicate)

register(
    'hydro-xml', Serializer,
    'hs_core.hs_rdf', 'HydroPrettyXMLSerializer')
