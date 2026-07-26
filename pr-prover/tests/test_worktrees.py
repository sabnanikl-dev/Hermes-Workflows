"""Worktree isolation guards and the narrow source-repository surface."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from _support import HEAD_A, HEAD_B, FakeRemote, FakeRunner, make_source_repo
from pr_prover.errors import StaleHead, WorktreeError
from pr_prover.worktrees import SourceRepo, WorktreeProvider


class SourceRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-worktree-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.clone = make_source_repo(self.tmp)
        self.remote = FakeRemote()
        self.runner = FakeRunner(self.remote)
        self.source = SourceRepo(runner=self.runner, path=self.clone)

    def test_a_non_checkout_path_is_refused(self) -> None:
        plain = self.tmp / "not-a-clone"
        plain.mkdir()
        with self.assertRaises(WorktreeError):
            SourceRepo(runner=self.runner, path=plain)

    def test_a_missing_path_is_refused(self) -> None:
        with self.assertRaises(WorktreeError):
            SourceRepo(runner=self.runner, path=self.tmp / "absent")

    def test_only_fetch_rev_parse_and_worktree_are_reachable(self) -> None:
        for subcommand in ("checkout", "commit", "reset", "clean", "push", "merge"):
            with self.subTest(subcommand=subcommand):
                with self.assertRaises(WorktreeError) as caught:
                    self.source._git([subcommand], what="test")
                self.assertIn("not permitted", caught.exception.message)

    def test_fetch_updates_only_this_branch_tracking_ref(self) -> None:
        self.source.fetch_branch("feat/example")
        argv = self.runner.calls[-1].argv
        self.assertEqual(argv[3:], ("fetch", "--no-tags", "origin", "+refs/heads/feat/example:refs/remotes/origin/feat/example"))

    def test_verified_head_matches_the_remote(self) -> None:
        self.assertEqual(self.source.verified_head("feat/example", HEAD_A), HEAD_A)

    def test_a_drifting_remote_head_is_stale(self) -> None:
        self.remote.head = HEAD_B
        with self.assertRaises(StaleHead) as caught:
            self.source.verified_head("feat/example", HEAD_A)
        self.assertEqual(caught.exception.evidence["remote_head"], HEAD_B)

    def test_a_short_expected_head_is_refused(self) -> None:
        with self.assertRaises(StaleHead):
            self.source.verified_head("feat/example", HEAD_A[:7])

    def test_a_failing_fetch_fails_closed(self) -> None:
        self.runner.fetch_failures = 1
        with self.assertRaises(WorktreeError):
            self.source.verified_head("feat/example", HEAD_A)


class WorktreeProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-provider-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.clone = make_source_repo(self.tmp)
        self.runner = FakeRunner(FakeRemote())
        self.source = SourceRepo(runner=self.runner, path=self.clone)
        self.provider = WorktreeProvider(self.source, self.tmp / "worktrees")

    def test_a_root_inside_the_source_clone_is_refused(self) -> None:
        with self.assertRaises(WorktreeError) as caught:
            WorktreeProvider(self.source, self.clone / "scratch")
        self.assertIn("overlaps", caught.exception.message)

    def test_a_root_containing_the_source_clone_is_refused(self) -> None:
        with self.assertRaises(WorktreeError):
            WorktreeProvider(self.source, self.tmp)

    def test_create_makes_a_detached_worktree_at_the_exact_head(self) -> None:
        path = self.provider.create("inspect", HEAD_A)
        self.assertTrue(path.is_dir())
        argv = self.runner.calls[-1].argv
        self.assertEqual(argv[3:], ("worktree", "add", "--detach", str(path), HEAD_A))

    def test_an_existing_path_is_never_reused(self) -> None:
        self.provider.create("inspect", HEAD_A)
        with self.assertRaises(WorktreeError) as caught:
            self.provider.create("inspect", HEAD_A)
        self.assertIn("fresh worktree", caught.exception.message)

    def test_a_non_exact_head_is_refused(self) -> None:
        with self.assertRaises(StaleHead):
            self.provider.create("inspect", "HEAD")

    def test_a_traversing_label_is_refused(self) -> None:
        for label in ("../escape", "nested/path", "with space"):
            with self.subTest(label=label):
                with self.assertRaises(WorktreeError):
                    self.provider.create(label, HEAD_A)

    def test_removing_a_foreign_worktree_is_refused(self) -> None:
        foreign = self.tmp / "someone-elses-worktree"
        foreign.mkdir()
        with self.assertRaises(WorktreeError) as caught:
            self.provider.remove(foreign)
        self.assertIn("did not create", caught.exception.message)
        self.assertTrue(foreign.is_dir())

    def test_remove_drops_only_the_run_owned_worktree(self) -> None:
        path = self.provider.create("inspect", HEAD_A)
        self.provider.remove(path)
        self.assertFalse(path.exists())
        self.assertEqual(self.provider.created, ())


class WorktreeRootFailureTests(unittest.TestCase):
    """REVIEWER-B-3 / IA-5: a bad configured root is a result, not a traceback.

    The defect these pin down: ``create()`` called ``Path.mkdir()`` directly,
    and the loop's ``run()`` translates prover errors rather than raw
    ``OSError`` subclasses. A worktree root configured under a regular file —
    an ordinary path mistake — therefore escaped as a ``NotADirectoryError``
    traceback instead of the sanitized ``needs-karan`` report, skipping the
    stable ``worktree-error`` reason, the retained evidence, and the journalled
    outcome the public contract promises.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-root-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()
        self.clone = make_source_repo(self.tmp)
        self.runner = FakeRunner(FakeRemote())
        self.source = SourceRepo(runner=self.runner, path=self.clone)

    def provider_under_a_regular_file(self) -> WorktreeProvider:
        blocker = self.tmp / "not-a-directory"
        blocker.write_text("this is a file\n", encoding="utf-8")
        return WorktreeProvider(self.source, blocker / "worktrees")

    def test_a_root_beneath_a_regular_file_is_a_prover_error(self) -> None:
        """The frozen probe ``WORKTREE_ROOT raised=builtins.NotADirectoryError``."""
        provider = self.provider_under_a_regular_file()

        with self.assertRaises(WorktreeError) as caught:
            provider.create("inspect", HEAD_A)

        self.assertEqual(caught.exception.reason, "worktree-error")
        self.assertEqual(caught.exception.evidence["stage"], "worktree-root")
        self.assertEqual(caught.exception.evidence["error"], "NotADirectoryError")
        self.assertEqual(caught.exception.evidence["label"], "inspect")

    def test_nothing_is_asked_of_git_once_the_root_failed(self) -> None:
        provider = self.provider_under_a_regular_file()

        with self.assertRaises(WorktreeError):
            provider.create("inspect", HEAD_A)

        self.assertEqual(
            [call.argv[3] for call in self.runner.calls if call.argv[0] == "git"], []
        )
        self.assertEqual(provider.created, ())

    def test_an_unwritable_root_parent_is_a_prover_error(self) -> None:
        parent = self.tmp / "locked"
        parent.mkdir()
        parent.chmod(0o500)
        self.addCleanup(parent.chmod, 0o700)
        provider = WorktreeProvider(self.source, parent / "worktrees")

        with self.assertRaises(WorktreeError) as caught:
            provider.create("inspect", HEAD_A)

        self.assertEqual(caught.exception.reason, "worktree-error")
        self.assertEqual(caught.exception.evidence["stage"], "worktree-root")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
