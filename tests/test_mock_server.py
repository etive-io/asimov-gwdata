"""
Tests for the mock gwdatafind server.
"""
import unittest
import time
from tests.mock_gwdatafind_server import MockGWDataFindServer


class TestMockGWDataFindServer(unittest.TestCase):
    """Test the mock gwdatafind server functionality."""
    
    def test_server_starts_and_stops(self):
        """Test that the server can start and stop."""
        server = MockGWDataFindServer(port=8766)
        server.start()
        time.sleep(0.2)  # Give it time to start
        server.stop()
    
    def test_server_with_context_manager(self):
        """Test using the server as a context manager."""
        with MockGWDataFindServer(port=8767) as server:
            self.assertIsNotNone(server.server)
    
    def test_server_returns_configured_frames(self):
        """Test that the server returns configured frame URLs."""
        frame_configs = {
            ('H', 'H1_HOFT_C02'): [
                'file:///data/H-H1_HOFT_C02-1126256640-4096.gwf'
            ]
        }
        
        with MockGWDataFindServer(port=8768, frame_configs=frame_configs) as server:
            # Make a request to the server
            import requests
            response = requests.get(
                f'http://localhost:8768/api/v1/gwf/H/H1_HOFT_C02/1126259460,1126259464/file.json',
                timeout=2
            )
            
            self.assertEqual(response.status_code, 200)
            urls = response.json()
            self.assertEqual(len(urls), 1)
            self.assertIn('H1_HOFT_C02', urls[0])
    
    def test_server_with_gwdatafind_client(self):
        """Test that gwdatafind can query the mock server."""
        try:
            import gwdatafind
        except ImportError:
            self.skipTest("gwdatafind not installed")
        
        frame_configs = {
            ('H', 'H1_HOFT_C02'): [
                'file:///data/H-H1_HOFT_C02-1126256640-4096.gwf'
            ],
            ('L', 'L1_HOFT_C02'): [
                'file:///data/L-L1_HOFT_C02-1126256640-4096.gwf'
            ]
        }
        
        with MockGWDataFindServer(port=8769, frame_configs=frame_configs) as server:
            # Query using gwdatafind with http:// explicitly
            urls = gwdatafind.find_urls(
                'H', 'H1_HOFT_C02',
                1126259460, 1126259464,
                host='http://localhost:8769'
            )
            
            self.assertEqual(len(urls), 1)
            self.assertIn('H1_HOFT_C02', urls[0])


if __name__ == '__main__':
    unittest.main()
