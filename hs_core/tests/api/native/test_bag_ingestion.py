# -*- coding: utf-8 -*-
import os
import tempfile
import zipfile
from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.files.uploadedfile import UploadedFile
from rdflib import Graph
from rdflib.compare import _squashed_graphs_triples
from rdflib.namespace import DCTERMS, RDF

from hs_core import hydroshare
from hs_core.hydroshare import resource, add_resource_files, current_site_url
from hs_core.testing import MockIRODSTestCaseMixin
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

        self.test_bag_path = 'hs_core/tests/data/test_resource_metadata_files.zip'

        self.extracted_directory = 'hs_core/tests/data/test_resource_metadata_files/'
        from pathlib import Path

        def zip_up(ziph, root_directory, directory=""):
            full_path = Path(os.path.join(root_directory, directory))
            dirs = [str(item) for item in full_path.iterdir() if item.is_dir()]
            files = [str(item) for item in full_path.iterdir() if item.is_file()]
            for file in files:
                ziph.write(file, arcname=os.path.join(directory, os.path.basename(file)))
            for d in dirs:
                zip_up(ziph, root_directory, os.path.join(directory, os.path.basename(d)))

        zipf = zipfile.ZipFile(self.test_bag_path, 'w')
        zip_up(zipf, self.extracted_directory)

    def tearDown(self):
        super(TestCreateResource, self).tearDown()
        os.remove(self.test_bag_path)

    def test_bag_ingestion(self):
        from hs_core.views.utils import unzip_file

        def normalize_metadata(metadata_str):
            """Prepares metadata string to match resource id and hydroshare url of original"""
            return metadata_str\
                .replace(current_site_url(), "http://www.hydroshare.org")\
                .replace(res.short_id, "97523bdb7b174901b3fc2d89813458f1")

        # create empty resource
        res = resource.create_resource(
            'CompositeResource',
            self.user,
            'My Test Resource'
            )
        full_paths = {}

        files_to_upload = [UploadedFile(file=open('hs_core/tests/data/test_resource_metadata_files.zip', 'rb'),
                                        name="test_resource_metadata_files.zip")]
        add_resource_files(res.short_id, *files_to_upload, full_paths=full_paths)

        unzip_file(self.user, res.short_id, "data/contents/test_resource_metadata_files.zip", True,
                   overwrite=True, auto_aggregate=True, ingest_metadata=True)

        def compare_metadatas(new_metadata_str, original_metadata_file):
            original_graph = Graph()
            with open(os.path.join(self.extracted_directory, original_metadata_file), "r") as f:
                original_graph = original_graph.parse(data=f.read())
            new_graph = Graph()
            new_graph = new_graph.parse(data=normalize_metadata(new_metadata_str))

            # remove modified date, they'll never match
            subject = new_graph.value(predicate=RDF.type, object=DCTERMS.modified)
            new_graph.remove((subject, None, None))
            subject = original_graph.value(predicate=RDF.type, object=DCTERMS.modified)
            original_graph.remove((subject, None, None))

            for (new_triple, original_triple) in _squashed_graphs_triples(new_graph, original_graph):
                self.assertEquals(new_triple, original_triple, "Ingested resource metadata does not match original")

        res.refresh_from_db()
        compare_metadatas(res.metadata.get_xml(), "resourcemetadata.xml")

        compare_metadatas(res.get_logical_files(GenericLogicalFile.type_name())[0].metadata.get_xml(),
                          "test_meta.xml")
        compare_metadatas(res.get_logical_files(FileSetLogicalFile.type_name())[0].metadata.get_xml(),
                          "asdf/asdf_meta.xml")
        compare_metadatas(res.get_logical_files(GeoFeatureLogicalFile.type_name())[0].metadata.get_xml(),
                          "watersheds_meta.xml")
        compare_metadatas(res.get_logical_files(GeoRasterLogicalFile.type_name())[0].metadata.get_xml(),
                          "logan_meta.xml")
        compare_metadatas(res.get_logical_files(NetCDFLogicalFile.type_name())[0].metadata.get_xml(),
                          "SWE_time_meta.xml")
        compare_metadatas(res.get_logical_files(RefTimeseriesLogicalFile.type_name())[0].metadata.get_xml(),
                          "msf_version.refts_meta.xml")
        compare_metadatas(res.get_logical_files(TimeSeriesLogicalFile.type_name())[0].metadata.get_xml(),
                          "ODM2_Multi_Site_One_Variable_meta.xml")
        compare_metadatas(res.get_logical_files(ModelProgramLogicalFile.type_name())[0].metadata.get_xml(),
                          "setup_meta.xml")
        compare_metadatas(res.get_logical_files(ModelInstanceLogicalFile.type_name())[0].metadata.get_xml(),
                          "generic_file_meta.xml")

        compare_metadatas(res.get_logical_files(ModelProgramLogicalFile.type_name())[0].metadata.get_xml(),
                          "model_program/model_program_meta.xml")
        compare_metadatas(res.get_logical_files(ModelInstanceLogicalFile.type_name())[0].metadata.get_xml(),
                          "model_instance/model_instance_meta.xml")
