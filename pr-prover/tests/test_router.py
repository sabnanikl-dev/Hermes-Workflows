"""The skill is a router, the contracts are contracts, and the tool is only the tool.

Four properties are worth holding still. The skill must stay a thin judgment
surface — trigger, routing, roles, taxonomy, cap, conditional references, merge
authority — because the previous version failed by growing into a procedure
manual nobody could keep true. The route it names must actually be runnable
from this no-install repository. The conditionally loaded references must stay
domain lessons rather than a second, conflicting prose implementation of the
lifecycle the router and ``MISSION.md`` own. And the shipped tool must stay the
small trusted-agent orchestrator it is: the zero-trust capability broker,
sandbox semantics model, runtime attestation, and container qualification that
were explored and rejected must not reappear by drift.

The repo-native contracts (``AGENTS.md`` and ``pr-prover/MISSION.md``) must
also stay discoverable, linked, and truthful about what is shipped — including
a status column that cannot be flattened to "everything shipped" without a
test failing.

The scans deliberately describe the surface that exists on current ``main``.
Nothing here assumes a later slice's module has already landed.
"""
from __future__ import annotations

import json
import os
import re
import unittest
from collections import Counter
from pathlib import Path
from typing import NamedTuple

REPO = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO / "Karan-skills" / "software-development" / "autonomous-pr-prover"
SKILL = SKILL_DIR / "SKILL.md"
REFERENCES = SKILL_DIR / "references"
PR_PROVER = REPO / "pr-prover"
AGENTS = REPO / "AGENTS.md"
MISSION = PR_PROVER / "MISSION.md"

# The one runnable route. There is no install step, so a bare ``pr-prover``
# command is exactly the failure this constant exists to pin down.
LAUNCHER = "pr-prover/bin/pr-prover"

# The shipped surface: what a user of this tool actually gets. The tests
# directory is excluded because this file necessarily names the machinery it is
# scanning for, and the two contract documents are excluded because naming the
# rejected apparatus in order to forbid it is their entire job — they get their
# own, stricter test below.
SHIPPED = (
    *sorted((PR_PROVER / "src").rglob("*.py")),
    *sorted((PR_PROVER / "examples").glob("*.json")),
    PR_PROVER / "README.md",
    PR_PROVER / "bin" / "pr-prover",
    SKILL,
)

# Every markdown document this slice makes mutually discoverable.
MARKDOWN = (AGENTS, MISSION, REPO / "README.md", PR_PROVER / "README.md", SKILL)

REJECTED = (
    "capability broker",
    "capabilitybroker",
    "lane secret",
    "lane_secret",
    # Plain "bearer" is legitimate in the redaction rules, so the scan looks
    # for the per-lane credential concept instead.
    "bearer secret",
    "per-lane secret",
    "channel authentication",
    "sandbox-exec",
    "seatbelt",
    "sandboxpolicy",
    "mac envelope",
    "attestation",
    "byte fingerprint",
    "cgroup",
    "job object",
    "job_object",
    "detached descendant",
    "telegram",
    "approval grammar",
)

# The core of the thin tool as it exists on current main. Later slices may add
# modules; this list is what must not go missing.
CORE_MODULES = (
    "__init__.py",
    "__main__.py",
    "cli.py",
    "commands.py",
    "config.py",
    "errors.py",
    "findings.py",
    "github.py",
    "loop.py",
    "redaction.py",
    "report.py",
    "state.py",
    "verdicts.py",
    "worktrees.py",
)

# Proof-map rows whose status must stay qualified on this head. Anything else
# must read exactly "shipped". Flattening the column in either direction — the
# demonstrated "mark every row shipped" mutation, or a blanket "owed" — fails.
QUALIFIED_INVARIANTS = ("M2", "M4", "M5", "M6", "M7", "M8", "M10", "M13")

# Lifecycle prose the references must not carry. The router and ``MISSION.md``
# own the A → B → Integration Auditor lifecycle, and ``pr-prover`` owns reviewer
# publication, transport, credentials, and GitHub readback. A reference that
# restates any of it becomes a second, conflicting implementation in prose.
CONFLICTING_LIFECYCLE = (
    r"\bA/B\b",
    r"Reviewer A and (?:Reviewer )?B\b",
    r"both role-signed reviews",
    r"\bgh (?:api|pr|auth)\b",
    r"\bGH_TOKEN\b",
    r"REVIEWER_TOKEN",
    r"--request-changes",
    r"under (?:the )?reviewer identity",
    r"\bheadRefOid\b",
    r"\blatestReviews\b",
    r"\breviewDecision\b",
)


class _Directive(NamedTuple):
    """One ordinary-prose lifecycle instruction the references must not carry.

    Deliberately no co-located sample. The previous shape paired each pattern
    with an example sentence and then proved the pattern against that same
    sentence, which is a tautology: three independent lanes each showed the
    scan returning nothing for ordinary synonyms of the very instructions it
    claimed to guard, while every focused test stayed green. Proof now comes
    from ``LIFECYCLE_CORPUS``, a data file no rule here was written from.
    """

    name: str
    pattern: str


