# ska-ser-jira-checks

ska-ser-jira-checks is a pytest suite
that checks the housekeeping status of your Jira project.

## Tests

### Test that every issue has been updated reasonably recently

This test fails if an issue has not been updated within a reasonable period of time.

For items in the BACKLOG, the limit is 90 days.
If an issue in the BACKLOG has not been updated in the last 90 days,
it's time to reassess this issue, and ask if it is still worth doing.
If so, add a comment that the issue has been reviewed and retained.
Otherwise, discard it.

For "To Do" items, the limit is 30 days.
If an issue exceeds the 30-day limit, ask whether this is still a task
that is part of the team plan, and which the team intends to do imminently.
If so, add a comment to that effect.
Otherwise, push it back to the BACKLOG, or discard it.

For items that are already in progress
("In Progress", "Reviewing", "BLOCKED", or "READY FOR ACCEPTANCE),
the limit is 30 days. Investigate why this issue has not progressed.

### Test that issues have an assignee

"BACKLOG" and "To Do" issues generally won't have an assignee,
but issues that are
"In Progress, "Reviewing", "READY FOR ACCEPTANCE", "Done", or "BLOCKED"
should.

### Test that no-one has too much work in progress (WIP)

This test fails if more than 4 "In Progress" issues are assigned to the same person.

### Test that no-one has too many BLOCKED issues

This test fails if more than 2 "BLOCKED" issues are assigned to the same person.

### Test that issues are assigned within the team

This test checks that all issues (that are not already "Done")
are assigned within the project team.

This is a useful check for when a team member leaves:
the test will fail if work remains assigned to that team member
after the Jira project membership has been updated to remove them.

**Note**: This test requires accessing a list of users
that belong to the "Developer" role of the project being checked.
This requires elevated permissions,
generally only held by the Scrum Master / Agile Coach
of the team that works on the project being checked.
When run by a user who lacks these permissions (such as in the CI pipeline)
this test is skipped.

### Test that everyone in the team has a ticket in progress

Test that everyone in the project team has a ticket "In Progress".

(This test might not be appropriate to all teams. This is yet to be determined.)

**Note**: This test requires accessing a list of users
that belong to the "Developer" role of the project being checked.
This requires elevated permissions,
generally only held by the Scrum Master / Agile Coach
of the team that works on the project being checked.
When run by a user who lacks these permissions (such as in the CI pipeline)
this test is skipped.

### Test that issues have descriptions

It's okay for a ticket in the BACKLOG to be lacking a description,
but once a ticket has been promoted to "To Do" or beyond,
a description should be required.

### Test that all issues have fixVersions

Issues in the BACKLOG need not be assigned to a PI (i.e. a fixVersion).
But promoting a issue to "To Do" indicates an intent to work on it imminently,
so 'To Do' issues should have a PI, as should issues that are 'In Progress' etc.

Strictly speaking, "Done" issues should have an fixVersion too;
but this test does not check 'Done' issues,
because the past is the past.

### Test that incomplete issues are assigned to the current or future PI

It's okay for "Done" issues to have an old fixVersion,
but other issues should link to a current or future fixVersion
(or not be linked to a fixVersion at all).

**TODO**: This test needs work: an issue can has multiple fixVersions.
If an issue fixVersion contains a current or future PI,
it shouldn't matter if it also contains an older PI.

### Test that every issue is child of a feature or relates to an objective

Within team projects, every issue should be
either the "Child of" a feature, or "Relates to" an objective.

### Test that no issues are child of an objective

Sometimes issues are mis-linked to be "Child of" an objective.

### Test that no issues relate to a feature

Sometimes issues are mis-linked to "Relates to" a feature.

### Test that no To Do or BACKLOG issues have commits

If an issue has commits, work has already started on it,
so it probably shouldn't be 'To Do' or 'Backlog'.

### Test that all READY FOR ACCEPTANCE issues have outcomes

Writing outcomes should be a pre-requisite to moving a ticket to RFA.

### Test that no READY FOR ACCEPTANCE or Done issues have unmerged MRs

Sometimes an issue is moved to READY FOR ACCEPTANCE or Done prematurely,
while that are still unmerged MRs.

While waiting for the MR to merge,
move the issue back to "In Progress" or "Reviewing" or "Blocked".
If the MR doesn't need to merge, close it.

### Test that there are not too many READY FOR ACCEPTANCE issues

If there are more than 9 READY FOR ACCEPTANCE issues,
your Product Owner needs to be prodded to review and accept them.

## Using this tool

### From the CI pipeline

The easiest way to use this tool is via its CI pipeline.

1. Go to the [Run Pipeline](https://gitlab.com/ska-telescope/ska-ser-jira-checks/-/pipelines/new) page.

2. Add a `JIRA_PROJECT` variable whose value is
   the slug of the project that you want to check,
   such as `MCCS`, `BANG`, `LOW`, etc.

3. Click "Run pipeline", wait for it to run,
   then examine the output of the `python-test` step.

**Note**: If your project is well unkempt,
and the list of failures dauntingly large,
you can go back to step 2 and also add a `JIRA_START_DATE` key,
with the value a date of the form `2024-09-11`
and all issues created before that date will be disregarded.

### Locally

1. Clone this repo.

2. Use `poetry install` to install into the environment of your choice.

3. Set appropriate values for these three environment variables:
   `JIRA_USERNAME`, `JIRA_PASSWORD` and `JIRA_PROJECT`.

4. Run `pytest`

**Note**: If you want to add your own tests to the test suite,
that are specific to your project and should not be checked in,
add them to a `test_custom.py` file.
This filename is already gitignored.

### Shortcut for users of the vscode remote container extension

This project has a devcontainer definition,
that loads environment variables from `.devcontainer/secrets.env`,
which is gitignored.
Create your own file of that name, with content like

```text
JIRA_USERNAME=my.username
JIRA_PASSWORD=SekretPa$$w0rd
JIRA_PROJECT=MYPROJ
```

and those variables will be set whenever you launch your devcontainer.
