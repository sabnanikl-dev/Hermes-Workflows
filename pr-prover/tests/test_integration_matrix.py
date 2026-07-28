"""PAPI-93: the merged slices, proved as one composed contract.

Every other module here proves a seam. This one proves that the seams still hold
when they are wired together on a *sequence* of heads, which is the only shape
the real loop ever runs in. The cases are deliberately the ones no single slice
owns:

* **Anti-Goodhart.** A builder can satisfy a gate by removing the thing that
  failed it. Gates measure a proxy, and a loop that can edit its own repository
  can move the proxy — so the gates passing on the final head is exactly the
  state this fixture puts the tool in, and the question is whether anything else
  still says no. What answers is the adversarial review triad, and what the
  fixture pins is that the answer survives all the way to the reported outcome:
  no `merge-ready` is reachable on a head whose only qualification is a metric
  the builder rewrote.

* **Kill-switch declarations under composition.** ``reviewers.py`` rejects a
  single artifact that declares no attempted kill-switch. That is a parser test.
  This module asks the composed question the PAPI-90 adversarial mandate
  actually makes: after two fix cycles, on the head the run finally reports, do
  all three published artifacts still carry their attempted kill-switches, bound
  to that head and to their own distinct roles.

The scenarios run against the same deterministic doubles as the rest of the
suite: no network, no ``gh``, no real ``git``, and no real agent.
"""
from __future__ import annotations

import json
import struct
import sys
import unittest
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _support import (
    HEAD_A,
    HEAD_B,
    HEAD_C,
    RELAY_PROGRAM as RELAY,
    REVIEWER_LOGIN,
    builder_output,
    fix_comment,
    reviewer_artifact,
    reviewer_output,
)
from pr_prover.loop import BLOCKED, MERGE_READY
from pr_prover.report import as_dict, to_markdown
from pr_prover.reviewers import parse_artifact
from test_loop import LoopHarness

# The real defect, as the repository's own test gate reports it. The gate is
# named so the frozen blocker id below is the one the loop derives from it.
GATE = {"name": "tests", "argv": ["lane-gate-tests", "--head", "{head}"]}
GATE_BLOCKER_ID = "gate-tests"

# What an adversarial reviewer finds on the head that "fixed" it. Both are the
# reviewer noticing that the gap did not shrink — only the measurement did.
DELETED_TEST = (
    "blocking",
    "deleted-coverage",
    "the failing test was removed rather than repaired",
)
NARROWED_ASSERTION = (
    "blocking",
    "narrowed-assertion",
    "the assertion was narrowed until the defect no longer trips it",
)


