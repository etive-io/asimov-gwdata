"""
Tests for downloading calibration uncertainty envelopes from the public
LIGO DCC (``datafind.calibration.get_calibration_from_dcc``).

Real DCC archives are multi-MB tarballs, so these tests build small
fixture tarballs that reproduce the real internal layouts (confirmed by
hand against https://dcc.ligo.org/LIGO-T2100313/public and
https://dcc.ligo.org/LIGO-T2500288/public) and patch ``download_file`` to
serve them locally instead of hitting the network.
"""
import os
import shutil
import tarfile
import unittest
from unittest.mock import patch

from tests.test_fixtures import temporary_test_directory

from datafind.calibration import (
    DCC_LIGO_ARCHIVES,
    DCC_VIRGO_ARCHIVES,
    _identify_dcc_run_from_gpstime,
    get_calibration_from_dcc,
)

ENVELOPE_HEADER = (
    "# Frequency\tMedian mag\tMedian phase (Rad)\t16th percentile mag\t"
    "16th percentile phase\t84th percentile mag\t84th percentile phase\n"
)
ENVELOPE_ROW = "+1.0000000e+01 +1.0e+00 +0.0e+00 +8.0e-01 -2.0e-01 +1.2e+00 +2.0e-01\n"


def _write_envelope_file(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(ENVELOPE_HEADER)
        f.write(ENVELOPE_ROW)


def _make_tarball(src_root, tgz_path):
    with tarfile.open(tgz_path, "w:gz") as tar:
        for entry in os.listdir(src_root):
            tar.add(os.path.join(src_root, entry), arcname=entry)


def _build_o3_style_archive(build_dir, tgz_path, gps_times_by_ifo):
    """{IFO}/<date>_<run>_<SITE>_GPSTime_<gps>_C02_..._FinalResults.txt"""
    site_by_ifo = {"H1": "LHO", "L1": "LLO"}
    for ifo, times in gps_times_by_ifo.items():
        for gps in times:
            fname = (
                f"Jun-28-2017_O1_{site_by_ifo[ifo]}_GPSTime_{gps}"
                "_C02_RelativeResponseUncertainty_FinalResults.txt"
            )
            _write_envelope_file(os.path.join(build_dir, ifo, fname))
    _make_tarball(build_dir, tgz_path)


def _build_hourly_archive(build_dir, tgz_path, run, gps_times_by_ifo):
    """{IFO}_{run}/calibration_uncertainty_{IFO}_{gps}.txt"""
    for ifo, times in gps_times_by_ifo.items():
        for gps in times:
            _write_envelope_file(
                os.path.join(
                    build_dir, f"{ifo}_{run}", f"calibration_uncertainty_{ifo}_{gps}.txt"
                )
            )
    _make_tarball(build_dir, tgz_path)


def _build_virgo_archive(build_dir, tgz_path, filenames):
    for fname in filenames:
        _write_envelope_file(os.path.join(build_dir, "V1", fname))
    _make_tarball(build_dir, tgz_path)


def _fake_download_file(prebuilt_tgz):
    """A stand-in for datafind.calibration.download_file that serves a
    pre-built local tarball instead of reaching the real DCC."""

    def _download(url, directory="frames", name=None):
        os.makedirs(directory, exist_ok=True)
        local_name = name or os.path.basename(url)
        dest = os.path.join(directory, local_name)
        if not os.path.exists(dest):
            shutil.copyfile(prebuilt_tgz, dest)
        return local_name

    return _download


class TestIdentifyDccRun(unittest.TestCase):
    def test_o4a_time(self):
        self.assertEqual(_identify_dcc_run_from_gpstime(1370000000), "O4a")

    def test_o1_time(self):
        self.assertEqual(_identify_dcc_run_from_gpstime(1130000000), "O1")

    def test_outside_any_run(self):
        self.assertIsNone(_identify_dcc_run_from_gpstime(1000000000))


class TestGetCalibrationFromDcc(unittest.TestCase):
    def test_o3_style_archive_selects_nearest_and_copies(self):
        with temporary_test_directory() as tmpdir:
            build_dir = os.path.join(tmpdir, "build")
            tgz_path = os.path.join(tmpdir, "LIGO_O3_cal_uncertainty.tgz")
            _build_o3_style_archive(
                build_dir,
                tgz_path,
                {
                    "H1": [1238166100, 1238166200],
                    "L1": [1238166100, 1238166200],
                },
            )

            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch(
                    "datafind.calibration.download_file", _fake_download_file(tgz_path)
                ):
                    data = get_calibration_from_dcc(
                        time=1238166190,
                        run="O3a",
                        interferometers=("H1", "L1"),
                        cache_dir="dcc_cache",
                    )

                self.assertIn("GPSTime_1238166200", data["H1"])
                self.assertIn("GPSTime_1238166200", data["L1"])
                self.assertTrue(os.path.exists(os.path.join("calibration", "H1.txt")))
                self.assertTrue(os.path.exists(os.path.join("calibration", "L1.txt")))
            finally:
                os.chdir(original_cwd)

    def test_hourly_style_archive_selects_nearest(self):
        with temporary_test_directory() as tmpdir:
            build_dir = os.path.join(tmpdir, "build")
            tgz_path = os.path.join(tmpdir, "LIGO_ER16_cal_uncertainty.tgz")
            _build_hourly_archive(
                build_dir,
                tgz_path,
                "ER16",
                {
                    "H1": [1396417050],
                    "L1": [1396417050],
                },
            )

            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch(
                    "datafind.calibration.download_file", _fake_download_file(tgz_path)
                ):
                    data = get_calibration_from_dcc(
                        time=1396417055,
                        run="ER16",
                        interferometers=("H1", "L1"),
                        cache_dir="dcc_cache",
                    )

                self.assertIn("calibration_uncertainty_H1_1396417050", data["H1"])
                self.assertIn("calibration_uncertainty_L1_1396417050", data["L1"])
            finally:
                os.chdir(original_cwd)

    def test_virgo_o3_picks_correct_half_of_run(self):
        with temporary_test_directory() as tmpdir:
            build_dir = os.path.join(tmpdir, "build")
            tgz_path = os.path.join(tmpdir, "Virgo_O3_cal_uncertainty.tgz")
            _build_virgo_archive(
                build_dir,
                tgz_path,
                [
                    "V_O3a_calibrationUncertaintyEnvelope_magnitude5percent.txt",
                    "V_O3b_calibrationUncertaintyEnvelope_magnitude5percent.txt",
                ],
            )

            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch(
                    "datafind.calibration.download_file", _fake_download_file(tgz_path)
                ):
                    data = get_calibration_from_dcc(
                        time=1238166190,
                        run="O3a",
                        interferometers=("V1",),
                        cache_dir="dcc_cache",
                    )

                self.assertIn("V_O3a_", data["V1"])
            finally:
                os.chdir(original_cwd)

    def test_v1_not_available_for_o4a_warns_and_omits(self):
        with temporary_test_directory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch("datafind.calibration.download_file") as mock_download:
                    mock_download.side_effect = AssertionError(
                        "should not attempt to download a LIGO archive for V1-only request"
                    )
                    data = get_calibration_from_dcc(
                        time=1370000000,
                        run="O4a",
                        interferometers=("V1",),
                    )
                self.assertEqual(data, {})
            finally:
                os.chdir(original_cwd)

    def test_time_outside_covered_runs_returns_empty(self):
        data = get_calibration_from_dcc(time=1000000000)
        self.assertEqual(data, {})

    def test_archive_only_downloaded_and_extracted_once(self):
        with temporary_test_directory() as tmpdir:
            build_dir = os.path.join(tmpdir, "build")
            tgz_path = os.path.join(tmpdir, "LIGO_ER16_cal_uncertainty.tgz")
            _build_hourly_archive(
                build_dir, tgz_path, "ER16", {"H1": [1396417050], "L1": [1396417050]}
            )

            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                fake = _fake_download_file(tgz_path)
                with patch(
                    "datafind.calibration.download_file", side_effect=fake
                ) as mock_download:
                    get_calibration_from_dcc(
                        time=1396417055, run="ER16", cache_dir="dcc_cache"
                    )
                    get_calibration_from_dcc(
                        time=1396417055, run="ER16", cache_dir="dcc_cache"
                    )
                self.assertEqual(mock_download.call_count, 1)
            finally:
                os.chdir(original_cwd)


class TestDccArchiveUrls(unittest.TestCase):
    """Guard against silently losing a run mapping in a future edit."""

    def test_all_ligo_runs_have_urls(self):
        for run in ("O1", "O2", "O3a", "O3b", "ER16", "O4a", "O4b"):
            self.assertIn(run, DCC_LIGO_ARCHIVES)
            self.assertTrue(DCC_LIGO_ARCHIVES[run].startswith("https://dcc.ligo.org/"))

    def test_virgo_only_covers_o2_o3(self):
        self.assertEqual(set(DCC_VIRGO_ARCHIVES.keys()), {"O2", "O3a", "O3b"})
