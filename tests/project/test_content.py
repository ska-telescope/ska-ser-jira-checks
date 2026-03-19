"""Report-based tests for issue content."""

import pytest


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
def test_issues_have_description(report, status):
    """
    Test that all issues of certain statuses have descriptions.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"no_description_{status}", [])
    if violations:
        msg = f"{len(violations)} {status} issues are lacking a description:\n"
        for v in violations:
            msg += f"- {v.issue_key} ({v.details['creator']})\n"
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
    ],
)
def test_issues_have_a_fix_version(report, status):
    """
    Test that all issues of certain status have a fixVersion.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"no_fix_version_{status}", [])
    if violations:
        msg = f"{len(violations)} {status} issues do not have a PI:\n"
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
    ],
)
def test_no_issues_with_old_fix_version(report, status):
    """
    Test that no incomplete issues have an old fixVersion.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"old_fix_version_{status}", [])
    if violations:
        msg = f"{len(violations)} {status} issues have old PI:\n"
        for v in violations:
            msg += (
                f"- {v.issue_key}: {v.summary} "
                f"(Assignee: {v.details['assignee']})\n"
            )
        pytest.fail(msg)
