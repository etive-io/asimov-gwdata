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
    get_o4_style_calibration)

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
