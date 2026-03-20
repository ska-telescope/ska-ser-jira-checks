"""RFA checks for Jira issues."""

# pylint: disable=too-few-public-methods,arguments-differ
from ska_ser_jira_checks.checks.utils import get_assignee, get_dev_field
from ska_ser_jira_checks.models import Check, ProjectCheckContext, Report


class RfaIssuesHaveOutcomesCheck(Check):
    """Check that all READY FOR ACCEPTANCE issues have outcomes."""

    parametrization = [{}]

    def check(self, report: Report, context: ProjectCheckContext, **kwargs) -> None:
        """Check that all READY FOR ACCEPTANCE issues have outcomes.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        rfa_issues = issues_by_status.get("READY FOR ACCEPTANCE", [])
        for issue in rfa_issues:
            if issue.fields.issuetype.name == "Bug":
                continue
            if not issue.fields.customfield_11949:
                report.add_violation(
                    check_name="rfa_no_outcomes",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"assignee": get_assignee(issue)},
                )


class NoActiveIssuesHaveOnlyClosedMergeRequestsCheck(Check):
    """Check that In Progress/Reviewing issues don't have only merged MRs."""

    parametrization = [
        {"status": "In Progress"},
        {"status": "Reviewing"},
        {"status": "Merge Request"},
    ]

    def check(
        self, report: Report, context: ProjectCheckContext, status: str, **kwargs
    ) -> None:
        """Check that In Progress/Reviewing issues don't have only merged MRs.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        for issue in issues_by_status.get(status, []):
            if issue.fields.issuetype.name == "Epic":
                continue

            dev_field = get_dev_field(issue)
            if not dev_field:
                continue

            pullrequest = (
                dev_field.get("cachedValue", {})
                .get("summary", {})
                .get("pullrequest", {})
            )
            counts = pullrequest.get("overall", {}).get("details", {})

            if counts.get("mergedCount") and not counts.get("openCount"):
                report.add_violation(
                    check_name=f"active_with_only_closed_mrs_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"status": status, "assignee": get_assignee(issue)},
                )


class NoRfaOrDoneIssuesHaveOpenMergeRequestsCheck(Check):
    """Check that no READY FOR ACCEPTANCE or Done issues have unmerged MRs."""

    parametrization = [
        {"status": "READY FOR ACCEPTANCE"},
        {"status": "Done"},
    ]

    def check(
        self, report: Report, context: ProjectCheckContext, status: str, **kwargs
    ) -> None:
        """Check that no READY FOR ACCEPTANCE or Done issues have unmerged MRs.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        for issue in issues_by_status.get(status, []):
            dev_field = get_dev_field(issue)
            if not dev_field:
                continue

            pullrequest = (
                dev_field.get("cachedValue", {})
                .get("summary", {})
                .get("pullrequest", {})
            )
            counts = pullrequest.get("overall", {}).get("details", {})

            if counts.get("openCount"):
                report.add_violation(
                    check_name=f"rfa_or_done_with_open_mrs_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"status": status, "assignee": get_assignee(issue)},
                )


class NotTooManyRfaIssuesCheck(Check):
    """Check that there are not too many READY FOR ACCEPTANCE issues."""

    parametrization = [{"max_rfa": 9}]

    def check(
        self, report: Report, context: ProjectCheckContext, max_rfa: int, **kwargs
    ) -> None:
        """Check that there are not too many READY FOR ACCEPTANCE issues.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param max_rfa: The maximum number of RFA issues allowed.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        rfa_issues = issues_by_status.get("READY FOR ACCEPTANCE", [])
        if len(rfa_issues) > max_rfa:
            report.add_violation(
                check_name="too_many_rfa",
                issue_key="N/A",
                summary=f"Too many RFA issues: {len(rfa_issues)} (limit {max_rfa})",
                details={
                    "rfa_count": len(rfa_issues),
                    "issues": [
                        {
                            "key": issue.key,
                            "summary": issue.fields.summary,
                            "assignee": get_assignee(issue),
                        }
                        for issue in rfa_issues
                    ],
                },
            )


class NoTodoOrBacklogIssueWithCommitsCheck(Check):
    """Check that no 'To Do' or 'Backlog' issues have commits."""

    parametrization = [
        {"status": "To Do"},
        {"status": "BACKLOG"},
    ]

    def check(
        self, report: Report, context: ProjectCheckContext, status: str, **kwargs
    ) -> None:
        """Check that no 'To Do' or 'Backlog' issues have commits.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        for issue in issues_by_status.get(status, []):
            dev_field = get_dev_field(issue)
            if not dev_field:
                continue

            repository = (
                dev_field.get("cachedValue", {})
                .get("summary", {})
                .get("repository", {})
            )
            overall = repository.get("overall", {})
            if overall.get("count"):
                report.add_violation(
                    check_name=f"todo_or_backlog_with_commits_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"status": status, "assignee": get_assignee(issue)},
                )
