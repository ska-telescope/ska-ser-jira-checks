"""Utility functions for checks."""

import json
from collections import defaultdict
from typing import Any, Dict, List


def get_issues_by_status(issues: List[Any]) -> Dict[str, List[Any]]:
    """
    Group issues by status.

    :param issues: The list of Jira issues.

    :return: A dictionary of issues keyed by status.
    """
    issues_by_status = defaultdict(list)
    for issue in issues:
        status = issue.fields.status.name
        issues_by_status[status].append(issue)
    return dict(issues_by_status)


def get_dev_field(issue: Any) -> Dict[str, Any]:
    """
    Extract the development field JSON from a Jira issue.

    :param issue: The Jira issue.

    :return: The development field JSON as a dictionary.
    """
    raw_dev_field = issue.fields.customfield_13300
    if not raw_dev_field:
        return {}

    index = raw_dev_field.find("devSummaryJson=")
    if index == -1:
        return {}

    json_bit = raw_dev_field[index + len("devSummaryJson=") : -1]
    return json.loads(json_bit)


def get_fix_versions(issue: Any) -> set[str]:
    """
    Extract the fix versions from a Jira issue.

    :param issue: The Jira issue.

    :return: A set of fix version names.
    """
    return {version.name for version in issue.fields.fixVersions}


def get_assignee(issue: Any) -> str:
    """
    Get the assignee name or "UNASSIGNED".

    :param issue: The Jira issue.

    :return: The assignee name or "UNASSIGNED".
    """
    return (
        issue.fields.assignee.name
        if issue.fields.assignee
        else (
            issue.fields.creator.name
            if hasattr(issue.fields, "creator")
            else "UNASSIGNED"
        )
    )
