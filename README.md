# ska-ser-jira-checks

`ska-ser-jira-checks` is a tool and test suite that checks the housekeeping status of your Jira project. It automatically discovers and runs all check classes defined in the `checks` package. It produces machine-readable reports in YAML format, and includes a pytest suite that asserts on the results of these reports.

## Housekeeping Checks

The tool performs several categories of checks:

### Age Checks
- **Update Frequency**: Fails if an issue has not been updated within a reasonable period (limits vary by status, e.g., 120 days for BACKLOG, 30 days for In Progress).

### Assignment Checks
- **Assignee Requirement**: Ensures that active issues ("In Progress", "Reviewing", etc.) have an assignee.
- **WIP Limits**: Fails if an individual team member has more than 4 "In Progress" issues.
- **Blocked Limits**: Fails if an individual team member has more than 2 "BLOCKED" issues.
- **Team Membership**: Verifies that work is assigned to current project team members.
- **Active Engagement**: Checks that every team member has at least one ticket "In Progress".

### Content Checks
- **Descriptions**: Required for any ticket promoted beyond "BACKLOG".
- **fixVersions**: Ensures issues are assigned to a Program Increment (PI).
- **PI Currency**: Incomplete issues must be assigned to the current or a future PI.

### Link and Consistency Checks
- **Link Integrity**: Prevents mis-linking issues as "Child of" an objective or "Relates to" a feature.
- **Parentage**: Ensures issues in the current PI are linked to an appropriate parent (Epic, Feature, or Objective).
- **Status Consistency**: Verifies that an issue's status is consistent with its parent's status (e.g., an "In Progress" issue shouldn't have a "Done" parent).

### Workflow Checks (RFA & Commits)
- **Commits on Inactive Issues**: Fails if "To Do" or "BACKLOG" issues have associated commits.
- **RFA Outcomes**: All "READY FOR ACCEPTANCE" issues must have recorded outcomes.
- **Merged MRs**: Active issues should not have only merged/closed MRs.
- **Open MRs**: "READY FOR ACCEPTANCE" or "Done" issues should not have unmerged MRs.
- **RFA Queue Size**: Fails if there are more than 9 issues waiting in "READY FOR ACCEPTANCE".

### SKB Checks
- **Component Allocation**: Every SKB must be allocated to a component.
- **Aggressive Deadlines**: SKBs have tighter update limits to encourage prompt action.
- **PI Linking**: SKBs must be linked to a feature or objective in the current PI.

## Using this tool

1. **Clone the repo.**
2. **Install dependencies**:
   ```bash
   uv sync
   ```
3. **Configure environment**: Create a `.env` file with your credentials and target project:
   ```text
   JIRA_API_TOKEN=your_token_here
   # OR
   JIRA_USERNAME=your_username
   JIRA_PASSWORD=your_password

   JIRA_PROJECT=LOW
   ```
4. **Generate reports**:
   ```bash
   make report
   ```
   This will produce `<PROJECT>-report.yaml` and `SKB-report.yaml` in the `reports/` directory.
5. **Run tests**:
   ```bash
   make python-test
   ```

### Via CLI

The tool provides a CLI entrypoint:
```bash
uv run ska-ser-jira-checks --project LOW --output-dir ./my-reports
```

## Architecture

The tool is organized as a Python package `ska_ser_jira_checks`:
- `main.py`: Entrypoint and report generation logic.
- `models.py`: Data models for violations, reports, and check contexts.
- `checks/`: Modular check implementations grouped by `project` and `skb`.
  - Each check is a class inheriting from `Check`.
  - Checks specify their own `parametrization` for multiple runs with different arguments.
