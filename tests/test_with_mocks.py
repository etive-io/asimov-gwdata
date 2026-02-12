"""
Tests demonstrating the use of mock fixtures for asimov-gwdata.

These tests show how to use the test fixtures to test asimov-gwdata
functionality without requiring access to external resources.
"""
import unittest
import os
from unittest.mock import patch

from tests.test_fixtures import (
    MockGWDataFind,
    MockGWOSC,
    temporary_test_directory,
    get_test_data_path
)


class TestMockFixtures(unittest.TestCase):
    """Test that the mock fixtures work correctly."""
    
    def test_mock_gwdatafind(self):
        """Test that MockGWDataFind correctly mocks find_urls."""
        # Set up mock with some test frame files
        mock_frames = {
            ('H', 'H1_HOFT_C02'): [
                'file:///data/H-H1_HOFT_C02-1126259460-4096.gwf'
            ]
        }
        mock_server = MockGWDataFind(mock_frames)
        
        # Test the mock directly
        urls = mock_server.mock_find_urls('H', 'H1_HOFT_C02', 1126259460, 1126259464)
        self.assertEqual(len(urls), 1)
        self.assertIn('H-H1_HOFT_C02', urls[0])
    
    def test_mock_gwdatafind_with_patch(self):
        """Test that MockGWDataFind works with patching."""
        mock_frames = {
            ('L', 'L1_HOFT_C02'): [
                'file:///data/L-L1_HOFT_C02-1126259460-4096.gwf'
            ]
        }
        mock_server = MockGWDataFind(mock_frames)
        
        with mock_server.patch_find_urls():
            # Import after patching to ensure the mock is active
            from gwdatafind import find_urls
            
            urls = find_urls('L', 'L1_HOFT_C02', 1126259460, 1126259464)
            self.assertEqual(len(urls), 1)
    
    def test_mock_gwosc(self):
        """Test that MockGWOSC correctly mocks get_urls."""
        mock_urls = {
            'H1': [
                'https://mock.gwosc/H-H1_GWOSC_O2_4KHZ_R1-1126259460-4096.gwf'
            ],
            'L1': [
                'https://mock.gwosc/L-L1_GWOSC_O2_4KHZ_R1-1126259460-4096.gwf'
            ]
        }
        mock_gwosc = MockGWOSC(mock_urls)
        
        # Test the mock directly
        urls = mock_gwosc.mock_get_urls('H1', 1126259460, 1126259464)
        self.assertEqual(len(urls), 1)
        self.assertIn('H1_GWOSC', urls[0])
    
    def test_temporary_test_directory(self):
        """Test that temporary test directory is created and cleaned up."""
        test_file_path = None
        
        with temporary_test_directory() as tmpdir:
            # Verify directory exists
            self.assertTrue(os.path.exists(tmpdir))
            
            # Create a test file
            test_file_path = os.path.join(tmpdir, 'test.txt')
            with open(test_file_path, 'w') as f:
                f.write('test data')
            
            self.assertTrue(os.path.exists(test_file_path))
        
        # Verify directory is cleaned up
        self.assertFalse(os.path.exists(tmpdir))
        self.assertFalse(os.path.exists(test_file_path))
    
    def test_get_test_data_path(self):
        """Test that get_test_data_path returns correct path."""
        path = get_test_data_path('V1.gwf')
        self.assertTrue(path.endswith('test_data/V1.gwf'))
        # The file should exist
        self.assertTrue(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
