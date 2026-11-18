"""
Check gwdata's ledger vocabulary is registered with asimov and covers the
keys used by the bundled blueprints.

asimov's vocabulary system was added in 0.8, so these tests are skipped on
older asimov.
"""

import glob
import os
import unittest

import yaml

try:
    from asimov.vocabulary import get_vocabulary
except ImportError:  # asimov < 0.8
    get_vocabulary = None

HERE = os.path.dirname(__file__)
BLUEPRINTS = sorted(
    glob.glob(os.path.join(HERE, "test_blueprints", "*.yaml"))
    + glob.glob(os.path.join(HERE, "..", "blueprints", "*.yaml"))
)


@unittest.skipIf(get_vocabulary is None, "asimov < 0.8 has no ledger vocabulary")
class TestVocabulary(unittest.TestCase):
    def setUp(self):
        self.vocabulary = get_vocabulary()

    def test_plugin_is_registered(self):
        self.assertIn("gwdata", self.vocabulary.plugins)

    def test_gwdata_terms_are_known(self):
        for path in [
            "source.type",
            "source.location",
            "source.analysis",
            "source.frames",
            "locations.calibration directory",
            "file length",
            "calibration version",
            "virgo prefix",
        ]:
            with self.subTest(path=path):
                self.assertIsNotNone(self.vocabulary.lookup(path))

    def test_blueprints_have_no_unknown_keys(self):
        self.assertTrue(BLUEPRINTS)
        for blueprint in BLUEPRINTS:
            with open(blueprint) as f:
                documents = [d for d in yaml.safe_load_all(f) if d]
            for document in documents:
                findings = [
                    finding
                    for finding in self.vocabulary.check(document)
                    if finding.kind in {"unknown", "duplicate", "type"}
                ]
                with self.subTest(blueprint=os.path.basename(blueprint)):
                    self.assertEqual(findings, [], [str(f) for f in findings])
