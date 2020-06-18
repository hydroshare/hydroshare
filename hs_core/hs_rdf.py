from rdflib import Graph
from rdflib.namespace import Namespace, NamespaceManager, DC, DCTERMS

HSTERMS = Namespace("http://hydroshare.org/terms/")
RDFS1 = Namespace("http://www.w3.org/2000/01/rdf-schema#")

NAMESPACE_MANAGER = NamespaceManager(Graph())
NAMESPACE_MANAGER.bind('hsterms', HSTERMS, override=False)
NAMESPACE_MANAGER.bind("rdfs1", RDFS1, override=False)
NAMESPACE_MANAGER.bind('dc', DC, override=False)
NAMESPACE_MANAGER.bind('dcterms', DCTERMS, override=False)