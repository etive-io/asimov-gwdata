.. _cli-reference:

Command Line Interface
======================

``asimov-gwdata`` provides a command-line interface for downloading gravitational wave data.

gwdata Command
--------------

The main command-line tool for downloading gravitational wave data.

.. click:: datafind.main:get_data
   :prog: gwdata
   :nested: full

asimov gw Commands
-------------------

``asimov-gwdata`` also registers a ``gw`` command group with asimov itself
(via the ``asimov.commands`` plugin hook), providing higher-level project
setup and event/analysis discovery on top of the `asimov/data
<https://git.ligo.org/asimov/data>`_ blueprint repository. This repository
is cloned to ``~/.asimov/gwdata/asimov-data`` on first use; set
``ASIMOV_DATA_PATH`` to point at a different checkout instead.

.. click:: datafind.cli:gw
   :prog: asimov gw
   :nested: full

Usage Examples
--------------

Basic Usage
~~~~~~~~~~~

To download data using a configuration file:

.. code-block:: console

   $ gwdata --settings config.yaml

Example Configuration Files
---------------------------

Downloading Frames
~~~~~~~~~~~~~~~~~~

Example configuration for downloading gravitational wave strain data:

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

Downloading Posterior Samples
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Example configuration for extracting posterior samples from a PESummary metafile:

.. code-block:: yaml

   data:
     - posterior
   source:
     type: pesummary
     location: /path/to/posterior_samples.h5
     analysis: C01:IMRPhenomXPHM

Downloading PSDs
~~~~~~~~~~~~~~~~

Example configuration for extracting PSDs from a PESummary metafile:

.. code-block:: yaml

   data:
     - psds
   source:
     type: pesummary
     location: /path/to/posterior_samples.h5
     analysis: C01:IMRPhenomXPHM

Downloading Calibration
~~~~~~~~~~~~~~~~~~~~~~~

Example configuration for downloading calibration uncertainty envelopes:

.. code-block:: yaml

   interferometers:
     - H1
     - L1
     - V1
   time:
     start: 1126259462
     end: 1126259478
     duration: 32
   data:
     - calibration
   locations:
     calibration directory: /home/cal/archive/
   calibration version: v1

Combined Download
~~~~~~~~~~~~~~~~~

You can download multiple data types in a single configuration:

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
     - psds
   source:
     type: pesummary
     location: /path/to/posterior_samples.h5
     analysis: C01:IMRPhenomXPHM
   locations:
     calibration directory: /home/cal/archive/
   calibration version: v1
