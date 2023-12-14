from django.contrib.contenttypes.fields import GenericRelation
from django.core.exceptions import ValidationError
from rdflib import Graph, BNode
from rdflib.collection import Collection
from rdflib.namespace import Namespace, DC, DCTERMS, RDF, RDFS
from rdflib.plugin import register
from rdflib.plugins.serializers.rdfxml import XMLLANG, OWL_NS, XMLBASE
from rdflib.plugins.serializers.xmlwriter import XMLWriter
from rdflib.serializer import Serializer
from rdflib.term import Literal, URIRef
from rdflib.util import first

HSTERMS = Namespace("https://www.hydroshare.org/terms/")
RDFS1 = Namespace("http://www.w3.org/2000/01/rdf-schema#")


class RDF_MetaData_Mixin(object):
    """
    A mixin for MetaData objects which store their metadata in generic relations.  If metadata outside of generic
    relations need to be used, you may extend ingest_metadata and get_rdf_graph to include the other metadata elements
    """

    def rdf_subject(self):
        raise NotImplementedError("RDF_Metadata_Mixin implementations must implement rdf_subject")

    def rdf_metadata_subject(self):
        raise NotImplementedError("RDF_Metadata_Mixin implementations must implement rdf_metadata_subject")

    def rdf_type(self):
        raise NotImplementedError("RDF_Metadata_Mixin implementations must implement rdf_type. "
                                  "https://www.w3.org/TR/rdf-schema/#ch_type")

    def ignored_generic_relations(self):
        """Override to exclude generic relations from the rdf/xml.  This is built specifically for Format, which is the
        only AbstractMetadataElement that is on a metadata model and not included in the rdf/xml.  Returns a list
        of classes to be ignored"""
        return []

    @classmethod
    def rdf_subject_from_graph(cls, graph):
        """Derive the root subject of an rdflib Graph by returning the subject in the triple with predicate DC.title"""
        subject = None
        for s, _, _ in graph.triples((None, DC.title, None)):
            subject = s
            break
        if not subject:
            raise Exception("Invalid rdf/xml, could not find required predicate dc:title")
        return subject

    def ingest_metadata(self, graph):
        """Given an rdflib Graph, run ingest_rdf for all generic relations on the object"""
        subject = self.rdf_subject_from_graph(graph)

        generic_relations = list(filter(lambda f: isinstance(f, GenericRelation), type(self)._meta.private_fields))
        for generic_relation in generic_relations:
            if generic_relation.related_model not in self.ignored_generic_relations():
                getattr(self, generic_relation.name).all().delete()
                generic_relation.related_model.ingest_rdf(graph, subject, self)
        self.save()

    def get_rdf_graph(self):
        """adds the rdf triples of all generic relations on the object into an rdflib Graph"""
        graph = Graph()
        graph.namespace_manager.bind('hsterms', HSTERMS, override=False)
        graph.namespace_manager.bind("rdfs1", RDFS1, override=False)
        graph.namespace_manager.bind('dc', DC, override=False)
        graph.namespace_manager.bind('dcterms', DCTERMS, override=False)

        subject = self.rdf_subject()
        graph.add((subject, RDF.type, self.rdf_type()))
        generic_relations = list(filter(lambda f: isinstance(f, GenericRelation), type(self)._meta.private_fields))
        for generic_relation in generic_relations:
            if generic_relation.related_model not in self.ignored_generic_relations():
                gr_name = generic_relation.name
                gr = getattr(self, gr_name)
                for f in gr.all():
                    f.rdf_triples(subject, graph)

        return graph

    def get_xml(self, pretty_print=True, include_format_elements=True):
        """Generates ORI+RDF xml for this metadata"""
        g = self.get_rdf_graph()
        return g.serialize(format='hydro-xml').decode()