class BadFaithPassTests(LoopHarness):
    """A builder that games the metric instead of closing the gap.

    The fixture is built so that the gamed head is genuinely clean by every
    mechanical measure the tool owns: the gate passes, the push is verified
    against all five views, the fix comment reads back, and every artifact
    lands. The only thing standing between that head and ``merge-ready`` is the
    review triad's judgement — which is precisely the property the anti-Goodhart
    case exists to pin down.
    """

    def push_after_builder(self, head: str) -> None:
        self.remote.push(head, comment=fix_comment(head))

    def gate(self, *, passes: bool) -> None:
        """One scripted run of the repository's own test gate."""
        self.script.add("lane-gate-tests", "", returncode=0 if passes else 1)

    def game_the_gate(self, *, triad_catches_it: bool) -> None:
        """The whole two-cycle scenario, with one knob.

        Cycle 1 removes the failing test; cycle 2 narrows what is left. The gate
        passes from the second head onward either way. ``triad_catches_it``
        chooses whether the reviewers do their job, which is the only difference
        between a blocked run and a merge-ready one.
        """
        # Head A: the real defect. The gate fails, so no reviewer is launched
        # and the frozen ledger is the gate finding alone.
        self.gate(passes=False)
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=[GATE_BLOCKER_ID]),
            after=lambda: self.push_after_builder(HEAD_B),
        )

        # Head B: the test is gone, so the gate is green. The triad is the only
        # thing that can see what actually happened.
        self.gate(passes=True)
        self.review_round(HEAD_B, [DELETED_TEST] if triad_catches_it else [])
        if not triad_catches_it:
            return
        self.script.add(
            "lane-builder",
            builder_output(HEAD_C, addressed=[DELETED_TEST[1]]),
            after=lambda: self.push_after_builder(HEAD_C),
        )

        # Head C: still green, still gamed.
        self.gate(passes=True)
        self.review_round(HEAD_C, [NARROWED_ASSERTION])

    def test_a_gamed_gate_cannot_buy_merge_ready_past_the_review_triad(self) -> None:
        loop = self.build(gates=[GATE])
        self.game_the_gate(triad_catches_it=True)

        result = loop.run()

        self.assertEqual(result.outcome, BLOCKED)
        self.assertEqual(result.reason, "attempt-cap-reached")
        self.assertEqual(result.head, HEAD_C)
        self.assertEqual(result.attempts_used, 2)
        self.assertEqual(result.exit_code, 1)
        self.assertTrue(self.script.exhausted)

    def test_the_final_head_is_blocked_while_every_gate_on_it_passes(self) -> None:
        """The heart of it: the proxy is green and the answer is still no.

        Without this assertion the case above would also pass on a run that
        simply never managed to fix the gate, which is an ordinary blocked head
        and proves nothing about metric gaming.
        """
        loop = self.build(gates=[GATE])
        self.game_the_gate(triad_catches_it=True)

        result = loop.run()

        self.assertTrue(result.gates, "the final head was evaluated with its gates")
        self.assertTrue(
            all(gate.passed for gate in result.gates),
            "the fixture must leave every mechanical gate green on the reported head",
        )
        blocking = result.classification.blocking
        self.assertEqual([item.finding.id for item in blocking], [NARROWED_ASSERTION[1]])
        # And the block came from a judging lane, not from the gate that was gamed.
        for item in blocking:
            with self.subTest(finding=item.finding.id):
                self.assertEqual(item.finding.provenance.role, "reviewer")
                self.assertNotEqual(item.finding.provenance.role, "gate")
                self.assertEqual(item.finding.head, HEAD_C)

    def test_the_run_never_records_merge_ready_on_any_gamed_head(self) -> None:
        """Not merely "the last outcome was blocked" — no head got a pass.

        ``merge-ready`` is written to the state file as the terminal outcome, so
        a run that briefly concluded it on the gamed second head and then moved
        on would be invisible to the assertion above.
        """
        loop = self.build(gates=[GATE])
        self.game_the_gate(triad_catches_it=True)

        result = loop.run()

        self.assertEqual(self.state()["outcome"], BLOCKED)
        self.assertNotEqual(result.outcome, MERGE_READY)
        # Substring, not membership: no event is ever the bare word, so the
        # run log has to be searched rather than asked whether it contains it.
        # The readiness guards ("… before report merge-ready") and the terminal
        # line are all it could appear in, and none of them may have run.
        for event in result.events:
            with self.subTest(event=event):
                self.assertNotIn(MERGE_READY, event)
                self.assertNotIn("no-blocking-findings", event)

    def test_the_gaming_really_did_satisfy_everything_except_the_triad(self) -> None:
        """Non-vacuity, and the sharpest statement of the Goodhart risk.

        Same builder, same deleted test, same green gate — only the reviewers
        change. If the triad shares the builder's framing, this head ships. That
        is the failure mode the adversarial mandate exists for, and it is why
        the mandate is load-bearing rather than stylistic.
        """
        loop = self.build(gates=[GATE])
        self.game_the_gate(triad_catches_it=False)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.head, HEAD_B)
        self.assertEqual(result.attempts_used, 1)
        self.assertTrue(all(gate.passed for gate in result.gates))
        self.assertTrue(self.script.exhausted)


class OrderedCleanPassTests(LoopHarness):
    """The whole legal clean path, in one run, down to the rendered report.

    Every step of this is asserted somewhere in the suite. What is not asserted
    anywhere is the *sequence*: inspect, then gates, then the three roles in
    their required order, then a zero-blocker classification, then a report that
    says all of it about one exact head. A slice that broke the ordering while
    keeping each step correct would pass every existing test.
    """

    def test_inspect_gates_the_three_roles_and_the_report_are_one_ordered_pass(self) -> None:
        loop = self.build(gates=[GATE])
        self.script.add("lane-gate-tests", "", returncode=0)
        self.review_round(HEAD_A)

        result = loop.run()
        payload = as_dict(result)

        # 1. Inspection bound the run to the live head, and said so.
        self.assertIn(f"inspected example/repo#7 at head {HEAD_A} (draft)", result.events)
        # 2. Gates ran before any judging lane, on that head.
        launched = [call.argv[0] for call in self.runner.calls if call.argv[0].startswith("lane-")]
        self.assertEqual(
            launched[:4],
            ["lane-gate-tests", "lane-reviewer-A", RELAY, "lane-reviewer-B"],
            "the gate must precede the acceptance lifecycle",
        )
        # 3. The three required roles, in the required order, each read back.
        self.assertEqual(
            [item["role"] for item in payload["transport"]],
            ["reviewer-a", "reviewer-b", "integration-auditor"],
        )
        self.assertTrue(all(item["complete"] for item in payload["transport"]))
        self.assertTrue(payload["transport_complete"])
        # 4. Zero blockers.
        self.assertEqual(payload["classification"]["blocking"], [])
        # 5. A report about one exact head, with authority left where it belongs.
        self.assertEqual(payload["outcome"], MERGE_READY)
        self.assertEqual(payload["head"], HEAD_A)
        self.assertEqual(payload["classification_head"], HEAD_A)
        self.assertTrue(payload["classification_head_current"])
        self.assertEqual(payload["attempts_used"], 0)
        self.assertTrue(all(gate["passed"] for gate in payload["gates"]))
        self.assertIn("Karan", payload["merge_authority"])
        self.assertIn(HEAD_A, to_markdown(result))
        self.assertTrue(self.script.exhausted)


