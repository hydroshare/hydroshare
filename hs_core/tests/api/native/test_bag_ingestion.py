# -*- coding: utf-8 -*-
import os
import tempfile
from unittest import TestCase

from django.contrib.auth.models import Group
from rdflib import Graph, URIRef
from rdflib.compare import _squashed_graphs_triples
from rdflib.namespace import DCTERMS, RDF, DC

from hs_core import hydroshare
from hs_core.hs_rdf import HSTERMS
from hs_core.hydroshare import resource, current_site_url
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.tests.api.utils import prepare_resource as prepare_resource_util
from hs_file_types.models import (
    GenericLogicalFile,
    FileSetLogicalFile,
    GeoFeatureLogicalFile,
    GeoRasterLogicalFile,
    NetCDFLogicalFile,
    RefTimeseriesLogicalFile,
    TimeSeriesLogicalFile,
    ModelProgramLogicalFile,
    ModelInstanceLogicalFile,
    CSVLogicalFile,
)


def graph_len(g):
    """Returns the number of triples in an rdflib graph"""
    count = 0
    for _, _, _ in g.triples((None, None, None)):
        count = count + 1
    return count


def compare_metadatas(self, short_id, new_metadata_str, original_metadata_file):
    def normalize_metadata(metadata_str):
        """Prepares metadata string to match resource id and hydroshare url of original"""
        return metadata_str \
            .replace(current_site_url(), "http://www.hydroshare.org") \
            .replace(short_id, "97523bdb7b174901b3fc2d89813458f1")

    original_graph = Graph()
    with open(os.path.join(self.extracted_directory, original_metadata_file), "r") as f:
        original_graph = original_graph.parse(data=f.read())
    new_graph = Graph()
    print(new_metadata_str)
    new_graph = new_graph.parse(data=normalize_metadata(new_metadata_str))

    original_count = graph_len(original_graph)

    is_resource = new_graph.value(predicate=DC.type, object=URIRef("http://www.hydroshare.org/terms/CompositeResource"))
    if is_resource:
        # remove modified date, they'll never match
        modified_subject = new_graph.value(predicate=RDF.type, object=DCTERMS.modified)
        new_graph.remove((modified_subject, None, None))
        modified_subject = original_graph.value(predicate=RDF.type, object=DCTERMS.modified)
        original_graph.remove((modified_subject, None, None))
    else:
        # remove rights if it's an aggregation (rights is not ingested)
        new_graph.remove((None, HSTERMS.URL, None))
        new_graph.remove((None, HSTERMS.rightsStatement, None))

        original_graph.remove((None, HSTERMS.URL, None))
        original_graph.remove((None, HSTERMS.rightsStatement, None))

    # assert we only removed 2 triples
    self.assertEqual(graph_len(original_graph) + 2, original_count)
    self.assertEqual(graph_len(new_graph) + 2, original_count)

    for (new_triple, original_triple) in _squashed_graphs_triples(new_graph, original_graph):
        self.assertEquals(new_triple, original_triple, "Ingested metadata does not match original")


def prepare_resource(self, folder, upload_to=""):
    prepare_resource_util(folder, self.res, self.user, self.extracted_directory, self.test_bag_path, upload_to)


