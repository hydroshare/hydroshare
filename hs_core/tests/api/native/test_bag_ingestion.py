# -*- coding: utf-8 -*-
import os
import tempfile
import zipfile
import shutil
from unittest import TestCase

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import UploadedFile
from rdflib import Graph, URIRef
from rdflib.compare import _squashed_graphs_triples
from rdflib.namespace import DCTERMS, RDF

from hs_composite_resource.models import CompositeResource
from hs_core.hydroshare import resource, add_resource_files, current_site_url
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core import hydroshare
from hs_file_types.models import GenericLogicalFile, FileSetLogicalFile, GeoFeatureLogicalFile, GeoRasterLogicalFile, \
    NetCDFLogicalFile, RefTimeseriesLogicalFile


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
        self.extracted_directory = "temp"

        with zipfile.ZipFile(self.test_bag_path, 'r') as zip_ref:
            zip_ref.extractall(self.extracted_directory)

    def tearDown(self):
        super(TestCreateResource, self).tearDown()

        shutil.rmtree(self.tmp_dir)

        self.user.uaccess.delete()
        self.user.delete()
        self.hs_group.delete()

        User.objects.all().delete()
        Group.objects.all().delete()
        CompositeResource.objects.all().delete()

        shutil.rmtree(self.extracted_directory)

    def test_bag_ingestion(self):
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

        files_to_upload = [UploadedFile(file=open(self.test_bag_path, 'rb'),
                                        name="test_resource_metadata_files.zip")]
        add_resource_files(res.short_id, *files_to_upload, full_paths=full_paths)
        from hs_core.views.utils import unzip_file

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
            # remove RDF.type for resource, this was newly added
            new_graph.remove((None, RDF.type, URIRef("http://hydroshare.org/terms/resource")))
            subject = original_graph.value(predicate=RDF.type, object=DCTERMS.modified)
            original_graph.remove((subject, None, None))

            for (new_triple, original_triple) in _squashed_graphs_triples(new_graph, original_graph):
                self.assertEquals(new_triple, original_triple, "Ingested resource metadata does not match original")

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
