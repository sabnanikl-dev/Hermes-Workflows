"""PAPI-90 item 6: committed changes stay inside the frozen packet's contract.

A clean attempt worktree and a valid readback say only that the builder
committed and pushed *something*. They say nothing about which files the commit
touched, and "fix the blocker, and also commit this unrelated file" leaves both
looking exactly right. So the committed old-head-to-new-head path set is
compared against the allowed-path contract the frozen repair packet carries.

The whole-repository allowance exists, and it has to be written down. Absence
and ambiguity both fail closed, because "the packet did not say" must never
come to mean "anything goes".
"""
from __future__ import annotations

import unittest

from pr_prover.errors import ConfigError
from pr_prover.paths import WHOLE_REPOSITORY, PathContract, changed_paths


class ContractParsingTests(unittest.TestCase):
    def parses(self, entries: object) -> PathContract:
        return PathContract.parse(entries, what="builder")

    def refuses(self, entries: object) -> ConfigError:
        with self.assertRaises(ConfigError) as caught:
            self.parses(entries)
        self.assertEqual(caught.exception.reason, "invalid-config")
        return caught.exception

    def test_an_absent_contract_fails_closed(self) -> None:
        """Former-red: there is no permissive default to fall into."""
        error = self.refuses(None)
        self.assertIn("declares no allowed_paths", error.message)
        self.assertIn(WHOLE_REPOSITORY, error.message)

    def test_an_empty_contract_fails_closed(self) -> None:
        self.refuses([])
        self.refuses({})
        self.refuses("src/")

    def test_exact_paths_and_directory_prefixes_parse(self) -> None:
        contract = self.parses(["README.md", "pr-prover/src/"])
        self.assertEqual(contract.entries, ("README.md", "pr-prover/src/"))
        self.assertFalse(contract.whole_repository)

    def test_the_whole_repository_allowance_must_be_explicit_and_alone(self) -> None:
        self.assertTrue(self.parses([WHOLE_REPOSITORY]).whole_repository)
        error = self.refuses([WHOLE_REPOSITORY, "src/"])
        self.assertIn("stands alone", error.message)

    def test_duplicate_entries_collapse(self) -> None:
        self.assertEqual(self.parses(["src/", "src/"]).entries, ("src/",))

    def test_a_wildcard_other_than_the_whole_repository_entry_is_refused(self) -> None:
        for entry in ("src/*", "*.py", "src/?.py", "src/[ab].py", "**/x"):
            with self.subTest(entry=entry):
                self.refuses([entry])

    def test_a_path_outside_the_repository_is_refused(self) -> None:
        for entry in ("/etc/passwd", "../outside", "src/../../etc", "~/secrets"):
            with self.subTest(entry=entry):
                self.refuses([entry])

    def test_a_path_that_is_not_plain_and_forward_slashed_is_refused(self) -> None:
        for entry in ("src\\\\win", "src//double", "src/\x00nul", "./src"):
            with self.subTest(entry=repr(entry)):
                self.refuses([entry])

    def test_an_entry_that_is_not_an_unpadded_string_is_refused(self) -> None:
        for entry in ("", " src/", "src/ ", 7, None):
            with self.subTest(entry=repr(entry)):
                self.refuses([entry])


class ContractMatchingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = PathContract.parse(
            ["pr-prover/src/", "README.md"], what="builder"
        )

    def test_an_exact_path_matches_only_itself(self) -> None:
        self.assertTrue(self.contract.allows("README.md"))
        self.assertFalse(self.contract.allows("README.md.bak"))
        self.assertFalse(self.contract.allows("docs/README.md"))

    def test_a_directory_prefix_matches_everything_under_it(self) -> None:
        self.assertTrue(self.contract.allows("pr-prover/src/loop.py"))
        self.assertTrue(self.contract.allows("pr-prover/src/deep/nested/file.py"))

    def test_a_directory_prefix_does_not_match_a_sibling_with_the_same_start(self) -> None:
        """The trailing slash is what stops 'src/' matching 'src-other/'."""
        self.assertFalse(self.contract.allows("pr-prover/srcx/loop.py"))
        self.assertFalse(self.contract.allows("pr-prover/src"))

    def test_the_whole_repository_allowance_matches_anything(self) -> None:
        contract = PathContract.parse([WHOLE_REPOSITORY], what="builder")
        for path in ("a", "a/b/c.py", "deeply/nested/thing"):
            self.assertTrue(contract.allows(path), path)

    def test_no_contract_ever_allows_a_path_that_escapes_the_repository(self) -> None:
        contract = PathContract.parse([WHOLE_REPOSITORY], what="builder")
        for path in ("/etc/passwd", "../outside", "a/../../b", ""):
            with self.subTest(path=path):
                self.assertFalse(contract.allows(path))

    def test_rejected_returns_every_path_outside_without_duplicates(self) -> None:
        outside = self.contract.rejected(
            ["README.md", "other.py", "pr-prover/src/x.py", "other.py", "docs/y.md"]
        )
        self.assertEqual(outside, ("other.py", "docs/y.md"))

    def test_rejected_is_empty_when_everything_is_in_contract(self) -> None:
        self.assertEqual(
            self.contract.rejected(["README.md", "pr-prover/src/a.py"]), ()
        )

    def test_the_contract_is_carried_into_the_frozen_packet(self) -> None:
        self.assertEqual(
            self.contract.as_dict(),
            {"allowed_paths": ["pr-prover/src/", "README.md"], "whole_repository": False},
        )
        self.assertIs(
            PathContract.parse([WHOLE_REPOSITORY], what="b").as_dict()["whole_repository"],
            True,
        )


class ChangedPathsTests(unittest.TestCase):
    def test_nul_separated_output_becomes_a_path_tuple(self) -> None:
        self.assertEqual(changed_paths("a.py\x00b/c.py\x00"), ("a.py", "b/c.py"))

    def test_an_empty_diff_is_no_paths(self) -> None:
        for raw in ("", "\x00", None):
            self.assertEqual(changed_paths(raw), ())  # type: ignore[arg-type]

    def test_a_path_containing_a_newline_survives_intact(self) -> None:
        """The -z form is why a filename with a newline in it cannot hide."""
        self.assertEqual(changed_paths("we\nird.py\x00"), ("we\nird.py",))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
