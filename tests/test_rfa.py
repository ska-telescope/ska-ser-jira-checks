"""Test RFA issues."""

import json
import pprint
from collections import defaultdict

import pytest


def test_rfa_issues_have_outcomes(rfa_issues):
    """
    Test that all READY FOR ACCEPTANCE issues have outcomes.

    Writing outcomes should be a pre-requisite to moving a ticket to RFA.

    :param rfa_issues: list of RFA issues.
    """
    no_outcomes_rfa = defaultdict(list)
    count = 0

    for issue in rfa_issues:
        if issue.fields.issuetype.name == "Bug":
            continue
        if not issue.fields.customfield_11949:
            assignee = (
                issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            )
            no_outcomes_rfa[assignee].append(issue.key)
            count += 1

    if len(no_outcomes_rfa) > 1:
        pytest.fail(
            f"{count} 'READY FOR ACCEPTANCE' issues have no outcomes:\n"
            f"{pprint.pformat(dict(no_outcomes_rfa))}."
        )
    elif len(no_outcomes_rfa) == 1:
        assignee, issues = no_outcomes_rfa.popitem()
        if len(issues) > 1:
            pytest.fail(
                f"{assignee} has {count} 'READY FOR ACCEPTANCE' issues "
                f"with no outcomes:\n{pprint.pformat(issues)}"
            )
        else:  # len(issues) == 1
            pytest.fail(
                f"{assignee} has {issues[0]} 'READY FOR ACCEPTANCE' with no outcomes."
            )


@pytest.mark.parametrize("status", ["Reviewing", "Merge Request"])
def test_reviewing_issues_have_open_merge_requests(issues_by_status, status):
    """
    Test that Reviewing or Merge Request issues have unmerged MRs.

    If they don't, then they should be moved through to READY FOR ACCEPTANCE.

    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    issues_with_no_open_mrs = defaultdict(list)
    count = 0

    for issue in issues_by_status[status]:
        raw_dev_field = issue.fields.customfield_13300

        index = raw_dev_field.find("devSummaryJson=")
        json_bit = raw_dev_field[index + len("devSummaryJson=") : -1]
        dev_field = json.loads(json_bit)

        if not dev_field["cachedValue"]["summary"]["pullrequest"]["overall"]["details"][
            "openCount"
        ]:
            name = issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            issues_with_no_open_mrs[name].append(issue.key)
            count += 1

    if len(issues_with_no_open_mrs) > 1:
        pytest.fail(
            f"{count} '{status}' issues have no unmerged commits:\n"
            f"{pprint.pformat(dict(issues_with_no_open_mrs))}"
        )
    elif len(issues_with_no_open_mrs) == 1:
        assignee, issues = issues_with_no_open_mrs.popitem()
        if len(issues) > 1:
            pytest.fail(
                f"{assignee} has {count} '{status}' issues with no unmerged commits:\n"
                f"{pprint.pformat(issues)}"
            )
        else:
            pytest.fail(
                f"{assignee}; {issues[0]} is '{status}' with no unmerged commits."
            )


@pytest.mark.parametrize("status", ["READY FOR ACCEPTANCE", "Done"])
def test_no_rfa_or_done_issues_have_open_merge_requests(issues_by_status, status):
    """
    Test that no READY FOR ACCEPTANCE or Done issues have unmerged MRs.

    :param issues_by_status: dictionary of issues, keyed by their status.
    :param status: the issue status under consideration.
    """
    issues_with_open_mrs = defaultdict(list)
    count = 0

    for issue in issues_by_status[status]:
        raw_dev_field = issue.fields.customfield_13300

        index = raw_dev_field.find("devSummaryJson=")
        json_bit = raw_dev_field[index + len("devSummaryJson=") : -1]
        dev_field = json.loads(json_bit)

        if dev_field["cachedValue"]["summary"]["pullrequest"]["overall"]["details"][
            "openCount"
        ]:
            name = issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            issues_with_open_mrs[name].append(issue.key)
            count += 1

    if len(issues_with_open_mrs) > 1:
        pytest.fail(
            f"{count} '{status}' issues have unmerged commits:\n"
            f"{pprint.pformat(dict(issues_with_open_mrs))}"
        )
    elif len(issues_with_open_mrs) == 1:
        assignee, issues = issues_with_open_mrs.popitem()
        if len(issues) > 1:
            pytest.fail(
                f"{assignee} has {count} '{status}' issues with unmerged commits:\n"
                f"{pprint.pformat(issues)}"
            )
        else:
            pytest.fail(f"{assignee}; {issues[0]} is '{status}' with unmerged commits.")


@pytest.mark.parametrize("max_rfa", [9])
def test_not_too_many_rfa_issues(rfa_issues, max_rfa):
    """
    Test that there are not too many READY FOR ACCEPTANCE issues.

    Too many RFA issues means the PO has fallen behind on moving these to Done.

    :param rfa_issues: list of RFA issues
    :param max_rfa: the maximum permitted number of READY FOR ACCEPTANCE issues.
    """
    if len(rfa_issues) > max_rfa:
        rfas_by_assignee = defaultdict(list)
        for issue in rfa_issues:
            name = issue.fields.assignee.name if issue.fields.assignee else "UNASSIGNED"
            rfas_by_assignee[name].append(issue.key)

        pytest.fail(
            f"{len(rfa_issues)} issues are RFA:\n"
            f"{pprint.pformat(dict(rfas_by_assignee))}"
        )
