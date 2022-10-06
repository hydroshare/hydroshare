# -*- coding: utf-8 -*-
import os
import zipfile
from unittest import TestCase

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from rdflib import Graph
from rdflib.namespace import DC
from rdflib.term import Literal

from hs_composite_resource.models import CompositeResource
from hs_core import hydroshare
from hs_core.hs_rdf import HSTERMS
from hs_core.models import Creator
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.tests.api.utils import zip_up


class TestIngestBag(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestIngestBag, self).setUp()

        self.hs_group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user
        self.user = hydroshare.create_account(
            'test_bag_ingestion@email.com',
            username='bag_ingestion_test',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[self.hs_group],
        )

        # delete all resources in case a test isn't cleaning up after itself
        CompositeResource.objects.all().delete()
        # TODO: Should we do this update or remove the 'hydroshare_user_id' attribute from
        #  the resourcemetadata.xml file?
        # need to update the resourcemetadata.xml test file for hydroshare_user_id to set this attribute to id of a
        # user that exists during this test
        res_id = 'd6c7a5744920404f8aceaf3c7774596e'
        self.res_meta_file_path = f"hs_core/tests/data/{res_id}/{res_id}/data/resourcemetadata.xml"
        graph_updated = False
        self.original_res_mata = ""
        with open(self.res_meta_file_path) as meta_file:
            self.original_res_meta = meta_file.read()
            graph = Graph().parse(data=self.original_res_meta)
            for s, _, _ in graph.triples((None, DC.creator, None)):
                subject = s
                break
            party_type = Creator.get_class_term()

            for party in graph.objects(subject=subject, predicate=party_type):
                for _, p, o in graph.triples((party, None, None)):
                    if p == HSTERMS.hydroshare_user_id:
                        graph.remove((party, p, o))
                        graph.add((party, p, Literal(self.user.id)))
                        graph_updated = True

        if graph_updated:
            with open(self.res_meta_file_path, 'w') as meta_file:
                meta_file.write(graph.serialize(format='hydro-xml').decode())
        else:
            self.original_meta = ""

        # zip up the test bag
        zipf = zipfile.ZipFile('hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e.zip', 'w')
        zip_up(zipf, 'hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e')

    def tearDown(self):
        super(TestIngestBag, self).tearDown()
        for res in CompositeResource.objects.all():
            res.delete()
        self.user.delete()
        self.hs_group.delete()
        os.remove('hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e.zip')
        # restore the original metadata for the test resourcemetadata.xml file
        if self.original_res_meta:
            with open(self.res_meta_file_path, 'w') as meta_file:
                meta_file.write(self.original_res_meta)

    def test_bag_ingestion_command(self):
        assert CompositeResource.objects.all().count() == 0
        call_command("ingest_bag", 'hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e.zip', user_id=str(self.user.id))
        assert CompositeResource.objects.all().count() == 1
        res = CompositeResource.objects.all().first()
        assert res.metadata.title.value == "czo res"
        assert res.files.all().count() == 1
        readme = res.files.all().first()
        assert readme.file_name == "README.md"

    def test_bag_ingestion_command_overwrite(self):
        assert CompositeResource.objects.all().count() == 0
        res = hydroshare.create_resource("CompositeResource", self.user, "To overwrite")
        call_command("ingest_bag", 'hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e.zip', user_id=str(self.user.id),
                     overwrite=True, resource_id=res.short_id)
        assert CompositeResource.objects.all().count() == 1
        res = CompositeResource.objects.all().first()
        assert res.metadata.title.value == "czo res"
        assert res.files.all().count() == 1
        readme = res.files.all().first()
        assert readme.file_name == "README.md"

    def test_bag_ingestion_command_overwrite_catch(self):
        res = hydroshare.create_resource("CompositeResource", self.user, "To overwrite")
        try:
            call_command("ingest_bag", 'hs_core/tests/data/d6c7a5744920404f8aceaf3c7774596e.zip',
                         user_id=str(self.user.id), resource_id=res.short_id)
            assert False, "should have thrown error"
        except ValidationError as e:
            assert f"Resource {res.short_id} exists, include the overwrite command or provide another resource_id." \
                   in str(e)
