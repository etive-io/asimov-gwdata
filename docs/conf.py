# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'asimov-gwdata'
copyright = '2024, Daniel Williams'
author = 'Daniel Williams'

# Try to get version dynamically
try:
    from importlib.metadata import version as get_version
    release = get_version('asimov-gwdata')
except Exception:
    release = '0.4.1'

version = '.'.join(release.split('.')[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.coverage',
    'sphinx_click',
    'sphinx_multiversion',
]

# Autodoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

autodoc_mock_imports = ['htcondor']

autosummary_generate = True

# Napoleon settings for parsing Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_type_aliases = None

# Intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'asimov': ('https://asimov.docs.ligo.org/', None),
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The master toctree document.
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'kentigern'
html_static_path = ['_static']

# Add custom CSS
html_css_files = [
    'custom.css',
]

# sphinx-multiversion configuration
smv_tag_whitelist = r'^v\d+\.\d+.*$'  # Include tags like v1.0, v1.0.1, etc.
smv_branch_whitelist = r'^(main|master)$'  # Include main/master branches
smv_remote_whitelist = r'^origin$'  # Use origin remote
smv_released_pattern = r'^refs/tags/v\d+\.\d+.*$'  # Released versions (matches tag whitelist)
smv_outputdir_format = '{ref.name}'  # Output directory format

html_sidebars = {
    '**': [
        'versioning.html',
    ],
}
