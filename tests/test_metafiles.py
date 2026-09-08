"""
Offline tests for ``datafind.metafiles.Metafile``, using a small synthetic
PESummary-style fixture instead of the ~12MB real GW150914 metafile (see
``tests/test_pesummary.py`` for tests against the real file, which are
skipped when it isn't present).
"""
import os
import unittest

import numpy as np

from datafind.calibration import CalibrationUncertaintyEnvelope
from datafind.metafiles import Metafile
from tests.test_fixtures import create_mock_pesummary_metafile, temporary_test_directory


class TestMetafile(unittest.TestCase):
    def test_psd_default_analysis_selection(self):
        with temporary_test_directory() as tmpdir:
            metafile_path = os.path.join(tmpdir, "fake.h5")
            create_mock_pesummary_metafile(metafile_path, analysis="C01:IMRPhenomXPHM")

            with Metafile(metafile_path) as metafile:
                psds = metafile.psd()  # no analysis given: should pick the only one

            self.assertIn("H1", psds)
            self.assertIn("L1", psds)

    def test_psd_named_analysis_and_to_ascii(self):
        with temporary_test_directory() as tmpdir:
            metafile_path = os.path.join(tmpdir, "fake.h5")
            create_mock_pesummary_metafile(metafile_path, analysis="C01:IMRPhenomXPHM")

            with Metafile(metafile_path) as metafile:
                psds = metafile.psd("C01:IMRPhenomXPHM")
                psds["H1"].to_ascii(os.path.join(tmpdir, "H1.dat"))

            data = np.loadtxt(os.path.join(tmpdir, "H1.dat"))
            self.assertEqual(data.shape[1], 2)

    def test_calibration_named_analysis_and_to_file(self):
        with temporary_test_directory() as tmpdir:
            metafile_path = os.path.join(tmpdir, "fake.h5")
            create_mock_pesummary_metafile(metafile_path, analysis="C01:IMRPhenomXPHM")

            with Metafile(metafile_path) as metafile:
                cals = metafile.calibration("C01:IMRPhenomXPHM")
                self.assertIsInstance(cals["H1"], CalibrationUncertaintyEnvelope)
                cals["H1"].to_file(os.path.join(tmpdir, "H1_envelope.dat"))

            data = CalibrationUncertaintyEnvelope.from_file(
                os.path.join(tmpdir, "H1_envelope.dat")
            )
            # from_file() keeps the on-disk (n_frequencies, 7) row orientation,
            # unlike from_array() which transposes to (7, n_frequencies) - see
            # test_calibration_envelope_orientation for the two compared directly.
            self.assertEqual(data.data.shape[1], 7)
            self.assertAlmostEqual(float(data.data[0][0]), 20.0, places=5)

    def test_unknown_analysis_raises_keyerror(self):
        with temporary_test_directory() as tmpdir:
            metafile_path = os.path.join(tmpdir, "fake.h5")
            create_mock_pesummary_metafile(metafile_path, analysis="C01:IMRPhenomXPHM")

            with Metafile(metafile_path) as metafile:
                with self.assertRaises(KeyError):
                    metafile.psd("NoSuchAnalysis")


if __name__ == "__main__":
    unittest.main()
