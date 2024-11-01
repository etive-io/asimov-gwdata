.. _installation-guide:

Installing asimov-gwdata
========================

There are lots of ways of installing ``asimov-gwdata``, and the best way of getting access to it depends both on your local setup, and on whether you have access to IGWN computing resources.

Installation using ``conda``
----------------------------

``asimov-gwdata`` is packaged and available for use in conda environments via conda-forge.

.. code-block:: console

		$ conda install -c conda-forge asimov-gwdata

Installation using ``pip``
--------------------------

The simplest method for installing ``asimov-gwdata`` is to use the latest released version from ``pypi``, the python package index.
We always recommend installing in a virtual environment.

You can install ``asimov-gwdata`` using ``pip``.

.. code-block:: console
   
		$ pip install asimov-gwdata
		
Installation from source
------------------------

If you want to run unreleased code you can do this by installing directly from the asimov git repository.

The quickest way to do this is to run

.. code-block:: console

		$ pip install git+https://git.ligo.org/asimov/pipelines/datafind.git

You should use the package with care if installing from source; while the master branch should represent stable code, it may contain new or undocumented features, or behave unexpectedly.


Installation for development
----------------------------

If you want to develop code in the ``asimov-gwdata`` repository then it can be helpful to install in development mode.

First clone a copy of the ``asimov-gwdata`` repository, for example by running

.. code-block:: console

		$ git clone https://git.ligo.org/asimov/pipelines/datafind.git asimov-gwdata

Then you can install this repository into your current virtual environment by running

.. code-block:: console

		$ cd asimov-gwdata
		$ pip install -e .