def _one_of(*alternatives: str) -> str:
    return "(?:" + "|".join(alternatives) + ")"


# The command spellings above are only half the failure. Deleting ``gh pr`` from
# a reference while leaving "post it on the PR, hand it to the builder, aim the
# next review pass" behind keeps the same parallel procedure, written in
# English — which is exactly the false pass the auditor demonstrated by
# appending one sentence to a clean reference and watching the scan stay green.
#
# The rules below are composed from concept vocabularies rather than written one
# sentence at a time, because a list built around one set of spellings is what
# ordinary synonyms walked straight through. A lifecycle *action* (publish, hand
# off, review, control the cycle) is paired with the lifecycle *target* it acts
# on, and the pair only counts in an instruction mood: a clause-initial
# imperative, its negation, or a causative such as "have Codex inspect …".
#
# Mood is what keeps this from becoming a keyword ban. A reference may
# *describe* a PR comment, a builder, Claude, a review, or the cycle cap as
# domain evidence; banning those nouns would gut the lessons the files exist
# for. What it may not do is *instruct* the operator to publish, hand off,
# sequence a review, or control the cycle — those belong to ``MISSION.md`` and
# ``pr-prover``.
#
# This is pattern matching over normalized clauses, not language understanding.
# It is proportional to what it guards: fifteen short domain references, checked
# against an independent corpus that decides whether the rules are broad enough.

# Sentence structure.
_MOOD = r"^(?:do not |don't |never |avoid )?"
# "re-post", "re-run", and "re-review" are the same instruction as their bases.
_AGAIN = r"(?:re-?)?"
_GAP = r"[^.;:!?]{0,120}"

# Lifecycle actions, grouped by the concern each one exercises.
_PUBLISH = _one_of(
    "post", "publish", "add", "record", "write", "note", "file", "submit",
    "attach", "leave", "drop", "put", "place", "relay", "announce", "comment",
    "push", "copy", "move",
)
_HANDOFF = _one_of(
    "give", "hand", "pass", "send", "route", "forward", "deliver", "dispatch",
    "launch", "prompt", "point", "assign", "task", "ask", "tell",
)
_REVIEWING = _one_of(
    "review", "audit", "inspect", "assess", "evaluate", "examine", "check",
    "run", "repeat", "redo", "schedule", "request", "aim", "direct", "target",
    "order", "sequence",
)
_CYCLING = _one_of(
    "start", "begin", "open", "allow", "permit", "use", "run", "spend",
    "grant", "limit", "cap", "restrict", "repeat", "take",
)
_CAUSATIVE = _one_of(
    "have", "ask", "get", "make", "tell", "let", "require", "instruct", "direct",
)

# Who work is handed to. Agent-shaped noun phrases only, so "scope the fix to
# the visual blocker" stays the domain sentence it is.
_AGENT = _one_of(
    "claude", "codex",
    r"(?:the|a|another|one)\s+(?:quiet\s+)?builder(?:\s+(?:lane|agent|pass|session))?",
    r"(?:the|a|another)\s+fixer",
    r"(?:the|a|another)\s+(?:fix|repair|corrective|correction|builder|build)\s+"
    r"(?:lane|agent|pass|round|session)",
    r"(?:fix|repair|corrective|builder|build)\s+lanes?",
)
# A published lifecycle artifact: a GitHub-ish venue word plus an artifact word.
_PR_ARTIFACT = (
    _one_of("pr", "prs", "pull[- ]request", "github", "blocking", "reviewer",
            "review", "closeout", "adjudication", "issue")
    + r"\b[^.;:!?]{0,40}?\b"
    + _one_of("comments?", "threads?", "discussion", "conversation", "artifact",
              "bus", "body", "description")
)
_PR_VENUE = _one_of("pr", "pull[- ]request", "github", "issue")
# What a review instruction points at: the next pass, or the head it runs on.
_REVIEW_TARGET = _one_of(
    r"(?:new|newest|updated|latest|repaired|fixed|corrected|next|revised)\s+"
    r"(?:exact\s+)?(?:head|revision|commit|diff|version)",
    r"(?:fresh|new|another|second|follow-?up)\s+(?:audit|review|pass)",
    r"review\s+(?:pass(?:es)?|rounds?|lanes?|prompts?|sequence)",
    r"(?:reviewer|review)\s+lanes?",
    r"(?:integration|three)\s+reviews?",
    r"a,?\s*b,?\s*and\s+integration\s+reviews?",
)
# What a cycle instruction counts.
_CYCLE_TARGET = _one_of(
    r"(?:repair|fix|correction|corrective|builder|review)\s+"
    r"(?:rounds?|cycles?|passes|pass)",
    r"cycle[- ]cap",
    r"another\s+(?:fix\s+|repair\s+)?cycle",
)

