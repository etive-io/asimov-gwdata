"""
The ledger vocabulary for the gwdata pipeline.

asimov (>= 0.8) loads this through the ``asimov.vocabulary`` entry point,
so that ``asimov vocabulary check`` recognises the keys gwdata reads.
"""

import importlib.resources


def vocabulary():
    """Return the path to gwdata's vocabulary file."""
    return importlib.resources.files("datafind").joinpath("vocabulary.yaml")
