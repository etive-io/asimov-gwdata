.. _functionality-overview:

Functionality Overview
======================

This page provides a comprehensive overview of all the capabilities of ``asimov-gwdata``.

Data Types Supported
--------------------

Strain Data (Frames)
~~~~~~~~~~~~~~~~~~~~

**Download gravitational wave strain data from GWOSC**

* 32-second and 4096-second frame files
* Multiple detectors: H1, L1, V1
* Automatic cache file generation
* Support for all observing runs (O1-O4)

**Private Data Access**

* Access to proprietary LIGO/Virgo/KAGRA data
* OSDF/Pelican protocol support
* Authentication via IGWN tokens
* Datafind server integration

See: :ref:`frames` for detailed documentation.

Calibration Uncertainty Envelopes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Multiple Calibration Sources**

* Local filesystem (LIGO detectors O2-O4)
* Frame files (Virgo O4+)
* PESummary metafiles
* Automatic observing run detection

**Supported Formats**

* ASCII text files (LIGO format)
* Frame-embedded calibration (Virgo)
* Bilby-compatible output format
* Per-detector version control

**Observing Runs**

* O2: LIGO (H1, L1) and Virgo (V1)
* O3a/O3b: LIGO and Virgo
* O4a/O4b/O4c: LIGO and Virgo (frame-based)

See: :ref:`calibration` for detailed documentation.

Posterior Samples
~~~~~~~~~~~~~~~~~

**PESummary Integration**

* Extract posterior samples from metafiles
* Support for multiple analyses per file
* Preserves original metafile format
* Automatic analysis selection

**Use Cases**

* Reproducing published results
* Building on previous analyses
* Comparing different waveform models
* Ensemble studies

See: :ref:`pesummary` for detailed documentation.

