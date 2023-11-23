import unittest
from unittest.mock import Mock, patch
import glob
from datafind.main import get_o4_style_calibration

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
