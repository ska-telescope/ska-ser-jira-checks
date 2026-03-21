"""Common pytest fixtures and test setup."""

# pylint: disable=redefined-outer-name
import os

import pytest

from ska_ser_jira_checks.main import load_overrides, run_checks


@pytest.fixture(scope="session")
def all_reports():
    """
    Generate all reports by running all checks.

    :return: a dictionary of reports keyed by project.
    """
    project = os.environ.get("JIRA_PROJECT")
    if not project:
        pytest.skip("JIRA_PROJECT environment variable not set.")

    start_date = os.environ.get("JIRA_START_DATE")

    overrides_file = os.environ.get("JIRA_OVERRIDES_FILE")
    overrides = load_overrides(overrides_file)
    return run_checks(project, start_date, overrides=overrides)


@pytest.fixture(scope="session")
def project_report(all_reports):
    """
    Fixture for the project-specific report.

    :param all_reports: The dictionary of all reports.
    :return: the project-specific report.
    """
    project = os.environ.get("JIRA_PROJECT")
    return all_reports[project]


@pytest.fixture(scope="session")
def skb_report(all_reports):
    """
    Fixture for the SKB-specific report.

    :param all_reports: The dictionary of all reports.
    :return: the SKB-specific report.
    """
    return all_reports["SKB"]


@pytest.fixture(scope="session")
def report(project_report):
    """
    Backward compatible fixture for the project-specific report.

    :param project_report: The project-specific report.
    :return: the project-specific report.
    """
    return project_report
