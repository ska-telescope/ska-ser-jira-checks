"""Report-based tests for issue story points."""

import pytest


@pytest.mark.parametrize(
    "status",
    [
        "To Do",
        "In Progress",
        "Reviewing",
        "READY FOR ACCEPTANCE",
        "BLOCKED",
        "Done",
    ],
)
def test_issues_in_this_pi_have_points(report, status):
    """
    Test that every story/enabler/spike in this PI and status has story points.

    :param report: The report to check.
    :param status: The status to check.
    """
    check_name = f"no_story_points_{status.lower().replace(' ', '_')}"
    violations = report.violations.get(check_name, [])
    if violations:
        msg = (
            f"{len(violations)} stories/enablers/spikes in status '{status}' "
            "do not have story points:\n"
        )
        for v in violations:
            msg += f"- {v.issue_key} ({v.details['issue_type']}): {v.summary}\n"
        pytest.fail(msg)
