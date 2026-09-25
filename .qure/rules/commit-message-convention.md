---
name: Commit message Jira ID convention
status: active
---
Every commit in this repository must start its message with the Jira issue
key of the task the commit implements, followed by a colon and a short
description, e.g.:

    SCRUM-12: run apt-get update before installing Apache/PHP packages in CI

- The key must be the ID of the Jira issue the commit actually corresponds to
  (the task/story/bug being worked on), not a placeholder or an unrelated
  ticket.
- This lets Jira's Git integration automatically track the commit against
  that issue.
- If a commit's work has no corresponding Jira issue, ask the user for the
  correct issue key (or whether one should be created) before committing —
  do not omit the prefix and do not guess an ID.
