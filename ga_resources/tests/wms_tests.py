from unittest import TestCase
import requests
from lxml import etree
from PIL import Image

host = 'http://localhost:8000/'

class TestWMS(TestCase):
    def assertSuccess(self, response, msg='response status code: {code}\n{response}'):
        msg = msg.format(code=response.status_code, response=response.text)
        self.assertGreaterEqual(response.status_code, 200, msg=msg)
        self.assertLess(response.status_code, 300, msg=msg)


    def test_GetCapabilities(self):
        rsp = requests.get('{host}ga_resources/wms/'.format(host=host), params={
            'request' : 'GetCapabilities',
            'version' : '1.1.0',
            'service' : 'WMS'
        })
        self.assertSuccess(rsp)
        etree.parse(rsp.text)

    def test_GetMap(self):
        rsp = requests.get('{host}ga_resources/wms/ '.format(host=host), params={
            'request': 'GetMap',
            'version': '1.1.0',
            'service': 'WMS',
            'bbox' : '-180,-90,180,90',
            'srs' : 'EPSG:4326',
            'layers' : 'example-layer',
            'styles' : 'example-style'
        }, stream=True)
        self.assertSuccess(rsp)
        Image.open(rsp.raw) # should raise an exception if it fails


    def test_GetFeatureInfo(self):
        self.fail('not written yet')

    def test_GetTile(self):
        rsp = requests.get('{host}ga_resources/example-layer/tms/8/1/1/'.format(host=host), stream=True)

        self.assertSuccess(rsp)
        Image.open(rsp.raw) # should raise an exception if it fails

