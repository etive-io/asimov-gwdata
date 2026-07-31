import unittest
from unittest.mock import patch
import os
import numpy as np
import igwn_auth_utils

try:
    a = igwn_auth_utils.find_scitoken(audience="https://datafind.igwn.org", scope="gwdatafind.read")
    logged_in=True
except igwn_auth_utils.IgwnAuthError as e:
    print(e)
    logged_in=False


#from datafind.frames import get_data_frames_private
from datafind.calibration import    (
    CalibrationUncertaintyEnvelope,
    get_calibration_from_frame,
    get_o4_style_calibration,
    find_calibrations_on_cit)

class CalibrationDataTests(unittest.TestCase):
    """
    These tests are intended to demonstrate that the
    package will correctly identify calibration files
    in the file structure which is provided to it.
    """

    @patch('glob.glob')
    def test_lookup(self, mock_glob):
        """Test to check that the nearest uncertainty file is correctly identified."""
        file_list =  [
            "/home/cal/public_html/archive/H1/uncertainty/1370/242226/calibration_uncertainty_H1_1370242224.txt",
            "/home/cal/public_html/archive/H1/uncertainty/1370/242226/calibration_uncertainty_H1_1370242226.txt",
            "/home/cal/public_html/archive/H1/uncertainty/1370/242226/calibration_uncertainty_H1_1370242228.txt"
        ]
        mock_glob.return_value = file_list

        output = get_o4_style_calibration(dir="test", time=1370242226.4)

        self.assertEqual(output.get('L1', 0), 0)
        self.assertEqual(output['H1'], file_list[1])

    @patch('glob.glob')
    def test_lookup_with_added_extras(self, mock_glob):
        """Test to check that the nearest uncertainty file is correctly identified."""
        file_list =  [
            "/home/cal/public_html/archive/H1/uncertainty/1370/242226/calibration_uncertainty_H1_1370242224.txt",
            "/home/cal/public_html/archive/H1/uncertainty/1370/242226/calibration_uncertainty_H1_1370242226.txt",
            "/home/cal/public_html/archive/H1/uncertainty/1370/242226/calibration_uncertainty_H1_1370242228.txt"
            "/home/cal/public_html/archive/H1/uncertainty/1370/242226/calibration_uncertainty_H1_1_pydarm2.txt",
            "/home/cal/public_html/archive/H1/uncertainty/1370/242226/calibration_uncertainty_H1_random.txt",
            "/home/cal/public_html/archive/H1/uncertainty/1370/242226/calibration_uncertainty_H1_90.txt",

            "/home/cal/public_html/archive/L1/uncertainty/1370/242226/calibration_uncertainty_L1_1370242226.txt",
        ]

        mock_glob.return_value = file_list

        output = get_o4_style_calibration(dir="test", time=1370242226.4)
        self.assertEqual(output['H1'], file_list[1])
        self.assertEqual(output['L1'], file_list[-1])

    @patch('glob.glob')
    def test_lookup_restricts_to_requested_interferometers(self, mock_glob):
        """
        An analysis which only asks for H1 should never return (or attempt
        to write out) an L1 envelope, even if L1 files are present.
        """
        file_list = [
            "/home/cal/public_html/archive/H1/uncertainty/1370/242226/calibration_uncertainty_H1_1370242226.txt",
            "/home/cal/public_html/archive/L1/uncertainty/1370/242226/calibration_uncertainty_L1_1370242226.txt",
        ]
        mock_glob.return_value = file_list

        output = get_o4_style_calibration(
            dir="test", time=1370242226.4, interferometers=["H1"]
        )

        self.assertIn("H1", output)
        self.assertNotIn("L1", output)

    @patch('glob.glob')
    def test_lookup_per_ifo_version_does_not_cross_contaminate(self, mock_glob):
        """
        Regression test for https://git.ligo.org/asimov/pipelines/gwdata/-/issues/27:
        requesting different calibration versions for different interferometers
        in a single call must not let one interferometer's version leak into,
        or overwrite, another's.
        """
        v2_h1 = "/archive/H1/uncertainty/v2/1370/242226/calibration_uncertainty_H1_1370242226.txt"
        v1_l1 = "/archive/L1/uncertainty/v1/1370/242226/calibration_uncertainty_L1_1370242226.txt"

        def fake_glob(pattern):
            if os.path.join("H1", "uncertainty", "v2") in pattern:
                return [v2_h1]
            if os.path.join("L1", "uncertainty", "v1") in pattern:
                return [v1_l1]
            # Any other IFO/version combination should not be queried.
            return []

        mock_glob.side_effect = fake_glob

        output = get_o4_style_calibration(
            dir="/archive",
            time=1370242226.4,
            version={"H1": "v2", "L1": "v1"},
        )

        self.assertEqual(output["H1"], v2_h1)
        self.assertEqual(output["L1"], v1_l1)

    @patch('glob.glob')
    def test_lookup_skips_ifo_missing_from_version_dict(self, mock_glob):
        """If a per-IFO version dict doesn't mention an interferometer, it
        should be skipped rather than guessing a version for it."""
        mock_glob.return_value = [
            "/archive/H1/uncertainty/v2/1370/242226/calibration_uncertainty_H1_1370242226.txt",
        ]

        output = get_o4_style_calibration(
            dir="/archive",
            time=1370242226.4,
            version={"H1": "v2"},
        )

        self.assertIn("H1", output)
        self.assertNotIn("L1", output)


