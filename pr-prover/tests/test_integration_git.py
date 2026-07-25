"""Exercise the real git argv shapes against a throwaway repository.

The rest of the suite runs on doubles, which cannot catch a wrong refspec or a
bad ``rev-parse`` argument. This module builds a bare "remote" plus a clone in a
temp directory and drives :class:`SourceRepo` and :class:`WorktreeProvider`
through real ``git``, then proves the clone's working tree and checked-out
branch came through untouched.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import _support  # noqa: F401 - inserts the package on sys.path
from pr_prover.commands import SubprocessRunner
from pr_prover.errors import StaleHead, WorktreeError
from pr_prover.loop import _hidden_index_entries, _redirecting_git_config
from pr_prover.worktrees import SourceRepo, WorktreeProvider

GIT = shutil.which("git")
BRANCH = "feat/example"


def git(*args: str, cwd: Path, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        [GIT, *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
        stdin=subprocess.DEVNULL,
        env=env,
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

    def test_a_pristine_worktree_passes_every_exact_tree_check(self) -> None:
        """PAPI-90 item 5, against real git: the checks do not stop an honest run.

        A check that fires on an ordinary clone is a way of having no check at
        all. ``core.filemode`` and ``core.ignorecase`` are written by ``git
        clone`` itself, so they cannot be read as tampering — this asserts that
        against the config a real clone actually produces, plus the plumbing the
        loop uses to prove a tree exact.
        """
        worktree = self.provider.create("pristine", self.head)

        self.assertEqual(git("rev-parse", "HEAD", cwd=worktree), self.head)
        self.assertEqual(
            git("rev-parse", "--verify", "HEAD^{tree}", cwd=worktree),
            git("rev-parse", "--verify", f"{self.head}^{{tree}}", cwd=worktree),
        )
        self.assertEqual(_hidden_index_entries(git("ls-files", "-v", cwd=worktree)), ())
        self.assertEqual(git("status", "--porcelain", "--untracked-files=all", cwd=worktree), "")
        listing = git("config", "--local", "--list", cwd=worktree)
        self.assertIn("core.filemode", listing)
        self.assertEqual(_redirecting_git_config(listing), ())

    def test_the_exact_tree_diff_sees_a_change_a_hidden_index_would_conceal(self) -> None:
        """The scratch index has no stat cache, so content is what is compared."""
        worktree = self.provider.create("probed", self.head)
        index = self.tmp / "scratch.index"
        env = {**os.environ, "GIT_INDEX_FILE": str(index)}

        def diff() -> str:
            index.unlink(missing_ok=True)
            git("read-tree", self.head, cwd=worktree, env=env)
            # Nonzero here just means "a path needs updating", which is the
            # answer this check is after rather than a failure to get one.
            subprocess.run(
                [GIT, "update-index", "-q", "--refresh"],
                cwd=str(worktree), capture_output=True, text=True, env=env, check=False,
            )
            return git(
                "diff-index", "--name-only", "-z", self.head, "--", cwd=worktree, env=env
            )

        self.assertEqual(diff(), "")

        # Hide the file from the real index the way a reviewer would, then change
        # it. `git status` is quiet about it; the scratch-index diff is not.
        git("update-index", "--skip-worktree", "feature.txt", cwd=worktree)
        (worktree / "feature.txt").write_text("tampered\n", encoding="utf-8")
        self.assertEqual(git("status", "--porcelain", cwd=worktree), "")
        self.assertIn("feature.txt", diff())
        self.assertIn("feature.txt", _hidden_index_entries(git("ls-files", "-v", cwd=worktree)))

    def test_the_clone_cannot_be_checked_out_through_the_source_repo(self) -> None:
        with self.assertRaises(WorktreeError):
            self.source._git(["checkout", BRANCH], what="test")
        self.assertEqual(git("rev-parse", "--abbrev-ref", "HEAD", cwd=self.clone), "main")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
