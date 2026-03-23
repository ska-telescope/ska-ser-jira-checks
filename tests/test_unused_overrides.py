"""Test for unused overrides."""

import pytest


def test_no_unused_overrides(all_reports):
    """Test that all specified overrides are used in at least one report.

    :param all_reports: The dictionary of all generated reports.
    """
    if not all_reports:
        pytest.skip("No reports generated.")

    # Collect all specified and used overrides across all reports
    all_overrides = {}
    all_used = {}
    for report in all_reports.values():
        # Specified overrides
        for check_name, keys in report.overrides.items():
            if check_name not in all_overrides:
                all_overrides[check_name] = set()
            all_overrides[check_name].update(keys)

        # Used overrides
        for check_name, keys in report.used_overrides.items():
            if check_name not in all_used:
                all_used[check_name] = set()
            all_used[check_name].update(keys)

    if not all_overrides:
        pytest.skip("No overrides specified.")

    # Find unused overrides
    unused = {}
    for check_name, keys in all_overrides.items():
        used_for_check = all_used.get(check_name, set())
        unused_for_check = [k for k in keys if k not in used_for_check]
        if unused_for_check:
            unused[check_name] = sorted(unused_for_check)

    if unused:
        msg = "The following overrides are unused and should be removed:\n"
        for check_name, keys in unused.items():
            msg += f"- {check_name}: {', '.join(keys)}\n"
        pytest.fail(msg)
