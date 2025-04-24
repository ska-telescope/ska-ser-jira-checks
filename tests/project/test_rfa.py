"""Test RFA issues."""

import json
from typing import Any

import pytest

from tests.conftest import fail_if_data


def test_rfa_issues_have_outcomes(rfa_issues):
    """
    Test that all READY FOR ACCEPTANCE issues have outcomes.

    Writing outcomes should be a pre-requisite to moving a ticket to RFA.

    :param rfa_issues: list of RFA issues.
    """
    no_outcomes_rfa: list[dict[str, Any]] = []

    for issue in rfa_issues:
        if issue.fields.issuetype.name == "Bug":
            continue
        if not issue.fields.customfield_11949:
            assignee = (
                issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            )
            no_outcomes_rfa.append(
                {
                    "Issue": issue.key,
                    "Summary": issue.fields.summary,
                    "Assignee": assignee,
                }
            )

    fail_if_data(
        no_outcomes_rfa,
        (
            "{Issue} ('{Summary}'), assigned to {Assignee}, "
            "is READY FOR ACCEPTANCE with no outcomes."
        ),
        "{length} READY FOR ACCEPTANCE issues have no outcomes:",
        sort_key="Issue",
    )


@pytest.mark.parametrize("status", ["Reviewing", "Merge Request"])
def test_reviewing_issues_have_open_merge_requests(issues_by_status, status):
    """
    Test that Reviewing or Merge Request issues have unmerged MRs.

    If they don't, then they should be moved through to READY FOR ACCEPTANCE.

    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    issues_with_no_open_mrs: list[dict[str, Any]] = []

    for issue in issues_by_status[status]:
        raw_dev_field = issue.fields.customfield_13300

        index = raw_dev_field.find("devSummaryJson=")
        json_bit = raw_dev_field[index + len("devSummaryJson=") : -1]
        dev_field = json.loads(json_bit)

        if not dev_field["cachedValue"]["summary"]["pullrequest"]["overall"]["details"][
            "openCount"
        ]:
            assignee = (
                issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            )
            issues_with_no_open_mrs.append(
                {
                    "Issue": issue.key,
                    "Summary": issue.fields.summary,
                    "Assignee": assignee,
                }
            )

    fail_if_data(
        issues_with_no_open_mrs,
        (
            "{Issue} ('{Summary}'), assigned to {Assignee}, "
            f"is {status} with no unmerged commits."
        ),
        f"{{length}} {status} issues have no unmerged commits:",
        sort_key="Issue",
    )


@pytest.mark.parametrize("status", ["READY FOR ACCEPTANCE", "Done"])
def test_no_rfa_or_done_issues_have_open_merge_requests(issues_by_status, status):
    """
    Test that no READY FOR ACCEPTANCE or Done issues have unmerged MRs.

    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    issues_with_open_mrs: list[dict[str, Any]] = []

    for issue in issues_by_status[status]:
        raw_dev_field = issue.fields.customfield_13300

        index = raw_dev_field.find("devSummaryJson=")
        json_bit = raw_dev_field[index + len("devSummaryJson=") : -1]
        dev_field = json.loads(json_bit)

        if dev_field["cachedValue"]["summary"]["pullrequest"]["overall"]["details"][
            "openCount"
        ]:
            assignee = (
                issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            )
            issues_with_open_mrs.append(
                {
                    "Issue": issue.key,
                    "Summary": issue.fields.summary,
                    "Assignee": assignee,
                }
            )

    fail_if_data(
        issues_with_open_mrs,
        (
            "{Issue} ('{Summary}'), assigned to {Assignee}, "
            f"is {status} with unmerged commits."
        ),
        f"{{length}} {status} issues have unmerged commits:",
        sort_key="Issue",
    )


@pytest.mark.parametrize("max_rfa", [9])
def test_not_too_many_rfa_issues(rfa_issues, max_rfa):
    """
    Test that there are not too many READY FOR ACCEPTANCE issues.

    Too many RFA issues means the PO has fallen behind on moving these to Done.

    :param rfa_issues: list of RFA issues
    :param max_rfa: the maximum permitted number of READY FOR ACCEPTANCE issues.
    """
    if len(rfa_issues) <= max_rfa:
        return

    rfas = []
    for issue in rfa_issues:
        assignee = issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"

        rfas.append(
            {
                "Issue": issue.key,
                "Summary": issue.fields.summary,
                "Assignee": assignee,
            }
        )

    fail_if_data(
        rfas,
        "{Issue} ('{Summary}') is REASY FOR ACCEPTANCE",
        "{length} issues are READY FOR ACCEPTANCE:",
        sort_key="Issue",
    )
