Accessing Calibration Uncertainty Envelopes
===========================================

Text Calibration Uncertainty Envelopes
--------------------------------------

For LIGO strain data from O1, O2, O3, and O4, and Virgo data from O2 and O3 calibration uncertainty information was distributed in ascii text files.
These can be retrieved directly from a file system by asimov-gwdata.

Calibration uncertainty envelopes are proprietary data available to members of the LIGO, Virgo, and KAGRA collaborations.

These can be accessed by setting ``calibration`` as an argument in the ``download`` section of the blueprint.

Additionally you can set the following variables:

``calibration version``
   The version of the calibration.

``locations: calibration directory``
   The location of the calibration files.

.. code-block:: yaml

		kind: analysis
		name: get-data
		pipeline: gwdata
		download:
		  - calibration
		locations:
		  calibration directory: /home/cal/archive/
		calibration version: v1


Calibration Uncertainty Envelopes in Frame files
------------------------------------------------

Starting in O4 the Virgo interferometer's calibration uncertainty envelopes are distributed in frame files alongside the strain.
Asimov will automatically determine the correct frame file to extract these from, download it, and extract the calibration data.

.. code-block:: yaml

		kind: analysis
		name: get-data
		pipeline: gwdata
		download:
		  - calibration


`asimov-gwdata` will then read the frame file and extract the calibration envelope from it saving it in a format compatible with pipelines such as `bilby`.

For L1 and H1 asimov will always attempt to find a calibration file on a local filesystem (and this is intended for use only on internal IGWN resources).
It is, however, possible to override this behaviour by specifying the source type.

For example, to force retrieval from a frame:

.. code-block:: yaml

		kind: analysis
		name: get-data
		pipeline: gwdata
		source:
		  type: frame
		download:
		  - calibration

Or to force local storage to be used:

.. code-block:: yaml

		kind: analysis
		name: get-data
		pipeline: gwdata
		source:
		  type: local storage
		download:
		  - calibration

Calibration Uncertainty from PESummary Metafiles
================================================

It is also possible to use a PESummary metafile as the source of a calibration file, making reproducing a previous analysis more straightforward.

In order to do this the source type should be specified as "pesummary".
You will also need to specify the path to the metafile.

.. code-block:: yaml

		kind: analysis
		name: get-data
		pipeline: gwdata
		source:
		  type: pesummary
		  location: /home/pe.o4/O4a/<event>/results/posterior_samples.h5
		download:
		  - calibration
