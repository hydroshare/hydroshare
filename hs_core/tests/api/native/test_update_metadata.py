__author__ = 'shaunjl'
"""
Tastypie API tests for update_science_metadata and update_system_metadata

comments-

"""
from tastypie.test import ResourceTestCase, TestApiClient
from unittest import TestCase
from django.contrib.auth.models import User, Group
from hs_core import hydroshare
from hs_core.models import GenericResource
from dublincore.models import QualifiedDublinCoreElement as QDCE
from mezzanine.generic.models import Keyword, AssignedKeyword


class TestUpdateMetadata(TestCase):
    def setUp(self):
        user = hydroshare.create_account(
            'shaun@gmail.com',
            username='shaunjl',
            first_name='shaun',
            last_name='john',
            superuser=True,
            )
        self.res = hydroshare.create_resource('GenericResource',user,'Test Resource')
    def tearDown(self):
        User.objects.all().delete()
        #hydroshare.delete_resource(self.res.short_id)
        GenericResource.objects.all().delete()
        QDCE.objects.all().delete()
        Keyword.objects.all().delete()
        #AssignedKeyword.objects.all().delete()

    def test_update_science_metadata(self):
        d_m = [{
            'term':'SRC',
            'qualifier': 'BYU Archives',
            'content': 'Archive may be found at HBLL Library at HBLL:S102948'
            },
            {
            'term':'REP',
            'qualifier': "Dr. Nielson's work",
            'content': 'replaced in 2003'
            },
            {
            'term':'PBL',
            'qualifier': 'Dr. Ames',
            'content': 'Published 2001'
            }]

        hydroshare.update_science_metadata(self.res.short_id, dublin_metadata=d_m)

        for t in ('SRC','REP', 'PBL'):
            self.assertTrue(any(QDCE.objects.filter(term=t)))
        self.assertEqual(QDCE.objects.all(), QDCE.objects.filter(content_object=res))



    def test_update_keywords(self):
        kws= ['kw1','kw2','kw3']

        hydroshare.update_system_metadata(self.res.short_id, keywords=kws)

        self.assertEqual(AssignedKeyword.objects.filter(object_pk=res.id),Keyword.objects.all())

    def test_update_kwargs(self):
        kwargs = {'description':'new description',
                  'title':'new title'
                  }

        hydroshare.update_system_metadata(self.res.short_id, **kwargs)

        self.assertEqual(res.description,'new description')
        self.assertEqual(user.title,'new title')

    # Pabitra's unit test for the new metadata implementation
    def test_update_science_metadata_pk(self):
        # add these new metadata elements
        metadata_dict = [
            {'creator': {'name':'John Smith', 'email':'jsmith@gmail.com'}},
            {'creator': {'name':'Lisa Molley', 'email':'lmolley@gmail.com'}},
            {'contributor': {'name':'Kelvin Marshal', 'email':'kmarshal@yahoo.com',
                             'organization': 'Utah State University',
                             'profile_links': [{'type':'yahooProfile', 'url': 'http://yahoo.com/LH001'}]}},
            {'coverage': {'type':'period', 'value':{'name':'Name for period coverage' , 'start':'1/1/2000', 'end':'12/12/2012'}}},
            {'coverage': {'type':'point', 'value': {'name':'Name for point coverage', 'east':'56.45678', 'north':'12.6789'}}},
            {'format': {'value': 'txt/csv'}},
            {'format': {'value': 'zip'}},
            {'identifier': {'name':'someIdentifier', 'url':"http://some.org/001"}},
            {'language': {'code':'eng'}},
            {'relation': {'type':'isPartOf', 'value':'http://hydroshare.org/resource/001'}},
            {'rights': {'statement':'This is the rights statement for this resource', 'url':'http://rights.ord/001'}},
            {'source': {'derived_from':'http://hydroshare.org/resource/0001'}},
            {'subject': {'value':'sub-1'}},
            {'subject': {'value':'sub-2'}},
            ]

        hydroshare.update_science_metadata(pk=self.res.short_id, metadata = metadata_dict)

        # title element is automatically added in the science metadata update api method
        self.assertEqual(self.res.metadata.title.value, self.res.title, msg='resource title did not match')

        # resource description element is automatically added in the science metadata update api method
        self.assertEqual(self.res.metadata.description.abstract, 'Test Resource')

        # the following 2 date elements are automatically added in the science metadata update api method
        self.assertEqual(self.res.metadata.dates.all().count(), 2, msg="Number of date elements not equal to 2.")
        self.assertIn('created', [dt.type for dt in self.res.metadata.dates.all()], msg="Date element type 'Created' does not exist")
        self.assertIn('modified', [dt.type for dt in self.res.metadata.dates.all()], msg="Date element type 'Modified' does not exist")

        # number of creators at this point should be 3 (2 we are creating here one is automatically generated in resource creation signal
        self.assertEqual(self.res.metadata.creators.all().count(), 3, msg='Number of creators not equal to 3')
        self.assertIn('John Smith', [cr.name for cr in self.res.metadata.creators.all()], msg="Creator 'John Smith' was not found")
        self.assertIn('Lisa Molley', [cr.name for cr in self.res.metadata.creators.all()], msg="Creator 'Lisa Molley' was not found")

        # number of contributors at this point should be 1
        self.assertEqual(self.res.metadata.contributors.all().count(), 1, msg='Number of contributors not equal to 1')

        # there should be now 2 coverage elements
        self.assertEqual(self.res.metadata.coverages.all().count(), 2, msg="Number of coverages not equal to 2.")

        # there should be now 2 format elements
        self.assertEqual(self.res.metadata.formats.all().count(), 2, msg="Number of format elements not equal to 2.")

        # there should be now 2 identifier elements ( 1 we rae creating her + 1 auto generated in the resource creation signal handler)
        self.assertEqual(self.res.metadata.identifiers.all().count(), 2, msg="Number of identifier elements not equal to 1.")

        self.assertEqual(self.res.metadata.language.code, 'eng', msg="Resource has a language that is not English.")

        self.assertEqual(self.res.metadata.relations.all().count(), 1,
                         msg="Number of source elements is not equal to 1")

        self.assertEqual(self.res.metadata.rights.statement, 'This is the rights statement for this resource', msg="Statement of rights did not match.")
        self.assertEqual(self.res.metadata.rights.url, 'http://rights.ord/001', msg="URL of rights did not match.")

        self.assertEqual(self.res.metadata.sources.all().count(), 1, msg="Number of sources is not equal to 1.")
        self.assertIn('http://hydroshare.org/resource/0001',
                      [src.derived_from for src in self.res.metadata.sources.all()],
                      msg="Source element with derived from avlue of %s does not exist."
                          % 'http://hydroshare.org/resource/0001')

        # there should be 2 subject elements for this resource
        self.assertEqual(self.res.metadata.subjects.all().count(), 2, msg="Number of subject elements found not be 1.")
        self.assertIn('sub-1', [sub.value for sub in self.res.metadata.subjects.all()],
                      msg="Subject element with value of %s does not exist." % 'sub-1')
        self.assertIn('sub-2', [sub.value for sub in self.res.metadata.subjects.all()],
                      msg="Subject element with value of %s does not exist." % 'sub-1')


