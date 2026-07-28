"""PAPI-100: a visual gate answers about what was rendered, not that it rendered.

The PAPI-96 pilot's visual gate produced nine PNGs and three PDFs and checked
their type and size. Every one of those checks passed, and the same review then
found, by looking at the output, that the print pages were missing the collapsed
operator-detail bodies entirely, that the failure table's cells lost their field
labels once the header row was hidden at 320px, and that small operational
numerals did not carry enough contrast to read. So the gate was green on a
rendering with three defects in it, because "a file of the right type and size
exists" and "the thing that had to be legible is legible" are different claims
and only the first was being made.

This module is the contract for the second claim, and the proof that it bites.

Where the responsibility sits
-----------------------------

Not in ``pr_prover``. Which detail bodies a print page owes, which columns a
mobile table must keep labelled, and which numerals are small enough to need a
contrast floor are all facts about one site, and a tool that knew them would be
a browser/accessibility framework wearing a merge-readiness tool's name — which
`MISSION.md` rules out. They live in the **operator-owned configured visual
gate**: ``pr-prover`` selects it, hands it the bound head and its own checkout,
and blocks the head when it exits nonzero. What is repository-owned is the
*shape* of the obligation, which is what is written down and proved here:

* the gate's report binds to the exact head, and declares an outcome for every
  assertion the run requires — a required assertion the report simply does not
  mention is a failure, not a pass, because silence is how a gate stops
  measuring something without anyone noticing;
* the rendered artifacts are read, not listed. The required print bodies are
  pulled out of the PDF's own content streams, so a gate cannot satisfy the
  print assertion by writing a PDF that does not contain them;
* the contrast assertion is *computed* here from the colours and size the gate
  recorded, by the ordinary WCAG relative-luminance formula, so a gate cannot
  satisfy it by declaring "contrast: ok". A design-token assertion is the one
  alternative, and the token has to be one the run approved;
* the screenshots and PDFs are retained as human evidence and are necessary —
  but on their own they are never sufficient, which is the case the pilot got
  wrong and the one asserted explicitly below.

The label assertion is the honest exception, and is written as one: no amount of
decoding a PNG recovers the accessible name of a table cell, so what the gate
records there is a measurement rather than a derivation. What this module
enforces is that the measurement was taken *for every required column* and that
a missing or empty label fails — not that the gate's own summary is believed.

Everything here is test support. No image, PDF, colour, or assertion is produced
or read by ``pr_prover`` itself, and nothing outside this module imports it. The
PDF is written and read from the standard library for the same reason the PNG
fixture is: a fixture that needs a dependency to make its own evidence is a
fixture that ends up skipped.
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _support import HEAD_A, HEAD_B, RELAY_PROGRAM as RELAY, builder_output
from pr_prover.loop import MERGE_READY
from test_integration_matrix import png_bytes, read_png_size
from test_loop import LoopHarness


class SemanticVisualError(AssertionError):
    """Rendered output that does not carry a required semantic property."""


# -- the print surface, written and read as a real PDF ---------------------

_PDF_TEXT = re.compile(rb"\((?P<literal>(?:\\.|[^\\()])*)\)\s*Tj")
_PDF_STREAM = re.compile(rb"stream\r?\n(?P<body>.*?)\r?\nendstream", re.DOTALL)


def _pdf_escape(text: str) -> bytes:
    encoded = text.encode("latin-1", "replace")
    for character, replacement in ((b"\\", b"\\\\"), (b"(", b"\\("), (b")", b"\\)")):
        encoded = encoded.replace(character, replacement)
    return encoded


def pdf_bytes(pages: Sequence[Sequence[str]]) -> bytes:
    """A real PDF whose pages carry exactly these lines of text.

    Structurally complete — header, numbered objects, cross-reference table,
    trailer, ``%%EOF`` — and deliberately uncompressed, so the text below is
    recovered from the page content streams the document actually contains
    rather than from anything written alongside it.
    """
    font = 3 + 2 * len(pages)
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids ["
        + b" ".join(b"%d 0 R" % (3 + 2 * index) for index in range(len(pages)))
        + b"] /Count %d >>" % len(pages),
    ]
    for index, lines in enumerate(pages):
        content = [b"BT", b"/F1 11 Tf", b"72 720 Td"]
        for line in lines:
            content += [b"(" + _pdf_escape(line) + b") Tj", b"0 -14 Td"]
        content.append(b"ET")
        body = b"\n".join(content)
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources "
            b"<< /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>" % (font, 4 + 2 * index)
        )
        objects.append(
            b"<< /Length %d >>\nstream\n" % len(body) + body + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, payload in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % number + payload + b"\nendobj\n"
    start = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for offset in offsets:
        out += b"%010d 00000 n \n" % offset
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1,
        start,
    )
    return bytes(out)


def pdf_text(data: bytes) -> str:
    """The text a reader would see, recovered from the document's own streams.

    Refuses a file that is not a PDF and one that carries no page content at
    all, so "the print assertion passed" can never mean "there was nothing to
    read".
    """
    if not data.startswith(b"%PDF-"):
        raise SemanticVisualError("not a print artifact: PDF header missing")
    if b"%%EOF" not in data:
        raise SemanticVisualError("corrupt print artifact: PDF has no %%EOF trailer")
    streams = _PDF_STREAM.findall(data)
    if not streams:
        raise SemanticVisualError("corrupt print artifact: PDF carries no page content stream")
    shown: list[str] = []
    for body in streams:
        for match in _PDF_TEXT.finditer(body):
            literal = match.group("literal")
            for escape, plain in ((b"\\(", b"("), (b"\\)", b")"), (b"\\\\", b"\\")):
                literal = literal.replace(escape, plain)
            shown.append(literal.decode("latin-1"))
    return "\n".join(shown)


# -- contrast, computed rather than declared -------------------------------


def _channel(value: int) -> float:
    ratio = value / 255
    return ratio / 12.92 if ratio <= 0.04045 else ((ratio + 0.055) / 1.055) ** 2.4


def relative_luminance(colour: str) -> float:
    """WCAG relative luminance of an ``#rrggbb`` colour."""
    text = colour.lstrip("#")
    if len(text) != 6 or any(character not in "0123456789abcdefABCDEF" for character in text):
        raise SemanticVisualError(f"not an #rrggbb colour: {colour!r}")
    red, green, blue = (int(text[at : at + 2], 16) for at in (0, 2, 4))
    return 0.2126 * _channel(red) + 0.7152 * _channel(green) + 0.0722 * _channel(blue)