MANUAL_LIFECYCLE_DIRECTIVES = (
    _Directive(
        "publish-a-pr-artifact",
        _MOOD + _AGAIN + _PUBLISH + r"\b" + _GAP + r"\b" + _PR_ARTIFACT + r"\b",
    ),
    _Directive(
        "put-it-on-the-pr",
        _MOOD + _AGAIN + _PUBLISH + r"\b" + _GAP
        + r"\b(?:on|onto|to|into|in|under)\s+(?:the|this|that|a|an)\s+"
        + _PR_VENUE + r"\b",
    ),
    _Directive(
        "edit-the-pr-metadata",
        _MOOD
        + _one_of("update", "edit", "rewrite", "correct", "amend", "revise")
        + r"\b" + _GAP + r"\b" + _one_of("pr", "pull[- ]request")
        + r"\s+(?:body|title|description)\b",
    ),
    _Directive(
        "hand-work-to-an-agent",
        _MOOD + _AGAIN + _HANDOFF + r"\b" + _GAP + r"\b" + _AGENT + r"\b"
        + r"|\bhand(?:s|ed|ing)?(?:\s+off)?\b[^.;:!?]{0,60}\bover\b"
        + r"|" + _MOOD + r"escalate\b[^.;:!?]{0,60}\b(?:karan|hermes)\b",
    ),
    _Directive(
        "direct-the-next-review",
        _MOOD + _AGAIN + _REVIEWING + r"\b" + _GAP + r"\b" + _REVIEW_TARGET + r"\b"
        + r"|^(?:the\s+)?(?:review|reviewer)\s+(?:lanes?|prompts?|passes)\s+"
        r"(?:should|must|need to|have to|will|shall)\b"
        + r"|\bask the (?:review )?lanes\b",
    ),
    _Directive(
        "have-an-agent-do-the-work",
        _MOOD + _CAUSATIVE + r"\s+(?:all\s+)?(?:the\s+|each\s+)?(?:three\s+)?"
        + _one_of(_AGENT, "reviewers?", r"(?:review|reviewer)\s+lanes?",
                  "auditors?", "integration auditor")
        + r"\b[^.;:!?]{0,60}\b" + _AGAIN
        + _one_of("review", "inspect", "assess", "evaluate", "examine", "audit",
                  "check", "look", "repair", "fix", "correct", "address",
                  "handle", "redo", "repeat")
        + r"\b",
    ),
    _Directive(
        "control-the-repair-cycle",
        _MOOD + _AGAIN + _CYCLING + r"\b" + _GAP + r"\b" + _CYCLE_TARGET + r"\b"
        + r"|\b(?:no more than|at most|not more than|up to)\s+"
        r"(?:one|two|three|four|\d+)\s+[^.;:!?]{0,30}\b" + _CYCLE_TARGET + r"\b"
        + r"|^respect the (?:cycle|fix)[- ]cap\b"
        + r"|\bif another (?:fix |repair )?cycle is needed\b"
        + r"|\bobtain explicit (?:human|karan)[a-z' ]{0,12}approval before continuing\b"
        + r"|\b(?:two|three|\d+) (?:fix |repair )?cycles,? (?:maximum|max)\b",
    ),
)

_FENCE = re.compile(r"^```")
_LIST_MARKER = re.compile(r"^(?:[-*+]|\d+[.)])\s+")
_MARKUP = re.compile(r"[*_`>#\[\]]")
# ", then …" and ", and then …" open a second instruction inside one sentence.
_CLAUSE_BREAK = re.compile(r"(?<=[.;:!?])\s+|\s+—\s+|,\s+(?=(?:and\s+)?then\b)")
_SMART = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})
# "If Karan expresses the preference in chat, put it on the PR first" and "On
# the updated head, repeat the reviews" are the same imperatives as their bare
# forms; a conditional or prepositional lead-in must not hide the verb from a
# clause-anchored match.
_LEAD_IN = re.compile(
    r"^(?:if|when|once|whenever|after|before|unless|while|where|for|on|in|at|"
    r"upon|during|from|with|as|given|assuming|following)\b[^,]{0,140},\s*"
)
_LEAD_ADVERB = re.compile(
    r"^(?:and\s+)?(?:also|then|next|now|first|always|finally|instead|again|"
    r"please|so)\b[,\s]+"
)


def prose_clauses(text: str) -> list[str]:
    """Split Markdown prose into normalized clause openings.

    Fenced code, table rows, and list/emphasis markup are dropped: the scan is
    about instructions written to a human operator, and a probe sketch or a
    boundary matrix row is domain content, not a procedure. What survives is
    lowercased, whitespace-collapsed, and stripped of lead-ins, so mood can be
    read off the opening word instead of off one particular spelling.
    """
    clauses: list[str] = []
    fenced = False
    for line in text.translate(_SMART).splitlines():
        stripped = line.strip()
        if _FENCE.match(stripped):
            fenced = not fenced
            continue
        if fenced or not stripped or stripped.startswith("|"):
            continue
        stripped = _MARKUP.sub("", _LIST_MARKER.sub("", stripped)).strip().lower()
        for clause in _CLAUSE_BREAK.split(re.sub(r"\s+", " ", stripped)):
            clause = clause.strip()
            while clause:
                clauses.append(clause)
                trimmed = _LEAD_ADVERB.sub("", _LEAD_IN.sub("", clause)).strip()
                if trimmed == clause:
                    break
                clause = trimmed
    return clauses


