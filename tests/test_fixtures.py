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
from unittest.mock import patch
from typing import Dict, List, Optional

import numpy as np
import h5py


def create_mock_frame_file(output_path, gps_start=1126259460, duration=4096):
    """
    Create a minimal mock GWF frame file for testing.
    
    Note: Currently this function copies an existing test frame file
    or creates an empty placeholder. The gps_start and duration parameters
    are reserved for future enhancement when we can create proper frame
    files with specific GPS times using gwpy.
    
    Parameters
    ----------
    output_path : str
        Path where the mock frame file should be created.
    gps_start : int, optional
        GPS start time for the frame. Default is 1126259460 (around GW150914).
        Currently not used, reserved for future implementation.
    duration : int, optional
        Duration of the frame in seconds. Default is 4096.
        Currently not used, reserved for future implementation.
        
    Returns
    -------
    str
        Path to the created frame file.
        
    TODO
    ----
    - Implement proper frame file creation with specified GPS time and duration
    - Use gwpy to create frames with known data for testing
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
    def patch_find_urls(self, import_path='gwdatafind.find_urls'):
        """
        Context manager to patch gwdatafind.find_urls with the mock.
        
        Parameters
        ----------
        import_path : str, optional
            The import path to patch. Default is 'gwdatafind.find_urls'.
            Use 'datafind.frames.find_urls' if patching where it's imported.
        
        Yields
        ------
        MockGWDataFind
            This mock instance.
        """
        with patch(import_path, side_effect=self.mock_find_urls):
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


def create_mock_pesummary_metafile(
    output_path,
    analysis="C01:IMRPhenomXPHM",
    ifos=("H1", "L1"),
    n_frequencies=16,
):
    """
    Create a small synthetic PESummary-style metafile for offline testing.

    This does not use PESummary's own metafile writer (which expects a full
    summarypages run's worth of inputs); instead it hand-builds just enough
    HDF5 structure for ``datafind.metafiles.Metafile`` to read - a top-level
    ``history``/``version`` pair (used to pick a default analysis name when
    none is given) plus one analysis group containing ``psds`` and
    ``calibration_envelope`` sub-groups, each with one dataset per detector.

    Parameters
    ----------
    output_path : str
        Where to write the ``.h5`` file.
    analysis : str, optional
        The analysis label the data is stored under. Defaults to
        ``"C01:IMRPhenomXPHM"``, matching the label used throughout the docs
        and other test fixtures.
    ifos : sequence of str, optional
        Detectors to generate PSD/calibration data for. Defaults to
        ``("H1", "L1")``.
    n_frequencies : int, optional
        Number of frequency bins in the synthetic PSD/calibration arrays.

    Returns
    -------
    str
        The path the file was written to.
    """
    frequencies = np.linspace(20.0, 1024.0, n_frequencies)

    with h5py.File(output_path, "w") as f:
        f.create_dataset("history", data=b"synthetic test fixture")
        f.create_dataset("version", data=b"v1.0.0")

        group = f.create_group(analysis)
        psds = group.create_group("psds")
        calibration = group.create_group("calibration_envelope")

        for ifo in ifos:
            psd_data = np.column_stack(
                [frequencies, np.ones(n_frequencies) * 1e-46]
            )
            psds.create_dataset(ifo, data=psd_data)

            envelope_data = np.column_stack(
                [
                    frequencies,
                    np.ones(n_frequencies),  # median magnitude
                    np.zeros(n_frequencies),  # median phase
                    np.ones(n_frequencies) * 0.95,  # 16th percentile magnitude
                    np.ones(n_frequencies) * -0.05,  # 16th percentile phase
                    np.ones(n_frequencies) * 1.05,  # 84th percentile magnitude
                    np.ones(n_frequencies) * 0.05,  # 84th percentile phase
                ]
            )
            calibration.create_dataset(ifo, data=envelope_data)

    return output_path
