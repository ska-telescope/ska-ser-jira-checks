"""Age checks for Jira issues."""

# pylint: disable=too-few-public-methods,arguments-differ
# pylint: disable=too-many-arguments,too-many-positional-arguments
import datetime

from ska_ser_jira_checks.checks.utils import get_assignee
from ska_ser_jira_checks.models import Check, ProjectCheckContext, Report


class IssuesNotTooOldCheck(Check):
    """Check that issues in a status have been updated reasonably recently."""

    parametrization = [
        {"status": "BACKLOG", "age_limit": 120},
        {
            "status": "To Do",
            "age_limit": 30,
            "include_epics": False,
        },
        {
            "status": "In Progress",
            "age_limit": 30,
            "include_epics": False,
        },
        {"status": "Reviewing", "age_limit": 14},
        {"status": "Merge Request", "age_limit": 14},
        {"status": "BLOCKED", "age_limit": 14},
        {"status": "READY FOR ACCEPTANCE", "age_limit": 7},
    ]

    def check(
        self,
        report: Report,
        context: ProjectCheckContext,
        status: str,
        age_limit: int,
        include_epics: bool = True,
        **kwargs,
    ) -> None:
        """
        Check that issues in a status have been updated reasonably recently.

        :param report: The report object to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param age_limit: The maximum age in days.
        :param include_epics: Whether to include Epics in the check.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        now = datetime.datetime.now(datetime.timezone.utc)
        deadline = now - datetime.timedelta(days=age_limit)

        for issue in issues_by_status.get(status, []):
            if issue.fields.issuetype.name == "Epic" and not include_epics:
                continue

            updated = datetime.datetime.strptime(
                issue.fields.updated, "%Y-%m-%dT%H:%M:%S.%f%z"
            )

            if updated < deadline:
                report.add_violation(
                    check_name=f"too_old_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={
                        "status": status,
                        "age_days": (now - updated).days,
                        "assignee": get_assignee(issue),
                    },
                )
