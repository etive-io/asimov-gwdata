"""
Test fixtures and utilities for asimov-gwdata.

This module provides test fixtures, mocks, and utilities for testing
asimov-gwdata without requiring access to external data sources like
GWOSC, gwdatafind servers, or Zenodo.
"""
import os
import tempfile
import shutil
from pathlib import Path
from contextlib import contextmanager
from unittest.mock import MagicMock, patch
from typing import Dict, List, Optional


def create_mock_frame_file(output_path, gps_start=1126259460, duration=4096):
    """
    Create a minimal mock GWF frame file for testing.
    
    Parameters
    ----------
    output_path : str
        Path where the mock frame file should be created.
    gps_start : int, optional
        GPS start time for the frame. Default is 1126259460 (around GW150914).
    duration : int, optional
        Duration of the frame in seconds. Default is 4096.
        
    Returns
    -------
    str
        Path to the created frame file.
    """
    # For now, just copy the existing test frame if it exists
    # In a real implementation, you might use gwpy to create a proper frame
    test_frame = Path(__file__).parent / "test_data" / "V1.gwf"
    if test_frame.exists():
        shutil.copy(test_frame, output_path)
    else:
        # Create an empty file as placeholder
        Path(output_path).touch()
    return output_path


class MockGWDataFind:
    """
    Mock gwdatafind server for testing.
    
    This class provides a simple mock that can be used to replace
    gwdatafind.find_urls in tests, returning pre-configured URLs
    instead of making actual network requests.
    
    Parameters
    ----------
    frame_files : dict, optional
        Dictionary mapping (site, frametype) tuples to lists of frame file paths.
        
    Examples
    --------
    >>> mock_server = MockGWDataFind({
    ...     ('H', 'H1_HOFT_C02'): ['file:///path/to/H-H1_HOFT_C02-1126259460-4096.gwf']
    ... })
    >>> with mock_server.patch_find_urls():
    ...     # Your tests here will use the mock
    ...     pass
    """
    
    def __init__(self, frame_files: Optional[Dict] = None):
        self.frame_files = frame_files or {}
        
    def mock_find_urls(self, site, frametype, gpsstart, gpsend, **kwargs):
        """
        Mock implementation of gwdatafind.find_urls.
        
        Returns pre-configured frame file URLs based on the site and frametype.
        """
        key = (site, frametype)
        if key in self.frame_files:
            return self.frame_files[key]
        return []
    
    @contextmanager
    def patch_find_urls(self):
        """
        Context manager to patch gwdatafind.find_urls with the mock.
        
        Yields
        ------
        MockGWDataFind
            This mock instance.
        """
        with patch('gwdatafind.find_urls', side_effect=self.mock_find_urls):
            yield self


class MockGWOSC:
    """
    Mock GWOSC (Gravitational Wave Open Science Center) interface.
    
    This class provides a mock for gwosc.locate.get_urls to avoid
    making actual network requests to GWOSC during testing.
    
    Parameters
    ----------
    frame_urls : dict, optional
        Dictionary mapping detector names to lists of frame URLs.
        
    Examples
    --------
    >>> mock_gwosc = MockGWOSC({
    ...     'H1': ['https://mock.gwosc/H-H1_GWOSC_O2_4KHZ_R1-1126259460-4096.gwf']
    ... })
    >>> with mock_gwosc.patch_get_urls():
    ...     # Your tests here
    ...     pass
    """
    
    def __init__(self, frame_urls: Optional[Dict[str, List[str]]] = None):
        self.frame_urls = frame_urls or {}
        
    def mock_get_urls(self, detector, start, end, **kwargs):
        """
        Mock implementation of gwosc.locate.get_urls.
        """
        return self.frame_urls.get(detector, [])
    
    @contextmanager
    def patch_get_urls(self):
        """
        Context manager to patch gwosc.locate.get_urls with the mock.
        
        Yields
        ------
        MockGWOSC
            This mock instance.
        """
        with patch('gwosc.locate.get_urls', side_effect=self.mock_get_urls):
            yield self


@contextmanager
def temporary_test_directory():
    """
    Create a temporary directory for test data.
    
    Yields
    ------
    str
        Path to the temporary directory. The directory is automatically
        cleaned up when the context exits.
        
    Examples
    --------
    >>> with temporary_test_directory() as tmpdir:
    ...     # Create test files in tmpdir
    ...     test_file = os.path.join(tmpdir, 'test.txt')
    ...     with open(test_file, 'w') as f:
    ...         f.write('test data')
    """
    tmpdir = tempfile.mkdtemp(prefix='gwdata_test_')
    try:
        yield tmpdir
    finally:
        if os.path.exists(tmpdir):
            shutil.rmtree(tmpdir)


def get_test_data_path(filename):
    """
    Get the absolute path to a test data file.
    
    Parameters
    ----------
    filename : str
        Name of the test data file.
        
    Returns
    -------
    str
        Absolute path to the test data file.
    """
    test_dir = Path(__file__).parent
    return str(test_dir / "test_data" / filename)
