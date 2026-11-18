"""
Tests for the ``asimov gw`` command group (``datafind.cli``).

These point ``AsimovDataRepository`` at a small local fixture directory via
``ASIMOV_DATA_PATH`` instead of the real ``asimov/data`` clone, so the tests
run offline and don't depend on what's checked out on the machine running
them.
"""
import os
import shutil
import subprocess
import sys
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


def _ledger_productions(project_dir):
    """
    Read ``{event: [(analysis, pipeline), ...]}`` from a project's ledger.

    Done in a subprocess because asimov reads its project configuration from
    the current directory when it is first imported.
    """
    script = (
        "import json\n"
        "from asimov import current_ledger as ledger\n"
        "print(json.dumps({e.name: [[p.name, str(p.pipeline)] for p in e.productions]"
        " for e in ledger.get_event()}))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=project_dir, capture_output=True, text=True, check=True,
    )
    import json
    return {k: [tuple(p) for p in v] for k, v in json.loads(result.stdout.splitlines()[-1]).items()}


@unittest.skipIf(shutil.which("asimov") is None, "the asimov command is not on PATH")
class GwCliRealProjectTests(unittest.TestCase):
    """
    Run ``setup`` and ``events add`` for real (not ``--dry-run``), so the
    ``asimov`` commands they generate are actually executed against a new
    project.
    """

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, True)
        self.data = os.path.join(self.tmpdir, "asimov-data")
        _build_fixture_repo(self.data)
        _write(
            os.path.join(self.data, "events", "gwtc-2-1", "GW151226_033853.yaml"),
            """
            kind: event
            name: GW151226_033853
            event time: 1135136350.6
            interferometers: [H1, L1]
            """,
        )
        _write(
            os.path.join(self.data, "analyses", "get-data.yaml"),
            """
            kind: analysis
            name: get-data
            pipeline: gwdata
            download: [calibration]
            source:
              type: public
            """,
        )
        self.work = os.path.join(self.tmpdir, "work")
        os.makedirs(self.work)

        env_patch = unittest.mock.patch.dict(os.environ, {"ASIMOV_DATA_PATH": self.data})
        env_patch.start()
        self.addCleanup(env_patch.stop)

        cwd = os.getcwd()
        self.addCleanup(os.chdir, cwd)

    def _setup_project(self):
        result = CliRunner().invoke(
            gw,
            [
                "setup",
                "--name", "real-project",
                "--events", "GW150914_095045",
                "--analyses", "get-data",
                "--directory", self.work,
            ],
        )
        self.assertEqual(result.exit_code, 0, result.output)
        return os.path.join(self.work, "real-project")

    def test_setup_creates_project_with_event_and_analysis(self):
        project = self._setup_project()
        self.assertTrue(os.path.isfile(os.path.join(project, ".asimov", "asimov.conf")))
        # asimov init must not have scattered the project into --directory itself.
        self.assertFalse(os.path.exists(os.path.join(self.work, ".asimov")))
        self.assertEqual(
            _ledger_productions(project),
            {"GW150914_095045": [("get-data", "gwdata")]},
        )

    def test_events_add_to_existing_project(self):
        project = self._setup_project()
        os.chdir(project)
        result = CliRunner().invoke(
            gw, ["events", "add", "GW151226_033853", "--analyses", "get-data"]
        )
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            _ledger_productions(project),
            {
                "GW150914_095045": [("get-data", "gwdata")],
                "GW151226_033853": [("get-data", "gwdata")],
            },
        )


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
