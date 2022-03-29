# run with: python manage.py test hs_core.tests.serialization.test_resourcemeta_sax_parsing
import unittest
import xml.sax

from hs_core.serialization import GenericResourceSAXHandler
from hs_geo_raster_resource.serialization import RasterResourceSAXHandler


class TestGenericResourceMetaSax(unittest.TestCase):
    def setUp(self):

        self.parse_sample = """<?xml version="1.0"?>
        <!DOCTYPE rdf:RDF PUBLIC "-//DUBLIN CORE//DCMES DTD 2002/07/31//EN"
        "http://dublincore.org/documents/2002/07/31/dcmes-xml/dcmes-xml-dtd.dtd">
        <rdf:RDF xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:hsterms="https://www.hydroshare.org/terms/">
          <rdf:Description rdf:about="http://localhost:8000/resource/dc52e6aa93154521af08522de27ec276">
            <dc:contributor>
              <rdf:Description rdf:about="http://localhost:8000/user/1/">
                <hsterms:name>Brian Miles</hsterms:name>
                <hsterms:organization>Someplace</hsterms:organization>
                <hsterms:email>foo@gmail.com</hsterms:email>
                <hsterms:address>123 Main Street</hsterms:address>
                <hsterms:phone rdf:resource="tel:412-555-1212"/>
                <hsterms:homepage rdf:resource="http://www.ie.unc.edu/"/>
              </rdf:Description>
            </dc:contributor>
            <dc:contributor>
              <rdf:Description rdf:about="http://localhost:8000/user/2/">
                <hsterms:name>Miles Brian</hsterms:name>
                <hsterms:organization>Elsewhere</hsterms:organization>
                <hsterms:email>bar@icloud.com</hsterms:email>
                <hsterms:address>123 Wall Street</hsterms:address>
                <hsterms:phone rdf:resource="tel:412-555-2121"/>
                <hsterms:homepage rdf:resource="http://www.cmu.edu/"/>
              </rdf:Description>
            </dc:contributor>
            <dc:subject>HydroShare</dc:subject>
            <dc:subject>cuahsi</dc:subject>
            <dc:subject>Presentation</dc:subject>
            <dc:subject>Hydroinformatics</dc:subject>
          </rdf:Description>
        </rdf:RDF>
        """

    def tearDown(self):
        pass

    def test_sax_parsing(self):
        handler = GenericResourceSAXHandler()
        xml.sax.parseString(self.parse_sample, handler)

        self.assertTrue(len(handler.subjects) == 4)
        self.assertEqual(handler.subjects[0], 'HydroShare')
        self.assertEqual(handler.subjects[1], 'cuahsi')
        self.assertEqual(handler.subjects[2], 'Presentation')
        self.assertEqual(handler.subjects[3], 'Hydroinformatics')

        self.assertTrue(len(handler.contributors) == 2)
        self.assertEqual(handler.contributors[0].uri, 'http://localhost:8000/user/1/')
        self.assertEqual(handler.contributors[0].name, 'Brian Miles')
        self.assertEqual(handler.contributors[0].organization, 'Someplace')
        self.assertEqual(handler.contributors[0].email, 'foo@gmail.com')
        self.assertEqual(handler.contributors[0].address, '123 Main Street')
        self.assertEqual(handler.contributors[0].phone, '412-555-1212')

        self.assertEqual(handler.contributors[1].uri, 'http://localhost:8000/user/2/')
        self.assertEqual(handler.contributors[1].name, 'Miles Brian')
        self.assertEqual(handler.contributors[1].organization, 'Elsewhere')
        self.assertEqual(handler.contributors[1].email, 'bar@icloud.com')
        self.assertEqual(handler.contributors[1].address, '123 Wall Street')
        self.assertEqual(handler.contributors[1].phone, '412-555-2121')

class TestRasterResourceMetaSax(unittest.TestCase):
    def setUp(self):

        self.parse_sample = """<?xml version="1.0"?>
        <!DOCTYPE rdf:RDF PUBLIC "-//DUBLIN CORE//DCMES DTD 2002/07/31//EN"
        "http://dublincore.org/documents/2002/07/31/dcmes-xml/dcmes-xml-dtd.dtd">
        <rdf:RDF xmlns:dcterms="http://purl.org/dc/terms/" xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:hsterms="https://www.hydroshare.org/terms/">
          <rdf:Description rdf:about="http://localhost:8000/resource/dc52e6aa93154521af08522de27ec276">
            <hsterms:BandInformation>
              <rdf:Description>
                <hsterms:name>Band_1</hsterms:name>
                <hsterms:variableName>red</hsterms:variableName>
                <hsterms:variableUnit>DN</hsterms:variableUnit>
                <hsterms:method>measured</hsterms:method>
                <hsterms:comment>real good.</hsterms:comment>
              </rdf:Description>
            </hsterms:BandInformation>
            <hsterms:BandInformation>
              <rdf:Description>
                <hsterms:name>Band_2</hsterms:name>
                <hsterms:variableName>green</hsterms:variableName>
                <hsterms:variableUnit>DN</hsterms:variableUnit>
                <hsterms:method>guessed</hsterms:method>
                <hsterms:comment>not so good.</hsterms:comment>
              </rdf:Description>
            </hsterms:BandInformation>
            <hsterms:BandInformation>
              <rdf:Description>
                <hsterms:name>Band_3</hsterms:name>
                <hsterms:variableName>blue</hsterms:variableName>
                <hsterms:variableUnit>DN</hsterms:variableUnit>
                <hsterms:method>random</hsterms:method>
                <hsterms:comment>random like.</hsterms:comment>
              </rdf:Description>
            </hsterms:BandInformation>
          </rdf:Description>
        </rdf:RDF>
        """

    def tearDown(self):
        pass

    def test_sax_parsing(self):
        handler = RasterResourceSAXHandler()
        xml.sax.parseString(self.parse_sample, handler)

        self.assertTrue(len(handler.band_info) == 3)
        self.assertEqual(handler.band_info[0].name, 'Band_1')
        self.assertEqual(handler.band_info[0].variableName, 'red')
        self.assertEqual(handler.band_info[0].variableUnit, 'DN')
        self.assertEqual(handler.band_info[0].method, 'measured')
        self.assertEqual(handler.band_info[0].comment, 'real good.')

        self.assertEqual(handler.band_info[1].name, 'Band_2')
        self.assertEqual(handler.band_info[1].variableName, 'green')
        self.assertEqual(handler.band_info[1].variableUnit, 'DN')
        self.assertEqual(handler.band_info[1].method, 'guessed')
        self.assertEqual(handler.band_info[1].comment, 'not so good.')

        self.assertEqual(handler.band_info[2].name, 'Band_3')
        self.assertEqual(handler.band_info[2].variableName, 'blue')
        self.assertEqual(handler.band_info[2].variableUnit, 'DN')
        self.assertEqual(handler.band_info[2].method, 'random')
        self.assertEqual(handler.band_info[2].comment, 'random like.')

