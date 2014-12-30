from zipfile import ZipFile
from cStringIO import StringIO

from django.contrib.gis.geos import Polygon
from lxml import etree
from . import Driver
from osgeo import osr
import re
from PIL import Image


class KmzDriver(Driver):
    @classmethod
    def supports_multiple_layers(cls):
        return False # should change to true if we can enable folder support down the road.

    @classmethod
    def supports_configuration(cls):
        return False

    def supports_point_query(cls):
        return False

    def supports_related(cls):
        return False

    def ready_data_resource(self, **kwargs):
        """Other keyword args get passed in as a matter of course, like BBOX, time, and elevation, but this basic driver
        ignores them"""

        slug, srs = super(KmzDriver, self).ready_data_resource(**kwargs)
        return slug, srs, {
            'type': 'kml',
            "file": self.get_filename('kmz')
        }

    def compute_fields(self, **kwargs):
        """Other keyword args get passed in as a matter of course, like BBOX, time, and elevation, but this basic driver
        ignores them"""

        super(KmzDriver, self).compute_fields(**kwargs)
        # archive = ZipFile(self.cached_basename + self.src_ext)

        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        self.resource.spatial_metadata.native_srs = srs.ExportToProj4()
        self.resource.spatial_metadata.bounding_box = Polygon.from_bbox((-180, -90, 180, 90))
        self.resource.spatial_metadata.native_bounding_box = Polygon.from_bbox((-180, -90, 180, 90))
        self.resource.spatial_metadata.three_d = False
        self.resource.spatial_metadata.save()
        self.resource.save()

    def open_stream(self, filename):
        archive = ZipFile(self.get_filename('kmz'))
        return archive.open(filename)

    def features(self):
        """Why do we change the namespace on this? because openlayers only knows about kml 2.0"""
        archive = ZipFile(self.get_filename('kmz'))
        with archive.open('doc.kml') as kml:
            kks = kml.read()
            kks = re.sub(r'"http://www.opengis.net/kml/[0-9]+.[0-9]+"', r'"http://www.opengis.net/kml/2.0"', kks)
            kks = re.sub(r'"http://www.google.com/kml/ext/[0-9]+.[0-9]+"', r'"http://www.google.com/kml/ext/2.0"', kks)
        return kks

    def ground_overlays(self):
        ground_overlays = []

        archive = ZipFile(self.get_filename('kmz'))

        on=False
        with archive.open('doc.kml') as kml:
            kml = StringIO(kml.read().replace('xsi:', "").replace('xmlns="', 'xmlnamespace="'))
            for event, elt in etree.iterparse(kml,events=['start','end'], remove_comments=True, remove_blank_text=True):
                print event, elt.tag
                if event == 'start':
                    if elt.tag == 'GroundOverlay':
                        ground_overlays.append({})
                        on = True
                    elif on and elt.tag in {'name', 'href'}:
                        ground_overlays[-1][elt.tag] = elt.text
                    elif on and elt.tag in {'west', 'east', 'north', 'south', 'rotation'}:
                        ground_overlays[-1][elt.tag] = float(elt.text)
                on = on and not (event == 'end' and elt.tag == 'GroundOverlay')

        # openlayers needs image dimensions right now.  should fix this in OL.
        for i, ol in enumerate(ground_overlays):
            ground_overlays[i]['width'], ground_overlays[i]['height'] = Image.open(StringIO(self.open_stream(ol['href']).read())).size


        return ground_overlays

    def summary(self, *args, **kwargs):
        return []

driver = KmzDriver
