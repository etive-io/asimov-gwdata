Accessing strain data
=====================

``asimov-gwdata`` is capable of retrieving gravitational wave strain data from the Gravitational wave open science centre.

We can do this using the ``download`` section of the blueprint, and setting the ``frames`` argument.
We also need to set the ``file length``, which can be either ``32`` or ``4096`` for a 32-second or 4096-second frame.

.. code-block:: yaml

    kind: analysis
    name: get-data
    pipeline: gwdata
    file length: 4096
    download:
      - frames	


