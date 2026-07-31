Accessing Calibration Uncertainty Envelopes
===========================================

Text Calibration Uncertainty Envelopes
--------------------------------------

For LIGO strain data from O1, O2, O3, and O4, and Virgo data from O2 and O3 calibration uncertainty information was distributed in ascii text files.
These can be retrieved directly from a file system by asimov-gwdata.

Calibration uncertainty envelopes are proprietary data available to members of the LIGO, Virgo, and KAGRA collaborations.

These can be accessed by setting ``calibration`` as an argument in the ``download`` section of the blueprint.

Additionally you can set the following variables:

``interferometers``
   The interferometers to retrieve calibration for. If this is omitted ``asimov-gwdata``
   defaults to trying both ``H1`` and ``L1``. Only the interferometers listed here are
   ever fetched (or written out), so an analysis which only asks for ``H1`` will never
   touch (or overwrite) any ``L1`` calibration another analysis may have produced.

``calibration version``
   The version of the calibration. This can either be a single value, applied to every
   requested LIGO interferometer, or a mapping from interferometer to version, e.g.

   .. code-block:: yaml

		calibration version:
		  H1: v2
		  L1: v1

   This allows different interferometers to use different versions within a single
   analysis -- see the example below.

``locations: calibration directory``
   The location of the calibration files.

.. code-block:: yaml

		kind: analysis
		name: get-data
		pipeline: gwdata
		interferometers:
		  - H1
		  - L1
		download:
		  - calibration
		locations:
		  calibration directory: /home/cal/archive/
		calibration version: v1

A single analysis can request different calibration versions for different
interferometers, without needing to be split into one analysis per interferometer:

.. code-block:: yaml

		kind: analysis
		name: get-data
		pipeline: gwdata
		interferometers:
		  - H1
		  - L1
		download:
		  - calibration
		locations:
		  calibration directory: /home/cal/archive/
		calibration version:
		  H1: v2
		  L1: v1


Calibration Uncertainty Envelopes in Frame files
------------------------------------------------

Starting in O4b the Virgo interferometer's calibration uncertainty envelopes are distributed in frame files alongside the strain, rather than as local text files.
If ``V1`` is included in ``interferometers``, ``asimov-gwdata`` will automatically determine the correct frame file to extract these from, download it, and extract the calibration data -- in the same analysis as any H1/L1 calibration requested alongside it, so a separate analysis is no longer needed just to pick up the Virgo envelope:

.. code-block:: yaml

		kind: analysis
		name: get-data
		pipeline: gwdata
		interferometers:
		  - H1
		  - L1
		  - V1
		download:
		  - calibration
		calibration version:
		  H1: v2
		  L1: v1

This retrieves H1 ``v2`` and L1 ``v1`` calibration from the local archive, and V1
calibration from a frame file, all within a single analysis. For O1/O2/O3 events, where
Virgo calibration *is* distributed as a local text file, ``V1`` is instead retrieved
from local storage alongside H1/L1, and the frame-based lookup is only used as a
fallback when local storage doesn't have it (i.e. for O4b onwards).

``asimov-gwdata`` will then read the frame file and extract the calibration envelope from it, saving it in a format compatible with pipelines such as `bilby`.

You can optionally set the following variables to control how the Virgo frame is located:

``virgo prefix``
   The channel prefix used to identify the calibration uncertainty channels in the frame.
   Defaults to ``V1:Hrec_hoft_U00``.

``virgo frametype``
   The frame type to search for. Defaults to ``V1:HoftAR1``.

``virgo timestamp channel``
   The channel used to identify the nearest calibration envelope for a given time.
   Defaults to ``{virgo prefix}_lastWriteGPS``.

It is also possible to force a single retrieval mechanism for the whole analysis by
specifying the source type explicitly. This is mostly useful for existing blueprints
which already split calibration retrieval across dedicated analyses.

To force retrieval from a frame only (no H1/L1 lookup at all):

.. code-block:: yaml

		kind: analysis
		name: get-data
		pipeline: gwdata
		source:
		  type: frame
		download:
		  - calibration

Or to force local storage only, which -- unlike the default behaviour above -- will
never fall back to a frame-based lookup for Virgo, even if ``V1`` is listed in
``interferometers`` and isn't found in the local archive:

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
