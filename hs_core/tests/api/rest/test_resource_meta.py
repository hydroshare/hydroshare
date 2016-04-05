import os
import json
import tempfile
import shutil

from lxml import etree

from rest_framework import status

from hs_core.hydroshare import resource
from .base import HSRESTTestCase


NS = {'rdf': "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
      'rdfs1': "http://www.w3.org/2001/01/rdf-schema#",
      'dc': "http://purl.org/dc/elements/1.1/",
      'dcterms': "http://purl.org/dc/terms/",
      'hsterms': "http://hydroshare.org/terms/"}

RESOURCE_METADATA = 'resourcemetadata.xml'
RESOURCE_METADATA_OLD = 'resourcemetadata_old.xml'
RESOURCE_METADATA_UPDATED = 'resourcemetadata_updated.xml'


class TestResourceMetadata(HSRESTTestCase):

    def setUp(self):
        super(TestResourceMetadata, self).setUp()

        self.rtype = 'GenericResource'
        self.title = 'My Test resource'
        res = resource.create_resource(self.rtype,
                                       self.user,
                                       self.title)
        self.pid = res.short_id
        self.resources_to_delete.append(self.pid)

    def test_get_sysmeta(self):
        # Get the resource system metadata
        sysmeta_url = "/hsapi/sysmeta/{res_id}/".format(res_id=self.pid)
        response = self.client.get(sysmeta_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = json.loads(response.content)
        self.assertEqual(content['resource_type'], self.rtype)
        self.assertEqual(content['resource_title'], self.title)
        self.assertEqual(content['resource_url'], self.resource_url.format(res_id=self.pid))

    def test_get_scimeta(self):
        # Get science metadata XML
        self.getScienceMetadata(self.pid)

    def test_put_scimeta_generic(self):
        # Update science metadata XML
        abstract_text = "This is an abstract"
        tmp_dir = tempfile.mkdtemp()

        try:
            # Get science metadata
            response = self.getScienceMetadata(self.pid, exhaust_stream=False)
            sci_meta_orig = os.path.join(tmp_dir, RESOURCE_METADATA_OLD)
            f = open(sci_meta_orig, 'w')
            for l in response.streaming_content:
                f.write(l)
            f.close()
            scimeta = etree.parse(sci_meta_orig)
            abstract = scimeta.xpath('/rdf:RDF/rdf:Description[1]/dc:description/rdf:Description/dcterms:abstract',
                                     namespaces=NS)
            self.assertEquals(len(abstract), 0)

            # Modify science metadata
            desc = scimeta.xpath('/rdf:RDF/rdf:Description[1]', namespaces=NS)[0]
            abs_dc_desc = etree.SubElement(desc, "{%s}description" % NS['dc'])
            abs_rdf_desc = etree.SubElement(abs_dc_desc, "{%s}Description" % NS['rdf'])
            abstract = etree.SubElement(abs_rdf_desc, "{%s}abstract" % NS['dcterms'])
            abstract.text = abstract_text
            # Write out to a file
            out = etree.tostring(scimeta, pretty_print=True)
            sci_meta_new = os.path.join(tmp_dir, RESOURCE_METADATA)
            f = open(sci_meta_new, 'w')
            f.writelines(out)
            f.close()

            ## Send updated metadata to REST API
            params = {'file': (RESOURCE_METADATA,
                               open(sci_meta_new),
                               'application/xml')}
            url = "/hsapi/scimeta/{pid}/".format(pid=self.pid)
            response = self.client.put(url, params)
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

            ## Get science metadata
            response = self.getScienceMetadata(self.pid, exhaust_stream=False)
            sci_meta_updated = os.path.join(tmp_dir, RESOURCE_METADATA_UPDATED)
            f = open(sci_meta_updated, 'w')
            for l in response.streaming_content:
                f.write(l)
            f.close()
            scimeta = etree.parse(sci_meta_updated)
            abstract = scimeta.xpath('/rdf:RDF/rdf:Description[1]/dc:description/rdf:Description/dcterms:abstract',
                                     namespaces=NS)
            self.assertEquals(len(abstract), 1)
            self.assertEquals(abstract[0].text, abstract_text)

            # Make sure metadata update is idempotent
            params = {'file': (RESOURCE_METADATA,
                               open(sci_meta_new),
                               'application/xml')}
            url = "/hsapi/scimeta/{pid}/".format(pid=self.pid)
            response = self.client.put(url, params)
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

            # Make sure changing the resource ID in the resource metadata causes an error
            desc = scimeta.xpath('/rdf:RDF/rdf:Description[1]', namespaces=NS)[0]
            desc.set('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about',
                     'http://example.com/resource/THISISNOTARESOURCEID')
            ## Write out to a file
            out = etree.tostring(scimeta, pretty_print=True)
            f = open(sci_meta_new, 'w')
            f.writelines(out)
            f.close()

            ## Send updated metadata to REST API
            params = {'file': (RESOURCE_METADATA,
                               open(sci_meta_new),
                               'application/xml')}
            url = "/hsapi/scimeta/{pid}/".format(pid=self.pid)
            response = self.client.put(url, params)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        finally:
            shutil.rmtree(tmp_dir)

    def test_put_scimeta_swat_model_instance(self):
        # Update science metadata XML
        abstract_text_1 = "This model is created for Flat River."
        tmp_dir = tempfile.mkdtemp()

        res = resource.create_resource('SWATModelInstanceResource',
                                       self.user,
                                       'Test SWAT Model Instance Resource')
        pid = res.short_id
        self.resources_to_delete.append(pid)

        try:
            # Apply metadata from saved file
            ## First update the resource ID
            scimeta = etree.parse('hs_core/tests/data/swat-resourcemetadata-1.xml')
            desc = scimeta.xpath('/rdf:RDF/rdf:Description[1]', namespaces=NS)[0]
            desc.set('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about',
                     "http://example.com/resource/{pid}".format(pid=pid))
            ## Write out to a file
            out = etree.tostring(scimeta, pretty_print=True)
            sci_meta_new = os.path.join(tmp_dir, RESOURCE_METADATA)
            f = open(sci_meta_new, 'w')
            f.writelines(out)
            f.close()

            ## Send updated metadata to REST API
            params = {'file': (RESOURCE_METADATA,
                               open(sci_meta_new),
                               'application/xml')}
            url = "/hsapi/scimeta/{pid}/".format(pid=pid)
            response = self.client.put(url, params)
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

            ## Get science metadata
            response = self.getScienceMetadata(pid, exhaust_stream=False)
            sci_meta_updated = os.path.join(tmp_dir, RESOURCE_METADATA_UPDATED)
            f = open(sci_meta_updated, 'w')
            for l in response.streaming_content:
                f.write(l)
            f.close()
            scimeta = etree.parse(sci_meta_updated)
            abstract = scimeta.xpath('/rdf:RDF/rdf:Description[1]/dc:description/rdf:Description/dcterms:abstract',
                                     namespaces=NS)
            self.assertEquals(len(abstract), 1)
            self.assertEquals(abstract[0].text, abstract_text_1)

            # Make sure metadata update is idempotent
            # params = {'file': (RESOURCE_METADATA,
            #                    open(sci_meta_new),
            #                    'application/xml')}
            # url = "/hsapi/scimeta/{pid}/".format(pid=self.pid)
            # response = self.client.put(url, params)
            # self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            # response = self.getScienceMetadata(pid, exhaust_stream=False)
            # sci_meta_updated = os.path.join(tmp_dir, RESOURCE_METADATA_UPDATED)
            # f = open(sci_meta_updated, 'w')
            # for l in response.streaming_content:
            #     f.write(l)
            # f.close()
            # scimeta = etree.parse(sci_meta_updated)
            # abstract = scimeta.xpath('/rdf:RDF/rdf:Description[1]/dc:description/rdf:Description/dcterms:abstract',
            #                          namespaces=NS)
            # self.assertEquals(len(abstract), 1)
            # self.assertEquals(abstract[0].text, abstract_text_1)

        finally:
            shutil.rmtree(tmp_dir)
