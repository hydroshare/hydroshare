"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from ga_ows.views import common
from django.test.client import Client
from django.test import TestCase
from django.utils import unittest
import tempfile
import json
from lxml import etree

class tdict(dict):
    def __add__(self, other):
        ret = tdict(self.copy())
        for k,v in other.items():
            ret[k] = v

        return ret


class TestOWSCommon(TestCase):
    def testGetCapabilitiesParsing(self):
        g = common.GetCapabilitiesMixin()
        req = g._parse_xml_GetCapabilities(etree.fromstring("""<?xml version="1.0" encoding="UTF-8"?>
        <GetCapabilities xmlns="http://www.opengis.net/ows/1.1"
        xmlns:ows="http://www.opengis.net/ows/1.1"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.opengis.net/ows/1.1
        fragmentGetCapabilitiesRequest.xsd" service="WCS"
        updateSequence="XYZ123">
           <!-- Maximum example for WCS. Primary editor: Arliss Whiteside -->
           <AcceptVersions>
              <Version>1.0.0</Version>
              <Version>0.8.3</Version>
           </AcceptVersions>
           <Sections>
              <Section>Contents</Section>
           </Sections>
           <AcceptFormats>
              <OutputFormat>text/xml</OutputFormat>
           </AcceptFormats>
        </GetCapabilities>"""))
        self.assertEqual(req.cleaned_data['service'], 'WCS')
        self.assertEqual(req.cleaned_data['accepted_formats'], ['text/xml'])
        self.assertEqual(req.cleaned_data['accepted_versions'], ['1.0.0', '0.8.3'])

    def textExceptionPrinting(self):
        e = common.OWSException()
        print e.xml(extend=True)


class TestWFSHttpGet(TestCase):
    fixtures = ['wfs_test.json']

    def stdTestCall(self, request, parms={}, suffix='', path='/tests/wfs'):
        rq = tdict({"service" : "WFS", "version" : "2.0.0"})
        response = self.client.get(path, (rq + {"request" : request}) + parms)
        self.assertEqual(response.status_code, 200)
        _0, name = tempfile.mkstemp(dir='/Users/jeff/geoanalytics/tmp', prefix=request, suffix=suffix+".xml") #yes, I intend for this to not be deleted upon exit
        f = open(name,'w')
        f.write(response.content)
        f.close()
        print name
        return response

    def testGetCapabilities(self):
        self.stdTestCall("GetCapabilities")

    def testListStoredQueries(self):
        self.stdTestCall("ListStoredQueries")

    def testDescribeStoredQueries(self):
        self.stdTestCall('DescribeStoredQueries', {'storedqueryid' : 'GetFeatureById'})

    def testGetFeature(self):
        self.stdTestCall("GetFeature", suffix='-all', parms={
            'srs_name' : '4326',
            'count' : 1,
            'startindex' : 1,
            'outputformat' : 'GeoJSON',
            'typenames' : ['ga_ows:WFSPointTest'],
            'filter' : json.dumps({'state' : 'NC'}),
            'filterlanguage' : 'JSON',
            'bbox' : '-81,29,-76,36',
            'sortby' : 'state'
        })

    def testGetFeatureSimple(self):
        self.stdTestCall("GetFeature", suffix='-simple', parms={
            'srs_name' : '4326',
            'typenames' : ['ga_ows:WFSPointTest'],
            'bbox' : '-81,29,-76,36'
        })

    def testGetFeatureMercator(self):
        self.stdTestCall("GetFeature", suffix='-mercator', parms={
            'srs_name' : '3857',
            'typenames' : ['ga_ows:WFSPointTest'],
            'bbox' : '-9016878.75425516,3375646.0349193094,-8460281.300288793,4300621.372044271',
            'outputformat' : 'GeoJSON',
        })

    def testGetFeatureSortBy(self):
        self.stdTestCall("GetFeature", suffix='-sortby', parms={
            'srs_name' : '3857',
            'typenames' : ['ga_ows:WFSPointTest'],
            'bbox' : '-81,29,-76,36',
            'sortby' : 'state',
            'outputformat' : 'GeoJSON',
        })

    def testGetFeatureCount(self):
        self.stdTestCall("GetFeature", suffix='-count', parms={
            'srs_name' : '4326',
            'typenames' : ['ga_ows:WFSPointTest'],
            'bbox' : '-81,29,-76,36',
            'count' : 1,
            'outputformat' : 'GeoJSON',
        })

    def testGetFeatureMaxFeatures(self):
        self.stdTestCall("GetFeature", suffix='-maxfeatures', parms={
            'srs_name' : '4326',
            'typenames' : ['ga_ows:WFSPointTest'],
            'bbox' : '-81,29,-76,36',
            'maxfeatures' : 1,
            'outputformat' : 'GeoJSON',
        })

    def testGetFeatureStartIndex(self):
        self.stdTestCall("GetFeature", suffix='-startindex', parms={
            'srs_name' : '4326',
            'typenames' : ['ga_ows:WFSPointTest'],
            'bbox' : '-81,29,-76,36',
            'startindex' : 2,
            'outputformat' : 'GeoJSON',
        })

    def testDescribeFeatureTypeJSON(self):
        self.stdTestCall("DescribeFeatureType", parms={"typename" : "ga_ows:WFSPointTest", "outputformat" : "json"})

    def testDescribeFeatureTypeXml(self):
        self.stdTestCall("DescribeFeatureType", parms={"typename" : "ga_ows:WFSPointTest"})

    @unittest.skip("get property value not implemented yet")
    def testGetPropertyValue(self):
        self.stdTestCall("GetPropertyValue", parms={
            'srs_name' : '4326',
            'typenames' : ['ga_ows:WFSPointTest'],
            'bbox' : '-81,29,-76,36'
        })

    @unittest.skip("create stored query not implemented yet")
    def testCreateStoredQuery(self):
        self.stdTestCall("CreateStoredQuery")

    @unittest.skip("drop stored query not implemented yet.")
    def testDropStoredQuery(self):
        self.stdTestCall("DropStoredQuery")

@unittest.skip("Skipping XML POST as it's not supported yet")
class TestWFSHttpPostXML(TestCase):
    def testGetCapabilities(self):
        client = Client()
    
    def testListStoredQueries(self):
        client = Client()
    
    def testDescribeStoredQueries(self):
        client = Client()
    
    def testGetFeature(self):
        client = Client()
    
    def testDescribeFeatureType(self):
        client = Client()
    
    def testGetPropertyValue(self):
        client = Client()
    
    def testCreateStoredQuery(self):
        client = Client()
    
    def testDropStoredQuery(self):
        client = Client()

@unittest.skip("Skipping transactions as they're not supported yet.")
class TestWFSTHttpGet(TestCase):
    def testTransaction(self):
        client = Client()

    def testGetFeatureWithLock(self):
        client = Client()

    def testLockFeature(self):
        client = Client()

@unittest.skip("Skipping transactions via POST as they're not supported yet.")
class TestWFSTHttpPost(unittest.TestCase):
    def testTransaction(self):
        client = Client()

    def testGetFeatureWithLock(self):
        client = Client()

    def testLockFeature(self):
        client = Client()

@unittest.skip("Skipping transactions via XML post as they're not supported yet.")
class TestWFSHttpPostXML(unittest.TestCase):
    def testTransaction(self):
        client = Client()

    def testGetFeatureWithLock(self):
        client = Client()

    def testLockFeature(self):
        client = Client()

