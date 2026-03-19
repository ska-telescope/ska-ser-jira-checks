"""Report-based tests for issue assignments."""

import pytest


@pytest.mark.parametrize(
    "status",
    [
        "In Progress",
        "Reviewing",
        "Merge Request",
        "READY FOR ACCEPTANCE",
        "Done",
        "BLOCKED",
    ],
)
def test_tickets_have_assignee(report, status):
    """
    Test that all tickets of certain statuses are assigned to someone.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"unassigned_{status}", [])
    if violations:
        msg = f"{len(violations)} '{status}' issues are unassigned:\n"
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary}\n"
        pytest.fail(msg)


def test_noone_has_too_much_wip(report):
    """
    Test that no-one has too many 'In Progress' issues assigned to them.

    :param report: The report to check.
    """
    violations = report.violations.get("too_much_wip", [])
    if violations:
        msg = f"{len(violations)} team members have more than 4 tickets In Progress:\n"
        for v in violations:
            assignee = v.details["assignee"]
            count = v.details["wip_count"]
            issue_keys = [issue["key"] for issue in v.details["issues"]]
            msg += f"- {assignee} has {count} tickets: {', '.join(issue_keys)}\n"
        pytest.fail(msg)


def test_noone_has_too_much_blocked(report):
    """
    Test that no-one has too many 'Blocked' issues assigned to them.

    :param report: The report to check.
    """
    violations = report.violations.get("too_much_blocked", [])
    if violations:
        msg = f"{len(violations)} team members have more than 2 tickets Blocked:\n"
        for v in violations:
            assignee = v.details["assignee"]
            count = v.details["blocked_count"]
            issue_keys = [issue["key"] for issue in v.details["issues"]]
            msg += f"- {assignee} has {count} tickets: {', '.join(issue_keys)}\n"
        pytest.fail(msg)


@pytest.mark.parametrize(
    "status",
    [
        "BACKLOG",
        "To Do",
        "BLOCKED",
        "In Progress",
        "Reviewing",
        "Merge Request",
        "READY FOR ACCEPTANCE",
    ],
)
def test_tickets_are_assigned_within_team(report, status):
    """
    Test that all tickets are assigned within the team.

    :param report: The report to check.
    :param status: The status to check.
    """
    violations = report.violations.get(f"misassigned_{status}", [])
    if violations:
        msg = f"{len(violations)} {status} issues are not assigned within the team:\n"
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary} (Assignee: {v.details['assignee']})\n"
        pytest.fail(msg)


def test_everyone_has_a_ticket_in_progress(report):
    """
    Test that everyone in the team has a ticket 'In Progress'.

    :param report: The report to check.
    """
    violations = report.violations.get("no_wip_for_member", [])
    if violations:
        msg = f"{len(violations)} team members don't have a ticket In Progress:\n"
        for v in violations:
            msg += f"- {v.details['member']}\n"
        pytest.fail(msg)
