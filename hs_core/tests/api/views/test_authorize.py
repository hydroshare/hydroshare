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
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': True, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': False,
                       'superuser': True, 'success': False, 'exception': PermissionDenied}
                      ]

        parameters = [{'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':False, 'full': False,
                       'superuser': False, 'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': True,
                       'superuser': False, 'success': True, 'exception': None}
                      ] + common_parameters

        self.request.user = self.user
        self._run_tests(self.request, parameters)

        # test for immutable/published resource
        self.assertFalse(self.res.raccess.immutable)
        self.res.raccess.immutable = True
        self.res.raccess.public = True
        self.res.raccess.published = True
        self.res.raccess.save()

        parameters = [{'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': True,
                       'superuser': False, 'success': False, 'exception': PermissionDenied}
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
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': True,
                       'superuser': False, 'success': False, 'exception': PermissionDenied },
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': True, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': False,
                       'superuser': True, 'success': False, 'exception': PermissionDenied}
                      ]

        parameters = [{'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':False, 'full': False,
                       'superuser': False, 'success': True, 'exception': None }
                      ] + common_parameters

        # grant edit_user edit permission
        self.user.uaccess.share_resource_with_user(self.res, edit_user, PrivilegeCodes.CHANGE)

        self._run_tests(self.request, parameters)

        # test for immutable/published resource
        self.assertFalse(self.res.raccess.immutable)
        self.res.raccess.immutable = True
        self.res.raccess.public = True
        self.res.raccess.published = True
        self.res.raccess.save()

        parameters = [{'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied }
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
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': True,
                       'superuser': False, 'success': False, 'exception': PermissionDenied },
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': True, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': False,
                       'superuser': True, 'success': False, 'exception': PermissionDenied}
                      ]

        # grant view_user view permission
        self.user.uaccess.share_resource_with_user(self.res, view_user, PrivilegeCodes.VIEW)

        self._run_tests(self.request, parameters)

    def test_authorize_superuser(self):
        # create super user
        super_user = users.create_account(
            'view_user@email.com',
            username='viewuser',
            first_name='view_first_name',
            last_name='view_last_name',
            superuser=True,
            groups=[])

        self.request.user = super_user

        common_parameters = [
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':False, 'full': False,
                       'superuser': False, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': False,
                       'superuser': True, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': True, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied },
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      ]

        parameters = [{'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': True,
                       'superuser': False, 'success': True, 'exception': None }
                      ] + common_parameters

        self._run_tests(self.request, parameters)

        # test for immutable/published resource
        self.assertFalse(self.res.raccess.immutable)
        self.res.raccess.immutable = True
        self.res.raccess.public = True
        self.res.raccess.published = True
        self.res.raccess.save()

        parameters = [{'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': True,
                       'superuser': False, 'success': False, 'exception': PermissionDenied }
                      ] + common_parameters

        self._run_tests(self.request, parameters)

    def test_authorize_anonymous_user(self):
        self.request.user = AnonymousUser()
        common_parameters = [
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': True,
                       'superuser': False, 'success': False, 'exception': PermissionDenied },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied }
                      ]
        parameters = [{'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': False, 'exception': PermissionDenied }
                      ] + common_parameters

        self.res.raccess.discoverable = True
        self.res.raccess.public = False
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

        parameters = [{'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': False, 'exception': PermissionDenied },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': False, 'exception': PermissionDenied }
                      ] + common_parameters

        self.res.raccess.discoverable = False
        self.res.raccess.public = False
        self.res.raccess.save()
        self._run_tests(self.request, parameters)

        parameters = [{'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': True, 'exception': None },
                       {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': True, 'exception': None },
                      ] + common_parameters

        self.res.raccess.discoverable = False
        self.res.raccess.public = True
        self.res.raccess.save()
        self._run_tests(self.request, parameters)

        parameters = [{'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': True, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': True, 'exception': None }
                      ] + common_parameters

        self.res.raccess.discoverable = True
        self.res.raccess.public = True
        self.res.raccess.save()
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
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': True,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied}
                      ]
        parameters = [{'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': False, 'exception': PermissionDenied}
                      ] + common_parameters

        self.res.raccess.discoverable = True
        self.res.raccess.public = False
        self.res.raccess.save()

        self._run_tests(self.request, parameters)

        self.res.raccess.discoverable = False
        self.res.raccess.public = True
        self.res.raccess.save()

        parameters = [{'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': True, 'exception': None}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

        self.res.raccess.discoverable = True
        self.res.raccess.public = True
        self.res.raccess.save()

        parameters = [{'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': True, 'exception': None },
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': True, 'exception': None},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': True, 'exception': None}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

        self.res.raccess.discoverable = False
        self.res.raccess.public = False
        self.res.raccess.save()

        parameters = [{'res_id': self.res.short_id, 'discoverable': True, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':False, 'full': False,
                       'superuser': False, 'success': False, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': False, 'view':True, 'full': False,
                       'superuser': False, 'success': True, 'exception': PermissionDenied},
                      {'res_id': self.res.short_id, 'discoverable': False, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': False, 'exception': PermissionDenied}
                      ] + common_parameters

        self._run_tests(self.request, parameters)

    def test_exception_notfound(self):
        invalid_res_id = '123x'
        parameters = [{'res_id': invalid_res_id, 'discoverable': True, 'edit': True, 'view':True, 'full': True,
                       'superuser': True, 'success': False, 'exception': NotFound}
                      ]

        self.request.user = self.user
        self._run_tests(self.request, parameters)

    def test_default_parameters(self):
        self.request.user = self.user
        with self.assertRaises(PermissionDenied):
            authorize(self.request, res_id=self.res.short_id)

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
                                          edit=True, view=True, full=True,
                                          superuser=True, raises_exception=False)
        self.assertEquals(authorized, False)
        self.assertEquals(res, self.res)
        self.assertEquals(user, authenticated_user)

    def test_return_data(self):
        self.request.user = self.user
        res, authorized, user = authorize(self.request, res_id=self.res.short_id, discoverable=True,
                                          edit=True, view=True, full=True, superuser=True)
        self.assertEquals(authorized, True)
        self.assertEquals(res, self.res)
        self.assertEquals(user, self.user)

    def _run_tests(self, request, parameters):
        for params in parameters:
            if params['exception'] is None:
                res, authorized, user = authorize(request, res_id=params['res_id'], discoverable=params['discoverable'],
                                                  edit=params['edit'], view=params['view'], full=params['full'],
                                                  superuser=params['superuser'])
                self.assertEquals(params['success'], authorized)
            else:
                with self.assertRaises(params['exception']):
                    authorize(request, res_id=params['res_id'], discoverable=params['discoverable'],
                              edit=params['edit'], view=params['view'],
                              full=params['full'], superuser=params['superuser'])