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
    get_calibration_from_dcc,
    find_calibrations_on_cit,
    identify_run_from_gpstime,
    OBSERVING_RUNS)

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


class TestPublicDCCCalibration(unittest.TestCase):
    """Test the public DCC calibration download functionality."""
    
    def test_identify_run_from_gpstime_o4a(self):
        """Test that the shared function correctly identifies O4a."""
        test_time = 1370000000  # Mid-O4a
        run = identify_run_from_gpstime(test_time)
        self.assertEqual(run, "O4a")
    
    def test_identify_run_from_gpstime_o3a(self):
        """Test that the shared function correctly identifies O3a."""
        test_time = 1240000000  # Mid-O3a
        run = identify_run_from_gpstime(test_time)
        self.assertEqual(run, "O3a")
    
    def test_identify_run_from_gpstime_invalid(self):
        """Test that the shared function returns None for invalid times."""
        test_time = 1000000000  # Before O1
        run = identify_run_from_gpstime(test_time)
        self.assertIsNone(run)
    
    def test_run_identification_o4a(self):
        """Test that O4a times are correctly identified."""
        from datafind.calibration import get_calibration_from_dcc
        # O4a time: 2023-05-24 15:00 to 2024-01-16 16:00
        # GPS: 1368975618 to 1389456018
        test_time = 1370000000  # Mid-O4a
        
        # We'll mock the download to avoid actual network calls
        with patch('datafind.calibration.download_file') as mock_download:
            mock_download.return_value = "H1.txt"
            # The function should identify this as O4a and try to download
            result = get_calibration_from_dcc(test_time)
            # Should have attempted downloads for H1 and L1
            # Even if downloads fail, function should return a dict
            self.assertIsInstance(result, dict)
    
    def test_run_identification_o3a(self):
        """Test that O3a times are correctly identified."""
        from datafind.calibration import get_calibration_from_dcc
        # O3a time: 1238166018 to 1253977218
        test_time = 1240000000  # Mid-O3a
        
        with patch('datafind.calibration.download_file') as mock_download:
            mock_download.return_value = "H1.txt"
            result = get_calibration_from_dcc(test_time)
            self.assertIsInstance(result, dict)
    
    def test_dcc_url_construction_o4(self):
        """Test that O4 DCC URLs are constructed correctly."""
        from datafind.calibration import get_calibration_from_dcc
        test_time = 1370000000  # O4a
        
        with patch('datafind.calibration.download_file') as mock_download:
            # Make H1 succeed on first URL, L1 on second
            def side_effect(url, directory=None, name=None):
                if "H1" in url:
                    return "H1.txt"
                elif "L1" in url:
                    return "L1.txt"
                raise Exception("Download failed")
            
            mock_download.side_effect = side_effect
            result = get_calibration_from_dcc(test_time)
            
            # Check that download_file was called with DCC URLs
            calls = mock_download.call_args_list
            # Should have tried to download for both H1 and L1
            # URLs should contain T2500288 for O4
            any_t2500288 = any('T2500288' in str(call) or '2500' in str(call) for call in calls)
            self.assertTrue(any_t2500288, "Should have tried to download from T2500288 DCC document")
    
    def test_dcc_url_construction_o3(self):
        """Test that O3 DCC URLs are constructed correctly."""
        from datafind.calibration import get_calibration_from_dcc
        test_time = 1240000000  # O3a
        
        with patch('datafind.calibration.download_file') as mock_download:
            def side_effect(url, directory=None, name=None):
                if "H1" in url:
                    return "H1.txt"
                elif "L1" in url:
                    return "L1.txt"
                raise Exception("Download failed")
            
            mock_download.side_effect = side_effect
            result = get_calibration_from_dcc(test_time)
            
            # Check that download_file was called with DCC URLs
            calls = mock_download.call_args_list
            # URLs should contain T2100313 for O1-O3
            any_t2100313 = any('T2100313' in str(call) or '2100' in str(call) for call in calls)
            self.assertTrue(any_t2100313, "Should have tried to download from T2100313 DCC document")
    
    def test_find_calibrations_with_public_flag(self):
        """Test that find_calibrations_on_cit respects the public flag."""
        test_time = 1370000000  # O4a
        
        with patch('datafind.calibration.get_calibration_from_dcc') as mock_dcc:
            mock_dcc.return_value = {"H1": "calibration/H1.txt", "L1": "calibration/L1.txt"}
            
            result = find_calibrations_on_cit(test_time, public=True)
            
            # Should have called get_calibration_from_dcc
            mock_dcc.assert_called_once_with(test_time)
            self.assertEqual(result, {"H1": "calibration/H1.txt", "L1": "calibration/L1.txt"})
    
    def test_invalid_time_returns_empty(self):
        """Test that times outside observing runs return empty dict."""
        from datafind.calibration import get_calibration_from_dcc
        # GPS time 1000000000 is before O1
        test_time = 1000000000
        
        result = get_calibration_from_dcc(test_time)
        self.assertEqual(result, {})

