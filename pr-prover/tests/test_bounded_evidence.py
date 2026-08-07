"""What a run says it established, and what it refuses to say.

Four claims are under test here, and each of them is one a report could make
falsely while every other check in this tool stayed green:

* the reported head was observed, and observed *at* a time this run can name;
* a configured gate's result is evidence about a bounded thing — a local
  command, a live endpoint, or an endpoint proved to be serving this head — and
  the strongest of those is never something a config file can simply assert;
* the reviewer lanes ran under adapters and declared runtimes the report names,
  without that being turned into a claim that they are independent;
* five things a green report is easily read as proving are stated unproven.

The negative half is the point of most of it. A gate that hits a preview URL
proves the URL answered; the fixtures below hold the difference between that and
"the URL was serving this commit" to a stop rather than to a sentence.
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from _support import (
    BINDING_SOURCE,
    ENVIRONMENT_NAME,
    ENVIRONMENT_URL,
    HEAD_A,
    HEAD_B,
    OBSERVED_AT,
    FakeGitHub,
    FakeRemote,
    FakeRunner,
    LaneScript,
    builder_output,
    environment_envelope,
    fix_comment,
    make_config,
    make_source_repo,
    records_environment,
    reviewer_output,
)
from pr_prover import report
from pr_prover.config import (
    GATE_EVIDENCE_HEAD_BOUND,
    GATE_EVIDENCE_LOCAL,
    GATE_EVIDENCE_MODES,
    GATE_EVIDENCE_UNBOUND,
    MAX_COVERAGE_CHARACTERS,
    UNBOUND_STATEMENT,
    RunConfig,
)
from pr_prover.environment import (
    MAX_ENVIRONMENT_EVIDENCE_BYTES,
    environment_evidence_path,
    read_binding,
)
from pr_prover.errors import ConfigError, EnvironmentEvidenceError
from pr_prover.loop import (
    MERGE_READY,
    NEEDS_KARAN,
    GateDisclosure,
    ProverLoop,
    RunResult,
)
from pr_prover.worktrees import SourceRepo, WorktreeProvider

COVERAGE = "HTTP smoke of the checkout endpoint against the preview deployment"


def gate(**overrides: object) -> dict[str, object]:
    """One configured gate, defaulting to the ordinary local kind."""
    configured: dict[str, object] = {
        "name": "tests",
        "argv": ["lane-gate-tests", "--head", "{head}"],
    }
    configured.update(overrides)
    return configured


def external_gate(*, binding: bool = False, **overrides: object) -> dict[str, object]:
    """A gate the operator declared to observe an external environment."""
    argv = ["lane-gate-preview", "--head", "{head}", "--url", ENVIRONMENT_URL]
    if binding:
        argv += ["--environment-evidence", "{environment_evidence_file}"]
    configured: dict[str, object] = {
        "name": "preview",
        "argv": argv,
        "coverage": COVERAGE,
        "environment": {"identifier": ENVIRONMENT_NAME, "binding_evidence": binding},
    }
    configured.update(overrides)
    return configured


class GateDeclarationConfigTests(unittest.TestCase):
    """The evidence mode is declared, never inferred, and never asserted upward."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-test-")
        self.tmp = Path(self._tmp.name).resolve()
        self.addCleanup(self._tmp.cleanup)
        self.source_repo = make_source_repo(self.tmp)

    def config(self, *gates: dict[str, object]) -> RunConfig:
        return make_config(self.tmp, source_repo=self.source_repo, gates=list(gates))

    def refusal(self, *gates: dict[str, object]) -> str:
        with self.assertRaises(ConfigError) as caught:
            self.config(*gates)
        return caught.exception.message

    def test_a_config_written_before_this_field_existed_is_still_valid(self) -> None:
        """Backward compatibility, and the conservative default that comes with it."""
        configured = self.config(gate()).gates[0]
        self.assertEqual(configured.coverage, "")
        self.assertIsNone(configured.environment)
        self.assertEqual(configured.declared_evidence_mode, GATE_EVIDENCE_LOCAL)
        self.assertFalse(configured.binds_environment)

    def test_a_head_token_and_a_url_in_argv_do_not_declare_an_environment(self) -> None:
        """The reporting hazard this whole seam exists for, as a config-level fact.

        Substituting the head into a command and naming a URL beside it is what
        an external check looks like, which is exactly why neither may mean
        anything: both are strings the operator typed, and neither is evidence
        about what a deployment served.
        """
        configured = self.config(
            gate(argv=["curl", "--fail", f"{ENVIRONMENT_URL}/build/{{head}}"])
        ).gates[0]
        self.assertEqual(configured.declared_evidence_mode, GATE_EVIDENCE_LOCAL)
        self.assertIsNone(configured.environment)

    def test_declaring_an_environment_reaches_unbound_and_stops_there(self) -> None:
        configured = self.config(external_gate()).gates[0]
        self.assertEqual(configured.declared_evidence_mode, GATE_EVIDENCE_UNBOUND)
        self.assertEqual(configured.environment.identifier, ENVIRONMENT_NAME)
        self.assertFalse(configured.binds_environment)

    def test_binding_evidence_is_an_opt_in_that_owes_a_file(self) -> None:
        configured = self.config(external_gate(binding=True)).gates[0]
        self.assertTrue(configured.binds_environment)
        # Still not head-bound from configuration alone. That mode is earned at
        # run time by a validated envelope and cannot be spelled in a file.
        self.assertEqual(configured.declared_evidence_mode, GATE_EVIDENCE_UNBOUND)

    def test_a_binding_gate_with_nowhere_to_write_is_refused(self) -> None:
        message = self.refusal(
            external_gate(binding=True, argv=["lane-gate-preview", "--head", "{head}"])
        )
        self.assertIn("nowhere to record", message)

    def test_an_evidence_path_nothing_would_read_is_refused(self) -> None:
        message = self.refusal(
            external_gate(
                argv=["lane-gate-preview", "--evidence", "{environment_evidence_file}"]
            )
        )
        self.assertIn("does not declare environment.binding_evidence", message)

    def test_an_unusable_coverage_declaration_is_refused(self) -> None:
        for case, value in (
            ("empty", ""),
            ("whitespace", "   "),
            ("not text", 7),
            ("too long", "x" * (MAX_COVERAGE_CHARACTERS + 1)),
        ):
            with self.subTest(case=case):
                self.assertIn("coverage", self.refusal(gate(coverage=value)))

    def test_coverage_survives_verbatim(self) -> None:
        self.assertEqual(self.config(gate(coverage=f"  {COVERAGE} ")).gates[0].coverage, COVERAGE)

    def test_an_unusable_environment_declaration_is_refused(self) -> None:
        for case, value in (
            ("not an object", "preview"),
            ("unknown key", {"identifier": "preview", "url": ENVIRONMENT_URL}),
            ("no identifier", {"binding_evidence": True}),
            ("empty identifier", {"identifier": ""}),
            ("leading space", {"identifier": " preview"}),
            # Compared byte for byte against what a gate writes, so a label that
            # differs from another only by a space nobody can see is refused.
            ("trailing space", {"identifier": "preview "}),
            ("identifier with a newline", {"identifier": "preview\nstaging"}),
            ("non-boolean opt-in", {"identifier": "preview", "binding_evidence": "yes"}),
        ):
            with self.subTest(case=case):
                self.assertIn("environment", self.refusal(gate(environment=value)))

    def test_the_classification_is_finite_and_every_mode_has_its_sentence(self) -> None:
        """Three modes, and a rendered statement for each one.

        The classification exists so a reader is never left to supply the
        difference themselves, which only holds if every mode has a sentence: a
        fourth value added without one would raise at the boundary that renders
        it, and a mode with no statement is the case this pins.
        """
        self.assertEqual(
            GATE_EVIDENCE_MODES,
            (GATE_EVIDENCE_LOCAL, GATE_EVIDENCE_UNBOUND, GATE_EVIDENCE_HEAD_BOUND),
        )
        self.assertEqual(set(report.EVIDENCE_STATEMENTS), set(GATE_EVIDENCE_MODES))
        self.assertEqual(
            report.EVIDENCE_STATEMENTS[GATE_EVIDENCE_UNBOUND], UNBOUND_STATEMENT
        )

    def test_check_config_says_in_advance_what_an_unbound_gate_will_report(self) -> None:
        notes = self.config(external_gate()).advisories()
        self.assertTrue(
            any(UNBOUND_STATEMENT in note and "preview" in note for note in notes), notes
        )

    def test_a_binding_gate_is_not_advised_as_unbound(self) -> None:
        notes = self.config(external_gate(binding=True)).advisories()
        self.assertFalse(any(UNBOUND_STATEMENT in note for note in notes), notes)


