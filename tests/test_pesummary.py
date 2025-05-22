"""
These tests check the operation of code to manipulate PESummary metafiles.
"""

import unittest
import os
import shutil
import urllib.request

from datafind.metafiles import Metafile

class TestPSDExtraction(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        if not os.path.exists("tests/GW150914.hdf5"):
            urllib.request.urlretrieve("https://zenodo.org/records/6513631/files/IGWN-GWTC2p1-v2-GW150914_095045_PEDataRelease_mixed_cosmo.h5?download=1",
                                       "tests/GW150914.hdf5")
    
    def setUp(self):
        self.summaryfile = "tests/GW150914.hdf5"
    
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
