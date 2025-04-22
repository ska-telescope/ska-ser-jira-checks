"""Test issue links."""

import functools
import json
from collections import defaultdict
from typing import Any

import pytest

from tests.conftest import UNLINKED_LABELS  # pylint: disable=import-error


@pytest.fixture(name="issue_parentage", scope="session")
def fixture_issue_parentage(issues, project):
    """
    Return a dictionary that lists the parents of each issue.

    :param issues: list of issues
    :param project: the project under consideration

    :return: a dictionary whose keys are issue keys,
        and whose values are lists of parent issue keys
    """
    parentage = defaultdict(list)

    for issue in issues:
        epic = issue.fields.customfield_10006
        if epic is not None and epic.startswith(f"{project}-"):
            parentage[issue.key].append(("EPIC", epic))

        for issuelink in issue.fields.issuelinks:
            link_type = issuelink.type.name

            if hasattr(issuelink, "outwardIssue"):
                parent = str(issuelink.outwardIssue)
                if link_type != "Relates" or not parent.startswith("SPO-"):
                    continue

            elif hasattr(issuelink, "inwardIssue"):
                parent = str(issuelink.inwardIssue)
                if link_type == "Parent/Child":
                    if not parent.startswith("SP-"):
                        continue
                elif link_type == "Relates":
                    if not parent.startswith("SPO-"):
                        continue
                else:
                    continue
            else:
                continue

            parentage[issue.key].append((issuelink.type.name, parent))

    return parentage


def test_no_issues_are_child_of_an_objective(issues, fail_if_data):
    """
    Test that no issues link to an objective with relationship "Child of".

    :param issues: list of issues.
    :param fail_if_data: utility function that constructs test failure output.
    """
    objective_children = []
    for issue in issues:
        for issuelink in issue.fields.issuelinks:
            if issuelink.type.name == "Parent/Child":
                if hasattr(issuelink, "inwardIssue"):
                    inward = str(issuelink.inwardIssue)
                    if inward.startswith("SPO-"):
                        objective_children.append(
                            {
                                "Issue": issue.key,
                                "Summary": issue.fields.summary,
                                "Objective": inward,
                            }
                        )

    fail_if_data(
        objective_children,
        "{Issue} ('{Summary}') is child of objective {Objective}.",
        "{length} issues are child of an objective:",
        sort_key="Issue",
    )


def test_no_issues_relate_to_a_feature(issues, fail_if_data):
    """
    Test that no issues link to a feature with relationship "Relates to".

    :param issues: list of issues.
    :param fail_if_data: utility function that constructs test failure output.
    """
    feature_relatives = []
    for issue in issues:
        for issuelink in issue.fields.issuelinks:
            if issuelink.type.name != "Relates":
                continue
            if hasattr(issuelink, "inwardIssue"):
                inward = str(issuelink.inwardIssue)
                if inward.startswith("SP-"):
                    feature_relatives.append(
                        {
                            "Issue": issue.key,
                            "Summary": issue.fields.summary,
                            "Feature": inward,
                        }
                    )
            elif hasattr(issuelink, "outwardIssue"):
                outward = str(issuelink.outwardIssue)
                if outward.startswith("SP-"):
                    feature_relatives.append(
                        {
                            "Issue": issue.key,
                            "Summary": issue.fields.summary,
                            "Feature": outward,
                        }
                    )

    fail_if_data(
        feature_relatives,
        "{Issue} ('{Summary}') relates to feature {Feature}.",
        "{length} issues relate to a feature:",
        sort_key="Issue",
    )


@pytest.mark.parametrize(
    "status",
    [
        "BACKLOG",  # TODO: Instead test that backlog issues aren't in this PI
        "To Do",
        "In Progress",
        "BLOCKED",
        "Reviewing",
        "Merge Request",
        "READY FOR ACCEPTANCE",
        "Done",
    ],
)
def test_issues_in_this_pi_are_linked(
    pi,
    issue_parentage,
    issues_by_status,
    status,
    fail_if_data,
):
    """
    Test that every issue is appropriately linked.

    Every issue should be either the "Child of" a feature,
    or "Relates to" an objective.

    Exceptions are made for tickets with one of the following labels:
    "TEAM_BACKLOG", "DEPENDENCY", "INNOVATION" or "OVERHEAD".

    :param pi: the current Program Increment number
    :param issue_parentage: dictionary specifying the parents of each issue
    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    :param fail_if_data: utility function that constructs test failure output.
    """
    current_pi = f"PI{pi}"
    unlinked_issues = []
    for issue in issues_by_status[status]:

        fix_versions = set(issue.name for issue in issue.fields.fixVersions)
        if current_pi not in fix_versions:
            continue
        lower_labels = set(label.lower() for label in issue.fields.labels)
        if lower_labels.intersection(UNLINKED_LABELS):
            continue

        if issue.key not in issue_parentage:
            unlinked_issues.append(
                {"Issue": issue.key, "Summary": issue.fields.summary}
            )

    fail_if_data(
        unlinked_issues,
        f"{{Issue}} ('{{Summary}}') is {status} and is not linked.",
        f"{{length}} {status} issues aren't linked:",
        sort_key="Issue",
    )


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
)  # pylint: disable-next=too-many-arguments, too-many-positional-arguments
def test_issues_in_this_pi_have_parent_in_this_pi(
    pi,
    session,
    issue_parentage,
    issues_by_status,
    status,
    fail_if_data,
):
    """
    Test that every issue is appropriately linked.

    Every issue should be either the "Child of" a feature,
    or "Relates to" an objective.

    Exceptions are made for tickets with one of the following labels:
    "TEAM_BACKLOG", "DEPENDENCY", "INNOVATION" or "OVERHEAD".

    :param pi: the current Program Increment number
    :param session: an active Jira session.
    :param issue_parentage: dictionary specifying the parents of each issue
    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    :param fail_if_data: utility function that constructs test failure output.
    """

    @functools.lru_cache
    def is_in_this_pi(issue_key):
        issue = session.issue(issue_key)
        fix_versions = set(issue.name for issue in issue.fields.fixVersions)
        return f"PI{pi}" in fix_versions

    current_pi = f"PI{pi}"
    mislinked_issues = []
    for issue in issues_by_status[status]:
        fix_versions = set(issue.name for issue in issue.fields.fixVersions)
        if current_pi not in fix_versions:
            continue
        lower_labels = set(label.lower() for label in issue.fields.labels)
        if lower_labels.intersection(UNLINKED_LABELS):
            continue
        if issue.key not in issue_parentage:
            continue
        for _, link_target in issue_parentage[issue.key]:
            if is_in_this_pi(link_target):
                break
        else:
            mislinked_issues.append(
                {"Issue": issue.key, "Summary": issue.fields.summary}
            )

    fail_if_data(
        mislinked_issues,
        (
            f"{{Issue}} ('{{Summary}}') is {status} "
            "and is not linked to a parent in the current PI."
        ),
        f"{{length}} {status} issues aren't linked to a parent in the current PI:",
        sort_key="Issue",
    )


