"""
Tests for the asimov pipeline plugin (``datafind.asimov.Pipeline``).

``datafind/asimov.py`` imports the ``htcondor`` python bindings unconditionally
at module level, so a stub is installed in ``sys.modules`` before the module
is imported here. This keeps these tests independent of whether the real
HTCondor bindings (and a running HTCondor daemon) are available - that full,
real-daemon exercise belongs to the end-to-end workflow instead.
"""
import configparser
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from tests.test_fixtures import temporary_test_directory


def _config_get(values):
    """Build a ``config.get(section, option)`` side_effect from a dict, raising
    ``configparser.NoOptionError`` (as the real asimov config does) for
    anything not supplied, rather than crashing on a bare KeyError."""

    def _get(section, option):
        try:
            return values[(section, option)]
        except KeyError:
            raise configparser.NoOptionError(option, section)

    return _get


class _FakeSubmit(dict):
    """Stand-in for ``htcondor.Submit`` that behaves like a real description dict."""

    def __str__(self):
        return "\n".join(f"{k} = {v}" for k, v in self.items())

    def queue(self, txn):
        return 4242


def _install_htcondor_stub():
    stub = MagicMock(name="htcondor")
    stub.Submit = _FakeSubmit
    stub.classad.quote.side_effect = lambda value: f'"{value}"'

    schedd = MagicMock(name="schedd")
    txn = MagicMock()
    txn.__enter__.return_value = txn
    txn.__exit__.return_value = False
    schedd.transaction.return_value = txn

    stub.Collector.return_value.locate.return_value = "schedd@localhost"
    stub.Schedd.return_value = schedd
    return stub, schedd


class PipelineTestCase(unittest.TestCase):
    """Base class which imports ``datafind.asimov`` under a stubbed ``htcondor``."""

    @classmethod
    def setUpClass(cls):
        cls.htcondor_stub, cls.schedd_stub = _install_htcondor_stub()
        cls._modules_patch = patch.dict(sys.modules, {"htcondor": cls.htcondor_stub})
        cls._modules_patch.start()
        sys.modules.pop("datafind.asimov", None)
        import datafind.asimov as datafind_asimov

        cls.asimov_module = datafind_asimov
        cls.Pipeline = datafind_asimov.Pipeline

    @classmethod
    def tearDownClass(cls):
        cls._modules_patch.stop()
        sys.modules.pop("datafind.asimov", None)

    def make_production(self, meta=None, event_meta=None, rundir=None, ini_contents=None):
        ini_path = None
        if rundir is not None and ini_contents is not None:
            ini_path = os.path.join(rundir, "get-data.ini")
            with open(ini_path, "w") as f:
                f.write(ini_contents)

        event = SimpleNamespace(
            name="GW150914_095045",
            meta=event_meta if event_meta is not None else {},
            repository=SimpleNamespace(find_prods=lambda name, category: [ini_path]),
            update_data=MagicMock(),
        )
        production = SimpleNamespace(
            name="get-data",
            meta=meta if meta is not None else {},
            rundir=rundir or "",
            event=event,
            status=None,
            job_id=None,
        )
        return production

    def make_pipeline(self, **kwargs):
        production = self.make_production(**kwargs)
        return self.Pipeline(production), production


class TestSubstituteLocationsInConfig(PipelineTestCase):
    def test_substitutes_event_and_gid(self):
        with temporary_test_directory() as tmpdir:
            pipeline, production = self.make_pipeline(
                rundir=tmpdir,
                ini_contents="event: <event>\ngid: <gid>\nresult: <illustrative_result>\n",
                event_meta={"ligo": {"preferred event": "G123456", "illustrative result": "online"}},
            )
            pipeline._substitute_locations_in_config()

            ini_path = os.path.join(tmpdir, "get-data.ini")
            with open(ini_path) as f:
                rendered = f.read()

            self.assertIn("event: GW150914_095045", rendered)
            self.assertIn("gid: G123456", rendered)
            self.assertIn("result: online", rendered)

    def test_illustrative_result_defaults_to_online_when_missing(self):
        with temporary_test_directory() as tmpdir:
            pipeline, production = self.make_pipeline(
                rundir=tmpdir,
                ini_contents="result: <illustrative_result>\n",
                event_meta={"ligo": {}},
            )
            pipeline._substitute_locations_in_config()
            with open(os.path.join(tmpdir, "get-data.ini")) as f:
                self.assertIn("result: online", f.read())

    def test_illustrative_result_defaults_to_online_when_falsy(self):
        with temporary_test_directory() as tmpdir:
            pipeline, production = self.make_pipeline(
                rundir=tmpdir,
                ini_contents="result: <illustrative_result>\n",
                event_meta={"ligo": {"illustrative result": ""}},
            )
            pipeline._substitute_locations_in_config()
            with open(os.path.join(tmpdir, "get-data.ini")) as f:
                self.assertIn("result: online", f.read())


