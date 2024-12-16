"""Pytest fixtures and test setup for SKB-specific tests."""

import datetime
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
