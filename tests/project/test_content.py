"""Test issue content."""

from typing import Any

import pytest

from tests.conftest import fail_if_data


@pytest.mark.parametrize(
    "status",
    [
        "To Do",
        "In Progress",
        "BLOCKED",
        "Reviewing",
        "Merge Request",
        "READY FOR ACCEPTANCE",
    ],
)
def test_issues_have_description(issues_by_status, status):
    """
    Test that all issues of certain statuses have descriptions.

    It's okay for tickets in the BACKLOG to be lacking descriptions,
    but once a ticket has been promoted to To Do or beyond,
    a description should be required.

    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    no_description: list[dict[str, Any]] = []

    for issue in issues_by_status[status]:
        if not issue.fields.description:
            no_description.append(
                {"Issue": issue.key, "Creator": issue.fields.creator.name}
            )

    fail_if_data(
        no_description,
        f"{{Issue}} ({{Creator}})) is {status} without a description.",
        f"{{length}} {status} issues are lacking a description:",
        sort_key="Issue",
    )


@pytest.mark.parametrize(
    "status",
    [
        "To Do",
        "In Progress",
        "BLOCKED",
        "Reviewing",
        "Merge Request",
        "READY FOR ACCEPTANCE",
    ],
)
def test_issues_have_a_fix_version(issues_by_status, status):
    """
    Test that all issues of certain status have a fixVersion.

    Issues in the BACKLOG need not be assigned to a PI (i.e. a fixVersion).
    But promoting a issue to 'To Do' indicates an intent to work on it imminently,
    so 'To Do' issues should have a PI, as should issues that are 'In Progress' etc.

    This test does not check 'Done' issues because the past is the past.

    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    no_pi = []
    for issue in issues_by_status[status]:
        if issue.fields.fixVersions:
            continue
        no_pi.append({"Issue": issue.key, "Summary": issue.fields.summary})

    fail_if_data(
        no_pi,
        f"{{Issue}} ('{{Summary}}') is {status} and does not have a PI.",
        f"{{length}} {status} issues do not have a PI:",
        sort_key="Issue",
    )


@pytest.mark.parametrize(
    "status",
    [
        "To Do",
        "In Progress",
        "BLOCKED",
        "Reviewing",
        "Merge Request",
        "READY FOR ACCEPTANCE",
    ],
)
def test_no_issues_with_old_fix_version(pi, issues_by_status, status):
    """
    Test that no incomplete issues have an old fixVersion.

    It's okay for "Done" issues to have an old fixVersion,
    but other issues should link to a current or future fixVersion
    (or not be linked to a fixVersion at all).

    :param pi: the current Program Increment number
    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    current_pi = f"PI{pi}"
    next_pi = f"PI{pi+1}"

    issues_with_old_fixversion: list[dict[str, Any]] = []

    for issue in issues_by_status[status]:
        fix_versions = set(issue.name for issue in issue.fields.fixVersions)
        if not fix_versions:
            continue

        if current_pi in fix_versions:
            continue
        if next_pi in fix_versions:
            continue

        assignee = issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
        issues_with_old_fixversion.append(
            {"Assignee": assignee, "Issue": issue.key, "Summary": issue.fields.summary}
        )

    fail_if_data(
        issues_with_old_fixversion,
        "{Issue} ('{Summary}'), assigned to {Assignee}, " f"is {status} with old PI.",
        f"{{length}} {status} issues have old PI:",
        sort_key="Issue",
    )
