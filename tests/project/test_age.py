"""Report-based tests for age of tickets."""

import pytest


@pytest.mark.parametrize(
    "status",
    [
        "BACKLOG",
        "To Do",
        "In Progress",
        "Reviewing",
        "Merge Request",
        "BLOCKED",
        "READY FOR ACCEPTANCE",
    ],
)
def test_issues_not_too_old(report, status):
    """
    Test that every issue has been updated reasonably recently.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"too_old_{status}", [])

    if violations:
        msg = f"{len(violations)} issues have been {status} for too long:\n"
        for v in violations:
            msg += (
                f"- {v.issue_key}: {v.summary} "
                f"(Age: {v.details['age_days']} days, "
                f"Assignee: {v.details['assignee']})\n"
            )
        pytest.fail(msg)
