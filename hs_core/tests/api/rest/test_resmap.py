import os
import json
import tempfile
import shutil
import requests

from rest_framework import status
from rdflib import Graph, term

from hs_core.hydroshare import resource
from .base import ResMapTestCase


class TestResourceMap(ResMapTestCase):

    def setUp(self):
        super(TestResourceMap, self).setUp()

        self.rtype = 'CompositeResource'
        self.title = 'My Test resource'
        self.res = resource.create_resource(self.rtype,
                                            self.user,
                                            self.title)

        self.pid = self.res.short_id
        self.resources_to_delete.append(self.pid)
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)
        super(TestResourceMap, self).tearDown()

    def test_get_resmap(self):
        response = self.client.get("/hsapi/resource/{pid}/map/".format(pid=self.pid),
                                   format='json')
        # Note: this presumes that there is always a single redirection.
        # This might not be true if we utilize other systems.
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        response2 = self.client.get(response.url)
        self.assertEqual(response2.status_code, status.HTTP_302_FOUND)
        minio_response = requests.get(response2.url)

        # parse as simple RDF graph
        g = Graph()
        g.parse(data=minio_response.content.decode("utf-8"))

        documents = g.triples(
            (None, term.URIRef('http://purl.org/spar/cito/documents'), None)
        )

        # check for "documents" node
        doclen = 0
        for s, p, o in documents:

            doclen += 1
            self.assertTrue(isinstance(s, term.URIRef))
            subject = s.split('/')
            subject = subject[len(subject) - 1]
            self.assertEqual(subject, "resourcemetadata.xml")

            self.assertTrue(isinstance(o, term.Literal))
            object = o.split('/')
            object = object[len(object) - 1]
            self.assertEqual(object, "resourcemap.xml#aggregation")

        self.assertEqual(doclen, 1)

        # now create a file in the resource map
        txt_file_name = 'test.txt'
        txt_file_path = os.path.join(self.tmp_dir, txt_file_name)
        txt = open(txt_file_path, 'w')
        txt.write("Hello World.\n")
        txt.close()

        # Upload the new resource file
        params = {'file': (txt_file_name,
                           open(txt_file_path, 'rb'),
                           'text/plain')}
        url = "/hsapi/resource/{pid}/files/".format(pid=self.pid)
        response = self.client.post(url, params)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        content = json.loads(response.content.decode())
        self.assertEqual(content['resource_id'], self.pid)

        # download the resource map and # make sure the new file appears
        response = self.client.get("/hsapi/resource/{pid}/map/".format(pid=self.pid))
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        response2 = self.client.get(response.url)
        self.assertEqual(response2.status_code, status.HTTP_302_FOUND)
        minio_response = requests.get(response2.url)

        # parse as a simple RDF file of triples
        g = Graph()
        g.parse(data=minio_response.content.decode("utf-8"))

        # check that the graph contains an appropriate "documents" node
        documents = g.triples(
            (None, term.URIRef('http://purl.org/spar/cito/documents'), None)
        )

        doclen = 0
        for s, p, o in documents:

            doclen += 1
            self.assertTrue(isinstance(s, term.URIRef))
            subject = s.split('/')
            subject = subject[len(subject) - 1]
            self.assertEqual(subject, "resourcemetadata.xml")

            self.assertTrue(isinstance(o, term.Literal))
            object = o.split('/')
            object = object[len(object) - 1]
            self.assertEqual(object, "resourcemap.xml#aggregation")

        self.assertEqual(doclen, 1)

        formats = g.triples(
            (None, term.URIRef('http://purl.org/dc/elements/1.1/format'), None)
        )

        # check that MIME types are correctly defined
        fmtlen = 0
        txt_count = 0
        xml_count = 0
        for s, p, o in formats:
            fmtlen += 1
            subject = s.split('/')
            subject = subject[len(subject) - 1]
            self.assertTrue(isinstance(o, term.Literal))
            if (subject == 'test.txt'):
                txt_count += 1
                self.assertEqual(str(o), 'text/plain')
            else:
                xml_count += 1
                self.assertEqual(str(o), 'application/rdf+xml')

        self.assertEqual(1, txt_count)
        self.assertEqual(2, xml_count)
        # pidgeonhole principle: if there are three, then one is the file in question
        self.assertEqual(fmtlen, 3)
