"""Pytest fixtures and test setup for SKB-specific tests."""

import pytest


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


@pytest.fixture(scope="session", name="team_skbs")
def fixture_team_skbs(skbs, team):
    """
    Return a list of issues in the SKB project, assigned to or created by team members.

    :param skbs: list of SKBs
    :param team: set of team member usernames

    :return: a list of issues in the SKB project,
        assigned to or created by team members.
    """
    team_skbs = []
    for skb in skbs:
        if skb.fields.assignee:
            if skb.fields.assignee.name in team:
                team_skbs.append(skb)
        elif skb.fields.creator.name in team:
            team.skbs.append(skb)
    return team_skbs


@pytest.fixture(scope="session", name="skb_statuses")
def fixture_skb_statuses():
    """
    Return a list of valid SKB statuses.

    :return: a list of valid SKB statuses.
    """
    return [
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


@pytest.fixture(scope="session", name="skbs_by_status")
def fixture_skbs_by_status(team_skbs, skb_statuses):
    """
    Return a dictionary of team SKB issues, keyed by status.

    :param team_skbs: list of all team SKBs
    :param skb_statuses: list of SKB statuses

    :return: a dictionary of team SKBs, keyed by status.
    """
    by_status = {status: [] for status in skb_statuses}

    for skb in team_skbs:
        by_status[skb.fields.status.name].append(skb)

    return by_status
