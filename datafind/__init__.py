"""
asimov-gwdata: Gravitational Wave Data Retrieval Pipeline
==========================================================

This package provides an asimov pipeline for collecting gravitational wave data
for use in parameter estimation and other analyses.

Main Components
---------------

main
    Command-line interface and core data retrieval logic
frames
    Strain data retrieval from GWOSC and private sources
calibration
    Calibration uncertainty envelope retrieval and manipulation
metafiles
    PESummary metafile handling and data extraction
asimov
    Integration with the asimov workflow management system
utils
    Utility functions for file downloading and manipulation

Usage
-----

As a command-line tool::

    $ gwdata --settings config.yaml

As an asimov pipeline::

    $ olivaw apply blueprint.yaml event_name

See the documentation for more details on configuration and usage.
"""
pass

