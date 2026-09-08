"""
Tests for the ``gwdata`` command-line dispatcher (``datafind.main.get_data``).

These mock out every external call (GWOSC, gwdatafind, filesystem calibration
archives, PESummary metafiles) so the tests only check that a settings file
is dispatched to the right code path with the right arguments.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

import yaml
from click.testing import CliRunner

from datafind.main import get_data
from tests.test_fixtures import create_mock_pesummary_metafile, temporary_test_directory


def write_settings(path, settings):
    with open(path, "w") as f:
        yaml.safe_dump(settings, f)


class TestFramesDispatch(unittest.TestCase):
    def test_frames_uses_gwosc(self):
        with temporary_test_directory() as tmpdir:
            settings_path = os.path.join(tmpdir, "settings.yaml")
            write_settings(
                settings_path,
                {
                    "interferometers": ["H1", "L1"],
                    "time": {"start": 1126259462, "end": 1126259478, "duration": 32},
                    "data": ["frames"],
                },
            )
            with patch("datafind.main.get_data_frames_gwosc") as mock_gwosc:
                mock_gwosc.return_value = ({}, {})
                result = CliRunner().invoke(get_data, ["--settings", settings_path])

            self.assertEqual(result.exit_code, 0, result.output)
            mock_gwosc.assert_called_once_with(["H1", "L1"], 1126259462, 1126259478, 32)


class TestCalibrationDispatch(unittest.TestCase):
    def test_calibration_defaults_to_local_storage_without_source(self):
        """
        Regression test: omitting the ``source`` block entirely for a
        calibration download used to crash with an AttributeError
        (``settings.get("source")`` returned None, then ``.get("type")``
        was called on it unconditionally) even though this is exactly the
        documented minimal example for local-storage calibration retrieval.
        """
        with temporary_test_directory() as tmpdir:
            settings_path = os.path.join(tmpdir, "settings.yaml")
            write_settings(
                settings_path,
                {
                    "time": {"start": 1238166018},
                    "data": ["calibration"],
                    "locations": {"calibration directory": "/home/cal/archive/"},
                    "calibration version": "v1",
                },
            )
            with patch("datafind.main.calibration.find_calibrations_on_cit") as mock_find:
                result = CliRunner().invoke(get_data, ["--settings", settings_path])

            self.assertEqual(result.exit_code, 0, result.output)
            mock_find.assert_called_once_with(
                1238166018, "/home/cal/archive/", version="v1"
            )

    def test_calibration_explicit_local_storage(self):
        with temporary_test_directory() as tmpdir:
            settings_path = os.path.join(tmpdir, "settings.yaml")
            write_settings(
                settings_path,
                {
                    "time": {"start": 1238166018},
                    "data": ["calibration"],
                    "source": {"type": "local storage"},
                },
            )
            with patch("datafind.main.calibration.find_calibrations_on_cit") as mock_find:
                result = CliRunner().invoke(get_data, ["--settings", settings_path])

            self.assertEqual(result.exit_code, 0, result.output)
            mock_find.assert_called_once()

    def test_calibration_from_pesummary(self):
        with temporary_test_directory() as tmpdir:
            settings_path = os.path.join(tmpdir, "settings.yaml")
            write_settings(
                settings_path,
                {
                    "data": ["calibration"],
                    "source": {
                        "type": "pesummary",
                        "location": "fake.h5",
                        "analysis": "C01:IMRPhenomXPHM",
                    },
                },
            )
            fake_envelope = MagicMock()
            fake_metafile = MagicMock()
            fake_metafile.calibration.return_value = {"H1": fake_envelope, "L1": fake_envelope}
            fake_metafile_cm = MagicMock()
            fake_metafile_cm.__enter__.return_value = fake_metafile
            fake_metafile_cm.__exit__.return_value = False

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with patch(
                    "datafind.main.Metafile", return_value=fake_metafile_cm
                ) as mock_meta_cls:
                    result = CliRunner().invoke(get_data, ["--settings", settings_path])
            finally:
                os.chdir(original_cwd)

            self.assertEqual(result.exit_code, 0, result.output)
            mock_meta_cls.assert_called_once_with("fake.h5")
            fake_metafile.calibration.assert_called_once_with("C01:IMRPhenomXPHM")
            self.assertEqual(fake_envelope.to_file.call_count, 2)

    def test_calibration_from_frame(self):
        with temporary_test_directory() as tmpdir:
            settings_path = os.path.join(tmpdir, "settings.yaml")
            write_settings(
                settings_path,
                {
                    "time": {"start": 1380000000},
                    "data": ["calibration"],
                    "source": {"type": "frame"},
                    "interferometers": ["V1"],
                    "virgo prefix": "V1:Hrec_hoft_U00",
                    "virgo frametype": "V1:HoftAR1",
                },
            )
            with patch("datafind.main.calibration.get_calibration_from_frame") as mock_frame:
                result = CliRunner().invoke(get_data, ["--settings", settings_path])

            self.assertEqual(result.exit_code, 0, result.output)
            mock_frame.assert_called_once_with(
                ifo="V1",
                prefix="V1:Hrec_hoft_U00",
                timestamp_channel=None,
                frametype="V1:HoftAR1",
                time=1380000000,
                host="datafind.igwn.org",
            )


class TestPosteriorAndPsdsDispatch(unittest.TestCase):
    def test_posterior_only(self):
        with temporary_test_directory() as tmpdir:
            summary_path = os.path.join(tmpdir, "fake.h5")
            open(summary_path, "w").close()
            settings_path = os.path.join(tmpdir, "settings.yaml")
            write_settings(
                settings_path,
                {
                    "data": ["posterior"],
                    "source": {
                        "type": "pesummary",
                        "location": summary_path,
                        "analysis": "C01:IMRPhenomXPHM",
                    },
                },
            )
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with patch("datafind.main.read") as mock_read:
                    mock_read.return_value = MagicMock()
                    result = CliRunner().invoke(
                        get_data, ["--settings", settings_path], catch_exceptions=False
                    )
            finally:
                os.chdir(original_cwd)

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue(
                os.path.exists(os.path.join(tmpdir, "posterior", "metafile.h5"))
            )

    def test_psds_only(self):
        with temporary_test_directory() as tmpdir:
            settings_path = os.path.join(tmpdir, "settings.yaml")
            write_settings(
                settings_path,
                {
                    "data": ["psds"],
                    "source": {
                        "type": "pesummary",
                        "location": "fake.h5",
                        "analysis": "C01:IMRPhenomXPHM",
                    },
                },
            )
            fake_psd = MagicMock()
            fake_metafile = MagicMock()
            fake_metafile.psd.return_value = {"H1": fake_psd, "L1": fake_psd}
            fake_metafile_cm = MagicMock()
            fake_metafile_cm.__enter__.return_value = fake_metafile
            fake_metafile_cm.__exit__.return_value = False

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                with patch("datafind.main.Metafile", return_value=fake_metafile_cm):
                    result = CliRunner().invoke(get_data, ["--settings", settings_path])
            finally:
                os.chdir(original_cwd)

            self.assertEqual(result.exit_code, 0, result.output)
            fake_metafile.psd.assert_called_once_with("C01:IMRPhenomXPHM")
            self.assertEqual(fake_psd.to_ascii.call_count, 2)
            self.assertEqual(fake_psd.to_xml.call_count, 2)

    def test_psds_without_source_raises(self):
        with temporary_test_directory() as tmpdir:
            settings_path = os.path.join(tmpdir, "settings.yaml")
            write_settings(settings_path, {"data": ["psds"]})
            result = CliRunner().invoke(get_data, ["--settings", settings_path])

            self.assertNotEqual(result.exit_code, 0)
            self.assertIsInstance(result.exception, ValueError)

    def test_psds_with_non_pesummary_source_raises(self):
        with temporary_test_directory() as tmpdir:
            settings_path = os.path.join(tmpdir, "settings.yaml")
            write_settings(
                settings_path,
                {"data": ["psds"], "source": {"type": "local storage"}},
            )
            result = CliRunner().invoke(get_data, ["--settings", settings_path])

            self.assertNotEqual(result.exit_code, 0)
            self.assertIsInstance(result.exception, ValueError)


class TestCombinedDispatch(unittest.TestCase):
    def test_frames_and_calibration_together(self):
        with temporary_test_directory() as tmpdir:
            settings_path = os.path.join(tmpdir, "settings.yaml")
            write_settings(
                settings_path,
                {
                    "interferometers": ["H1", "L1"],
                    "time": {"start": 1126259462, "end": 1126259478, "duration": 32},
                    "data": ["frames", "calibration"],
                    "locations": {"calibration directory": "/home/cal/archive/"},
                    "calibration version": "v1",
                },
            )
            with patch("datafind.main.get_data_frames_gwosc") as mock_gwosc, patch(
                "datafind.main.calibration.find_calibrations_on_cit"
            ) as mock_find:
                mock_gwosc.return_value = ({}, {})
                result = CliRunner().invoke(get_data, ["--settings", settings_path])

            self.assertEqual(result.exit_code, 0, result.output)
            mock_gwosc.assert_called_once()
            mock_find.assert_called_once()


class TestCalibrationAndPsdsFromRealMetafile(unittest.TestCase):
    """
    Runs the CLI dispatcher against a real (synthetic) PESummary-style h5
    file with no mocking of ``Metafile``, to catch wiring issues between
    ``main.get_data`` and ``datafind.metafiles`` that per-function mocks
    would miss.
    """

    def test_calibration_and_psds_from_pesummary_metafile(self):
        with temporary_test_directory() as tmpdir:
            metafile_path = os.path.join(tmpdir, "fake.h5")
            create_mock_pesummary_metafile(metafile_path, ifos=("H1", "L1"))

            settings_path = os.path.join(tmpdir, "settings.yaml")
            write_settings(
                settings_path,
                {
                    "data": ["calibration", "psds"],
                    "source": {
                        "type": "pesummary",
                        "location": metafile_path,
                        "analysis": "C01:IMRPhenomXPHM",
                    },
                },
            )

            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                result = CliRunner().invoke(
                    get_data, ["--settings", settings_path], catch_exceptions=False
                )
            finally:
                os.chdir(original_cwd)

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "calibration", "H1.dat")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "calibration", "L1.dat")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "psds", "H1.dat")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "psds", "L1.dat")))


if __name__ == "__main__":
    unittest.main()
