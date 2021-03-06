"""Project and user settings API"""
import json
import logging

from projectroles.models import AppSetting, APP_SETTING_TYPES, SODAR_CONSTANTS
from projectroles.plugins import get_app_plugin, get_active_plugins


# SODAR constants
APP_SETTING_SCOPE_PROJECT = SODAR_CONSTANTS['APP_SETTING_SCOPE_PROJECT']
APP_SETTING_SCOPE_USER = SODAR_CONSTANTS['APP_SETTING_SCOPE_USER']
APP_SETTING_SCOPE_PROJECT_USER = SODAR_CONSTANTS[
    'APP_SETTING_SCOPE_PROJECT_USER'
]

# Local constants
VALID_SCOPES = [
    APP_SETTING_SCOPE_PROJECT,
    APP_SETTING_SCOPE_USER,
    APP_SETTING_SCOPE_PROJECT_USER,
]


logger = logging.getLogger(__name__)


class AppSettingAPI:
    @classmethod
    def _check_project_and_user(cls, scope, project, user):
        """
        Ensure one of the project and user parameters is set.

        :param scope: Scope of Setting (USER, PROJECT, PROJECT_USER)
        :param project: Project object
        :param user: User object
        :raise: ValueError if none or both objects exist
        """
        if scope == APP_SETTING_SCOPE_PROJECT:
            if not project:
                raise ValueError('Project unset for setting with project scope')
            if user:
                raise ValueError('User set for setting with project scope')
        elif scope == APP_SETTING_SCOPE_USER:
            if project:
                raise ValueError('Project set for setting with user scope')
            if not user:
                raise ValueError('User unset for setting with user scope')
        elif scope == APP_SETTING_SCOPE_PROJECT_USER:
            if not project:
                raise ValueError(
                    'Project unset for setting with project_user scope'
                )
            if not user:
                raise ValueError(
                    'User unset for setting with project_user scope'
                )

    @classmethod
    def _check_scope(cls, scope):
        """
        Ensure the validity of a scope definition.

        :param scope: String
        :raise: ValueError if scope is not recognized
        """
        if scope not in VALID_SCOPES:
            raise ValueError('Invalid scope "{}"'.format(scope))

    @classmethod
    def _check_type(cls, setting_type):
        """
        Ensure the validity of app setting type.

        :param setting_type: String
        :raise: ValueError if type is not recognized
        """
        if setting_type not in APP_SETTING_TYPES:
            raise ValueError('Invalid setting type "{}"'.format(setting_type))

    @classmethod
    def _get_json_value(cls, value):
        """
        Return JSON value as dict regardless of input type

        :param value: Original value (string or dict)
        :raise: json.decoder.JSONDecodeError if string value is not valid JSON
        :raise: ValueError if value type is not recognized or if value is not
                valid JSON
        :return: dict
        """
        if not value:
            return {}

        try:
            if isinstance(value, str):
                return json.loads(value)

            else:
                json.dumps(value)  # Ensure this is valid
                return value

        except Exception:
            raise ValueError('Value is not valid JSON: {}'.format(value))

    @classmethod
    def _compare_value(cls, setting_obj, input_value):
        """
        Compare input value to value in an AppSetting object

        :param setting_obj: AppSetting object
        :param input_value: Input value (string, int, bool or dict)
        :return: Bool
        """
        if setting_obj.type == 'JSON':
            return setting_obj.value_json == cls._get_json_value(input_value)

        elif setting_obj.type == 'BOOLEAN':
            # TODO: Also do conversion on input value here if necessary
            return bool(int(setting_obj.value)) == input_value

        return setting_obj.value == str(input_value)

    @classmethod
    def get_default_setting(cls, app_name, setting_name, post_safe=False):
        """
        Get default setting value from an app plugin.

        :param app_name: App name (string, must equal "name" in app plugin)
        :param setting_name: Setting name (string)
        :param post_safe: Whether a POST safe value should be returned (bool)
        :return: Setting value (string, integer or boolean)
        :raise: ValueError if app plugin is not found
        :raise: KeyError if nothing is found with setting_name
        """
        app_plugin = get_app_plugin(app_name)

        if not app_plugin:
            raise ValueError('App plugin not found: "{}"'.format(app_name))

        if setting_name in app_plugin.app_settings:
            if app_plugin.app_settings[setting_name]['type'] == 'JSON':
                if not app_plugin.app_settings[setting_name].get('default'):
                    return {}

                if post_safe:
                    return json.dumps(
                        app_plugin.app_settings[setting_name]['default']
                    )

            return app_plugin.app_settings[setting_name]['default']

        raise KeyError(
            'Setting "{}" not found in app plugin "{}"'.format(
                setting_name, app_name
            )
        )

    @classmethod
    def get_app_setting(
        cls, app_name, setting_name, project=None, user=None, post_safe=False
    ):
        """
        Return app setting value for a project or an user. If not set, return
        default.

        :param app_name: App name (string, must equal "name" in app plugin)
        :param setting_name: Setting name (string)
        :param project: Project object (optional)
        :param user: User object (optional)
        :param post_safe: Whether a POST safe value should be returned (bool)
        :return: String or None
        :raise: KeyError if nothing is found with setting_name
        """
        try:
            val = AppSetting.objects.get_setting_value(
                app_name, setting_name, project=project, user=user
            )

        except AppSetting.DoesNotExist:
            val = cls.get_default_setting(app_name, setting_name, post_safe)

        # Handle post_safe for dict values (JSON)
        if post_safe and isinstance(val, dict):
            return json.dumps(val)

        return val

    @classmethod
    def get_all_settings(cls, project=None, user=None, post_safe=False):
        """
        Return all setting values. If the value is not found, return
        the default.

        :param project: Project object (optional)
        :param user: User object (optional)
        :param post_safe: Whether POST safe values should be returned (bool)
        :return: Dict
        :raise: ValueError if neither project nor user are set
        """
        if not project and not user:
            raise ValueError('Project and user are both unset')

        ret = {}
        app_plugins = get_active_plugins()

        for plugin in app_plugins:
            p_settings = cls.get_setting_defs(
                APP_SETTING_SCOPE_PROJECT, plugin=plugin
            )

            for s_key in p_settings:
                ret[
                    'settings.{}.{}'.format(plugin.name, s_key)
                ] = cls.get_app_setting(
                    plugin.name, s_key, project, user, post_safe
                )

        return ret

    @classmethod
    def get_all_defaults(cls, scope, post_safe=False):
        """
        Get all default settings for a scope.

        :param scope: Setting scope (PROJECT, USER or PROJECT_USER)
        :param post_safe: Whether POST safe values should be returned (bool)
        :return: Dict
        """
        cls._check_scope(scope)

        ret = {}
        app_plugins = get_active_plugins()

        for plugin in app_plugins:
            p_settings = cls.get_setting_defs(scope, plugin=plugin)

            for s_key in p_settings:
                ret[
                    'settings.{}.{}'.format(plugin.name, s_key)
                ] = cls.get_default_setting(plugin.name, s_key, post_safe)

        return ret

    @classmethod
    def set_app_setting(
        cls,
        app_name,
        setting_name,
        value,
        project=None,
        user=None,
        validate=True,
    ):
        """
        Set value of an existing project or user settings. Creates the object if
        not found.

        :param app_name: App name (string, must equal "name" in app plugin)
        :param setting_name: Setting name (string)
        :param value: Value to be set
        :param project: Project object (optional)
        :param user: User object (optional)
        :param validate: Validate value (bool, default=True)
        :return: True if changed, False if not changed
        :raise: ValueError if validating and value is not accepted for setting
                type
        :raise: ValueError if neither project nor user are set
        :raise: KeyError if setting name is not found in plugin specification
        """

        def _log_debug(action, app_name, setting_name, value, project, user):
            extra_data = []

            if project:
                extra_data.append('project={}'.format(project.sodar_uuid))
            if user:
                extra_data.append('user={}'.format(user.username))

            logger.debug(
                '{} app setting: {}.{} = "{}"{}'.format(
                    action,
                    app_name,
                    setting_name,
                    value,
                    ' ({})'.format('; '.join(extra_data)) if extra_data else '',
                )
            )

        if not project and not user:
            raise ValueError('Project and user are both unset')

        try:
            setting = AppSetting.objects.get(
                app_plugin__name=app_name,
                name=setting_name,
                project=project,
                user=user,
            )

            if cls._compare_value(setting, value):
                return False

            if validate:
                cls.validate_setting(setting.type, value)

            if setting.type == 'JSON':
                setting.value_json = cls._get_json_value(value)

            else:
                setting.value = value

            setting.save()
            _log_debug('Set', app_name, setting_name, value, project, user)
            return True

        except AppSetting.DoesNotExist:
            app_plugin = get_app_plugin(app_name)

            if setting_name not in app_plugin.app_settings:
                raise KeyError(
                    'Setting "{}" not found in app plugin "{}"'.format(
                        setting_name, app_name
                    )
                )

            s_def = app_plugin.app_settings[setting_name]
            s_type = s_def['type']
            s_mod = (
                bool(s_def['user_modifiable'])
                if 'user_modifiable' in s_def
                else True
            )

            cls._check_scope(s_def['scope'])
            cls._check_project_and_user(s_def['scope'], project, user)

            if validate:
                v = cls._get_json_value(value) if s_type == 'JSON' else value
                cls.validate_setting(s_type, v)

            s_vals = {
                'app_plugin': app_plugin.get_model(),
                'project': project,
                'user': user,
                'name': setting_name,
                'type': s_type,
                'user_modifiable': s_mod,
            }

            if s_type == 'JSON':
                s_vals['value_json'] = cls._get_json_value(value)

            else:
                s_vals['value'] = value

            AppSetting.objects.create(**s_vals)
            _log_debug('Create', app_name, setting_name, value, project, user)
            return True

    @classmethod
    def validate_setting(cls, setting_type, setting_value):
        """
        Validate setting value according to its type.

        :param setting_type: Setting type
        :param setting_value: Setting value
        :raise: ValueError if setting_type or setting_value is invalid
        """
        cls._check_type(setting_type)

        if setting_type == 'BOOLEAN':
            if not isinstance(setting_value, bool):
                raise ValueError(
                    'Please enter a valid boolean value ({})'.format(
                        setting_value
                    )
                )

        elif setting_type == 'INTEGER':
            if (
                not isinstance(setting_value, int)
                and not str(setting_value).isdigit()
            ):
                raise ValueError(
                    'Please enter a valid integer value ({})'.format(
                        setting_value
                    )
                )

        elif setting_type == 'JSON':
            try:
                json.dumps(setting_value)
            except TypeError:
                raise ValueError(
                    'Please enter valid JSON ({})'.format(setting_value)
                )

        return True

    @classmethod
    def get_setting_def(cls, name, plugin=None, app_name=None):
        """
        Return definition for a single app setting, either based on an app name
        or the plugin object.

        :param name: Setting name
        :param plugin: Plugin object extending ProjectAppPluginPoint
        :param app_name: Name of the app plugin (string)
        :return: Dict
        :raise: ValueError if neither app_name or plugin are set or if setting
                is not found in plugin
        """
        if not plugin and not app_name:
            raise ValueError('Plugin and app name both unset')

        elif not plugin:
            plugin = get_app_plugin(app_name)

            if not plugin:
                raise ValueError(
                    'Plugin not found with app name "{}"'.format(app_name)
                )

        if name not in plugin.app_settings:
            raise ValueError(
                'App setting not found in app "{}" with name "{}"'.format(
                    plugin.name, name
                )
            )

        setting_def = plugin.app_settings[name]
        cls._check_type(setting_def['type'])

        return setting_def

    @classmethod
    def get_setting_defs(
        cls, scope, plugin=False, app_name=False, user_modifiable=False
    ):
        """
        Return app setting definitions of a specific scope from a plugin.

        :param scope: PROJECT, USER or PROJECT_USER
        :param plugin: project app plugin object extending ProjectAppPluginPoint
        :param app_name: Name of the app plugin (string)
        :param user_modifiable: Only return modifiable settings if True
                                (boolean)
        :return: Dict
        :raise: ValueError if scope is invalid or if if neither app_name or
                plugin are set
        """
        if not plugin and not app_name:
            raise ValueError('Plugin and app name both unset')

        if not plugin:
            plugin = get_app_plugin(app_name)

            if not plugin:
                raise ValueError(
                    'Plugin not found with app name "{}"'.format(app_name)
                )

        cls._check_scope(scope)
        setting_defs = {
            k: v
            for k, v in plugin.app_settings.items()
            if (
                'scope' in v
                and v['scope'] == scope
                and (
                    not user_modifiable
                    or (
                        'user_modifiable' not in v
                        or v['user_modifiable'] is True
                    )
                )
            )
        }

        # Ensure type validity
        for k, v in setting_defs.items():
            cls._check_type(v['type'])

        return setting_defs
