"""
These tests check the operation of code to manipulate PESummary metafiles.
"""

import unittest
import os
import shutil
import urllib.request

from datafind.metafiles import Metafile
from datafind import calibration

# Path to test data file
TEST_DATA_FILE = "tests/GW150914.hdf5"

# Note: To run these tests, you need to either:
# 1. Have the test file already present in tests/GW150914.hdf5, or
# 2. Allow the test to download it from Zenodo (requires network access)
#
# For CI/CD testing without network access, you can:
# - Pre-download the file and commit it to the repository, or
# - Use git-lfs for large files, or
# - Skip these tests when network is unavailable


def setUpModule():
    """
    Set up the test module by downloading test data if needed.
    
    This function runs once before all tests in this module.
    
    Downloads the GW150914 PESummary metafile (~12MB) from Zenodo if it's
    not already present and network access is available. The file is used
    for testing PSD and calibration extraction functionality.
    
    If the download fails (e.g., no network access), tests requiring this
    file will be skipped gracefully with an informative message.
    
    The downloaded file is cached locally and won't be re-downloaded on
    subsequent test runs unless deleted.
    """
    if not os.path.exists(TEST_DATA_FILE):
        # Only try to download if we have network access
        # In CI/CD without network, these tests will be skipped
        try:
            print(f"\nDownloading test data file to {TEST_DATA_FILE}...")
            print("(This is a one-time download of ~12MB from Zenodo)")
            urllib.request.urlretrieve(
                "https://zenodo.org/records/6513631/files/IGWN-GWTC2p1-v2-GW150914_095045_PEDataRelease_mixed_cosmo.h5?download=1",
                TEST_DATA_FILE
            )
            print("Download complete.")
        except Exception as e:
            print(f"\nWarning: Could not download test data: {e}")
            print("Tests requiring this file will be skipped.")


class TestPSDExtraction(unittest.TestCase):

    def setUp(self):
        self.summaryfile = TEST_DATA_FILE
        if not os.path.exists(self.summaryfile):
            self.skipTest(
                f"Test data file {self.summaryfile} not available. "
                "Run tests with network access to download it."
            )

    def test_dump_psd(self):
        with Metafile(self.summaryfile) as metafile:
            metafile.psd()['L1'].to_ascii("L1.txt")
            metafile.psd()['H1'].to_ascii("H1.txt")

        with open("L1.txt", "r") as psd_file:
            data = psd_file.read()

        self.assertEqual(float(data[0][0]), 0)


    @unittest.skipIf(shutil.which("convert_psd_ascii2xml") is None,
                     "RIFT is not installed")
    def test_dump_xml_psd(self):
        with Metafile(self.summaryfile) as metafile:
            metafile.psd()['L1'].to_xml()
            metafile.psd()['H1'].to_xml()

        import os.path
        self.assertTrue(os.path.isfile("H1-psd.xml.gz"))
        self.assertTrue(os.path.isfile("L1-psd.xml.gz"))


class TestCalibrationExtraction(unittest.TestCase):

    def setUp(self):
        self.summaryfile = TEST_DATA_FILE
        if not os.path.exists(self.summaryfile):
            self.skipTest(
                f"Test data file {self.summaryfile} not available. "
                "Run tests with network access to download it."
            )

    def test_dump_calibration(self):
        with Metafile(self.summaryfile) as metafile:
            metafile.calibration()['L1'].to_file("L1.dat")
            metafile.calibration()['H1'].to_file("H1.dat")

        data = calibration.CalibrationUncertaintyEnvelope.from_file("L1.dat")

        self.assertLessEqual(20 - float(data.data[0][0]), 1E-5)
