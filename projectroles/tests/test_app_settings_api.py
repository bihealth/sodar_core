"""Tests for the project settings API in the projectroles app"""

from test_plus.test import TestCase

from ..models import Role, AppSetting, SODAR_CONSTANTS
from ..plugins import get_app_plugin
from ..app_settings import AppSettingAPI
from .test_models import ProjectMixin, RoleAssignmentMixin, AppSettingMixin

# SODAR constants
PROJECT_ROLE_OWNER = SODAR_CONSTANTS['PROJECT_ROLE_OWNER']
PROJECT_ROLE_DELEGATE = SODAR_CONSTANTS['PROJECT_ROLE_DELEGATE']
PROJECT_ROLE_CONTRIBUTOR = SODAR_CONSTANTS['PROJECT_ROLE_CONTRIBUTOR']
PROJECT_ROLE_GUEST = SODAR_CONSTANTS['PROJECT_ROLE_GUEST']
PROJECT_TYPE_CATEGORY = SODAR_CONSTANTS['PROJECT_TYPE_CATEGORY']
PROJECT_TYPE_PROJECT = SODAR_CONSTANTS['PROJECT_TYPE_PROJECT']
SUBMIT_STATUS_OK = SODAR_CONSTANTS['SUBMIT_STATUS_OK']
SUBMIT_STATUS_PENDING = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
SUBMIT_STATUS_PENDING_TASKFLOW = SODAR_CONSTANTS['SUBMIT_STATUS_PENDING']
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']

# Local settings
EXISTING_SETTING = 'project_bool_setting'
EXAMPLE_APP_NAME = 'example_project_app'

# App settings API
app_settings = AppSettingAPI()


