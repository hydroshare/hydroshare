__author__ = 'valentin'

from tastypie.serializers import Serializer

from rdflib import Graph,Literal,BNode,Namespace,RDF, URIRef

from rdflib.namespace import DC,DCTERMS, FOAF

class PersonFoafSerializer(Serializer):
    formats = ['json','jsonp','rdf']
    content_types = {
        'json':'application/json',
        'jsonp':'text/javascript',
        'rdf':'application/rdf+xml'

    }
    schemaOrg = Namespace('http://www.schema.org/')

# <rdf:RDF
#       xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
#       xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
#       xmlns:foaf="http://xmlns.com/foaf/0.1/"
#       xmlns:admin="http://webns.net/mvcb/">
# <foaf:PersonalProfileDocument rdf:about="">
#   <foaf:maker rdf:resource="#me"/>
#   <foaf:primaryTopic rdf:resource="#me"/>
#   <admin:generatorAgent rdf:resource="http://www.ldodds.com/foaf/foaf-a-matic"/>
#   <admin:errorReportsTo rdf:resource="mailto:leigh@ldodds.com"/>
# </foaf:PersonalProfileDocument>
# <foaf:Person rdf:ID="me">
# <foaf:name>David Valentine</foaf:name>
# <foaf:title>Dr</foaf:title>
# <foaf:givenname>David</foaf:givenname>
# <foaf:family_name>Valentine</foaf:family_name>
# <foaf:nick>val</foaf:nick>
# <foaf:mbox_sha1sum>94e6c3e99d821582e99c81fae151c5d4e9c58246</foaf:mbox_sha1sum>
# <foaf:homepage rdf:resource="http://www.example.com"/>
# <foaf:phone rdf:resource="tel:000-000-0000"/>
# <foaf:workplaceHomepage rdf:resource="http://www.sdsc.edu/"/>
# <foaf:workInfoHomepage rdf:resource="http://spatial.sdsc.edu/"/>
# <foaf:knows>
# <foaf:Person>
# <foaf:name>ilya</foaf:name>
# <foaf:mbox_sha1sum>4b6fc3561c8148a690e462624c8a8eb8ebac30a7</foaf:mbox_sha1sum></foaf:Person></foaf:knows></foaf:Person>
# </rdf:RDF>
    def to_rdf(self, data, options=None):
        pObject = data.obj
        data = self.to_simple(data, options)


        g = Graph()
        g.bind('dc',DC)
        g.bind('dc',DCTERMS)
        g.bind('foaf',FOAF)
        g.bind('schema',self.schemaOrg)

        person = URIRef(data['resource_uri'])
        g.add( (person,RDF.type,FOAF.person) )


        g.add( (person,FOAF.name,Literal(data['name'])) )
        if (data['givenName']):
            g.add( (person,FOAF.givenName,Literal( data['givenName'] ) ) )
        if (data['familyName']):
            g.add( (person,FOAF.familyName,Literal("last") ) )
        if (data['notes']):
            g.add( (person,DC.description,Literal(data['notes']) ) )

        if (data['memberOf']):
            for p in data['memberOf'] :
                g.add( (person,self.schemaOrg.memberOf,URIRef(p ) ) )

        # if (pObject.memberOf):
        #     for p in pObject.memberOf :
        #         g.add( (person,self.schemaOrg.memberOf,Literal(p['resource_uri'] ) ) )

        # if (data['email_addresses']):
        #     g.add( (person,FOAF.mbox,URIRef("mailto:me@example.com")) )

        #g.add( (person,FOAF.nick,Literal("name",lang='en') ) )
        return g.serialize(format='xml')

    pass

