from rdflib import Graph
from rdflib.namespace import Namespace, NamespaceManager, DC, DCTERMS

HSTERMS = Namespace("http://hydroshare.org/terms/")
RDFS1 = Namespace("http://www.w3.org/2000/01/rdf-schema#")

namespace_manager = NamespaceManager(Graph())
namespace_manager.bind('hsterms', HSTERMS, override=False)
namespace_manager.bind("rdfs1", RDFS1)
namespace_manager.bind('dc', DC)
namespace_manager.bind('dcterms', DCTERMS)