def contrast_ratio(foreground: str, background: str) -> float:
    """The WCAG contrast ratio between two colours, lighter over darker."""
    first, second = relative_luminance(foreground), relative_luminance(background)
    lighter, darker = max(first, second), min(first, second)
    return (lighter + 0.05) / (darker + 0.05)


# -- the semantic gate contract -------------------------------------------


@dataclass(frozen=True)
class VisualContract:
    """What the operator's configured gate is required to have proved.

    Site-specific by nature — these are facts about one report's pages, not
    about pull requests — which is exactly why they are a value the run
    configures rather than anything ``pr_prover`` knows.
    """

    print_detail_bodies: tuple[str, ...]
    mobile_columns: tuple[str, ...]
    small_text: tuple[str, ...]
    approved_tokens: frozenset[str] = frozenset()
    # WCAG 2.1 AA for text below large-text size. Small operational numerals and
    # labels are the case it exists for.
    minimum_contrast: float = 4.5


def verify_visual_semantics(
    report: Path, *, head: str, contract: VisualContract, disposable_root: Path
) -> dict[str, object]:
    """Prove this head's rendering carries the semantics the contract requires.

    Returns the measurements that were checked, so a caller can assert on what
    was proved rather than only on the absence of an exception. Every clause is
    one way a gate can be green over a rendering nobody could use.
    """
    if not report.is_file():
        raise SemanticVisualError(f"no visual semantics report was written at {report}")
    record = json.loads(report.read_text(encoding="utf-8"))
    if record.get("head") != head:
        raise SemanticVisualError(
            f"visual evidence is bound to {record.get('head')!r}, not to {head!r}"
        )

    # 1. The human evidence. Necessary, and on its own never sufficient: every
    #    later clause still has to be satisfied after this one passes.
    declared = record.get("screenshots") or ()
    if not declared:
        raise SemanticVisualError("the visual report declares no screenshots")
    for entry in declared:
        path = Path(entry["path"])
        if not path.is_file():
            raise SemanticVisualError(f"declared screenshot is missing: {path}")
        if path.is_relative_to(disposable_root):
            raise SemanticVisualError(f"screenshot was left in a disposable checkout: {path}")
        width, height = read_png_size(path.read_bytes())
        if (width, height) != (entry["width"], entry["height"]):
            raise SemanticVisualError(
                f"{path.name} is {width}x{height}, but the report declares "
                f"{entry['width']}x{entry['height']}"
            )

    # 2. Print detail bodies, read out of the PDF rather than asserted about it.
    printed = record.get("print")
    if not printed:
        raise SemanticVisualError(
            "the visual report declares no print artifact, so the print assertions "
            "were not measured on anything"
        )
    pdf = Path(printed["path"])
    if not pdf.is_file():
        raise SemanticVisualError(f"declared print artifact is missing: {pdf}")
    text = pdf_text(pdf.read_bytes())
    missing = [body for body in contract.print_detail_bodies if body not in text]
    if missing:
        raise SemanticVisualError(
            "the print output omits required collapsed detail bodies: "
            + ", ".join(repr(body) for body in missing)
        )

    # 3. Mobile field labels. Hiding the header row is a legitimate layout
    #    choice; letting the cells lose their field names with it is not, so
    #    every required column has to be recorded and has to carry a label.
    labels: Mapping[str, str] = {
        entry.get("column", ""): (entry.get("label") or "").strip()
        for entry in record.get("mobile_fields") or ()
    }
    unmeasured = [column for column in contract.mobile_columns if column not in labels]
    if unmeasured:
        raise SemanticVisualError(
            "the mobile rendering was not measured for required failure-table "
            "columns: " + ", ".join(unmeasured)
        )
    unlabelled = [column for column in contract.mobile_columns if not labels[column]]
    if unlabelled:
        raise SemanticVisualError(
            "mobile failure-table values carry no accessible field label: "
            + ", ".join(unlabelled)
        )

    # 4. Small operational text: a measured ratio, or an approved token. The
    #    ratio is recomputed here from the colours the gate recorded, so the
    #    gate reports observations and this decides whether they pass.
    measured: dict[str, float] = {}
    recorded = {entry.get("name", ""): entry for entry in record.get("small_text") or ()}
    for name in contract.small_text:
        entry = recorded.get(name)
        if entry is None:
            raise SemanticVisualError(
                f"required small operational text {name!r} was not measured at all"
            )
        token = entry.get("token")
        if token:
            if token not in contract.approved_tokens:
                raise SemanticVisualError(
                    f"{name!r} claims design token {token!r}, which this run does not approve"
                )
            continue
        ratio = contrast_ratio(entry["foreground"], entry["background"])
        measured[name] = ratio
        if ratio < contract.minimum_contrast:
            raise SemanticVisualError(
                f"{name!r} renders at {ratio:.2f}:1, below the required "
                f"{contract.minimum_contrast:.1f}:1 at {entry.get('font_px')}px"
            )
    return {"screenshots": len(declared), "print_text": text, "contrast": measured}


