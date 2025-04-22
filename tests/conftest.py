"""Common pytest fixtures and test setup."""

import os
from datetime import date
from operator import itemgetter
from typing import Any

import jira
import pytest
from tabulate import tabulate

UNLINKED_LABELS = {"innovation", "overhead", "team_backlog", "dependency"}


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


@pytest.fixture(scope="session", name="fail_if_data")
def fixture_fail_if_data():
    """
    Return a utility function that prepares output for test failure.

    :return: a utility function
    """

    def fail_if_data(
        data: list[dict[str, Any]],
        one_template: str,
        many_template: str,
        sort_key: str | None = None,
        reverse: bool = False,
    ) -> None:
        """
        Fail with a well-formatted message if the provided data is non-empty.

        :param data: a list of dictionaries providing
            information about failure cases.
        :param one_template: a string template specifying
            how to report the failure if there is only one failure case.
            In this case, we want to present all the information we can
            on a single line. The template will be templated against
            the content of that one failure case.
        :param many_template: a string template specifying
            how to report the failure if there are multiple failure cases.
            The only argument available for templating this is "length",
            which is the number of failure cases.
            This string will be printed,
            followed by a table describing each failure case.
        :param sort_key: the key to sort the table by;
            if omitted, the table order will reflect the list provided.
        :param reverse: whether the reverse the sort order; default to False
        """
        if len(data) == 1:
            pytest.fail(one_template.format(**data[0]))
        elif len(data) > 1:
            if sort_key is not None:
                data = sorted(data, key=itemgetter(sort_key), reverse=reverse)
            pytest.fail(
                many_template.format(length=len(data))
                + "\n\n"
                + tabulate(data, headers="keys", maxcolwidths=100)
            )

    return fail_if_data
