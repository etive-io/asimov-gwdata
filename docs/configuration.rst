.. _configuration:

Configuration Reference
=======================

This page provides a complete reference for all configuration options available in ``asimov-gwdata``.

Configuration File Format
-------------------------

Configuration files for ``asimov-gwdata`` are written in YAML format. The general structure is:

.. code-block:: yaml

   interferometers: [list of detectors]
   time:
     start: GPS_START_TIME
     end: GPS_END_TIME
     duration: FRAME_DURATION
   data: [list of data types]
   source:
     type: SOURCE_TYPE
     location: PATH_OR_URL
     analysis: ANALYSIS_NAME
   locations:
     calibration directory: PATH
   calibration version: VERSION

Core Configuration Options
--------------------------

interferometers
~~~~~~~~~~~~~~~

:Type: List of strings
:Required: For frames and some calibration sources
:Description: List of detector names to download data for
:Valid values: ``H1``, ``L1``, ``V1``, ``K1`` (Note: K1/KAGRA calibration support is pending)
:Example:

.. code-block:: yaml

   interferometers:
     - H1
     - L1
     - V1

time
~~~~

Configuration for GPS time ranges and frame durations.

time.start
^^^^^^^^^^

:Type: Integer (GPS time)
:Required: For frames and calibration
:Description: Start GPS time for data retrieval
:Example:

.. code-block:: yaml

   time:
     start: 1126259462

time.end
^^^^^^^^

:Type: Integer (GPS time)
:Required: For frames
:Description: End GPS time for data retrieval
:Example:

.. code-block:: yaml

   time:
     end: 1126259478

time.duration
^^^^^^^^^^^^^

:Type: Integer
:Required: For frames
:Description: Duration of frame files in seconds
:Valid values: ``32`` or ``4096``
:Example:

.. code-block:: yaml

   time:
     duration: 4096

data
~~~~

:Type: List of strings
:Required: Yes
:Description: List of data types to download
:Valid values: ``frames``, ``calibration``, ``posterior``, ``psds``
:Example:

.. code-block:: yaml

   data:
     - frames
     - calibration
     - posterior
     - psds

Data Source Configuration
-------------------------

source
~~~~~~

Configuration for data sources, particularly for PESummary metafiles.

source.type
^^^^^^^^^^^

:Type: String
:Required: For posterior, psds, and some calibration sources
:Description: Type of data source
:Valid values: ``pesummary``, ``frame``, ``local storage``, ``public``
:Example:

.. code-block:: yaml

   source:
     type: pesummary

.. code-block:: yaml

   source:
     type: public

source.location
^^^^^^^^^^^^^^^

:Type: String (file path)
:Required: When source.type is specified
:Description: Path to the source file (supports glob patterns)
:Example:

.. code-block:: yaml

   source:
     location: /home/pe/O3/<event>/posterior_samples.h5

source.analysis
^^^^^^^^^^^^^^^

:Type: String
:Required: For PESummary sources when multiple analyses exist
:Description: Name of the analysis within the PESummary metafile
:Example:

.. code-block:: yaml

   source:
     analysis: C01:IMRPhenomXPHM

Calibration Configuration
-------------------------

locations
~~~~~~~~~

Configuration for file system locations.

locations.calibration directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Type: String (directory path)
:Required: For local storage calibration retrieval
:Description: Base directory for calibration files
:Default: ``/home/cal/public_html/archive`` (on LIGO clusters)
:Example:

.. code-block:: yaml

   locations:
     calibration directory: /home/cal/archive/

locations.datafind server
^^^^^^^^^^^^^^^^^^^^^^^^^

:Type: String (hostname)
:Required: No
:Description: Datafind server for frame file lookups
:Default: ``datafind.igwn.org``
:Example:

.. code-block:: yaml

   locations:
     datafind server: datafind.igwn.org

calibration version
~~~~~~~~~~~~~~~~~~~

:Type: String or Dictionary
:Required: For local storage calibration (LIGO detectors)
:Description: Version identifier for calibration files. Can be a string (applies to all detectors) or a dictionary (per-detector versions)
:Example (single version):

