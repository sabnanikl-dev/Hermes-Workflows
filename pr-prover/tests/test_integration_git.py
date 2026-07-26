"""Exercise the real git argv shapes against a throwaway repository.

The rest of the suite runs on doubles, which cannot catch a wrong refspec or a
bad ``rev-parse`` argument. This module builds a bare "remote" plus a clone in a
temp directory and drives :class:`SourceRepo` and :class:`WorktreeProvider`
through real ``git``, then proves the clone's working tree and checked-out
branch came through untouched.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import _support  # noqa: F401 - inserts the package on sys.path
from pr_prover.commands import SubprocessRunner
from pr_prover.errors import StaleHead, WorktreeError
from pr_prover.worktrees import SourceRepo, WorktreeProvider

GIT = shutil.which("git")
BRANCH = "feat/example"


def git(*args: str, cwd: Path) -> str:
    completed = subprocess.run(
        [GIT, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
        stdin=subprocess.DEVNULL,
    )
    return completed.stdout.strip()


@unittest.skipIf(GIT is None, "git is not available")
class RealGitTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="pr-prover-git-")
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name).resolve()

        self.origin = self.tmp / "origin.git"
        git("init", "--bare", "--initial-branch=main", str(self.origin), cwd=self.tmp)

        seed = self.tmp / "seed"
        git("clone", str(self.origin), str(seed), cwd=self.tmp)
        git("config", "user.email", "test@example.invalid", cwd=seed)
        git("config", "user.name", "pr-prover tests", cwd=seed)
        (seed / "README.md").write_text("seed\n", encoding="utf-8")
        git("add", "README.md", cwd=seed)
        git("commit", "-m", "seed", cwd=seed)
        git("push", "origin", "main", cwd=seed)
        git("checkout", "-b", BRANCH, cwd=seed)
        (seed / "feature.txt").write_text("one\n", encoding="utf-8")
        git("add", "feature.txt", cwd=seed)
        git("commit", "-m", "feature", cwd=seed)
        git("push", "-u", "origin", BRANCH, cwd=seed)
        self.head = git("rev-parse", "HEAD", cwd=seed)
        self.seed = seed

        self.clone = self.tmp / "clone"
        git("clone", str(self.origin), str(self.clone), cwd=self.tmp)
        self.source = SourceRepo(runner=SubprocessRunner(default_timeout=120.0), path=self.clone)
        self.provider = WorktreeProvider(self.source, self.tmp / "worktrees")

    def clone_state(self) -> tuple[str, str, str]:
        return (
            git("rev-parse", "HEAD", cwd=self.clone),
            git("rev-parse", "--abbrev-ref", "HEAD", cwd=self.clone),
            git("status", "--porcelain", cwd=self.clone),
        )

    def test_verified_head_resolves_the_real_remote_tracking_ref(self) -> None:
        self.assertEqual(self.source.verified_head(BRANCH, self.head), self.head)

    def test_a_head_that_is_not_the_remote_head_is_stale(self) -> None:
        other = git("rev-parse", "HEAD~1", cwd=self.seed)
        with self.assertRaises(StaleHead):
            self.source.verified_head(BRANCH, other)

    def test_a_new_upstream_commit_is_picked_up_by_the_fetch(self) -> None:
        (self.seed / "feature.txt").write_text("two\n", encoding="utf-8")
        git("commit", "-am", "second", cwd=self.seed)
        git("push", "origin", BRANCH, cwd=self.seed)
        moved = git("rev-parse", "HEAD", cwd=self.seed)

        self.assertEqual(self.source.verified_head(BRANCH, moved), moved)
        with self.assertRaises(StaleHead):
            self.source.verified_head(BRANCH, self.head)

    def test_a_worktree_is_created_detached_at_the_exact_head(self) -> None:
        worktree = self.provider.create("inspect", self.head)
        self.assertEqual(git("rev-parse", "HEAD", cwd=worktree), self.head)
        self.assertEqual(git("rev-parse", "--abbrev-ref", "HEAD", cwd=worktree), "HEAD")
        self.assertEqual((worktree / "feature.txt").read_text(encoding="utf-8"), "one\n")
        self.provider.remove(worktree)
        self.assertFalse(worktree.exists())

    def test_two_attempts_can_hold_the_same_head_at_once(self) -> None:
        first = self.provider.create("attempt1", self.head)
        second = self.provider.create("attempt2", self.head)
        self.assertNotEqual(first, second)
        self.assertEqual(git("rev-parse", "HEAD", cwd=second), self.head)

    def test_the_clone_is_untouched_by_a_full_worktree_lifecycle(self) -> None:
        before = self.clone_state()
        self.source.verified_head(BRANCH, self.head)
        worktree = self.provider.create("inspect", self.head)
        (worktree / "scratch.txt").write_text("builder scratch\n", encoding="utf-8")
        self.provider.remove(worktree)

        self.assertEqual(self.clone_state(), before)
        self.assertEqual(before[1], "main", "the clone must stay on its own branch")
        self.assertEqual(before[2], "", "the clone must stay clean")

    def test_the_clone_cannot_be_checked_out_through_the_source_repo(self) -> None:
        with self.assertRaises(WorktreeError):
            self.source._git(["checkout", BRANCH], what="test")
        self.assertEqual(git("rev-parse", "--abbrev-ref", "HEAD", cwd=self.clone), "main")

    def test_commits_added_lists_the_real_fix_commit(self) -> None:
        (self.seed / "feature.txt").write_text("two\n", encoding="utf-8")
        git("commit", "-am", "fix the blocker", cwd=self.seed)
        git("push", "origin", BRANCH, cwd=self.seed)
        fixed = git("rev-parse", "HEAD", cwd=self.seed)
        self.source.verified_head(BRANCH, fixed)

        self.assertEqual(self.source.commits_added(self.head, fixed), (fixed,))

    def test_a_head_that_does_not_contain_the_reviewed_commit_is_refused(self) -> None:
        """A replaced history, not an extended one: the reviewed commit is gone."""
        git("checkout", "-b", "feat/rebuilt", "HEAD~1", cwd=self.seed)
        (self.seed / "feature.txt").write_text("rebuilt\n", encoding="utf-8")
        git("add", "feature.txt", cwd=self.seed)
        git("commit", "-m", "rebuilt", cwd=self.seed)
        git("push", "origin", "feat/rebuilt", cwd=self.seed)
        rebuilt = git("rev-parse", "HEAD", cwd=self.seed)
        self.source.verified_head("feat/rebuilt", rebuilt)

        with self.assertRaises(StaleHead) as caught:
            self.source.commits_added(self.head, rebuilt)
        self.assertEqual(caught.exception.evidence["dropped"], [self.head])

    def test_a_worktree_this_run_did_not_create_is_left_alone(self) -> None:
        other = self.tmp / "someone-elses-worktree"
        git("worktree", "add", "--detach", str(other), self.head, cwd=self.clone)
        marker = other / "another-agent.txt"
        marker.write_text("in use\n", encoding="utf-8")

        with self.assertRaises(WorktreeError):
            self.provider.remove(other)

        mine = self.provider.create("inspect", self.head)
        self.provider.remove(mine)
        self.assertTrue(marker.exists(), "an unrelated worktree must survive this run")
        self.assertEqual(marker.read_text(encoding="utf-8"), "in use\n")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
