"""Ajax API view permission tests for the projectroles app"""

from django.test import override_settings
from django.urls import reverse

from projectroles.models import SODAR_CONSTANTS
from projectroles.tests.test_permissions import TestProjectPermissionBase


# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']


class TestProjectViews(TestProjectPermissionBase):
    """Permission tests for Project Ajax views"""

    def test_starring_ajax(self):
        """Test permissions for project starring Ajax view"""
        url = reverse(
            'projectroles:ajax_star',
            kwargs={'project': self.project.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.anonymous, self.user_no_roles]
        self.assert_response(url, good_users, 200, method='POST')
        self.assert_response(url, bad_users, 403, method='POST')

    def test_starring_ajax_category(self):
        """Test permissions for project starring Ajax view under category"""
        url = reverse(
            'projectroles:ajax_star',
            kwargs={'project': self.category.sodar_uuid},
        )
        good_users = [
            self.superuser,
            self.owner_as.user,
            self.delegate_as.user,
            self.contributor_as.user,
            self.guest_as.user,
        ]
        bad_users = [self.anonymous, self.user_no_roles]
        self.assert_response(url, good_users, 200, method='POST')
        self.assert_response(url, bad_users, 403, method='POST')

    @override_settings(PROJECTROLES_ALLOW_LOCAL_USERS=True)
    def test_user_autocomplete_ajax(self):
        """Test UserAutocompleteAjaxView access"""
        url = reverse('projectroles:ajax_autocomplete_user')
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
        self.assert_response(url, bad_users, 403)
