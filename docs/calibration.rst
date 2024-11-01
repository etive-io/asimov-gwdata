Accessing Calibration Uncertainty Envelopes
===========================================

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