class NativeGateMatrixTests(LoopHarness):
    """Several repository-native gates, not one stand-in for all of them.

    Gates are whatever argv the operator writes, so "lint, test, build, static"
    is a configuration rather than a concept the tool models. That is exactly
    why the composed behaviour is worth pinning: a run with four of them must
    run all four, in the configured order, each in its own checkout at the bound
    head — and must turn each failure into its own separately-actionable
    finding rather than one collapsed "gates failed".
    """

    NATIVE = tuple(
        {"name": name, "kind": "baseline", "argv": [f"lane-gate-{name}", "--head", "{head}"]}
        for name in ("lint", "tests", "build", "static")
    )

    def test_every_configured_native_gate_runs_in_order_at_the_bound_head(self) -> None:
        loop = self.build(gates=list(self.NATIVE))
        for gate in self.NATIVE:
            self.script.add(f"lane-gate-{gate['name']}", "", returncode=0)
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual(
            [gate.name for gate in result.gates], ["lint", "tests", "build", "static"]
        )
        gate_calls = [
            call for call in self.runner.calls if call.argv[0].startswith("lane-gate-")
        ]
        self.assertEqual(
            [call.argv[0] for call in gate_calls],
            ["lane-gate-lint", "lane-gate-tests", "lane-gate-build", "lane-gate-static"],
        )
        for call in gate_calls:
            with self.subTest(gate=call.argv[0]):
                self.assertEqual(list(call.argv[1:]), ["--head", HEAD_A])
        # One checkout each, and no two gates sharing one.
        directories = [call.cwd for call in gate_calls]
        self.assertEqual(len(set(directories)), 4, "two gates shared a checkout")
        self.assertTrue(self.script.exhausted)

    def test_each_failing_gate_becomes_its_own_actionable_blocker(self) -> None:
        """Two failures are two instructions, not one 'the gates failed'."""
        loop = self.build(gates=list(self.NATIVE))
        for gate in self.NATIVE:
            self.script.add(
                f"lane-gate-{gate['name']}",
                f"{gate['name']} said no",
                returncode=0 if gate["name"] in ("tests", "static") else 2,
            )
        # The ledger is what this test is about, so the builder declines it and
        # the run stops carrying the ledger rather than spending two cycles.
        self.script.add(
            "lane-builder",
            builder_output(HEAD_A, addressed=["gate-lint", "gate-build"], status="failure"),
            returncode=1,
        )

        result = loop.run()

        self.assertNotEqual(result.outcome, MERGE_READY)
        # Two separate ids, in the ledger's one canonical order — not one
        # collapsed "the gates failed" the builder cannot act on piecewise.
        self.assertEqual(
            [item.finding.id for item in result.classification.blocking],
            ["gate-build", "gate-lint"],
        )
        # Each carries the command to re-run and what that command said.
        for item in result.classification.blocking:
            with self.subTest(finding=item.finding.id):
                self.assertEqual(item.finding.provenance.role, "gate")
                self.assertEqual(item.finding.head, HEAD_A)
                self.assertIn(HEAD_A, item.finding.provenance.location.reference)
        # A failing gate stops the round before any judging lane is launched.
        self.assertNotIn(
            "lane-reviewer-A", [call.argv[0] for call in self.runner.calls]
        )


# -- fixture-local screenshot evidence -------------------------------------
#
# A visual gate's whole claim is that something was rendered and looked at. A
# fixture that scripts the *sentence* "captured 3 screenshots" proves only that
# a string can contain a SHA, so the deterministic visual lane below writes real
# image files instead, and the case reads them back. Everything here is test
# support: no image is produced, stored, or validated by ``pr_prover``, and
# nothing outside this module imports it. PNG is written and read from ``struct``
# and ``zlib`` because a fixture that needs a dependency to make its own evidence
# is a fixture that ends up skipped.

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class VisualEvidenceError(AssertionError):
    """Evidence offered for a head that is missing, unreadable, or another head's."""


@dataclass(frozen=True)
class Screenshot:
    """One image file that was found, decoded, and matched to its manifest entry."""

    path: Path
    width: int
    height: int


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)


def png_bytes(width: int, height: int) -> bytes:
    """A real, decodable PNG of exactly this size: signature, IHDR, IDAT, IEND."""
    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)  # 8-bit greyscale
    scanlines = b"".join(b"\x00" + bytes([(row * 7) % 256]) * width for row in range(height))
    return b"".join(
        (
            _PNG_SIGNATURE,
            _png_chunk(b"IHDR", header),
            _png_chunk(b"IDAT", zlib.compress(scanlines, 6)),
            _png_chunk(b"IEND", b""),
        )
    )