class EnvironmentEnvelopeTests(unittest.TestCase):
    """The one artifact that can raise a gate to head-bound, held to its grammar."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-test-")
        self.tmp = Path(self._tmp.name).resolve()
        self.addCleanup(self._tmp.cleanup)
        self.path = self.tmp / "binding.json"

    def write(self, payload: object) -> Path:
        text = payload if isinstance(payload, str) else json.dumps(payload)
        self.path.write_text(text, encoding="utf-8")
        return self.path

    def read(self, **overrides: object) -> object:
        arguments: dict[str, object] = {
            "repo": "example/repo",
            "pr": 7,
            "gate": "preview",
            "environment": ENVIRONMENT_NAME,
            "head": HEAD_A,
        }
        arguments.update(overrides)
        return read_binding(self.path, **arguments)  # type: ignore[arg-type]

    def refusal(self, payload: object, **overrides: object) -> str:
        self.write(payload)
        with self.assertRaises(EnvironmentEvidenceError) as caught:
            self.read(**overrides)
        return caught.exception.message

    def test_a_matching_revision_binds_the_environment_to_the_head(self) -> None:
        self.write(environment_envelope(head=HEAD_A))
        binding = self.read()
        self.assertEqual(binding.revision, HEAD_A)
        self.assertEqual(binding.environment, ENVIRONMENT_NAME)
        self.assertEqual(binding.url, ENVIRONMENT_URL)
        self.assertEqual(binding.binding_source, BINDING_SOURCE)
        self.assertEqual(binding.observed_at, OBSERVED_AT)

    def test_a_revision_that_is_not_the_head_is_the_failure_this_exists_for(self) -> None:
        """The endpoint answered; it was serving something else."""
        message = self.refusal(environment_envelope(head=HEAD_A, revision=HEAD_B))
        self.assertIn("is not the head this run is bound to", message)

    def test_absent_evidence_fails_closed(self) -> None:
        with self.assertRaises(EnvironmentEvidenceError) as caught:
            self.read()
        self.assertIn("produced no binding evidence", caught.exception.message)

    def test_malformed_empty_and_oversized_evidence_fail_closed(self) -> None:
        for case, payload in (
            ("empty", "   \n"),
            ("not JSON", "{not json"),
            ("not an object", [environment_envelope(head=HEAD_A)]),
            ("oversized", "x" * (MAX_ENVIRONMENT_EVIDENCE_BYTES + 1)),
        ):
            with self.subTest(case=case):
                self.refusal(payload)

    def test_an_envelope_that_is_not_this_one_fails_closed(self) -> None:
        complete = environment_envelope(head=HEAD_A)
        for case, payload in (
            ("missing a key", {key: value for key, value in complete.items() if key != "url"}),
            ("an extra key", {**complete, "findings": ["everything is fine"]}),
            ("another schema", environment_envelope(head=HEAD_A, schema_version=2)),
            # ``True == 1`` in Python, so a JSON boolean would satisfy an
            # ordinary comparison against this schema version.
            ("a boolean schema version", environment_envelope(head=HEAD_A, schema_version=True)),
        ):
            with self.subTest(case=case):
                self.refusal(payload)

    def test_evidence_produced_for_another_run_fails_closed(self) -> None:
        for case, payload in (
            ("another repository", environment_envelope(head=HEAD_A, repo="other/repo")),
            ("another pull request", environment_envelope(head=HEAD_A, pr=8)),
            ("another gate", environment_envelope(head=HEAD_A, gate="smoke")),
            ("another environment", environment_envelope(head=HEAD_A, environment="staging")),
            ("another head", environment_envelope(head=HEAD_B)),
        ):
            with self.subTest(case=case):
                self.refusal(payload)

    def test_a_boolean_pull_request_number_does_not_pass_for_pull_request_one(self) -> None:
        self.refusal(environment_envelope(head=HEAD_A, pr=True), pr=1)

    def test_an_unusable_field_fails_closed(self) -> None:
        for case, payload in (
            ("short revision", environment_envelope(head=HEAD_A, revision="abc")),
            ("upper-case revision", environment_envelope(head=HEAD_A, revision=HEAD_A.upper())),
            ("no revision", environment_envelope(head=HEAD_A, revision=None) | {"revision": None}),
            ("empty url", environment_envelope(head=HEAD_A, url="  ")),
            ("unbounded url", environment_envelope(head=HEAD_A, url="https://x/" + "y" * 600)),
            ("no binding source", environment_envelope(head=HEAD_A, binding_source="")),
            ("local observation time", environment_envelope(head=HEAD_A, observed_at="2026-08-03 12:00:00")),
            ("offset observation time", environment_envelope(head=HEAD_A, observed_at="2026-08-03T12:00:00+01:00")),
            ("no observation time", environment_envelope(head=HEAD_A, observed_at="")),
        ):
            with self.subTest(case=case):
                self.refusal(payload)

    def test_the_evidence_path_is_cleared_before_a_gate_can_write_it(self) -> None:
        """A previous cycle's file must never be read as this gate's observation."""
        first = environment_evidence_path(self.tmp, gate="preview", head=HEAD_A)
        first.write_text("stale\n", encoding="utf-8")
        again = environment_evidence_path(self.tmp, gate="preview", head=HEAD_A)
        self.assertEqual(first, again)
        self.assertFalse(again.exists())

    def test_the_evidence_path_lives_outside_every_repository(self) -> None:
        path = environment_evidence_path(self.tmp, gate="preview", head=HEAD_A)
        self.assertTrue(path.is_relative_to(self.tmp))
        self.assertTrue(path.name.startswith("environment-preview-"))


class DisclosureHarness(unittest.TestCase):
    """One loop over scripted gates, with a clock a test can name."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-test-")
        self.tmp = Path(self._tmp.name).resolve()
        self.addCleanup(self._tmp.cleanup)
        self.source_repo = make_source_repo(self.tmp)
        self.remote = FakeRemote()
        self.script = LaneScript()
        self.runner = FakeRunner(self.remote, self.script)
        self.github = FakeGitHub(self.remote)
        self.observations: list[str] = []

    def clock(self) -> str:
        """A strictly increasing UTC stamp, so "when was this seen" is checkable."""
        self.observations.append(f"2026-08-03T12:{len(self.observations):02d}:00Z")
        return self.observations[-1]

    def build(self, **config_kwargs: object) -> ProverLoop:
        config = make_config(self.tmp, source_repo=self.source_repo, **config_kwargs)
        self.config = config
        source = SourceRepo(runner=self.runner, path=config.source_repo)
        return ProverLoop(
            config,
            runner=self.runner,
            github=self.github,
            worktrees=WorktreeProvider(source, config.worktree_root),
            scratch_root=self.tmp / "scratch",
            clock=self.clock,
        )

    def review_round(self, head: str) -> None:
        self.script.add("lane-reviewer-A", reviewer_output(head))
        self.script.add("lane-reviewer-B", reviewer_output(head))

    def disclosure(self, result: object, name: str) -> dict:
        payload = report.as_dict(result)
        return next(item for item in payload["configured_gates"] if item["name"] == name)