class TestBuildAndSubmitDag(PipelineTestCase):
    def test_build_dag_writes_submit_files_and_sets_job_id(self):
        with temporary_test_directory() as tmpdir:
            pipeline, production = self.make_pipeline(
                rundir=tmpdir,
                ini_contents="data: [frames]\n",
                meta={"scheduler": {"accounting group": "ligo.dev.o4.cbc.pe.bilby"}},
            )
            with patch.object(
                self.asimov_module.config, "get",
                side_effect=_config_get(
                    {
                        ("pipelines", "environment"): "/opt/env",
                        ("condor", "user"): "submituser",
                    }
                ),
            ):
                pipeline.build_dag()

            sub_path = os.path.join(tmpdir, "get-data.sub")
            sh_path = os.path.join(tmpdir, "get-data.sh")
            self.assertTrue(os.path.exists(sub_path))
            self.assertTrue(os.path.exists(sh_path))

            with open(sub_path) as f:
                sub_contents = f.read()
            self.assertIn("gwdata", sub_contents)
            self.assertIn("--settings", sub_contents)
            self.assertIn("batch_name = gwdata/get-data", sub_contents)
            self.assertIn("accounting_group = ligo.dev.o4.cbc.pe.bilby", sub_contents)

            self.assertEqual(production.job_id, 4242)
            self.assertEqual(pipeline.clusterid, 4242)

    def test_build_dag_without_accounting_group_still_submits(self):
        with temporary_test_directory() as tmpdir:
            pipeline, production = self.make_pipeline(
                rundir=tmpdir, ini_contents="data: [frames]\n", meta={}
            )
            with patch.object(
                self.asimov_module.config, "get",
                side_effect=_config_get({("pipelines", "environment"): "/opt/env"}),
            ):
                pipeline.build_dag()

            with open(os.path.join(tmpdir, "get-data.sub")) as f:
                sub_contents = f.read()
            self.assertNotIn("accounting_group", sub_contents)
            self.assertEqual(production.job_id, 4242)

    def test_submit_dag_sets_status_running(self):
        pipeline, production = self.make_pipeline()
        pipeline.clusterid = 99
        result = pipeline.submit_dag()

        self.assertEqual(production.status, "running")
        self.assertEqual(production.job_id, 99)
        self.assertEqual(result, 99)


class TestDetectCompletion(PipelineTestCase):
    def test_true_when_assets_present(self):
        with temporary_test_directory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "frames"))
            open(os.path.join(tmpdir, "frames", "H-H1_GWOSC-1-32.gwf"), "w").close()
            pipeline, _ = self.make_pipeline(
                rundir=tmpdir,
                meta={"download": ["frames"]},
                event_meta={"data": {}},
            )
            self.assertTrue(pipeline.detect_completion())

    def test_true_when_virgo_calibration_not_required_for_event(self):
        pipeline, _ = self.make_pipeline(
            rundir="/nonexistent-rundir",
            meta={"download": ["calibration"], "interferometers": ["V1"]},
            event_meta={"interferometers": ["H1", "L1"], "data": {}},
        )
        self.assertTrue(pipeline.detect_completion())

    def test_false_when_no_assets_and_virgo_not_relevant(self):
        pipeline, _ = self.make_pipeline(
            rundir="/nonexistent-rundir",
            meta={"download": ["frames"], "interferometers": ["H1"]},
            event_meta={"interferometers": ["H1"], "data": {}},
        )
        self.assertFalse(pipeline.detect_completion())


class TestCollectAssets(PipelineTestCase):
    def test_collects_frames_cache_psds_calibration_posterior(self):
        with temporary_test_directory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "frames"))
            open(os.path.join(tmpdir, "frames", "H-H1_GWOSC_16KHZ_R1-1126259447-32.gwf"), "w").close()

            os.makedirs(os.path.join(tmpdir, "cache"))
            open(os.path.join(tmpdir, "cache", "H1.cache"), "w").close()

            os.makedirs(os.path.join(tmpdir, "psds"))
            open(os.path.join(tmpdir, "psds", "H1.dat"), "w").close()

            os.makedirs(os.path.join(tmpdir, "calibration"))
            open(os.path.join(tmpdir, "calibration", "H1.dat"), "w").close()

            os.makedirs(os.path.join(tmpdir, "posterior"))
            open(os.path.join(tmpdir, "posterior", "metafile.h5"), "w").close()

            pipeline, production = self.make_pipeline(
                rundir=tmpdir,
                meta={"download": ["frames", "psds", "calibration", "posterior"]},
                event_meta={"data": {}},
            )
            assets = pipeline.collect_assets()

            self.assertIn("H1", assets["frames"])
            self.assertIn("H1", assets["caches"])
            self.assertIn("H1", assets["psds"])
            self.assertIn("H1", assets["calibration"])
            self.assertTrue(assets["samples"].endswith("metafile.h5"))

            self.assertIn("H1", production.event.meta["data"]["data files"])
            self.assertIn("H1", production.event.meta["data"]["cache files"])
            self.assertIn("H1", production.event.meta["data"]["calibration"])
            self.assertIn("H1", production.event.meta["psds"])

    def test_empty_rundir_returns_no_assets(self):
        with temporary_test_directory() as tmpdir:
            pipeline, _ = self.make_pipeline(rundir=tmpdir, event_meta={"data": {}})
            self.assertEqual(pipeline.collect_assets(), {})


class TestAfterCompletionAndHtml(PipelineTestCase):
    def test_after_completion_marks_uploaded_and_updates_event(self):
        pipeline, production = self.make_pipeline(event_meta={"data": {}})
        pipeline.after_completion()

        self.assertEqual(production.status, "uploaded")
        production.event.update_data.assert_called_once()

    def test_html_empty_when_not_finished(self):
        pipeline, production = self.make_pipeline(event_meta={"data": {}})
        production.status = "running"
        self.assertEqual(pipeline.html(), "")

    def test_html_renders_assets_when_finished(self):
        with temporary_test_directory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "cache"))
            open(os.path.join(tmpdir, "cache", "H1.cache"), "w").close()
            pipeline, production = self.make_pipeline(rundir=tmpdir, event_meta={"data": {}})
            production.status = "finished"

            html = pipeline.html()
            self.assertIn("asimov-pipeline", html)
            self.assertIn("H1", html)


if __name__ == "__main__":
    unittest.main()