# -- one honest rendering, and the ways it goes wrong ----------------------

CONTRACT = VisualContract(
    print_detail_bodies=(
        "Operator detail: retry budget exhausted after 3 attempts",
        "Operator detail: upstream returned 502 for 41s",
    ),
    mobile_columns=("Check", "Failure", "First seen"),
    small_text=("run-id numerals", "threshold caption"),
    approved_tokens=frozenset({"text-critical-on-surface"}),
)
VIEWPORTS = ((320, 568), (768, 1024), (1440, 900))
# Grey on white, both sides of the 4.5:1 floor: #595959 measures about 7.0:1 and
# #949494 about 3.0:1, so the failing case fails on the arithmetic rather than on
# a threshold picked to make it fail.
READABLE, TOO_FAINT = "#595959", "#949494"


class VisualEvidence:
    """What an operator's visual gate leaves behind for one head.

    A plain object rather than a test case, because both the focused cases and
    the composed loop case below need to render evidence and only one of them is
    a fixture for it.
    """

    def __init__(self, root: Path) -> None:
        self.evidence = root / "visual-evidence"
        self.disposable = root / "worktrees"
        self.disposable.mkdir(parents=True, exist_ok=True)
        self.report = self.evidence / "semantics.json"

    def render(
        self,
        *,
        head: str = HEAD_A,
        print_bodies: Sequence[str] | None = None,
        mobile_labels: bool = True,
        drop_column: str | None = None,
        contrast: str = READABLE,
        token: str | None = None,
        drop_small_text: bool = False,
        screenshots: bool = True,
        print_artifact: bool = True,
    ) -> Path:
        """Render one head's evidence, with exactly one property withdrawn.

        The default is an honest gate: three screenshots, a print PDF whose
        pages really carry the required detail bodies, labelled mobile cells,
        and legible small text. Each keyword withdraws exactly one of those, so
        every case below names the single property it removes.
        """
        self.evidence.mkdir(parents=True, exist_ok=True)
        entries = []
        if screenshots:
            for width, height in VIEWPORTS:
                path = self.evidence / f"{head[:12]}-{width}x{height}.png"
                path.write_bytes(png_bytes(width, height))
                entries.append({"path": str(path), "width": width, "height": height})

        record: dict[str, object] = {"head": head, "screenshots": entries}

        if print_artifact:
            bodies = (
                list(CONTRACT.print_detail_bodies) if print_bodies is None else list(print_bodies)
            )
            pdf = self.evidence / f"{head[:12]}-print.pdf"
            pdf.write_bytes(
                pdf_bytes(
                    [
                        ["Run report", "Checks: 7 passed, 2 failed"],
                        ["Failure detail", *bodies],
                    ]
                )
            )
            record["print"] = {"path": str(pdf)}

        fields = []
        for column in CONTRACT.mobile_columns:
            if column == drop_column:
                continue
            fields.append(
                {"column": column, "value": "…", "label": column if mobile_labels else ""}
            )
        record["mobile_fields"] = fields

        if not drop_small_text:
            small: list[dict[str, object]] = [
                {
                    "name": "run-id numerals",
                    "font_px": 12,
                    "foreground": contrast,
                    "background": "#ffffff",
                }
            ]
            caption: dict[str, object] = {"name": "threshold caption", "font_px": 11}
            if token is None:
                caption.update({"foreground": contrast, "background": "#ffffff"})
            else:
                caption["token"] = token
            small.append(caption)
            record["small_text"] = small

        self.report.write_text(json.dumps(record, indent=2), encoding="utf-8")
        return self.report

    def verify(self, *, head: str = HEAD_A, contract: VisualContract = CONTRACT):
        return verify_visual_semantics(
            self.report, head=head, contract=contract, disposable_root=self.disposable
        )


