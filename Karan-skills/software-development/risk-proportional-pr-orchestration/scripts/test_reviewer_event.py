#!/usr/bin/env python3
"""Offline safety regression; does not resolve credentials or call GitHub."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('publisher', Path(__file__).with_name('publish_reviewer_artifact.py'))
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)

class ReviewEventTests(unittest.TestCase):
    def test_explicit_states(self):
        expected = {'pass': 'APPROVE', 'block': 'REQUEST_CHANGES', 'fail': 'REQUEST_CHANGES',
                    'needs-karan': 'COMMENT', 'needs-human': 'COMMENT'}
        for status, event in expected.items():
            for delimiter in (': ', '='):
                with self.subTest(status=status, delimiter=delimiter):
                    self.assertEqual(publisher.review_event('STATUS' + delimiter + status + '  \n'), event)

    def test_unknown_missing_duplicate_fail_closed(self):
        for body in ('', 'STATUS: pending', 'STATUS: not-pass', 'STATUS: pass\nSTATUS=block'):
            with self.subTest(body=body), self.assertRaises(RuntimeError):
                publisher.review_event(body)

    def test_human_hold_is_not_implicit_approval(self):
        body = 'REVIEWER: A\nSTATUS: needs-karan\nBLOCKERS: 0\n'
        legacy_status = 'needs-karan'
        legacy_event = 'REQUEST_CHANGES' if 'block' in legacy_status or 'fail' in legacy_status else 'APPROVE'
        self.assertEqual(legacy_event, 'APPROVE')
        self.assertEqual(publisher.review_event(body), 'COMMENT')

if __name__ == '__main__':
    unittest.main()