class ObservationTimeTests(DisclosureHarness):
    def test_a_clean_run_dates_the_head_it_reports(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.head, HEAD_A)
        # The terminal freshness read is the last observation the run made, and
        # it is the one the report is dated by.
        self.assertEqual(result.observed_at, self.observations[-1])
        payload = report.as_dict(result)
        self.assertEqual(payload["observed_at"], self.observations[-1])
        self.assertIn(
            f"**Head observed at:** {self.observations[-1]} (UTC)", report.to_markdown(result)
        )

    def test_a_run_that_read_nothing_live_manufactures_no_observation(self) -> None:
        """An interrupted attempt stops before its first GitHub read, on purpose."""
        loop = self.build()
        (self.tmp / "state.json").write_text(
            json.dumps(
                {
                    "schema_version": 3,
                    "repo": "example/repo",
                    "pr": 7,
                    "head": HEAD_A,
                    "attempt": 1,
                    "phase": "attempt-in-flight",
                    "attempt_head": HEAD_A,
                    "corrective_reruns": [],
                    "outcome": None,
                    "classification": None,
                    "verified_artifacts": {},
                }
            ),
            encoding="utf-8",
        )

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertIsNone(result.head)
        self.assertIsNone(result.observed_at)
        self.assertEqual(self.observations, [])
        payload = report.as_dict(result)
        self.assertIsNone(payload["observed_at"])
        self.assertIn("**Head observed at:** never", report.to_markdown(result))


