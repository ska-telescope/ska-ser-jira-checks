"""Custom team-specific checks for Jira issues."""

# pylint: disable=too-few-public-methods
from ska_ser_jira_checks.checks.utils import get_fix_versions
from ska_ser_jira_checks.models import Check, ProjectCheckContext, Report


class NoRfaIssuesAssignedToAlexCheck(Check):
    """Check that Alex doesn't have any RFA issues (project LOW only)."""

    parametrization = [{}]

    def check(self, report: Report, context: ProjectCheckContext, **kwargs) -> None:
        """
        Check that Alex doesn't have any RFA issues (project LOW only).

        :param report: The report object to add violations to.
        :param context: The context containing issue data.
        :param kwargs: Additional parameters for the check.
        """
        if context.project != "LOW":
            return

        issues_by_status = context.issues_by_status
        rfa_issues = issues_by_status.get("READY FOR ACCEPTANCE", [])
        for issue in rfa_issues:
            if (
                issue.fields.assignee
                and issue.fields.assignee.name == "A.Hill"
                and issue.fields.issuetype.name != "Epic"
            ):
                report.add_violation(
                    check_name="rfa_assigned_to_alex",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"assignee": "A.Hill"},
                )


class IssuesInThisPiHaveAcceptableTypesCheck(Check):
    """Check that every issue has an acceptable type."""

    parametrization = [{}]

    def check(self, report: Report, context: ProjectCheckContext, **kwargs) -> None:
        """
        Check that every issue has an acceptable type.

        :param report: The report object to add violations to.
        :param context: The context containing issue data.
        :param kwargs: Additional parameters for the check.
        """
        acceptable_types = ["Story", "Enabler", "Spike", "Bug", "Epic"]
        current_pi = f"PI{context.pi}"

        for issues in context.issues_by_status.values():
            for issue in issues:
                fix_versions = get_fix_versions(issue)
                if current_pi not in fix_versions:
                    continue
                if issue.fields.issuetype.name in acceptable_types:
                    continue

                report.add_violation(
                    check_name="unacceptable_issue_type",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"type": issue.fields.issuetype.name},
                )
