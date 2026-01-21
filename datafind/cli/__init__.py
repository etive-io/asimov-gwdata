"""
CLI commands for asimov-gwdata plugin.

This module provides GW-specific convenience commands for asimov,
including event discovery, analysis templates, and quick project setup.
"""

import click

from .events import events
from .analyses import analyses
from .setup import setup, quickstart


@click.group(name="gw")
def gw():
    """
    Gravitational wave data and analysis commands.

    This command group provides GW-specific utilities for working with
    asimov projects, including:

    - Discovering and browsing GWTC events
    - Listing available analysis templates
    - Quick project setup with sensible defaults
    - Adding events and analyses to existing projects
    """
    pass


# Register subcommands
gw.add_command(events)
gw.add_command(analyses)
gw.add_command(setup)
gw.add_command(quickstart)


__all__ = ["gw"]
