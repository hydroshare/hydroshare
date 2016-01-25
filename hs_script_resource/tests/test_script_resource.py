__author__ = 'shawn'

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import Group, User
from django.http import HttpRequest, QueryDict

from hs_core.hydroshare import resource
from hs_core import hydroshare

from hs_script_resource.models import ScriptSpecificMetadata, ScriptResource
from hs_script_resource.receivers import script_pre_create, script_metadata_pre_create_handler, script_metadata_pre_update_handler


class TestScriptResource(TransactionTestCase):

    def setUp(self):
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
                'scrawley@byu.edu',
                username='scrawley',
                first_name='Shawn',
                last_name='Crawley',
                superuser=False,
                groups=[self.group]
        )
        self.allowance = 0.00001

        self.resScript = hydroshare.create_resource(
                resource_type='ScriptResource',
                owner=self.user,
                title='Test R Script Resource',
                keywords=['kw1', 'kw2']
        )

    def test_script_res_specific_metadata(self):

        #######################
        # Class: ScriptSpecificMetadata
        #######################
        # no ScriptSpecificMetadata obj
        self.assertEqual(ScriptSpecificMetadata.objects.all().count(), 0)

        # create 1 ScriptSpecificMetadata obj with required params
        resource.create_metadata_element(self.resScript.short_id, 'ScriptSpecificMetadata', scriptLanguage='R',
                                         languageVersion='3.5', scriptVersion='1.0',
                                         scriptDependencies='None', scriptReleaseDate='2015-12-01 00:00',
                                         scriptCodeRepository='http://www.google.com')
        self.assertEqual(ScriptSpecificMetadata.objects.all().count(), 1)

        # may not create additional instance of ScriptSpecificMetadata
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.resScript.short_id, 'ScriptSpecificMetadata', scriptLanguage='R',
                                             languageVersion='3.5', scriptVersion='1.0',
                                             scriptDependencies='None', scriptReleaseDate='12/01/2015',
                                             scriptCodeRepository='http://www.google.com')

        self.assertEqual(ScriptSpecificMetadata.objects.all().count(), 1)

        # update existing meta
        resource.update_metadata_element(self.resScript.short_id, 'ScriptSpecificMetadata',
                                         element_id=ScriptSpecificMetadata.objects.first().id,
                                         scriptLanguage='python',
                                         languageVersion='2.7')
        self.assertEqual(ScriptSpecificMetadata.objects.first().scriptLanguage, 'python')
        self.assertEqual(ScriptSpecificMetadata.objects.first().languageVersion, '2.7')

        # delete ScriptSpecificMetadata obj
        resource.delete_metadata_element(self.resScript.short_id, 'ScriptSpecificMetadata',
                                         element_id=ScriptSpecificMetadata.objects.first().id)
        self.assertEqual(ScriptSpecificMetadata.objects.all().count(), 0)

    def test_receivers(self):
        request = HttpRequest()

        # ScriptSpecificMetadata
        request.POST = {'scriptLanguage': 'R', 'languageVersion': '3.5'}

        data = script_metadata_pre_create_handler(sender=ScriptResource,
                                                  element_name="ScriptSpecificMetadata",
                                                  request=request)
        self.assertTrue(data["is_valid"])

        request.POST = None

        data = script_metadata_pre_create_handler(sender=ScriptResource,
                                                  element_name="ScriptSpecificMetadata",
                                                  request=request)
        self.assertFalse(data["is_valid"])

        data = script_pre_create(sender=ScriptResource,
                                 metadata=[],
                                 files=None)

        self.assertEqual(data[0]['scriptspecificmetadata'], {})

        request.POST = {'scriptLanguage': 'R', 'languageVersion': '3.5'}

        data = script_metadata_pre_update_handler(sender=ScriptResource,
                                                  element_name="ScriptSpecificMetadata",
                                                  request=request)

        self.assertTrue(data["is_valid"])

        request.POST = None

        data = script_metadata_pre_update_handler(sender=ScriptResource,
                                                  element_name="ScriptSpecificMetadata",
                                                  request=request)

        self.assertFalse(data["is_valid"])
