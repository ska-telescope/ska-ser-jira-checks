"""Pytest fixtures and test setup for SKB-specific tests."""

import pytest

SKB_STATUSES = [
    "Identified",
    "Assessment",
    "Assigned",
    "In Progress",
    "BLOCKED",
    "Verifying",
    "Validating",
    "Done",
    "Discarded",
]


@pytest.fixture(scope="session", name="skbs")
def fixture_skbs(session, start_date):
    """
    Return a list of issues in the SKB project, created since the start date.

    :param session: an active Jira session.
    :param start_date: the earliest creation date for which issues will be considered.

    :return: a list of issues in the SKB project, created since the state date.
    """
    search_string = "project = SKB"
    if start_date:
        search_string += f" AND createdDate > {start_date}"

    issues = []
    i = 0
    chunk_size = 100
    while True:
        chunk = session.search_issues(search_string, startAt=i, maxResults=chunk_size)
        i += chunk_size
        issues += chunk.iterable
        if i >= chunk.total:
            break

    return issues


@pytest.fixture(scope="session", name="team_created_skbs_by_status")
def fixture_team_created_skbs_by_status(skbs, team):
    """
    Return a dictionary of team-created SKB issues, keyed by status.

    :param skbs: list of SKBs
    :param team: set of team member usernames

    :return: a dictionary of team-created SKBs, keyed by status.
    """
    by_status = {status: [] for status in SKB_STATUSES}

    for skb in skbs:
        if skb.fields.creator.name in team:
            by_status[skb.fields.status.name].append(skb)

    return by_status


@pytest.fixture(scope="session", name="team_assigned_skbs_by_status")
def fixture_team_assigned_skbs_by_status(skbs, team):
    """
    Return a dictionary of team-assigned SKB issues, keyed by status.

    :param skbs: list of SKBs
    :param team: set of team member usernames

    :return: a dictionary of team-assigned SKBs, keyed by status.
    """
    by_status = {status: [] for status in SKB_STATUSES}

    for skb in skbs:
        if not skb.fields.assignee:
            continue
        if skb.fields.assignee.name in team:
            by_status[skb.fields.status.name].append(skb)

    return by_status