class RDF_Term_MixIn(object):
    """
    Provides methods for serializing a django model into and rdflib triples and deserializing from an rdflib Graph
     back to a django model.  This mixin is designed for django models that are generic relations of another django
     model which represents a group of metadata.

     Without any configuration, the rdf_triples(subject) method will add all fields on the generic relation model except
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
        term = self.get_class_term()
        if not term:
            metadata_node = subject
        else:
            metadata_node = BNode()
            graph.add((subject, term, metadata_node))
        for field_term, field_value in self.get_field_terms_and_values():
            graph.add((metadata_node, field_term, field_value))

    def get_field_terms_and_values(self, extra_ignored_fields=[]):
        """Method that returns the field terms and field values on an object"""
        from hs_core.hydroshare import encode_resource_url
        term_values = []
        extra_ignored_fields.extend(self.ignored_fields)
        for field in [field for field in self._meta.fields if field.name not in extra_ignored_fields]:
            field_term = self.get_field_term(field.name)
            field_value = getattr(self, field.name)
            if field_value is not None and field_value != 'None':
                # urls should be a URIRef term, all others should be a Literal term
                if isinstance(field_value, str) and field_value.startswith('http'):
                    field_value = URIRef(encode_resource_url(field_value))
                else:
                    field_value = Literal(field_value)
                term_values.append((field_term, field_value))
        return term_values

    @classmethod
    def get_class_term(cls):
        """
        return a term mapped by the @rdf_terms decorator or if the decorator is not provided, create an
        HSTERMS.{cls.__name__}
        """
        return cls.rdf_term if hasattr(cls, 'rdf_term') else getattr(HSTERMS, cls.__name__)

    @classmethod
    def get_field_term(cls, field_name):
        """
        Given a class field_name, return a term mapped by the @rdf_terms decoroator or if the decorator is
        not provided, create an HSTERMS.{field_name}
        """
        field_term_attr = field_name + '_rdf_term'
        if hasattr(cls, field_term_attr):
            return getattr(cls, field_term_attr)
        else:
            return getattr(HSTERMS, field_name)

    @classmethod
    def ingest_rdf(cls, graph, subject, content_object):
        """Default implementation that ingests by convention"""
        from hs_core.hydroshare import decode_resource_url

        term = cls.get_class_term()
        if not term:
            metadata_nodes = [subject]
        else:
            metadata_nodes = graph.objects(subject=subject, predicate=term)

        for metadata_node in metadata_nodes:
            value_dict = {}
            for field in cls._meta.fields:
                if cls.ignored_fields and field.name in cls.ignored_fields:
                    continue
                field_term = cls.get_field_term(field.name)
                val = graph.value(subject=metadata_node, predicate=field_term)
                if val is not None:
                    if isinstance(val, URIRef):
                        value_dict[field.name] = decode_resource_url(str(val.toPython()))
                    else:
                        value_dict[field.name] = str(val.toPython())
            if value_dict:
                cls.create(content_object=content_object, **value_dict)


def rdf_terms(class_term, **field_terms):
    """
    Decorator for mapping a class and fields to RDF terms.  The first parameter maps the class to your specified
    term.  field_terms are key/values with the key matching a class's field and the value being the mapped term.

    :raises ValidationError when a field_term key does not match a field on the class"""
    def decorator(obj):
        obj.rdf_term = class_term
        for k, v in field_terms.items():
            if not hasattr(obj, k):
                raise ValidationError("field {} not found".format(k))
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
        stream.write(b"\n")

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

        elif subject not in self.__serialized:
            self.__serialized[subject] = 1
            type = first(store.objects(subject, RDF.type))

            try:
                self.nm.qname(type)
            except: # noqa
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
            if first(store.objects(object, RDF.first)):
                self.__serialized[object] = 1

                # Warn that any assertions on object other than
                # RDF.first and RDF.rest are ignored... including RDF.List
                import warnings
                warnings.warn(
                    "Assertions on %s other than RDF.first " % repr(object)
                    + "and RDF.rest are ignored ... including RDF.List",
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

                    if object not in self.__serialized \
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