class TestIngestMetadata(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestIngestMetadata, self).setUp()

        self.tmp_dir = tempfile.mkdtemp()
        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_user@email.com',
            username='mytestuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group]
        )

        # create empty resource
        self.res = resource.create_resource(
            'CompositeResource',
            self.user,
            'My Test Resource'
        )

        self.test_bag_path = 'hs_core/tests/data/test_resource_metadata_files.zip'

        self.extracted_directory = 'hs_core/tests/data/test_resource_metadata_files/'

    def tearDown(self):
        super(TestIngestMetadata, self).tearDown()
        os.remove(self.test_bag_path)
        self.res.delete()
        self.user.delete()

    def test_nested_fileset_ingestion(self):
        prepare_resource(self, "fileset_nested")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(FileSetLogicalFile.type_name())[0].metadata.get_xml(),
                          "fileset_nested/fileset/fileset_meta.xml")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(GenericLogicalFile.type_name())[0].metadata.get_xml(),
                          "fileset_nested/fileset/singlefile_meta.xml")

    def test_modelinstance_ingestion_at_root(self):
        """Ingesting at root of the resource file path"""
        prepare_resource(self, "model_program")
        prepare_resource(self, "model_instance")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(ModelInstanceLogicalFile.type_name())[0].metadata.get_xml(),
                          "model_instance/generic_file_meta.xml")

    def test_modelinstance_ingestion_at_folder(self):
        """Ingesting at a folder of the resource"""
        prepare_resource(self, "model_program_folder", upload_to="model_program_folder")
        prepare_resource(self, "model_instance_folder", upload_to="model_instance_folder")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(ModelInstanceLogicalFile.type_name())[0].metadata.get_xml(),
                          "model_instance_folder/generic_file_meta.xml")

    def test_modelinstance_folder_ingestion(self):
        prepare_resource(self, "model_program_folder_based")
        prepare_resource(self, "model_instance_folder_based")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(ModelInstanceLogicalFile.type_name())[0].metadata.get_xml(),
                          "model_instance_folder_based/model_instance/model_instance_meta.xml")

    def test_modelprogram_ingestion_at_root(self):
        """Ingesting at root of the resource file path"""
        prepare_resource(self, "model_program")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(ModelProgramLogicalFile.type_name())[0].metadata.get_xml(),
                          "model_program/setup_meta.xml")

    def test_modelprogram_ingestion_at_folder(self):
        """Ingesting at a folder of the resource"""
        prepare_resource(self, "model_program_folder", upload_to="model_program_folder")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(ModelProgramLogicalFile.type_name())[0].metadata.get_xml(),
                          "model_program_folder/setup_meta.xml")

    def test_modelprogram_folder_ingestion(self):
        prepare_resource(self, "model_program_folder_based")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(ModelProgramLogicalFile.type_name())[0].metadata.get_xml(),
                          "model_program_folder_based/model_program/model_program_meta.xml")

    def test_timeseries_ingestion_at_root(self):
        """Ingesting at root of the resource file path"""
        prepare_resource(self, "timeseries")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(TimeSeriesLogicalFile.type_name())[0].metadata.get_xml(),
                          "timeseries/ODM2_Multi_Site_One_Variable_meta.xml")

    def test_timeseries_ingestion_at_folder(self):
        """Ingesting at a folder of the resource"""
        prepare_resource(self, "timeseries_folder", upload_to="timeseries_folder")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(TimeSeriesLogicalFile.type_name())[0].metadata.get_xml(),
                          "timeseries_folder/ODM2_Multi_Site_One_Variable_meta.xml")

    def test_netcdf_ingestion_at_root(self):
        """Ingesting at root of the resource file path"""
        prepare_resource(self, "netcdf")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(NetCDFLogicalFile.type_name())[0].metadata.get_xml(),
                          "netcdf/SWE_time_meta.xml")

    def test_netcdf_ingestion_at_folder(self):
        """Ingesting at a folder of the resource"""
        prepare_resource(self, "netcdf_folder", upload_to="netcdf_folder")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(NetCDFLogicalFile.type_name())[0].metadata.get_xml(),
                          "netcdf_folder/SWE_time_meta.xml")

    def test_geofeature_ingestion_at_root(self):
        prepare_resource(self, "geographic_feature")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(GeoFeatureLogicalFile.type_name())[0].metadata.get_xml(),
                          "geographic_feature/watersheds_meta.xml")

    def test_geofeature_ingestion_at_folder(self):
        prepare_resource(self, "geographic_feature_folder", upload_to="geographic_feature_folder")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(GeoFeatureLogicalFile.type_name())[0].metadata.get_xml(),
                          "geographic_feature_folder/watersheds_meta.xml")

    def test_resource_ingestion(self):
        prepare_resource(self, "resource")
        compare_metadatas(self, self.res.short_id, self.res.metadata.get_xml(), "resource/resourcemetadata.xml")

    def test_singlefile_ingestion_at_root(self):
        prepare_resource(self, "single_file")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(GenericLogicalFile.type_name())[0].metadata.get_xml(),
                          "single_file/test_meta.xml")

    def test_singlefile_ingestion_at_folder(self):
        prepare_resource(self, "single_file_folder", upload_to="single_file_folder")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(GenericLogicalFile.type_name())[0].metadata.get_xml(),
                          "single_file_folder/test_meta.xml")

    # write test for CSVLogicalFile

    def test_csv_ingestion_at_root(self):
        prepare_resource(self, "csv_file")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(CSVLogicalFile.type_name())[0].metadata.get_xml(),
                          "csv_file/csv_test_modified_meta.xml")
        self.assertEqual(CSVLogicalFile.objects.count(), 1)
        csv_logical_file = CSVLogicalFile.objects.first()
        self.assertGreater(len(csv_logical_file.preview_data.strip()), 0)

    def test_csv_ingestion_at_folder(self):
        prepare_resource(self, "csv_file_folder", upload_to="csv_file_folder")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(CSVLogicalFile.type_name())[0].metadata.get_xml(),
                          "csv_file_folder/csv_test_modified_meta.xml")
        self.assertEqual(CSVLogicalFile.objects.count(), 1)
        csv_logical_file = CSVLogicalFile.objects.first()
        self.assertGreater(len(csv_logical_file.preview_data.strip()), 0)

    def test_fileset_ingestion(self):
        prepare_resource(self, "file_set")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(FileSetLogicalFile.type_name())[0].metadata.get_xml(),
                          "file_set/asdf/asdf_meta.xml")

    def test_georaster_ingestion_to_root(self):
        """Ingesting at root of the resource file path"""
        prepare_resource(self, "geographic_raster")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(GeoRasterLogicalFile.type_name())[0].metadata.get_xml(),
                          "geographic_raster/logan_meta.xml")

    def test_georaster_ingestion_to_folder(self):
        """Ingesting at a folder of the resource"""
        prepare_resource(self, "geographic_raster_folder", upload_to="geographic_raster_folder")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(GeoRasterLogicalFile.type_name())[0].metadata.get_xml(),
                          "geographic_raster_folder/logan_meta.xml")

    def test_reftimeseries_ingestion_at_root(self):
        prepare_resource(self, "reference_timeseries")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(RefTimeseriesLogicalFile.type_name())[0].metadata.get_xml(),
                          "reference_timeseries/msf_version.refts_meta.xml")

    def test_reftimeseries_ingestion_at_folder(self):
        prepare_resource(self, "reference_timeseries_folder", upload_to="reference_timeseries_folder")
        compare_metadatas(self, self.res.short_id,
                          self.res.get_logical_files(RefTimeseriesLogicalFile.type_name())[0].metadata.get_xml(),
                          "reference_timeseries_folder/msf_version.refts_meta.xml")
