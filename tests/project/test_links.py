"""Test issue links."""

import functools
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
        "Done",
    ],
)  # pylint: disable-next=too-many-locals,
def test_issues_in_this_pi_link_to_feature_or_objective_in_this_pi(
    pi, session, unlinked_labels, issues_by_status, status
):
    """
    Test that every issue is appropriately linked.

    Every issue should be either the "Child of" a feature,
    or "Relates to" an objective.

    Exceptions are made for tickets with one of the following labels:
    "TEAM_BACKLOG", "INNOVATION" or "OVERHEAD".

    :param pi: the current Program Increment number
    :param session: an active Jira session.
    :param unlinked_labels: set of lower-case labels
        that indicate that an issue is deliberately not linked
        to a feature or objective, and therefore should be ignored by this test.
    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """

    @functools.lru_cache
    def is_in_this_pi(issue_key):
        issue = session.issue(issue_key)
        fix_versions = set(issue.name for issue in issue.fields.fixVersions)
        return f"PI{pi}" in fix_versions

    current_pi = f"PI{pi}"
    count = 0
    unlinked_issues = defaultdict(list)
    for issue in issues_by_status[status]:
        fix_versions = set(issue.name for issue in issue.fields.fixVersions)
        if current_pi not in fix_versions:
            continue
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
            assignee = (
                issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            )
            unlinked_issues[assignee].append(issue.key)
            count += 1

    if len(unlinked_issues) > 1:
        pytest.fail(
            f"{count} '{status}' issues aren't linked "
            "to a feature or objective in the current PI:\n"
            f"{pprint.pformat(dict(unlinked_issues))}"
        )
    elif len(unlinked_issues) == 1:
        assignee, issues = unlinked_issues.popitem()
        if len(issues) == 1:
            pytest.fail(
                f"{assignee}: {issues[0]} is '{status}' and is not linked "
                "to a feature or objective in the current PI."
            )
        else:
            pytest.fail(
                f"{assignee}: {len(issues)} issues are '{status}' and not linked "
                "to a feature or objective in the current PI:\n"
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
