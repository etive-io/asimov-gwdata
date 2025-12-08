"""
Tools to help asimov-gwdata produce an html report.
"""
import os

try:
    from asimov.event import Production
    analysis_type = Production
except ImportError:
    from asimov.analysis import Analysis
    analysis_type = Analysis

import otter
import otter.bootstrap as bt

from .plotting import plot_spectrogram

class Report:
    """
    A class to help produce an HTML report for asimov-gwdata.
    """

    def __init__(self, 
                 production: analysis_type, 
                 webdir: str):
        """
        Create a report for a GWData analysis.

        Parameters
        ----------
        production : asimov.Production
            The production object representing the analysis.
        webdir : str
            The directory where the report HTML and assets will be saved.

        Returns
        -------
        None
        """
        self.production = production
        self.webdir = webdir
        self.report = otter.Otter(os.path.join(webdir, "index.html"), 
                             author="Asimov-gwdata", 
                             title="Data Report")
        
        self.products = self.production.collect_assets()

        if "frames" in self.products:
            self._add_spectrograms()


    def _add_spectrograms(self):
        """Add spectrograms to the report."""
        for frame in self.products.get("frames"):
            channel = self.production.meta.get("data", {}).get("channel", "None")
            time = self.production.meta.get("event time", None)
            spec_f = plot_spectrogram(frame, channel, time)

            with self.report as report:
                report + spec_f
