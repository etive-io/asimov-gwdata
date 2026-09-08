.. _api-reference:

API Reference
=============

This section provides detailed API documentation for the ``asimov-gwdata`` package.

Core Modules
------------

Main Module
~~~~~~~~~~~

.. automodule:: datafind.main
   :members:
   :undoc-members:
   :show-inheritance:

Frames Module
~~~~~~~~~~~~~

The frames module handles retrieval of gravitational wave strain data from GWOSC and private data sources.

.. automodule:: datafind.frames
   :members:
   :undoc-members:
   :show-inheritance:

Calibration Module
~~~~~~~~~~~~~~~~~~

The calibration module provides functionality for retrieving and manipulating calibration uncertainty envelopes.

.. automodule:: datafind.calibration
   :members:
   :undoc-members:
   :show-inheritance:

Metafiles Module
~~~~~~~~~~~~~~~~

The metafiles module provides functionality for working with PESummary metafiles.

.. automodule:: datafind.metafiles
   :members:
   :undoc-members:
   :show-inheritance:

Report Module
~~~~~~~~~~~~~

The report module builds an HTML summary of a download job's assets, including spectrograms of any downloaded frames.

.. automodule:: datafind.report
   :members:
   :undoc-members:
   :show-inheritance:

Plotting Module
~~~~~~~~~~~~~~~

The plotting module provides the spectrogram plotting helper used by the report module.

.. automodule:: datafind.plotting
   :members:
   :undoc-members:
   :show-inheritance:

Asimov Pipeline
~~~~~~~~~~~~~~~

Integration with the asimov pipeline framework.

.. automodule:: datafind.asimov
   :members:
   :undoc-members:
   :show-inheritance:

Utilities
~~~~~~~~~

.. automodule:: datafind.utils
   :members:
   :undoc-members:
   :show-inheritance:
