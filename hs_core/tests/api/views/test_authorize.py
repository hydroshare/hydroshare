from django.contrib.auth.models import Group, AnonymousUser
from django.test import TestCase, RequestFactory
from rest_framework.exceptions import PermissionDenied, NotFound

from hs_core.hydroshare import resource
from hs_core.hydroshare import users
from hs_core.testing import MockIRODSTestCaseMixin
from hs_core.views.utils import authorize
from hs_access_control.models import PrivilegeCodes

class TestAuthorize(MockIRODSTestCaseMixin, TestCase):

    def setUp(self):
        super(TestAuthorize, self).setUp()
        self.group, _ = Group.objects.get_or_create(name='Hydroshare Author')
        # create a user - resource owner
        self.user = users.create_account(
            'test_user@email.com',
            username='testuser',
            first_name='some_first_name',
            last_name='some_last_name',
            superuser=False,
            groups=[])
        self.res = resource.create_resource(
            'GenericResource',
            self.user,
            'My Test Resource'
            )

        self.request = RequestFactory().request()

    def test_authorize_owner(self):
        common_parameters = [
                      # setting of parameter 'discoverable' has no effect for owner authorization

                      # resource owner has authorization for resource view (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None}
                      ]

        parameters = [
                      # setting of parameter 'discoverable' has no effect for owner authorization

                      # resource owner has authorization for resource edit (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': True, 'exception': None},

                      # resource owner has authorization for resource delete or setting resource flags
                      # (public, published/immutable, shareable etc)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': True, 'exception': None}
                      ] + common_parameters

        self.request.user = self.user

        # test for private resource
        self.assertFalse(self.res.raccess.public)
        self.assertFalse(self.res.raccess.discoverable)

        self._run_tests(self.request, parameters)

        # test for discoverable resource
        self.assertFalse(self.res.raccess.discoverable)
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = True
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

        # test for public resource
        self.assertTrue(self.res.raccess.discoverable)
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = False
        self.res.raccess.public = True
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

        # test for immutable/published resource
        self.assertFalse(self.res.raccess.immutable)
        self.assertFalse(self.res.raccess.published)
        self.assertTrue(self.res.raccess.public)

        self.res.raccess.published = True
        self.res.raccess.immutable = True
        self.res.raccess.save()

        parameters = [
                      # setting of parameter 'discoverable' has no effect for owner authorization

                      # resource owner has authorization for view of published resource
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},

                      # resource owner has no authorization for editing a published resource
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},

                      # resource owner has no authorization for deleting a published resource or setting resource
                      # flags (public, immutable/published, shareable etc)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

    def test_authorize_editor(self):
        # create edit_user
        edit_user = users.create_account(
                'edit_user@email.com',
                username='edituser',
                first_name='edit_first_name',
                last_name='edit_last_name',
                superuser=False,
                groups=[])

        self.request.user = edit_user

        common_parameters = [
                      # parameter 'discoverable' has no effect on authorization

                      # resource editor has authorization for resource view (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},

                      # resource editor has no authorization for deleting a resource or changing resource flags
                      # (e.g., public, published/immutable, shareable etc)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied}
                      ]

        parameters = [
                      # parameter 'discoverable' has no effect on authorization

                      # resource editor has authorization for resource edit (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': True, 'exception': None}
                      ] + common_parameters

        # grant edit_user edit permission
        self.user.uaccess.share_resource_with_user(self.res, edit_user, PrivilegeCodes.CHANGE)

        # test for private resource
        self.assertFalse(self.res.raccess.public)
        self.assertFalse(self.res.raccess.discoverable)

        self._run_tests(self.request, parameters)

        # test for discoverable resource
        self.assertFalse(self.res.raccess.discoverable)
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = True
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

        # test for public resource
        self.assertTrue(self.res.raccess.discoverable)
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = False
        self.res.raccess.public = True
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

        # test for immutable/published resource
        self.assertFalse(self.res.raccess.immutable)
        self.assertFalse(self.res.raccess.published)
        self.assertTrue(self.res.raccess.public)

        self.res.raccess.immutable = True
        self.res.raccess.published = True
        self.res.raccess.save()

        parameters = [
                      # parameter 'discoverable' has no effect on authorization

                      # resource editor has authorization for published resource view (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},

                      # resource editor has no authorization for editing a published resource
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

    def test_authorize_viewer(self):
        # create view_user
        view_user = users.create_account(
            'view_user@email.com',
            username='viewuser',
            first_name='view_first_name',
            last_name='view_last_name',
            superuser=False,
            groups=[])

        self.request.user = view_user

        parameters = [
                      # parameter 'discoverable' has no effect on authorization

                      # resource viewer has authorization for resource metadata view
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},
                      # resource viewer has authorization for resource view (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},

                      # resource viewer has no authorization for editing a resource
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},

                      # resource viewer has no authorization for deleting a resource or changing resource flags
                      # (e.g., public, published/immutable, shareable etc)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied}
                      ]

        # grant view_user view permission
        self.user.uaccess.share_resource_with_user(self.res, view_user, PrivilegeCodes.VIEW)

        # test for private resource
        self.assertFalse(self.res.raccess.public)
        self.assertFalse(self.res.raccess.discoverable)

        self._run_tests(self.request, parameters)

        # test for discoverable resource
        self.assertFalse(self.res.raccess.discoverable)
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = True
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

        # test for public resource
        self.assertTrue(self.res.raccess.discoverable)
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = False
        self.res.raccess.public = True
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

        # test for immutable/published resource
        self.assertFalse(self.res.raccess.immutable)
        self.assertFalse(self.res.raccess.published)
        self.assertTrue(self.res.raccess.public)

        self.res.raccess.immutable = True
        self.res.raccess.published = True
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

    def test_authorize_superuser(self):
        # create super user
        super_user = users.create_account(
            'super_user@email.com',
            username='superuser',
            first_name='super_first_name',
            last_name='super_last_name',
            superuser=True,
            groups=[])

        self.request.user = super_user

        common_parameters = [
                      # parameter 'discoverable' has no effect on authorization

                      # super user has authorization for resource view (both metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},

                      # super user has authorization for resource edit
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': True, 'exception': None}
                      ]

        parameters = [
                      # super user has no authorization for resource delete or setting resource flags (e.g., public,
                      # published/immutable, shareable etc)
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': True, 'exception': None}
                      ] + common_parameters

        # test for private resource
        self.assertFalse(self.res.raccess.public)
        self.assertFalse(self.res.raccess.discoverable)

        self._run_tests(self.request, parameters)

        # test for discoverable resource
        self.assertFalse(self.res.raccess.discoverable)
        self.res.raccess.discoverable = True
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

        # test for public resource
        self.assertTrue(self.res.raccess.discoverable)
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = False
        self.res.raccess.public = True
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

        # test for immutable/published resource
        self.assertFalse(self.res.raccess.immutable)
        self.assertFalse(self.res.raccess.published)
        self.assertTrue(self.res.raccess.public)

        self.res.raccess.immutable = True
        self.res.raccess.published = True
        self.res.raccess.save()

        parameters = [
                      # super user has no authorization for resource delete or setting resource flags (e.g., public,
                      # published/immutable, shareable etc)
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

    def test_authorize_anonymous_user(self):
        self.request.user = AnonymousUser()
        common_parameters = [
                      # setting of parameter 'discoverable' has no effect for anonymous user authorization when
                      # resource is not discoverable

                      # anonymous user has no authorization for resource edit (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},

                      # anonymous user has no authorization for resource delete
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied}
                      ]

        # test for private resource
        self.assertFalse(self.res.raccess.public)
        self.assertFalse(self.res.raccess.discoverable)

        self._run_tests(self.request, common_parameters)

        # test for discoverable resource
        self.res.raccess.discoverable = True
        self.res.raccess.public = False
        self.res.raccess.save()

        parameters = [
                      # anonymous user has no authorization for resource view (metadata and content files) for a
                      # resource that is discoverable
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': False, 'exception': PermissionDenied},
                      # anonymous user has authorization for metadata view for a resource that is discoverable
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

        # test for public resource
        self.assertTrue(self.res.raccess.discoverable)
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = False
        self.res.raccess.public = True
        self.res.raccess.save()

        parameters = [
                      # anonymous user has authorization for resource view (metadata and content files) for a
                      # resource that is public
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},
                      # anonymous user has authorization for metadata view for a resource that is pu
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

        parameters = [
                      # anonymous user has authorization for resource view (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

        # test for immutable/published resource
        self.assertFalse(self.res.raccess.immutable)
        self.assertFalse(self.res.raccess.published)
        self.assertTrue(self.res.raccess.public)

        self.res.raccess.immutable = True
        self.res.raccess.published = True
        self.res.raccess.save()

        parameters = [
                      # anonymous user has authorization for resource view (metadata and content files)
                      # but public
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

    def test_authorize_user(self):
        # create user - has no assigned resource access privilege
        authenticated_user = users.create_account(
            'user@email.com',
            username='user',
            first_name='user_first_name',
            last_name='user_last_name',
            superuser=False,
            groups=[])

        self.request.user = authenticated_user

        common_parameters = [
                      # parameter 'discoverable' has no effect on authorization

                      # authenticated user has no authorization for resource edit (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},

                      # authenticated user has no authorization for resource delete or setting resource flags
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied}
                      ]

        # test for private resource
        self.assertFalse(self.res.raccess.public)
        self.assertFalse(self.res.raccess.discoverable)

        parameters = [
                      # authenticated user has no authorization for resource view
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

        # test for discoverable resource
        self.res.raccess.discoverable = True
        self.res.raccess.public = False
        self.res.raccess.save()

        parameters = [
                      # authenticated user has no authorization for resource view (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': False, 'exception': PermissionDenied},
                      # authenticated user has authorization for resource metadata only view
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

        # test for public resource
        self.assertTrue(self.res.raccess.discoverable)
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = False
        self.res.raccess.public = True
        self.res.raccess.save()

        parameters = [
                      # authenticated user has authorization for resource view (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},
                      # authenticated user has authorization for resource metadata only view
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

        # test for immutable/published resource
        self.assertFalse(self.res.raccess.immutable)
        self.assertFalse(self.res.raccess.published)
        self.assertTrue(self.res.raccess.public)
        self.res.raccess.immutable = True
        self.res.raccess.published = True
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

    def test_authorize_inactive_user(self):
        self.user.is_active = False
        self.user.save()
        self.request.user = self.user

        common_parameters = [
                      # setting of parameter 'discoverable' has no effect for owner authorization

                      # resource inactive owner has no authorization for resource edit (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': PermissionDenied},

                      # resource inactive owner has no authorization for resource delete or setting resource flags
                      # (public, published/immutable, shareable etc)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': PermissionDenied}
                      ]

        # test for private resource
        self.assertFalse(self.res.raccess.public)
        self.assertFalse(self.res.raccess.discoverable)

        parameters = [
                      # setting of parameter 'discoverable' has no effect for owner authorization

                      # resource inactive owner has no authorization for resource view (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': False, 'exception': PermissionDenied},
                      # resource inactive owner has no authorization for resource metadata view
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': False, 'exception': PermissionDenied}

                      ] + common_parameters

        self._run_tests(self.request, parameters)

        # test for discoverable resource
        self.assertFalse(self.res.raccess.discoverable)
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = True
        self.res.raccess.save()

        parameters = [
                      # resource inactive owner has no authorization for resource view (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': False, 'exception': PermissionDenied},
                      # resource inactive owner has authorization for resource metadata view
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None}

                      ] + common_parameters

        self._run_tests(self.request, parameters)

        # test for public resource
        self.assertTrue(self.res.raccess.discoverable)
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = False
        self.res.raccess.public = True
        self.res.raccess.save()

        parameters = [
                      # setting of parameter 'discoverable' has no effect for owner authorization

                      # resource inactive owner has authorization for resource view (metadata and content files)
                      {'res_id': self.res.short_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None},
                      # resource inactive owner has authorization for resource metadata view
                      {'res_id': self.res.short_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': True, 'exception': None}

                      ] + common_parameters

        self._run_tests(self.request, parameters)

        # test for immutable/published resource
        self.assertFalse(self.res.raccess.immutable)
        self.assertFalse(self.res.raccess.published)
        self.assertTrue(self.res.raccess.public)

        self.res.raccess.published = True
        self.res.raccess.immutable = True
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

    def test_exception_notfound(self):
        invalid_res_id = '123x'
        parameters = [
                      {'res_id': invalid_res_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': False, 'exception': NotFound},
                      {'res_id': invalid_res_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.VIEW,
                       'success': False, 'exception': NotFound},
                      {'res_id': invalid_res_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': NotFound},
                      {'res_id': invalid_res_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.CHANGE,
                       'success': False, 'exception': NotFound},
                      {'res_id': invalid_res_id, 'discoverable': False, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': NotFound},
                      {'res_id': invalid_res_id, 'discoverable': True, 'needed_permission':PrivilegeCodes.OWNER,
                       'success': False, 'exception': NotFound}
                      ]

        self.request.user = self.user
        self._run_tests(self.request, parameters)

    def test_default_parameters(self):
        # default permission is view

        # >> test private resource
        self.assertFalse(self.res.raccess.public)

        # test owner
        self.request.user = self.user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test super user
        super_user = users.create_account(
            'super_user@email.com',
            username='superuser',
            first_name='super_first_name',
            last_name='super_last_name',
            superuser=True,
            groups=[])

        self.request.user = super_user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test edit user
        edit_user = users.create_account(
                'edit_user@email.com',
                username='edituser',
                first_name='edit_first_name',
                last_name='edit_last_name',
                superuser=False,
                groups=[])

        self.request.user = edit_user
        # grant edit_user edit permission
        self.user.uaccess.share_resource_with_user(self.res, edit_user, PrivilegeCodes.CHANGE)
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test view user
        view_user = users.create_account(
            'view_user@email.com',
            username='viewuser',
            first_name='view_first_name',
            last_name='view_last_name',
            superuser=False,
            groups=[])

        self.request.user = view_user
        # grant view_user view permission
        self.user.uaccess.share_resource_with_user(self.res, view_user, PrivilegeCodes.VIEW)
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test authenticated user with no granted permission
        authenticated_user = users.create_account(
            'user@email.com',
            username='user',
            first_name='user_first_name',
            last_name='user_last_name',
            superuser=False,
            groups=[])

        self.request.user = authenticated_user

        with self.assertRaises(PermissionDenied):
            authorize(self.request, res_id=self.res.short_id)

        # test anonymous user
        self.request.user = AnonymousUser()

        with self.assertRaises(PermissionDenied):
            authorize(self.request, res_id=self.res.short_id)

        # >> test for discoverable resource
        self.assertFalse(self.res.raccess.discoverable)
        self.res.raccess.discoverable = True
        self.res.raccess.public = False
        self.res.raccess.save()

        # test owner
        self.request.user = self.user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test super user
        self.request.user = super_user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test edit user
        self.request.user = edit_user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test view user
        self.request.user = view_user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test authenticated user
        self.request.user = authenticated_user
        with self.assertRaises(PermissionDenied):
            authorize(self.request, res_id=self.res.short_id)

        # test anonymous user
        self.request.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            authorize(self.request, res_id=self.res.short_id)

        # >> test for public resource
        self.assertFalse(self.res.raccess.public)
        self.res.raccess.discoverable = False
        self.res.raccess.public = True
        self.res.raccess.save()

        # test owner
        self.request.user = self.user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test super user
        self.request.user = super_user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test edit user
        self.request.user = edit_user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test view user
        self.request.user = view_user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test authenticated user
        self.request.user = authenticated_user
        #with self.assertRaises(PermissionDenied):
        authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test anonymous user
        self.request.user = AnonymousUser()
        #with self.assertRaises(PermissionDenied):
        authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # >> test for published resource
        self.assertFalse(self.res.raccess.published)
        self.res.raccess.published = False
        self.res.raccess.immutable = True
        self.res.raccess.save()

        # test owner
        self.request.user = self.user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test super user
        self.request.user = super_user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test edit user
        self.request.user = edit_user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test view user
        self.request.user = view_user
        _, authorized, _ = authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test authenticated user
        self.request.user = authenticated_user
        #with self.assertRaises(PermissionDenied):
        authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

        # test anonymous user
        self.request.user = AnonymousUser()
        #with self.assertRaises(PermissionDenied):
        authorize(self.request, res_id=self.res.short_id)
        self.assertTrue(authorized)

    def test_raise_no_exception(self):
        # create user - has no assigned resource access privilege
        authenticated_user = users.create_account(
            'user@email.com',
            username='user',
            first_name='user_first_name',
            last_name='user_last_name',
            superuser=False,
            groups=[])

        self.request.user = authenticated_user

        res, authorized, user = authorize(self.request, res_id=self.res.short_id, discoverable=True,
                                          needed_permission=PrivilegeCodes.VIEW, raises_exception=False)
        self.assertEquals(authorized, False)
        self.assertEquals(res, self.res)
        self.assertEquals(user, authenticated_user)

    def test_return_data(self):
        # test authorization True
        self.request.user = self.user
        res, authorized, user = authorize(self.request, res_id=self.res.short_id, needed_permission=PrivilegeCodes.VIEW)
        self.assertEquals(authorized, True)
        self.assertEquals(res, self.res)
        self.assertEquals(user, self.user)

        # test authorization False
        anonymous_user = AnonymousUser()
        self.request.user = anonymous_user
        res, authorized, user = authorize(self.request, res_id=self.res.short_id, needed_permission=PrivilegeCodes.VIEW,
                                          raises_exception=False)
        self.assertEquals(authorized, False)
        self.assertEquals(res, self.res)
        self.assertEquals(user, anonymous_user)

    def _run_tests(self, request, parameters):
        for params in parameters:
            if params['exception'] is None:
                res, authorized, user = authorize(request, res_id=params['res_id'], discoverable=params['discoverable'],
                                                  needed_permission=params['needed_permission'])
                self.assertEquals(params['success'], authorized)
            else:
                with self.assertRaises(params['exception']):
                    authorize(request, res_id=params['res_id'], discoverable=params['discoverable'],
                              needed_permission=params['needed_permission'])