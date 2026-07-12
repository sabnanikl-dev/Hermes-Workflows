# Blocker Correction Comments

Use this pattern when an investigation changes the root blocker after Linear has already received an earlier/stale status comment.

## Trigger

- A previous Linear comment named the wrong blocker, dependency, project, credential, or owner.
- A later verification step proves the earlier blocker is resolved or was caused by using the wrong context.
- The issue should remain open/in review because a different human/account/data blocker remains.

## Pattern

1. Do not edit history silently. Add a new corrective comment that clearly supersedes the stale comment.
2. Name the corrected root cause first, then explain the stale interpretation briefly.
3. Include verification evidence in bullets:
   - exact project/client/account/context used now
   - API or system call that succeeded
   - API or system call that still fails, including non-secret error class
   - current blocker owner/action
4. Keep status aligned with reality:
   - `In Review` when Hermes work is paused on human/account review
   - `In Progress` only while Hermes is actively executing
   - `Done` only after the blocker is resolved and acceptance criteria are verified
5. Explicitly state any non-actions when approval gates matter: no account mutation, no publish/deploy, no paid action, no public-facing change.
6. Re-query the issue after commenting and verify the latest comment body plus state.

## Comment skeleton

```md
Status correction after re-verification:

- Earlier blocker: <what prior comment said>.
- Corrected blocker: <current blocker>.
- Verified now:
  - <context/project/account used>
  - <call/check succeeded>
  - <call/check still blocked + non-secret error class>
- Human/account action needed: <specific owner/action>.

No <approval-gated mutations> were performed.
```

## Pitfalls

- Do not overwrite the stale blocker by only changing docs; Linear readers need an explicit corrective comment.
- Do not mark an issue Done when only the API/client/scope layer is fixed but data access or human permission is still missing.
- Do not paste OAuth codes, tokens, client secrets, or full credential payloads into Linear; project IDs, account emails, token file paths, and non-secret client prefixes are usually enough for reproducibility.
