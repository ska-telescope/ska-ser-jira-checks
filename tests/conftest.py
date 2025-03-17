"""Common pytest fixtures and test setup."""

import os
from datetime import date

import jira
import pytest


@pytest.fixture(name="unlinked_labels", scope="session")
def fixture_unlinked_labels() -> set:
    """
    Return a  set of labels that indicate that an issue is deliberately not linked.

    :return: a  set of lower-case string labels
        that indicate that an issue is deliberately not linked.
    """
    return {"innovation", "overhead", "team_backlog"}


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
