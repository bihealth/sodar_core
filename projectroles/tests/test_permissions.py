"""UI view permission tests for the projectroles app"""

from urllib.parse import urlencode

from django.test import override_settings
from django.urls import reverse

from test_plus.test import TestCase

from projectroles.models import Role, SODAR_CONSTANTS
from projectroles.utils import build_secret
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
    RemoteSiteMixin,
    RemoteProjectMixin,
)


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SITE_MODE_SOURCE = SODAR_CONSTANTS['SITE_MODE_SOURCE']
SITE_MODE_TARGET = SODAR_CONSTANTS['SITE_MODE_TARGET']

# Local constants
REMOTE_SITE_NAME = 'Test site'
REMOTE_SITE_URL = 'https://sodar.bihealth.org'
REMOTE_SITE_SECRET = build_secret()


class TestPermissionMixin:
    """Helper class for permission tests"""

    def assert_response(
        self,
        url,
        users,
        status_code,
        redirect_user=None,
        redirect_anon=None,
        method='GET',
        data=None,
    ):
        """
        Assert a response status code for url with a list of users. Also checks
        for redirection URL where applicable.

        :param url: Target URL for the request
        :param users: Users to test (single user, list or tuple)
        :param status_code: Status code
        :param redirect_user: Redirect URL for signed in user (None=default)
        :param redirect_anon: Redirect URL for anonymous (None=default)
        :param method: Method for request (default='GET')
        :param data: Optional data for request (dict)
        """

        def _send_request():
            req_method = getattr(self.client, method.lower(), None)

            if not req_method:
                raise ValueError('Invalid method "{}"'.format(method))

            return req_method(url, **req_kwargs)

        if not isinstance(users, (list, tuple)):
            users = [users]

        for user in users:
            req_kwargs = {'data': data} if data else {}

            if user:  # Authenticated user
                redirect_url = (
                    redirect_user if redirect_user else reverse('home')
                )

                with self.login(user):
                    response = _send_request()

            else:  # Anonymous
                redirect_url = (
                    redirect_anon
                    if redirect_anon
                    else reverse('login') + '?next=' + url
                )
                response = _send_request()

            msg = 'user={}'.format(user)
            self.assertEqual(response.status_code, status_code, msg=msg)

            if status_code == 302:
                self.assertEqual(response.url, redirect_url, msg=msg)


class TestPermissionBase(TestPermissionMixin, TestCase):
    """
    Base class for permission tests for UI views.

    NOTE: To use with DRF API views, you need to use APITestCase
    """

    pass


class TestProjectPermissionBase(
    ProjectMixin, RoleAssignmentMixin, ProjectInviteMixin, TestPermissionBase
):
    """
    Base class for testing project permissions.

    NOTE: To use with DRF API views, you need to use APITestCase
    """

    def setUp(self):
        # Init roles
        self.role_owner = Role.objects.get_or_create(name=PROJECT_ROLE_OWNER)[0]
        self.role_delegate = Role.objects.get_or_create(
            name=PROJECT_ROLE_DELEGATE
        )[0]
        self.role_contributor = Role.objects.get_or_create(
            name=PROJECT_ROLE_CONTRIBUTOR
        )[0]
        self.role_guest = Role.objects.get_or_create(name=PROJECT_ROLE_GUEST)[0]

        # Init users

        # Superuser
        self.superuser = self.make_user('superuser')
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()

        # No user
        self.anonymous = None

        # Users with role assignments
        self.user_owner_cat = self.make_user('user_owner_cat')
        self.user_owner = self.make_user('user_owner')
        self.user_delegate = self.make_user('user_delegate')
        self.user_contributor = self.make_user('user_contributor')
        self.user_guest = self.make_user('user_guest')

        # User without role assignments
        self.user_no_roles = self.make_user('user_no_roles')

        # Init projects

        # Top level category
        self.category = self._make_project(
            title='TestCategoryTop', type=PROJECT_TYPE_CATEGORY, parent=None
        )

        # Subproject under category
        self.project = self._make_project(
            title='TestProjectSub',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category,
        )

        # Init role assignments
        self.owner_as_cat = self._make_assignment(
            self.category, self.user_owner_cat, self.role_owner
        )
        self.owner_as = self._make_assignment(
            self.project, self.user_owner, self.role_owner
        )
        self.delegate_as = self._make_assignment(
            self.project, self.user_delegate, self.role_delegate
        )
        self.contributor_as = self._make_assignment(
            self.project, self.user_contributor, self.role_contributor
        )
        self.guest_as = self._make_assignment(
            self.project, self.user_guest, self.role_guest
        )


