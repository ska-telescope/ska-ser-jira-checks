"""Test issue content."""

import pprint
from collections import defaultdict

import pytest


@pytest.mark.parametrize(
    "status",
    [
        "In Progress",
        "To Do",
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
    no_description = defaultdict(list)
    count = 0

    for issue in issues_by_status[status]:
        if not issue.fields.description:
            no_description[issue.fields.creator.name].append(issue.key)
            count += 1

    if len(no_description) > 1:
        pytest.fail(
            f"{count} '{status}' issues are lacking a description:\n"
            f"{pprint.pformat(dict(no_description))}"
        )
    elif len(no_description) == 1:
        creator, issues = no_description.popitem()
        if len(issues) > 1:
            pytest.fail(
                f"{creator} has {count} '{status}' issues without a description:\n"
                f"{pprint.pformat(issues)}"
            )
        else:  # len(issues) == 1
            pytest.fail(f"{creator}: {issues[0]} is '{status}' without a description.")


@pytest.mark.parametrize(
    "status",
    ["In Progress", "BLOCKED", "Reviewing", "Merge Request", "READY FOR ACCEPTANCE"],
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
    no_pi = [
        issue.key for issue in issues_by_status[status] if not issue.fields.fixVersions
    ]

    if len(no_pi) > 1:
        pytest.fail(
            f"{len(no_pi)} '{status}' issues do not have a fixVersions field:\n{no_pi}"
        )
    elif len(no_pi) == 1:
        pytest.fail(f"{no_pi[0]} is '{status}' and does not have a fixVersions field.")


@pytest.mark.parametrize(
    "status",
    [
        "BACKLOG",
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

    TODO: This should be refactored so that it doesn't complain if an issue
    links to an old *and* current fixVersion.

    :param pi: the current Program Increment number
    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    current_pi = f"PI{pi}"
    old_pis = {f"PI{i}" for i in range(1, pi)}

    issues_with_old_fixversion = defaultdict(list)
    count = 0

    for issue in issues_by_status[status]:
        fix_versions = set(issue.fields.fixVersions)
        if current_pi in fix_versions:
            continue
        if old_pis.intersection(fix_versions):
            assignee = (
                issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            )
            issues_with_old_fixversion[assignee].append(issue.key)
            count += 1
            break

    if len(issues_with_old_fixversion) > 1:
        pytest.fail(
            f"{count} '{status}' issues have old fixVersions:\n"
            f"{pprint.pformat(dict(issues_with_old_fixversion))}"
        )
    elif len(issues_with_old_fixversion) == 1:
        assignee, issues = issues_with_old_fixversion.popitem()
        if len(issues) > 1:
            pytest.fail(
                f"{assignee} has {count} '{status}' issues with old fixVersions:\n"
                f"{pprint.pformat(issues)}"
            )
        else:  # len(issues) == 1
            pytest.fail(f"{assignee} has {issues[0]} '{status}' with old fixVersion.")