class ObservationPairingTests(unittest.TestCase):
    """The head and its observation time are one fact, at the rendering boundary too.

    The loop sets them in a single statement, so they cannot come apart there.
    This is the other end: a result that somehow carries a time without the head
    it dates must not print one, because a timestamp beside ``head: unknown``
    reads as a live read that happened.
    """

    def test_a_binding_for_another_head_is_not_disclosed_as_this_one(self) -> None:
        """The rendering cannot show a revision that is not the reported head.

        The loop drops a previous head's binding when it binds a new one, and
        this is the other half of that rule: whatever reaches the renderer, a
        gate is disclosed as bound only for the head this report is about.
        """
        bound = GateDisclosure(
            name="preview",
            kind="baseline",
            invocation="preview-check --head {head}",
            coverage=COVERAGE,
            evidence_mode=GATE_EVIDENCE_HEAD_BOUND,
            environment=ENVIRONMENT_NAME,
            url=ENVIRONMENT_URL,
            revision=HEAD_A,
            binding_source=BINDING_SOURCE,
            observed_at=OBSERVED_AT,
        )
        result = RunResult(
            outcome=NEEDS_KARAN,
            reason="stale-head",
            head=HEAD_B,
            observed_at=OBSERVED_AT,
            configured_gates=(bound,),
        )

        payload = report.as_dict(result)

        disclosed = payload["configured_gates"][0]
        self.assertEqual(disclosed["evidence_mode"], GATE_EVIDENCE_UNBOUND)
        self.assertEqual(disclosed["revision"], "")
        self.assertFalse(payload["proof_scope"]["environment_revision_binding"])
        self.assertNotIn(HEAD_A, report.to_markdown(result))

    def test_a_time_without_a_head_is_not_rendered_as_an_observation(self) -> None:
        result = RunResult(
            outcome=NEEDS_KARAN,
            reason="unexpected-state",
            head=None,
            observed_at=OBSERVED_AT,
        )
        self.assertIsNone(report.as_dict(result)["observed_at"])
        markdown = report.to_markdown(result)
        self.assertIn("**Head observed at:** never", markdown)
        self.assertNotIn(OBSERVED_AT, markdown)


