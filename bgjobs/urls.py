"""URL configuration for the ``bgjobs`` app.

Note that the job detail view is implemented
"""

from django.conf.urls import url
from . import views

app_name = 'bgjobs'

urlpatterns = [
    # List jobs that the user has access to
    url(
        regex=r'^(?P<project>[0-9a-f-]+)/list$',
        view=views.ProjectBackgroundJobView.as_view(),
        name='list',
    ),
    # Clear jobs in project owned by the current user.
    url(
        regex=r'^(?P<project>[0-9a-f-]+)/clear/own$',
        view=views.BackgroundJobClearOwnView.as_view(),
        name='clear_own',
    ),
    # Clear jobs in project regardless of the user.
    url(
        regex=r'^(?P<project>[0-9a-f-]+)/clear/all$',
        view=views.BackgroundJobClearAllView.as_view(),
        name='clear_all',
    ),
    # List global background jobs.
    url(
        regex=r'^list$',
        view=views.GlobalBackgroundJobView.as_view(),
        name='site_list',
    ),
]
