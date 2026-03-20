"""Content checks for Jira issues."""

# pylint: disable=too-few-public-methods,arguments-differ
from ska_ser_jira_checks.checks.utils import get_assignee, get_fix_versions
from ska_ser_jira_checks.models import Check, ProjectCheckContext, Report


class IssuesHaveDescriptionCheck(Check):
    """Check that all issues in a status have descriptions."""

    parametrization = [
        {"status": "To Do"},
        {"status": "In Progress"},
        {"status": "BLOCKED"},
        {"status": "Reviewing"},
        {"status": "Merge Request"},
        {"status": "READY FOR ACCEPTANCE"},
    ]

    def check(
        self, report: Report, context: ProjectCheckContext, status: str, **kwargs
    ) -> None:
        """
        Check that all issues in a status have descriptions.

        :param report: The report object to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        for issue in issues_by_status.get(status, []):
            if not issue.fields.description:
                report.add_violation(
                    check_name=f"no_description_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={
                        "status": status,
                        "creator": issue.fields.creator.name,
                    },
                )


class IssuesHaveFixVersionCheck(Check):
    """Check that all issues in a status have a fixVersion."""

    parametrization = [
        {"status": "To Do"},
        {"status": "In Progress"},
        {"status": "BLOCKED"},
        {"status": "Reviewing"},
        {"status": "Merge Request"},
        {"status": "READY FOR ACCEPTANCE"},
    ]

    def check(
        self, report: Report, context: ProjectCheckContext, status: str, **kwargs
    ) -> None:
        """
        Check that all issues in a status have a fixVersion.

        :param report: The report object to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        for issue in issues_by_status.get(status, []):
            if not issue.fields.fixVersions:
                report.add_violation(
                    check_name=f"no_fix_version_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"status": status},
                )


class NoIssuesWithOldFixVersionCheck(Check):
    """Check that no incomplete issues have an old fixVersion."""

    parametrization = [
        {"status": "To Do"},
        {"status": "In Progress"},
        {"status": "BLOCKED"},
        {"status": "Reviewing"},
        {"status": "Merge Request"},
        {"status": "READY FOR ACCEPTANCE"},
    ]

    def check(
        self, report: Report, context: ProjectCheckContext, status: str, **kwargs
    ) -> None:
        """
        Check that no incomplete issues have an old fixVersion.

        :param report: The report object to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        pi = context.pi
        current_pi = f"PI{pi}"
        issues_by_status = context.issues_by_status

        for issue in issues_by_status.get(status, []):
            fix_versions = get_fix_versions(issue)
            if not fix_versions:
                continue

            if current_pi in fix_versions:
                continue

            report.add_violation(
                check_name=f"old_fix_version_{status}",
                issue_key=issue.key,
                summary=issue.fields.summary,
                details={"status": status, "assignee": get_assignee(issue)},
            )