def lifecycle_directives_in(text: str) -> list[tuple[str, str]]:
    """Every (directive name, offending clause) pair the prose scan finds."""
    return [
        (directive.name, clause)
        for clause in prose_clauses(text)
        for directive in MANUAL_LIFECYCLE_DIRECTIVES
        if re.search(directive.pattern, clause)
    ]


# The independent oracle. It is a data file on purpose: it holds sentences and
# provenance, never patterns, so the scan above cannot be "proved" by the
# examples it was built from. Every mutation the three lanes reported at
# 5136419 is in it, alongside variants written from ordinary English.
LIFECYCLE_CORPUS = json.loads(
    (Path(__file__).resolve().parent / "lifecycle_corpus.json").read_text(encoding="utf-8")
)

# The reason each reference is kept. A rewrite that strips the conflicting
# lifecycle prose must not also strip the domain lesson, and the mapping's key
# set doubles as the expected reference inventory.
PRESERVED_LESSONS = {
    "static-site-current-head-review-loop.md": ("canonical", "sitemap", "public-copy-sweep"),
    "static-copy-pr-current-head-closeout.md": ("forbidden claim", "approved"),
    "static-contract-review-edge-cases.md": ("coalesce", "groq", "fixture"),
    "static-faq-accordion-geo-pr-loop.md": ("<details", "faqpage"),
    "current-head-visual-contract-review-loop.md": ("scrollwidth", "iframe"),
    "human-visual-reference-map-alignment.md": ("aria-hidden", "geocoordinates"),
    "pr-contract-surfaces-and-visual-pause.md": ("untrusted external content", "anchored"),
    "read-command-output-path-safety-pr-loop.md": ("--out", "fail-closed"),
    "deterministic-validator-false-pass-probes.md": ("fail-closed", "oserror"),
    "human-review-live-cms-source-of-truth.md": ("source of truth", "sanity"),
    "human-copy-goal-contract-cascade.md": ("negative proof", "allowlist"),
    "injected-clock-and-reviewer-scratch-hygiene.md": ("number.isfinite", "/tmp"),
    "partial-run-independent-row-contract.md": ("superseded", "per-item"),
    "partial-builder-fix-cycle-recovery.md": ("scope opinion",),
    "shared-reviewer-account-state-and-quiet-lanes.md": ("collapses", "mcp"),
}

_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_REFERENCE = re.compile(r"`references/([a-z0-9-]+\.md)`")


class RouterShapeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")
        self.lines = self.text.splitlines()

    def test_the_router_stays_around_sixty_lines(self) -> None:
        self.assertLessEqual(
            len(self.lines), 72, "the router grew back into a procedure manual"
        )
        self.assertGreater(len(self.lines), 40, "the router lost required sections")

    def test_the_required_sections_are_all_present(self) -> None:
        headings = [line.strip() for line in self.lines if line.startswith("## ")]
        self.assertEqual(
            headings,
            [
                "## Trigger and non-goals",
                "## Route it into the tool",
                "## Trusted roles",
                "## Classify every finding",
                "## Cycles and escalation",
                "## Conditional references",
                "## Merge authority",
            ],
        )

    def test_it_routes_into_the_executable_loop(self) -> None:
        self.assertIn(f"{LAUNCHER} check-config --config", self.text)
        self.assertIn(f"{LAUNCHER} run --config", self.text)
        self.assertIn("examples/run.example.json", self.text)

    def test_the_documented_route_is_the_shipped_repo_native_executable(self) -> None:
        """The router's own command block, resolved and executed-bit checked.

        A substring match is not enough: the previous version named a command
        that does not exist in this no-install repository, and every router test
        still passed.
        """
        block = self.text.split("```bash", 1)[1].split("```", 1)[0]
        commands = [
            stripped.split("#", 1)[0].split()
            for line in block.splitlines()
            if (stripped := line.strip())
        ]
        self.assertTrue(commands, "the router lost its routing command block")
        subcommands = set()
        for command in commands:
            with self.subTest(command=" ".join(command)):
                self.assertEqual(
                    command[0], LAUNCHER, "the router must name the repo-native launcher"
                )
                executable = REPO / command[0]
                self.assertTrue(executable.is_file(), f"{command[0]} does not exist")
                self.assertTrue(
                    os.access(executable, os.X_OK), f"{command[0]} is not executable"
                )
                self.assertIn("--config", command)
                subcommands.add(command[1])
        self.assertEqual(subcommands, {"check-config", "run"})

    def test_it_never_names_an_uninstalled_bare_command(self) -> None:
        """Nothing named ``pr-prover`` is on ``PATH``; only the repo path runs."""
        bare = re.findall(r"(?<![\w/.-])pr-prover (?:run|check-config|reset)\b", self.text)
        self.assertEqual(bare, [], f"the router names uninstalled commands: {bare}")

    def test_the_route_delegates_mechanics_instead_of_restating_them(self) -> None:
        """Exact-head, commit-list, worktree, and readback mechanics live in the tool."""
        route = self.text.split("## Route it into the tool", 1)[1].split("## Trusted", 1)[0]
        for restated in (
            "headRefOid",
            "commit list",
            "remote branch",
            "attempt worktree",
            "all agree",
            "signed comment",
        ):
            with self.subTest(restated=restated):
                self.assertNotIn(restated, route)
        for pointer in ("examples/run.example.json", "pr-prover/MISSION.md", "pr-prover/README.md"):
            with self.subTest(pointer=pointer):
                self.assertIn(pointer, route)
        body = [line for line in route.splitlines() if line.strip()]
        self.assertLessEqual(len(body), 10, "the route grew mechanics back")

    def test_it_points_at_both_repo_native_contracts(self) -> None:
        self.assertIn("pr-prover/MISSION.md", self.text)
        self.assertIn("pr-prover/README.md", self.text)

    def test_it_names_the_trusted_role_split(self) -> None:
        for role in ("Claude Code", "Codex Reviewer A/B", "Integration Auditor", "Hermes", "Karan"):
            with self.subTest(role=role):
                self.assertIn(role, self.text)

    def test_it_carries_the_blocker_taxonomy(self) -> None:
        for bucket in ("blocking", "non-blocking", "false positive", "needs Karan"):
            with self.subTest(bucket=bucket):
                self.assertIn(f"**{bucket}**", self.text)

    def test_it_states_the_two_cycle_cap_and_escalation(self) -> None:
        self.assertIn("Two fix cycles, maximum", self.text)
        self.assertIn("Stop and ask Karan", self.text)

    def test_karan_remains_the_merge_authority(self) -> None:
        self.assertIn("Karan alone merges", self.text)
        self.assertIn("never permission", self.text)

    def test_the_mechanics_walls_are_gone(self) -> None:
        for removed in (
            "## Pitfalls",
            "## Procedure",
            "## Final Report Format",
            "## Lightweight Durable State",
            "## Core Invariants",
            "## Legacy Reference Override",
            "--dangerously-skip-permissions",
            "gh api repos/",
            "security find-generic-password",
            "headRefOid",
            "commit list",
            "attempt worktree",
        ):
            with self.subTest(removed=removed):
                self.assertNotIn(removed, self.text)

    def test_only_the_routing_command_block_remains(self) -> None:
        self.assertEqual(self.text.count("```"), 2, "the router should hold one code block")


class ConditionalReferenceIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")
        self.index = self.text.split("## Conditional references", 1)[1].split("## Merge", 1)[0]

    def test_every_reference_is_one_conditional_line(self) -> None:
        entries = [line for line in self.index.splitlines() if line.startswith("- ")]
        self.assertGreaterEqual(len(entries), 8)
        for entry in entries:
            with self.subTest(entry=entry[:60]):
                self.assertIn("→", entry, "a reference entry must say when to read it")
                self.assertIn("references/", entry)

    def test_every_referenced_file_exists(self) -> None:
        named = set(_REFERENCE.findall(self.text))
        self.assertTrue(named)
        for name in sorted(named):
            with self.subTest(reference=name):
                self.assertTrue((SKILL_DIR / "references" / name).is_file())

    def test_no_reference_file_was_orphaned_by_the_slimming(self) -> None:
        """Lessons are preserved by pointing at them, so nothing may be unreachable."""
        on_disk = {path.name for path in (SKILL_DIR / "references").glob("*.md")}
        named = set(_REFERENCE.findall(self.text))
        self.assertEqual(on_disk - named, set())

    def test_the_required_lesson_families_are_routed(self) -> None:
        families = {
            "static-site / SEO": "static-site-current-head-review-loop.md",
            "visual contract": "current-head-visual-contract-review-loop.md",
            "CLI output-path safety": "read-command-output-path-safety-pr-loop.md",
            "validator false-pass": "deterministic-validator-false-pass-probes.md",
        }
        for family, reference in families.items():
            with self.subTest(family=family):
                self.assertIn(reference, self.index)


