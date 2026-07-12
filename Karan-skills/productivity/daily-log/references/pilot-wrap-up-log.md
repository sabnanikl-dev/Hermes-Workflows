# Pilot Wrap-up Daily Log Notes

When a multi-agent or multi-repo pilot is finalized, the daily log should capture the high-level operational outcome, not raw PR numbers or temporary branch details.

## Include

- Which pilot/batch was wrapped.
- Major task classes completed, e.g. harness/spec, reusable template, skill library, tracker closeout.
- Verification category, e.g. PR merges verified and tracker issues moved to Done.
- Any durable process lesson, such as agent-agnostic harness docs or shared-workspace parallelism.

## Avoid

- Long lists of commit SHAs.
- Temporary branch names unless needed to understand the process.
- Stale task progress that will be irrelevant within a week.

## Example

```md
- Wrapped the multi-profile Kanban pilot across JMD and PAPI ops work.
- Merged the related GitHub PRs after user approval and verified merge state through GitHub.
- Posted Linear wrap-up comments and moved the pilot issues to Done.
- Captured the durable lesson that reusable harness docs must be agent-agnostic and that shared-repo mutation should be serialized or isolated by worktree.
```
