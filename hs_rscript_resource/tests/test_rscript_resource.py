__author__ = 'shawn'

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import Group, User
from django.http import HttpRequest, QueryDict

from hs_core.hydroshare import resource
from hs_core import hydroshare

from hs_rscript_resource.models import RSMetadata, RScriptResource
from hs_rscript_resource.receivers import rs_pre_trigger, metadata_element_pre_create_handler, rs_pre_update_handler


class TestRScriptResource(TransactionTestCase):

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

        self.resRScript = hydroshare.create_resource(
                resource_type='RScriptResource',
                owner=self.user,
                title='Test R Script Resource',
                keywords=['kw1', 'kw2']
        )

    def test_rscript_res_specific_metadata(self):

        #######################
        # Class: RSMetadata
        #######################
        # no RSMetadata obj
        self.assertEqual(RSMetadata.objects.all().count(), 0)

        # create 1 RSMetadata obj with required params
        resource.create_metadata_element(self.resRScript.short_id, 'RSMetadata', scriptLanguage='R',
                                         languageVersion='3.5', scriptVersion='1.0',
                                         scriptDependencies='None', scriptReleaseDate='2015-12-01 00:00',
                                         scriptCodeRepository='http://www.google.com')
        self.assertEqual(RSMetadata.objects.all().count(), 1)

        # may not create additional instance of RSMetadata
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.resRScript.short_id, 'RSMetadata', scriptLanguage='R',
                                             languageVersion='3.5', scriptVersion='1.0',
                                             scriptDependencies='None', scriptReleaseDate='12/01/2015',
                                             scriptCodeRepository='http://www.google.com')

        self.assertEqual(RSMetadata.objects.all().count(), 1)

        # update existing meta
        resource.update_metadata_element(self.resRScript.short_id, 'RSMetadata',
                                         element_id=RSMetadata.objects.first().id,
                                         scriptLanguage='python',
                                         languageVersion='2.7')
        self.assertEqual(RSMetadata.objects.first().scriptLanguage, 'python')
        self.assertEqual(RSMetadata.objects.first().languageVersion, '2.7')

        # delete RSMetadata obj
        resource.delete_metadata_element(self.resRScript.short_id, 'RSMetadata',
                                         element_id=RSMetadata.objects.first().id)
        self.assertEqual(RSMetadata.objects.all().count(), 0)

    def test_receivers(self):
        request = HttpRequest()

        # RSMetadata
        request.POST = {'scriptLanguage': 'R', 'languageVersion': '3.5'}

        data = metadata_element_pre_create_handler(sender=RScriptResource,
                                                   element_name="RSMetadata",
                                                   request=request)
        self.assertTrue(data["is_valid"])

        request.POST = None

        data = metadata_element_pre_create_handler(sender=RScriptResource,
                                                   element_name="RSMetadata",
                                                   request=request)
        self.assertFalse(data["is_valid"])

        data = rs_pre_trigger(sender=RScriptResource,
                              metadata=[])

        self.assertEqual(data[0]['rsmetadata'], {})

        request.POST = {'scriptLanguage': 'R', 'languageVersion': '3.5'}

        data = rs_pre_update_handler(sender=RScriptResource,
                                     element_name="RSMetadata",
                                     request=request)

        self.assertTrue(data["is_valid"])

        request.POST = None

        data = rs_pre_update_handler(sender=RScriptResource,
                                     element_name="RSMetadata",
                                     request=request)

        self.assertFalse(data["is_valid"])
