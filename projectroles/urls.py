from django.conf.urls import url

from . import views


app_name = 'projectroles'

urlpatterns = [
    # General project views
    url(
        regex=r'^(?P<project>[0-9a-f-]+)$',
        view=views.ProjectDetailView.as_view(),
        name='detail',
    ),
    url(
        regex=r'^update/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectUpdateView.as_view(),
        name='update',
    ),
    url(
        regex=r'^create$',
        view=views.ProjectCreateView.as_view(),
        name='create',
    ),
    url(
        regex=r'^create/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectCreateView.as_view(),
        name='create',
    ),
    # Search view
    url(
        regex=r'^search/$',
        view=views.ProjectSearchView.as_view(),
        name='search',
    ),
    # Project role views
    url(
        regex=r'^members/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectRoleView.as_view(),
        name='roles',
    ),
    url(
        regex=r'^members/create/(?P<project>[0-9a-f-]+)$',
        view=views.RoleAssignmentCreateView.as_view(),
        name='role_create',
    ),
    url(
        regex=r'^members/update/(?P<roleassignment>[0-9a-f-]+)$',
        view=views.RoleAssignmentUpdateView.as_view(),
        name='role_update',
    ),
    url(
        regex=r'^members/delete/(?P<roleassignment>[0-9a-f-]+)$',
        view=views.RoleAssignmentDeleteView.as_view(),
        name='role_delete',
    ),
    url(
        regex=r'^members/import/(?P<project>[0-9a-f-]+)$',
        view=views.RoleAssignmentImportView.as_view(),
        name='role_import',
    ),
    # Project invite views
    url(
        regex=r'^invites/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectInviteView.as_view(),
        name='invites',
    ),
    url(
        regex=r'^invites/create/(?P<project>[0-9a-f-]+)$',
        view=views.ProjectInviteCreateView.as_view(),
        name='invite_create',
    ),
    url(
        regex=r'^invites/accept/(?P<secret>[\w\-]+)$',
        view=views.ProjectInviteAcceptView.as_view(),
        name='invite_accept',
    ),
    url(
        regex=r'^invites/resend/(?P<projectinvite>[0-9a-f-]+)$',
        view=views.ProjectInviteResendView.as_view(),
        name='invite_resend',
    ),
    url(
        regex=r'^invites/revoke/(?P<projectinvite>[0-9a-f-]+)$',
        view=views.ProjectInviteRevokeView.as_view(),
        name='invite_revoke',
    ),
    # Remote site and project views
    url(
        regex=r'^remote/$',
        view=views.RemoteManagementView.as_view(),
        name='remote',
    ),
    url(
        regex=r'^remote/site/add$',
        view=views.RemoteSiteCreateView.as_view(),
        name='remote_site_create',
    ),
    url(
        regex=r'^remote/site/update/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteSiteUpdateView.as_view(),
        name='remote_site_update',
    ),
    url(
        regex=r'^remote/site/delete/(?P<remotesite>[0-9a-f-]+)$',
        view=views.RemoteSiteDeleteView.as_view(),
        name='remote_site_delete',
    ),
    # Javascript API views
    url(
        regex=r'^star/(?P<project>[0-9a-f-]+)',
        view=views.ProjectStarringAPIView.as_view(),
        name='star',
    ),
    # Taskflow API views
    url(
        regex=r'^taskflow/get$',
        view=views.ProjectGetAPIView.as_view(),
        name='taskflow_project_get',
    ),
    url(
        regex=r'^taskflow/update$',
        view=views.ProjectUpdateAPIView.as_view(),
        name='taskflow_project_update',
    ),
    url(
        regex=r'^taskflow/role/get$',
        view=views.RoleAssignmentGetAPIView.as_view(),
        name='taskflow_role_get',
    ),
    url(
        regex=r'^taskflow/role/set$',
        view=views.RoleAssignmentSetAPIView.as_view(),
        name='taskflow_role_set',
    ),
    url(
        regex=r'^taskflow/role/delete$',
        view=views.RoleAssignmentDeleteAPIView.as_view(),
        name='taskflow_role_delete',
    ),
    url(
        regex=r'^taskflow/settings/get$',
        view=views.ProjectSettingsGetAPIView.as_view(),
        name='taskflow_settings_get',
    ),
    url(
        regex=r'^taskflow/settings/set$',
        view=views.ProjectSettingsSetAPIView.as_view(),
        name='taskflow_settings_set',
    ),
]
