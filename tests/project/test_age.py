"""Tests that address the age of tickets."""

import datetime
import pprint
from collections import defaultdict

import pytest


@pytest.mark.parametrize(
    ("status", "age", "include_epics"),
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
def test_issues_not_too_old(issues_by_status, status, age, include_epics):
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
    :param age: the maximum permitted number of days since an issue has been updated.
    :param include_epics: whether to include issues of type Epic
    """
    deadline = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        days=age
    )

    old_issues = defaultdict(list)
    count = 0
    for issue in issues_by_status[status]:
        if issue.fields.issuetype.name == "Epic" and not include_epics:
            continue
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
            f"{count} '{status}' issues have not been updated "
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