class FindCalibrationsOnCitTests(unittest.TestCase):
    """
    Tests for the observing-run dispatch and interferometer/Virgo gating
    in ``find_calibrations_on_cit``.
    """

    def setUp(self):
        patcher = patch("datafind.calibration.copy_file")
        self.addCleanup(patcher.stop)
        self.mock_copy_file = patcher.start()

    def test_o1_does_not_raise(self):
        """
        Regression test: O1-era times used to raise a NameError because
        `data` was never initialised before being used on that branch.
        """
        result = find_calibrations_on_cit(time=1130000000)
        self.assertEqual(result, {})

    def test_time_outside_any_observing_run(self):
        result = find_calibrations_on_cit(time=1)
        self.assertEqual(result, {})

    @patch("datafind.calibration.get_o3_style_calibration")
    def test_o3_virgo_only_included_when_requested(self, mock_o3):
        mock_o3.return_value = {"H1": "/path/H1.txt", "L1": "/path/L1.txt"}

        result = find_calibrations_on_cit(time=1240000000, interferometers=["H1", "L1"])
        self.assertNotIn("V1", result)

        result = find_calibrations_on_cit(
            time=1240000000, interferometers=["H1", "L1", "V1"]
        )
        self.assertIn("V1", result)

    @patch("datafind.calibration.get_o4_style_calibration")
    def test_o4_passes_interferometers_and_version_through(self, mock_o4):
        mock_o4.return_value = {"H1": "/path/H1.txt"}

        find_calibrations_on_cit(
            time=1400000000,
            version={"H1": "v2", "L1": "v1"},
            interferometers=["H1"],
        )

        mock_o4.assert_called_once()
        args, kwargs = mock_o4.call_args
        self.assertEqual(kwargs.get("interferometers") or args[3], ["H1"])


@unittest.skipIf(logged_in==False, "No scitoken was found")
class TestFrameCalibration(unittest.TestCase):
    """Test the workflow for finding a frame and extracting a calibration envelope."""
    def setUp(self):
        self.time = 1415277701 #1412725132

    def test_lookup(self):
        
        get_calibration_from_frame(
            ifo='V1',
            time=self.time,
            prefix="V1:Hrec_hoftRepro1AR_U01"
        )

        data_1 = np.loadtxt("calibration/V1.dat")
        data_2 = np.loadtxt("tests/test_data/test_envelope.txt")

        np.testing.assert_equal(data_1, data_2)
