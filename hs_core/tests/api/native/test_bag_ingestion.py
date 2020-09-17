# -*- coding: utf-8 -*-
import os
import tempfile
import zipfile
import shutil
from unittest import TestCase

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import UploadedFile
from rdflib import Graph
from rdflib.compare import _squashed_graphs_triples

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
        self.extracted_directory = os.path.join(self.extracted_directory, 'test_resource_metadata_files')

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
        files_to_upload = []
        full_paths = {}
        # prepare files and metadata files to add to new resource
        for fd in os.listdir(self.extracted_directory):
            if os.path.isdir(os.path.join(self.extracted_directory, fd)):
                for f in os.listdir(os.path.join(self.extracted_directory, fd)):
                    file_to_upload = UploadedFile(file=open(os.path.join(self.extracted_directory, fd, f), 'rb'),
                                                  name=f)
                    files_to_upload.append(file_to_upload)
                    full_paths[file_to_upload] = os.path.join(fd, f)
            else:
                file_to_upload = UploadedFile(file=open(os.path.join(self.extracted_directory, fd), 'rb'), name=fd)
                files_to_upload.append(file_to_upload)
        add_resource_files(res.short_id, *files_to_upload, full_paths=full_paths)

        def compare_metadatas(new_metadata_str, original_metadata_file):
            original_graph = Graph()
            with open(os.path.join(self.extracted_directory, original_metadata_file), "r") as f:
                original_graph = original_graph.parse(data=f.read())
            new_graph = Graph()
            new_graph = new_graph.parse(data=normalize_metadata(new_metadata_str))
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