.. code-block:: yaml

   calibration version: v1

:Example (per-detector versions):

.. code-block:: yaml

   calibration version:
     H1: v2
     L1: v1

Virgo Calibration Options
~~~~~~~~~~~~~~~~~~~~~~~~~~

These options are specific to retrieving Virgo calibration from frame files.

virgo prefix
^^^^^^^^^^^^

:Type: String
:Required: No
:Description: Channel prefix for Virgo calibration data
:Default: ``V1:Hrec_hoft_U00``
:Example:

.. code-block:: yaml

   virgo prefix: "V1:Hrec_hoft_U00"

virgo timestamp channel
^^^^^^^^^^^^^^^^^^^^^^^

:Type: String
:Required: No
:Description: Channel containing timestamp for calibration envelope lookup
:Default: ``{virgo prefix}_lastWriteGPS``
:Example:

.. code-block:: yaml

   virgo timestamp channel: "V1:Hrec_hoft_U00_lastWriteGPS"

virgo frametype
^^^^^^^^^^^^^^^

:Type: String
:Required: No
:Description: Frame type to use for Virgo calibration retrieval
:Default: ``V1:HoftAR1``
:Example:

.. code-block:: yaml

   virgo frametype: "V1:HoftAR1"

Asimov Blueprint Configuration
------------------------------

When used within asimov, additional fields are available:

kind
~~~~

:Type: String
:Required: Yes (in asimov)
:Description: Type of asimov object
:Value: ``analysis``

name
~~~~

:Type: String
:Required: Yes (in asimov)
:Description: Name of the analysis

pipeline
~~~~~~~~

:Type: String
:Required: Yes (in asimov)
:Description: Pipeline identifier
:Value: ``gwdata``

event
~~~~~

:Type: String
:Required: Yes (in asimov)
:Description: Event name (can use ``<event>`` placeholder)

file length
~~~~~~~~~~~

:Type: Integer
:Required: For frame downloads in asimov
:Description: Frame file duration
:Valid values: ``32`` or ``4096``

download
~~~~~~~~

:Type: List of strings
:Required: Yes (in asimov)
:Description: Equivalent to ``data`` in standalone configuration

Complete Configuration Examples
--------------------------------

Minimal Configuration
~~~~~~~~~~~~~~~~~~~~~

This minimal example extracts posterior samples from a PESummary metafile.

.. code-block:: yaml

   data:
     - posterior
   source:
     type: pesummary
     location: /path/to/file.h5
     analysis: Analysis1

Full Configuration
~~~~~~~~~~~~~~~~~~

This comprehensive example downloads all available data types (frames, calibration, posteriors, and PSDs) 
from both GWOSC and PESummary sources, with per-detector calibration versions and custom Virgo settings.

.. code-block:: yaml

   interferometers:
     - H1
     - L1
     - V1
   time:
     start: 1126259462
     end: 1126259478
     duration: 4096
   data:
     - frames
     - calibration
     - posterior
     - psds
   source:
     type: pesummary
     location: /home/pe/O3/<event>/results/posterior_samples.h5
     analysis: C01:IMRPhenomXPHM
   locations:
     calibration directory: /home/cal/archive/
     datafind server: datafind.igwn.org
   calibration version:
     H1: v2
     L1: v1
   virgo prefix: "V1:Hrec_hoft_U00"
   virgo frametype: "V1:HoftAR1"

Asimov Blueprint Example
~~~~~~~~~~~~~~~~~~~~~~~~~

This example shows how to configure gwdata as an asimov pipeline with automatic event substitution.

.. code-block:: yaml

   kind: analysis
   name: get-data
   pipeline: gwdata
   event: GW150914
   file length: 4096
   download:
     - frames
     - calibration
     - posterior
     - psds
   source:
     type: pesummary
     location: /home/pe/O3/<event>/results/posterior_samples.h5
     analysis: C01:IMRPhenomXPHM
   locations:
     calibration directory: /home/cal/archive/
   calibration version: v1
