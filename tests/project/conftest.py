"""Pytest fixtures and test setup for project-specific tests."""

from collections import defaultdict

import pytest


@pytest.fixture(scope="session", name="statuses")
def fixture_statuses():
    """
    Return a list of valid issue statuses.

    :return: a list of valid issue statuses.
    """
    return [
        "BACKLOG",
        "BLOCKED",
        "Discarded",
        "Done",
        "In Progress",
        "READY FOR ACCEPTANCE",
        "Reviewing",  # JANUS and THORN
        "Merge Request",  # WOMBAT
        "To Do",
    ]


@pytest.fixture(scope="session", name="issues")
def fixture_issues(session, project, start_date):
    """
    Return a list of issues in the specified project, created since the start date.

    :param session: an active Jira session.
    :param project: the project under consideration.
    :param start_date: the earliest creation date for which issues will be considered.

    :return: a list of issues in the specified project, created since the state date.
    """
    search_string = f"project = {project}"
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


@pytest.fixture(scope="session", name="issues_by_status")
def fixture_issues_by_status(issues, statuses):
    """
    Return a dictionary of issues, keyed by status.

    :param issues: list of all issues under consideration
    :param statuses: list of issue statuses.

    :return: a dictionary of issues, keyed by status.
    """
    by_status = {}
    for status in statuses:
        by_status[status] = []

    for issue in issues:
        by_status[issue.fields.status.name].append(issue)

    return by_status


@pytest.fixture(scope="session", name="rfa_issues")
def fixture_rfa_issues(issues_by_status):
    """
    Return a list of "READY FOR ACCEPTANCE" issues.

    :param issues_by_status: dictionary of issues, keyed by their status.

    :return: a list of "READY FOR ACCEPTANCE" issues.
    """
    return issues_by_status["READY FOR ACCEPTANCE"]


@pytest.fixture(scope="session", name="in_progress_issues_by_assignee")
def fixture_in_progress_issues_by_assignee(issues_by_status):
    """
    Return a dictionary of "In Progress" issues, keyed by the assignee.

    :param issues_by_status: dictionary of issues, keyed by their status.

    :return: a dictionary of "In Progress" issues, keyed by assignee.
    """
    by_assignee = defaultdict(list)
    for issue in issues_by_status["In Progress"]:
        if issue.fields.assignee:
            by_assignee[issue.fields.assignee.name].append(issue)
    return by_assignee


@pytest.fixture(scope="session", name="blocked_issues_by_assignee")
def fixture_blocked_issues_by_assignee(issues_by_status):
    """
    Return a dictionary of "BLOCKED" issues, keyed by the assignee.

    :param issues_by_status: dictionary of issues, keyed by their status.

    :return: a dictionary of "BLOCKED" issues, keyed by assignee.
    """
    by_assignee = defaultdict(list)
    for issue in issues_by_status["BLOCKED"]:
        if issue.fields.assignee:
            by_assignee[issue.fields.assignee.name].append(issue)
    return by_assignee