def read_png_size(data: bytes) -> tuple[int, int]:
    """Answer "is this an image, and how big" — or say why it is not one.

    Deliberately strict about the parts a fabricated artifact gets wrong: the
    signature, a well-formed 13-byte ``IHDR`` whose checksum matches its own
    bytes, and a terminating ``IEND``. Truncated, transplanted, and
    plain-text-with-a-``.png``-suffix files all fail here rather than being
    counted as screenshots.
    """
    if not data.startswith(_PNG_SIGNATURE):
        raise VisualEvidenceError("not an image: PNG signature missing")
    if len(data) < 33:
        raise VisualEvidenceError("not an image: truncated before the PNG header chunk")
    length = struct.unpack(">I", data[8:12])[0]
    kind, payload = data[12:16], data[16:29]
    if kind != b"IHDR" or length != 13:
        raise VisualEvidenceError(
            f"not an image: first chunk is {kind!r}/{length}, not a 13-byte IHDR"
        )
    if struct.unpack(">I", data[29:33])[0] != zlib.crc32(kind + payload) & 0xFFFFFFFF:
        raise VisualEvidenceError("corrupt image: PNG header checksum does not match")
    if not data.endswith(_png_chunk(b"IEND", b"")):
        raise VisualEvidenceError("corrupt image: PNG stream does not end with IEND")
    width, height = struct.unpack(">II", payload[:8])
    if width <= 0 or height <= 0:
        raise VisualEvidenceError(f"degenerate image dimensions: {width}x{height}")
    return width, height


def verify_screenshot_evidence(
    manifest: Path, *, head: str, disposable_root: Path
) -> tuple[Screenshot, ...]:
    """Prove a manifest and its files are this head's screenshot evidence.

    Every clause is one way the claim fails: no record was written at all, the
    record answers about a different head, it declares nothing, a declared file
    is absent, it was left in a checkout the run throws away, it is not an
    image, or the image is not the size the record says it is.
    """
    if not manifest.is_file():
        raise VisualEvidenceError(f"no screenshot manifest was written at {manifest}")
    record = json.loads(manifest.read_text(encoding="utf-8"))
    recorded = record.get("head")
    if recorded != head:
        raise VisualEvidenceError(
            f"screenshot evidence is bound to {recorded!r}, not to {head!r}"
        )
    declared = record.get("screenshots") or ()
    if not declared:
        raise VisualEvidenceError("the screenshot manifest declares no images")
    found: list[Screenshot] = []
    for entry in declared:
        path = Path(entry["path"])
        if not path.is_file():
            raise VisualEvidenceError(f"declared screenshot is missing: {path}")
        if path.is_relative_to(disposable_root):
            raise VisualEvidenceError(
                f"screenshot was left in a disposable lane checkout: {path}"
            )
        width, height = read_png_size(path.read_bytes())
        if (width, height) != (entry["width"], entry["height"]):
            raise VisualEvidenceError(
                f"{path.name} is {width}x{height}, but the manifest declares "
                f"{entry['width']}x{entry['height']}"
            )
        found.append(Screenshot(path=path, width=width, height=height))
    return tuple(found)


