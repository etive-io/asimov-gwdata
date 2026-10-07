"""
Tests for the ``asimov gw`` command group (``datafind.cli``).

These point ``AsimovDataRepository`` at a small local fixture directory via
``ASIMOV_DATA_PATH`` instead of the real ``asimov/data`` clone, so the tests
run offline and don't depend on what's checked out on the machine running
them.
"""
import os
import shutil
import tempfile
import textwrap
import unittest
import unittest.mock

import yaml
from click.testing import CliRunner

from datafind.cli import gw
from datafind.repository import get_repository


def _write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(textwrap.dedent(content))


def _build_fixture_repo(root):
    """Lay out a minimal asimov-data-shaped tree under ``root``."""
    _write(
        os.path.join(root, "events", "gwtc-2-1", "GW150914_095045.yaml"),
        """
        kind: event
        name: GW150914_095045
        event time: 1126259462.4
        interferometers: [H1, L1]
        """,
    )
    _write(
        os.path.join(root, "analyses", "production-default.yaml"),
        """
        kind: analysis
        name: production-default
        pipeline: bilby
        """,
    )
    _write(
        os.path.join(root, "defaults", "production-pe.yaml"),
        yaml.safe_dump({"kind": "configuration", "name": "production-pe"}),
    )
    _write(
        os.path.join(root, "defaults", "production-pe-priors.yaml"),
        yaml.safe_dump({"kind": "configuration", "name": "production-pe-priors"}),
    )


class GwCliFixtureTests(unittest.TestCase):
    """Tests that exercise the CLI against a hermetic fixture repository."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, True)
        _build_fixture_repo(self.tmpdir)

        # AsimovDataRepository is a module-level singleton, and it reads
        # ASIMOV_DATA_PATH fresh on every call, so pointing the env var at
        # the fixture is enough to isolate each test - no need to touch the
        # singleton itself.
        env_patch = unittest.mock.patch.dict(os.environ, {"ASIMOV_DATA_PATH": self.tmpdir})
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def test_events_list_shows_fixture_event(self):
        result = CliRunner().invoke(gw, ["events", "list"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("GW150914_095045", result.output)

    def test_analyses_list_shows_fixture_analysis(self):
        result = CliRunner().invoke(gw, ["analyses", "list"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("production-default", result.output)

    def test_setup_dry_run_plans_expected_steps(self):
        result = CliRunner().invoke(
            gw,
            [
                "setup",
                "--name",
                "test-project",
                "--events",
                "GW150914_095045",
                "--dry-run",
            ],
        )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("GW150914_095045", result.output)
        self.assertIn("DRY RUN", result.output)
        self.assertIn("production-default", result.output)

    def test_repository_get_event_roundtrip(self):
        repo = get_repository()
        event = repo.get_event("GW150914_095045")
        self.assertIsNotNone(event)
        self.assertEqual(event["catalog"], "gwtc-2-1")


class GwCliHelpTests(unittest.TestCase):
    """Smoke tests that every command group wires up and shows help."""

    def test_help_text(self):
        for args in (
            ["--help"],
            ["events", "--help"],
            ["analyses", "--help"],
            ["setup", "--help"],
            ["quickstart", "--help"],
        ):
            result = CliRunner().invoke(gw, args)
            self.assertEqual(result.exit_code, 0, f"{args}: {result.output}")


if __name__ == "__main__":
    unittest.main()
