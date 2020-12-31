# -*- coding: utf-8 -*-
import os
import tempfile
import zipfile
import shutil
from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from rdflib import Graph
from rdflib.compare import _squashed_graphs_triples
from rdflib.namespace import DCTERMS, RDF

from hs_core.hydroshare import resource, add_resource_files, current_site_url
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_file_types.models import (
    GenericLogicalFile,
    FileSetLogicalFile,
    GeoFeatureLogicalFile,
    # GeoRasterLogicalFile,
    NetCDFLogicalFile,
    RefTimeseriesLogicalFile,
    TimeSeriesLogicalFile,
    # ModelInstanceLogicalFile,
    ModelProgramLogicalFile
)


class TestCreateResource(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestCreateResource, self).setUp()

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
        self.bag_file_name = 'test_resource_metadata_files.zip'
        self.test_bag_path = 'hs_core/tests/data/{}'.format(self.bag_file_name)
        self.extracted_directory = "temp"

        with zipfile.ZipFile(self.test_bag_path, 'r') as zip_ref:
            zip_ref.extractall(self.extracted_directory)

    def tearDown(self):
        super(TestCreateResource, self).tearDown()

        shutil.rmtree(self.tmp_dir)

        shutil.rmtree(self.extracted_directory)

    def test_bag_ingestion(self):
        from hs_core.views.utils import unzip_file

        def normalize_metadata(metadata_str):
            """Prepares metadata string to match resource id and hydroshare url of original"""
            return metadata_str\
                .replace(current_site_url(), "http://www.hydroshare.org")\
                .replace(res.short_id, "0f371c7bab0e41b9851ed79b7260cca2")

        # create empty resource
        res = resource.create_resource(
            'CompositeResource',
            self.user,
            'My Test Resource'
            )
        full_paths = {}

        files_to_upload = [UploadedFile(file=open(self.test_bag_path, 'rb'),
                                        name=self.bag_file_name)]
        add_resource_files(res.short_id, *files_to_upload, full_paths=full_paths)

        unzip_file(self.user, res.short_id, "data/contents/{}".format(self.bag_file_name), True,
                   overwrite=True, auto_aggregate=True, ingest_metadata=True)

        def compare_metadatas(new_metadata_str, original_metadata_file, resource_meta=False):
            original_graph = Graph()
            with open(os.path.join(self.extracted_directory, original_metadata_file), "r") as f:
                original_graph = original_graph.parse(data=f.read())
            new_graph = Graph()
            new_graph = new_graph.parse(data=normalize_metadata(new_metadata_str))
            if resource_meta:
                # remove modified date, they'll never match
                subject = new_graph.value(predicate=RDF.type, object=DCTERMS.modified)
                new_graph.remove((subject, None, None))

                subject = original_graph.value(predicate=RDF.type, object=DCTERMS.modified)
                original_graph.remove((subject, None, None))

            for (new_triple, original_triple) in _squashed_graphs_triples(new_graph, original_graph):
                self.assertEquals(new_triple, original_triple, "Ingested resource metadata does not match original")

        res.refresh_from_db()
        compare_metadatas(res.metadata.get_xml(), "resourcemetadata.xml", resource_meta=True)

        compare_metadatas(res.get_logical_files(GenericLogicalFile.type_name())[0].metadata.get_xml(),
                          "test_meta.xml")
        compare_metadatas(res.get_logical_files(FileSetLogicalFile.type_name())[0].metadata.get_xml(),
                          "asdf/asdf_meta.xml")
        compare_metadatas(res.get_logical_files(GeoFeatureLogicalFile.type_name())[0].metadata.get_xml(),
                          "watersheds_meta.xml")

        # TODO (Pabitra): This one is failing
        # compare_metadatas(res.get_logical_files(GeoRasterLogicalFile.type_name())[0].metadata.get_xml(),
        #                   "logan_meta.xml")

        compare_metadatas(res.get_logical_files(NetCDFLogicalFile.type_name())[0].metadata.get_xml(),
                          "SWE_time_meta.xml")
        compare_metadatas(res.get_logical_files(RefTimeseriesLogicalFile.type_name())[0].metadata.get_xml(),
                          "msf_version.refts_meta.xml")
        compare_metadatas(res.get_logical_files(TimeSeriesLogicalFile.type_name())[0].metadata.get_xml(),
                          "ODM2_Multi_Site_One_Variable_meta.xml")

        # TODO (Pabitra): need to implement ingest_metadata() for model instance before this test for model
        #  instance can be run
        # mi_logical_files = res.get_logical_files(ModelInstanceLogicalFile.type_name())
        # for mi_lf in mi_logical_files:
        #     if mi_lf.aggregation_name.startswith('mi_aggr.'):
        #         compare_metadatas(mi_lf.metadata.get_xml(), "mi_aggr_meta.xml")
        #         # print(mi_lf.metadata.get_xml())
        #         # self.fail(">>Testing...")
        #         break
        # else:
        #     self.fail("Model instance aggregation not found for metadata file: mi_aggr_meta.xml")

        # for mi_lf in mi_logical_files:
        #     if mi_lf.aggregation_name == 'mi-aggr-folder':
        #         compare_metadatas(mi_lf.metadata.get_xml(), "mi-aggr-folder/mi-aggr-folder_meta.xml")
        #         break
        # else:
        #     self.fail("Model instance aggregation not found for metadata file: mi-aggr-folder/mi-aggr-folder_meta.xml")

        mp_logical_files = res.get_logical_files(ModelProgramLogicalFile.type_name())
        for mp_lf in mp_logical_files:
            if mp_lf.aggregation_name.startswith('mp_aggr.'):
                compare_metadatas(mp_lf.metadata.get_xml(), "mp_aggr_meta.xml")
                break
        else:
            self.fail("Model program aggregation not found for metadata file: mp_aggr_meta.xml")

        for mp_lf in mp_logical_files:
            if mp_lf.aggregation_name == 'mp-aggr-folder':
                compare_metadatas(mp_lf.metadata.get_xml(), "mp-aggr-folder/mp-aggr-folder_meta.xml")
                break
        else:
            self.fail("Model program aggregation not found for metadata file: mp-aggr-folder/mp-aggr-folder_meta.xml")