class VisualGateEvidenceTests(LoopHarness):
    """Browser/visual QA: selected deliberately, and evidenced on the exact head.

    Selection is a configured property of the run rather than something inferred
    from the diff, and `config.py` already refuses the flag without a gate. What
    composition adds is that the selected visual gate really is handed the bound
    head, really does run in a checkout of its own at that head, and that the
    evidence it left behind is *this head's* — readable image files, of the size
    they claim, outside the checkout the run is about to delete.

    The negative cases are the reason the positive one means anything. A lane
    that only prints a sentence containing the SHA satisfies none of them, which
    is the visual seam's version of the anti-Goodhart case above: a gate's own
    account of itself is not the evidence.
    """

    VISUAL = {
        "name": "visual",
        "kind": "visual",
        "argv": ["lane-gate-visual", "--head", "{head}", "--worktree", "{worktree}"],
    }
    # The viewports the scripted lane renders, and the sentence it prints about
    # them. The sentence names the manifest, so it points at the evidence rather
    # than standing in for it.
    VIEWPORTS = ((320, 568), (768, 1024), (1440, 900))
    EVIDENCE = "captured {count} screenshots at 320/768/1440 for {head}; manifest {manifest}"

    def setUp(self) -> None:
        super().setUp()
        # Where the lane retains what it rendered: a directory the run neither
        # owns nor cleans up, which is the point of the "outside the disposable
        # checkout" clause below.
        self.evidence_root = self.tmp / "visual-evidence"
        self.manifest = self.evidence_root / "manifest.json"
        # Filled in while the lane is live. A clean gate's checkout is removed
        # when it returns, so "which commit was it standing on" has to be asked
        # then, not afterwards.
        self.lane_cwd = ""
        self.lane_oid = ""

    def render(
        self,
        *,
        head: str | None = None,
        write: bool = True,
        corrupt: int | None = None,
        declared: Sequence[tuple[int, int]] | None = None,
    ) -> Callable[[], None]:
        """What the scripted visual lane leaves behind when it runs.

        The default is an honest lane: one real PNG per viewport plus a manifest
        naming the head the lane was actually handed, all of it written outside
        the checkout it rendered from. Each keyword withdraws exactly one
        property — the files, one file's readability, the declared sizes, or the
        head — so every negative case below names the single thing it removes.
        """

        def produce() -> None:
            call = self.runner.calls[-1]
            argv = list(call.argv)
            bound = argv[argv.index("--head") + 1]
            self.lane_cwd = str(Path(call.cwd).resolve())
            self.lane_oid = self.runner.worktree_oids[self.lane_cwd]
            if not write:
                return
            self.evidence_root.mkdir(parents=True, exist_ok=True)
            sizes = list(declared or self.VIEWPORTS)
            entries = []
            for index, (width, height) in enumerate(self.VIEWPORTS):
                path = self.evidence_root / f"{bound[:12]}-{width}x{height}.png"
                path.write_bytes(
                    b"screenshot pending; see the lane transcript"
                    if corrupt == index
                    else png_bytes(width, height)
                )
                entries.append(
                    {"path": str(path), "width": sizes[index][0], "height": sizes[index][1]}
                )
            self.manifest.write_text(
                json.dumps({"head": head or bound, "screenshots": entries}, indent=2),
                encoding="utf-8",
            )

        return produce

    def script_visual(self, **defect) -> None:
        self.script.add(
            "lane-gate-visual",
            self.EVIDENCE.format(
                count=len(self.VIEWPORTS), head=HEAD_A, manifest=self.manifest
            ),
            returncode=0,
            after=self.render(**defect),
        )

    def verify(self, head: str) -> tuple[Screenshot, ...]:
        return verify_screenshot_evidence(
            self.manifest, head=head, disposable_root=self.config.worktree_root
        )

    def test_a_required_visual_gate_is_evidenced_against_the_exact_head(self) -> None:
        loop = self.build(gates=[GATE, self.VISUAL], visual_qa_required=True)
        self.script.add("lane-gate-tests", "", returncode=0)
        self.script_visual()
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        visual = next(gate for gate in result.gates if gate.kind == "visual")
        self.assertTrue(visual.passed)
        call = next(
            call for call in self.runner.calls if call.argv[0] == "lane-gate-visual"
        )
        self.assertEqual(call.argv[2], HEAD_A)
        # Its own checkout, at the bound head, shared with no other lane.
        self.assertEqual(call.argv[4], call.cwd)
        self.assertEqual(self.lane_cwd, str(Path(call.cwd).resolve()))
        self.assertEqual(self.lane_oid, HEAD_A)
        self.assertEqual(
            len({c.cwd for c in self.runner.calls if c.argv[0].startswith("lane-gate-")}), 2
        )
        # The retained output is about this head and points at the record, which
        # is all a line of stdout is allowed to be worth.
        self.assertIn(HEAD_A, visual.output)
        self.assertIn(str(self.manifest), visual.output)
        # The evidence itself: files that exist, decode as images, are the size
        # they claim, and are recorded against the head the lane was handed.
        shots = self.verify(HEAD_A)
        self.assertEqual(
            [(shot.width, shot.height) for shot in shots], list(self.VIEWPORTS)
        )
        for shot in shots:
            with self.subTest(shot=shot.path.name):
                self.assertIn(HEAD_A[:12], shot.path.name)
        # And it outlived the checkout it was rendered from — a lane's own
        # working directory is deleted, so evidence kept there is not evidence.
        self.assertFalse(Path(self.lane_cwd).exists())
        self.assertEqual(result.retained_paths, ())

    def test_a_sentence_naming_the_head_is_not_screenshot_evidence(self) -> None:
        """The kill-switch every reviewer of this slice ran, as a standing case.

        The gate passes, its output names the exact head, and the loop is
        satisfied — because deciding what a browser lane's images prove is the
        gate's job, not this tool's. What the *fixture* may accept as this
        head's visual evidence is the question, and a claim does not answer it.
        """
        loop = self.build(gates=[self.VISUAL], visual_qa_required=True)
        self.script_visual(write=False)
        self.review_round(HEAD_A)

        result = loop.run()

        visual = next(gate for gate in result.gates if gate.kind == "visual")
        self.assertTrue(visual.passed)
        self.assertIn(HEAD_A, visual.output)
        with self.assertRaises(VisualEvidenceError) as caught:
            self.verify(HEAD_A)
        self.assertIn("no screenshot manifest", str(caught.exception))

    def test_a_declared_screenshot_that_does_not_decode_is_not_evidence(self) -> None:
        """A file of the right name and the wrong bytes is not an image."""
        loop = self.build(gates=[self.VISUAL], visual_qa_required=True)
        self.script_visual(corrupt=1)
        self.review_round(HEAD_A)

        loop.run()

        with self.assertRaises(VisualEvidenceError) as caught:
            self.verify(HEAD_A)
        self.assertIn("not an image", str(caught.exception))

    def test_a_screenshot_that_is_not_the_declared_size_is_not_evidence(self) -> None:
        """Non-vacuity for the dimension check: the manifest is not self-proving."""
        loop = self.build(gates=[self.VISUAL], visual_qa_required=True)
        self.script_visual(declared=[(320, 568), (768, 1024), (390, 844)])
        self.review_round(HEAD_A)

        loop.run()

        with self.assertRaises(VisualEvidenceError) as caught:
            self.verify(HEAD_A)
        self.assertIn("manifest declares 390x844", str(caught.exception))
        # The check is discriminating rather than refusing everything: the two
        # viewports whose declaration was honest decode to exactly what they say.
        record = json.loads(self.manifest.read_text(encoding="utf-8"))
        for entry in record["screenshots"][:2]:
            with self.subTest(shot=entry["path"]):
                self.assertEqual(
                    read_png_size(Path(entry["path"]).read_bytes()),
                    (entry["width"], entry["height"]),
                )

    def test_evidence_recorded_against_another_head_is_not_this_head_s(self) -> None:
        """Real images, real sizes, wrong commit — the M1 binding, for pixels."""
        loop = self.build(gates=[self.VISUAL], visual_qa_required=True)
        self.script_visual(head=HEAD_B)
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.head, HEAD_A)
        with self.assertRaises(VisualEvidenceError) as caught:
            self.verify(HEAD_A)
        self.assertIn(f"bound to {HEAD_B!r}", str(caught.exception))
        # The evidence is well-formed in every other respect: only the head is
        # wrong, so the case cannot pass by accident on a missing file.
        self.assertEqual(len(self.verify(HEAD_B)), len(self.VIEWPORTS))

    def test_a_visual_gate_is_not_selected_when_the_run_does_not_require_it(self) -> None:
        """Non-vacuity for the case above: selection really is the knob."""
        loop = self.build(gates=[GATE, self.VISUAL], visual_qa_required=False)
        self.script.add("lane-gate-tests", "", returncode=0)
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual([gate.name for gate in result.gates], ["tests"])
        self.assertNotIn(
            "lane-gate-visual", [call.argv[0] for call in self.runner.calls]
        )
        self.assertTrue(self.script.exhausted)

    def test_a_failing_visual_gate_blocks_the_head_it_was_measured_on(self) -> None:
        loop = self.build(gates=[self.VISUAL], visual_qa_required=True)
        self.script.add(
            "lane-gate-visual", "mobile overflow at 320px", returncode=3
        )
        self.script.add(
            "lane-builder",
            builder_output(HEAD_A, addressed=["gate-visual"], status="failure"),
            returncode=1,
        )

        result = loop.run()

        self.assertNotEqual(result.outcome, MERGE_READY)
        blocking = result.classification.blocking
        self.assertEqual([item.finding.id for item in blocking], ["gate-visual"])
        self.assertEqual(blocking[0].finding.head, HEAD_A)
        self.assertIn("mobile overflow", blocking[0].finding.provenance.evidence_excerpt)


