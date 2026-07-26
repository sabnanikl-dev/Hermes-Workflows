"""Argv discipline, template rendering, and the real subprocess boundary."""
from __future__ import annotations

import sys
import unittest

import _support  # noqa: F401 - inserts the package on sys.path
from pr_prover.commands import SubprocessRunner, render_argv, validate_argv
from pr_prover.errors import CommandContractError


class ArgvValidationTests(unittest.TestCase):
    def test_a_shell_string_is_refused(self) -> None:
        with self.assertRaises(CommandContractError) as caught:
            validate_argv("git status && rm -rf /")
        self.assertIn("argv array", caught.exception.message)

    def test_bytes_are_refused(self) -> None:
        with self.assertRaises(CommandContractError):
            validate_argv(b"git")

    def test_an_empty_array_is_refused(self) -> None:
        with self.assertRaises(CommandContractError):
            validate_argv([])

    def test_a_non_string_element_is_refused(self) -> None:
        with self.assertRaises(CommandContractError):
            validate_argv(["git", 7])

    def test_an_empty_element_is_refused(self) -> None:
        with self.assertRaises(CommandContractError):
            validate_argv(["git", ""])

    def test_a_nul_byte_is_refused(self) -> None:
        with self.assertRaises(CommandContractError):
            validate_argv(["git", "sta\x00tus"])

    def test_a_valid_array_becomes_a_tuple(self) -> None:
        self.assertEqual(validate_argv(["git", "status"]), ("git", "status"))


class RenderTests(unittest.TestCase):
    values = {"head": "a" * 40, "repo": "example/repo"}

    def test_placeholders_are_substituted(self) -> None:
        rendered = render_argv(["review", "--head", "{head}", "--repo", "{repo}"], self.values)
        self.assertEqual(rendered, ("review", "--head", "a" * 40, "--repo", "example/repo"))

    def test_an_unknown_placeholder_fails_closed(self) -> None:
        with self.assertRaises(CommandContractError) as caught:
            render_argv(["review", "{token}"], self.values)
        self.assertEqual(caught.exception.evidence["placeholder"], "token")

    def test_a_substituted_value_is_never_re_parsed(self) -> None:
        """Shell metacharacters in a value stay inside one argv element."""
        rendered = render_argv(["review", "{head}"], {"head": "; rm -rf / #"})
        self.assertEqual(rendered, ("review", "; rm -rf / #"))

    def test_format_spec_syntax_is_not_honoured(self) -> None:
        rendered = render_argv(["review", "{head!r:>90}"], self.values)
        self.assertEqual(rendered[1], "{head!r:>90}")

    def test_attribute_access_is_not_honoured(self) -> None:
        rendered = render_argv(["review", "{head.__class__}"], self.values)
        self.assertEqual(rendered[1], "{head.__class__}")


class SubprocessRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = SubprocessRunner(default_timeout=30.0)

    def test_stdout_and_exit_code_are_captured(self) -> None:
        result = self.runner.run([sys.executable, "-c", "print('hello')"])
        self.assertTrue(result.ok)
        self.assertEqual(result.stdout.strip(), "hello")

    def test_a_non_zero_exit_is_reported_not_raised(self) -> None:
        result = self.runner.run([sys.executable, "-c", "raise SystemExit(3)"])
        self.assertFalse(result.ok)
        self.assertEqual(result.returncode, 3)

    def test_a_shell_string_never_reaches_the_shell(self) -> None:
        with self.assertRaises(CommandContractError):
            self.runner.run("echo hello > /tmp/pr-prover-should-not-exist")

    def test_a_timeout_is_reported_as_a_failure(self) -> None:
        result = self.runner.run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.2)
        self.assertTrue(result.timed_out)
        self.assertFalse(result.ok)

    def test_a_missing_executable_fails_closed(self) -> None:
        with self.assertRaises(CommandContractError):
            self.runner.run(["pr-prover-no-such-executable-zzz"])

    def test_children_get_no_stdin(self) -> None:
        result = self.runner.run([sys.executable, "-c", "import sys; print(repr(sys.stdin.read()))"])
        self.assertEqual(result.stdout.strip(), "''")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
