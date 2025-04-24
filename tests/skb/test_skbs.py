"""Pytest fixtures and test setup for SKB-specific tests."""

import datetime
import functools
from typing import Any

import pytest

from tests.conftest import UNLINKED_LABELS, fail_if_data


@pytest.mark.parametrize(
    ("status", "age_limit"),
    [
        ("Identified", 7),
        ("Assessment", 7),
        ("Assigned", 14),
        ("In Progress", 30),
        ("BLOCKED", 7),
        ("Verifying", 2),
        ("Validating", 2),
    ],
)
def test_skb_not_too_old(skbs_by_status, status, age_limit):
    """
    Test that every SKB has been updated reasonably recently.

    :param skbs_by_status: dictionary of SKB issues, keyed by their status.
    :param status: the issue status under consideration.
    :param age_limit: the maximum permitted number of days
        since an issue has been updated.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    deadline = now - datetime.timedelta(days=age_limit)

    old_issues: list[dict[str, Any]] = []
    for issue in skbs_by_status[status]:
        updated = datetime.datetime.strptime(
            issue.fields.updated, "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        if updated < deadline:
            age = (now - updated).days
            assignee = (
                issue.fields.assignee.name
                if issue.fields.assignee
                else issue.fields.creator.name
            )
            old_issues.append(
                {
                    "Issue": issue.key,
                    "Summary": issue.fields.summary,
                    "Assignee": assignee,
                    "Age": age,
                }
            )

    fail_if_data(
        old_issues,
        (
            f"{{Issue}} ('{{Summary}}'), assigned to {{Assignee}}, "
            f"is {status} and has not been updated for {{Age}} days)."
        ),
        (
            f"{{length}} {status} SKBs have not been updated "
            f"for more than {age_limit} days:"
        ),
        sort_key="Age",
        reverse=True,
    )


@pytest.mark.parametrize(
    "status",
    [
        "Identified",
        "Assessment",
        "Assigned",
        "In Progress",
        "BLOCKED",
        "Verifying",
        "Validating",
    ],
)
def test_that_skbs_are_child_of_a_feature_or_relate_to_an_objective_in_this_pi(
    pi, session, skbs_by_status, status
):
    """
    Test that SKBs are child of a feature or relate to an objective.

    :param pi: the current Program Increment number
    :param session: an active Jira session.
    :param skbs_by_status: dictionary of SKB issues, keyed by their status.
    :param status: the issue status under consideration.
    """

    @functools.lru_cache
    def is_in_this_pi(issue_key):
        issue = session.issue(issue_key)
        fix_versions = set(issue.name for issue in issue.fields.fixVersions)
        return f"PI{pi}" in fix_versions

    unlinked_issues: list[dict[str, Any]] = []
    for issue in skbs_by_status[status]:
        lower_labels = set(label.lower() for label in issue.fields.labels)
        if lower_labels.intersection(UNLINKED_LABELS):
            continue

        for issuelink in issue.fields.issuelinks:
            if (
                issuelink.type.name == "Parent/Child"
                and hasattr(issuelink, "inwardIssue")
                and str(issuelink.inwardIssue).startswith("SP-")
                and is_in_this_pi(str(issuelink.inwardIssue))
            ):
                break

            if issuelink.type.name == "Relates":
                if (
                    hasattr(issuelink, "inwardIssue")
                    and str(issuelink.inwardIssue).startswith("SPO-")
                    and is_in_this_pi(str(issuelink.inwardIssue))
                ):
                    break
                if (
                    hasattr(issuelink, "outwardIssue")
                    and str(issuelink.outwardIssue).startswith("SPO-")
                    and is_in_this_pi(str(issuelink.outwardIssue))
                ):
                    break
        else:
            assignee = (
                issue.fields.assignee.name
                if issue.fields.assignee
                else issue.fields.creator.name
            )
            unlinked_issues.append(
                {
                    "Issue": issue.key,
                    "Summary": issue.fields.summary,
                    "Assignee": assignee,
                }
            )

    fail_if_data(
        unlinked_issues,
        (
            "{Issue} ('{Summary}'), assigned to {Assignee}, "
            "is not linked to a feature or objective in the current PI."
        ),
        (
            f"{{length}} {status} SKBs aren't linked "
            "to a feature or objective in the current PI:"
        ),
        sort_key="Issue",
    )
