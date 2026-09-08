"""
Tests for the asimov pipeline plugin (``datafind.asimov.Pipeline``).

Job submission is tested by mocking ``Pipeline.scheduler`` (asimov's own
scheduler-agnostic abstraction, ``asimov.scheduler.Scheduler``) rather than
any HTCondor internals - ``datafind.asimov`` no longer imports ``htcondor``
directly at all. A real HTCondor daemon is only exercised by the end-to-end
workflow.
"""
import configparser
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import datafind.asimov as datafind_asimov
from asimov.scheduler import JobDescription
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


class PipelineTestCase(unittest.TestCase):
    asimov_module = datafind_asimov
    Pipeline = datafind_asimov.Pipeline

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

    def make_pipeline_with_scheduler(self, cluster_id=4242, **kwargs):
        """Like ``make_pipeline``, but with a mocked scheduler pre-installed
        (bypassing the real, lazily-constructed one from the ``Pipeline``
        base class) so ``build_dag`` never touches a real HTCondor/Slurm
        backend."""
        pipeline, production = self.make_pipeline(**kwargs)
        scheduler = MagicMock()
        scheduler.submit.return_value = cluster_id
        pipeline._scheduler = scheduler
        return pipeline, production, scheduler


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
            pipeline, production, scheduler = self.make_pipeline_with_scheduler(
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

            scheduler.submit.assert_called_once()
            (submitted_job,), _ = scheduler.submit.call_args
            self.assertIsInstance(submitted_job, JobDescription)
            self.assertEqual(submitted_job.executable, os.path.join("/opt/env", "bin", "gwdata"))

            self.assertEqual(production.job_id, 4242)
            self.assertEqual(pipeline.clusterid, 4242)

    def test_build_dag_without_accounting_group_still_submits(self):
        with temporary_test_directory() as tmpdir:
            pipeline, production, scheduler = self.make_pipeline_with_scheduler(
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

    def test_build_dag_requests_scitoken_for_frame_source(self):
        with temporary_test_directory() as tmpdir:
            pipeline, _, scheduler = self.make_pipeline_with_scheduler(
                rundir=tmpdir,
                ini_contents="data: [calibration]\n",
                meta={"source": {"type": "frame"}},
            )
            with patch.object(
                self.asimov_module.config, "get",
                side_effect=_config_get({("pipelines", "environment"): "/opt/env"}),
            ):
                pipeline.build_dag()

            (submitted_job,), _ = scheduler.submit.call_args
            self.assertEqual(submitted_job.to_htcondor()["use_oauth_services"], "scitokens")

    def test_build_dag_requests_scitoken_for_osdf_frames(self):
        with temporary_test_directory() as tmpdir:
            pipeline, _, scheduler = self.make_pipeline_with_scheduler(
                rundir=tmpdir,
                ini_contents="data: [frames]\n",
                meta={"source": {"frames": "osdf"}},
            )
            with patch.object(
                self.asimov_module.config, "get",
                side_effect=_config_get({("pipelines", "environment"): "/opt/env"}),
            ):
                pipeline.build_dag()

            (submitted_job,), _ = scheduler.submit.call_args
            self.assertEqual(submitted_job.to_htcondor()["use_oauth_services"], "scitokens")

    def test_build_dag_no_scitoken_for_gwosc_frames(self):
        with temporary_test_directory() as tmpdir:
            pipeline, _, scheduler = self.make_pipeline_with_scheduler(
                rundir=tmpdir, ini_contents="data: [frames]\n", meta={}
            )
            with patch.object(
                self.asimov_module.config, "get",
                side_effect=_config_get({("pipelines", "environment"): "/opt/env"}),
            ):
                pipeline.build_dag()

            (submitted_job,), _ = scheduler.submit.call_args
            self.assertNotIn("use_oauth_services", submitted_job.to_htcondor())

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

    def test_multiple_frame_files_for_the_same_ifo_are_all_collected(self):
        """
        Regression test: collect_assets used to overwrite frames[ifo] on
        each match instead of accumulating a list, so only the
        alphabetically-last frame file for a detector survived when more
        than one existed in the rundir (e.g. two segments for the same
        interferometer).
        """
        with temporary_test_directory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "frames"))
            open(os.path.join(tmpdir, "frames", "H-H1_GWOSC_16KHZ_R1-1126259447-32.gwf"), "w").close()
            open(os.path.join(tmpdir, "frames", "H-H1_GWOSC_16KHZ_R1-1126259479-32.gwf"), "w").close()

            pipeline, _ = self.make_pipeline(
                rundir=tmpdir,
                meta={"download": ["frames"]},
                event_meta={"data": {}},
            )
            assets = pipeline.collect_assets()

            self.assertIsInstance(assets["frames"]["H1"], list)
            self.assertEqual(len(assets["frames"]["H1"]), 2)

    def test_stale_cache_dir_ignored_when_frames_not_requested(self):
        """
        Regression test: a cache/ directory left over from an earlier job in
        the same rundir used to be picked up even when this job didn't
        request frames at all.
        """
        with temporary_test_directory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, "cache"))
            open(os.path.join(tmpdir, "cache", "H1.cache"), "w").close()

            pipeline, _ = self.make_pipeline(
                rundir=tmpdir,
                meta={"download": ["calibration"]},
                event_meta={"data": {}},
            )
            assets = pipeline.collect_assets()

            self.assertNotIn("caches", assets)

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
            pipeline, production = self.make_pipeline(
                rundir=tmpdir,
                meta={"download": ["frames"]},
                event_meta={"data": {}},
            )
            production.status = "finished"

            html = pipeline.html()
            self.assertIn("asimov-pipeline", html)
            self.assertIn("H1", html)


if __name__ == "__main__":
    unittest.main()
