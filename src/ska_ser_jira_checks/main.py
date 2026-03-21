"""Main entrypoint for Jira checks."""

import argparse
import importlib
import inspect
import os
import pkgutil
from collections import defaultdict
from datetime import date
from typing import Any, Dict, List, Type

import yaml

import ska_ser_jira_checks.checks.project
import ska_ser_jira_checks.checks.skb
from ska_ser_jira_checks.checks.utils import get_issues_by_status
from ska_ser_jira_checks.client import JiraClient
from ska_ser_jira_checks.models import (
    Check,
    ProjectCheckContext,
    Report,
    SkbCheckContext,
)


def get_current_pi() -> int:
    """Calculate current PI.

    :return: The current PI number.
    """
    delta = date.today() - date(2018, 9, 19)
    return delta.days // 91


def get_issue_parentage(
    issues: List[Any], project: str
) -> Dict[str, List[tuple[str, str]]]:
    """Get the parents of each issue.

    :param issues: The list of issues to process.
    :param project: The project key.

    :return: A dictionary mapping issue keys to a list of parent (type, key) tuples.
    """
    parentage = defaultdict(list)
    for issue in issues:
        epic = issue.fields.customfield_10006
        if epic is not None and epic.startswith(f"{project}-"):
            parentage[issue.key].append(("EPIC", epic))

        for issuelink in issue.fields.issuelinks:
            link_type = issuelink.type.name
            if hasattr(issuelink, "outwardIssue"):
                parent = str(issuelink.outwardIssue)
                if link_type != "Relates" or not parent.startswith("SPO-"):
                    continue
            elif hasattr(issuelink, "inwardIssue"):
                parent = str(issuelink.inwardIssue)
                if link_type == "Parent/Child":
                    if not parent.startswith("SP-"):
                        continue
                elif link_type == "Relates":
                    if not parent.startswith("SPO-"):
                        continue
                else:
                    continue
            else:
                continue
            parentage[issue.key].append((issuelink.type.name, parent))
    return parentage


def discover_checks(package: Any) -> List[Type[Check]]:
    """
    Dynamically discover all Check subclasses in the given package.

    :param package: The package to search for checks.

    :return: A list of Check subclasses.
    """
    check_classes = []
    for _, module_name, _ in pkgutil.walk_packages(
        package.__path__, package.__name__ + "."
    ):
        module = importlib.import_module(module_name)
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, Check) and obj is not Check:
                check_classes.append(obj)
    return check_classes


class NoAliasDumper(yaml.SafeDumper):
    """YAML dumper that doesn't use aliases."""

    def ignore_aliases(self, data: Any) -> bool:
        """
        Ignore aliases.

        :param data: The data to check for aliases.

        :return: True to ignore aliases.
        """
        return True


def save_report_to_yaml(report: Report, file_path: str) -> None:
    """
    Save the report to a YAML file.

    :param report: The report to save.
    :param file_path: The path to the file to save the report to.
    """
    # Create a simplified dict for YAML output
    report_dict = {
        "project": report.project,
        "pi": report.pi,
        "violations": {
            check_name: [
                {
                    "issue_key": v.issue_key,
                    "summary": v.summary,
                    "details": v.details,
                }
                for v in violations
            ]
            for check_name, violations in report.violations.items()
        },
    }

    unused_overrides = {}
    for check_name, issue_keys in report.overrides.items():
        used_for_check = report.used_overrides.get(check_name, [])
        unused_for_check = [k for k in issue_keys if k not in used_for_check]
        if unused_for_check:
            unused_overrides[check_name] = unused_for_check

    if unused_overrides:
        report_dict["unused_overrides"] = unused_overrides

    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(
            report_dict,
            f,
            sort_keys=False,
            Dumper=NoAliasDumper,
            width=1000,  # Prevent line wrapping for long summaries
        )


def load_overrides(file_path: str = None) -> Dict[str, List[str]]:
    """
    Load violation overrides from a YAML file.

    :param file_path: Path to the YAML file. If None, it will not load anything.

    :return: A dictionary of overrides.
    """
    if not file_path:
        return {}

    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# pylint: disable=too-many-locals