@pytest.mark.parametrize(
    ("status", "consistent_parent_statuses"),
    [
        ("BACKLOG", ["BACKLOG"]),
        ("To Do", ["To Do", "In Progress", "Implementing", "BLOCKED", "Identified"]),
        ("In Progress", ["In Progress", "Implementing", "BLOCKED"]),
        ("BLOCKED", ["In Progress", "Implementing", "BLOCKED"]),
        ("Reviewing", ["In Progress", "Implementing", "BLOCKED"]),
        ("Merge Request", ["In Progress", "Implementing", "BLOCKED"]),
        (
            "READY FOR ACCEPTANCE",
            ["In Progress", "Implementing", "BLOCKED", "READY FOR ACCEPTANCE"],
        ),
        (
            "Done",
            [
                "In Progress",
                "Implementing",
                "BLOCKED",
                "READY FOR ACCEPTANCE",
                "Releasing",
                "Done",
                "Achieved",
                "NOT ACHIEVED",
                "Evaluated",
                "Discarded",
            ],
        ),
    ],
)  # pylint: disable-next=too-many-arguments, too-many-positional-arguments
def test_status_is_consistent_with_parent_status(
    session,
    issues_by_status,
    status,
    consistent_parent_statuses,
    issue_parentage,
    fail_if_data,
):
    """
    Test that issue status is consistent with the status of its parent issues.

    For example, it doesn't make sense for an issue to be "In Progress"
    if its parent issue is already "Done";
    so this test will fail if it encounters such a situation.

    :param session: an active Jira session.
    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    :param consistent_parent_statuses: list of parent statuses consistent
        with the current issue status.
    :param issue_parentage: dictionary specifying the parents of each issue
    :param fail_if_data: utility function that constructs test failure output.
    """

    @functools.lru_cache
    def issue_status(issue_key):
        issue = session.issue(issue_key)
        return issue.fields.status.name

    inconsistent_issues: list[dict[str, Any]] = []
    for issue in issues_by_status[status]:
        if issue.key not in issue_parentage:
            continue

        inconsistent_parents: list[str] = []
        for _, parent_key in issue_parentage[issue.key]:
            if issue_status(parent_key) not in consistent_parent_statuses:
                inconsistent_parents.append(parent_key)
        if inconsistent_parents:
            inconsistent_issues.append(
                {
                    "Issue": issue.key,
                    "Summary": issue.fields.summary,
                    "Parents": ", ".join(inconsistent_parents),
                }
            )

    fail_if_data(
        inconsistent_issues,
        "{Issue} ('{Summary}') has inconsistent parent/s {Parents}.",
        "{length} issues have inconsistent parent status:",
        sort_key="Issue",
    )


@pytest.mark.parametrize("status", ["To Do", "BACKLOG"])
def test_no_todo_or_backlog_issue_with_commits(issues_by_status, status, fail_if_data):
    """
    Test that no 'To Do' or 'Backlog' issues have commits.

    If an issue has commits, work has already started on it,
    so it probably shouldn't be 'To Do' or 'Backlog'.

    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    :param fail_if_data: utility function that constructs test failure output.
    """
    issues_with_commits: list[dict[str, Any]] = []

    for issue in issues_by_status[status]:
        raw_dev_field = issue.fields.customfield_13300

        index = raw_dev_field.find("devSummaryJson=")
        json_bit = raw_dev_field[index + len("devSummaryJson=") : -1]
        dev_field = json.loads(json_bit)

        if dev_field["cachedValue"]["summary"]["repository"]["overall"]["count"]:
            assignee = (
                issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            )
            issues_with_commits.append(
                {
                    "Issue": issue.key,
                    "Summary": issue.fields.summary,
                    "Assignee": assignee,
                }
            )

    fail_if_data(
        issues_with_commits,
        (
            "{Issue} ('{Summary}'), assigned to {Assignee}, "
            f"is {status} but has commits."
        ),
        f"{{length}} {status} issues have commits:",
        sort_key="Issue",
    )