class TestAppSettingAPI(
    ProjectMixin, RoleAssignmentMixin, AppSettingMixin, TestCase
):
    """Tests for AppSettingAPI"""

    # NOTE: This assumes an example app is available

    def setUp(self):
        # Init project
        self.project = self._make_project(
            title='TestProject', type=PROJECT_TYPE_PROJECT, parent=None
        )

        # Init role
        self.role_owner = Role.objects.get(name=PROJECT_ROLE_OWNER)

        # Init user & role
        self.user = self.make_user('owner')
        self.owner_as = self._make_assignment(
            self.project, self.user, self.role_owner
        )

        # Init test setting
        self.setting_str_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_str_setting',
            'setting_type': 'STRING',
            'value': 'test',
            'update_value': 'better test',
            'non_valid_value': False,
        }
        self.setting_int_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_int_setting',
            'setting_type': 'INTEGER',
            'value': 0,
            'update_value': 170,
            'non_valid_value': 'Nan',
        }
        self.setting_bool_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_bool_setting',
            'setting_type': 'BOOLEAN',
            'value': False,
            'update_value': True,
            'non_valid_value': 170,
        }
        self.setting_json_values = {
            'app_name': EXAMPLE_APP_NAME,
            'project': self.project,
            'name': 'project_json_setting',
            'setting_type': 'JSON',
            'value': {
                'Example': 'Value',
                'list': [1, 2, 3, 4, 5],
                'level_6': False,
            },
            'update_value': {'Test_more': 'often_always'},
            'non_valid_value': self.project,
        }
        self.settings = [
            self.setting_int_values,
            self.setting_json_values,
            self.setting_str_values,
            self.setting_bool_values,
        ]
        for s in self.settings:
            self._make_setting(
                app_name=s['app_name'],
                name=s['name'],
                setting_type=s['setting_type'],
                value=s['value'] if s['setting_type'] != 'JSON' else '',
                value_json=s['value'] if s['setting_type'] == 'JSON' else {},
                project=s['project'],
            )

    def test_get_project_setting(self):
        """Test get_app_setting()"""
        for setting in self.settings:
            val = app_settings.get_app_setting(
                app_name=setting['app_name'],
                setting_name=setting['name'],
                project=setting['project'],
            )
            self.assertEqual(val, setting['value'])

    def test_get_project_setting_default(self):
        """Test get_app_setting() with default value for existing setting"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)
        default_val = app_plugin.app_settings[EXISTING_SETTING]['default']

        val = app_settings.get_app_setting(
            app_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING,
            project=self.project,
        )

        self.assertEqual(val, default_val)

    def test_get_project_setting_nonexisting(self):
        """Test get_app_setting() with an non-existing setting"""
        with self.assertRaises(KeyError):
            app_settings.get_app_setting(
                app_name=EXAMPLE_APP_NAME,
                setting_name='NON-EXISTING SETTING',
                project=self.project,
            )

    def test_get_project_setting_post_safe(self):
        """Test get_app_setting() with JSON setting and post_safe=True"""
        val = app_settings.get_app_setting(
            app_name=self.setting_json_values['app_name'],
            setting_name=self.setting_json_values['name'],
            project=self.setting_json_values['project'],
            post_safe=True,
        )
        self.assertEqual(type(val), str)

    def test_set_project_setting(self):
        """Test set_app_setting()"""

        for setting in self.settings:
            ret = app_settings.set_app_setting(
                app_name=setting['app_name'],
                setting_name=setting['name'],
                project=setting['project'],
                value=setting['update_value'],
            )
            self.assertEqual(ret, True)

            val = app_settings.get_app_setting(
                app_name=setting['app_name'],
                setting_name=setting['name'],
                project=setting['project'],
            )
            self.assertEqual(val, setting['update_value'])

    def test_set_project_setting_unchanged(self):
        """Test set_app_setting() with an unchnaged value"""

        for setting in self.settings:
            ret = app_settings.set_app_setting(
                app_name=setting['app_name'],
                setting_name=setting['name'],
                project=setting['project'],
                value=setting['value'],
            )
            self.assertEqual(
                ret,
                False,
                msg='setting={}.{}'.format(
                    setting['app_name'], setting['name']
                ),
            )

            val = app_settings.get_app_setting(
                app_name=setting['app_name'],
                setting_name=setting['name'],
                project=setting['project'],
            )
            self.assertEqual(
                val,
                setting['value'],
                msg='setting={}.{}'.format(
                    setting['app_name'], setting['name']
                ),
            )

    def test_set_project_setting_new(self):
        """Test set_app_setting() with a new but defined setting"""

        # Assert precondition
        val = AppSetting.objects.get(
            app_plugin=get_app_plugin(EXAMPLE_APP_NAME).get_model(),
            project=self.project,
            name=EXISTING_SETTING,
        ).value
        self.assertEqual(bool(int(val)), False)

        ret = app_settings.set_app_setting(
            app_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING,
            value=True,
            project=self.project,
        )

        # Asset postconditions
        self.assertEqual(ret, True)
        val = app_settings.get_app_setting(
            app_name=EXAMPLE_APP_NAME,
            setting_name=EXISTING_SETTING,
            project=self.project,
        )
        self.assertEqual(True, val)

        setting = AppSetting.objects.get(
            app_plugin=get_app_plugin(EXAMPLE_APP_NAME).get_model(),
            project=self.project,
            name=EXISTING_SETTING,
        )
        self.assertIsInstance(setting, AppSetting)

    def test_set_project_setting_undefined(self):
        """Test set_app_setting() with an undefined setting (should fail)"""
        with self.assertRaises(KeyError):
            app_settings.set_app_setting(
                app_name=EXAMPLE_APP_NAME,
                setting_name='new_setting',
                value='new',
                project=self.project,
            )

    def test_validator(self):
        """Test validate_setting() with type BOOLEAN"""
        for setting in self.settings:
            self.assertEqual(
                app_settings.validate_setting(
                    setting['setting_type'], setting['value']
                ),
                True,
            )
            if setting['setting_type'] == 'STRING':
                continue
            with self.assertRaises(ValueError):
                app_settings.validate_setting(
                    setting['setting_type'], setting['non_valid_value']
                )

    def test_validate_project_setting_int(self):
        """Test validate_setting() with type INTEGER"""
        self.assertEqual(app_settings.validate_setting('INTEGER', 170), True)
        # NOTE: String is also OK if it corresponds to an int
        self.assertEqual(app_settings.validate_setting('INTEGER', '170'), True)

        with self.assertRaises(ValueError):
            app_settings.validate_setting('INTEGER', 'not an integer')

    def test_validate_project_setting_invalid(self):
        """Test validate_setting() with an invalid type"""
        with self.assertRaises(ValueError):
            app_settings.validate_setting('INVALID_TYPE', 'value')

    def test_get_setting_def_plugin(self):
        """Test get_setting_def() with a plugin"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)
        expected = {
            'scope': APP_SETTING_SCOPE_PROJECT,
            'type': 'STRING',
            'label': 'String Setting',
            'default': '',
            'description': 'Example string project setting',
            'user_modifiable': True,
        }
        s_def = app_settings.get_setting_def(
            'project_str_setting', plugin=app_plugin
        )
        self.assertEqual(s_def, expected)

    def test_get_setting_def_app_name(self):
        """Test get_setting_def() with an app name"""
        expected = {
            'scope': APP_SETTING_SCOPE_PROJECT,
            'type': 'STRING',
            'label': 'String Setting',
            'default': '',
            'description': 'Example string project setting',
            'user_modifiable': True,
        }
        s_def = app_settings.get_setting_def(
            'project_str_setting', app_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(s_def, expected)

    def test_get_setting_def_user(self):
        """Test get_setting_def() with a user setting"""
        expected = {
            'scope': APP_SETTING_SCOPE_USER,
            'type': 'STRING',
            'label': 'String Setting',
            'default': '',
            'description': 'Example string user setting',
            'user_modifiable': True,
        }
        s_def = app_settings.get_setting_def(
            'user_str_setting', app_name=EXAMPLE_APP_NAME
        )
        self.assertEqual(s_def, expected)

    def test_get_setting_def_invalid(self):
        """Test get_setting_def() with innvalid input"""
        with self.assertRaises(ValueError):
            app_settings.get_setting_def(
                'non_existing_setting', app_name=EXAMPLE_APP_NAME
            )

        with self.assertRaises(ValueError):
            app_settings.get_setting_def(
                'project_str_setting', app_name='non_existing_app_name'
            )

        # Both app_name and plugin unset
        with self.assertRaises(ValueError):
            app_settings.get_setting_def('project_str_setting')

    def test_get_setting_defs_project(self):
        """Test get_setting_defs() with the PROJECT scope"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)
        expected = {
            'project_str_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'STRING',
                'label': 'String Setting',
                'default': '',
                'description': 'Example string project setting',
                'user_modifiable': True,
            },
            'project_int_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'INTEGER',
                'label': 'Integer Setting',
                'default': 0,
                'description': 'Example integer project setting',
                'user_modifiable': True,
            },
            'project_bool_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'BOOLEAN',
                'label': 'Boolean Setting',
                'default': False,
                'description': 'Example boolean project setting',
                'user_modifiable': True,
            },
            'project_json_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'JSON',
                'label': 'JSON Setting',
                'default': {
                    'Example': 'Value',
                    'list': [1, 2, 3, 4, 5],
                    'level_6': False,
                },
                'description': 'Example JSON project setting',
                'user_modifiable': True,
            },
            'project_hidden_setting': {
                'scope': APP_SETTING_SCOPE_PROJECT,
                'type': 'STRING',
                'default': '',
                'description': 'Example hidden project setting',
                'user_modifiable': False,
            },
        }
        defs = app_settings.get_setting_defs(
            app_plugin, APP_SETTING_SCOPE_PROJECT
        )
        self.assertEqual(defs, expected)

    def test_get_setting_defs_user(self):
        """Test get_setting_defs() with the USER scope"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)
        expected = {
            'user_str_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'STRING',
                'label': 'String Setting',
                'default': '',
                'description': 'Example string user setting',
                'user_modifiable': True,
            },
            'user_int_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'INTEGER',
                'label': 'Integer Setting',
                'default': 0,
                'description': 'Example integer user setting',
                'user_modifiable': True,
            },
            'user_bool_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'BOOLEAN',
                'label': 'Boolean Setting',
                'default': False,
                'description': 'Example boolean user setting',
                'user_modifiable': True,
            },
            'user_json_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'JSON',
                'label': 'JSON Setting',
                'default': {
                    'Example': 'Value',
                    'list': [1, 2, 3, 4, 5],
                    'level_6': False,
                },
                'description': 'Example JSON project setting',
                'user_modifiable': True,
            },
            'user_hidden_setting': {
                'scope': APP_SETTING_SCOPE_USER,
                'type': 'STRING',
                'default': '',
                'description': 'Example hidden user setting',
                'user_modifiable': False,
            },
        }
        defs = app_settings.get_setting_defs(app_plugin, APP_SETTING_SCOPE_USER)
        self.assertEqual(defs, expected)

    def test_get_setting_defs_modifiable(self):
        """Test get_setting_defs() with the user_modifiable arg"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)
        defs = app_settings.get_setting_defs(
            app_plugin, APP_SETTING_SCOPE_PROJECT
        )
        self.assertEqual(len(defs), 5)
        defs = app_settings.get_setting_defs(
            app_plugin, APP_SETTING_SCOPE_PROJECT, user_modifiable=True
        )
        self.assertEqual(len(defs), 4)

    def test_get_setting_defs_invalid(self):
        """Test get_setting_defs() with an invalid scope"""
        app_plugin = get_app_plugin(EXAMPLE_APP_NAME)

        with self.assertRaises(ValueError):
            app_settings.get_setting_defs(app_plugin, 'Ri4thai8aez5ooRa')

    def test_get_all_defaults_project(self):
        """Test get_all_defaults() with the PROJECT scope"""
        prefix = 'settings.{}.'.format(EXAMPLE_APP_NAME)
        defaults = app_settings.get_all_defaults(APP_SETTING_SCOPE_PROJECT)
        self.assertEqual(defaults[prefix + 'project_bool_setting'], False)

    def test_get_all_defaults_user(self):
        """Test get_all_defaults() with the USER scope"""
        prefix = 'settings.{}.'.format(EXAMPLE_APP_NAME)
        defaults = app_settings.get_all_defaults(APP_SETTING_SCOPE_USER)
        self.assertEqual(defaults[prefix + 'user_str_setting'], '')
        self.assertEqual(defaults[prefix + 'user_int_setting'], 0)
        self.assertEqual(defaults[prefix + 'user_bool_setting'], False)
