"""Report-based tests for issue links."""

import pytest


def test_no_issues_are_child_of_an_objective(report):
    """
    Test that no issues link to an objective with relationship 'Child of'.

    :param report: The report to check.
    """
    violations = report.violations.get("child_of_objective", [])
    if violations:
        msg = f"{len(violations)} issues are child of an objective:\n"
        for v in violations:
            msg += (
                f"- {v.issue_key}: {v.summary} (Objective: {v.details['objective']})\n"
            )
        pytest.fail(msg)


def test_no_issues_relate_to_a_feature(report):
    """
    Test that no issues link to a feature with relationship 'Relates to'.

    :param report: The report to check.
    """
    violations = report.violations.get("relates_to_feature", [])
    if violations:
        msg = f"{len(violations)} issues relate to a feature:\n"
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary} (Feature: {v.details['feature']})\n"
        pytest.fail(msg)


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
        "Done",
    ],
)
def test_issues_in_this_pi_are_linked(report, status):
    """
    Test that every issue is appropriately linked.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"unlinked_{status}", [])
    if violations:
        msg = f"{len(violations)} {status} issues aren't linked:\n"
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary}\n"
        pytest.fail(msg)


@pytest.mark.parametrize(
    "status",
    [
        "To Do",
        "In Progress",
        "BLOCKED",
        "Reviewing",
        "Merge Request",
        "READY FOR ACCEPTANCE",
        "Done",
    ],
)
def test_issues_in_this_pi_have_parent_in_this_pi(report, status):
    """
    Test that every issue in this PI has a parent in this PI.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"parent_not_in_pi_{status}", [])
    if violations:
        msg = (
            f"{len(violations)} {status} issues aren't linked "
            "to a parent in the current PI:\n"
        )
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary}\n"
        pytest.fail(msg)


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
        "Done",
    ],
)
def test_status_is_consistent_with_parent_status(report, status):
    """
    Test that issue status is consistent with the status of its parent issues.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"inconsistent_parent_status_{status}", [])
    if violations:
        msg = f"{len(violations)} {status} issues have inconsistent parent status:\n"
        for v in violations:
            msg += (
                f"- {v.issue_key}: {v.summary} "
                f"(Parents: {', '.join(v.details['inconsistent_parents'])})\n"
            )
        pytest.fail(msg)


@pytest.mark.parametrize("status", ["To Do", "BACKLOG"])
def test_no_todo_or_backlog_issue_with_commits(report, status):
    """
    Test that no 'To Do' or 'Backlog' issues have commits.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"todo_or_backlog_with_commits_{status}", [])
    if violations:
        msg = f"{len(violations)} {status} issues have commits:\n"
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary} (Assignee: {v.details['assignee']})\n"
        pytest.fail(msg)
