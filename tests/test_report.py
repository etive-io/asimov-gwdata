"""
Tests for ``datafind.report.Report``.

``otter.Otter`` (real HTML page building) and ``Frame.spectrogram`` (real
matplotlib/gwpy signal processing) are both mocked - these tests only check
Report's own dispatch logic, not the underlying rendering/plotting.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

from datafind.report import Report
from tests.test_fixtures import temporary_test_directory


class TestReportStandalone(unittest.TestCase):
    """Tests for the settings-only (no ``production``) construction path,
    i.e. how Report is used from the standalone ``gwdata`` CLI."""

    def test_no_frames_does_not_touch_spectrograms(self):
        with temporary_test_directory() as tmpdir, patch("datafind.report.otter.Otter"):
            report = Report(settings={"time": {"end": 100}}, webdir=tmpdir)
            self.assertEqual(report.frames, {})

    def test_frames_setter_requires_dict(self):
        with temporary_test_directory() as tmpdir, patch("datafind.report.otter.Otter"):
            report = Report(settings={"time": {"end": 100}}, webdir=tmpdir)
            with self.assertRaises(ValueError):
                report.frames = ["not", "a", "dict"]

    def test_setting_frames_adds_spectrograms_using_settings_time(self):
        """
        Regression test: with no ``production`` (the standalone CLI path),
        Report._add_spectrograms used to leave ``post_trigger`` unbound
        (dead code checked ``self.production is not None`` inside the
        branch already guarded by ``self.production is None``), crashing
        with an UnboundLocalError on every frame.
        """
        with temporary_test_directory() as tmpdir, patch("datafind.report.otter.Otter"):
            report = Report(
                settings={"time": {"end": 1126259478}, "likelihood": {"post trigger time": 2}},
                webdir=tmpdir,
            )
            fake_spectrogram = MagicMock()
            with patch("datafind.report.Frame") as mock_frame_cls:
                mock_frame_cls.return_value.spectrogram.return_value = fake_spectrogram
                report.frames = {"H1": ["H-H1_GWOSC-1126259462-32.gwf"]}
                report._add_spectrograms()

            mock_frame_cls.return_value.spectrogram.assert_called_once_with(
                time=1126259476, channel=None
            )

    def test_spectrogram_failure_is_caught_per_frame(self):
        with temporary_test_directory() as tmpdir, patch("datafind.report.otter.Otter"):
            report = Report(
                settings={"time": {"end": 1126259478}, "likelihood": {"post trigger time": 2}},
                webdir=tmpdir,
            )
            with patch("datafind.report.Frame") as mock_frame_cls:
                mock_frame_cls.return_value.spectrogram.side_effect = RuntimeError("boom")
                report.frames = {"H1": ["bad-frame.gwf"]}
                # Should not raise, even though every spectrogram attempt fails.
                report._add_spectrograms()

    def test_single_frame_path_string_is_not_iterated_as_characters(self):
        """
        Regression test: an IFO's frames value can be a single path string
        (per the `frames` property's own docstring), not just a list, but
        _add_spectrograms used to iterate it directly - iterating a string
        character-by-character and trying to build a Frame from each one.
        """
        with temporary_test_directory() as tmpdir, patch("datafind.report.otter.Otter"):
            report = Report(
                settings={"time": {"end": 1126259478}, "likelihood": {"post trigger time": 2}},
                webdir=tmpdir,
            )
            fake_spectrogram = MagicMock()
            with patch("datafind.report.Frame") as mock_frame_cls:
                mock_frame_cls.return_value.spectrogram.return_value = fake_spectrogram
                report.frames = {"H1": "H-H1_GWOSC-1126259462-32.gwf"}
                report._add_spectrograms()

            mock_frame_cls.assert_called_once_with(
                os.path.join("frames", "H-H1_GWOSC-1126259462-32.gwf")
            )

    def test_clear_error_without_production_or_settings(self):
        """
        Regression test: constructing Report with neither `production` nor
        `settings` (both are optional) and later assigning frames used to
        hit an opaque AttributeError from calling `.get()` on
        `self.settings` (None). Like any other per-frame spectrogram
        failure this doesn't crash the whole report (it's caught and noted
        inline), but the note itself should now name the real problem
        instead of the confusing "'NoneType' object has no attribute
        'get'".
        """
        with temporary_test_directory() as tmpdir, patch("datafind.report.otter.Otter"):
            report = Report(webdir=tmpdir)
            with patch("datafind.report.Frame"):
                report.frames = {"H1": ["H-H1_GWOSC-1126259462-32.gwf"]}
                # Should not raise - failures are noted in the report, not
                # propagated - but should fail for the *right* reason.
                report._add_spectrograms()

            messages = [
                call.args[0] for call in report.report.__add__.call_args_list
            ]
            self.assertTrue(
                any("needs either a" in str(m) for m in messages),
                f"Expected a clear 'needs either a production or settings' "
                f"message, got: {messages}",
            )


class TestReportWithProduction(unittest.TestCase):
    """Tests for the production-backed construction path (asimov Pipeline.html())."""

    def test_collects_assets_and_frames_trigger_spectrograms_eagerly(self):
        with temporary_test_directory() as tmpdir, patch("datafind.report.otter.Otter"):
            production = MagicMock()
            production.collect_assets.return_value = {
                "frames": {"H1": ["H-H1_GWOSC-1126259462-32.gwf"]}
            }
            production.meta = {"event time": 1126259462}

            with patch("datafind.report.Frame") as mock_frame_cls:
                mock_frame_cls.return_value.spectrogram.return_value = MagicMock()
                Report(production=production, webdir=tmpdir)

            mock_frame_cls.return_value.spectrogram.assert_called_once_with(
                time=1126259462, channel=None
            )

    def test_no_assets_means_no_frames(self):
        with temporary_test_directory() as tmpdir, patch("datafind.report.otter.Otter"):
            production = MagicMock()
            production.collect_assets.return_value = {}

            report = Report(production=production, webdir=tmpdir)
            self.assertEqual(report.frames, {})


if __name__ == "__main__":
    unittest.main()
