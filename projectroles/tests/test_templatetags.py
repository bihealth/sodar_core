"""Tests for template tags in the projectroles app"""

from importlib import import_module
import mistune
import uuid

from django.conf import settings
from django.test import override_settings, RequestFactory
from django.urls import reverse

from test_plus.test import TestCase

import projectroles
from projectroles.models import (
    Role,
    SODAR_CONSTANTS,
    PROJECT_TAG_STARRED,
    Project,
    RemoteProject,
    RemoteSite,
)
from projectroles.plugins import get_app_plugin, get_active_plugins
from projectroles.project_tags import set_tag_state
from projectroles.templatetags import (
    projectroles_common_tags as c_tags,
    projectroles_tags as tags,
)
from projectroles.tests.test_models import (
    ProjectMixin,
    RoleAssignmentMixin,
    ProjectInviteMixin,
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
SITE_MODE_PEER = SODAR_CONSTANTS['SITE_MODE_PEER']
REMOTE_LEVEL_READ_ROLES = SODAR_CONSTANTS['REMOTE_LEVEL_READ_ROLES']


# Local constants
NON_EXISTING_UUID = uuid.uuid4()
STATIC_FILE_PATH = 'images/logo_navbar.png'
TEMPLATE_PATH = 'projectroles/home.html'


site = import_module(settings.SITE_PACKAGE)


class TestTemplateTagsBase(
    ProjectMixin, RoleAssignmentMixin, ProjectInviteMixin, TestCase
):
    """Base class for testing project permissions"""

    def setUp(self):
        # Init roles
        self.role_owner = Role.objects.get_or_create(name=PROJECT_ROLE_OWNER)[0]

        # Init users
        self.user = self.make_user('user_owner')

        # Init category
        self.category = self._make_project(
            title='TestCategoryTop', type=PROJECT_TYPE_CATEGORY, parent=None
        )

        # Init project under category
        self.project = self._make_project(
            title='TestProjectSub',
            type=PROJECT_TYPE_PROJECT,
            parent=self.category,
        )

        # Init role assignments
        self.owner_as_cat = self._make_assignment(
            self.category, self.user, self.role_owner
        )
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )


