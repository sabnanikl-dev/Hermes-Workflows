# Reviewing agent-launcher OS and capability boundaries

Use this reference when a technical artifact or PR claims that an autonomous builder/reviewer receives only narrow authority, cannot reveal credentials, is read-only, or is fully terminated by a timeout. These are OS-boundary claims, not ordinary application invariants.

## Core distinctions

### Environment scrubbing is not process isolation

A synthetic `HOME`, an allowlisted environment, redirected Git/GitHub config, and removed token variables prevent ambient discovery. They do **not** stop a same-UID process with Bash or file tools from:

- opening an absolute credential/config path;
- inspecting same-UID process state where the OS permits it;
- invoking unreviewed executables from an inherited `PATH`;
- connecting to another same-UID Unix socket;
- altering owner-writable runtime files outside its worktree.

Review environment composition and OS-enforced reachability as separate acceptance claims. If the contract says prompt injection cannot reveal credentials, environment-only proof is insufficient unless the contract explicitly narrows that claim.

### Unix permissions are user isolation, not lane isolation

A random AF_UNIX socket in a `0700` directory with a `0600` socket is protected from *other users*. Two lanes running as the same UID can normally discover and connect to each other's sockets. A lane-bound capability channel needs a structural discriminator another lane cannot obtain, such as:

- an inherited connected file descriptor instead of a discoverable listener;
- a per-launch authenticator plus validated peer/process identity;
- an OS sandbox that allows only the exact lane socket;
- serialization that forbids concurrent same-UID channels until a real negative test proves isolation.

Do not describe random paths or owner mode bits as lane authentication.

### Process groups are not complete lifetime domains

`start_new_session=True` plus `killpg()` handles ordinary descendants, including orphaned servers that remain in the original group. A descendant can call `setsid()` and leave that group. A strict claim that no work survives timeout/cancellation requires a stronger primitive such as a container process namespace, cgroup, job object, VM, or equivalent supervisor-owned domain.

If that primitive is unavailable, classify the result honestly:

- **Continue:** the live platform supplies and proves the required domain;
- **Narrow:** preserve process-group cleanup as defense in depth and move full lifetime containment to a downstream qualification gate with explicit human approval;
- **Stop:** the current contract requires the stronger guarantee and cannot pass on this platform.

Disclosure alone does not close an acceptance criterion.

## Claude Code CLI sandboxing

Using Claude Code CLI does not automatically solve these boundaries. For security-sensitive lanes, use code-owned strict sandbox settings rather than relying on prompts or permission mode alone:

- `sandbox.enabled: true`
- `sandbox.failIfUnavailable: true`
- `sandbox.allowUnsandboxedCommands: false`
- filesystem `denyRead` outside approved roots and narrow `allowRead` for the exact worktree/runtime inputs;
- narrow write roots per role;
- deny external network and unrelated Unix sockets; permit only the exact broker endpoint when required.

Claude Code's OS sandbox governs **Bash and Bash descendants**. Built-in file tools such as Read/Edit/Write are governed by Claude's permission system instead. A launcher claiming OS-level read confinement must remove those tools, add equivalent hard-deny permission rules, or prove their access boundary separately. Keep unsandboxed fallback disabled.

Strict Bash sandboxing can make an escaped descendant much less dangerous because the inherited filesystem/network sandbox remains, but it does not by itself prove that the process no longer exists after the wall-clock budget.

## Capability-broker lifecycle

A closed operation vocabulary and bound argv composition are necessary but not sufficient. Review all of these:

1. **Authentication:** can another lane/run reach the channel?
2. **Request schema:** can callers name repo, PR, ref, commit, event, force flag, or executable?
3. **Operation budget:** is it role/phase-specific and bounded?
4. **Handler lifecycle:** are accepted requests tracked and drained?
5. **Shutdown:** does close reject new work and wait for every in-flight handler and broker subprocess?
6. **Readback ordering:** can a push/comment/review finish after lane failure, worktree cleanup, or final reporting?
7. **Credential custody:** can the child reacquire the broker credential from files, process state, inherited PATH tools, or ambient orchestration commands?

`socketserver.Threading*` with daemon request threads is a common trap: stopping the accept loop does not necessarily join active handlers. Add a blocking-runner test proving `close()` cannot return while an accepted operation remains active.

## Reviewer isolation proof

A fresh worktree plus `git status --porcelain` is not byte-level proof. A same-owner reviewer can restore write bits, alter tracked bytes, and hide changes with index flags such as `skip-worktree` or `assume-unchanged`; it can also modify shared runtime/PATH files while leaving the worktree clean.

For strong exact-head proof:

- give each lane a fresh runtime directory as well as a fresh worktree;
- resolve trusted executables to absolute paths before launching untrusted work;
- remove/verify one lane's runtime before constructing the next;
- compare tracked working-tree bytes to the bound commit independently of mutable index hints;
- reject index/config changes and unexpected untracked files;
- use an enforceable read-only sandbox/mount when the contract requires immutable bytes.

## Changed-path containment

Never infer scope containment from the builder's `ADDRESSED=` lines, final marker, or a clean committed worktree. Compute the actual committed delta from the frozen old head to the reported new head and compare it to an explicit allowed-path policy. Add a former-red case where valid blocker IDs accompany an unrelated committed file.

## Minimum adversarial probes

For a security-sensitive launcher repair, include real probes for:

- absolute-path read of a fake secret outside HOME/worktree;
- same-UID cross-channel request against another concurrent channel;
- direct attempts to merge, push another ref/repository, or submit a non-comment review;
- a self-`setsid` descendant surviving normal exit and timeout;
- an accepted slow broker operation during channel close;
- shared-runtime modification affecting a later lane;
- hidden tracked-file mutation using index flags;
- unrelated committed path with otherwise valid blocker markers.

Use fake credentials and disposable local repos/sockets. Do not inspect real secrets.

## Review-loop adjudication

Separate findings into:

- **code-local repairs** — request validation, handler draining, per-lane runtime, byte verification, diff containment;
- **platform primitives** — filesystem/process isolation, separate UID/container/cgroup/job domain;
- **contract decisions** — whether a disclosed platform limitation is accepted as Narrow or still blocks the current issue.

At the repair/re-review cap, do not keep adding apparatus or silently redefine the threshold. Freeze the evidence, ask the human to Continue/Narrow/Stop, update the governing contract and downstream qualification work, then resume only against that explicit decision.
