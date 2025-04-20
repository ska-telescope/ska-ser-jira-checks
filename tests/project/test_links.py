"""Test issue links."""

import functools
import json
import pprint
from collections import defaultdict

import pytest


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


def test_no_issues_are_child_of_an_objective(issues):
    """
    Test that no issues link to an objective with relationship "Child of".

    :param issues: list of issues.
    """
    objective_children = []
    for issue in issues:
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
    pi, unlinked_labels, issue_parentage, issues_by_status, status
):
    """
    Test that every issue is appropriately linked.

    Every issue should be either the "Child of" a feature,
    or "Relates to" an objective.

    Exceptions are made for tickets with one of the following labels:
    "TEAM_BACKLOG", "DEPENDENCY", "INNOVATION" or "OVERHEAD".

    :param pi: the current Program Increment number
    :param unlinked_labels: set of lower-case labels
        that indicate that an issue is deliberately not linked
        to a feature or objective, and therefore should be ignored by this test.
    :param issue_parentage: dictionary specifying the parents of each issue
    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    current_pi = f"PI{pi}"
    unlinked_issues = []
    for issue in issues_by_status[status]:

        fix_versions = set(issue.name for issue in issue.fields.fixVersions)
        if current_pi not in fix_versions:
            continue
        lower_labels = set(label.lower() for label in issue.fields.labels)
        if lower_labels.intersection(unlinked_labels):
            continue

        if issue.key not in issue_parentage:
            unlinked_issues.append(issue.key)

    if len(unlinked_issues) > 1:
        pytest.fail(
            f"{len(unlinked_issues)} '{status}' issues aren't linked:\n"
            f"{pprint.pformat(unlinked_issues)}"
        )
    elif len(unlinked_issues) == 1:
        pytest.fail(f"{unlinked_issues[0]} ('{status}') is not linked.")


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
    pi, session, unlinked_labels, issue_parentage, issues_by_status, status
):
    """
    Test that every issue is appropriately linked.

    Every issue should be either the "Child of" a feature,
    or "Relates to" an objective.

    Exceptions are made for tickets with one of the following labels:
    "TEAM_BACKLOG", "DEPENDENCY", "INNOVATION" or "OVERHEAD".

    :param pi: the current Program Increment number
    :param session: an active Jira session.
    :param unlinked_labels: set of lower-case labels
        that indicate that an issue is deliberately not linked
        to a feature or objective, and therefore should be ignored by this test.
    :param issue_parentage: dictionary specifying the parents of each issue
    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
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
        if lower_labels.intersection(unlinked_labels):
            continue
        if issue.key not in issue_parentage:
            continue
        for _, link_target in issue_parentage[issue.key]:
            if is_in_this_pi(link_target):
                break
        else:
            mislinked_issues.append(issue.key)

    if len(mislinked_issues) > 1:
        pytest.fail(
            f"{len(mislinked_issues)} '{status}' issues aren't linked "
            "to a parent in the current PI:\n"
            f"{pprint.pformat(mislinked_issues)}"
        )
    elif len(mislinked_issues) == 1:
        pytest.fail(
            f"{mislinked_issues[0]} is '{status}' and is not linked "
            "to a parent in the current PI."
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
)
def test_status_is_consistent_with_parent_status(
    session, issues_by_status, status, consistent_parent_statuses, issue_parentage
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
    """

    @functools.lru_cache
    def issue_status(issue_key):
        issue = session.issue(issue_key)
        return issue.fields.status.name

    inconsistent_issues = defaultdict(list)
    for issue in issues_by_status[status]:
        if issue.key not in issue_parentage:
            continue
        for _, parent_key in issue_parentage[issue.key]:
            if issue_status(parent_key) not in consistent_parent_statuses:
                inconsistent_issues[issue.key].append(parent_key)

    if len(inconsistent_issues) > 1:
        pytest.fail(
            f"{len(inconsistent_issues)} issues have inconsistent parent status:"
            f"{pprint.pformat(dict(inconsistent_issues))}"
        )
    elif len(inconsistent_issues) == 1:
        inconsistent_issue, parents = inconsistent_issues.popitem()
        pytest.fail(f"{inconsistent_issue} has an inconsistent parent/s {parents}.")


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