class QuietLaneObservationTests(LoopHarness):
    """Silence is written down and reported, never converted into a failure.

    `test_trusted_agents.py` proves this about the real `SubprocessRunner`
    against real children. What that cannot show is that the loop *keeps* the
    distinction: a builder that produced nothing for half an hour and then
    exited cleanly must reach the report as a long quiet lane that succeeded,
    which is a different fact from a lane that stalled.
    """

    QUIET = 1_800.0
    RAN_FOR = 2_040.0

    def push_after_builder(self, head: str) -> None:
        self.remote.push(head, comment=fix_comment(head))

    def test_a_long_quiet_builder_that_exits_cleanly_still_succeeds(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A, [DELETED_TEST])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=[DELETED_TEST[1]]),
            after=lambda: self.push_after_builder(HEAD_B),
            duration=self.RAN_FOR,
            quiet_seconds=self.QUIET,
            # Alive and saying so, while saying nothing else.
            progress=((600.0, 0, 600.0), (1_200.0, 0, 1_200.0), (1_800.0, 0, 1_800.0)),
        )
        self.review_round(HEAD_B)

        result = loop.run()
        payload = as_dict(result)

        self.assertEqual(result.outcome, MERGE_READY)
        builder = next(
            lane for lane in payload["lanes"] if lane["lane"] == "builder (initial)"
        )
        self.assertEqual(builder["state"], "exited")
        self.assertEqual(builder["returncode"], 0)
        self.assertEqual(builder["quiet_seconds"], self.QUIET)
        self.assertEqual(builder["duration_seconds"], self.RAN_FOR)
        # The progress evidence that distinguishes quiet from stalled is kept.
        still_running = [event for event in result.events if "still running" in event]
        self.assertEqual(len(still_running), 3)
        self.assertIn(
            "builder (initial) still running at 1800s (0 bytes of output", still_running[-1]
        )

    def test_the_same_silence_under_a_timeout_fails_closed_instead(self) -> None:
        """The distinction, stated as a contrast rather than asserted alone.

        Identical quiet time, identical clean marker — only the process result
        differs, and that is the thing allowed to end a lane.
        """
        loop = self.build()
        self.review_round(HEAD_A, [DELETED_TEST])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=[DELETED_TEST[1]]),
            timed_out=True,
            returncode=124,
            duration=self.RAN_FOR,
            quiet_seconds=self.QUIET,
        )

        result = loop.run()

        self.assertNotEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.reason, "lane-failure")


