"""Code related to ``django-plugins``.

First, it creates a ``ProjectAppPluginPoint`` for the ``bgjobs`` app.

Second, it creates a new plugin point for the registering ``BackgroundJob``
specializations.
"""

from djangoplugins.point import PluginPoint

from projectroles.plugins import ProjectAppPluginPoint, SiteAppPluginPoint
from .urls import urlpatterns


class ProjectAppPlugin(ProjectAppPluginPoint):
    """Plugin for registering app with the ``ProjectAppPluginPoint`` from the
    ``projectroles`` app."""

    name = 'bgjobs'
    title = 'Background Jobs'
    urls = urlpatterns

    icon = 'tasks'

    entry_point_url_id = 'bgjobs:list'

    description = 'Jobs executed in the background'

    #: Required permission for accessing the app
    app_permission = 'bgjobs.view_data'

    #: Enable or disable general search from project title bar
    search_enable = False

    #: List of search object types for the app
    search_types = []

    #: Search results template
    search_template = None

    #: App card template for the project details page
    details_template = 'bgjobs/_details_card.html'

    #: App card title for the project details page
    details_title = 'Background Jobs App Overview'

    #: Position in plugin ordering
    plugin_ordering = 100


class BackgroundJobsPluginPoint(PluginPoint):
    """Definition of a plugin point for registering background job types with
    the ``bgjobs`` app."""

    #: Mapping from job specialization name to specialization class
    # (OneToOneField "inheritance").
    job_specs = {}


class SiteAppPlugin(SiteAppPluginPoint):
    """Projectroles plugin for registering the app"""

    #: Name (slug-safe, used in URLs)
    name = 'sitebgjobs'

    #: Title (used in templates)
    title = 'Global Background Jobs'

    #: App URLs (will be included in settings by djangoplugins)
    urls = urlpatterns

    #: FontAwesome icon ID string
    icon = 'tasks'

    #: Description string
    description = 'Global background jobs'

    #: Entry point URL ID
    entry_point_url_id = 'bgjobs:site_list'

    #: Required permission for displaying the app
    app_permission = 'bgjobs:bgjobs.site_view_data'
