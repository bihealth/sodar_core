"""Rule definitions for the ``bgjobs`` app."""

import rules
from projectroles import rules as pr_rules  # To access common predicates


# Predicates -------------------------------------------------------------------


# TODO: If we need to assign new predicates, we do it here


# Rules ------------------------------------------------------------------------


# TODO: Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------------

# Allow viewing of background jobs
rules.add_perm(
    'bgjobs.view_data',
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor
    | pr_rules.is_project_guest,
)

# Allow viewing of background jobs
rules.add_perm(
    'bgjobs.view_jobs_own',
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor
    | pr_rules.is_project_guest,
)

# Allow creating background jobs
rules.add_perm(
    'bgjobs.create_bgjob',
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor,
)

# Allow modifying or deleting the user's background jobs
rules.add_perm(
    'bgjobs.update_bgjob_own',
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor
    | pr_rules.is_project_guest,
)

# Allow modifying or deleting all background jobs
rules.add_perm(
    'bgjobs.update_bgjob_all',
    pr_rules.is_project_owner | pr_rules.is_project_delegate,
)

# Allow viewing site-global background jobs (not project-specific).
rules.add_perm('bgjobs.site_view_data', rules.is_superuser)
