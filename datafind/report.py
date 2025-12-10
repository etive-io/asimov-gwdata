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

from .frames import Frame

import otter
import otter.bootstrap as bt

class Report:
    """
    A class to help produce an HTML report for asimov-gwdata.
    """

    def __init__(self, 
                 production: analysis_type = None, 
                 settings: dict = None,
                 webdir: str = "report"):
        """
        Create a report for a GWData analysis.

        Parameters
        ----------
        production : asimov.Production, optional
            The production object representing the analysis.
            
        settings : dict, optional
            The settings dictionary for the analysis.

        webdir : str
            The directory where the report HTML and assets will be saved.

        Returns
        -------
        None
        """
        self.production = production
        self.settings = settings
        self.webdir = webdir
        self.report = otter.Otter(os.path.join(webdir, "index.html"), 
                             author="Asimov-gwdata", 
                             title="Data Report")
        
        if self.production is not None:
            self.products = self.production.collect_assets()
        else:
            self.products = {}

        if "frames" in self.products:
            self._add_spectrograms()

    @property
    def frames(self):
        """
        Return the list of frames in the report.
        """
        return self.products.get("frames", [])
    
    @frames.setter
    def frames(self, value):    
        """
        Set the frame list for this report.

        Parameters
        ----------
        value : dict
            A dictionary of frames to include in the report.
            The key for each frame should be the name of the interferometer,
            and the value should be the path to the frame file, or a list of paths.
        """
        assert(isinstance(value, dict)), "Frames must be provided as a dict."
        self.products["frames"] = value

    def _add_spectrograms(self, channel=None):
        """Add spectrograms to the report."""
        for ifo, frames in self.products.get("frames").items():
            # channel = self.production.meta.get("data", {}).get("channel", "None")

            row = bt.Row(1)

            with self.report:
                self.report + f"## Spectrograms for {ifo}"

            for fr in frames:
                frame = Frame(os.path.join("frames", fr))

                if self.production is not None:
                    time = self.production.meta.get("event time", None)
                else:
                    time = self.settings.get("time", {}).get("end", None) - 2
                    
                spec_f = frame.spectrogram(time=time, channel=channel)

                with self.report:
                    self.report + spec_f