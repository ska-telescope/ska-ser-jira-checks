"""Tests that address the age of tickets."""

import datetime

import pytest

from tests.conftest import fail_if_data


@pytest.mark.parametrize(
    ("status", "age_limit", "include_epics"),
    [
        ("BACKLOG", 90, True),
        ("To Do", 30, False),
        ("In Progress", 30, False),
        ("Reviewing", 14, True),
        ("Merge Request", 14, True),
        ("BLOCKED", 14, True),
        ("READY FOR ACCEPTANCE", 7, True),
    ],
)
def test_issues_not_too_old(issues_by_status, status, age_limit, include_epics):
    """
    Test that every issue has been updated reasonably recently.

    Actions:

    * For a "BACKLOG" item, it's time to re-examine this issue,
      and ask if it is still something that is worth doing.
      If so, add a comment that the issue has been reviewed and retained.
      Otherwise, discard it.

    * For a "To Do" item, ask whether this is still a task that
      the team intends to do imminently.
      If so, add a comment to that effect.
      Otherwise, push it back to the BACKLOG, or discard it.

    * For other items, why is this issue is not being progressed?

    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    :param age_limit: the maximum permitted number of days
         since an issue has been updated.
    :param include_epics: whether to include issues of type Epic
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    deadline = now - datetime.timedelta(days=age_limit)

    old_issues = []
    for issue in issues_by_status[status]:
        if issue.fields.issuetype.name == "Epic" and not include_epics:
            continue
        updated = datetime.datetime.strptime(
            issue.fields.updated, "%Y-%m-%dT%H:%M:%S.%f%z"
        )
        if updated < deadline:
            assignee = (
                issue.fields.assignee.name
                if issue.fields.assignee
                else issue.fields.creator.name
            )
            old_issues.append(
                {
                    "Key": issue.key,
                    "Summary": issue.fields.summary,
                    "Assignee": assignee,
                    "Age": (now - updated).days,
                }
            )

    fail_if_data(
        old_issues,
        (
            "{Key} ('{Summary}'), assigned to {Assignee}, "
            f"has been {status} for {{Age}} days."
        ),
        f"{{length}} issues have been {status} for more than {age_limit} days.",
        sort_key="Age",
        reverse=True,
    )
