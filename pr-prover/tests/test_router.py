"""The skill is a router, and the tool is only the tool.

Two properties are worth holding still. The skill must stay a thin judgment
surface — trigger, routing, roles, taxonomy, cap, conditional references,
merge authority — because the previous version failed by growing into a
procedure manual nobody could keep true. And the shipped tool must stay the
small trusted-agent orchestrator it is: the zero-trust capability broker,
sandbox semantics model, runtime attestation, and container qualification that
were explored and rejected must not reappear by drift.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO / "Karan-skills" / "software-development" / "autonomous-pr-prover"
SKILL = SKILL_DIR / "SKILL.md"
PR_PROVER = REPO / "pr-prover"

# The shipped surface: what a user of this tool actually gets. The tests
# directory is excluded because this file necessarily names the machinery it is
# scanning for.
SHIPPED = (
    *sorted((PR_PROVER / "src").rglob("*.py")),
    *sorted((PR_PROVER / "examples").glob("*.json")),
    PR_PROVER / "README.md",
    PR_PROVER / "bin" / "pr-prover",
    SKILL,
)


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
        self.assertIn("pr-prover run --config", self.text)
        self.assertIn("pr-prover check-config --config", self.text)
        self.assertIn("examples/run.example.json", self.text)

    def test_it_names_the_trusted_role_split(self) -> None:
        for role in ("Claude Code", "Codex Reviewer A/B", "Integration Auditor", "Hermes", "Karan"):
            self.assertIn(role, self.text)

    def test_it_carries_the_blocker_taxonomy(self) -> None:
        for bucket in ("blocking", "non-blocking", "false positive", "needs Karan"):
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
            "--dangerously-skip-permissions",
            "gh api repos/",
            "security find-generic-password",
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
        named = set(re.findall(r"`references/([a-z0-9-]+\.md)`", self.text))
        self.assertTrue(named)
        for name in sorted(named):
            with self.subTest(reference=name):
                self.assertTrue((SKILL_DIR / "references" / name).is_file())

    def test_no_reference_file_was_orphaned_by_the_slimming(self) -> None:
        """Lessons are preserved by pointing at them, so nothing may be unreachable."""
        on_disk = {path.name for path in (SKILL_DIR / "references").glob("*.md")}
        named = set(re.findall(r"`references/([a-z0-9-]+\.md)`", self.text))
        self.assertEqual(on_disk - named, set())

    def test_the_required_lesson_families_are_routed(self) -> None:
        families = {
            "static-site / SEO": "static-site-current-head-review-loop.md",
            "visual contract": "current-head-visual-contract-review-loop.md",
            "CLI output-path safety": "read-command-output-path-safety-pr-loop.md",
        }
        for family, reference in families.items():
            with self.subTest(family=family):
                self.assertIn(reference, self.index)


class RemovedFrameworkScanTests(unittest.TestCase):
    """The replacement must not have quietly reintroduced the rejected slice."""

    def shipped(self) -> list[tuple[Path, str]]:
        return [(path, path.read_text(encoding="utf-8")) for path in SHIPPED]

    def test_no_rejected_module_is_present(self) -> None:
        for name in ("capabilities.py", "sandbox.py", "attestation.py", "broker.py"):
            with self.subTest(module=name):
                self.assertFalse(list((PR_PROVER / "src").rglob(name)))

    def test_no_rejected_machinery_is_named_in_the_shipped_surface(self) -> None:
        forbidden = (
            "capability broker",
            "capabilitybroker",
            "lane secret",
            "lane_secret",
            # Plain "bearer" is legitimate in the redaction rules, so the scan
            # looks for the per-lane credential concept instead.
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
        for path, text in self.shipped():
            lowered = text.lower()
            for token in forbidden:
                with self.subTest(path=path.name, token=token):
                    self.assertNotIn(token, lowered)

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
        """A thin tool: one small package, no framework hiding inside it."""
        modules = sorted(path.name for path in (PR_PROVER / "src" / "pr_prover").glob("*.py"))
        self.assertEqual(
            modules,
            [
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
            ],
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
