"""SKB checks for Jira issues."""

# pylint: disable=too-few-public-methods,arguments-differ
import datetime
import functools

from ska_ser_jira_checks.checks.utils import get_assignee, get_fix_versions
from ska_ser_jira_checks.constants import UNLINKED_LABELS
from ska_ser_jira_checks.models import Check, Report, SkbCheckContext


class SkbsHaveComponentCheck(Check):
    """Check that every SKB has been allocated to a component."""

    parametrization = [
        {"status": "Identified"},
        {"status": "In Assessment"},
        {"status": "Assigned"},
    ]

    def check(
        self, report: Report, context: SkbCheckContext, status: str, **kwargs
    ) -> None:
        """Check that every SKB has been allocated to a component.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        for issue in context.team_created_skbs:
            if issue.fields.status.name != status:
                continue
            if not issue.fields.components:
                report.add_violation(
                    check_name=f"skb_no_component_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={
                        "status": status,
                        "creator": issue.fields.creator.name,
                    },
                )


class SkbNotTooOldCheck(Check):
    """Check that every SKB has been updated reasonably recently."""

    parametrization = [
        {"status": "Identified", "age_limit": 7},
        {"status": "In Assessment", "age_limit": 7},
        {"status": "Assigned", "age_limit": 14},
        {"status": "In Progress", "age_limit": 30},
        {"status": "BLOCKED", "age_limit": 7},
        {"status": "Validating", "age_limit": 2},
    ]

    def check(
        self,
        report: Report,
        context: SkbCheckContext,
        status: str,
        age_limit: int,
        **kwargs,
    ) -> None:
        """Check that every SKB has been updated reasonably recently.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param age_limit: The maximum age in days.
        :param kwargs: Additional parameters for the check.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        deadline = now - datetime.timedelta(days=age_limit)

        for issue in context.team_assigned_skbs:
            if issue.fields.status.name != status:
                continue
            updated = datetime.datetime.strptime(
                issue.fields.updated, "%Y-%m-%dT%H:%M:%S.%f%z"
            )
            if updated < deadline:
                report.add_violation(
                    check_name=f"skb_too_old_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={
                        "status": status,
                        "age_days": (now - updated).days,
                        "assignee": get_assignee(issue),
                    },
                )


class SkbsLinkedToPiFeatureOrObjectiveCheck(Check):
    """Check that SKBs are linked to a feature or objective in this PI."""

    parametrization = [
        {"status": "Identified"},
        {"status": "In Assessment"},
        {"status": "Assigned"},
        {"status": "In Progress"},
        {"status": "BLOCKED"},
        {"status": "Validating"},
    ]

    def check(
        self,
        report: Report,
        context: SkbCheckContext,
        status: str,
        **kwargs,
    ) -> None:
        """Check that SKBs are linked to a feature or objective in this PI.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param status: The status to check.
        :param kwargs: Additional parameters for the check.
        """
        current_pi = f"PI{context.pi}"
        client = context.client

        @functools.lru_cache
        def is_in_this_pi(issue_key):
            parent_issue = client.get_issue(issue_key)
            fix_versions = get_fix_versions(parent_issue)
            return current_pi in fix_versions

        for issue in context.team_assigned_skbs:
            if issue.fields.status.name != status:
                continue
            lower_labels = {label.lower() for label in issue.fields.labels}
            if lower_labels.intersection(UNLINKED_LABELS):
                continue

            linked = False
            for issuelink in issue.fields.issuelinks:
                if (
                    issuelink.type.name == "Parent/Child"
                    and hasattr(issuelink, "inwardIssue")
                    and str(issuelink.inwardIssue).startswith("SP-")
                    and is_in_this_pi(str(issuelink.inwardIssue))
                ):
                    linked = True
                    break

                if issuelink.type.name == "Relates":
                    if (
                        hasattr(issuelink, "inwardIssue")
                        and str(issuelink.inwardIssue).startswith("SPO-")
                        and is_in_this_pi(str(issuelink.inwardIssue))
                    ):
                        linked = True
                        break
                    if (
                        hasattr(issuelink, "outwardIssue")
                        and str(issuelink.outwardIssue).startswith("SPO-")
                        and is_in_this_pi(str(issuelink.outwardIssue))
                    ):
                        linked = True
                        break

            if not linked:
                report.add_violation(
                    check_name=f"skb_not_linked_to_pi_{status}",
                    issue_key=issue.key,
                    summary=issue.fields.summary,
                    details={"status": status, "assignee": get_assignee(issue)},
                )
