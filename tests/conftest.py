"""Common pytest fixtures and test setup."""

import os
from collections import defaultdict
from datetime import date

import jira
import pytest


@pytest.fixture(scope="session", name="pi")
def fixture_pi():
    """
    Return the number of the current PI.

    :return: the number of the current PI.
    """
    delta = date.today() - date(2018, 9, 19)
    pi = delta.days // 91
    return pi


@pytest.fixture(scope="session", name="start_date")
def fixture_start_date():
    """
    Return the start date for issues to be considered.

    :return: the start date for issues to be considered,
        or None to include all issues in the history of the project.
    """
    return os.environ.get("JIRA_START_DATE")


@pytest.fixture(scope="session", name="project")
def fixture_project():
    """
    Return the name of the project.

    :return: the name of the project.
    """
    return os.environ["JIRA_PROJECT"]


@pytest.fixture(scope="session", name="session")
def fixture_session():
    """
    Return an active Jira session.

    :return: an active Jira session.

    :raises ValueError: if Jira auth environment variables are not available.
    """
    token = os.environ.get("JIRA_API_TOKEN")
    if token:
        headers = jira.JIRA.DEFAULT_OPTIONS["headers"].copy()
        headers["Authorization"] = f"Bearer {token}"
        return jira.JIRA("https://jira.skatelescope.org", options={"headers": headers})

    username = os.environ.get("JIRA_USERNAME")
    password = os.environ.get("JIRA_PASSWORD")
    if username and password:
        return jira.JIRA(
            "https://jira.skatelescope.org",
            basic_auth=(username, password),
        )

    raise ValueError(
        "Jira credentials not supplied: "
        "set either JIRA_AUTH environment variable, "
        "or both JIRA_USERNAME and JIRA_PASSWORD environment variables."
    )


@pytest.fixture(scope="session", name="team")
def fixture_team(session, project):
    """
    Return the set of team members.

    :param session: an active Jira session.
    :param project: the project under consideration.

    :return: the set of team members.
    """
    try:
        roles = session.project_roles(project=project)
        developer_id = roles["Developers"]["id"]
        team_members = session.project_role(project=project, id=developer_id).actors
        return {member.name for member in team_members}
    except jira.exceptions.JIRAError:
        pytest.skip(
            reason="You don't have permission to read membership of this project."
        )
        return None


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