class VisualSemanticsFixture(unittest.TestCase):
    """One temporary directory, and the evidence writer that renders into it."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-visual-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.gate = VisualEvidence(self.tmp)
        self.evidence = self.gate.evidence
        self.disposable = self.gate.disposable
        self.report = self.gate.report
        self.render = self.gate.render
        self.verify = self.gate.verify


class SemanticVisualProofTests(VisualSemanticsFixture):
    def test_a_complete_rendering_satisfies_the_contract(self) -> None:
        """The control. Without it every case below could pass vacuously."""
        self.render()
        proved = self.verify()
        self.assertEqual(proved["screenshots"], 3)
        for body in CONTRACT.print_detail_bodies:
            with self.subTest(body=body):
                self.assertIn(body, proved["print_text"])
        self.assertGreaterEqual(min(proved["contrast"].values()), CONTRACT.minimum_contrast)

    def test_files_of_the_right_type_and_size_do_not_satisfy_the_gate(self) -> None:
        """The PAPI-96 failure exactly: nine PNGs, three PDFs, three real defects.

        Every screenshot decodes, is the size it claims, and sits outside the
        disposable checkout; the PDF is a structurally valid PDF. The pilot's
        gate had nothing left to check at this point and went green.
        """
        self.render(print_bodies=[], mobile_labels=False, contrast=TOO_FAINT)

        record = json.loads(self.report.read_text(encoding="utf-8"))
        for entry in record["screenshots"]:
            with self.subTest(screenshot=Path(entry["path"]).name):
                data = Path(entry["path"]).read_bytes()
                self.assertEqual(read_png_size(data), (entry["width"], entry["height"]))
        self.assertTrue(Path(record["print"]["path"]).read_bytes().startswith(b"%PDF-"))

        with self.assertRaises(SemanticVisualError):
            self.verify()

    def test_absent_print_detail_bodies_fail_the_gate(self) -> None:
        """The PDF is real, paginated, and readable — and does not say the thing."""
        self.render(print_bodies=["Failure detail omitted for brevity"])
        with self.assertRaises(SemanticVisualError) as caught:
            self.verify()
        message = str(caught.exception)
        self.assertIn("omits required collapsed detail bodies", message)
        self.assertIn("retry budget exhausted", message)

    def test_one_missing_detail_body_out_of_two_still_fails(self) -> None:
        """Partial print output is not proportional credit."""
        self.render(print_bodies=[CONTRACT.print_detail_bodies[0]])
        with self.assertRaises(SemanticVisualError) as caught:
            self.verify()
        self.assertIn("upstream returned 502", str(caught.exception))

    def test_mobile_values_that_lost_their_labels_fail_the_gate(self) -> None:
        self.render(mobile_labels=False)
        with self.assertRaises(SemanticVisualError) as caught:
            self.verify()
        message = str(caught.exception)
        self.assertIn("carry no accessible field label", message)
        for column in CONTRACT.mobile_columns:
            with self.subTest(column=column):
                self.assertIn(column, message)

    def test_a_column_the_gate_never_measured_is_not_a_pass(self) -> None:
        """Silence is the way an assertion stops being made without anyone noticing."""
        self.render(drop_column="Failure")
        with self.assertRaises(SemanticVisualError) as caught:
            self.verify()
        self.assertIn("was not measured for required failure-table columns", str(caught.exception))
        self.assertIn("Failure", str(caught.exception))

    def test_small_text_below_the_contrast_floor_fails_the_gate(self) -> None:
        self.render(contrast=TOO_FAINT)
        with self.assertRaises(SemanticVisualError) as caught:
            self.verify()
        self.assertIn("below the required 4.5:1", str(caught.exception))

    def test_the_contrast_ratio_is_computed_not_taken_from_the_report(self) -> None:
        """A gate cannot pass this assertion by declaring that it passes.

        The report carries colours and a size; the verdict is arithmetic done
        here. The two named greys sit either side of the floor, and the
        published WCAG values for them are what is asserted.
        """
        self.assertAlmostEqual(contrast_ratio(READABLE, "#ffffff"), 7.0, places=1)
        self.assertAlmostEqual(contrast_ratio(TOO_FAINT, "#ffffff"), 3.0, places=1)
        self.assertAlmostEqual(contrast_ratio("#000000", "#ffffff"), 21.0, places=1)
        self.assertAlmostEqual(contrast_ratio("#ffffff", "#ffffff"), 1.0, places=1)
        # ...and it is symmetric, so which colour the gate calls foreground
        # cannot change the verdict.
        self.assertAlmostEqual(
            contrast_ratio(TOO_FAINT, "#ffffff"), contrast_ratio("#ffffff", TOO_FAINT)
        )

    def test_an_approved_design_token_satisfies_the_assertion(self) -> None:
        self.render(token="text-critical-on-surface")
        self.assertEqual(self.verify()["contrast"].keys(), {"run-id numerals"})

    def test_an_unapproved_design_token_does_not(self) -> None:
        """Otherwise the token escape hatch answers every contrast question."""
        self.render(token="text-muted")
        with self.assertRaises(SemanticVisualError) as caught:
            self.verify()
        self.assertIn("which this run does not approve", str(caught.exception))

    def test_small_text_the_gate_never_measured_fails(self) -> None:
        self.render(drop_small_text=True)
        with self.assertRaises(SemanticVisualError) as caught:
            self.verify()
        self.assertIn("was not measured at all", str(caught.exception))

    def test_a_report_for_another_head_is_not_this_head_s_evidence(self) -> None:
        self.render(head=HEAD_B)
        with self.assertRaises(SemanticVisualError) as caught:
            self.verify(head=HEAD_A)
        self.assertIn("bound to", str(caught.exception))

    def test_a_missing_report_is_not_a_pass(self) -> None:
        with self.assertRaises(SemanticVisualError):
            self.verify()

    def test_a_rendering_with_no_print_artifact_cannot_pass_the_print_assertion(self) -> None:
        self.render(print_artifact=False)
        with self.assertRaises(SemanticVisualError) as caught:
            self.verify()
        self.assertIn("declares no print artifact", str(caught.exception))

    def test_screenshots_left_in_the_disposable_checkout_are_not_evidence(self) -> None:
        """A lane's own checkout is deleted, so evidence inside it is already gone."""
        self.render()
        record = json.loads(self.report.read_text(encoding="utf-8"))
        inside = self.disposable / "gate-visual" / "shot.png"
        inside.parent.mkdir(parents=True)
        inside.write_bytes(png_bytes(320, 568))
        record["screenshots"][0] = {"path": str(inside), "width": 320, "height": 568}
        self.report.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaises(SemanticVisualError) as caught:
            self.verify()
        self.assertIn("disposable checkout", str(caught.exception))

    def test_a_print_artifact_that_is_not_a_pdf_fails(self) -> None:
        self.render()
        record = json.loads(self.report.read_text(encoding="utf-8"))
        fake = self.evidence / "not-really.pdf"
        fake.write_text("print output pending", encoding="utf-8")
        record["print"] = {"path": str(fake)}
        self.report.write_text(json.dumps(record), encoding="utf-8")
        with self.assertRaises(SemanticVisualError) as caught:
            self.verify()
        self.assertIn("PDF header missing", str(caught.exception))

    def test_the_pdf_round_trips_the_text_it_was_given(self) -> None:
        """The reader has to be non-vacuous before the print assertion means anything."""
        data = pdf_bytes([["first page line"], ["second (parenthesised) line", "third"]])
        text = pdf_text(data)
        for line in ("first page line", "second (parenthesised) line", "third"):
            with self.subTest(line=line):
                self.assertIn(line, text)
        self.assertNotIn("never rendered", text)