def run_checks(
    project: str, start_date: str = None, overrides: Dict[str, Any] = None
) -> Dict[str, Report]:
    """Run all Jira checks and produce two reports.

    :param project: The Jira project key.
    :param start_date: Optional start date for issues (YYYY-MM-DD).
    :param overrides: Optional dictionary of violation overrides.

    :return: A dictionary of Report objects keyed by project name.
    """
    client = JiraClient()
    pi = get_current_pi()
    overrides = overrides or {}

    project_overrides = overrides.get(project, {})
    skb_overrides = overrides.get("SKB", {})

    # Fetch project issues
    jql = f"project = {project}"
    if start_date:
        jql += f" AND createdDate > {start_date}"
    all_issues = client.search_issues(jql)
    issues_by_status = get_issues_by_status(all_issues)

    # Fetch team members
    try:
        team = client.get_team_members(project)
    except Exception:  # pylint: disable=broad-exception-caught
        print("Warning: Could not fetch team members. Skipping team-based checks.")
        team = set()

    # Pre-calculate parentage
    parentage = get_issue_parentage(all_issues, project)

    # Project checks
    project_report = Report(project=project, pi=pi, overrides=project_overrides)
    project_context = ProjectCheckContext(
        issues_by_status=issues_by_status,
        pi=pi,
        team=team,
        project=project,
        client=client,
        parentage=parentage,
    )
    project_checks = discover_checks(ska_ser_jira_checks.checks.project)
    for check_class in project_checks:
        checker = check_class()
        for params in checker.parametrization:
            checker.check(project_report, project_context, **params)

    # SKB Checks
    skb_report = Report(project="SKB", pi=pi, overrides=skb_overrides)
    jql_skb = "project = SKB"
    if start_date:
        jql_skb += f" AND createdDate > {start_date}"
    skb_issues = client.search_issues(jql_skb)

    team_created_skbs = []
    team_assigned_skbs = []
    for issue in skb_issues:
        if team and issue.fields.creator.name in team:
            team_created_skbs.append(issue)
        if team and issue.fields.assignee and issue.fields.assignee.name in team:
            team_assigned_skbs.append(issue)

    skb_context = SkbCheckContext(
        team_created_skbs=team_created_skbs,
        team_assigned_skbs=team_assigned_skbs,
        pi=pi,
        client=client,
    )
    skb_checks = discover_checks(ska_ser_jira_checks.checks.skb)
    for check_class in skb_checks:
        checker = check_class()
        for params in checker.parametrization:
            checker.check(skb_report, skb_context, **params)

    return {project: project_report, "SKB": skb_report}


def main():
    """Run the main entrypoint."""
    parser = argparse.ArgumentParser(description="Run Jira housekeeping checks.")
    parser.add_argument(
        "--project",
        default=os.environ.get("JIRA_PROJECT"),
        help="Jira project key.",
    )
    parser.add_argument(
        "--start-date",
        default=os.environ.get("JIRA_START_DATE"),
        help="Start date for issues.",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to save the reports (defaults to current directory).",
    )
    parser.add_argument(
        "--overrides",
        default=os.environ.get("JIRA_OVERRIDES_FILE"),
        help="Path to YAML file containing violation overrides.",
    )

    args = parser.parse_args()

    if not args.project:
        parser.error("Project must be specified via --project or JIRA_PROJECT env var.")

    overrides = load_overrides(args.overrides)
    if overrides:
        num_overrides = sum(len(v) for v in overrides.values() if isinstance(v, dict))
        print(f"Loaded {num_overrides} overrides from {args.overrides}.")

    reports = run_checks(args.project, args.start_date, overrides)

    project_output = os.path.join(args.output_dir, f"{args.project}-report.yaml")
    save_report_to_yaml(reports[args.project], project_output)
    print(f"Project report saved to {project_output}")

    skb_output = os.path.join(args.output_dir, "SKB-report.yaml")
    save_report_to_yaml(reports["SKB"], skb_output)
    print(f"SKB report saved to {skb_output}")


if __name__ == "__main__":
    main()
