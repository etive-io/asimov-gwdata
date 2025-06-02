import unittest
from unittest.mock import patch
import os
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


@unittest.skipIf(~os.path.exists("/cvmfs/virgo.storage.igwn.org"), reason="CVMFS is not available on this system")
class TestFrameCalibration(unittest.TestCase):
    """Test the workflow for finding a frame and extracting a calibration envelope."""
    def setUp(self):
        self.time = 1397154010

    @patch('gwdatafind.find_urls')
    @patch('datafind.utils.download_file')
    def test_lookup(self, mocklookup, mockdownload):
        mocklookup.return_value = ["file:///tests/test_data/V-HoftAR1-1397154000-2000.gwf"]
        mockdownload.return_value = ["tests/test_data/V-HoftAR1-1397154000-2000.gwf"]
        get_calibration_from_frame(
            ifo='V1',
            time=self.time)

class TestVirgoCalibration(unittest.TestCase):
    """Test Virgo-style calibration uncertainty, distributed in frames."""


    def setUp(self):
        """Create a calibration envelope object"""
        self.test_frame = "tests/test_data/V1.gwf"
        self.envelope = CalibrationUncertaintyEnvelope.from_frame(frame=self.test_frame)

    def test_plot(self):
        """Create a plot of the envelope"""
        self.envelope.plot("test_envelope.png")

    def test_save_file(self):
        """Create a text file of the envelope."""
        self.envelope.to_file("test_envelope.txt")

# I can't get NDS2 to find the virgo data yet.

# class VirgoCalibrationNDS(unittest.TestCase):
#     """Test Virgo-style calibration uncertainty, distributed in frames."""

#     def setUp(self):
#         """Create a calibration envelope object"""
#         self.envelope = CalibrationUncertaintyEnvelope.from_time(time=1397154000)

#     def test_plot(self):
#         """Create a plot of the envelope"""
#         self.envelope.plot("test_envelope.png")

#     def test_save_file(self):
#         """Create a text file of the envelope."""
#         self.envelope.to_file("test_envelope.txt")
