"""Miro board checks for Jira issues."""

# pylint: disable=too-few-public-methods
# pylint: disable=too-many-locals, too-many-branches
import os

import requests

from ska_ser_jira_checks.models import Check, ProjectCheckContext, Report


class MiroBoardCheck(Check):
    """Check that Jira tickets are on the Miro board."""

    parametrization = [
        {"include_epics": True},
    ]

    def check(
        self,
        report: Report,
        context: ProjectCheckContext,
        include_epics: bool = True,
        **kwargs,
    ) -> None:
        """
        Check that Jira tickets for the current PI are on the Miro board.

        :param report: The report object to add violations to.
        :param context: The context containing issue data.
        :param include_epics: Whether to include Epics in the check.
        :param kwargs: Additional parameters for the check.
        """
        pi_str = f"PI{context.pi}"

        # Original code used PROJECT and PI in JQL, but here issues
        # are already fetched. Filter for the current PI as a fixVersion.
        relevant_issues = []
        for status, status_issues in context.issues_by_status.items():
            if status == "Discarded":
                continue
            for issue in status_issues:
                if issue.fields.issuetype.name == "Epic" and not include_epics:
                    continue

                fix_versions = {v.name for v in issue.fields.fixVersions}
                if pi_str in fix_versions:
                    relevant_issues.append(issue)

        if not relevant_issues:
            return

        # Fetch Miro board items
        token = os.environ.get("MIRO_API_TOKEN")
        board_id = os.environ.get("MIRO_BOARD_ID")

        if not token or not board_id:
            # If credentials are not provided, we skip this check.
            # We don't want to fail if Miro is not configured.
            return

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }
        url = f"https://api.miro.com/v2/boards/{board_id}/items?type=card&limit=50"

        miro_titles = set()
        try:
            while url:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                for item in data.get("data", []):
                    if "data" in item and "title" in item["data"]:
                        miro_titles.add(item["data"]["title"])

                url = data.get("links", {}).get("next")
        except Exception as e:  # pylint: disable=broad-exception-caught
            # If we can't fetch Miro data, we report a violation.
            report.add_violation(
                check_name="miro_connection_error",
                issue_key=context.project,
                summary=f"Could not fetch Miro data: {str(e)}",
                details={},
            )
            return

        for issue in relevant_issues:
            if issue.fields.summary not in miro_titles:
                report.add_violation(
                    check_name="missing_from_miro",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={
                        "pi": pi_str,
                        "board_id": board_id,
                    },
                )