class TestBaseViews(TestProjectPermissionBase):
    """Tests for base UI views"""

    def test_home(self):
        """Test permissions for the home view"""
        url = reverse('home')
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_project_search(self):
        """Test permissions for the search view"""
        url = reverse('projectroles:search') + '?' + urlencode({'s': 'test'})
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        bad_users = [self.anonymous]
        self.assert_response(url, good_users, 200)
        self.assert_response(reverse('home'), bad_users, 302)

    def test_login(self):
        """Test permissions for the login view"""
        url = reverse('login')
        good_users = [
            self.anonymous,
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)

    def test_logout(self):
        """Test permissions for the logout view"""
        url = reverse('logout')
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(
            url,
            good_users,
            302,
            redirect_user='/login/',
            redirect_anon='/login/',
        )

    def test_about(self):
        """Test permissions for the about view"""
        url = reverse('about')
        good_users = [
            self.anonymous,
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)

    def test_admin(self):
        """Test permissions for the admin view"""
        url = '/admin/'
        good_users = [self.superuser]
        bad_users = [
            self.anonymous,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(
            url,
            bad_users,
            302,
            redirect_user='/admin/login/?next=/admin/',
            redirect_anon='/admin/login/?next=/admin/',
        )


class TestProjectViews(TestProjectPermissionBase):
    """Permission tests for Project UI views"""

    # TODO: Add category owner
    def test_category_details(self):
        """Test permissions for category details"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.category.sodar_uuid}
        )

        # Add user with access to project below category: should still be able
        # to view the category
        new_user = self.make_user('new_user')
        self._make_assignment(self.project, new_user, self.role_contributor)

        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            new_user,
        ]
        bad_users = [self.anonymous, self.user_no_roles]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    # TODO: Test inherited owner from category
    def test_project_details(self):
        """Test permissions for project details"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,  # Inherited
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.anonymous, self.user_no_roles]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_update(self):
        """Test permissions for project updating"""
        url = reverse(
            'projectroles:update', kwargs={'project': self.project.sodar_uuid}
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_update_category(self):
        """Test permissions for category updating"""
        url = reverse(
            'projectroles:update', kwargs={'project': self.category.sodar_uuid}
        )
        good_users = [self.superuser, self.owner_as_cat.user]
        bad_users = [
            self.anonymous,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_create_top(self):
        """Test permissions for top level project creation"""
        url = reverse('projectroles:create')
        good_users = [self.superuser]
        bad_users = [
            self.anonymous,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_create_sub(self):
        """Test permissions for subproject creation"""
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        good_users = [self.superuser, self.owner_as_cat.user]
        bad_users = [
            self.anonymous,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_roles(self):
        """Test permissions for role list"""
        url = reverse(
            'projectroles:roles', kwargs={'project': self.project.sodar_uuid}
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.anonymous, self.user_no_roles]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_roles_category(self):
        """Test permissions for role list under category"""

        # Set up category roles
        self._make_assignment(
            self.category, self.delegate_as.user, self.role_delegate
        )
        self._make_assignment(
            self.category, self.contributor_as.user, self.role_contributor
        )
        self._make_assignment(
            self.category, self.guest_as.user, self.role_guest
        )

        url = reverse(
            'projectroles:roles', kwargs={'project': self.category.sodar_uuid}
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.anonymous, self.owner_as.user, self.user_no_roles]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_create(self):
        """Test permissions for role creation"""
        url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_create_category(self):
        """Test permissions for role creation under category"""

        # Set up category roles
        self._make_assignment(
            self.category, self.delegate_as.user, self.role_delegate
        )
        self._make_assignment(
            self.category, self.contributor_as.user, self.role_contributor
        )
        self._make_assignment(
            self.category, self.guest_as.user, self.role_guest
        )

        url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.category.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.owner_as.user,  # Not the owner here
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_update(self):
        """Test permissions for role updating"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_delete(self):
        """Test permissions for role deletion"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_update_owner(self):
        """Test permissions for owner role update (should fail)"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        bad_users = [
            self.anonymous,
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_role_delete_owner(self):
        """Test permissions for owner role deletion: (should fail)"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.owner_as.sodar_uuid},
        )
        bad_users = [
            self.anonymous,
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_role_update_delegate(self):
        """Test permissions for delegate role update"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.delegate_as.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_delete_delegate(self):
        """Test permissions for role deletion for delegate"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.delegate_as.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_transfer_owner(self):
        """Test permissions for owner role update: not allowed, should fail"""
        url = reverse(
            'projectroles:role_transfer_owner',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_invite_create(self):
        """Test permissions for role invite creation"""
        url = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_invite_create_category(self):
        """Test permissions for role invite creation under category"""

        # Set up category roles
        self._make_assignment(
            self.category, self.delegate_as.user, self.role_delegate
        )
        self._make_assignment(
            self.category, self.contributor_as.user, self.role_contributor
        )
        self._make_assignment(
            self.category, self.guest_as.user, self.role_guest
        )

        url = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.category.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.owner_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_invite_list(self):
        """Test permissions for role invite list"""
        url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_invite_list_category(self):
        """Test permissions for role invite list under category"""

        # Set up category roles
        self._make_assignment(
            self.category, self.delegate_as.user, self.role_delegate
        )
        self._make_assignment(
            self.category, self.contributor_as.user, self.role_contributor
        )
        self._make_assignment(
            self.category, self.guest_as.user, self.role_guest
        )

        url = reverse(
            'projectroles:invites', kwargs={'project': self.category.sodar_uuid}
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.owner_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_invite_resend(self):
        """Test permissions for role invite resending"""

        # Init invite
        invite = self._make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
            message='',
        )

        url = reverse(
            'projectroles:invite_resend',
            kwargs={'projectinvite': invite.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(
            url,
            good_users,
            302,
            redirect_user=reverse(
                'projectroles:invites',
                kwargs={'project': self.project.sodar_uuid},
            ),
        )
        self.assert_response(url, bad_users, 302)

    def test_role_invite_revoke(self):
        """Test permissions for role invite revoking"""

        # Init invite
        invite = self._make_invite(
            email='test@example.com',
            project=self.project,
            role=self.role_contributor,
            issuer=self.user_owner,
            message='',
        )

        url = reverse(
            'projectroles:invite_revoke',
            kwargs={'projectinvite': invite.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
        ]
        bad_users = [
            self.anonymous,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestTargetProjectViews(
    RemoteSiteMixin, RemoteProjectMixin, TestProjectPermissionBase
):
    """Tests for Project updating views on a TARGET site"""

    def setUp(self):
        super().setUp()

        # Create site
        self.site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )

        # Create RemoteProject objects
        self.remote_category = self._make_remote_project(
            project_uuid=self.category.sodar_uuid,
            project=self.category,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )
        self.remote_project = self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES'],
        )

    def test_update(self):
        """Test permissions for project updating as target"""
        url = reverse(
            'projectroles:update', kwargs={'project': self.project.sodar_uuid}
        )
        bad_users = [
            self.anonymous,
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_create_top_allowed(self):
        """Test permissions for top level project creation as target"""
        url = reverse('projectroles:create')
        good_users = [self.superuser]
        bad_users = [
            self.anonymous,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    # TODO: Add separate tests for local/remote creation
    # TODO: Remote creation should fail
    def test_create_sub_local(self):
        """Test permissions for subproject creation as target under a local category"""

        # Make category local
        self.remote_category.delete()

        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        good_users = [self.superuser, self.owner_as_cat.user]
        bad_users = [
            self.anonymous,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_create_sub_remote(self):
        """Test permissions for subproject creation as target under a local category"""
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        bad_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.anonymous,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    @override_settings(PROJECTROLES_TARGET_CREATE=False)
    def test_create_sub_disallowed(self):
        """Test permissions for subproject creation with creation disallowed as target"""
        url = reverse(
            'projectroles:create', kwargs={'project': self.category.sodar_uuid}
        )
        bad_users = [
            self.anonymous,
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_role_create(self):
        """Test permissions for role creation as target"""
        url = reverse(
            'projectroles:role_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        bad_users = [
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.anonymous,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_role_update(self):
        """Test permissions for role updating as target"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        bad_users = [
            self.anonymous,
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_role_delete(self):
        """Test permissions for role deletion as target"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.contributor_as.sodar_uuid},
        )
        bad_users = [
            self.anonymous,
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_role_update_delegate(self):
        """Test permissions for delegate role update as target"""
        url = reverse(
            'projectroles:role_update',
            kwargs={'roleassignment': self.delegate_as.sodar_uuid},
        )
        bad_users = [
            self.anonymous,
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_role_delete_delegate(self):
        """Test permissions for role deletion for delegate as target"""
        url = reverse(
            'projectroles:role_delete',
            kwargs={'roleassignment': self.delegate_as.sodar_uuid},
        )
        bad_users = [
            self.anonymous,
            self.superuser,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_role_invite_create(self):
        """Test permissions for role invite creation as target"""
        url = reverse(
            'projectroles:invite_create',
            kwargs={'project': self.project.sodar_uuid},
        )
        bad_users = [
            self.superuser,
            self.anonymous,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)

    def test_role_invite_list(self):
        """Test permissions for role invite list as target"""
        url = reverse(
            'projectroles:invites', kwargs={'project': self.project.sodar_uuid}
        )
        bad_users = [
            self.superuser,
            self.anonymous,
            self.owner_as_cat.user,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, bad_users, 302)


@override_settings(PROJECTROLES_SITE_MODE=SITE_MODE_TARGET)
class TestRevokedRemoteProject(
    RemoteSiteMixin, RemoteProjectMixin, TestProjectPermissionBase
):
    """Tests for views for a revoked project on a TARGET site"""

    def setUp(self):
        super().setUp()

        # Create site
        self.site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_SOURCE'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )

        # Create RemoteProject objects
        self.remote_category = self._make_remote_project(
            project_uuid=self.category.sodar_uuid,
            project=self.category,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_READ_INFO'],
        )
        self.remote_project = self._make_remote_project(
            project_uuid=self.project.sodar_uuid,
            project=self.project,
            site=self.site,
            level=SODAR_CONSTANTS['REMOTE_LEVEL_REVOKED'],
        )

    def test_project_details(self):
        """Test permissions for REVOKED project detail page as target"""
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )
        good_users = [self.superuser, self.owner_as.user, self.delegate_as.user]
        bad_users = [
            self.anonymous,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_role_list(self):
        """Test permissions for REVOKED project's role list as target"""
        url = reverse(
            'projectroles:roles', kwargs={'project': self.project.sodar_uuid}
        )
        good_users = [self.superuser, self.owner_as.user, self.delegate_as.user]
        bad_users = [
            self.anonymous,
            self.contributor_as.user,
            self.guest_as.user,
            self.user_no_roles,
        ]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)


class TestRemoteSiteApp(RemoteSiteMixin, TestPermissionBase):
    """Tests for remote site management views"""

    def setUp(self):
        # Create users
        self.superuser = self.make_user('superuser')
        self.superuser.is_superuser = True
        self.superuser.is_staff = True
        self.superuser.save()

        self.regular_user = self.make_user('regular_user')

        # No user
        self.anonymous = None

        # Create site
        self.site = self._make_site(
            name=REMOTE_SITE_NAME,
            url=REMOTE_SITE_URL,
            mode=SODAR_CONSTANTS['SITE_MODE_TARGET'],
            description='',
            secret=REMOTE_SITE_SECRET,
        )

    def test_site_list(self):
        """Test remote site list view permissions"""
        url = reverse('projectroles:remote_sites')
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_site_create(self):
        """Test remote site create view permissions"""
        url = reverse('projectroles:remote_site_create')
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_site_update(self):
        """Test remote site update view permissions"""
        url = reverse(
            'projectroles:remote_site_update',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_site_delete(self):
        """Test remote site delete view permissions"""
        url = reverse(
            'projectroles:remote_site_delete',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_project_list(self):
        """Test remote project list view permissions"""
        url = reverse(
            'projectroles:remote_projects',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)

    def test_project_update(self):
        """Test remote project update view permissions"""
        url = reverse(
            'projectroles:remote_projects_update',
            kwargs={'remotesite': self.site.sodar_uuid},
        )
        good_users = [self.superuser]
        bad_users = [self.anonymous, self.regular_user]
        self.assert_response(url, good_users, 200)
        self.assert_response(url, bad_users, 302)