class GateEvidenceModeTests(DisclosureHarness):
    def test_a_local_gate_reports_local_scope_however_its_argv_reads(self) -> None:
        loop = self.build(
            gates=[gate(argv=["lane-gate-tests", "--url", f"{ENVIRONMENT_URL}/{{head}}"])]
        )
        self.script.add("lane-gate-tests", "200 OK\n")
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        disclosed = self.disclosure(result, "tests")
        self.assertEqual(disclosed["evidence_mode"], GATE_EVIDENCE_LOCAL)
        # The invocation is disclosed rather than read: a reader can see the
        # URL and the head token, and the mode still says what it says.
        self.assertIn(ENVIRONMENT_URL, disclosed["invocation"])
        self.assertIn("{head}", disclosed["invocation"])
        self.assertFalse(report.as_dict(result)["proof_scope"]["environment_revision_binding"])

    def test_an_external_gate_with_no_binding_evidence_says_exactly_that(self) -> None:
        loop = self.build(gates=[external_gate()])
        self.script.add("lane-gate-preview", "200 OK\n")
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        disclosed = self.disclosure(result, "preview")
        self.assertEqual(disclosed["evidence_mode"], GATE_EVIDENCE_UNBOUND)
        self.assertEqual(disclosed["evidence_statement"], UNBOUND_STATEMENT)
        self.assertEqual(disclosed["coverage"], COVERAGE)
        self.assertEqual(disclosed["environment"], ENVIRONMENT_NAME)
        self.assertEqual(disclosed["revision"], "")
        self.assertIn(UNBOUND_STATEMENT, report.to_markdown(result))
        self.assertFalse(report.as_dict(result)["proof_scope"]["environment_revision_binding"])

    def test_a_validated_envelope_earns_head_bound_with_its_evidence(self) -> None:
        loop = self.build(gates=[external_gate(binding=True)])
        self.script.add(
            "lane-gate-preview", "200 OK\n", after=records_environment(self.runner)
        )
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        disclosed = self.disclosure(result, "preview")
        self.assertEqual(disclosed["evidence_mode"], GATE_EVIDENCE_HEAD_BOUND)
        self.assertEqual(disclosed["revision"], HEAD_A)
        self.assertEqual(disclosed["url"], ENVIRONMENT_URL)
        self.assertEqual(disclosed["binding_source"], BINDING_SOURCE)
        self.assertEqual(disclosed["observed_at"], OBSERVED_AT)
        payload = report.as_dict(result)
        self.assertTrue(payload["proof_scope"]["environment_revision_binding"])
        self.assertIn("environment revision binding: **established**", report.to_markdown(result))

    def test_the_evidence_file_is_written_outside_the_gate_worktree(self) -> None:
        loop = self.build(gates=[external_gate(binding=True)])
        self.script.add(
            "lane-gate-preview", "200 OK\n", after=records_environment(self.runner)
        )
        self.review_round(HEAD_A)
        loop.run()

        call = next(
            item for item in self.runner.calls if item.argv[0] == "lane-gate-preview"
        )
        path = Path(call.argv[call.argv.index("--environment-evidence") + 1])
        self.assertFalse(path.is_relative_to(Path(call.cwd)))
        self.assertFalse(path.is_relative_to(self.source_repo))

    def test_evidence_the_run_cannot_reconcile_stops_before_the_reviewers(self) -> None:
        """Every negative envelope, from inside a real run rather than beside one.

        The mode a mismatched envelope must not reach is only half of it. The
        other half is *when* the run stops: a reviewer lane that has already
        judged a head this gate could not bind has spent a model on evidence the
        run was about to refuse, and the auditor after it would be reconciling
        artifacts about a head nobody proved anything external about.
        """
        cases = (
            ("wrote nothing", None),
            ("another revision", {"revision": HEAD_B}),
            ("another head", {"head": HEAD_B}),
            ("another gate", {"gate": "smoke"}),
            ("another environment", {"environment": "staging"}),
            ("another repository", {"repo": "other/repo"}),
            ("another pull request", {"pr": 8}),
            ("no observation time", {"observed_at": ""}),
        )
        for case, overrides in cases:
            with self.subTest(case=case):
                self.setUp()
                loop = self.build(gates=[external_gate(binding=True)])
                self.script.add(
                    "lane-gate-preview",
                    "200 OK\n",
                    after=(
                        None
                        if overrides is None
                        else records_environment(self.runner, **overrides)
                    ),
                )
                self.review_round(HEAD_A)

                result = loop.run()

                self.assertEqual(result.outcome, NEEDS_KARAN)
                self.assertEqual(result.reason, "environment-evidence")
                self.assertEqual(result.verdicts, ())
                self.assertFalse(
                    [call for call in self.runner.calls if "reviewer" in call.argv[0]],
                    "a reviewer lane ran on a head the run could not bind",
                )
                disclosed = self.disclosure(result, "preview")
                self.assertEqual(disclosed["evidence_mode"], GATE_EVIDENCE_UNBOUND)

    def test_a_failing_external_gate_blocks_rather_than_owing_its_envelope(self) -> None:
        """A gate that did not pass established nothing external, and says so."""
        loop = self.build(gates=[external_gate(binding=True)])
        self.script.add("lane-gate-preview", "503 from the preview\n", returncode=1)
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["gate-preview"], status="failure"),
        )

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertNotEqual(result.reason, "environment-evidence")
        self.assertEqual(
            self.disclosure(result, "preview")["evidence_mode"], GATE_EVIDENCE_UNBOUND
        )

    def test_a_binding_does_not_survive_the_push_that_invalidated_it(self) -> None:
        """New head, new observation: the previous head's binding is not evidence."""
        loop = self.build(gates=[external_gate(binding=True)])
        self.script.add(
            "lane-gate-preview", "200 OK\n", after=records_environment(self.runner)
        )
        self.script.add("lane-reviewer-A", reviewer_output(HEAD_A, [("blocking", "x", "s")]))
        self.script.add("lane-reviewer-B", reviewer_output(HEAD_A))
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=["x"]),
            after=lambda: self.remote.push(HEAD_B, comment=fix_comment(HEAD_B)),
        )
        # The gate on the new head answers, and records nothing this time. The
        # reviewers for that head are never reached, which is the point.
        self.script.add("lane-gate-preview", "200 OK\n")

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        self.assertEqual(result.reason, "environment-evidence")
        self.assertEqual(
            self.disclosure(result, "preview")["evidence_mode"], GATE_EVIDENCE_UNBOUND
        )

    def test_a_skipped_gate_is_still_part_of_the_configured_scope(self) -> None:
        loop = self.build(
            gates=[
                gate(),
                gate(name="visual", kind="visual", argv=["lane-gate-visual", "--head", "{head}"]),
            ]
        )
        self.script.add("lane-gate-tests", "ok\n")
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual([item.name for item in result.gates], ["tests"])
        payload = report.as_dict(result)
        self.assertEqual(
            [item["name"] for item in payload["configured_gates"]], ["tests", "visual"]
        )
        self.assertIn("none declared for this gate", report.to_markdown(result))


