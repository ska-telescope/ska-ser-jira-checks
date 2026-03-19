"""Assignment checks for Jira issues."""

# pylint: disable=too-few-public-methods,arguments-differ
from collections import defaultdict

from ska_ser_jira_checks.checks.utils import get_assignee
from ska_ser_jira_checks.models import Check, ProjectCheckContext, Report


class TicketsHaveAssigneeCheck(Check):
    """Check that all tickets in a status have an assignee."""

    parametrization = [
        {"status": "In Progress"},
        {"status": "Reviewing"},
        {"status": "Merge Request"},
        {"status": "READY FOR ACCEPTANCE"},
        {"status": "Done"},
        {"status": "BLOCKED"},
    ]

    def check(
        self, report: Report, context: ProjectCheckContext, status: str, **kwargs
    ) -> None:
        """Check that all tickets in a status have an assignee.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        for issue in issues_by_status.get(status, []):
            if not issue.fields.assignee:
                report.add_violation(
                    check_name=f"unassigned_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"status": status},
                )


class NoOneHasTooMuchWipCheck(Check):
    """Check that no one has too many issues 'In Progress'."""

    parametrization = [{"max_wip": 4}]

    def check(
        self, report: Report, context: ProjectCheckContext, max_wip: int, **kwargs
    ) -> None:
        """Check that no one has too many issues 'In Progress'.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param max_wip: The maximum number of issues in progress allowed.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        in_progress = issues_by_status.get("In Progress", [])
        by_assignee = defaultdict(list)
        for issue in in_progress:
            if issue.fields.issuetype.name == "Epic":
                continue
            assignee = get_assignee(issue)
            if assignee != "UNASSIGNED":
                by_assignee[assignee].append(issue)

        for assignee, assignee_issues in by_assignee.items():
            if len(assignee_issues) > max_wip:
                report.add_violation(
                    check_name="too_much_wip",
                    issue_key="N/A",
                    summary=(
                        f"Assignee {assignee} has too much WIP: "
                        f"{len(assignee_issues)} issues (limit {max_wip})"
                    ),
                    details={
                        "assignee": assignee,
                        "wip_count": len(assignee_issues),
                        "issues": [
                            {"key": issue.key, "summary": issue.fields.summary}
                            for issue in assignee_issues
                        ],
                    },
                )


class NoOneHasTooMuchBlockedCheck(Check):
    """Check that no one has too many issues 'BLOCKED'."""

    parametrization = [{"max_blocked": 2}]

    def check(
        self, report: Report, context: ProjectCheckContext, max_blocked: int, **kwargs
    ) -> None:
        """Check that no one has too many issues 'BLOCKED'.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param max_blocked: The maximum number of blocked issues allowed.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        blocked = issues_by_status.get("BLOCKED", [])
        by_assignee = defaultdict(list)
        for issue in blocked:
            if issue.fields.issuetype.name == "Epic":
                continue
            assignee = get_assignee(issue)
            if assignee != "UNASSIGNED":
                by_assignee[assignee].append(issue)

        for assignee, assignee_issues in by_assignee.items():
            if len(assignee_issues) > max_blocked:
                report.add_violation(
                    check_name="too_much_blocked",
                    issue_key="N/A",
                    summary=(
                        f"Assignee {assignee} has too many blocked issues: "
                        f"{len(assignee_issues)} issues (limit {max_blocked})"
                    ),
                    details={
                        "assignee": assignee,
                        "blocked_count": len(assignee_issues),
                        "issues": [
                            {"key": issue.key, "summary": issue.fields.summary}
                            for issue in assignee_issues
                        ],
                    },
                )


class TicketsAreAssignedWithinTeamCheck(Check):
    """Check that tickets in a status are assigned within the team."""

    parametrization = [
        {"status": "BACKLOG"},
        {"status": "To Do"},
        {"status": "BLOCKED"},
        {"status": "In Progress"},
        {"status": "Reviewing"},
        {"status": "Merge Request"},
        {"status": "READY FOR ACCEPTANCE"},
    ]

    def check(
        self, report: Report, context: ProjectCheckContext, status: str, **kwargs
    ) -> None:
        """Check that tickets in a status are assigned within the team.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        team = context.team
        if not team:
            return

        for issue in issues_by_status.get(status, []):
            assignee = get_assignee(issue)
            if assignee != "UNASSIGNED" and assignee not in team:
                report.add_violation(
                    check_name=f"misassigned_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"status": status, "assignee": assignee},
                )


class EveryoneHasATicketInProgressCheck(Check):
    """Check that everyone in the team has a ticket 'In Progress'."""

    parametrization = [{}]

    def check(self, report: Report, context: ProjectCheckContext, **kwargs) -> None:
        """Check that everyone in the team has a ticket 'In Progress'.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        team = context.team
        if not team:
            return

        in_progress = issues_by_status.get("In Progress", [])
        assignees_in_progress = {
            get_assignee(issue)
            for issue in in_progress
            if issue.fields.issuetype.name != "Epic"
        }

        unassigned_members = team - assignees_in_progress
        for member in unassigned_members:
            report.add_violation(
                check_name="no_wip_for_member",
                issue_key="N/A",
                summary=f"Team member {member} has no tickets In Progress.",
                details={"member": member},
            )