Power Spectral Densities (PSDs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**PSD Extraction**

* From PESummary metafiles
* Multiple output formats (ASCII, XML)
* Per-detector PSD files
* Compatible with inference codes

**Output Formats**

* Tab-delimited ASCII (``.dat``)
* XML format (``.xml.gz``)
* Bilby-compatible
* LALInference-compatible

See: :ref:`pesummary` for detailed documentation.

Configuration Options
---------------------

Flexible YAML Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Data Selection**

* Specify multiple data types in a single config
* Mix and match data sources
* Filter by detector, time range, analysis

**Time Configuration**

* GPS time ranges
* Frame durations (32s or 4096s)
* Automatic time validation

**Source Configuration**

* PESummary metafiles
* Local file systems
* Frame files
* GWOSC public data

See: :ref:`configuration` for complete reference.

Integration Capabilities
-------------------------

Asimov Workflow System
~~~~~~~~~~~~~~~~~~~~~~~

**Blueprint-Based Configuration**

* Seamless integration with asimov
* Event-based data retrieval
* Conditional logic support
* Placeholder substitution

**Workflow Features**

* Automatic job submission
* HTCondor integration
* Progress tracking
* Asset collection

**Example Use Cases**

* Parameter estimation pipelines
* Data quality studies
* Multi-event analyses
* Systematic studies

Command-Line Interface
~~~~~~~~~~~~~~~~~~~~~~

**Standalone Operation**

* Direct YAML configuration
* No asimov required
* Quick data retrieval
* Scripting support

**Example Commands**

.. code-block:: console

   # Download frames for GW150914
   $ gwdata --settings gw150914.yaml
   
   # Extract posterior from metafile
   $ gwdata --settings extract_posterior.yaml

See: :ref:`cli-reference` for detailed CLI documentation.

Advanced Features
-----------------

Multi-Version Support
~~~~~~~~~~~~~~~~~~~~~

* Version-specific calibration handling
* Per-detector version specification
* Backward compatibility
* Automatic version detection

Observing Run Detection
~~~~~~~~~~~~~~~~~~~~~~~

* Automatic run identification from GPS time
* Run-specific calibration retrieval
* Cross-run compatibility
* Future-proof design for new runs

Error Handling
~~~~~~~~~~~~~~

* Graceful failure modes
* Informative error messages
* Missing data detection
* Validation checks

Authentication
~~~~~~~~~~~~~~

* IGWN token support
* SciTokens integration
* Automatic credential handling
* Secure data access

Output Organization
-------------------

Directory Structure
~~~~~~~~~~~~~~~~~~~

The tool creates organized output directories:

.. code-block:: text

   output/
   ├── frames/          # Strain data files
   ├── cache/           # Frame cache files
   ├── calibration/     # Calibration envelopes
   ├── posterior/       # Posterior samples
   └── psds/            # Power spectral densities

File Naming Conventions
~~~~~~~~~~~~~~~~~~~~~~~

* Detector-specific filenames (e.g., ``H1.dat``)
* Standard extensions (``.gwf``, ``.dat``, ``.h5``)
* Cache format compatible with LAL
* Human-readable organization

Use Case Examples
-----------------

Reproducing Published Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Download posterior from official data release
2. Extract PSDs and calibration from metafile
3. Use data to reproduce published plots
4. Compare with independent analyses

Parameter Estimation Pipeline
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Download strain data for event
2. Retrieve appropriate calibration
3. Configure inference code
4. Run parameter estimation
5. Compare with published results

Open Data Tutorial
~~~~~~~~~~~~~~~~~~

1. Download public GWOSC data
2. Get calibration for observing run
3. Demonstrate analysis techniques
4. Educational/outreach purposes

Multi-Event Study
~~~~~~~~~~~~~~~~~

1. Batch download data for multiple events
2. Standardized calibration retrieval
3. Consistent data format
4. Population analysis ready

Data Quality Investigation
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Download strain data
2. Compare multiple analyses
3. Investigate systematic effects
4. Validate calibration

Supported Detectors
-------------------

LIGO Detectors
~~~~~~~~~~~~~~

* **H1** (LIGO Hanford)
* **L1** (LIGO Livingston)

**Data Access:** GWOSC (public), IGWN (private)

**Calibration:** Local filesystem (O2-O4)

Virgo Detector
~~~~~~~~~~~~~~

* **V1** (Virgo)

**Data Access:** GWOSC (public), IGWN (private)

**Calibration:** 
  - O2-O3: Local filesystem
  - O4+: Frame files

KAGRA Detector
~~~~~~~~~~~~~~

* **K1** (KAGRA)

**Data Access:** GWOSC (public), IGWN (private)

**Calibration:** TBD based on collaboration distribution

Observing Runs
--------------

Supported Runs
~~~~~~~~~~~~~~

* **O1** (2015-2016): Frames only, no calibration
* **O2** (2016-2017): Full support
* **O3a** (2019): Full support
* **O3b** (2019-2020): Full support
* **O4a** (2023-2024): Full support
* **O4b** (2024-2025): Full support
* **O4c** (2025): Full support

Limitations and Known Issues
-----------------------------

Current Limitations
~~~~~~~~~~~~~~~~~~~

* O1 calibration not available
* KAGRA calibration pending
* Requires IGWN credentials for private data
* Network connectivity required for downloads

Known Issues
~~~~~~~~~~~~

* HTCondor dependency for asimov integration
* Network timeouts for large frame downloads
* Version detection edge cases at run boundaries

Performance Considerations
--------------------------

Download Speed
~~~~~~~~~~~~~~

* Depends on network bandwidth
* OSDF/Pelican optimized for large files
* Parallel downloads not currently supported

Storage Requirements
~~~~~~~~~~~~~~~~~~~~

* 4096s frames: ~100MB per detector per file
* 32s frames: ~1MB per detector per file
* Calibration files: <1MB per detector
* PSDs: <1MB per detector

Future Enhancements
-------------------

Planned Features
~~~~~~~~~~~~~~~~

* Parallel frame downloads
* More data validation checks
* Additional output formats
* Enhanced error recovery
* Automated data quality checks

Community Contributions
~~~~~~~~~~~~~~~~~~~~~~~

We welcome contributions! See :ref:`contributing` for guidelines.

Getting Help
------------

* 📖 Read the :ref:`examples`
* 🔧 Check the :ref:`configuration` reference
* 💻 Review the :ref:`api-reference`
* 🐛 Report issues on GitHub
* 💬 Ask questions in discussions

Summary
-------

``asimov-gwdata`` is a comprehensive tool for gravitational wave data retrieval that:

✅ Supports multiple data types (frames, calibration, posteriors, PSDs)

✅ Integrates with asimov workflow system

✅ Works standalone via command-line

✅ Handles authentication automatically

✅ Supports all major observing runs

✅ Provides flexible configuration

✅ Organizes output systematically

✅ Enables reproducible science
