# -*- coding: utf-8 -*-
"""
Test geospatial functions 
"""

from unittest import TestCase
from hs_geo.jaccard import geo_one_degree, geo_inside, geo_area_union, geo_area_intersection, geo_jaccard_internal

class GeoTest(TestCase):

    def test_geo_one(self):
        stuff = [
          [{'type': 'point', 'east': 230.0, 'north': 40.0}, 
           {'type': 'point', 'east': 230.5, 'north': 40.5}, 
           1.0], 
          [{'type': 'point', 'east': 230.0, 'north': 40.0}, 
           {'type': 'point', 'east': 231.5, 'north': 40.5}, 
           0.0]
        ] 
        for n in stuff:
            result = geo_one_degree(n[0], n[1])
            self.assertEqual(result, n[2])

    def test_geo_inside(self): 
        stuff = [
          [{'type': 'point', 'east': 175.0, 'north': 41.0}, 
           {'type': 'box', 'westlimit': 170.0, 'eastlimit': 180.0, 'southlimit': 40.5, 'northlimit': 41.4}, 
           1.0], 
          [{'type': 'point', 'east': 165.0, 'north': 41.0}, 
           {'type': 'box', 'westlimit': 170.0, 'eastlimit': 180.0, 'southlimit': 40.5, 'northlimit': 41.4}, 
           0.0], 
          [{'type': 'point', 'east': 175.0, 'north': 42.0}, 
           {'type': 'box', 'westlimit': 170.0, 'eastlimit': 180.0, 'southlimit': 40.5, 'northlimit': 41.4}, 
           0.0]
        ] 
        for n in stuff:
            result = geo_inside(n[0], n[1])
            self.assertEqual(result, n[2])
    
    def test_geo_area_union(self):
        stuff = [
          [{'type': 'box', 'westlimit': 170.0, 'eastlimit': 171.0, 'southlimit': 40, 'northlimit': 41}, 
           {'type': 'box', 'westlimit': 170.0, 'eastlimit': 171.0, 'southlimit': 40, 'northlimit': 41}, 
           1.0], 
          [{'type': 'box', 'westlimit': 170.0, 'eastlimit': 171.0, 'southlimit': 40, 'northlimit': 41}, 
           {'type': 'box', 'westlimit': 170.0, 'eastlimit': 170.5, 'southlimit': 40, 'northlimit': 40.5}, 
           1.0] 
        ]
        for n in stuff:
            result = geo_area_union(n[0], n[1])
            self.assertEqual(result, n[2])