class ArtifactCompositionStopTests(LoopHarness):
    """Two artifact defects, proved where they actually have to be caught.

    Both are exhaustively covered by the parser's own tests. Neither is covered
    through `loop.run()`, and the parser passing is not the claim that matters:
    what matters is that the loop consults it on the path that publishes, so a
    lane declaring the wrong role or nothing it attempted stops the run instead
    of putting a defective artifact on the pull request.
    """

    def prepare(self, body_for) -> None:
        self.runner.reviewer_artifact = body_for

    def test_an_artifact_declaring_no_kill_switch_never_reaches_the_pr(self) -> None:
        loop = self.build()
        self.review_round(HEAD_A)
        self.prepare(
            lambda argv, status, blocking: reviewer_artifact(
                role=argv[argv.index("--role") + 1],
                head=argv[argv.index("--head") + 1],
                status=status,
                blocking=blocking,
                kill_switches=(),
            )
        )

        result = loop.run()

        self.assertNotEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.reason, "relay-failure")
        self.assertEqual(
            [comment for comment in self.remote.comments if comment.author == REVIEWER_LOGIN],
            [],
            "a kill-switch-free artifact was published anyway",
        )
        self.assertNotIn(RELAY, [call.argv[0] for call in self.runner.calls])

    def test_an_artifact_declaring_another_lanes_role_stops_the_run(self) -> None:
        """The independence the three lanes exist for, at the artifact layer."""
        loop = self.build()
        self.review_round(HEAD_A)
        self.prepare(
            lambda argv, status, blocking: reviewer_artifact(
                role="integration-auditor",
                head=argv[argv.index("--head") + 1],
                status=status,
                blocking=blocking,
            )
        )

        result = loop.run()

        self.assertNotEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.reason, "relay-failure")
        self.assertNotIn(RELAY, [call.argv[0] for call in self.runner.calls])


class PostPushInvalidationTests(LoopHarness):
    """A push invalidates the previous head's evidence — checked on both halves.

    The invalidation is proven elsewhere in its positive direction: after a fix
    cycle, every accepted verdict carries the new head. Both cases here are the
    negative direction on the *second* head, which is the only place the two can
    come apart. Everything on the first head is bound before any push has
    happened, so a run that quietly re-used a rendered command or accepted a
    stale marker after a push would look identical there.
    """

    def push_after_builder(self, head: str) -> None:
        self.remote.push(head, comment=fix_comment(head))

    def test_the_gate_on_the_second_head_is_rendered_with_that_head(self) -> None:
        """The re-run gate measures the new commit, not the one it was frozen on.

        A gate whose ``{head}`` was substituted once and reused would re-run
        happily and re-report the *old* head's result as the new head's
        evidence — a green second cycle that proves nothing.
        """
        loop = self.build(gates=[GATE])
        self.script.add("lane-gate-tests", "", returncode=1)
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=[GATE_BLOCKER_ID]),
            after=lambda: self.push_after_builder(HEAD_B),
        )
        self.script.add("lane-gate-tests", "", returncode=0)
        self.review_round(HEAD_B)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.head, HEAD_B)
        # Exhaustion is part of the claim: a second gate that never ran would
        # otherwise leave this test asserting only the first one.
        self.assertTrue(self.script.exhausted, "the gate did not re-run on the new head")
        gate_calls = [
            call.argv for call in self.runner.calls if call.argv[0] == "lane-gate-tests"
        ]
        self.assertEqual(len(gate_calls), 2)
        self.assertEqual(list(gate_calls[0]), ["lane-gate-tests", "--head", HEAD_A])
        self.assertEqual(list(gate_calls[1]), ["lane-gate-tests", "--head", HEAD_B])

    def test_a_post_push_verdict_for_the_previous_head_stops_the_run(self) -> None:
        """The stale marker a fix cycle is the only way to produce.

        A reviewer relaunched on the new head that answers about the old one is
        reporting evidence the push already invalidated. Accepting it would let
        the head that *caused* the fix cycle sign off on the fix.
        """
        loop = self.build()
        self.review_round(HEAD_A, [DELETED_TEST])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=[DELETED_TEST[1]]),
            after=lambda: self.push_after_builder(HEAD_B),
        )
        # Relaunched for HEAD_B; answers about HEAD_A.
        self.script.add("lane-reviewer-A", reviewer_output(HEAD_A))

        result = loop.run()

        self.assertNotEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.reason, "stale-head")
        self.assertEqual(result.attempts_used, 1)
        # The stale lane stops the round: the lanes that judge after it never run.
        launched = [call.argv[0] for call in self.runner.calls if call.argv[0].startswith("lane-")]
        self.assertNotIn("lane-reviewer-B", launched[launched.index("lane-builder") :])
        self.assertNotIn("lane-reviewer-Auditor", launched[launched.index("lane-builder") :])


