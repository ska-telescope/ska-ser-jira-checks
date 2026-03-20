"""Report-based tests for SKB issues."""

import pytest


@pytest.mark.parametrize("status", ["Identified", "In Assessment", "Assigned"])
def test_team_created_skbs_have_component(skb_report, status):
    """
    Test that every team-created SKB has been allocated to a component.

    :param skb_report: The report to check.
    :param status: The status to check.
    """
    violations = skb_report.violations.get(f"skb_no_component_{status}", [])
    if violations:
        msg = f"{len(violations)} team-created SKBs are {status} with no component:\n"
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary} (Creator: {v.details['creator']})\n"
        pytest.fail(msg)


@pytest.mark.parametrize(
    "status",
    [
        "Identified",
        "In Assessment",
        "Assigned",
        "In Progress",
        "BLOCKED",
        "Validating",
    ],
)
def test_skb_not_too_old(skb_report, status):
    """
    Test that every SKB assigned to the team has been updated reasonably recently.

    :param skb_report: The report to check.
    :param status: The status to check.
    """
    violations = skb_report.violations.get(f"skb_too_old_{status}", [])
    if violations:
        msg = f"{len(violations)} {status} SKBs have not been updated for too long:\n"
        for v in violations:
            msg += (
                f"- {v.issue_key}: {v.summary} "
                f"(Age: {v.details['age_days']} days, "
                f"Assignee: {v.details['assignee']})\n"
            )
        pytest.fail(msg)


@pytest.mark.parametrize(
    "status",
    [
        "Identified",
        "In Assessment",
        "Assigned",
        "In Progress",
        "BLOCKED",
        "Validating",
    ],
)
def test_that_skbs_are_child_of_a_feature_or_relate_to_an_objective_in_this_pi(
    skb_report, status
):
    """
    Test that SKBs are child of a feature or relate to an objective.

    :param skb_report: The report to check.
    :param status: The status to check.
    """
    violations = skb_report.violations.get(f"skb_not_linked_to_pi_{status}", [])
    if violations:
        msg = (
            f"{len(violations)} {status} SKBs aren't linked "
            "to a feature or objective in the current PI:\n"
        )
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary} (Assignee: {v.details['assignee']})\n"
        pytest.fail(msg)
