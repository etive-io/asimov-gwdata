.. _contributing:

Contributing to asimov-gwdata
==============================

We welcome contributions to ``asimov-gwdata``! This guide will help you get started.

Getting Started
---------------

Development Setup
~~~~~~~~~~~~~~~~~

1. Fork the repository on GitHub or git.ligo.org
2. Clone your fork locally:

   .. code-block:: console

      $ git clone https://github.com/yourusername/asimov-gwdata.git
      $ cd asimov-gwdata

3. Install the package in development mode:

   .. code-block:: console

      $ pip install -e .

4. Install the documentation dependencies:

   .. code-block:: console

      $ pip install -r docs-requirements.txt

Making Changes
--------------

Code Style
~~~~~~~~~~

* Follow PEP 8 style guidelines for Python code
* Use meaningful variable and function names
* Add docstrings to all public functions and classes
* Use Google or NumPy style docstrings

Testing
~~~~~~~

Before submitting changes:

1. Test your changes manually
2. Ensure existing functionality still works
3. Update tests if you add new features

Documentation
~~~~~~~~~~~~~

When adding new features:

1. Add docstrings to new functions and classes
2. Update relevant documentation pages in ``docs/``
3. Add usage examples where appropriate
4. Build the documentation locally to verify:

   .. code-block:: console

      $ cd docs
      $ make html

Submitting Changes
------------------

Pull Request Process
~~~~~~~~~~~~~~~~~~~~

1. Create a new branch for your changes:

   .. code-block:: console

      $ git checkout -b feature/your-feature-name

2. Make your changes and commit them:

   .. code-block:: console

      $ git add .
      $ git commit -m "Add feature: description"

3. Push to your fork:

   .. code-block:: console

      $ git push origin feature/your-feature-name

4. Create a pull request on GitHub

Pull Request Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~

* Provide a clear description of the changes
* Reference any related issues
* Ensure all documentation is updated
* Be responsive to feedback during review

Types of Contributions
----------------------

Bug Reports
~~~~~~~~~~~

When reporting bugs, please include:

* Your operating system and Python version
* Steps to reproduce the issue
* Expected behavior vs. actual behavior
* Any error messages or stack traces

Feature Requests
~~~~~~~~~~~~~~~~

We're always interested in new ideas! When suggesting features:

* Explain the use case clearly
* Describe how it would benefit users
* Consider backward compatibility

Documentation Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~

Documentation improvements are always welcome:

* Fix typos or unclear explanations
* Add more examples
* Improve API documentation
* Add tutorials for common tasks

Code Contributions
~~~~~~~~~~~~~~~~~~

Ideas for contributions:

* Add support for new data sources
* Improve error handling and messages
* Optimize performance
* Add new configuration options
* Extend calibration support

Code Review Process
-------------------

All submissions require review. We use GitHub pull requests for this purpose.

* Reviews typically happen within a few days
* Be patient and responsive to feedback
* All discussions should be constructive and respectful
* Maintainers have the final say on what gets merged

Community Guidelines
--------------------

* Be respectful and inclusive
* Welcome newcomers
* Provide constructive feedback
* Focus on the code, not the person
* Assume good faith

Getting Help
------------

If you need help:

* Open an issue on GitHub
* Ask questions in pull request comments
* Check existing documentation and issues

Thank you for contributing to asimov-gwdata!