class KillSwitchCompositionTests(LoopHarness):
    """The adversarial declaration, checked after the slices are composed.

    A single artifact is validated by ``reviewers.py`` before its relay may
    publish it. What that cannot say is whether the stance survives two fix
    cycles and three heads — whether the artifacts standing on the head the run
    finally reports are all three of them, all bound to that head, all under
    their own role, and all still declaring what they tried.
    """

    def push_after_builder(self, head: str) -> None:
        self.remote.push(head, comment=fix_comment(head))

    def two_cycles_then_a_clean_head(self) -> None:
        self.review_round(HEAD_A, [DELETED_TEST])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_B, addressed=[DELETED_TEST[1]]),
            after=lambda: self.push_after_builder(HEAD_B),
        )
        self.review_round(HEAD_B, [NARROWED_ASSERTION])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_C, addressed=[NARROWED_ASSERTION[1]]),
            after=lambda: self.push_after_builder(HEAD_C),
        )
        self.review_round(HEAD_C)

    def artifacts_on(self, head: str) -> dict[str, object]:
        """Every published artifact this run's lanes bound to ``head``, by role."""
        found = {}
        for comment in self.remote.comments:
            if comment.author != REVIEWER_LOGIN:
                continue
            reading = parse_artifact(comment.body)
            if reading.ok and reading.claim.head == head:
                found[reading.claim.role] = reading.claim
        return found

    def test_all_three_roles_still_declare_a_kill_switch_on_the_final_head(self) -> None:
        loop = self.build()
        self.two_cycles_then_a_clean_head()

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        self.assertEqual(result.head, HEAD_C)
        self.assertEqual(result.attempts_used, 2)

        final = self.artifacts_on(HEAD_C)
        self.assertEqual(
            sorted(final), ["integration-auditor", "reviewer-a", "reviewer-b"]
        )
        for role, claim in sorted(final.items()):
            with self.subTest(role=role):
                self.assertTrue(
                    claim.kill_switches,
                    f"{role} published an artifact that declares nothing it attempted",
                )
                self.assertEqual(claim.head, HEAD_C)
                self.assertEqual(claim.status, "pass")
                self.assertTrue(claim.runtime)

    def test_the_earlier_heads_artifacts_stay_bound_to_the_heads_they_judged(self) -> None:
        """Composition must not let a declaration drift onto a later head.

        Every cycle republishes, so the PR accumulates artifacts. The one thing
        that would quietly destroy the per-head lifecycle is an artifact from an
        earlier head reading as evidence about this one.
        """
        loop = self.build()
        self.two_cycles_then_a_clean_head()

        loop.run()

        for head in (HEAD_A, HEAD_B, HEAD_C):
            with self.subTest(head=head):
                self.assertEqual(
                    sorted(self.artifacts_on(head)),
                    ["integration-auditor", "reviewer-a", "reviewer-b"],
                    f"the three roles did not each publish exactly once for {head}",
                )

    def test_a_failing_head_declares_its_kill_switches_too(self) -> None:
        """"I found a problem" and "I did not look" stay distinguishable.

        The declaration is most load-bearing on the artifact that reports a
        blocker, because that is the one a fix cycle is built from.
        """
        loop = self.build()
        self.review_round(HEAD_A, [DELETED_TEST])
        self.script.add(
            "lane-builder",
            builder_output(HEAD_A, addressed=[DELETED_TEST[1]], status="failure"),
            returncode=1,
        )

        loop.run()

        failing = [
            parse_artifact(comment.body).claim
            for comment in self.remote.comments
            if comment.author == REVIEWER_LOGIN and parse_artifact(comment.body).ok
        ]
        reviewer_a = next(claim for claim in failing if claim.role == "reviewer-a")
        self.assertEqual(reviewer_a.status, "fail")
        self.assertEqual(reviewer_a.blocking, 1)
        self.assertTrue(reviewer_a.kill_switches)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
