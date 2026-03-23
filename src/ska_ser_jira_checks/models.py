"""Data models for Jira checks."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Violation:
    """A violation of a check."""

    check_name: str
    issue_key: str
    summary: str
    details: Dict[str, Any]


@dataclass
class Report:
    """A report containing check results."""

    project: str
    pi: int
    violations: Dict[str, List[Violation]] = field(default_factory=dict)
    overrides: Dict[str, List[str]] = field(default_factory=dict)
    used_overrides: Dict[str, List[str]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def add_violation(
        self,
        check_name: str,
        issue_key: str,
        summary: str,
        details: Dict[str, Any],
    ) -> None:
        """Add a violation to the report.

        :param check_name: The name of the check that failed.
        :param issue_key: The Jira issue key.
        :param summary: A brief summary of the issue.
        :param details: Additional details about the violation.
        """
        if issue_key in self.overrides.get(check_name, []):
            if issue_key not in self.used_overrides[check_name]:
                self.used_overrides[check_name].append(issue_key)
            return

        if check_name not in self.violations:
            self.violations[check_name] = []
        self.violations[check_name].append(
            Violation(check_name, issue_key, summary, details)
        )


@dataclass
class ProjectCheckContext:
    """Context for running project-specific Jira checks."""

    issues_by_status: Dict[str, List[Any]]
    pi: int
    team: set[str]
    project: str
    client: Any
    parentage: Dict[str, List[tuple[str, str]]]


@dataclass
class SkbCheckContext:
    """Context for running SKB-specific Jira checks."""

    team_created_skbs: List[Any]
    team_assigned_skbs: List[Any]
    pi: int
    client: Any


# pylint: disable=too-few-public-methods
class Check:
    """Base class for Jira checks."""

    parametrization: List[Dict[str, Any]] = []

    def check(self, report: Report, context: Any, **kwargs) -> None:
        """Run the check.

        :param report: The report to add violations to.
        :param context: The context containing issue data.
        :param kwargs: Additional parameters for the check.

        :raises NotImplementedError: If the method is not implemented.
        """
        raise NotImplementedError
