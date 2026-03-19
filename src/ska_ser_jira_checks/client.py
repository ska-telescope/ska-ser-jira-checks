"""Jira client wrapper."""

import os

import jira


class JiraClient:
    """A wrapper around the Jira library for common operations."""

    def __init__(self, url: str = "https://jira.skatelescope.org"):
        """Initialize the Jira client.

        :param url: The URL of the Jira instance.
        """
        self.url = url
        self.session = self._create_session()

    def _create_session(self) -> jira.JIRA:
        """
        Create a Jira session from environment variables.

        :return: A Jira session object.

        :raises ValueError: if Jira auth environment variables are not available.
        """
        token = os.environ.get("JIRA_API_TOKEN")
        if token:
            headers = jira.JIRA.DEFAULT_OPTIONS["headers"].copy()
            headers["Authorization"] = f"Bearer {token}"
            return jira.JIRA(self.url, options={"headers": headers})

        username = os.environ.get("JIRA_USERNAME")
        password = os.environ.get("JIRA_PASSWORD")
        if username and password:
            return jira.JIRA(self.url, basic_auth=(username, password))

        raise ValueError(
            "Jira credentials not supplied: "
            "set either JIRA_API_TOKEN environment variable, "
            "or both JIRA_USERNAME and JIRA_PASSWORD environment variables."
        )

    def search_issues(self, jql: str, chunk_size: int = 100) -> list[jira.Issue]:
        """
        Search for issues using JQL and handle pagination.

        :param jql: JQL search string.
        :param chunk_size: Number of issues to fetch per request.

        :return: A list of Jira issues.
        """
        issues = []
        i = 0
        while True:
            chunk = self.session.search_issues(jql, startAt=i, maxResults=chunk_size)
            i += chunk_size
            issues.extend(chunk.iterable)
            if i >= chunk.total:
                break
        return issues

    def get_issue(self, issue_key: str) -> jira.Issue:
        """
        Get a single issue by key.

        :param issue_key: The issue key (e.g., 'SP-123').

        :return: The Jira issue.
        """
        return self.session.issue(issue_key)

    def get_team_members(self, project: str) -> set[str]:
        """
        Get the set of team members (Developers) for a project.

        :param project: the project name.

        :return: the set of team member usernames.
        """
        roles = self.session.project_roles(project=project)
        developer_id = roles["Developers"]["id"]
        team_members = self.session.project_role(
            project=project, id=developer_id
        ).actors
        return {member.name for member in team_members}
