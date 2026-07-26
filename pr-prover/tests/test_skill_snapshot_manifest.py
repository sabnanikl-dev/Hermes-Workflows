"""``Karan-skills/.sync-manifest.json`` must describe the bytes actually committed.

The manifest records, for every mirrored bundle, a file count and a tree digest.
Those fields are computed by ``scripts/sync_karan_skills.py`` from the copied
destination, so they are a content record of this repository's snapshot — not a
provenance note about the machine the bytes came from. Editing a skill and
leaving its recorded digest alone therefore ships a known-false integrity claim,
which is exactly what this module refuses to let happen again.

The digest function is imported from the sync script rather than reimplemented,
so the test cannot drift from the semantics it is meant to hold. Nothing here
reads, writes, or installs the live Hermes skill directory; installation is a
separate slice's concern.
"""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SNAPSHOT = REPO / "Karan-skills"
MANIFEST = SNAPSHOT / ".sync-manifest.json"
SYNC_SCRIPT = REPO / "scripts" / "sync_karan_skills.py"


def load_sync_module():
    """Borrow the repository's own tree-digest and exclusion rules."""
    spec = importlib.util.spec_from_file_location("_karan_skills_sync_under_test", SYNC_SCRIPT)
    assert spec and spec.loader, f"could not load {SYNC_SCRIPT}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SkillSnapshotManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sync = load_sync_module()
        cls.sha256_tree = staticmethod(sync.sha256_tree)
        cls.ignored = staticmethod(sync.ignored)
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_no_bundle_carries_a_file_the_sync_would_never_copy(self) -> None:
        """A stray local artifact reads as a digest mismatch; name it directly instead.

        ``sha256_tree`` hashes whatever is under the bundle root, while the sync
        filters caches, VCS data, and secret-bearing files before copying. A
        ``__pycache__`` or ``.DS_Store`` left in a snapshot therefore breaks the
        recomputation for a reason that has nothing to do with the manifest.
        """
        stray = []
        for entry in self.manifest["skills"]:
            root = SNAPSHOT / entry["path"]
            for path in root.rglob("*"):
                if self.ignored(str(path.parent), [path.name]):
                    stray.append(str(path.relative_to(SNAPSHOT)))
        self.assertEqual(stray, [], "remove these local artifacts from the snapshot")

    def test_the_manifest_shape_is_internally_consistent(self) -> None:
        self.assertEqual(self.manifest["schema_version"], 2)
        skills = self.manifest["skills"]
        self.assertEqual(self.manifest["skill_count"], len(skills))
        self.assertGreater(len(skills), 1, "the manifest lost its recorded bundles")
        self.assertEqual(len({entry["name"] for entry in skills}), len(skills))
        self.assertEqual(len({entry["path"] for entry in skills}), len(skills))

    def test_every_recorded_bundle_matches_its_committed_bytes(self) -> None:
        """One deterministic recomputation per recorded bundle, no sampling."""
        mismatches = []
        for entry in self.manifest["skills"]:
            root = SNAPSHOT / entry["path"]
            with self.subTest(skill=entry["name"]):
                self.assertTrue(root.is_dir(), f"{entry['path']} is recorded but absent")
                self.assertTrue((root / "SKILL.md").is_file(), f"{entry['path']} has no SKILL.md")
            digest, file_count = self.sha256_tree(root)
            if (digest, file_count) != (entry["sha256"], entry["files"]):
                mismatches.append(
                    f"{entry['name']}: recorded {entry['files']} files/{entry['sha256'][:12]}…, "
                    f"computed {file_count} files/{digest[:12]}…"
                )
        self.assertEqual(mismatches, [], "manifest entries do not describe the committed bundles")

    def test_the_router_bundle_is_covered(self) -> None:
        """The bundle this repository edits most must be one of the recorded ones."""
        recorded = {entry["path"]: entry for entry in self.manifest["skills"]}
        entry = recorded.get("software-development/autonomous-pr-prover")
        self.assertIsNotNone(entry, "the router bundle is not recorded in the manifest")
        digest, file_count = self.sha256_tree(SNAPSHOT / entry["path"])
        self.assertEqual((entry["files"], entry["sha256"]), (file_count, digest))

    def test_the_digest_notices_a_changed_or_added_byte(self) -> None:
        """Non-vacuity: the check above only means something if the digest moves."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "SKILL.md").write_text("one\n", encoding="utf-8")
            first, count = self.sha256_tree(root)
            self.assertEqual(count, 1)

            (root / "SKILL.md").write_text("two\n", encoding="utf-8")
            changed, count = self.sha256_tree(root)
            self.assertEqual(count, 1)
            self.assertNotEqual(first, changed, "an edited byte left the digest unchanged")

            (root / "references").mkdir()
            (root / "references" / "extra.md").write_text("two\n", encoding="utf-8")
            grown, count = self.sha256_tree(root)
            self.assertEqual(count, 2)
            self.assertNotEqual(changed, grown, "an added file left the digest unchanged")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
