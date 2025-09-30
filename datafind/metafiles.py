"""
Functions to manipulate PESummary metafiles.
"""

import shutil
import logging
import h5py
import contextlib
import subprocess
import os
import numpy as np

from .calibration import CalibrationUncertaintyEnvelope

logger = logging.getLogger("gwdata")

class Metafile(contextlib.AbstractContextManager):
    """
    This class handles PESummary metafiles in an efficient manner.
    """

    def __init__(self,  filename: str):
        """
        Read a PESummary Metafile.

        Parameters
        ----------
        filename : str
           The path to the metafile.

        """
        self.filename = filename


    def __enter__(self):

        self.metafile = h5py.File(self.filename)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.metafile.close()

    def psd(self, analysis=None):
        if not analysis:
            # If no analysis is specified use the first one
            analyses = list(self.metafile.keys())
            analyses.remove("history")
            analyses.remove("version")
            analysis = sorted(analyses)[0]
        psds = {}
        for ifo, psd in self.metafile[analysis]['psds'].items():
            psds[ifo] = PSD(psd, ifo=ifo)
        return psds

    def calibration(self, analysis=None):
        if not analysis:
            # If no analysis is specified use the first one
            analyses = list(self.metafile.keys())
            analyses.remove("history")
            analyses.remove("version")
            analysis = sorted(analyses)[0]
        cals = {}
        for ifo, cal in self.metafile[analysis]['calibration_envelope'].items():
            cals[ifo] = CalibrationUncertaintyEnvelope.from_array(cal)
        return cals


class PSD:

    def __init__(self, data, ifo=None):
        self.data = data
        self.ifo = ifo

    def to_ascii(self, filename):
        np.savetxt(filename, self.data)

    def to_xml(self):
        tmp = "psd.tmp"
        self.to_ascii(tmp)

        executable = "convert_psd_ascii2xml"
        if shutil.which(executable) is not None:

            command = [
                executable,
                "--fname-psd-ascii",
                f"{tmp}",
                "--conventional-postfix",
                "--ifo",
                f"{self.ifo}",
            ]

            pipe = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            out, err = pipe.communicate()

            if err:
                logger.warning(f"An XML format PSD could not be created. {err}")
            os.remove(tmp)

        else:
            logger.warning("An XML format PSD could not be created.")
