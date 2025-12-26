.. _examples:

Usage Examples
==============

This page provides comprehensive examples of using ``asimov-gwdata`` for various data retrieval tasks.

Basic Workflow
--------------

The typical workflow for using ``asimov-gwdata`` involves:

1. Creating a YAML configuration file specifying what data to download
2. Running the ``gwdata`` command with your configuration
3. Accessing the downloaded data in the output directories

Example: GW150914 Analysis
--------------------------

This example shows how to retrieve all necessary data for analyzing GW150914, the first gravitational wave detection.

Step 1: Create Configuration File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a file named ``gw150914_config.yaml``:

.. code-block:: yaml

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

Step 2: Download the Data
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ gwdata --settings gw150914_config.yaml

Step 3: Access the Data
~~~~~~~~~~~~~~~~~~~~~~~~

After running the command, you'll find:

- Frame files in the ``frames/`` directory
- Cache files in the ``cache/`` directory
- Calibration files in the ``calibration/`` directory

Working with PESummary Metafiles
---------------------------------

Extracting Posterior Samples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have a PESummary metafile from a previous analysis, you can extract the posterior samples:

.. code-block:: yaml

   data:
     - posterior
   source:
     type: pesummary
     location: /home/pe/O3/GW150914/posterior_samples.h5
     analysis: C01:IMRPhenomXPHM

This will copy the metafile to ``posterior/metafile.h5``.

Extracting PSDs
~~~~~~~~~~~~~~~

To extract power spectral density (PSD) files from a metafile:

.. code-block:: yaml

   data:
     - psds
   source:
     type: pesummary
     location: /home/pe/O3/GW150914/posterior_samples.h5
     analysis: C01:IMRPhenomXPHM

PSD files will be saved in the ``psds/`` directory as both text (``*.dat``) and XML (``*.xml.gz``) formats.

Extracting Calibration from Metafile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Calibration uncertainty envelopes can also be extracted from PESummary metafiles:

.. code-block:: yaml

   data:
     - calibration
   source:
     type: pesummary
     location: /home/pe/O3/GW150914/posterior_samples.h5
     analysis: C01:IMRPhenomXPHM

Advanced Calibration Retrieval
-------------------------------

Retrieving from Local Storage
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For LIGO data (H1, L1), calibration files are typically stored locally. The default behavior is to search local storage:

.. code-block:: yaml

   interferometers:
     - H1
     - L1
   time:
     start: 1126259462
     end: 1126259478
     duration: 32
   data:
     - calibration
   locations:
     calibration directory: /home/cal/archive/
   calibration version: v1

Retrieving from Frame Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For Virgo data (V1) in O4 and later, or when you want to force retrieval from frames:

.. code-block:: yaml

   interferometers:
     - V1
   time:
     start: 1380000000
     end: 1380000016
     duration: 32
   data:
     - calibration
   source:
     type: frame
   virgo prefix: "V1:Hrec_hoft_U00"
   virgo frametype: "V1:HoftAR1"

Using with Asimov
-----------------

``asimov-gwdata`` is designed to work seamlessly with the ``asimov`` workflow management system.

Creating a Blueprint
~~~~~~~~~~~~~~~~~~~~

Create a blueprint file for your analysis:

.. code-block:: yaml

   kind: analysis
   name: get-data
   pipeline: gwdata
   event: GW150914
   download:
     - frames
     - calibration
     - posterior
   source:
     type: pesummary
     location: /home/pe/O3/<event>/posterior_samples.h5
     analysis: C01:IMRPhenomXPHM
   file length: 4096
   locations:
     calibration directory: /home/cal/archive/
   calibration version: v1

Applying the Blueprint
~~~~~~~~~~~~~~~~~~~~~~~

Apply the blueprint to your event in asimov:

.. code-block:: console

   $ olivaw apply get-data GW150914

Multi-Detector Analysis
------------------------

Downloading Data for All Detectors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To download data from multiple detectors:

.. code-block:: yaml

   interferometers:
     - H1
     - L1
     - V1
   time:
     start: 1238166018
     end: 1238170018
     duration: 4096
   data:
     - frames
     - calibration

This will download:
- Strain data from GWOSC for all three detectors
- Calibration files appropriate for each detector and observing run

Reproducing Published Results
------------------------------

Complete Example
~~~~~~~~~~~~~~~~

To reproduce a published analysis, you typically need the posterior samples, PSDs, and calibration files:

.. code-block:: yaml

   data:
     - posterior
     - psds
     - calibration
   source:
     type: pesummary
     location: /home/pe/O3/GW190814/published_results.h5
     analysis: PublishedAnalysis

This single configuration will extract all the necessary data products from the published metafile, making it easy to reproduce or build upon previous work.

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**Missing calibration files**

If calibration files are not found, check:
- The observing run corresponds to the GPS time
- You have access to the calibration directory
- The calibration version is correct for your observing run

**Frame download failures**

If frames fail to download:
- Verify the GPS times are within available data ranges
- Check your network connectivity
- Ensure you have proper authentication for private data

**PESummary metafile errors**

If you encounter errors with metafiles:
- Verify the file path is correct
- Check that the analysis name exists in the metafile
- Ensure the metafile contains the requested data products
