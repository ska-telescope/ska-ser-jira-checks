"""Report-based tests for RFA issues."""

import pytest


def test_rfa_issues_have_outcomes(report):
    """
    Test that all READY FOR ACCEPTANCE issues have outcomes.

    :param report: The report to check.
    """
    violations = report.violations.get("rfa_no_outcomes", [])
    if violations:
        msg = f"{len(violations)} READY FOR ACCEPTANCE issues have no outcomes:\n"
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary} (Assignee: {v.details['assignee']})\n"
        pytest.fail(msg)


@pytest.mark.parametrize("status", ["In Progress", "Reviewing", "Merge Request"])
def test_no_active_issues_have_only_closed_merge_requests(report, status):
    """
    Test that In Progress and Reviewing issues don't have only merged MRs.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"active_with_only_closed_mrs_{status}", [])
    if violations:
        msg = f"{len(violations)} {status} issues have no unmerged commits:\n"
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary} (Assignee: {v.details['assignee']})\n"
        pytest.fail(msg)


@pytest.mark.parametrize("status", ["READY FOR ACCEPTANCE", "Done"])
def test_no_rfa_or_done_issues_have_open_merge_requests(report, status):
    """
    Test that no READY FOR ACCEPTANCE or Done issues have unmerged MRs.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"rfa_or_done_with_open_mrs_{status}", [])
    if violations:
        msg = f"{len(violations)} {status} issues have unmerged commits:\n"
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary} (Assignee: {v.details['assignee']})\n"
        pytest.fail(msg)


def test_not_too_many_rfa_issues(report):
    """
    Test that there are not too many READY FOR ACCEPTANCE issues.

    :param report: The report to check.
    """
    violations = report.violations.get("too_many_rfa", [])
    if violations:
        violation = violations[0]
        count = violation.details["rfa_count"]
        msg = f"{count} issues are READY FOR ACCEPTANCE:\n"
        for issue in violation.details["issues"]:
            msg += (
                f"- {issue['key']}: {issue['summary']} "
                f"(Assignee: {issue['assignee']})\n"
            )
        pytest.fail(msg)
