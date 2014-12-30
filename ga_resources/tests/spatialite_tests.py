from unittest import TestCase

from . import utils
from ga_resources.drivers.spatialite import SpatialiteDriver
from ga_resources.models import DataResource
from osgeo import osr
import pandas
from shapely.wkt import geom_from_wkt


#@skip
class SpatialiteTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds = utils.load_example_dataset_from_filesystem()

    @classmethod
    def tearDownClass(cls):
        for o in DataResource.objects.all():
            o.delete()

    def test_spatial_metadata(self):
        self.assertIsNotNone(self.ds.native_srs)
        self.assertIsNotNone(self.ds.native_bounding_box)
        self.assertIsNotNone(self.ds.bounding_box)

        self.assertIsInstance(self.ds.srs, osr.SpatialReference)

    def test_driver_basics(self):
        self.assertIsNotNone(self.ds.resource)

    def test_dataframe(self):
        df = self.ds.resource.as_dataframe()

        self.assertIsNotNone(df)
        self.assertIsInstance(df, pandas.DataFrame, msg='dataframe is wrong type {df}'.format(df=type(df)))
        self.assertGreaterEqual(df.shape[0], 100, msg='shape of dataframe is wrong: {shape}'.format(shape=df.shape))

    def test_summary(self):
        summary = self.ds.resource.summary()
        self.assertIsNotNone(summary)

    def test_add_column(self):
        self.ds.resource.add_column('new_column', 'TEXT')
        self.assertIn('new_column', self.ds.resource.schema())

    def test_get_row(self):
        row = self.ds.resource.get_row(1, geometry_format='geojson')
        wkt_row = self.ds.resource.get_row(1, geometry_format='wkt')
        self.assertIn('objectid_1', row, msg='missing first key from row: {k}'.format(k=row.keys()))
        self.assertIn('shape_area', row, msg='missing last key from row: {k}'.format(k=row.keys()))
        self.assertIn('GEOMETRY', row, msg='missing geometry field: {k} '.format(k=row.keys()))
        self.assertIsInstance(
            row['shape_area'], float,
            msg='shape_area should be a float, is a {t}'.format(t=type(row['shape_area'])))
        self.assertIsInstance(
            row['objectid'], int,
            msg='objectid should be an int, is a {t}'.format(t=type(row['objectid'])))
        self.assertIsInstance(
            row['county'], basestring,
            msg='county should be a string, is a {t}'.format(t=type(row['county'])))
        self.assertIsInstance(
            row['ck_date'], basestring,
            msg='ck_date should be a date string, is a {t}'.format(t=type(row['ck_date'])))
        self.assertIsInstance(
            row['GEOMETRY'], dict,
            msg='geometry should be an instance of dict')
        self.assertIsInstance(
            wkt_row['GEOMETRY'], basestring,
            msg='geometry should be in instance of basestring in wkt_row')


    def test_get_data_for_point(self):
        row = self.ds.resource.get_row(1, geometry_format='geojson')
        x, y = row['GEOMETRY']['coordinates'][0][0]
        s_srs = self.ds.srs
        t_srs = osr.SpatialReference()
        t_srs.ImportFromEPSG(4326)
        crx = osr.CoordinateTransformation(s_srs, t_srs)
        x1, y1, _ = crx.TransformPoint(x, y)

        native_pt = self.ds.resource.get_data_for_point(x, y, self.ds.srs, 0)
        transformed_pt = self.ds.resource.get_data_for_point(x1, y1, t_srs, 0)

        self.assertIsNotNone(native_pt, msg='native point was null')
        self.assertIsNotNone(transformed_pt, msg='transformed point was null')

        print native_pt

        self.assertEqual(
            native_pt[0]['objectid'], row['objectid'],
            msg='native point brought back a different row: {OGC_FID}'.format(**native_pt[0]))
        self.assertEqual(
            transformed_pt[0]['objectid'], row['objectid'],
            msg='transformed point brought back different row: {OGC_FID}'.format(**transformed_pt[0]))

        self.ds.resource.get_data_for_point(0, 0, self.ds.srs, 0) # shouldn't throw an exception just because we don't get data

    def test_get_rows(self):
        rc1_10 = self.ds.resource.get_rows(ogc_fid_start=1, ogc_fid_end=10, limit=None, geometry_format='wkt')
        rc91_100 = self.ds.resource.get_rows(ogc_fid_start=91, ogc_fid_end=100, limit=None, geometry_format='wkt')
        rc98 = self.ds.resource.get_rows(ogc_fid_start=98, ogc_fid_end=98, limit=None, geometry_format='wkt')
        rc98_102 = self.ds.resource.get_rows(ogc_fid_start=98, ogc_fid_end=102, limit=None, geometry_format='wkt')
        rc0_L100 = self.ds.resource.get_rows(ogc_fid_start=0, ogc_fid_end=None, limit=100, geometry_format='wkt')

        self.assertEqual(len(rc1_10), 10, msg='length should be 10, was {len}'.format(len=len(rc1_10)))
        self.assertEqual(len(rc91_100), 10, msg='length should be 10, was {len}'.format(len=len(rc91_100)))
        self.assertEqual(rc91_100[0]['OGC_FID'], 91, msg='first record should have been record 91, was {rec}'.format(rec=rc91_100[0]['OGC_FID']))
        self.assertEqual(len(rc98), 1, msg='length should be 1, was {len}'.format(len=len(rc98)))
        self.assertGreaterEqual(len(rc98_102), 2, msg='length should be 2, was {len}'.format(len=len(rc98_102)))
        self.assertEqual(len(rc0_L100), 100, msg='length should be 100, was {len}'.format(len=len(rc0_L100)))


    def test_eq(self):
        alamance = self.ds.resource.query(county__eq='Alamance')
        self.assertIsNotNone(alamance, msg='Query on "Alamance" returned None')
        self.assertEqual(len(alamance), 1, msg='Query on "Alamance" returned 0 results')
        self.assertEqual(
            alamance[0]['county'], 'Alamance',
            msg="Query on 'Alamance' returned {c}".format(c=alamance[0]['county'])
        )

    def test_like(self):
        als1 = self.ds.resource.query(county__like='Al%')

        self.assertIsNotNone(als1, msg='Query on "Alamance" returned None')
        self.assertListEqual(
            sorted([a['county'] for a in als1]),
            ['Alamance','Alexander','Alleghany'],
            msg='Query on "Al" should return 3 counties, returned {a}'.format(a=[x['county'] for x in als1])
        )

    def test_startswith(self):
        als2 = self.ds.resource.query(county__startswith='Al')

        self.assertIsNotNone(als2, msg='Query on "Alamance" returned None')
        self.assertGreater(len(als2), 0, msg='startswith Query on "Alamance" returned 0 results')
        self.assertListEqual(
            sorted([a['county'] for a in als2]),
            ['Alamance', 'Alexander', 'Alleghany'],
            msg='startswith Query on "Al" should return 3 counties, returned {a}'.format(a=[x['county'] for x in als2])
        )

    def test_endswith(self):
        ons = self.ds.resource.query(county__endswith='ell')

        self.assertIsNotNone(ons, msg='Query on "ell$" returned None')
        self.assertGreater(len(ons), 0, msg='Query on "ell$" returned 0 results')
        self.assertListEqual(
            sorted([a['county'] for a in ons]),
            ['Caldwell', 'Caswell', 'Iredell', 'Mcdowell','Mitchell','Tyrrell'],
            msg='Query on "ell" should return 6 counties, returned {a}'.format(a=[x['county'] for x in ons])
        )

    def test_contains(self):
        als3 = self.ds.resource.query(county__contains='lamanc')

        self.assertIsNotNone(als3, msg='contains Query on "Alamance" returned None')
        self.assertGreater(len(als3), 0, msg='contains Query on "Alamance" returned 0 results')
        self.assertListEqual(
            sorted([a['county'] for a in als3]),
            ['Alamance'],
            msg='Contains Query on "lamanc" should return Alamanace, returned {a}'.format(a=[x['county'] for x in als3])
        )

    def test_lt(self):
        fid1 = self.ds.resource.query(OGC_FID__lt=2)

        self.assertIsNotNone(fid1, msg='Query on OGC_FID<2 returned None')
        self.assertEqual(len(fid1), 1, msg='Query on OGC_FID<2 returned {n} results'.format(n=len(fid1)))
        self.assertEqual(
            fid1[0]['OGC_FID'], 1,
            msg="Query on 'OGC_FID<2' returned {c}".format(c=fid1[0]['county'])
        )

    def test_gt(self):
        fid100 = self.ds.resource.query(OGC_FID__gt=99)

        self.assertIsNotNone(fid100, msg='Query on OGC_FID>99 returned None')
        self.assertEqual(len(fid100), 1, msg='Query on OGC_FID>99 returned {n} results'.format(n=len(fid100)))
        self.assertEqual(
            fid100[0]['OGC_FID'], 100,
            msg="Query on 'OGC_FID>99' returned {c}".format(c=fid100[0]['county'])
        )

    def test_le(self):
        fid1_ = self.ds.resource.query(OGC_FID__le=1)
        self.assertIsNotNone(fid1_, msg='Query on OGC_FID<=1 returned None')
        self.assertEqual(len(fid1_), 1, msg='Query on OGC_FID<=1 returned {n} results'.format(n=len(fid1_)))
        self.assertEqual(
            fid1_[0]['OGC_FID'], 1,
            msg="Query on 'OGC_FID<=1' returned {c}".format(c=fid1_[0]['county'])
        )

    def test_ge(self):
        fid100_ = self.ds.resource.query(OGC_FID__ge=100)
        self.assertIsNotNone(fid100_, msg='Query on OGC_FID>99 returned None')
        self.assertEqual(len(fid100_), 1, msg='Query on OGC_FID>99 returned {n} results'.format(n=len(fid100_)))
        self.assertEqual(
            fid100_[0]['OGC_FID'], 100,
            msg="Query on 'OGC_FID>=100' returned {c}".format(c=fid100_[0]['county'])
        )

    def test_none(self):
        is_none = self.ds.resource.query(OGC_FID__eq=0)
        self.assertEqual(len(is_none), 0, msg='Query on "OGC_FID=0" returned {is_none}'.format(is_none=is_none))

    def test_regexp(self):
        alamance_regexp = self.ds.resource.query(county__regexp='.lamance')
        self.assertIsNotNone(alamance_regexp, msg='Query on ".lamance" returned None')
        self.assertGreater(len(alamance_regexp), 0, msg='Query on ".lamance" returned 0 results')
        self.assertEqual(
            alamance_regexp[0]['county'], 'Alamance',
            msg="Query on '.lamance' returned {c}".format(c=alamance_regexp[0]['county'])
        )

    def test_glob(self):
        alamance_glob = self.ds.resource.query(county__glob='?lamance')
        self.assertIsNotNone(alamance_glob, msg='Query on "?lamance" returned None')
        self.assertGreater(len(alamance_glob), 0, msg='Query on "?lamance" returned 0 results')
        self.assertEqual(
            alamance_glob[0]['county'], 'Alamance', 
            msg="Query on '?lamance' returned {c}".format(c=alamance_glob[0]['county'])
        )

    def test_only_county(self):
        only_county = self.ds.resource.query(only=['county'])
        self.assertIsNotNone(only_county, msg='Query on only county returned None')
        self.assertGreater(len(only_county), 0, msg='Query on only county returned 0 results')
        self.assertEqual(
            len(only_county[0].keys()), 1,
            msg="Query on only county returned {c}".format(c=only_county[0].keys())
        )

    def test_limit_10(self):
        limit_10 = self.ds.resource.query(limit=10)
        self.assertIsNotNone(limit_10, msg='Query on "limit 10" returned None')
        self.assertGreater(len(limit_10), 0, msg='Query on "limit 10" returned 0 results')
        self.assertEqual(
            len(limit_10), 10,
            msg="Query on 'Alamance' returned {c}".format(c=limit_10[0]['county'])
        )

    def test_start_10(self):
        start_10 = self.ds.resource.query(start=10, limit=10)
        self.assertIsNotNone(start_10, msg='Query on "start 10" returned None')
        self.assertGreater(len(start_10), 0, msg='Query on "start 10" returned 0 results')
        self.assertEqual(
            start_10[0]['OGC_FID'], 10,
            msg="Query on start 10 returned {c}".format(c=start_10[0]['OGC_FID'])
        )


    def test_end_100(self):
        end_100 = self.ds.resource.query(start=90, end=100)
        self.assertIsNotNone(end_100, msg='Query on "end 100" returned None')
        self.assertGreater(len(end_100), 0, msg='Query on "end 100" returned 0 results')
        self.assertEqual(
            end_100[-1]['OGC_FID'], 100,
            msg="Query on end 100 returned {c}".format(c=end_100[-1]['OGC_FID'])
        )


    def test_geometry_query(self):
        row = self.ds.resource.get_row(1, geometry_format='wkt')
        geom = row['GEOMETRY']

        geom_only = self.ds.resource.query(query_geometry=geom, geometry_operator='intersects')
        self.assertGreaterEqual(len(geom_only), 1, msg='no results from the geometry query')


    def test_mbr_query(self):
        row = self.ds.resource.get_row(1, geometry_format='wkt')
        geom = geom_from_wkt(row['GEOMETRY'])
        box = geom.bounds

        box_only = self.ds.resource.query(query_mbr=box)
        self.assertGreaterEqual(len(box_only), 1, msg='no results from the following query: {box}'.format(box=box))

        exact_record = self.ds.resource.query(query_mbr=box, objectid__eq=row['objectid'])
        self.assertEqual(len(exact_record), 1, msg='exact record query returned {n} records'.format(n=len(exact_record)))
        self.assertEqual(exact_record[0]['objectid'], row['objectid'], msg='exact record query returned the wrong record {n}'.format(n=exact_record[0]['objectid']))

    def test_distance_query(self):
        row1 = self.ds.resource.get_row(1, geometry_format='wkt')
        row2 = self.ds.resource.get_row(2, geometry_format='wkt')
        g1 = geom_from_wkt(row1['GEOMETRY'])
        g2 = geom_from_wkt(row2['GEOMETRY']).centroid
        min_d = g2.distance(g1)
        should_be_row1 = self.ds.resource.query(
            geometry_operator='distance:ge:-1:{d}:{wkt}'.format(d=min_d, wkt=g2.wkt),
            objectid__eq=row1['objectid'],
        )
        objects = self.ds.resource.query(
            geometry_operator='distance:ge:-1:{d}:{wkt}'.format(d=min_d, wkt=g2.wkt)
        )

        self.assertEqual(len(should_be_row1), 1, msg='limited query should have returned one row, returned {n}'.format(n=len(should_be_row1)))
        self.assertEqual(should_be_row1[0]['objectid'], 1, msg='limited query should have returned FID 1, returned {n}'.format(n=should_be_row1[0]['objectid']))
        self.assertGreaterEqual(len(objects), 1, msg='unlimited query returned only one object. should have returned several')


    def test_schema(self):
        schema = self.ds.resource.schema()
        row = self.ds.resource.get_row(1).keys()
        self.assertListEqual(sorted(schema), sorted(row), msg='schema: \n{schema}\nrow:\n{row}'.format(**locals()))

    def test_derive_dataset(self):
        ds2 = SpatialiteDriver.derive_dataset('derived dataset',self.ds, self.ds)
        self.assertIsInstance(ds2, DataResource)

        rs = ds2.resource.get_rows(1, 100, geometry_format='wkt')
        self.assertEqual(len(rs), 100, 'derived dataset length {n}. should have been 100'.format(n=len(rs)))


    def test_create_dataset(self):
        ds2 = SpatialiteDriver.create_dataset('created dataset', columns_definitions=(
            ('name', "TEXT"),
            ('i' , 'INTEGER'),
            ('j' , "REAL"),
        ))
        ds3 = SpatialiteDriver.create_dataset('created empty dataset')

        self.assertListEqual(['OGC_FID', 'GEOMETRY','name','i','j'], ds2.resource.schema(),
             'empty dataset with four columns should have had four columns, but had {schema}'.format(
                 schema=ds2.resource.schema()))
        self.assertListEqual(['OGC_FID', 'GEOMETRY'], ds3.resource.schema(),
             'empty dataset schema should have had nothing in it, had {schema}'.format(schema=ds3.resource.schema()))

        ds3.resource.add_column('name', 'TEXT')
        ds3.resource.add_column('i', 'TEXT')
        ds3.resource.add_column('j', 'TEXT')

        self.assertListEqual(ds3.resource.schema(), ['OGC_FID', 'GEOMETRY','name','i','j'],
             "added columns, but they didn't show up right: {schema}".format(schema=ds3.resource.schema()))

    def test_create_dataset_with_parent_geometry(self):
        ds2 = SpatialiteDriver.create_dataset_with_parent_geometry(
            'geometry derived dataset',
            self.ds,
            columns_definitions=(('name', 'TEXT'), ('i', 'INTEGER'), ('j', 'REAL'))
        )
        ds3 = SpatialiteDriver.create_dataset_with_parent_geometry(
            'geometry dervied dataset 2',
            self.ds
        )
        self.assertListEqual(['OGC_FID', 'GEOMETRY', 'name', 'i', 'j'], ds2.resource.schema(),
                             'empty dataset with three columns should have had three columns, but had {schema}'.format(
                                 schema=ds2.resource.schema()))
        self.assertListEqual(['OGC_FID', 'GEOMETRY'], ds3.resource.schema(),
                             'empty dataset schema should have had nothing in it, had {schema}'.format(
                                 schema=ds3.resource.schema()))

        ds3.resource.add_column('name', 'TEXT')
        ds3.resource.add_column('i', 'TEXT')
        ds3.resource.add_column('j', 'TEXT')

        self.assertListEqual(ds3.resource.schema(), ['OGC_FID', 'GEOMETRY', 'name', 'i', 'j'],
                             "added columns, but they didn't show up right: {schema}".format(schema=ds3.resource.schema()))

    def test_update_row(self):
        ds2 = SpatialiteDriver.create_dataset('update test dataset', columns_definitions=(
            ('name', "TEXT"),
            ('i', 'INTEGER'),
            ('j', "REAL"),
        ))
        ds2.resource.add_row(name='jeff',i=1,j=2.0, GEOMETRY='POINT(0 0)')
        ds2.resource.update_row(1, name='jeff heard')
        row = ds2.resource.get_row(1)

        self.assertEqual(row['name'], 'jeff heard', msg='update should have changed name, but name was {name}'.format(
            name=row['name']
        ))

    def test_delete_row(self):
        ds2 = SpatialiteDriver.create_dataset('update test dataset', columns_definitions=(
            ('name', "TEXT"),
            ('i', 'INTEGER'),
            ('j', "REAL"),
        ))
        ds2.resource.add_row(name='jeff', i=1, j=2.0, GEOMETRY='POINT(0 0)')
        row = ds2.resource.get_row(1)
        rs = ds2.resource.get_rows(1, limit=100)

        self.assertEqual(len(rs), 1, msg='add row failed.  length was (n).'.format(
            n=len(rs)
        ))

        ds2.resource.delete_row(1)
        rs = ds2.resource.get_rows(1, limit=100)

        self.assertEqual(len(rs), 0, msg='delete row should have deleted the row but didnt.  length was (n).'.format(
            n=len(rs)
        ))

    def test_add_row(self):
        ds2 = SpatialiteDriver.create_dataset('update test dataset', columns_definitions=(
            ('name', "TEXT"),
            ('i', 'INTEGER'),
            ('j', "REAL"),
        ))
        ds2.resource.add_row(name='jeff', i=1, j=2.0, GEOMETRY='POINT(0 0)')
        row = ds2.resource.get_row(1)

        self.assertEqual(row['name'], 'jeff', msg='add should have added jeff, but name was {name}'.format(
            name=row['name']
        ))