class TestCommonTemplateTags(TestTemplateTagsBase):
    """Test for template tags in projectroles_common_tags"""

    def test_site_version(self):
        """Test site_version()"""
        self.assertEqual(c_tags.site_version(), site.__version__)

    def test_core_version(self):
        """Test core_version()"""
        self.assertEqual(c_tags.core_version(), projectroles.__version__)

    def test_check_backend(self):
        """Test check_backend()"""
        self.assertEqual(c_tags.check_backend('timeline_backend'), True)
        self.assertEqual(c_tags.check_backend('example_backend_app'), True)
        self.assertEqual(c_tags.check_backend('sodar_cache'), True)
        self.assertEqual(c_tags.check_backend('NON_EXISTING_PLUGIN'), False)

    def test_get_projcet_by_uuid(self):
        """Test get_project_by_uuid()"""
        self.assertEqual(
            c_tags.get_project_by_uuid(self.project.sodar_uuid), self.project
        )
        self.assertEqual(c_tags.get_project_by_uuid(NON_EXISTING_UUID), None)

    def test_get_user_by_username(self):
        """Test get_user_by_username()"""
        self.assertEqual(
            c_tags.get_user_by_username(self.user.username), self.user
        )
        self.assertEqual(c_tags.get_user_by_username('NON_EXISTING_USER'), None)

    def test_get_django_setting(self):
        """Test get_django_setting()"""
        ret = c_tags.get_django_setting('PROJECTROLES_BROWSER_WARNING')
        self.assertEqual(ret, True)
        self.assertIsInstance(ret, bool)
        ret = c_tags.get_django_setting('PROJECTROLES_BROWSER_WARNING', js=True)
        self.assertEqual(ret, 1)
        self.assertIsInstance(ret, int)
        self.assertEqual(
            c_tags.get_django_setting('NON_EXISTING_SETTING'), None
        )
        self.assertEqual(
            c_tags.get_django_setting(
                'NON_EXISTING_SETTING', default='default'
            ),
            'default',
        )

    def test_get_app_setting(self):
        """Test get_app_setting()"""
        self.assertEqual(
            c_tags.get_app_setting(
                'example_project_app',
                'project_bool_setting',
                project=self.project,
            ),
            False,
        )
        self.assertEqual(
            c_tags.get_app_setting(
                'example_project_app', 'user_bool_setting', user=self.user
            ),
            False,
        )

    def test_static_file_exists(self):
        """Test static_file_exists()"""
        self.assertEqual(c_tags.static_file_exists(STATIC_FILE_PATH), True)
        self.assertEqual(
            c_tags.static_file_exists('NON_EXISTING_PATH/FILE.txt'), False
        )

    def test_template_exists(self):
        """Test template_exists()"""
        self.assertEqual(c_tags.template_exists(TEMPLATE_PATH), True)
        self.assertEqual(
            c_tags.template_exists('projectroles/NON_EXISTING_FILE.html'), False
        )

    def test_get_full_url(self):
        """Test get_full_url()"""
        req_factory = RequestFactory()
        url = reverse(
            'projectroles:detail', kwargs={'project': self.project.sodar_uuid}
        )

        with self.login(self.user):
            request = req_factory.get(url)
            self.assertEqual(
                c_tags.get_full_url(request, url),
                'http://testserver/project/{}'.format(self.project.sodar_uuid),
            )

    def test_get_display_name(self):
        """Test get_display_name()"""
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=False, count=1), 'project'
        )
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=True, count=1), 'Project'
        )
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=False, count=2), 'projects'
        )
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=True, count=2), 'Projects'
        )
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=False, plural=True),
            'projects',
        )
        self.assertEqual(
            c_tags.get_display_name('PROJECT', title=True, plural=True),
            'Projects',
        )

    def test_get_project_title_html(self):
        """Test get_project_title_html()"""
        self.assertEqual(
            c_tags.get_project_title_html(self.project),
            'TestCategoryTop / TestProjectSub',
        )

    def test_get_project_link(self):
        """Test get_project_link()"""
        self.assertEqual(
            c_tags.get_project_link(self.project, full_title=False),
            '<a href="/project/{}" title="{}" data-toggle="tooltip" '
            'data-placement="top">{}</a>'.format(
                self.project.sodar_uuid,
                self.project.description,
                self.project.title,
            ),
        )
        self.assertEqual(
            c_tags.get_project_link(self.project, full_title=True),
            '<a href="/project/{}" title="{}" data-toggle="tooltip" '
            'data-placement="top">{}</a>'.format(
                self.project.sodar_uuid,
                self.project.description,
                self.project.get_full_title(),
            ),
        )
        # TODO: Also test remote project link display (with icon)

    def test_get_user_html(self):
        """Test get_user_html()"""
        self.assertEqual(
            c_tags.get_user_html(self.user),
            '<a title="{}" href="mailto:{}" data-toggle="tooltip" '
            'data-placement="top">{}</a>'.format(
                self.user.get_full_name(), self.user.email, self.user.username
            ),
        )

    def test_get_history_dropdown(self):
        """Test get_history_dropdown()"""
        url = reverse(
            'timeline:list_object',
            kwargs={
                'project': self.project.sodar_uuid,
                'object_model': self.user.__class__.__name__,
                'object_uuid': self.user.sodar_uuid,
            },
        )
        self.assertEqual(
            c_tags.get_history_dropdown(self.project, self.user),
            '<a class="dropdown-item" href="{}">\n<i class="fa fa-fw '
            'fa-clock-o"></i> History</a>\n'.format(url),
        )

    def test_highlight_search_term(self):
        """Test highlight_search_term()"""
        item = 'Some Highlighted Text'
        term = 'highlight'
        self.assertEqual(
            c_tags.highlight_search_term(item, term),
            'Some <span class="sodar-search-highlight">Highlight</span>ed Text',
        )

    def test_get_info_link(self):
        """Test get_info_link()"""
        self.assertEqual(
            c_tags.get_info_link('content'),
            '<a class="sodar-info-link" tabindex="0" data-toggle="popover" '
            'data-trigger="focus" data-placement="top" data-content="content" '
            '><i class="fa fa-info-circle text-info"></i></a>',
        )
        self.assertEqual(
            c_tags.get_info_link('content', html=True),
            '<a class="sodar-info-link" tabindex="0" data-toggle="popover" '
            'data-trigger="focus" data-placement="top" data-content="content" '
            'data-html="true"><i class="fa fa-info-circle text-info"></i></a>',
        )

    # TODO: Test get_remote_icon() (need to set up remote projects)

    def test_get_visible_projects(self):
        """Test get_visible_projects()"""
        # Setup projects
        create_values = {'title': 'TestProject'}
        project = Project.objects.create(**create_values)

        # Setup sites
        create_values = {
            'name': 'VisibleSite',
            'url': 'visible.site',
            'mode': SITE_MODE_TARGET,
            'user_display': True,
        }
        visible_site = RemoteSite.objects.create(**create_values)

        create_values = {
            'name': 'InvisibleSite',
            'url': 'invisible.site',
            'mode': SITE_MODE_TARGET,
            'user_display': False,
        }
        invisible_site = RemoteSite.objects.create(**create_values)

        # Setup remote projects
        create_values = {
            'project_uuid': project.sodar_uuid,
            'project': project,
            'site': visible_site,
            'level': REMOTE_LEVEL_READ_ROLES,
        }
        visible_project = RemoteProject.objects.create(**create_values)

        create_values['site'] = invisible_site
        invisible_project = RemoteProject.objects.create(**create_values)

        # Test returned peer projects
        peer_projects = c_tags.get_visible_projects(
            [visible_project, invisible_project]
        )

        self.assertEqual(peer_projects, [visible_project])

    def test_render_markdown(self):
        """Test render_markdown()"""
        raw_md = '**Some markdown**'
        self.assertEqual(
            c_tags.render_markdown(raw_md), mistune.markdown(raw_md)
        )

    def test_force_wrap(self):
        """Test force_wrap()"""
        s = 'sometext'
        s_space = 'some text'
        s_hyphen = 'some-text'
        self.assertEqual(c_tags.force_wrap(s, 4), 'some<wbr />text')
        self.assertEqual(c_tags.force_wrap(s_space, 4), s_space)
        self.assertEqual(c_tags.force_wrap(s_hyphen, 4), s_hyphen)

    def test_get_class(self):
        """Test get_class()"""
        self.assertEqual(c_tags.get_class(self.project), 'Project')
        self.assertEqual(c_tags.get_class(self.project, lower=True), 'project')

    def test_include_invalid_plugin(self):
        """Test get_backend_include() plugin checks"""
        self.assertEqual(
            c_tags.get_backend_include('NON_EXISTING_PLUGIN', 'js'), ''
        )
        # Testing a plugin which is not backend
        self.assertEqual(c_tags.get_backend_include('filesfolders', 'js'), '')

    def test_include_none_value(self):
        """Test get_backend_include none attribute check"""
        # TODO: Replace with get_app_plugin once implemented for backend plugins
        backend_plugin = get_active_plugins('backend')[0]
        type(backend_plugin).javascript_url = None
        type(backend_plugin).css_url = None

        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'js'), ''
        )
        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'css'), ''
        )

    def test_include_invalid_url(self):
        """Test get_backend_include file existence check"""
        # TODO: Replace with get_app_plugin once implemented for backend plugins
        backend_plugin = get_active_plugins('backend')[0]

        type(
            backend_plugin
        ).javascript_url = 'example_backend_app/js/NOT_EXISTING_JS.js'
        type(
            backend_plugin
        ).css_url = 'example_backend_app/css/NOT_EXISTING_CSS.css'

        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'js'), ''
        )
        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'css'), ''
        )

    def test_get_backend_include(self):
        """Test get_backend_include"""
        # TODO: Replace with get_app_plugin once implemented for backend plugins
        backend_plugin = get_active_plugins('backend')[0]

        type(
            backend_plugin
        ).javascript_url = 'example_backend_app/js/greeting.js'
        type(backend_plugin).css_url = 'example_backend_app/css/greeting.css'

        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'js'),
            '<script type="text/javascript" '
            'src="/static/example_backend_app/js/greeting.js"></script>',
        )
        self.assertEqual(
            c_tags.get_backend_include(backend_plugin.name, 'css'),
            '<link rel="stylesheet" type="text/css" '
            'href="/static/example_backend_app/css/greeting.css"/>',
        )


