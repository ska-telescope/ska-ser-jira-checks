"""Test issue links."""

import pprint
from collections import defaultdict

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
def test_tickets_have_assignee(issues_by_status, status):
    """
    Test that all tickets of certain statuses are assigned to someone.

    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    unassigned = [
        issue.key for issue in issues_by_status[status] if not issue.fields.assignee
    ]

    if len(unassigned) > 1:
        pytest.fail(
            f"{len(unassigned)} '{status}' issues are unassigned:\n{unassigned}"
        )
    elif len(unassigned) == 1:
        pytest.fail(f"{unassigned[0]} is '{status}' and unassigned:\n{unassigned}")


@pytest.mark.parametrize("max_wip", [4])
def test_noone_has_too_much_wip(in_progress_issues_by_assignee, max_wip):
    """
    Test that no-one has too many "In Progress" issues assigned to them.

    :param in_progress_issues_by_assignee: dictionary of "In Progress" issues,
        keyed by the assignee.
    :param max_wip: the maximum permitted number of In Progress issues.
    """
    overwip = {}
    for member, issues in in_progress_issues_by_assignee.items():
        if len(issues) > max_wip:
            overwip[member] = [issue.key for issue in issues]
    if len(overwip) > 1:
        pytest.fail(
            f"{len(overwip)} team members have more than "
            f"{max_wip} tickets In Progress:\n"
            f"{pprint.pformat(overwip)}"
        )
    elif len(overwip) == 1:
        member, issues = overwip.popitem()
        pytest.fail(
            f"{member} has {len(issues)} tickets In Progress:\n{pprint.pformat(issues)}"
        )


@pytest.mark.parametrize("max_blocked", [2])
def test_noone_has_too_much_blocked(blocked_issues_by_assignee, max_blocked):
    """
    Test that no-one has too many "Blocked" issues assigned to them.

    :param blocked_issues_by_assignee: dictionary of "BLOCKED" issues,
        keyed by the assignee
    :param max_blocked: the maximum permitted number of BLOCKED issues.
    """
    blocked = {}
    for member, issues in blocked_issues_by_assignee.items():
        if len(issues) > 1:
            blocked[member] = [issue.key for issue in issues]
    if len(blocked) > max_blocked:
        pytest.fail(
            f"{len(blocked)} team members have more than "
            f"{max_blocked} tickets BLOCKED:\n"
            f"{pprint.pformat(blocked)}"
        )
    elif len(blocked) == 1:
        member, issues = blocked.popitem()
        pytest.fail(
            f"{member} has {len(issues)} tickets BLOCKED:\n{pprint.pformat(issues)}"
        )


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
def test_tickets_are_assigned_within_team(team, issues_by_status, status):
    """
    Test that all tickets are assigned within the team.

    :param team: set of team members usernames
    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    misassigned = defaultdict(list)
    count = 0

    for issue in issues_by_status[status]:
        if issue.fields.assignee and issue.fields.assignee.name not in team:
            misassigned[issue.fields.assignee.name].append(issue.key)
            count += 1

    if count > 1:
        pytest.fail(
            f"{count} '{status}' issues are not assigned within the team:\n"
            f"{pprint.pformat(dict(misassigned))}"
        )
    elif count == 1:
        assignee, issue = misassigned.popitem()
        pytest.fail(f"{issue} is '{status}' and assigned to {assignee}.")


def test_everyone_has_a_ticket_in_progress(in_progress_issues_by_assignee, team):
    """
    Test that everyone in the team has a ticket "In Progress".

    :param in_progress_issues_by_assignee: dictionary of "In Progress" issues,
        keyed by the assignee.
    :param team: set of team members
    """
    unassigned_members = team - set(in_progress_issues_by_assignee)
    if len(unassigned_members) > 1:
        pytest.fail(
            f"{len(unassigned_members)} team members don't have a ticket In Progress:\n"
            f"{pprint.pformat(unassigned_members)}"
        )
    elif len(unassigned_members) == 1:
        pytest.fail(f"{unassigned_members.pop()} doesn't have a ticket In Progress.")
