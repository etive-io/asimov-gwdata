import unittest
from unittest.mock import Mock, patch
import glob
from datafind.main import get_o4_style_calibration
from datafind.calibration import CalibrationUncertaintyEnvelope

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
        self.assertEqual(output['L1'], file_list[1])


class VirgoCalibration(unittest.TestCase):
    """Test Virgo-style calibration uncertainty, distributed in frames."""

    
    def setUp(self):
        """Create a calibration envelope object"""
        self.test_frame = "tests/test_data/V-HoftAR1-1397154000-2000.gwf"

        self.envelope = CalibrationUncertaintyEnvelope(frame=self.test_frame)

    def test_columns(self):
        """Test that the columns match what bilby anticipates"""
        columns = ["Frequency", "Median mag", "Median phase (Rad)", "16th percentile mag",
                   "16th percentile phase",  "84th percentile mag",   "84th percentile phase"]
        self.assertEqual(self.envelope.columns, columns)
