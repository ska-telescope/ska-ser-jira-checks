"""Points checks for Jira issues."""

# pylint: disable=too-few-public-methods,arguments-differ
from ska_ser_jira_checks.checks.utils import get_fix_versions
from ska_ser_jira_checks.models import Check, ProjectCheckContext, Report


class IssuesInThisPiHavePointsCheck(Check):
    """Check that every story/enabler/spike in this PI has story points."""

    parametrization = [
        {"status": "To Do"},
        {"status": "In Progress"},
        {"status": "Reviewing"},
        {"status": "READY FOR ACCEPTANCE"},
        {"status": "BLOCKED"},
        {"status": "Done"},
    ]

    def check(
        self,
        report: Report,
        context: ProjectCheckContext,
        status: str,
        **kwargs,
    ) -> None:
        """
        Check that every story/enabler/spike in this PI has story points.

        :param report: The report object to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        current_pi = f"PI{context.pi}"
        issues_in_status = context.issues_by_status.get(status, [])
        issue_types_to_check = ["Story", "Enabler", "Spike"]

        for issue in issues_in_status:
            if issue.fields.issuetype.name not in issue_types_to_check:
                continue

            fix_versions = get_fix_versions(issue)
            if current_pi not in fix_versions:
                continue

            # Story points is customfield_10002
            story_points = getattr(issue.fields, "customfield_10002", None)

            if story_points is None:
                report.add_violation(
                    check_name=f"no_story_points_{status.lower().replace(' ', '_')}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={
                        "issue_type": issue.fields.issuetype.name,
                        "pi": current_pi,
                        "status": status,
                    },
                )