class ReferenceContractTests(unittest.TestCase):
    """The references are domain lessons, not a parallel prose lifecycle.

    Each conditionally loaded file exists for a risk the tool cannot encode —
    static copy/SEO, visual QA, CLI output-path safety, validator false passes,
    CMS truth, human goal changes, clock and scratch hygiene. None of them may
    redefine lifecycle completion, reviewer publication, credential recovery, or
    the fix cycle: those belong to ``MISSION.md`` and ``pr-prover``.
    """

    def setUp(self) -> None:
        self.documents = {
            path.name: path.read_text(encoding="utf-8")
            for path in sorted(REFERENCES.glob("*.md"))
        }

    def test_the_reference_inventory_is_exactly_the_audited_set(self) -> None:
        self.assertEqual(sorted(self.documents), sorted(PRESERVED_LESSONS))
        for name, text in self.documents.items():
            with self.subTest(reference=name):
                self.assertGreater(len(text.strip()), 400, "a reference lost its content")

    def test_no_reference_redefines_the_lifecycle_or_publication_mechanics(self) -> None:
        for name, text in self.documents.items():
            for pattern in CONFLICTING_LIFECYCLE:
                with self.subTest(reference=name, pattern=pattern):
                    self.assertIsNone(
                        re.search(pattern, text, re.IGNORECASE),
                        f"{name} carries lifecycle/publication prose matching {pattern!r}",
                    )

    def test_the_conflict_scan_is_not_vacuous(self) -> None:
        """Every pattern must still match the prose it was written to catch."""
        samples = (
            "re-run A/B reviewers on the new head",
            "verify Reviewer A and Reviewer B signed approvals",
            "require both role-signed reviews on the new exact head",
            "gh api repos/owner/name/pulls/6/reviews",
            'GH_TOKEN="$TOKEN" gh pr comment 6',
            "REVIEWER_TOKEN=$(gh auth token -u karanagent1)",
            "gh pr review --request-changes",
            "post the artifact under the reviewer identity",
            "gh pr view --json headRefOid,commits",
            "do not rely on latestReviews or reviewDecision",
        )
        for pattern in CONFLICTING_LIFECYCLE:
            with self.subTest(pattern=pattern):
                self.assertTrue(
                    any(re.search(pattern, sample, re.IGNORECASE) for sample in samples),
                    f"{pattern!r} no longer catches any known conflicting phrasing",
                )

    def test_no_reference_instructs_publication_handoff_or_sequencing_in_prose(self) -> None:
        """The half of FROZEN-P92-004 that survived deleting the command spellings."""
        for name, text in self.documents.items():
            with self.subTest(reference=name):
                self.assertEqual(
                    lifecycle_directives_in(text),
                    [],
                    f"{name} instructs lifecycle mechanics MISSION.md/pr-prover own",
                )

    def test_the_adversarial_corpus_is_independent_of_the_scan(self) -> None:
        """The oracle must come from outside the implementation.

        A guard proved against its own examples proves nothing, which is how a
        finite spelling list passed forty focused tests while returning nothing
        for ordinary synonyms. So the corpus carries every mutation the three
        lanes reported at this PR's reviewed head, plus variants written from
        ordinary English rather than from the vocabularies above.
        """
        sources = Counter(item["source"] for item in LIFECYCLE_CORPUS["directives"])
        for lane in ("reviewer-a", "reviewer-b", "integration-auditor"):
            with self.subTest(lane=lane):
                self.assertGreaterEqual(
                    sources[lane], 5, f"{lane}'s reported mutations are not all recorded"
                )
        self.assertGreaterEqual(
            sources["independent"], 6, "the corpus only restates what was already reported"
        )
        self.assertGreaterEqual(len(LIFECYCLE_CORPUS["descriptive"]), 15)

    def test_the_prose_scan_catches_every_corpus_directive(self) -> None:
        """Each independently written instruction, appended to a clean reference.

        Reproduction from the re-review: append a single ordinary sentence to a
        clean indexed reference and the previous scan still reported OK. Each
        mutation is appended to a real, currently-clean reference, so a green
        baseline and a red mutant are proved against the same document.
        """
        for name, text in sorted(self.documents.items()):
            self.assertEqual(lifecycle_directives_in(text), [], f"{name} is not a clean baseline")
        baseline = self.documents["deterministic-validator-false-pass-probes.md"]
        for item in LIFECYCLE_CORPUS["directives"]:
            with self.subTest(source=item["source"], sentence=item["sentence"]):
                self.assertTrue(
                    lifecycle_directives_in(f"{baseline}\n{item['sentence']}\n"),
                    f"an appended {item['sentence']!r} still passes the scan",
                )

    def test_no_directive_rule_is_dead_weight(self) -> None:
        """Non-vacuity, without letting a rule vouch for itself.

        Every rule has to be reached by at least one sentence the corpus wrote
        independently. A rule nothing in the corpus triggers is either
        unreachable or tuned to wording no reviewer would actually use.
        """
        fired = {
            name
            for item in LIFECYCLE_CORPUS["directives"]
            for name, _ in lifecycle_directives_in(item["sentence"])
        }
        self.assertEqual(
            [rule.name for rule in MANUAL_LIFECYCLE_DIRECTIVES if rule.name not in fired],
            [],
            "a directive rule is never exercised by the independent corpus",
        )

    def test_the_prose_scan_is_not_indiscriminate(self) -> None:
        """Domain evidence prose using the same nouns still passes.

        This half matters as much as the catching half: "PR", "comment",
        "review", "builder", "Claude", "Codex", "correction", and "cycle cap"
        are load-bearing words in these lessons, and a scan that rejected them
        as nouns would delete the content it is protecting.
        """
        for item in LIFECYCLE_CORPUS["descriptive"]:
            with self.subTest(sentence=item["sentence"]):
                self.assertEqual(
                    lifecycle_directives_in(item["sentence"]),
                    [],
                    "the scan rejected descriptive domain evidence",
                )

    def lesson_gaps(self, documents: dict[str, str]) -> list[tuple[str, str]]:
        return [
            (name, token)
            for name, tokens in PRESERVED_LESSONS.items()
            for token in tokens
            if token not in documents.get(name, "").lower()
        ]

    def test_every_reference_keeps_the_domain_lesson_it_exists_for(self) -> None:
        """Removing conflicting mechanics must not remove the reusable lesson."""
        self.assertEqual(self.lesson_gaps(self.documents), [])

    def test_the_lesson_scan_notices_a_deleted_domain_token(self) -> None:
        """Non-vacuity: a rewrite that quietly guts a lesson has to fail here."""
        for name, tokens in PRESERVED_LESSONS.items():
            for token in tokens:
                mutated = dict(self.documents)
                mutated[name] = re.sub(
                    re.escape(token), "", self.documents[name], flags=re.IGNORECASE
                )
                with self.subTest(reference=name, lesson=token):
                    self.assertNotEqual(
                        mutated[name], self.documents[name], f"{name} never held {token!r}"
                    )
                    self.assertIn((name, token), self.lesson_gaps(mutated))

    def test_every_reference_is_reachable_from_the_router(self) -> None:
        indexed = set(_REFERENCE.findall(SKILL.read_text(encoding="utf-8")))
        self.assertEqual(indexed, set(self.documents), "a reference is orphaned or missing")


