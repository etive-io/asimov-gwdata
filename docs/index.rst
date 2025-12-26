Accessing gravitational wave data with asimov
=============================================

``asimov-gwdata`` is a pipeline designed to work with the ``asimov`` package to collect gravitational wave data for use in parameter estimation and other analyses.

It simplifies the process of finding and collecting various data products which might be used across a variety of analysis tasks, including:

* **Strain data (frames)**: Gravitational wave strain data from GWOSC and private sources
* **Calibration envelopes**: Calibration uncertainty information for LIGO, Virgo, and KAGRA detectors
* **Posterior samples**: Parameter estimation results from PESummary metafiles
* **PSDs**: Power spectral densities from previous analyses

While designed to work as part of a larger ``asimov`` workflow, ``asimov-gwdata`` can also be used as a standalone command-line tool for downloading gravitational wave data.

Getting Started
---------------

New to asimov-gwdata? Start here:

* :doc:`installation` - Installation instructions
* :ref:`functionality-overview` - Complete feature overview
* :ref:`examples` - Usage examples and tutorials
* :ref:`cli-reference` - Command-line interface reference

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   :hidden:

   installation
   examples
   cli
   configuration
   functionality

.. toctree::
   :maxdepth: 2
   :caption: Data Types
   :hidden:

   frames
   calibration
   pesummary

.. toctree::
   :maxdepth: 2
   :caption: API Documentation
   :hidden:

   api

.. toctree::
   :maxdepth: 1
   :caption: Development
   :hidden:

   contributing

Features
--------

**Multiple Data Sources**
  Download data from GWOSC, private LIGO/Virgo/KAGRA data archives, and PESummary metafiles.

**Flexible Configuration**
  Simple YAML configuration files specify exactly what data you need.

**Asimov Integration**
  Seamlessly integrates with the asimov workflow management system for complex analysis pipelines.

**Comprehensive Data Types**
  Supports strain data, calibration uncertainty envelopes, posterior samples, and PSDs.

**Multi-Version Support**
  Works across different observing runs (O1, O2, O3, O4) with appropriate calibration handling.

**Command-Line Interface**
  Easy-to-use CLI for quick data retrieval tasks.

Quick Example
-------------

Download gravitational wave strain data for GW150914:

.. code-block:: yaml

   # config.yaml
   interferometers:
     - H1
     - L1
   time:
     start: 1126259462
     end: 1126259478
     duration: 4096
   data:
     - frames
     - calibration

.. code-block:: console

   $ gwdata --settings config.yaml

Contributing
------------

``asimov-gwdata`` is open source software. Contributions are welcome!

Project Information
-------------------

* **License**: MIT
* **Repository**: https://git.ligo.org/asimov/pipelines/datafind

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
