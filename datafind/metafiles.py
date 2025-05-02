"""
Functions to manipulate PESummary metafiles.
"""

import h5py
import contextlib
import subprocess
import os
import numpy as np

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


class PSD:

    def __init__(self, data, ifo=None):
        self.data = data
        self.ifo = ifo

    def to_ascii(self, filename):
        np.savetxt(filename, self.data)

    def to_xml(self):
        tmp = "psd.tmp"
        self.to_ascii(tmp)

        command = [
            "convert_psd_ascii2xml",
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
            if hasattr(self.production.event, "issue_object"):
                raise Exception(
                    f"An XML format PSD could not be created.\n{command}\n{out}\n\n{err}",
                )
            else:
                raise Exception(
                    f"An XML format PSD could not be created.\n{command}\n{out}\n\n{err} ",
                )
        os.remove(tmp)