class RepoContractTests(unittest.TestCase):
    """The contracts exist, say what they must, and stay reachable from the README."""

    def test_both_contracts_are_present(self) -> None:
        self.assertTrue(AGENTS.is_file(), "the repository agent contract is missing")
        self.assertTrue(MISSION.is_file(), "the pr-prover mission contract is missing")

    def test_the_agent_contract_carries_the_boundary_sections(self) -> None:
        text = AGENTS.read_text(encoding="utf-8")
        for heading in (
            "## Read first",
            "## Repository shape",
            "## `pr-prover` mission lock",
            "## Roles and authority",
            "## Change discipline",
            "## Required verification",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, text)
        self.assertIn("Karan** is the sole merge authority", text)
        for runtime in ("python3 -m unittest", "python3.11 -m unittest"):
            with self.subTest(runtime=runtime):
                self.assertIn(runtime, text)

    def test_the_mission_states_the_thin_product_and_its_non_goals(self) -> None:
        text = MISSION.read_text(encoding="utf-8")
        for heading in (
            "## Product definition",
            "## Product boundary",
            "## Trusted operating model",
            "## Explicit non-goals",
            "## Normative lifecycle",
            "## Outcome meanings",
            "## Load-bearing invariants and proof map",
            "## Review contract",
            "## Completion gate",
        ):
            with self.subTest(heading=heading):
                self.assertIn(heading, text)
        self.assertIn("not a hostile same-UID zero-trust system", text)
        for outcome in ("merge-ready", "blocked", "needs-Karan"):
            with self.subTest(outcome=outcome):
                self.assertIn(outcome, text)

    def proof_map(self) -> dict[str, tuple[str, str]]:
        rows = [
            line
            for line in MISSION.read_text(encoding="utf-8").splitlines()
            if re.match(r"\|\s*M\d+\s*\|", line)
        ]
        parsed = {}
        for row in rows:
            cells = row.split("|")
            parsed[cells[1].strip()] = (cells[3].strip(), cells[4].strip())
        return parsed

    def test_the_proof_map_covers_every_invariant_and_declares_its_status(self) -> None:
        """A contract obligation must never read as an implemented one."""
        rows = self.proof_map()
        self.assertEqual(list(rows), [f"M{index}" for index in range(1, 15)])
        for identifier, (status, seams) in rows.items():
            with self.subTest(invariant=identifier):
                self.assertTrue(status, "every invariant declares a status")
                self.assertRegex(status, r"shipped|owed|partial|none")
                self.assertTrue(seams, "every invariant names its proof seams")

    def test_the_status_column_cannot_be_flattened_to_all_shipped(self) -> None:
        """The demonstrated overclaim mutation: replace every status with "shipped".

        A row this head only half-implements must say so, and a row it does
        implement must not hedge — so flattening the column in either direction
        fails here rather than shipping a false proof map.
        """
        rows = self.proof_map()
        for identifier, (status, _) in rows.items():
            with self.subTest(invariant=identifier):
                if identifier in QUALIFIED_INVARIANTS:
                    self.assertNotEqual(
                        status.lower(),
                        "shipped",
                        f"{identifier} is not fully shipped on this head and must not claim it",
                    )
                    self.assertRegex(status, r"owed|partial|shipped for")
                else:
                    self.assertEqual(
                        status, "shipped", f"{identifier} is shipped and must not hedge"
                    )
        for identifier, (status, _) in rows.items():
            if re.search(r"owed|partial", status):
                with self.subTest(invariant=identifier):
                    self.assertRegex(
                        status,
                        r"PAPI-\d+|M\d+",
                        f"{identifier} defers work without naming who owes it",
                    )

    def test_m13_separates_shipped_redaction_from_owed_transport_and_authority(self) -> None:
        """Reports redact recursively today; transport status and merge authority do not exist yet."""
        status, seams = self.proof_map()["M13"]
        self.assertIn("redaction", status.lower())
        for owed in ("transport", "merge-authority", "PAPI-90", "PAPI-97"):
            with self.subTest(owed=owed):
                self.assertIn(owed, status)
        self.assertRegex(seams, r"no transport-status or merge-authority field")
        report = (PR_PROVER / "src" / "pr_prover" / "report.py").read_text(encoding="utf-8")
        for absent in ("transport_status", "merge_authority", "readback_status"):
            with self.subTest(field=absent):
                self.assertNotIn(
                    absent,
                    report,
                    "report.py grew the field M13 declares owed; update the proof map",
                )

    def test_the_contracts_are_reachable_from_the_readmes(self) -> None:
        root = (REPO / "README.md").read_text(encoding="utf-8")
        self.assertIn("(AGENTS.md)", root)
        self.assertIn("(pr-prover/MISSION.md)", root)
        self.assertIn("autonomous-pr-prover/SKILL.md", root)
        self.assertIn("(MISSION.md)", (PR_PROVER / "README.md").read_text(encoding="utf-8"))

    def test_every_local_markdown_link_resolves(self) -> None:
        for document in MARKDOWN:
            for target in _LINK.findall(document.read_text(encoding="utf-8")):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                path = (document.parent / target.split("#", 1)[0]).resolve()
                with self.subTest(document=document.name, link=target):
                    self.assertTrue(path.exists(), f"{document.name} links to a missing {target}")


