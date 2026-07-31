"""
Tests for the datafind.main CLI entry point (``gwdata --settings ...``), in
particular the calibration retrieval dispatch in ``get_data``.

These exercise the fix for gwdata issue #27: a single analysis listing
multiple interferometers (optionally with different calibration versions
per interferometer) should fetch each of them with the right mechanism in
one pass, instead of needing a separate analysis per interferometer/source.
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import yaml

from datafind.main import get_data


def _write_settings(path, settings):
    with open(path, "w") as f:
        yaml.safe_dump(settings, f)


class CalibrationDispatchTests(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)
        self._cwd = os.getcwd()
        os.chdir(self.tmpdir)
        self.addCleanup(os.chdir, self._cwd)

    def _run(self, settings):
        settings_path = os.path.join(self.tmpdir, "settings.yaml")
        _write_settings(settings_path, settings)
        get_data.callback(settings=settings_path)

    @patch("datafind.main.calibration.get_calibration_from_frame")
    @patch("datafind.main.calibration.find_calibrations_on_cit")
    def test_default_path_fetches_ligo_and_virgo_together(self, mock_local, mock_frame):
        """A single analysis listing H1, L1 and V1 should fetch all three
        in one call to get_data, without needing separate analyses. Here
        the local archive doesn't have V1 (an O4b-era time), so the frame
        fallback should be used for it."""
        mock_local.return_value = {"H1": "/archive/H1.txt", "L1": "/archive/L1.txt"}

        self._run({
            "data": ["calibration"],
            "time": {"start": 1400000000, "end": 1400000010, "duration": 32},
            "interferometers": ["H1", "L1", "V1"],
            "calibration version": {"H1": "v2", "L1": "v1"},
        })

        mock_local.assert_called_once()
        _, kwargs = mock_local.call_args
        self.assertEqual(kwargs["interferometers"], ["H1", "L1", "V1"])
        self.assertEqual(kwargs["version"], {"H1": "v2", "L1": "v1"})

        mock_frame.assert_called_once()
        _, kwargs = mock_frame.call_args
        self.assertEqual(kwargs["ifo"], "V1")

    @patch("datafind.main.calibration.get_calibration_from_frame")
    @patch("datafind.main.calibration.find_calibrations_on_cit")
    def test_default_path_skips_frame_fallback_when_virgo_already_found(
        self, mock_local, mock_frame
    ):
        """For O2/O3 events Virgo calibration comes back from the local
        archive itself (a text file); the frame-based fallback should not
        be triggered on top of that."""
        mock_local.return_value = {
            "H1": "/archive/H1.txt",
            "L1": "/archive/L1.txt",
            "V1": "/archive/V1.txt",
        }

        self._run({
            "data": ["calibration"],
            "time": {"start": 1240000000, "end": 1240000010, "duration": 32},
            "interferometers": ["H1", "L1", "V1"],
        })

        mock_local.assert_called_once()
        mock_frame.assert_not_called()

    @patch("datafind.main.calibration.get_calibration_from_frame")
    @patch("datafind.main.calibration.find_calibrations_on_cit")
    def test_default_path_skips_virgo_when_not_requested(self, mock_local, mock_frame):
        mock_local.return_value = {"H1": "/archive/H1.txt", "L1": "/archive/L1.txt"}

        self._run({
            "data": ["calibration"],
            "time": {"start": 1400000000, "end": 1400000010, "duration": 32},
            "interferometers": ["H1", "L1"],
        })

        mock_local.assert_called_once()
        mock_frame.assert_not_called()

    @patch("datafind.main.calibration.get_calibration_from_frame")
    @patch("datafind.main.calibration.find_calibrations_on_cit")
    def test_default_path_falls_back_to_frame_when_only_virgo_requested(
        self, mock_local, mock_frame
    ):
        """Local storage is still tried first (it's the only source for
        O2/O3-era Virgo), and only falls through to the frame-based lookup
        when the archive doesn't have it."""
        mock_local.return_value = {}

        self._run({
            "data": ["calibration"],
            "time": {"start": 1400000000, "end": 1400000010, "duration": 32},
            "interferometers": ["V1"],
        })

        mock_local.assert_called_once()
        _, kwargs = mock_local.call_args
        self.assertEqual(kwargs["interferometers"], ["V1"])
        mock_frame.assert_called_once()

    @patch("datafind.main.calibration.get_calibration_from_frame")
    @patch("datafind.main.calibration.find_calibrations_on_cit")
    def test_explicit_local_storage_never_falls_back_to_frame(self, mock_local, mock_frame):
        """`source: {type: local storage}` is an explicit request to use
        only the local archive; it must never trigger frame-based
        (Virgo) retrieval, even if V1 is requested and not found."""
        mock_local.return_value = {"H1": "/archive/H1.txt"}

        self._run({
            "data": ["calibration"],
            "time": {"start": 1400000000, "end": 1400000010, "duration": 32},
            "interferometers": ["H1", "V1"],
            "source": {"type": "local storage"},
        })

        mock_local.assert_called_once()
        mock_frame.assert_not_called()

    @patch("datafind.main.calibration.get_calibration_from_frame")
    @patch("datafind.main.calibration.find_calibrations_on_cit")
    def test_legacy_frame_source_type_still_works(self, mock_local, mock_frame):
        """Old blueprints using `source: {type: frame}` as a dedicated,
        Virgo-only analysis should keep behaving exactly as before."""
        self._run({
            "data": ["calibration"],
            "time": {"start": 1400000000, "end": 1400000010, "duration": 32},
            "source": {"type": "frame"},
        })

        mock_local.assert_not_called()
        mock_frame.assert_called_once()
        _, kwargs = mock_frame.call_args
        self.assertEqual(kwargs["ifo"], "V1")

    @patch("datafind.main.calibration.get_calibration_from_frame")
    @patch("datafind.main.calibration.find_calibrations_on_cit")
    def test_missing_source_block_does_not_crash(self, mock_local, mock_frame):
        """`source` is optional for the default (local storage) path; it
        used to raise AttributeError (`NoneType.get`) when omitted."""
        mock_local.return_value = {"H1": "/archive/H1.txt"}

        self._run({
            "data": ["calibration"],
            "time": {"start": 1400000000, "end": 1400000010, "duration": 32},
            "interferometers": ["H1"],
        })
        mock_local.assert_called_once()
        mock_frame.assert_not_called()

    @patch("datafind.main.calibration.get_calibration_from_frame")
    @patch("datafind.main.calibration.find_calibrations_on_cit")
    def test_no_interferometers_key_defaults_to_both_ligo_sites(self, mock_local, mock_frame):
        """Back-compat: settings with no `interferometers` key at all should
        still try both H1 and L1, matching pre-fix behaviour."""
        mock_local.return_value = {"H1": "/archive/H1.txt", "L1": "/archive/L1.txt"}

        self._run({
            "data": ["calibration"],
            "time": {"start": 1400000000, "end": 1400000010, "duration": 32},
        })

        mock_local.assert_called_once()
        _, kwargs = mock_local.call_args
        self.assertEqual(kwargs["interferometers"], ["H1", "L1"])
        mock_frame.assert_not_called()


if __name__ == "__main__":
    unittest.main()