class ReviewerTopologyTests(DisclosureHarness):
    def test_each_lane_reports_its_adapter_and_its_artifact_runtime_claim(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        payload = report.as_dict(result)
        topology = payload["reviewer_topology"]
        self.assertEqual(
            [(item["role"], item["adapter"]) for item in topology],
            [
                ("reviewer-a", "lane-reviewer-A"),
                ("reviewer-b", "lane-reviewer-B"),
                ("integration-auditor", "lane-reviewer-Auditor"),
            ],
        )
        # The runtime is read off the body GitHub is showing, not off the file
        # the lane wrote, so what is attributed is what a reader can check.
        self.assertEqual({item["runtime"] for item in topology}, {"codex-exec/test"})
        self.assertFalse(payload["reviewer_adapters_shared"])
        self.assertTrue(payload["reviewer_runtimes_shared"])

    def test_one_adapter_behind_three_roles_is_named_as_one_adapter(self) -> None:
        shared = [
            {
                **lane,
                "argv": ["lane-reviewer-shared", *list(lane["argv"])[1:]],
            }
            for lane in _shipped_lanes()
        ]
        loop = self.build(reviewers=shared)
        for _ in range(3):
            self.script.add("lane-reviewer-shared", reviewer_output(HEAD_A))

        result = loop.run()

        payload = report.as_dict(result)
        self.assertTrue(payload["reviewer_adapters_shared"])
        self.assertTrue(payload["reviewer_runtimes_shared"])
        markdown = report.to_markdown(result)
        self.assertIn(
            "every reviewer lane ran the same configured adapter and declared the same runtime",
            markdown,
        )
        self.assertIn("heterogeneous reviewer independence was not established", markdown)

    def test_distinct_runtimes_still_do_not_establish_independence(self) -> None:
        """Diversity is not the claim; what executed is not measured either way."""
        runtimes = iter(("codex/one", "codex/two", "codex/three"))

        def artifact(*, argv, status, blocking):
            from _support import reviewer_artifact

            return reviewer_artifact(
                role=_flag(argv, "--role"),
                head=_flag(argv, "--head"),
                status=status,
                blocking=blocking,
                runtime=next(runtimes),
            )

        loop = self.build()
        self.runner.reviewer_artifact = artifact
        self.review_round(HEAD_A)

        result = loop.run()

        payload = report.as_dict(result)
        self.assertEqual(
            [item["runtime"] for item in payload["reviewer_topology"]],
            ["codex/one", "codex/two", "codex/three"],
        )
        self.assertFalse(payload["reviewer_runtimes_shared"])
        self.assertFalse(payload["proof_scope"]["heterogeneous_reviewer_independence"])
        self.assertIn(
            "heterogeneous reviewer independence was not established",
            report.to_markdown(result),
        )

    def test_a_lane_that_never_published_reports_no_runtime_claim(self) -> None:
        loop = self.build()
        self.runner.relay_failures = 1
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, NEEDS_KARAN)
        payload = report.as_dict(result)
        self.assertEqual([item["runtime"] for item in payload["reviewer_topology"]], [""])
        # Three unknowns are not three matching runtimes, and one lane shares
        # nothing with anybody.
        self.assertFalse(payload["reviewer_runtimes_shared"])
        self.assertIn("RUNTIME= not read back", report.to_markdown(result))