class TestProjectrolesTemplateTags(TestTemplateTagsBase):
    """Test for template tags in projectroless_tags"""

    def test_sodar_constant(self):
        """Test sodar_constant()"""
        self.assertEqual(tags.sodar_constant('PROJECT_TYPE_PROJECT'), 'PROJECT')
        self.assertEqual(tags.sodar_constant('NON_EXISTING_CONSTANT'), None)

    def test_get_backend_plugins(self):
        """Test get_backend_plugins()"""
        self.assertEqual(
            len(tags.get_backend_plugins()),
            len(settings.ENABLED_BACKEND_PLUGINS),
        )

    def test_get_site_apps(self):
        """Test get_site_apps()"""
        self.assertEqual(len(tags.get_site_apps()), 7)

    # TODO: Test get_site_app_messages() (set up admin alert)

    def test_has_star(self):
        """Test has_star()"""
        # Test with no star
        self.assertEqual(tags.has_star(self.project, self.user), False)

        # Set star and test again
        set_tag_state(self.project, self.user, name=PROJECT_TAG_STARRED)
        self.assertEqual(tags.has_star(self.project, self.user), True)

    # TODO: Test get_remote_project_obj() (Set up remote projects)

    def test_allow_project_creation(self):
        """Test allow_project_creation()"""
        self.assertEqual(tags.allow_project_creation(), True)

    @override_settings(
        PROJECTROLES_SITE_MODE='TARGET', PROJECTROLES_TARGET_CREATE=False
    )
    def test_allow_project_creation_target(self):
        """Test allow_project_creation() in target mode"""
        self.assertEqual(tags.allow_project_creation(), False)

    def test_is_app_link_visible(self):
        """Test is_app_link_visible()"""
        app_plugin = get_app_plugin('filesfolders')
        self.assertEqual(
            tags.is_app_link_visible(app_plugin, self.project, self.user), True
        )

    def test_is_app_link_visible_category(self):
        """Test is_app_link_visible() with a category"""
        app_plugin = get_app_plugin('filesfolders')
        self.assertEqual(
            tags.is_app_link_visible(app_plugin, self.category, self.user),
            False,
        )

    def test_is_app_link_visible_category_enabled(self):
        """Test is_app_link_visible() with category_enable=True"""
        app_plugin = get_app_plugin('timeline')
        self.assertEqual(
            tags.is_app_link_visible(app_plugin, self.category, self.user), True
        )

    @override_settings(PROJECTROLES_HIDE_APP_LINKS=['filesfolders'])
    def test_is_app_link_visible_hide(self):
        """Test is_app_link_visible() with a hidden app and normal/superuser"""
        app_plugin = get_app_plugin('filesfolders')
        superuser = self.make_user('superuser')
        superuser.is_superuser = True
        superuser.save()
        self.assertEqual(
            tags.is_app_link_visible(app_plugin, self.project, self.user), False
        )
        self.assertEqual(
            tags.is_app_link_visible(app_plugin, self.project, superuser), True
        )

    def test_get_project_list(self):
        """Test get_project_list()"""
        user_no_roles = self.make_user('user_no_roles')
        self.assertEqual(len(tags.get_project_list(self.user)), 2)
        self.assertEqual(
            len(tags.get_project_list(self.user, parent=self.category)), 1
        )
        self.assertEqual(len(tags.get_project_list(user_no_roles)), 0)

    # TODO: Refactor and test get_project_list_indent()

    # TODO: Test get_not_found_alert()

    def test_get_project_list_value(self):
        """Test get_project_list_value()"""
        app_plugin = get_app_plugin('filesfolders')
        # TODO: Refactor column system so that function returns link URL as
        # TODO: second return value instead of HTML
        self.assertEqual(
            tags.get_project_list_value(
                app_plugin, 'files', self.project, self.user
            ),
            0,
        )

    def test_get_project_list_column(self):
        """Test get_project_list_columns()"""
        cols = tags.get_project_list_columns()
        self.assertEqual(len(cols), 2)
        self.assertEqual(cols[0]['key'], 'links')  # Assert ordering

    def test_get_project_column_count(self):
        """Test get_project_column_count()"""
        app_plugins = get_active_plugins()

        self.assertEqual(tags.get_project_column_count(app_plugins), 4)
        self.assertEqual(tags.get_project_column_count([]), 2)

    def test_get_user_role_html(self):
        """Test get_user_role_html()"""
        superuser = self.make_user('superuser')
        superuser.is_superuser = True
        superuser.save()
        user_no_roles = self.make_user('user_no_roles')
        self.assertEqual(
            tags.get_user_role_html(self.project, self.user), 'Owner'
        )
        self.assertEqual(
            tags.get_user_role_html(self.project, superuser),
            '<span class="text-danger">Superuser</span>',
        )
        self.assertEqual(
            tags.get_user_role_html(self.project, user_no_roles),
            '<span class="text-muted">N/A</span>',
        )

    def test_get_app_link_state(self):
        """Test get_app_link_state()"""
        app_plugin = get_app_plugin('filesfolders')
        # TODO: Why does this also require app_name?
        self.assertEqual(
            tags.get_app_link_state(app_plugin, 'filesfolders', 'list'),
            'active',
        )
        self.assertEqual(
            tags.get_app_link_state(
                app_plugin, 'filesfolders', 'NON_EXISTING_URL_NAME'
            ),
            '',
        )

    # TODO: Test get_pr_link_state()

    def test_get_star(self):
        """Test get_star()"""
        user_no_roles = self.make_user('user_no_roles')
        self.assertEqual(tags.get_star(self.project, self.user), '')
        set_tag_state(self.project, self.user, name=PROJECT_TAG_STARRED)
        self.assertEqual(
            tags.get_star(self.project, self.user),
            '<i class="fa fa-star text-warning sodar-tag-starred"></i>',
        )
        self.assertEqual(tags.get_star(self.project, user_no_roles), '')

    def test_get_help_highlight(self):
        """Test get_help_highlight()"""
        self.assertEqual(
            tags.get_help_highlight(self.user), 'font-weight-bold text-warning'
        )

    # TODO: Test get_role_import_action() (Set up remote projects)
    # TODO: Test get_target_project_select() (Set up remote projects)

    def test_get_remote_access_legend(self):
        """Test get_remote_access_legend()"""
        self.assertEqual(tags.get_remote_access_legend('NONE'), 'No access')
        self.assertEqual(
            tags.get_remote_access_legend('NON_EXISTING_LEVEL'), 'N/A'
        )

    def test_get_sidebar_app_legend(self):
        """Test get_sidebar_app_legend()"""
        self.assertEqual(
            tags.get_sidebar_app_legend('Update Project'), 'Update<br />Project'
        )
