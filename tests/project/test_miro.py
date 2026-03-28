"""Report-based tests for Jira tickets on Miro board."""

import os

import pytest


def test_all_jira_tickets_on_miro_board(report):
    """
    Test that all Jira tickets are on the Miro board.

    :param report: The report to check.
    """
    if not os.environ.get("MIRO_API_TOKEN") or not os.environ.get("MIRO_BOARD_ID"):
        pytest.skip("Miro credentials not provided.")

    violations = report.violations.get("missing_from_miro", [])

    if violations:
        msg = f"{len(violations)} tickets are missing from the Miro board:\n"
        for v in violations:
            msg += f"- {v.issue_key}: {v.summary}\n"
        pytest.fail(msg)