class ProofScopeTests(DisclosureHarness):
    """The five claims a green report is easily read as making."""

    OMISSIONS = (
        "environment_revision_binding",
        "heterogeneous_reviewer_independence",
        "merged_result_behavior",
        "deployment_or_production_health",
        "human_final_merge_review",
    )

    def test_a_merge_ready_run_still_states_every_omission(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        payload = report.as_dict(result)
        self.assertEqual(sorted(payload["proof_scope"]), sorted(self.OMISSIONS))
        self.assertEqual(set(payload["proof_scope"].values()), {False})
        markdown = report.to_markdown(result)
        for claim in (
            "merged-result behavior: **not established**",
            "deployment or production health: **not established**",
            "human final merge review and authorization: **not established**",
            "heterogeneous reviewer independence: **not established**",
        ):
            with self.subTest(claim=claim):
                self.assertIn(claim, markdown)
        # And the one thing a report may never soften.
        self.assertIn(report.MERGE_AUTHORITY, markdown)

    def test_the_only_claim_evidence_can_move_is_the_one_with_evidence(self) -> None:
        loop = self.build(gates=[external_gate(binding=True)])
        self.script.add(
            "lane-gate-preview", "200 OK\n", after=records_environment(self.runner)
        )
        self.review_round(HEAD_A)

        payload = report.as_dict(loop.run())

        self.assertTrue(payload["proof_scope"]["environment_revision_binding"])
        self.assertEqual(
            {key: value for key, value in payload["proof_scope"].items() if key != self.OMISSIONS[0]},
            {key: False for key in self.OMISSIONS[1:]},
        )
        # The note travels with the boolean rather than contradicting it.
        self.assertIn(
            "equal to this head", payload["proof_scope_notes"]["environment_revision_binding"]
        )

    def test_the_report_never_claims_the_configured_gates_are_enough(self) -> None:
        loop = self.build(gates=[external_gate()])
        self.script.add("lane-gate-preview", "200 OK\n")
        self.review_round(HEAD_A)

        result = loop.run()
        payload = report.as_dict(result)

        self.assertIn("does not infer gate sufficiency", payload["gate_coverage_declaration"])
        markdown = report.to_markdown(result)
        self.assertIn(f"operator-declared coverage: {COVERAGE}", markdown)
        self.assertIn(payload["gate_coverage_declaration"], markdown)


class DisclosureRedactionTests(DisclosureHarness):
    """The new surfaces pass the same final boundary every other one does."""

    SECRET = "ghp_" + "a" * 36

    def test_a_secret_in_a_gate_declaration_or_its_evidence_is_scrubbed(self) -> None:
        loop = self.build(
            gates=[
                external_gate(
                    binding=True,
                    coverage=f"smoke with {self.SECRET} in the operator's own sentence",
                )
            ]
        )
        self.script.add(
            "lane-gate-preview",
            "200 OK\n",
            after=records_environment(
                self.runner,
                url=f"{ENVIRONMENT_URL}?token={self.SECRET}",
                binding_source=f"header carrying {self.SECRET}",
            ),
        )
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertNotIn(self.SECRET, report.to_json(result))
        self.assertNotIn(self.SECRET, report.to_markdown(result))
        disclosed = self.disclosure(result, "preview")
        # Scrubbed, not dropped: the disclosure still says what it disclosed.
        self.assertIn("<redacted>", disclosed["coverage"])
        self.assertIn("<redacted>", disclosed["url"])
        self.assertEqual(disclosed["evidence_mode"], GATE_EVIDENCE_HEAD_BOUND)


def _shipped_lanes() -> list[dict[str, object]]:
    from _support import REVIEWER_LANES, reviewer_lane

    return [reviewer_lane(name, role, program) for name, role, program in REVIEWER_LANES]


def _flag(argv, name: str) -> str:
    for index, item in enumerate(argv[:-1]):
        if item == name:
            return argv[index + 1]
    return ""


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
