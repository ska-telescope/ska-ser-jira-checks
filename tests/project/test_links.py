"""Test issue links."""

import json
import pprint
from collections import defaultdict

import pytest


@pytest.mark.parametrize(
    "status",
    [
        "To Do",
        "In Progress",
        "BLOCKED",
        "Reviewing",
        "Merge Request",
        "READY FOR ACCEPTANCE",
    ],
)
def test_issues_are_child_of_a_feature_or_relate_to_an_objective(
    issues_by_status, status
):
    """
    Test that every issue is appropriately linked.

    Every issue should be either the "Child of" a feature,
    or "Relates to" an objective.

    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    count = 0
    unlinked_issues = defaultdict(list)
    for issue in issues_by_status[status]:
        for issuelink in issue.fields.issuelinks:
            if (
                issuelink.type.name == "Parent/Child"
                and hasattr(issuelink, "inwardIssue")
                and str(issuelink.inwardIssue).startswith("SP-")
            ):
                break

            if issuelink.type.name == "Relates":
                if hasattr(issuelink, "inwardIssue") and str(
                    issuelink.inwardIssue
                ).startswith("SPO-"):
                    break
                if hasattr(issuelink, "outwardIssue") and str(
                    issuelink.outwardIssue
                ).startswith("SPO-"):
                    break
        else:
            assignee = (
                issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            )
            unlinked_issues[assignee].append(issue.key)
            count += 1

    if len(unlinked_issues) > 1:
        pytest.fail(
            f"{count} '{status}' issues aren't linked:\n"
            f"{pprint.pformat(dict(unlinked_issues))}"
        )
    elif len(unlinked_issues) == 1:
        assignee, issues = unlinked_issues.popitem()
        if len(issues) == 1:
            pytest.fail(f"{assignee}: {issues[0]} is '{status}' and is not linked.")
        else:
            pytest.fail(
                f"{assignee}: {len(issues)} issues are '{status}' and not linked:\n"
                f"{pprint.pformat(issues)}."
            )


def test_no_issues_are_child_of_an_objective(issues):
    """
    Test that no issues link to an objective with relationship "Child of".

    :param issues: list of issues.
    """
    objective_children = []
    for issue in issues:
        print(issue.key)
        for issuelink in issue.fields.issuelinks:
            if issuelink.type.name == "Parent/Child":
                if hasattr(issuelink, "inwardIssue"):
                    inward = str(issuelink.inwardIssue)
                    if inward.startswith("SPO-"):
                        objective_children.append(inward)

    if len(objective_children) > 1:
        pytest.fail(
            f"{len(objective_children)} issues are child of an objective:\n"
            f"{objective_children}"
        )
    elif len(objective_children) == 1:
        pytest.fail(f"{objective_children[0]} issues are child of an objective.")


def test_no_issues_relate_to_a_feature(issues):
    """
    Test that no issues link to a feature with relationship "Relates to".

    :param issues: list of issues.
    """
    feature_relatives = []
    for issue in issues:
        for issuelink in issue.fields.issuelinks:
            if issuelink.type.name == "Relates":
                if hasattr(issuelink, "inwardIssue"):
                    inward = str(issuelink.inwardIssue)
                    if inward.startswith("SP-"):
                        feature_relatives.append(issue.key)
                elif hasattr(issuelink, "outwardIssue"):
                    outward = str(issuelink.outwardIssue)
                    if outward.startswith("SP-"):
                        feature_relatives.append(issue.key)

    if len(feature_relatives) > 1:
        pytest.fail(
            f"{len(feature_relatives)} issues relate to a feature:\n"
            f"{feature_relatives}"
        )
    elif len(feature_relatives) == 1:
        pytest.fail(f"{feature_relatives[0]} relates to a feature.")


@pytest.mark.parametrize("status", ["To Do", "BACKLOG"])
def test_no_todo_or_backlog_issue_with_commits(issues_by_status, status):
    """
    Test that no 'To Do' or 'Backlog' issues have commits.

    If an issue has commits, work has already started on it,
    so it probably shouldn't be 'To Do' or 'Backlog'.

    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    issues_with_commits = defaultdict(list)
    count = 0

    for issue in issues_by_status[status]:
        raw_dev_field = issue.fields.customfield_13300

        index = raw_dev_field.find("devSummaryJson=")
        json_bit = raw_dev_field[index + len("devSummaryJson=") : -1]
        dev_field = json.loads(json_bit)

        if dev_field["cachedValue"]["summary"]["repository"]["overall"]["count"]:
            name = issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            issues_with_commits[name].append(issue.key)
            count += 1

    if len(issues_with_commits) > 1:
        pytest.fail(
            f"{count} '{status}' issues have commits:\n"
            f"{pprint.pformat(dict(issues_with_commits))}"
        )
    elif len(issues_with_commits) == 1:
        assignee, issues = issues_with_commits.popitem()
        if len(issues) == 1:
            pytest.fail(f"{assignee}: {issues[0]} is '{status}' but has commits.")
        else:
            pytest.fail(
                f"{assignee} has {count} '{status}' issues with commits:\n"
                f"{pprint.pformat(issues)}"
            )