class ConfiguredVisualGateTests(LoopHarness):
    """The semantics belong to the configured gate, and the gate blocks the head.

    This is the composition half: ``pr-prover`` does not learn what a legible
    report looks like, it runs the operator's gate at the bound head in a
    checkout of its own and believes its exit status. So the fixture below makes
    that exit status *be* the semantic verdict over really-rendered files —
    computed by :func:`verify_visual_semantics`, not chosen by the test — and
    then asks what the run does with it.
    """

    VISUAL = {
        "name": "visual",
        "kind": "visual",
        "argv": ["lane-gate-visual", "--head", "{head}", "--worktree", "{worktree}"],
    }
    GATE = {"name": "tests", "argv": ["lane-gate-tests", "--head", "{head}"]}

    def setUp(self) -> None:
        super().setUp()
        self.gate = VisualEvidence(self.tmp / "visual")
        self.reason = ""

    def script_visual(self, **defect) -> int:
        """Render the evidence, then script the gate to report what it proves.

        The gate's exit status is the semantic verdict over the files just
        rendered — computed here by :func:`verify_visual_semantics`, not a
        number chosen to make the case come out a particular way.
        """
        self.gate.render(**defect)
        try:
            verify_visual_semantics(
                self.gate.report,
                head=HEAD_A,
                contract=CONTRACT,
                disposable_root=self.config.worktree_root,
            )
            code = 0
        except SemanticVisualError as error:
            code = 1
            self.reason = str(error)
        self.script.add(
            "lane-gate-visual",
            f"semantic visual gate for {HEAD_A}; report {self.gate.report}",
            returncode=code,
        )
        return code

    def decline_the_ledger(self) -> None:
        """The builder reports back that it did not close the visual blocker.

        These cases are about the gate, so the run stops on a reported failure
        rather than spending two fix cycles re-rendering a fixture.
        """
        self.script.add(
            "lane-builder",
            builder_output(HEAD_A, addressed=["gate-visual"], status="failure"),
            returncode=1,
        )

    def test_a_rendering_that_carries_its_semantics_lets_the_head_through(self) -> None:
        loop = self.build(gates=[self.GATE, self.VISUAL], visual_qa_required=True)
        self.script.add("lane-gate-tests", "", returncode=0)
        self.assertEqual(self.script_visual(), 0, "the control must really be green")
        self.review_round(HEAD_A)

        result = loop.run()

        self.assertEqual(result.outcome, MERGE_READY)
        visual = next(gate for gate in result.gates if gate.kind == "visual")
        self.assertTrue(visual.passed)
        call = next(c for c in self.runner.calls if c.argv[0] == "lane-gate-visual")
        self.assertEqual(call.argv[2], HEAD_A)

    def test_a_rendering_missing_its_print_bodies_blocks_the_head(self) -> None:
        """Files exist, the gate is selected, and the head does not go through."""
        loop = self.build(gates=[self.GATE, self.VISUAL], visual_qa_required=True)
        self.script.add("lane-gate-tests", "", returncode=0)
        self.assertEqual(self.script_visual(print_bodies=[]), 1)
        self.decline_the_ledger()

        result = loop.run()

        self.assertNotEqual(result.outcome, MERGE_READY)
        # The visual gate is the blocker, named as its own actionable finding.
        self.assertIn(
            "gate-visual", [item.finding.id for item in result.classification.blocking]
        )
        self.assertIn("omits required collapsed detail bodies", self.reason)

    def test_a_rendering_that_lost_its_mobile_labels_blocks_the_head(self) -> None:
        loop = self.build(gates=[self.GATE, self.VISUAL], visual_qa_required=True)
        self.script.add("lane-gate-tests", "", returncode=0)
        self.assertEqual(self.script_visual(mobile_labels=False), 1)
        self.decline_the_ledger()

        result = loop.run()

        self.assertNotEqual(result.outcome, MERGE_READY)
        self.assertIn("carry no accessible field label", self.reason)

    def test_a_rendering_below_the_contrast_floor_blocks_the_head(self) -> None:
        loop = self.build(gates=[self.GATE, self.VISUAL], visual_qa_required=True)
        self.script.add("lane-gate-tests", "", returncode=0)
        self.assertEqual(self.script_visual(contrast=TOO_FAINT), 1)
        self.decline_the_ledger()

        result = loop.run()

        self.assertNotEqual(result.outcome, MERGE_READY)
        self.assertIn("below the required 4.5:1", self.reason)

    def test_a_failing_visual_gate_stops_the_round_before_any_reviewer(self) -> None:
        """A head nobody can read is not sent to three models to be judged."""
        loop = self.build(gates=[self.GATE, self.VISUAL], visual_qa_required=True)
        self.script.add("lane-gate-tests", "", returncode=0)
        self.script_visual(contrast=TOO_FAINT)
        self.decline_the_ledger()

        result = loop.run()

        self.assertNotEqual(result.outcome, MERGE_READY)
        self.assertNotIn("lane-reviewer-A", [call.argv[0] for call in self.runner.calls])
        self.assertNotIn(RELAY, [call.argv[0] for call in self.runner.calls])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
