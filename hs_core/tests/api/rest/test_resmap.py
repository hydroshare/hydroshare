import os
import json
import tempfile
import shutil
from rest_framework import status
from rdflib import Graph, term

from hs_core.hydroshare import resource
from .base import ResMapTestCase


class TestResourceMap(ResMapTestCase):

    def setUp(self):
        super(TestResourceMap, self).setUp()

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title)

        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)
        super(TestResourceMap, self).tearDown()

    def test_get_resmap(self):
        response = self.client.get("/hsapi/resmap/{pid}/".format(pid=self.pid),
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        response2 = self.client.get(response.url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # collect response from stream
        output = ""
        while True:
            try:
                output += response2.streaming_content.next()
            except StopIteration:
                break

        # parse as simple RDF graph
        g = Graph()
        g.parse(data=output)

        documents = g.triples(
            (None, term.URIRef(u'http://purl.org/spar/cito/documents'), None)
        )

        self.assertEqual(len(documents), 1)
        # check for "documents" node
        for s, p, o in documents:

            self.assertTrue(isinstance(s, term.URIRef))
            subject = s.split('/')
            subject = subject[len(subject)-1]
            self.assertEqual(subject, "resourcemetadata.xml")

            self.assertTrue(isinstance(o, term.Literal))
            object = o.split('/')
            object = object[len(object)-1]
            self.assertEqual(object, "resourcemap.xml#aggregation")

        # now create a file in the resource map
        txt_file_name = 'text.txt'
        txt_file_path = os.path.join(self.tmp_dir, txt_file_name)
        txt = open(txt_file_path, 'w')
        txt.write("Hello World.\n")
        txt.close()

        # Upload the new resource file
        params = {'file': (txt_file_name,
                           open(txt_file_path),
                           'text/plain')}
        url = "/hsapi/resource/{pid}/files/".format(pid=self.pid)
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content)
        self.assertEquals(content['resource_id'], self.pid)

        # download the resource map and
        # Make sure the new file appears in the resource map
        response = self.client.get("/hsapi/resmap/{pid}/".format(pid=self.pid))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        response2 = self.client.get(response.url)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        # collect the map from the stream
        output = ""
        while True:
            try:
                output += response2.streaming_content.next()
            except StopIteration:
                break

        # parse as a simple RDF file of triples
        g = Graph()
        g.parse(data=output)

        # check that the graph contains an appropriate "documents" node
        documents = g.triples(
            (None, term.URIRef(u'http://purl.org/spar/cito/documents'), None)
        )
        self.assertEqual(len(documents), 1)

        for s, p, o in documents:

            self.assertTrue(isinstance(s, term.URIRef))
            subject = s.split('/')
            subject = subject[len(subject)-1]
            self.assertEqual(subject, "resourcemetadata.xml")

            self.assertTrue(isinstance(o, term.Literal))
            object = o.split('/')
            object = object[len(object)-1]
            self.assertEqual(object, "resourcemap.xml#aggregation")

        formats = g.triples(
            (None, term.URIRef(u'http://purl.org/dc/elements/1.1/format'), None)
        )
        self.assertEqual(len(formats), 3)

        # check that MIME types are correctly defined
        for s, p, o in formats:
            subject = s.split('/')
            subject = subject[len(subject)-1]
            self.assertTrue(isinstance(o, term.Literal))
            if (subject == 'test.txt'):
                self.assertEqual(o, u'text/plain')
            else:
                self.assertEqual(o, u'application/rdf+xml')
