Accessing posterior samples
===========================

Posterior samples from parameter estimation can be read from PESummary metafiles.

.. code-block:: yaml

		kind: analysis
		name: get-data
		pipeline: gwdata
		download:
		  - posterior
		source:
		  type: pesummary
		  location: /home/pe.o4/O4a/<event>/<illustrative_result>/summary/samples/posterior_samples.h5

Accessing published power spectral densities (PSDs)
===================================================

PSD files from parameter estimation can be read from PESummary metafiles.

.. code-block:: yaml

		kind: analysis
		name: get-data
		pipeline: gwdata
		download:
		  - psds
		source:
		  type: pesummary
		  location: /home/pe.o4/O4a/<event>/<illustrative_result>/summary/samples/posterior_samples.h5
