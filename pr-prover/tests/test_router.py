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

What this module proves about the third property is deliberately bounded. It
checks the exact committed reference set: the inventory, the router index, the
named domain lesson each file exists for, and a fixed list of known conflicting
command, API, credential, and role spellings that must not return. It does not
decide whether an arbitrary English sentence is a lifecycle instruction. An
earlier attempt to do that — pattern rules over concept vocabularies, proved
against a curated sentence corpus — overclaimed, and three independent review
lanes walked ordinary synonyms straight through it. Judging new reference prose
is exact-head human/agent review; whether a bounded linter is worth building at
all is PAPI-98 research and does not gate this slice.

The scans deliberately describe the surface that exists on current ``main``.
Nothing here assumes a later slice's module has already landed.
"""
from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

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

# The exact conflicting spellings already found in these references, pinned so
# they cannot come back. The router and ``MISSION.md`` own the A → B →
# Integration Auditor lifecycle, and ``pr-prover`` owns reviewer publication,
# transport, credentials, and GitHub readback; a reference restating any of it
# becomes a second, conflicting implementation in prose.
#
# This is a fixed inventory of known forms, not a decision procedure for
# English. A new phrasing that means the same thing is caught by exact-head
# review of the committed prose, not here.
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

    That rule is a contract on the prose, and these tests are not the whole of
    its enforcement. What is deterministic here is the exact committed set: the
    inventory, the reachability, the named lesson each file keeps, and the fixed
    list of conflicting spellings already found and removed. Whether a newly
    written sentence crosses the line is a judgment made by exact-head review.
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

    def test_no_reference_carries_a_known_conflicting_lifecycle_spelling(self) -> None:
        """The pinned inventory only: each exact form must stay absent."""
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