class RemovedFrameworkScanTests(unittest.TestCase):
    """The replacement must not have quietly reintroduced the rejected slice."""

    def shipped(self) -> list[tuple[Path, str]]:
        return [(path, path.read_text(encoding="utf-8")) for path in SHIPPED]

    def test_no_rejected_module_is_present(self) -> None:
        for name in ("capabilities.py", "sandbox.py", "attestation.py", "broker.py"):
            with self.subTest(module=name):
                self.assertFalse(list((PR_PROVER / "src").rglob(name)))

    def test_no_rejected_machinery_is_named_in_the_shipped_surface(self) -> None:
        for path, text in self.shipped():
            lowered = text.lower()
            for token in REJECTED:
                with self.subTest(path=path.name, token=token):
                    self.assertNotIn(token, lowered)

    def test_the_contracts_name_the_rejected_apparatus_only_to_forbid_it(self) -> None:
        """Naming it under 'do not introduce' is the point; asserting it is drift."""
        prohibition = re.compile(
            r"do not (introduce|add|build)|does not include|non-goals|must not", re.IGNORECASE
        )
        for document in (AGENTS, MISSION):
            intro = ""
            for line in document.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith(("-", "*", "|")):
                    intro = stripped
                lowered = stripped.lower()
                for token in REJECTED:
                    if token not in lowered:
                        continue
                    with self.subTest(document=document.name, token=token):
                        self.assertTrue(
                            stripped.startswith("-"),
                            f"{document.name} mentions {token!r} outside a prohibition list",
                        )
                        self.assertRegex(
                            intro,
                            prohibition,
                            f"{document.name} mentions {token!r} without forbidding it",
                        )

    def test_no_broker_or_crypto_transport_is_imported(self) -> None:
        pattern = re.compile(
            r"^\s*(?:import|from)\s+(socket|socketserver|ssl|hmac|ctypes|resource|"
            r"multiprocessing|xmlrpc|http\.server|secrets)\b",
            re.MULTILINE,
        )
        for path in (PR_PROVER / "src").rglob("*.py"):
            with self.subTest(path=path.name):
                self.assertIsNone(pattern.search(path.read_text(encoding="utf-8")))

    def test_the_session_environment_is_never_rebuilt_from_nothing(self) -> None:
        for path in (PR_PROVER / "src").rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotIn("os.environ.clear", text)
                self.assertNotIn("env={}", text)

    def test_the_loop_still_holds_its_own_shape(self) -> None:
        """A thin tool: one small package, no framework hiding inside it.

        The core is asserted by name and the package is held to a size, rather
        than pinned to an exact listing — a later slice may add a module, but
        it may not lose one of these or grow a framework behind them.
        """
        modules = sorted(path.name for path in (PR_PROVER / "src" / "pr_prover").glob("*.py"))
        self.assertEqual([name for name in CORE_MODULES if name not in modules], [])
        self.assertLessEqual(len(modules), 20, "the thin tool grew into a framework")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
