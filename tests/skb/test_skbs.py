"""Pytest fixtures and test setup for SKB-specific tests."""

import datetime
import functools
import pprint
from collections import defaultdict

import pytest


@pytest.mark.parametrize(
    ("status", "age"),
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
def test_skb_not_too_old(skbs_by_status, status, age):
    """
    Test that every SKB has been updated reasonably recently.

    :param skbs_by_status: dictionary of SKB issues, keyed by their status.
    :param status: the issue status under consideration.
    :param age: the maximum permitted number of days since an issue has been updated.
    """
    deadline = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=age
    )

    old_issues = defaultdict(list)
    count = 0
    for issue in skbs_by_status[status]:
        updated = datetime.datetime.strptime(
            issue.fields.updated, "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        if updated < deadline:
            key = (
                issue.fields.assignee.name
                if issue.fields.assignee
                else issue.fields.creator.name
            )
            old_issues[key].append((issue.key, str(updated.date())))
            count += 1

    if len(old_issues) > 1:
        pytest.fail(
            f"{count} '{status}' SKBs have not been updated "
            f"for more than {age} days:\n{pprint.pformat(dict(old_issues))}"
        )
    elif len(old_issues) == 1:
        (name, issues) = old_issues.popitem()
        if len(issues) == 1:
            (issue, updated) = issues[0]
            pytest.fail(
                f"{name}: {issue} is '{status}' and has not been updated "
                f"since {updated} (more than {age} days)."
            )
        else:
            pytest.fail(
                f"{name}: {len(issues)} are '{status}' and have not been updated "
                f"for more than {age} days:\n"
                f"{pprint.pformat(issues)}"
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
    pi, session, skbs_by_status, status, unlinked_labels
):
    """
    Test that SKBs are child of a feature or relate to an objective.

    :param pi: the current Program Increment number
    :param session: an active Jira session.
    :param skbs_by_status: dictionary of SKB issues, keyed by their status.
    :param status: the issue status under consideration.
    :param unlinked_labels: set of lower-case labels
        that indicate that an issue is deliberately not linked
        to a feature or objective, and therefore should be ignored by this test.
    """

    @functools.lru_cache
    def is_in_this_pi(issue_key):
        issue = session.issue(issue_key)
        fix_versions = set(issue.name for issue in issue.fields.fixVersions)
        return f"PI{pi}" in fix_versions

    unlinked_issues = defaultdict(list)
    count = 0
    for issue in skbs_by_status[status]:
        lower_labels = set(label.lower() for label in issue.fields.labels)
        if lower_labels.intersection(unlinked_labels):
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
            key = (
                issue.fields.assignee.name
                if issue.fields.assignee
                else issue.fields.creator.name
            )
            unlinked_issues[key].append(issue.key)
            count += 1

    if len(unlinked_issues) > 1:
        pytest.fail(
            f"{count} '{status}' SKBs aren't linked to a feature or objective "
            "in the current PI:\n"
            f"{pprint.pformat(dict(unlinked_issues))}"
        )
    elif len(unlinked_issues) == 1:
        (name, issues) = unlinked_issues.popitem()
        if len(issues) == 1:
            pytest.fail(
                f"{name}: {issues[0]} is not linked to a feature or objective "
                "in the current PI."
            )
        else:
            pytest.fail(
                f"{name}: {len(issues)} are not linked to a feature or objective "
                "in the current PI:\n"
                f"{pprint.pformat(issues)}"
            )
