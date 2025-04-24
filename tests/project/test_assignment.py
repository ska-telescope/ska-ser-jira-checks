"""Test issue links."""

from typing import Any

import pytest

from tests.conftest import fail_if_data


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
    unassigned = []
    for issue in issues_by_status[status]:
        if issue.fields.assignee:
            continue
        unassigned.append({"Issue": issue.key, "Summary": issue.fields.summary})

    fail_if_data(
        unassigned,
        f"{{Issue}} ('{{Summary}}') is '{status}' and unassigned.",
        f"{{length}} '{status}' issues are unassigned:",
        sort_key="Issue",
    )


@pytest.mark.parametrize("max_wip", [4])
def test_noone_has_too_much_wip(in_progress_issues_by_assignee, max_wip):
    """
    Test that no-one has too many "In Progress" issues assigned to them.

    :param in_progress_issues_by_assignee: dictionary of "In Progress" issues,
        keyed by the assignee.
    :param max_wip: the maximum permitted number of In Progress issues.
    """
    overwip = []
    for assignee, issues in in_progress_issues_by_assignee.items():
        if len(issues) > max_wip:
            overwip.append(
                {
                    "Assignee": assignee,
                    "Issues": ", ".join([issue.key for issue in issues]),
                    "Count": len(issues),
                }
            )

    fail_if_data(
        overwip,
        "{Assignee} has {Count} tickets In Progress: {Issues}.",
        f"{{length}} team members have more than {max_wip} tickets In Progress:",
        sort_key="Assignee",
    )


@pytest.mark.parametrize("max_blocked", [2])
def test_noone_has_too_much_blocked(blocked_issues_by_assignee, max_blocked):
    """
    Test that no-one has too many "Blocked" issues assigned to them.

    :param blocked_issues_by_assignee: dictionary of "BLOCKED" issues,
        keyed by the assignee
    :param max_blocked: the maximum permitted number of BLOCKED issues.
    """
    blocked: list[dict[str, Any]] = []

    for assignee, issues in blocked_issues_by_assignee.items():
        if len(issues) > max_blocked:
            blocked.append(
                {
                    "Assignee": assignee,
                    "Issues": ", ".join([issue.key for issue in issues]),
                    "Count": len(issues),
                }
            )

    fail_if_data(
        blocked,
        "{Assignee} has {Count} tickets blocked: {Issues}.",
        f"{{length}} team members have more than {max_blocked} tickets Blocked:",
        sort_key="Assignee",
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
    misassigned: list[dict[str, Any]] = []

    for issue in issues_by_status[status]:
        if issue.fields.assignee and issue.fields.assignee.name not in team:
            misassigned.append(
                {
                    "Assignee": issue.fields.assignee.name,
                    "Issue": issue.key,
                    "Summary": issue.fields.summary,
                }
            )

    fail_if_data(
        misassigned,
        f"{{Issue}} ('{{Summary}}') is {status} and assigned to {{Assignee}}.",
        f"{{length}} {status} issues are not assigned within the team:",
        sort_key="Issue",
    )


def test_everyone_has_a_ticket_in_progress(in_progress_issues_by_assignee, team):
    """
    Test that everyone in the team has a ticket "In Progress".

    :param in_progress_issues_by_assignee: dictionary of "In Progress" issues,
        keyed by the assignee.
    :param team: set of team members
    """
    unassigned_members = team - set(in_progress_issues_by_assignee)
    unassigned_members = [{"Member": member} for member in unassigned_members]

    fail_if_data(
        unassigned_members,
        "{Member} doesn't have a ticket In Progress.",
        "{length} team members don't have a ticket In Progress:\n",
        sort_key="Issue",
    )
