from dateutil import parser
from lxml import etree
from unittest import TestCase

from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, User
from django.db import Error
from hs_core.hydroshare import resource
from hs_core.models import GenericResource, Creator, Contributor, CoreMetaData, \
    Coverage, Rights, Title, Language, Publisher, Identifier, \
    Type, Subject, Description, Date, Format, Relation, Source, FundingAgency
from hs_core import hydroshare
from hs_core.testing import MockIRODSTestCaseMixin


class TestCoreMetadata(MockIRODSTestCaseMixin, TestCase):
    def setUp(self):
        super(TestCoreMetadata, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        self.user = hydroshare.create_account(
            'user1@nowhere.com',
            username='user1',
            first_name='Creator_FirstName',
            last_name='Creator_LastName',
            superuser=False,
            groups=[]
        )

        self.res = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='Generic resource',
            keywords=['kw1', 'kw2']
        )

    # without this tearDown() getting transaction error even if we make this class inherit from django TestCase and
    # and not uninttest TestCase
    def tearDown(self):
        super(TestCoreMetadata, self).tearDown()
        User.objects.all().delete()
        Group.objects.all().delete()
        GenericResource.objects.all().delete()
        Creator.objects.all().delete()
        Contributor.objects.all().delete()
        CoreMetaData.objects.all().delete()
        Coverage.objects.all().delete()
        Rights.objects.all().delete()
        Title.objects.all().delete()
        Publisher.objects.all().delete()
        Description.objects.all().delete()
        Relation.objects.all().delete()
        Subject.objects.all().delete()
        Source.objects.all().delete()
        Identifier.objects.all().delete()
        Type.objects.all().delete()
        Format.objects.all().delete()
        Date.objects.all().delete()
        Language.objects.all().delete()

    def test_auto_element_creation(self):
        # The following metadata elements are automatically generated upon resource creation

        self.assertEqual(self.res.metadata.title.value, 'Generic resource', msg='resource title did not match')

        # number of creators at this point should be 1
        self.assertEqual(self.res.metadata.creators.all().count(), 1, msg='Number of creators not equal to 1')

        self.assertEqual(self.res.metadata.creators.all().first().name, self.res.creator.get_full_name(),
                         msg='resource creator did not match')

        self.assertIn('created', [dt.type for dt in self.res.metadata.dates.all()], msg="Date created not found")
        self.assertIn('modified', [dt.type for dt in self.res.metadata.dates.all()], msg="Date modified not found")

        # there should be hydroshare identifier - only one identifier at this point
        self.assertEqual(self.res.metadata.identifiers.all().count(), 1,
                         msg="Number of identifier elements not equal to 1.")
        self.assertIn('hydroShareIdentifier', [id.name for id in self.res.metadata.identifiers.all()],
                      msg="Identifier name was not found.")

        self.assertEqual(self.res.metadata.subjects.all().count(), 2, msg="Number of subjects elements not equal to 2.")
        self.assertIn('kw1', [sub.value for sub in self.res.metadata.subjects.all()],
                      msg="Subject value 'kw1' was not found.")

        self.assertIn('kw2', [sub.value for sub in self.res.metadata.subjects.all()],
                      msg="Subject value 'kw2' was not found.")

        # 'Type' element should have been created
        type_url = '{0}/terms/{1}'.format(hydroshare.utils.current_site_url(), 'GenericResource')
        self.assertEqual(self.res.metadata.type.url, type_url, msg='type element url is wrong')

        # Language element should have been created
        self.assertNotEqual(self.res.metadata.language, None, msg="Resource has no language element.")

        # the default language should be english
        self.assertEqual(self.res.metadata.language.code, 'eng', msg="Resource has language element which is not "
                                                                     "English.")
        # By default a resource should have the rights element
        self.assertNotEqual(self.res.metadata.rights, None, msg="Resource has no rights element.")

        default_rights_statement = 'This resource is shared under the Creative Commons Attribution CC BY.'
        default_rights_url = 'http://creativecommons.org/licenses/by/4.0/'
        self.assertEqual(self.res.metadata.rights.statement,
                         default_rights_statement, msg="Rights statement didn't match")
        self.assertEqual(self.res.metadata.rights.url, default_rights_url, msg="URL of rights did not match.")

        # test that when a resource is created it already generates the 'created' and 'modified' date elements
        self.assertEqual(self.res.metadata.dates.all().count(), 2, msg="Number of date elements not equal to 2.")
        self.assertIn('created', [dt.type for dt in self.res.metadata.dates.all()],
                      msg="Date element type 'Created' does not exist")
        self.assertIn('modified', [dt.type for dt in self.res.metadata.dates.all()],
                      msg="Date element type 'Modified' does not exist")

    def test_title_create(self):
        # trying to create a title element for a resource should raise an exception
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id, 'title',
                                                                              value='new resource'))

    def test_creator(self):
        # add a creator element
        resource.create_metadata_element(self.res.short_id,'creator', name='John Smith')

        # number of creators at this point should be 2
        self.assertEqual(self.res.metadata.creators.all().count(), 2, msg='Number of creators not equal to 2')
        self.assertIn('John Smith', [cr.name for cr in self.res.metadata.creators.all()],
                      msg="Creator 'John Smith' was not found")

        # update creator John Smith
        metadata_type = ContentType.objects.get_for_model(self.res.metadata)
        creator = Creator.objects.filter(name='John Smith', object_id=self.res.metadata.id,
                                         content_type__pk=metadata_type.id).first()
        kwargs = {'email':'jsmith@gmail.com', 'order': 2}
        resource.update_metadata_element(self.res.short_id,'creator', creator.id, **kwargs)

        self.assertIn('jsmith@gmail.com', [cr.email for cr in self.res.metadata.creators.all()],
                      msg="Creator 'John Smith' email was not found")

        # test adding a creator with all sub-elements
        cr_name = 'Mike Sundar'
        cr_des = 'http://hydroshare.org/user/001'
        cr_org = "USU"
        cr_email = 'mike.sundar@usu.edu'
        cr_address = "11 River Drive, Logan UT-84321, USA"
        cr_phone = '435-567-0989'
        cr_homepage = 'http://usu.edu/homepage/001'

        resource.create_metadata_element(self.res.short_id,'creator',
                                         name=cr_name,
                                         description=cr_des,
                                         organization=cr_org,
                                         email=cr_email,
                                         address=cr_address,
                                         phone=cr_phone,
                                         homepage=cr_homepage,
                                        )

        cr_mike = self.res.metadata.creators.all().filter(email=cr_email).first()
        self.assertNotEqual(cr_mike, None, msg='Creator Mike was not found')
        self.assertEqual(cr_mike.name, cr_name)
        self.assertEqual(cr_mike.description, cr_des)
        self.assertEqual(cr_mike.organization, cr_org)
        self.assertEqual(cr_mike.address, cr_address)
        self.assertEqual(cr_mike.phone, cr_phone)
        self.assertEqual(cr_mike.homepage, cr_homepage)
        self.assertEqual(cr_mike.order, 3)

        # update Mike's order to 2 from 3
        resource.update_metadata_element(self.res.short_id,'creator', cr_mike.id, order=2)
        cr_mike = self.res.metadata.creators.all().filter(email=cr_email).first()
        self.assertEqual(cr_mike.order, 2)

        # now John's order should be 3 (changed from 2)
        cr_john = self.res.metadata.creators.all().filter(email='jsmith@gmail.com').first()
        self.assertEqual(cr_john.order, 3)

        # update John's order to 4 from 3 - this should not change John's order
        resource.update_metadata_element(self.res.short_id,'creator', cr_john.id, order=4)
        self.assertEqual(cr_john.order, 3)

        # try to add a creator with no name
        resource.create_metadata_element(self.res.short_id, 'creator',
                                         organization='test org',
                                         description='test desc',
                                         email='test@test.com',
                                         address='test address',
                                         phone='111-111-1111',
                                         homepage='http://www.test.com',
                                         )
        self.assertEqual(self.res.metadata.creators.all().count(), 4)
        self.assertIn('test org', [cr.organization for cr in self.res.metadata.creators.all()],
                      msg="Creator 'test org' was not found")

        # try to add a creator with no name or organization should raise error
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id, 'creator',
                                             description='test desc',
                                             email='test@test.com',
                                             address='test address',
                                             phone='111-111-1111',
                                             homepage='http://www.test.com',
                                             )

        # delete Mike's home page
        resource.update_metadata_element(self.res.short_id,'creator', cr_mike.id, homepage=None)
        cr_mike = self.res.metadata.creators.all().filter(email=cr_email).first()
        self.assertEqual(cr_mike.homepage, None)

        # test that the resource must have at least one creator - trying to delete the last creator should fail
        # delete John
        resource.delete_metadata_element(self.res.short_id, 'creator', cr_john.id )
        self.assertEqual(Creator.objects.filter(id=cr_john.id).first(), None)

        # trying to update (description) hydroshare user identifier to a different identifier should raise exception
        with self.assertRaises(ValidationError):
            resource.update_metadata_element(self.res.short_id,'creator', cr_mike.id,
                                             description="http://hydroshare.org/user/002")

        # however, it should be possible to to update (description) hydroshare identifier to empty string
        cr_mike = self.res.metadata.creators.all().filter(email=cr_email).first()
        self.assertEquals(cr_mike.description, 'http://hydroshare.org/user/001')
        resource.update_metadata_element(self.res.short_id,'creator', cr_mike.id, description='')
        cr_mike = self.res.metadata.creators.all().filter(email=cr_email).first()
        self.assertEquals(cr_mike.description, '')

        # delete Mike
        resource.delete_metadata_element(self.res.short_id, 'creator', cr_mike.id )
        self.assertEqual(Creator.objects.filter(id=cr_mike.id).first(), None)

        # deleting the last user should raise exception
        self.assertRaises(Exception, lambda :resource.delete_metadata_element(self.res.short_id, 'creator',
                                                                              self.user.id ))

    def test_contributor(self):
        # initially there should be no contributors
        self.assertEqual(self.res.metadata.contributors.all().count(), 0, msg='Number of contributors not equal to 0')

        # add a contributor element
        resource.create_metadata_element(self.res.short_id,'contributor', name='John Smith')
        # number of contributors at this point should be 1
        self.assertEqual(self.res.metadata.contributors.all().count(), 1, msg='Number of contributors not equal to 1')
        self.assertIn('John Smith', [con.name for con in self.res.metadata.contributors.all()],
                      msg="Contributor 'John Smith' was not found")

        # update contributor John Smith
        metadata_type = ContentType.objects.get_for_model(self.res.metadata)
        con_john = Contributor.objects.filter(name='John Smith', object_id=self.res.metadata.id,
                                              content_type__pk=metadata_type.id).first()
        kwargs = {'email':'jsmith@gmail.com'}
        resource.update_metadata_element(self.res.short_id,'contributor', con_john.id, **kwargs)

        self.assertIn('jsmith@gmail.com', [con.email for con in self.res.metadata.contributors.all()],
                      msg="Contributor 'John Smith' email was not found")

        # test adding a contributor with all sub_elements
        con_name = 'Mike Sundar'
        con_des = 'http://hydroshare.org/user/001'
        con_org = "USU"
        con_email = 'mike.sundar@usu.edu'
        con_address = "11 River Drive, Logan UT-84321, USA"
        con_phone = '435-567-0989'
        con_homepage = 'http://usu.edu/homepage/001'
        resource.create_metadata_element(self.res.short_id,'contributor',
                                         name=con_name,
                                         description=con_des,
                                         organization=con_org,
                                         email=con_email,
                                         address=con_address,
                                         phone=con_phone,
                                         homepage=con_homepage,
                                        )

        # number of contributors at this point should be 2
        self.assertEqual(self.res.metadata.contributors.all().count(), 2, msg='Number of contributors not equal to 2')

        con_mike = self.res.metadata.contributors.all().filter(email=con_email).first()
        self.assertNotEqual(con_mike, None, msg='Creator Mike was not found')
        self.assertEqual(con_mike.name, con_name)
        self.assertEqual(con_mike.description, con_des)
        self.assertEqual(con_mike.organization, con_org)
        self.assertEqual(con_mike.address, con_address)
        self.assertEqual(con_mike.phone, con_phone)
        self.assertEqual(con_mike.homepage, con_homepage)

        # update Mike's phone
        con_phone = '435-567-9999'
        resource.update_metadata_element(self.res.short_id,'contributor', con_mike.id, phone=con_phone)
        con_mike = self.res.metadata.contributors.all().filter(email=con_email).first()
        self.assertEqual(con_mike.phone, con_phone)

        # delete Mike's home page
        resource.update_metadata_element(self.res.short_id,'contributor', con_mike.id, homepage=None)
        con_mike = self.res.metadata.contributors.all().filter(email=con_email).first()
        self.assertEqual(con_mike.homepage, None)

        # trying to update (description) hydroshare user identifier to a different identifier should raise exception
        with self.assertRaises(ValidationError):
            resource.update_metadata_element(self.res.short_id,'contributor', con_mike.id,
                                             description="http://hydroshare.org/user/002")

        # however, it should be possible to to update (description) hydroshare identifier to empty string
        con_mike = self.res.metadata.contributors.all().filter(email=con_email).first()
        self.assertEquals(con_mike.description, 'http://hydroshare.org/user/001')
        resource.update_metadata_element(self.res.short_id,'contributor', con_mike.id, description='')
        con_mike = self.res.metadata.contributors.all().filter(email=con_email).first()
        self.assertEquals(con_mike.description, '')

        # test that all resource contributors can be deleted
        # delete John
        resource.delete_metadata_element(self.res.short_id, 'contributor', con_john.id )
        self.assertEqual(Contributor.objects.filter(id=con_john.id).first(), None)


        # delete Mike
        resource.delete_metadata_element(self.res.short_id, 'contributor', con_mike.id )
        self.assertEqual(Contributor.objects.filter(id=con_mike.id).first(), None)

        # number of contributors at this point should be 0
        self.assertEqual(self.res.metadata.contributors.all().count(), 0, msg='Number of contributors not equal to 0')

    def test_party_external_links(self):
        # TESTING LINKS FOR CREATOR: add creator element with profile links
        kwargs = {'name':'Lisa Howard', 'email':'lasah@yahoo.com', 'profile_links': [{'type': 'yahooProfile',
                                                                                      'url': 'http://yahoo.com/LH001'}]}
        resource.create_metadata_element(self.res.short_id,'creator', **kwargs)
        # test external link
        cr_lisa = self.res.metadata.creators.all().filter(email='lasah@yahoo.com').first()

        # lisa should have one external profile link
        self.assertEqual(cr_lisa.external_links.all().count(), 1, msg="Creator Lisa does not have 1 external link.")

        # test that trying to add another link of the same type should raise exception
        kwargs = {'profile_links': [{'type':'yahooProfile', 'url': 'http://yahoo.com/LH002'}]}
        self.assertRaises(Exception, lambda : resource.update_metadata_element(self.res.short_id,'creator',
                                                                               cr_lisa.id, **kwargs))

        # test that trying to add another link of the same url should raise exception
        kwargs = {'profile_links': [{'type':'yahooProfile2', 'url': 'http://yahoo.com/LH001'}]}
        self.assertRaises(Exception, lambda : resource.update_metadata_element(self.res.short_id,'creator',
                                                                               cr_lisa.id, **kwargs))

        # test a link of different type can be added
        kwargs = {'profile_links': [{'type':'usuProfile', 'url': 'http://usu.edu/profile/LH001'}]}
        resource.update_metadata_element(self.res.short_id,'creator', cr_lisa.id, **kwargs)

        # lisa should have 2 external profile links at this point
        self.assertEqual(cr_lisa.external_links.all().count(), 2, msg="Creator Lisa does not have 2 external link.")

        self.assertIn('yahooProfile', [link.type for link in cr_lisa.external_links.all()],
                      msg="Creator 'Lisa' does not have link type: yahooProfile")
        self.assertIn('usuProfile', [link.type for link in cr_lisa.external_links.all()],
                      msg="Creator 'Lisa' does not have link type: usuProfile")
        self.assertIn('http://yahoo.com/LH001', [link.url for link in cr_lisa.external_links.all()],
                      msg="Creator 'Lisa' does not have link url: 'http://yahoo.com/LH001'")
        self.assertIn('http://usu.edu/profile/LH001', [link.url for link in cr_lisa.external_links.all()],
                      msg="Creator 'Lisa' does not have link url: 'http://usu.edu/profile/LH001'")

        # test deleting a link
        usu_link = cr_lisa.external_links.all().filter(type='usuProfile').first()
        kwargs = {'profile_links': [{'link_id':usu_link.id}]}
        resource.update_metadata_element(self.res.short_id,'creator', cr_lisa.id, **kwargs)
        # lisa should have one external profile link
        self.assertEqual(cr_lisa.external_links.all().count(), 1, msg="Creator Lisa does not have 1 external link.")

        # TESTING LINKS FOR CONTRIBUTOR: add contributor element with profile links
        kwargs = {'name':'Lisa Howard', 'email':'lasah@yahoo.com', 'profile_links': [{'type': 'yahooProfile',
                                                                                      'url': 'http://yahoo.com/LH001'}]}
        resource.create_metadata_element(self.res.short_id,'contributor', **kwargs)
        # test external link
        con_lisa = self.res.metadata.contributors.all().filter(email='lasah@yahoo.com').first()

        # lisa should have one external profile link
        self.assertEqual(con_lisa.external_links.all().count(), 1,
                         msg="contributor Lisa does not have 1 external link.")

        # test that trying to add another link of the same type should raise exception
        kwargs = {'profile_links': [{'type':'yahooProfile', 'url': 'http://yahoo.com/LH002'}]}
        self.assertRaises(Exception, lambda : resource.update_metadata_element(self.res.short_id, 'contributor',
                                                                               con_lisa.id, **kwargs))

        # test a link of different type can be added
        kwargs = {'profile_links': [{'type':'usuProfile', 'url': 'http://usu.edu/profile/LH001'}]}
        resource.update_metadata_element(self.res.short_id,'contributor', con_lisa.id, **kwargs)

        # lisa should have 2 external profile links at this point
        self.assertEqual(con_lisa.external_links.all().count(), 2,
                         msg="Contributor Lisa does not have 2 external link.")

        self.assertIn('yahooProfile', [link.type for link in con_lisa.external_links.all()],
                      msg="Contributor 'Lisa' does not have link type: yahooProfile")
        self.assertIn('usuProfile', [link.type for link in con_lisa.external_links.all()],
                      msg="Contributor 'Lisa' does not have link type: usuProfile")
        self.assertIn('http://yahoo.com/LH001', [link.url for link in con_lisa.external_links.all()],
                      msg="Contributor 'Lisa' does not have link url: 'http://yahoo.com/LH001'")
        self.assertIn('http://usu.edu/profile/LH001', [link.url for link in con_lisa.external_links.all()],
                      msg="Contributor 'Lisa' does not have link url: 'http://usu.edu/profile/LH001'")

    def test_title(self):
        # test that a 2nd title can't be added
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id,'title',
                                                                              value="another title"))

        # test that the existing title can't be deleted
        self.assertRaises(Exception, lambda: resource.delete_metadata_element(self.res.short_id,'title',
                                                                              self.res.metadata.title.id))

        # test that title can be updated
        resource.update_metadata_element(self.res.short_id,'title', self.res.metadata.title.id, value="another title")
        self.assertEqual(self.res.metadata.title.value, 'another title')

    def test_coverage(self):
        # there should not be any coverages at this point
        self.assertEqual(self.res.metadata.coverages.all().count(), 0, msg="One more coverages found.")

        # add a period type coverage
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
        resource.create_metadata_element(self.res.short_id, 'coverage', type='period', value=value_dict)

        # there should be now one coverage element
        self.assertEqual(self.res.metadata.coverages.all().count(), 1, msg="Number of coverages not equal to 1.")

        # add another period type coverage - which raise an exception
        value_dict = {'name':'Name for period coverage', 'start':'1/1/2002', 'end':'12/12/2013'}
        self.assertRaises(Exception, lambda : resource.create_metadata_element(self.res.short_id,'coverage',
                                                                               type='period', value=value_dict))

        # test that the name is optional
        self.res.metadata.coverages.all()[0].delete()
        value_dict = {'start':'1/1/2000', 'end':'12/12/2012'}
        resource.create_metadata_element(self.res.short_id,'coverage', type='period', value=value_dict)
        # there should be now one coverage element
        self.assertEqual(self.res.metadata.coverages.all().count(), 1, msg="Number of coverages not equal to 1.")

        # add a point type coverage
        value_dict = {'east':'56.45678', 'north':'12.6789', 'units': 'decimal deg'}
        resource.create_metadata_element(self.res.short_id,'coverage', type='point', value=value_dict)

        # there should be now 2 coverage elements
        self.assertEqual(self.res.metadata.coverages.all().count(), 2, msg="Total overages not equal 2.")

        # test that the name, elevation, zunits and projection are optional
        self.res.metadata.coverages.get(type='point').delete()
        value_dict = {'east':'56.45678', 'north':'12.6789', 'units': 'decimal deg', 'name': 'Little bear river',
                      'elevation': '34.6789', 'zunits': 'rad deg', 'projection': 'NAD83'}
        resource.create_metadata_element(self.res.short_id,'coverage', type='point', value=value_dict)
        # there should be now 2 coverage elements
        self.assertEqual(self.res.metadata.coverages.all().count(), 2, msg="Total coverages not equal 2.")

        # add a box type coverage - this should raise an exception as we already have a point type coverage
        value_dict = {'northlimit':'56.45678', 'eastlimit':'12.6789','southlimit':'16.45678', 'westlimit':'16.6789',
                      'units': 'decimal deg' }
        self.assertRaises(Exception, lambda : resource.create_metadata_element(self.res.short_id,'coverage',
                                                                               type='box', value=value_dict))

        self.assertIn('point', [cov.type for cov in self.res.metadata.coverages.all()],
                      msg="Coverage type 'Point' does not exist")
        self.assertIn('period', [cov.type for cov in self.res.metadata.coverages.all()],
                      msg="Coverage type 'Point' does not exist")

        # test coverage element can't be deleted - raises exception
        cov_pt = self.res.metadata.coverages.all().filter(type='point').first()
        self.assertRaises(Exception, lambda : resource.delete_metadata_element(self.res.short_id, 'coverage',
                                                                               cov_pt.id ))

        # change the point coverage to type box
        value_dict = {'northlimit':'56.45678', 'eastlimit':'120.6789','southlimit':'16.45678', 'westlimit':'16.6789',
                      'units':'decimal deg' }
        resource.update_metadata_element(self.res.short_id,'coverage', cov_pt.id, type='box', value=value_dict)
        self.assertIn('box', [cov.type for cov in self.res.metadata.coverages.all()],
                      msg="Coverage type 'box' does not exist")
        self.assertIn('period', [cov.type for cov in self.res.metadata.coverages.all()],
                      msg="Coverage type 'Period' does not exist")

        # test that the name, uplimit, downlimit, zunits and projection are optional
        self.res.metadata.coverages.get(type='box').delete()
        value_dict = {'northlimit': '56.45678', 'eastlimit': '120.6789','southlimit': '16.45678', 'westlimit': '16.6789',
                      'units': 'decimal deg', 'name': 'Bear river', 'uplimit': '45.234', 'downlimit': '12.345',
                      'zunits': 'decimal deg', 'projection': 'NAD83'}
        resource.create_metadata_element(self.res.short_id, 'coverage', type='box', value=value_dict)

        # there should be now 2 coverage elements
        self.assertEqual(self.res.metadata.coverages.all().count(), 2, msg="Total overages not equal to 2.")

        # for point type coverage test valid data for 'north' and 'east'

        self.res.metadata.coverages.get(type='box').delete()
        # now try to create point type coverage with invalid data
        # value for 'east' should be >= -180 and <= 180 and 'north' >= -90 and <= 90
        value_dict = {'east': '181.45678', 'north': '50', 'units': 'decimal deg'}
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='point', value=value_dict)

        value_dict = {'east': '-181.45678', 'north': '50', 'units': 'decimal deg'}
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='point', value=value_dict)

        value_dict = {'east': '120.45678', 'north': '91', 'units': 'decimal deg'}
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='point', value=value_dict)

        value_dict = {'east': '120.45678', 'north': '-91', 'units': 'decimal deg'}
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='point', value=value_dict)

        # now create coverage of type 'point' with all valid data
        value_dict = {'east': '120.45678', 'north': '80.60', 'units': 'decimal deg'}
        resource.create_metadata_element(self.res.short_id,'coverage', type='point', value=value_dict)
        self.assertEqual(self.res.metadata.coverages.filter(type='point').count(), 1)

        # for box type coverage test valid data for 'northlimit', 'southlimit', 'eastlimit' and 'westlimit'

        self.res.metadata.coverages.get(type='point').delete()
        # valid value for 'northlimit' should be in the range of -90 to 90
        value_dict = {'northlimit': '91.45678', 'eastlimit': '120.6789', 'southlimit': '16.45678',
                      'westlimit': '16.6789', 'units': 'decimal deg' }
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='box', value=value_dict)

        value_dict = {'northlimit': '-91.45678', 'eastlimit': '120.6789', 'southlimit': '16.45678',
                      'westlimit': '16.6789', 'units': 'decimal deg' }
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='box', value=value_dict)

        # value for 'southlimit' should be in the range of -90 to 90
        value_dict = {'northlimit': '80.45678', 'eastlimit': '120.6789', 'southlimit': '-91.45678',
                      'westlimit': '16.6789', 'units': 'decimal deg' }
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='box', value=value_dict)

        value_dict = {'northlimit': '80.45678', 'eastlimit': '120.6789', 'southlimit': '91.45678',
                      'westlimit': '16.6789', 'units': 'decimal deg' }
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='box', value=value_dict)

        # value for 'northlimit' must be greater than 'southlimit'
        value_dict = {'northlimit': '70.45678', 'eastlimit': '120.6789', 'southlimit': '80.45678',
                      'westlimit': '16.6789', 'units': 'decimal deg' }
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='box', value=value_dict)

        # value for 'eastlimit should be in the range of -180 to 180
        value_dict = {'northlimit': '80.45678', 'eastlimit': '181.6789', 'southlimit': '70.45678',
                      'westlimit': '16.6789', 'units': 'decimal deg' }
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='box', value=value_dict)

        value_dict = {'northlimit': '80.45678', 'eastlimit': '-181.6789', 'southlimit': '70.45678',
                      'westlimit': '16.6789', 'units': 'decimal deg' }
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='box', value=value_dict)

        # value for 'westlimit' must be in the range of -180 to 180
        value_dict = {'northlimit': '80.45678', 'eastlimit': '120.6789', 'southlimit': '70.45678',
                      'westlimit': '-181.6789', 'units': 'decimal deg' }
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='box', value=value_dict)

        value_dict = {'northlimit': '80.45678', 'eastlimit': '120.6789', 'southlimit': '70.45678',
                      'westlimit': '181.6789', 'units': 'decimal deg' }
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='box', value=value_dict)

        # value for 'eastlimit' must be greater than 'westlimit'
        value_dict = {'northlimit': '80.45678', 'eastlimit': '120.6789', 'southlimit': '70.45678',
                      'westlimit': '130.6789', 'units': 'decimal deg' }
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id,'coverage', type='box', value=value_dict)

        # now create with all valid data
        value_dict = {'northlimit': '80.45678', 'eastlimit': '120.6789', 'southlimit': '70.45678',
                      'westlimit': '110.6789', 'units': 'decimal deg' }
        resource.create_metadata_element(self.res.short_id,'coverage', type='box', value=value_dict)

        self.assertEqual(self.res.metadata.coverages.filter(type='box').count(), 1)

    def test_date(self):
        # test that when a resource is created it already generates the 'created' and 'modified' date elements
        self.assertEqual(self.res.metadata.dates.all().count(), 2, msg="Number of date elements not equal to 2.")
        self.assertIn('created', [dt.type for dt in self.res.metadata.dates.all()],
                      msg="Date element type 'Created' does not exist")
        self.assertIn('modified', [dt.type for dt in self.res.metadata.dates.all()],
                      msg="Date element type 'Modified' does not exist")

        # add another date of type 'created' - which should raise an exception
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id,'date',
                                                                              type='created',
                                                                              start_date=parser.parse("8/10/2014")))

        # add another date of type 'modified' - which should raise an exception
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id,'date',
                                                                              type='modified',
                                                                              start_date=parser.parse("8/10/2014")))

        # add another date of type 'published' - which should raise an exception since the resource is not yet
        # published.
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id,'date',
                                                                              type='published',
                                                                              start_date=parser.parse("8/10/2014")))

        # make the resource published and then add the date type published - which should work
        self.res.raccess.published = True
        self.res.raccess.save()
        resource.create_metadata_element(self.res.short_id, 'date', type='published',
                                         start_date=parser.parse("8/10/2014"))

        # add date type 'available' when the the resource is NOT public - this should raise an exception
        self.res.raccess.public = False
        self.res.raccess.save()
        self.assertRaises(Exception, lambda : resource.create_metadata_element(self.res.short_id, 'date',
                                                                               type='available',
                                                                               start_date=parser.parse("8/10/2014")))

        # make the resource public and then add available date
        self.res.raccess.public = True
        self.res.raccess.save()
        resource.create_metadata_element(self.res.short_id,'date', type='available',
                                         start_date=parser.parse("8/10/2014"))
        self.assertIn('available', [dt.type for dt in self.res.metadata.dates.all()],
                      msg="Date element type 'Available' does not exist")

        # add date type 'valid' - it seems there is no restriction for this date type
        resource.create_metadata_element(self.res.short_id, 'date', type='valid', start_date=parser.parse("8/10/2014"))
        self.assertIn('valid', [dt.type for dt in self.res.metadata.dates.all()],
                      msg="Date element type 'Valid' does not exist")

        # trying to add an existing date type element should raise an exception
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id, 'date', type='valid',
                                                                              start_date=parser.parse("9/10/2014")))

        # add another date of type 'none-type' that is not one of the date types allowed -
        # which should raise an exception.
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id, 'date',
                                                                              type='none-type',
                                                                              start_date=parser.parse("8/10/2014")))

        # test updating a date element
        # update of created date is not allowed
        dt_created = self.res.metadata.dates.all().filter(type='created').first()
        self.assertRaises(Exception, lambda: resource.update_metadata_element(self.res.short_id, 'date', dt_created.id,
                                                                             start_date=parser.parse('8/10/2014')))

        # update of modified date should not change to what the user specifies
        # it should always match with resource update date value
        dt_modified = self.res.metadata.dates.all().filter(type='modified').first()
        resource.update_metadata_element(self.res.short_id,'date', dt_modified.id, start_date=parser.parse('8/10/2014'))
        dt_modified = self.res.metadata.dates.all().filter(type='modified').first()
        self.assertNotEqual(dt_modified.start_date.date(), parser.parse('8/10/2014').date())
        self.assertEqual(self.res.updated.date(), dt_modified.start_date.date())

        # test the date type can't be changed - it does not through any exception though - it just ignores
        resource.update_metadata_element(self.res.short_id,'date', dt_modified.id, type='valid',
                                         start_date=parser.parse('8/10/2013'))
        self.assertIn('modified', [dt.type for dt in self.res.metadata.dates.all()],
                      msg="Date element type 'Modified' does not exist")

        # test that date value for date type 'valid' can be changed
        dt_valid = self.res.metadata.dates.all().filter(type='valid').first()
        resource.update_metadata_element(self.res.short_id,'date', dt_valid.id, start_date=parser.parse('8/10/2011'),
                                         end_date=parser.parse('8/11/2012'))
        dt_valid = self.res.metadata.dates.all().filter(type='valid').first()
        self.assertEqual(dt_valid.start_date.date(), parser.parse('8/10/2011').date())
        self.assertEqual(dt_valid.end_date.date(), parser.parse('8/11/2012').date())

        # test that date value for date type 'available' can be changed
        dt_available = self.res.metadata.dates.all().filter(type='available').first()
        resource.update_metadata_element(self.res.short_id,'date', dt_available.id,
                                         start_date=parser.parse('8/11/2011'))
        dt_available = self.res.metadata.dates.all().filter(type='available').first()
        self.assertEqual(dt_available.start_date.date(), parser.parse('8/11/2011').date())

        # test that date value for date type 'published can be changed
        dt_published = self.res.metadata.dates.all().filter(type='published').first()
        resource.update_metadata_element(self.res.short_id, 'date', dt_published.id,
                                         start_date=parser.parse('8/9/2011'))
        dt_published = self.res.metadata.dates.all().filter(type='published').first()
        self.assertEqual(dt_published.start_date.date(), parser.parse('8/9/2011').date())

        # trying to delete date type 'created' should raise exception
        dt_created = self.res.metadata.dates.all().filter(type='created').first()
        self.assertRaises(Exception, lambda: resource.delete_metadata_element(self.res.short_id,'date', dt_created.id))

        # trying to delete date type 'modified' should raise exception
        dt_modified = self.res.metadata.dates.all().filter(type='modified').first()
        self.assertRaises(Exception, lambda: resource.delete_metadata_element(self.res.short_id,'date',
                                                                              dt_modified.id))

        # trying to delete date type 'published' should work
        dt_published = self.res.metadata.dates.all().filter(type='published').first()
        resource.delete_metadata_element(self.res.short_id,'date', dt_published.id)

        # trying to delete date type 'available' should work
        dt_available = self.res.metadata.dates.all().filter(type='available').first()
        resource.delete_metadata_element(self.res.short_id,'date', dt_available.id)

        # trying to delete date type 'valid' should work
        dt_valid = self.res.metadata.dates.all().filter(type='valid').first()
        resource.delete_metadata_element(self.res.short_id,'date', dt_valid.id)

    def test_description(self):

        # test that the resource metadata does not contain abstract
        self.assertEqual(self.res.metadata.description, None, msg='Abstract exists for the resource')

        # create a abstract for the resource
        resource.create_metadata_element(self.res.short_id,'description', abstract='new abstract for the resource')

        # update the abstract
        resource.update_metadata_element(self.res.short_id,'description', self.res.metadata.description.id,
                                         abstract='Updated generic resource')
        self.assertEqual(self.res.metadata.description.abstract, 'Updated generic resource')

        # test adding a 2nd description element - should raise an exception
        self.assertRaises(Exception, lambda :resource.create_metadata_element(self.res.short_id,'description',
                                                                              abstract='new abstract for the resource'))

        # delete the abstract - should raise exception
        self.assertRaises(Exception, lambda :resource.delete_metadata_element(self.res.short_id,'description',
                                                                              self.res.metadata.description.id))

    def test_format(self):
        # when a resource is created with no content files, there should not be any formats elements
        # associated with it
        self.assertEqual(self.res.metadata.formats.all().count(), 0, msg="Number of format elements not equal to 0.")

        # add a format element
        format_csv = 'text/csv'
        resource.create_metadata_element(self.res.short_id, 'format', value=format_csv)
        self.assertEqual(self.res.metadata.formats.all().count(), 1, msg="Number of format elements not equal to 1.")
        self.assertIn(format_csv, [fmt.value for fmt in self.res.metadata.formats.all()],
                      msg="Format element with value of %s does not exist." % format_csv)

        # duplicate formats are not allowed - exception is thrown
        format_CSV = 'text/csv'
        self.assertRaises(Exception, lambda:resource.create_metadata_element(self.res.short_id,'format',
                                                                             value=format_CSV))

        # test that a resource can have multiple formats
        format_zip = 'zip'
        resource.create_metadata_element(self.res.short_id,'format', value=format_zip)
        self.assertEqual(self.res.metadata.formats.all().count(), 2, msg="Number of format elements not equal to 2.")
        self.assertIn(format_csv, [fmt.value for fmt in self.res.metadata.formats.all()],
                      msg="Format element with value of %s does not exist." % format_csv)
        self.assertIn(format_zip, [fmt.value for fmt in self.res.metadata.formats.all()],
                      msg="Format element with value of %s does not exist." % format_zip)

        # test that it possible to update an existing format value
        fmt_element = self.res.metadata.formats.all().filter(value__iexact=format_csv).first()
        format_CSV = 'csv/text'
        resource.update_metadata_element(self.res.short_id, 'format', fmt_element.id, value=format_CSV)
        fmt_element = self.res.metadata.formats.all().filter(value__iexact=format_CSV).first()
        self.assertEqual(fmt_element.value, format_CSV)

        # test that it is possible to delete all format elements
        for fmt in self.res.metadata.formats.all():
            resource.delete_metadata_element(self.res.short_id,'format', fmt.id)

        # there should not be any format elements at this point
        self.assertEqual(self.res.metadata.formats.all().count(), 0, msg="Number of format elements not equal to 0.")

        # TODO: test a format element is created automatically if a resource is created with content files

    def test_auto_format_element_creation(self):
        # when a resource is created with content file(s), one ore more format elements are created automatically

        # create a file that will be used for creating a resource
        res_file_1 = "file_one.txt"
        open(res_file_1, "w").close()

        # open the file for read
        file_obj_1 = open(res_file_1, "r")
        res = hydroshare.create_resource(resource_type='GenericResource',
                                         owner=self.user,
                                         title='Generic resource',
                                         files=(file_obj_1,)
                                        )
        format_CSV = 'text/plain'
        # there should be only one format element at this point
        self.assertEquals(res.metadata.formats.all().count(), 1, msg="Number of format elements is not equal to 1")
        fmt_element = res.metadata.formats.all().first()
        self.assertEqual(fmt_element.value, format_CSV)

        # test adding more files of same mime type creates only one format element
        res_file_2 = "file_two.txt"
        open(res_file_2, "w").close()

        # open the file for read
        file_obj_2 = open(res_file_2, "r")
        res = hydroshare.create_resource(resource_type='GenericResource',
                                         owner=self.user,
                                         title='Generic resource',
                                         files=(file_obj_1, file_obj_2)
                                        )

        # there should be only one format element at this point
        self.assertEquals(res.metadata.formats.all().count(), 1, msg="Number of format elements is not equal to 1")
        fmt_element = res.metadata.formats.all().first()
        self.assertEqual(fmt_element.value, format_CSV)

        # test adding files of different mime types creates one format element for each mime type
        res_file_3 = "file_three.tif"
        open(res_file_3, "w").close()
        file_obj_3 = open(res_file_3, "r")

        # reopen file_obj_1 for read
        file_obj_1 = open(res_file_1, "r")

        res = hydroshare.create_resource(resource_type='GenericResource',
                                         owner=self.user,
                                         title='Generic resource',
                                         files=(file_obj_1, file_obj_3)
                                        )
        # there should be two format elements at this point
        self.assertEquals(res.metadata.formats.all().count(), 2, msg="Number of format elements is not equal to 2")
        fmt_element = res.metadata.formats.all().filter(value__iexact=format_CSV).first()
        self.assertEqual(fmt_element.value, format_CSV)

        format_tif = "image/tiff"
        fmt_element = res.metadata.formats.all().filter(value__iexact=format_tif).first()
        self.assertEqual(fmt_element.value, format_tif)

    def test_format_element_auto_deletion(self):
        # deleting resource content files deletes format elements

        # create a file that will be used for creating a resource
        res_file_1 = "file_one.txt"
        open(res_file_1, "w").close()

        # open the file for read
        file_obj_1 = open(res_file_1, "r")
        res = hydroshare.create_resource(resource_type='GenericResource',
                                         owner=self.user,
                                         title='Generic resource',
                                         files=(file_obj_1,)
                                        )
        format_CSV = 'text/plain'
        # there should be only one format element at this point
        self.assertEquals(res.metadata.formats.all().count(), 1, msg="Number of format elements is not equal to 1")
        fmt_element = res.metadata.formats.all().first()
        self.assertEqual(fmt_element.value, format_CSV)

        # there should be only one file
        self.assertEquals(res.files.all().count(), 1) 
        
        # that file should be file_one.txt 
        self.assertEquals(res.files.all()[0].short_path, "file_one.txt") 

        # delete resource file
        hydroshare.delete_resource_file(res.short_id, file_obj_1.name, self.user)

        istorage = res.get_irods_storage()

        # there should be not be any format element at this point for this resource
        self.assertEquals(res.metadata.formats.all().count(), 0, msg="Number of format elements is not equal to 0")

        # add content files of same mime type to the resource
        res_file_2 = "file_two.txt"
        open(res_file_2, "w").close()

        # open the file for read
        file_obj_2 = open(res_file_2, "r")
        file_obj_1 = open(res_file_1, "r")
        hydroshare.add_resource_files(res.short_id, file_obj_1, file_obj_2)

        # the two files have the same format
        self.assertEquals(res.files.all().count(), 2) 

        # there should be one format element at this point for this resource
        self.assertEquals(res.metadata.formats.all().count(), 1, msg="Number of format elements is not equal to 1")
        fmt_element = res.metadata.formats.all().first()
        self.assertEqual(fmt_element.value, format_CSV)

        # delete resource file
        hydroshare.delete_resource_file(res.short_id, file_obj_1.name, self.user)

        # there should be still one format element at this point for this resource
        self.assertEquals(res.metadata.formats.all().count(), 1, msg="Number of format elements is not equal to 1")
        fmt_element = res.metadata.formats.all().first()
        self.assertEqual(fmt_element.value, format_CSV)

        # delete resource file
        hydroshare.delete_resource_file(res.short_id, file_obj_2.name, self.user)

        # there should be not be any format element at this point for this resource
        self.assertEquals(res.metadata.formats.all().count(), 0, msg="Number of format elements is not equal to 0")

    def test_identifier(self):
        # when a resource is created there should be one identifier element
        self.assertEqual(self.res.metadata.identifiers.all().count(), 1,
                         msg="Number of identifier elements not equal to 1.")
        self.assertIn('hydroShareIdentifier', [id.name for id in self.res.metadata.identifiers.all()],
                      msg="hydroShareIdentifier name was not found.")
        id_url = '{}/resource/{}'.format(hydroshare.utils.current_site_url(), self.res.short_id)
        self.assertIn(id_url, [id.url for id in self.res.metadata.identifiers.all()],
                      msg="Identifier url was not found.")

        # add another identifier
        resource.create_metadata_element(self.res.short_id,'identifier',
                                         name='someIdentifier', url="http://some.org/001")
        self.assertEqual(self.res.metadata.identifiers.all().count(), 2,
                         msg="Number of identifier elements not equal to 2.")
        self.assertIn('someIdentifier', [id.name for id in self.res.metadata.identifiers.all()],
                      msg="Identifier name was not found.")

        # identifier name needs to be unique - this one should raise an exception
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id,'identifier',
                                                                              name='someIdentifier',
                                                                              url="http://some.org/001"))

        # test that non-hydroshare identifier name can be updated
        some_idf = self.res.metadata.identifiers.all().filter(name='someIdentifier').first()
        resource.update_metadata_element(self.res.short_id, 'identifier', some_idf.id, name='someOtherIdentifier')
        self.assertIn('someOtherIdentifier', [id.name for id in self.res.metadata.identifiers.all()],
                      msg="Identifier name was not found.")

        # hydroshare internal identifier can't be updated - exception will occur
        hs_idf = self.res.metadata.identifiers.all().filter(name='hydroShareIdentifier').first()
        self.assertRaises(Exception, lambda: resource.update_metadata_element(self.res.short_id, 'identifier',
                                                                              hs_idf.id,
                                                                              name='anotherIdentifier'))
        self.assertRaises(Exception, lambda: resource.update_metadata_element(self.res.short_id, 'identifier',
                                                                              hs_idf.id,
                                                                              url='http://resources.org/001'))

        # test adding an identifier with name 'DOI' when the resource does not have a DOI - should raise an exception
        self.res.doi = None
        self.res.save()
        url_doi = "http://dx.doi.org/10.4211/hs.{res_id}".format(res_id=self.res.short_id)
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id,'identifier',
                                                                              name='DOI',  url=url_doi))

        # test adding identifier 'DOI' when the resource has a DOI and that should work
        self.res.doi = 'doi1000100010001'
        self.res.save()
        resource.create_metadata_element(self.res.short_id,'identifier', name='DOI', url=url_doi)

        # test that Identifier name 'DOI' can't be changed - should raise exception
        doi_idf = self.res.metadata.identifiers.all().filter(name='DOI').first()
        self.assertRaises(Exception, lambda: resource.update_metadata_element(self.res.short_id, 'identifier',
                                                                              doi_idf.id, name='DOI-1'))

        # test that 'DOI' identifier url can be changed
        resource.update_metadata_element(self.res.short_id, 'identifier', doi_idf.id, url='http://doi.org/001')

        # test that hydroshareidentifier can't be deleted - raise exception
        hs_idf = self.res.metadata.identifiers.all().filter(name='hydroShareIdentifier').first()
        self.assertRaises(Exception, lambda: resource.delete_metadata_element(self.res.short_id, 'identifier',
                                                                              hs_idf.id))

        # test that the DOI identifier can't be deleted when the resource has a DOI - should cause exception
        doi_idf = self.res.metadata.identifiers.all().filter(name='DOI').first()
        self.assertRaises(Exception, lambda: resource.delete_metadata_element(self.res.short_id, 'identifier',
                                                                              doi_idf.id))

        # test that identifier DOI can be deleted when the resource does not have a DOI.
        self.res.doi = None
        self.res.save()
        resource.delete_metadata_element(self.res.short_id, 'identifier', doi_idf.id)

    def test_language(self):
        # when the resource is created by default the language element should be created
        self.assertNotEqual(self.res.metadata.language, None, msg="Resource has no language element.")

        # the default language should be english
        self.assertEqual(self.res.metadata.language.code, 'eng', msg="Resource has language element which is not "
                                                                     "English.")

        # no more than one language element per resource - raises exception
        self.assertRaises(Exception, lambda : resource.create_metadata_element(self.res.short_id,'language',
                                                                               code='fre'))

        # should be able to update language
        resource.update_metadata_element(self.res.short_id,'language', self.res.metadata.language.id, code='fre')
        self.assertEqual(self.res.metadata.language.code, 'fre', msg="Resource has a language that is not French.")

        # it should be possible to delete the language element
        resource.delete_metadata_element(self.res.short_id,'language', self.res.metadata.language.id)
        self.assertEqual(self.res.metadata.language, None, msg="Resource has a language element.")

    def test_publisher(self):
        publisher_CUAHSI = "Consortium of Universities for the Advancement of Hydrologic Science, Inc. (CUAHSI)"
        url_CUAHSI = 'https://www.cuahsi.org'

        # publisher element can't be added when the resource is not published
        self.res.raccess.published = False
        self.res.raccess.save()
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.res.short_id, 'publisher', name='HydroShare',
                                             url="http://hydroshare.org")

        # publisher element can be added when the resource is published
        self.res.raccess.published = True
        self.res.raccess.save()
        resource.create_metadata_element(self.res.short_id, 'publisher', name='USGS', url="http://usgs.gov")
        self.assertEqual(self.res.metadata.publisher.url, "http://usgs.gov",
                         msg="Resource publisher url did not match.")
        self.assertEqual(self.res.metadata.publisher.name, "USGS", msg="Resource publisher name did not match.")

        # a 2nd publisher element can't be created - should raise exception
        with self.assertRaises(Exception):
            resource.create_metadata_element(self.res.short_id, 'publisher', name='USU', url="http://usu.edu")

        # test that updating publisher element raises exception
        with self.assertRaises(Exception):
            resource.update_metadata_element(self.res.short_id, 'publisher', self.res.metadata.publisher.id,
                                             name='USU', url="http://usu.edu")

        # Test that when a resource has one or more content files, the publisher has to be CUASHI
        # publisher name 'CUAHSI' only and publisher url to 'https://www.cuahsi.org' only.
        # create a different resource
        res_with_files = hydroshare.create_resource(
            resource_type='GenericResource',
            owner=self.user,
            title='Generic resource with files',
        )

        # check the resource is not published
        self.assertFalse(res_with_files.raccess.published)

        res_with_files.raccess.published = True
        res_with_files.raccess.save()

        # trying to make CUAHSI as the publisher for a resource that has no content files should raise exception
        with self.assertRaises(Exception):
            resource.create_metadata_element(res_with_files.short_id, 'publisher', name=publisher_CUAHSI,
                                             url=url_CUAHSI)

        # create a file
        original_file_name = 'original.txt'
        original_file = open(original_file_name, 'w')
        original_file.write("original text")
        original_file.close()

        original_file = open(original_file_name, 'r')
        # add the file to the resource
        hydroshare.add_resource_files(res_with_files.short_id, original_file)

        # trying to set publisher someone other than CUAHSI for a resource that has content files
        # should raise exception
        with self.assertRaises(Exception):
            resource.create_metadata_element(res_with_files.short_id, 'publisher', name='USU', url="http://usu.edu")

        # only 'CUAHSI" can be set as the publisher for a resource that has content files
        resource.create_metadata_element(res_with_files.short_id, 'publisher', name=publisher_CUAHSI,
                                         url=url_CUAHSI)

        self.assertEqual(res_with_files.metadata.publisher.name, publisher_CUAHSI,
                         msg="Resource publisher name did not match.")
        self.assertEqual(res_with_files.metadata.publisher.url, url_CUAHSI,
                         msg="Resource publisher url did not match.")

        # trying to delete the publisher should raise exception
        with self.assertRaises(Exception):
            resource.delete_metadata_element(res_with_files.short_id, 'publisher', self.res.metadata.publisher.id)

    def test_relation(self):
        # at this point there should not be any relation elements
        self.assertEqual(self.res.metadata.relations.all().count(), 0, msg="Resource has relation element(s).")

        # add a relation element of uri type
        resource.create_metadata_element(self.res.short_id,'relation', type='isPartOf',
                                         value='http://hydroshare.org/resource/001')
        # at this point there should be 1 relation element
        self.assertEqual(self.res.metadata.relations.all().count(), 1,
                         msg="Number of source elements is not equal to 1")
        self.assertIn('isPartOf', [rel.type for rel in self.res.metadata.relations.all()],
                      msg="No relation element of type 'isPartOF' was found")

        # add another relation element of uri type
        resource.create_metadata_element(self.res.short_id,'relation', type='isDataFor',
                                         value='http://hydroshare.org/resource/002')

        # at this point there should be 2 relation elements
        self.assertEqual(self.res.metadata.relations.all().count(), 2,
                         msg="Number of source elements is not equal to 2")
        self.assertIn('isPartOf', [rel.type for rel in self.res.metadata.relations.all()],
                      msg="No relation element of type 'isPartOf' was found")
        self.assertIn('isDataFor', [rel.type for rel in self.res.metadata.relations.all()],
                      msg="No relation element of type 'isDataFor' was found")

        # add another relation element with isHostedBy type
        resource.create_metadata_element(self.res.short_id,'relation', type='isHostedBy',
                                value='https://www.cuahsi.org/')

        # at this point there should be 3 relation elements
        self.assertEqual(self.res.metadata.relations.all().count(), 3,
                         msg="Number of source elements is not equal to 3")
        self.assertIn('isHostedBy', [rel.type for rel in self.res.metadata.relations.all()],
                      msg="No relation element of type 'isHostedBy' was found")
        self.assertIn('isPartOf', [rel.type for rel in self.res.metadata.relations.all()],
                      msg="No relation element of type 'isPartOf' was found")
        self.assertIn('isDataFor', [rel.type for rel in self.res.metadata.relations.all()],
                      msg="No relation element of type 'isDataFor' was found")

        # test isHostedBy and isCopiedFrom are mutually exclusive
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id,'relation',
                                                                              type='isCopiedFrom',
                                                                              value='Another Source'))

        rel_to_update = self.res.metadata.relations.all().filter(type='isHostedBy').first()
        self.assertRaises(Exception, lambda: resource.update_metadata_element(self.res.short_id,
                                                                              'relation',
                                                                              rel_to_update.id,
                                                                              type='isCopiedFrom',
                                                                              value="dummy value 1"))

        # test that cannot create a relation that is identical to an existing one
        # (same type and same value) is not allowed
        self.assertTrue(self.res.metadata.relations.all().
                        filter(type='isHostedBy', value='https://www.cuahsi.org/').exists())
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id,
                          'relation', type='isHostedBy', value='https://www.cuahsi.org/'))

        # test update relation type
        rel_to_update = self.res.metadata.relations.all().filter(type='isPartOf').first()
        resource.update_metadata_element(self.res.short_id, 'relation', rel_to_update.id,
                                         type='isVersionOf', value="dummy value 2")
        self.assertIn('isVersionOf', [rel.type for rel in self.res.metadata.relations.all()],
                      msg="No relation element of type 'isVersionOf' was found")

        # test update relation value
        rel_to_update = self.res.metadata.relations.all().filter(type='isVersionOf').first()
        # missing any of 'type' and 'value' is not allowed:
        self.assertRaises(Exception,
                          lambda: resource.
                          update_metadata_element(self.res.short_id, 'relation', rel_to_update.id,
                                                  value='Another resource'))
        self.assertRaises(Exception,
                          lambda: resource.
                          update_metadata_element(self.res.short_id, 'relation', rel_to_update.id,
                                                  type='isVersionOf'))

        resource.update_metadata_element(self.res.short_id, 'relation', rel_to_update.id, type='isVersionOf',
                                         value='Another resource')
        self.assertIn('isVersionOf', [rel.type for rel in self.res.metadata.relations.all()],
                      msg="No relation element of type 'isVersionOf' was found")
        self.assertIn('Another resource', [rel.value for rel in self.res.metadata.relations.all()],
                      msg="No relation element of value 'Another resource' was found")

        # test that cannot update relation to what is identical to an existing one
        rel_to_update = self.res.metadata.relations.all().filter(type='isVersionOf').first()
        self.assertTrue(self.res.metadata.relations.all().
                        filter(type='isHostedBy', value='https://www.cuahsi.org/').exists())
        self.assertRaises(Exception,
                          lambda: resource.
                          update_metadata_element(self.res.short_id,
                                                  'relation',
                                                  rel_to_update.id,
                                                  type='isHostedBy',
                                                  value='https://www.cuahsi.org/'))

        # test that it is possible to delete all relation elements
        for rel in self.res.metadata.relations.all():
            resource.delete_metadata_element(self.res.short_id,'relation', rel.id)

        # at this point there should not be any relation elements
        self.assertEqual(self.res.metadata.relations.all().count(), 0,
                         msg="Resource has relation element(s) after deleting all.")

        # test to add relation element with isCopiedFrom type
        resource.create_metadata_element(self.res.short_id,'relation', type='isCopiedFrom',
                                value='https://www.cuahsi.org/')
        # at this point there should be 1 relation element
        self.assertEqual(self.res.metadata.relations.all().count(), 1,
                         msg="Number of source elements is not equal to 1")
        self.assertIn('isCopiedFrom', [rel.type for rel in self.res.metadata.relations.all()],
                      msg="No relation element of type 'isCopiedFrom' was found")

        # test update relation value
        rel_to_update = self.res.metadata.relations.all().filter(type='isCopiedFrom').first()
        resource.update_metadata_element(self.res.short_id, 'relation', rel_to_update.id, type='isCopiedFrom',
                                         value='Another Source')
        self.assertIn('isCopiedFrom', [rel.type for rel in self.res.metadata.relations.all()],
                      msg="No relation element of type 'isCopiedFrom' was found")
        self.assertIn('Another Source', [rel.value for rel in self.res.metadata.relations.all()],
                      msg="No relation element of value 'Another Source' was found")

        # test isHostedBy and isCopiedFrom are mutually exclusive
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id,'relation',
                                                                              type='isHostedBy',
                                                                              value='https://www.cuahsi.org/'))

        rel_to_update = self.res.metadata.relations.all().filter(type='isCopiedFrom').first()
        self.assertRaises(Exception, lambda: resource.
                          update_metadata_element(self.res.short_id,
                                                  'relation',
                                                  rel_to_update.id,
                                                  type='isHostedBy',
                                                  value="dummy value 3"))

        # test that it is possible to delete all relation elements
        for rel in self.res.metadata.relations.all():
            resource.delete_metadata_element(self.res.short_id, 'relation', rel.id)

        # at this point there should not be any relation elements
        self.assertEqual(self.res.metadata.relations.all().count(), 0,
                         msg="Resource has relation element(s) after deleting all.")

    def test_funding_agency(self):
        # at this point there should not be any funding agency elements
        self.assertEqual(self.res.metadata.funding_agencies.all().count(), 0)
        # add a funding agency element with only the required name value type
        resource.create_metadata_element(self.res.short_id,'fundingagency', agency_name='NSF')
        # at this point there should be one funding agency element
        self.assertEqual(self.res.metadata.funding_agencies.all().count(), 1)
        # test the name of the funding agency is NSF
        agency_element = self.res.metadata.funding_agencies.all().first()
        self.assertEquals(agency_element.agency_name, 'NSF')
        # add another funding agency element with only the required name value type
        resource.create_metadata_element(self.res.short_id,'fundingagency', agency_name='USDA')
        # at this point there should be 2 funding agency element
        self.assertEqual(self.res.metadata.funding_agencies.all().count(), 2)
        # there should be one funding agency with name USDA
        agency_element = self.res.metadata.funding_agencies.all().filter(agency_name='USDA').first()
        self.assertNotEquals(agency_element, None)

        # test update
        resource.update_metadata_element(self.res.short_id, 'fundingagency', agency_element.id,
                                         award_title="Cyber Infrastructure", award_number="NSF-101-20-6789",
                                         agency_url="http://www.nsf.gov")
        agency_element = self.res.metadata.funding_agencies.all().filter(agency_name='USDA').first()
        self.assertEquals(agency_element.agency_name, 'USDA')
        self.assertEquals(agency_element.award_title, 'Cyber Infrastructure')
        self.assertEquals(agency_element.award_number, 'NSF-101-20-6789')
        self.assertEquals(agency_element.agency_url, 'http://www.nsf.gov')

        # test there can be duplicate funding agency elements for a given resource
        resource.create_metadata_element(self.res.short_id, 'fundingagency', agency_name="EPA",
                                         award_title="Cyber Infrastructure", award_number="NSF-101-20-6789",
                                         agency_url="http://www.epa.gov")

        resource.create_metadata_element(self.res.short_id, 'fundingagency', agency_name="EPA",
                                         award_title="Cyber Infrastructure", award_number="NSF-101-20-6789",
                                         agency_url="http://www.epa.gov")

        self.assertEquals(self.res.metadata.funding_agencies.all().filter(agency_name='EPA').count(), 2)

        # test that agency name is required for  creating a funding agency element
        self.assertEquals(self.res.metadata.funding_agencies.all().count(), 4)
        with self.assertRaises(ValidationError):
            resource.create_metadata_element(self.res.short_id, 'fundingagency',
                                             award_title="Modeling on cloud",
                                             award_number="101-20-6789",
                                             agency_url="http://www.usa.gov")

        # at this point there should be 4 funding agency element
        self.assertEqual(self.res.metadata.funding_agencies.all().count(), 4)

        # test that it is possible to delete all funding agency elements
        for agency in self.res.metadata.funding_agencies.all():
            resource.delete_metadata_element(self.res.short_id,'fundingagency', agency.id)

        # at this point there should not be any funding agency element
        self.assertEqual(self.res.metadata.funding_agencies.all().count(), 0)

    def test_rights(self):
        # By default a resource should have the rights element
        self.assertNotEqual(self.res.metadata.rights, None, msg="Resource has no rights element.")

        default_rights_statement = 'This resource is shared under the Creative Commons Attribution CC BY.'
        default_rights_url = 'http://creativecommons.org/licenses/by/4.0/'
        self.assertEqual(self.res.metadata.rights.statement,
                         default_rights_statement, msg="Rights statement didn't match")
        self.assertEqual(self.res.metadata.rights.url, default_rights_url, msg="URL of rights did not match.")

        # can't have more than one rights elements
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id,
                                                                              'rights',
                                                                              statement='This is the rights statement '
                                                                                        'for this resource',
                                                                              url='http://rights.ord/001'))

        # deleting rights element is not allowed - exception
        self.assertRaises(Exception, lambda : resource.delete_metadata_element(self.res.short_id,'rights',
                                                                               self.res.metadata.rights.id))

        # should be able to update the rights element
        resource.update_metadata_element(self.res.short_id, 'rights', self.res.metadata.rights.id,
                                         statement='This is the modified rights statement for this resource',
                                         url='http://rights-modified.ord/001')
        self.assertEqual(self.res.metadata.rights.statement, 'This is the modified rights statement for this resource',
                         msg="Statement of rights did not match.")
        self.assertEqual(self.res.metadata.rights.url, 'http://rights-modified.ord/001',
                         msg="URL of rights did not match.")

    def test_source(self):
        # at this point there should not be any source element
        self.assertEqual(self.res.metadata.sources.all().count(), 0, msg="Number of sources is not equal to 0.")

        # add a source element of uri type
        resource.create_metadata_element(self.res.short_id,'source', derived_from='http://hydroshare.org/resource/0001')
        # at this point there should be 1 source element
        self.assertEqual(self.res.metadata.sources.all().count(), 1, msg="Number of sources is not equal to 1.")
        self.assertIn('http://hydroshare.org/resource/0001', [src.derived_from for src in
                                                              self.res.metadata.sources.all()],
                      msg="Source element with derived from a value of %s does not exist." %
                          'http://hydroshare.org/resource/0001')

        #test update
        src_1 = self.res.metadata.sources.all().filter(derived_from='http://hydroshare.org/resource/0001').first()
        resource.update_metadata_element(self.res.short_id, 'source', src_1.id,
                                         derived_from='http://hydroshare.org/resource/0002')
        self.assertIn('http://hydroshare.org/resource/0002', [src.derived_from for src in
                                                              self.res.metadata.sources.all()],
                      msg="Source element with derived from a value of %s does not exist."
                          % 'http://hydroshare.org/resource/0002')

        # add another source element of string type
        resource.create_metadata_element(self.res.short_id,'source', derived_from='This resource has been derived '
                                                                                  'from another resource')
        # at this point there should be 2 source element
        self.assertEqual(self.res.metadata.sources.all().count(), 2, msg="Number of sources is not equal to 2.")

        # duplicate source elements are not allowed - exception raised
        self.assertRaises(Exception, lambda:resource.create_metadata_element(
            self.res.short_id, 'source', derived_from='http://hydroshare.org/resource/0002'))

        # test that it is possible to delete all source elements
        for src in self.res.metadata.sources.all():
            resource.delete_metadata_element(self.res.short_id,'source', src.id)

    def test_subject(self):
        # there should be 2 subject elements for this resource as we provided two keywords when creating the resource
        self.assertEqual(self.res.metadata.subjects.all().count(), 2, msg="Number of subject elements found not be 2.")

        # delete all existing subject elements
        self.res.metadata.subjects.all().delete()

        # add a subject element
        resource.create_metadata_element(self.res.short_id,'subject', value='sub-1')

        # there should be 1 subject element for this resource
        self.assertEqual(self.res.metadata.subjects.all().count(), 1, msg="Number of subject elements found not be 1.")
        self.assertIn('sub-1', [sub.value for sub in self.res.metadata.subjects.all()],
                      msg="Subject element with value of %s does not exist." % 'sub-1')

        # add another subject element
        resource.create_metadata_element(self.res.short_id,'subject', value='sub-2')

        # there should be 2 subject elements for this resource
        self.assertEqual(self.res.metadata.subjects.all().count(), 2, msg="Number of subject elements found not be 1.")
        self.assertIn('sub-1', [sub.value for sub in self.res.metadata.subjects.all()],
                      msg="Subject element with value of %s does not exist." % 'sub-1')
        self.assertIn('sub-2', [sub.value for sub in self.res.metadata.subjects.all()],
                      msg="Subject element with value of %s does not exist." % 'sub-1')

        # add another subject element with duplicate value (note values are case insensitive for
        # determining duplicates)
        # - should raise exception
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id, 'subject',
                                                                              value='sub-2'))
        self.assertRaises(Exception,
                          lambda: resource.create_metadata_element(self.res.short_id, 'subject',
                                                                   value='Sub-2'))

        # test sub-element update
        sub_1 = self.res.metadata.subjects.all().filter(value='sub-1').first()
        resource.update_metadata_element(self.res.short_id, 'subject', sub_1.id, value='sub-1.1')
        self.assertIn('sub-1.1', [sub.value for sub in self.res.metadata.subjects.all()],
                      msg="Subject element with value of %s does not exist." % 'sub-1.1')

        # test deleting of subject elements - all but the last one can be deleted
        resource.delete_metadata_element(self.res.short_id, 'subject', sub_1.id)
        # there should be 1 subject element for this resource
        self.assertEqual(self.res.metadata.subjects.all().count(), 1, msg="Number of subject elements found not be 1.")

        # deleting the last subject element should raise exception
        sub_2 = self.res.metadata.subjects.all().filter(value='sub-2').first()
        self.assertRaises(Exception, lambda: resource.delete_metadata_element(self.res.short_id, 'subject', sub_2.id))

    def test_type(self):
        # type element is auto created at the resource creation (see test_auto_element_creation)
        # adding a 2nd type element should raise exception
        self.assertRaises(Exception, lambda: resource.create_metadata_element(self.res.short_id, 'type',
                                                                              url="http://hydroshare.org/generic"))

        # it should be possible to update the type element
        resource.update_metadata_element(self.res.short_id, 'type', self.res.metadata.type.id,
                                         url="http://hydroshare2.org/generic")
        self.assertEqual(self.res.metadata.type.url, "http://hydroshare2.org/generic",
                         msg="Resource type url did not match.")

        # deleting of type element is not allowed.
        self.assertRaises(Exception, lambda: resource.delete_metadata_element(self.res.short_id, 'type',
                                                                              self.res.metadata.type.id))

    def test_get_xml(self):

        # change the title
        resource.update_metadata_element(self.res.short_id, 'title', self.res.metadata.title.id,
                                         value="Test generic resource")

        # add another creator with all sub_elements
        cr_name = 'Mike Sundar'
        cr_des = 'http://hydroshare.org/user/001'
        cr_org = "USU"
        cr_email = 'mike.sundar@usu.edu'
        cr_address = "11 River Drive, Logan UT-84321, USA"
        cr_phone = '435-567-0989'
        cr_homepage = 'http://usu.edu/homepage/001'

        self.res.metadata.create_element('creator',
                                         name=cr_name,
                                         description=cr_des,
                                         organization=cr_org,
                                         email=cr_email,
                                         address=cr_address,
                                         phone=cr_phone,
                                         homepage=cr_homepage,
                                         profile_links=[{'type': 'researchID', 'url': 'http://research.org/001'},
                                               {'type': 'researchGateID', 'url': 'http://research-gate.org/001'}]
                                        )

        # add another creator with only the name
        self.res.metadata.create_element('creator', name='Lisa Holley')

        # test adding a contributor with all sub_elements
        con_name = 'Sujan Peterson'
        con_des = 'http://hydroshare.org/user/002'
        con_org = "USU"
        con_email = 'sujan.peterson@usu.edu'
        con_address = "101 Center St, Logan UT-84321, USA"
        con_phone = '435-567-3245'
        con_homepage = 'http://usu.edu/homepage/009'

        self.res.metadata.create_element('contributor',
                                         name=con_name,
                                         description=con_des,
                                         organization=con_org,
                                         email=con_email,
                                         address=con_address,
                                         phone=con_phone,
                                         homepage=con_homepage,
                                        )
        # add another creator with only the name
        self.res.metadata.create_element('contributor', name='Andrew Smith')

        # add a period type coverage
        value_dict = {'name':'fall season' , 'start':'1/1/2000', 'end':'12/12/2012'}
        self.res.metadata.create_element('coverage', type='period', value=value_dict)

        # TODO: add a point type coverage
        # value_dict = {'east':'56.45678', 'north':'12.6789', 'units': 'decimal deg', 'name': 'Little bear river',
        #               'elevation': '34.6789', 'zunits': 'rad deg', 'projection': 'NAD83'}
        # self.res.metadata.create_element('coverage', type='point', value=value_dict)

        # TODO: test box type coverage - uncomment this one and comment the above point type test
        value_dict = {'northlimit':'56.45678', 'eastlimit':'120.6789','southlimit':'16.45678', 'westlimit':'16.6789',
                      'units': 'decimal deg','name': 'Bear river', 'uplimit': '45.234', 'downlimit': '12.345',
                      'zunits': 'decimal deg', 'projection': 'NAD83'}
        self.res.metadata.create_element('coverage', type='box', value=value_dict)

        # add date of type 'valid'
        self.res.metadata.create_element('date', type='valid', start_date=parser.parse('8/10/2011'),
                                         end_date=parser.parse('8/11/2012'))

        # add a format element
        format_csv = 'text/csv'
        self.res.metadata.create_element('format', value=format_csv)

        # add 'DOI' identifier
        self.res.doi='doi1000100010001'
        self.res.save()
        self.res.metadata.create_element('identifier', name='DOI', url="http://dx.doi.org/001")

        # no need to add a language element - language element is created at the time of resource creation

        # add 'Publisher' element
        original_file_name = 'original.txt'
        original_file = open(original_file_name, 'w')
        original_file.write("original text")
        original_file.close()

        original_file = open(original_file_name, 'r')
        # add the file to the resource
        hydroshare.add_resource_files(self.res.short_id, original_file)

        publisher_CUAHSI = "Consortium of Universities for the Advancement of Hydrologic Science, Inc. (CUAHSI)"
        url_CUAHSI = 'https://www.cuahsi.org'
        self.res.raccess.published=True
        self.res.raccess.save()
        self.res.metadata.create_element('publisher', name=publisher_CUAHSI, url=url_CUAHSI)

        # add a relation element of uri type
        self.res.metadata.create_element('relation', type='isPartOf',
                                         value='http://hydroshare.org/resource/001')

        # add another relation element of non-uri type
        self.res.metadata.create_element('relation', type='isDataFor',
                                         value='This resource is for another resource')


        # add a source element of uri type
        self.res.metadata.create_element('source', derived_from='http://hydroshare.org/resource/0002')

        # No need to ass rights element as this one gets created at the time of resource creation

        # add a subject element
        self.res.metadata.create_element('subject', value='sub-1')

        # add another subject element
        self.res.metadata.create_element('subject', value='sub-2')

        # add funding agency
        self.res.metadata.create_element('fundingagency', agency_name='NSF',
                                         award_title="Cyber Infrastructure", award_number="NSF-101-20-6789",
                                         agency_url="http://www.nsf.gov")
        # check the content of the metadata xml string
        RDF_ROOT = etree.XML(self.res.metadata.get_xml())

        # check root 'Description' element
        container = RDF_ROOT.find('rdf:Description', namespaces=self.res.metadata.NAMESPACES)

        self.assertNotEqual(container, None, msg="Root 'Description' element was not found.")
        #res_uri = 'http://hydroshare.org/resource/%s' % self.res.short_id
        res_uri = '{}/resource/{}'.format(hydroshare.utils.current_site_url(), self.res.short_id)

        self.assertEqual(container.get('{%s}about' % self.res.metadata.NAMESPACES['rdf']), res_uri,
                         msg="'Description' element attribute value did not match.")

        title_sub_element = container.find('dc:title', namespaces=self.res.metadata.NAMESPACES)
        self.assertEqual(title_sub_element.text, self.res.metadata.title.value,
                         msg="'Title element attribute value did not match.")

        type_sub_element = container.find('dc:type', namespaces=self.res.metadata.NAMESPACES)
        self.assertEqual(type_sub_element.get('{%s}resource' % self.res.metadata.NAMESPACES['rdf']),
                         self.res.metadata.type.url,
                         msg="'Resource type element url attribute value did not match.")

        # TODO: check all other elements (their text values and/or attribute values)

        #abstract_sub_element = RDF_ROOT.find('.//dcterms:abstract', namespaces=self.res.metadata.NAMESPACES)
        # self.assertEqual(abstract_sub_element.text, self.res.metadata.description.abstract,
        #                  msg="'Description element abstract attribute value did not match.")

        #print (abstract_sub_element.text)
        #print(self.res.metadata.description.abstract)
        #print (container.get('{%s}title' % self.res.metadata.NAMESPACES['dc']))
        #print self.res.metadata.get_xml()
        #print (bad)

    def test_metadata_delete_on_resource_delete(self):
        # when a resource is deleted all the associated metadata elements should be deleted
        # create a abstract for the resource
        resource.create_metadata_element(self.res.short_id, 'description', abstract='new abstract for the resource')
        # add a format element
        format_csv = 'text/csv'
        resource.create_metadata_element(self.res.short_id, 'format', value=format_csv)
        # add a contributor element
        resource.create_metadata_element(self.res.short_id, 'contributor', name='John Smith')
        # add a period type coverage
        value_dict = {'name': 'Name for period coverage', 'start': '1/1/2000', 'end': '12/12/2012'}
        resource.create_metadata_element(self.res.short_id,'coverage', type='period', value=value_dict)
        # add another identifier
        resource.create_metadata_element(self.res.short_id,'identifier',
                                         name='someIdentifier', url="http://some.org/001")

        # add a source element of uri type
        resource.create_metadata_element(self.res.short_id,'source', derived_from='http://hydroshare.org/resource/0001')
        core_metadata_obj = self.res.metadata
        # add a relation element of uri type
        resource.create_metadata_element(self.res.short_id,'relation', type='isPartOf',
                                value='http://hydroshare.org/resource/001')

        # add publisher element
        self.res.raccess.published = True
        self.res.raccess.save()
        resource.create_metadata_element(self.res.short_id, 'publisher', name='USGS', url="http://usgs.gov")

        # add funding agency element
        resource.create_metadata_element(self.res.short_id, 'fundingagency', agency_name='NSF',
                                         award_title="Cyber Infrastructure", award_number="NSF-101-20-6789",
                                         agency_url="http://www.nsf.gov")
        # before resource delete
        self.assertEquals(CoreMetaData.objects.all().count(), 1, msg="# of CoreMetadata objects is not equal to 1.")
        # there should be Creator metadata objects
        self.assertTrue(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Contributor metadata objects
        self.assertTrue(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Identifier metadata objects
        self.assertTrue(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Type metadata objects
        self.assertTrue(Type.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Source metadata objects
        self.assertTrue(Source.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Relation metadata objects
        self.assertTrue(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Publisher metadata objects
        self.assertTrue(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Title metadata objects
        self.assertTrue(Title.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Description (Abstract) metadata objects
        self.assertTrue(Description.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Date metadata objects
        self.assertTrue(Date.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Subject metadata objects
        self.assertTrue(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Coverage metadata objects
        self.assertTrue(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Format metadata objects
        self.assertTrue(Format.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Language metadata objects
        self.assertTrue(Language.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Rights metadata objects
        self.assertTrue(Rights.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be FundingAgency metadata objects
        self.assertTrue(FundingAgency.objects.filter(object_id=core_metadata_obj.id).exists())

        # delete resource
        hydroshare.delete_resource(self.res.short_id)
        self.assertEquals(CoreMetaData.objects.all().count(), 0, msg="CoreMetadata object was found")

        # there should be no Creator metadata objects
        self.assertFalse(Creator.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Contributor metadata objects
        self.assertFalse(Contributor.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Identifier metadata objects
        self.assertFalse(Identifier.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Type metadata objects
        self.assertFalse(Type.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Source metadata objects
        self.assertFalse(Source.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Relation metadata objects
        self.assertFalse(Relation.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be Publisher metadata objects
        self.assertFalse(Publisher.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Title metadata objects
        self.assertFalse(Title.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Description (Abstract) metadata objects
        self.assertFalse(Description.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Date metadata objects
        self.assertFalse(Date.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Subject metadata objects
        self.assertFalse(Subject.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Coverage metadata objects
        self.assertFalse(Coverage.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Format metadata objects
        self.assertFalse(Format.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Language metadata objects
        self.assertFalse(Language.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no Rights metadata objects
        self.assertFalse(Rights.objects.filter(object_id=core_metadata_obj.id).exists())
        # there should be no FundingAgency metadata objects
        self.assertFalse(FundingAgency.objects.filter(object_id=core_metadata_obj.id).exists())

