__author__ = 'valentin'

from tastypie.serializers import Serializer

from rdflib import Graph,Literal,BNode,Namespace,RDF,RDFS, URIRef

from rdflib.namespace import Namespace,DC,DCTERMS, FOAF

class OrganizationFFoafSerializer(Serializer):
    formats = ['json','jsonp','rdf']
    content_types = {
        'json':'application/json',
        'jsonp':'text/javascript',
        'rdf':'application/rdf+xml'

    }
    schemaOrg = Namespace('http://www.schema.org/')

    def to_rdf(self, data, options=None):
        data = self.to_simple(data, options)
        g = Graph()
        g.bind('dc',DC)
        g.bind('dc',DCTERMS)
        g.bind('foaf',FOAF)
        g.bind('schema',self.schemaOrg)

        #org = BNode()
        org = URIRef(data['resource_uri'])
        #org.set(RDF.type, FOAF.Person) # .set replaces all other values
        #org.set(RDFS.label, Literal("org2"))

        g.add( (org,RDF.type,FOAF.organization) )

        g.add( (org,FOAF.name,Literal( data['name'] )) )

        # if ( data['businessAddress'] ):
        #     g.add( (org,self.schemaOrg.address,Literal( data['businessAddress'] ) ) )

        if(data['url']):
             g.add( (org,FOAF.homepage,URIRef(data['url'])) )

        if(data['notes']):
            g.add( (org,DC.description,Literal(data['notes']) ) )

        if( data['logoUrl']):
            g.add ( (org,FOAF.img, URIRef(data['logoUrl'])) )


        #g.add( (org,FOAF.nick,Literal("name",lang='en') ) )

        return g.serialize(format='xml')

    pass

