"""Link checks for Jira issues."""

# pylint: disable=too-few-public-methods,arguments-differ
# pylint: disable=too-many-nested-blocks
import functools

from ska_ser_jira_checks.checks.utils import get_fix_versions
from ska_ser_jira_checks.constants import UNLINKED_LABELS
from ska_ser_jira_checks.models import Check, ProjectCheckContext, Report


class NoIssuesAreChildOfAnObjectiveCheck(Check):
    """Check that no issues link to an objective with relationship 'Child of'."""

    parametrization = [{}]

    def check(self, report: Report, context: ProjectCheckContext, **kwargs) -> None:
        """Check that no issues link to an objective with relationship 'Child of'.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param kwargs: Additional parameters for the check.
        """
        for issues in context.issues_by_status.values():
            for issue in issues:
                for issuelink in issue.fields.issuelinks:
                    if issuelink.type.name == "Parent/Child":
                        if hasattr(issuelink, "inwardIssue"):
                            inward = str(issuelink.inwardIssue)
                            if inward.startswith("SPO-"):
                                report.add_violation(
                                    check_name="child_of_objective",
                                    issue_key=issue.key,
                                    summary=issue.fields.summary,
                                    details={"objective": inward},
                                )


class NoIssuesRelateToAFeatureCheck(Check):
    """Check that no issues link to a feature with relationship 'Relates to'."""

    parametrization = [{}]

    def check(self, report: Report, context: ProjectCheckContext, **kwargs) -> None:
        """Check that no issues link to a feature with relationship 'Relates to'.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param kwargs: Additional parameters for the check.
        """
        for issues in context.issues_by_status.values():
            for issue in issues:
                for issuelink in issue.fields.issuelinks:
                    if issuelink.type.name != "Relates":
                        continue
                    if hasattr(issuelink, "inwardIssue"):
                        inward = str(issuelink.inwardIssue)
                        if inward.startswith("SP-"):
                            report.add_violation(
                                check_name="relates_to_feature",
                                issue_key=issue.key,
                                summary=issue.fields.summary,
                                details={"feature": inward},
                            )
                    elif hasattr(issuelink, "outwardIssue"):
                        outward = str(issuelink.outwardIssue)
                        if outward.startswith("SP-"):
                            report.add_violation(
                                check_name="relates_to_feature",
                                issue_key=issue.key,
                                summary=issue.fields.summary,
                                details={"feature": outward},
                            )


class IssuesInThisPiAreLinkedCheck(Check):
    """Check that every issue in this PI is linked."""

    parametrization = [
        {"status": "BACKLOG"},
        {"status": "To Do"},
        {"status": "In Progress"},
        {"status": "BLOCKED"},
        {"status": "Reviewing"},
        {"status": "Merge Request"},
        {"status": "READY FOR ACCEPTANCE"},
        {"status": "Done"},
    ]

    def check(
        self,
        report: Report,
        context: ProjectCheckContext,
        status: str,
        **kwargs,
    ) -> None:
        """Check that every issue in this PI is linked.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        current_pi = f"PI{context.pi}"
        issues_by_status = context.issues_by_status
        parentage = context.parentage

        for issue in issues_by_status.get(status, []):
            fix_versions = get_fix_versions(issue)
            if current_pi not in fix_versions:
                continue
            lower_labels = {label.lower() for label in issue.fields.labels}
            if lower_labels.intersection(UNLINKED_LABELS):
                continue

            if issue.key not in parentage:
                report.add_violation(
                    check_name=f"unlinked_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"status": status},
                )


class IssuesInThisPiHaveParentInThisPiCheck(Check):
    """Check that every issue in this PI has a parent in this PI."""

    parametrization = [
        {"status": "To Do"},
        {"status": "In Progress"},
        {"status": "BLOCKED"},
        {"status": "Reviewing"},
        {"status": "Merge Request"},
        {"status": "READY FOR ACCEPTANCE"},
        {"status": "Done"},
    ]

    def check(
        self,
        report: Report,
        context: ProjectCheckContext,
        status: str,
        **kwargs,
    ) -> None:
        """Check that every issue in this PI has a parent in this PI.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        current_pi = f"PI{context.pi}"
        issues_by_status = context.issues_by_status
        parentage = context.parentage
        client = context.client

        @functools.lru_cache
        def is_in_this_pi(issue_key):
            parent_issue = client.get_issue(issue_key)
            fix_versions = get_fix_versions(parent_issue)
            return current_pi in fix_versions

        for issue in issues_by_status.get(status, []):
            fix_versions = get_fix_versions(issue)
            if current_pi not in fix_versions:
                continue
            lower_labels = {label.lower() for label in issue.fields.labels}
            if lower_labels.intersection(UNLINKED_LABELS):
                continue
            if issue.key not in parentage:
                continue

            for _, link_target in parentage[issue.key]:
                if is_in_this_pi(link_target):
                    break
            else:
                report.add_violation(
                    check_name=f"parent_not_in_pi_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"status": status},
                )


class StatusIsConsistentWithParentStatusCheck(Check):
    """Check that issue status is consistent with parent status."""

    parametrization = [
        {
            "status": "BACKLOG",
            "consistent_parent_statuses": ["BACKLOG", "Identified"],
        },
        {
            "status": "To Do",
            "consistent_parent_statuses": [
                "To Do",
                "In Progress",
                "Implementing",
                "BLOCKED",
                "Identified",
            ],
        },
        {
            "status": "In Progress",
            "consistent_parent_statuses": ["In Progress", "Implementing", "BLOCKED"],
        },
        {
            "status": "BLOCKED",
            "consistent_parent_statuses": ["In Progress", "Implementing", "BLOCKED"],
        },
        {
            "status": "Reviewing",
            "consistent_parent_statuses": ["In Progress", "Implementing", "BLOCKED"],
        },
        {
            "status": "Merge Request",
            "consistent_parent_statuses": ["In Progress", "Implementing", "BLOCKED"],
        },
        {
            "status": "READY FOR ACCEPTANCE",
            "consistent_parent_statuses": [
                "In Progress",
                "Implementing",
                "BLOCKED",
                "READY FOR ACCEPTANCE",
            ],
        },
        {
            "status": "Done",
            "consistent_parent_statuses": [
                "In Progress",
                "Implementing",
                "BLOCKED",
                "READY FOR ACCEPTANCE",
                "Releasing",
                "Done",
                "Achieved",
                "NOT ACHIEVED",
                "Evaluated",
                "Discarded",
            ],
        },
    ]

    def check(
        self,
        report: Report,
        context: ProjectCheckContext,
        status: str,
        consistent_parent_statuses: list[str],
        **kwargs,
    ) -> None:
        """Check that issue status is consistent with parent status.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param consistent_parent_statuses: A list of consistent parent statuses.
        :param kwargs: Additional parameters for the check.
        """
        issues_by_status = context.issues_by_status
        parentage = context.parentage
        client = context.client

        @functools.lru_cache
        def get_parent_status(issue_key):
            parent_issue = client.get_issue(issue_key)
            return parent_issue.fields.status.name

        for issue in issues_by_status.get(status, []):
            if issue.key not in parentage:
                continue

            inconsistent_parents = []
            for _, parent_key in parentage[issue.key]:
                if get_parent_status(parent_key) not in consistent_parent_statuses:
                    inconsistent_parents.append(parent_key)
            if inconsistent_parents:
                report.add_violation(
                    check_name=f"inconsistent_parent_status_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={
                        "status": status,
                        "inconsistent_parents": inconsistent_parents,
                    },
                )
