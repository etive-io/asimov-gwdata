# Building the Documentation

This directory contains the documentation for `asimov-gwdata`.

## Building Locally

To build the documentation locally:

1. Install the documentation requirements:
   ```bash
   pip install -r ../docs-requirements.txt
   ```

2. Install the package in development mode:
   ```bash
   pip install -e ..
   ```

3. Build the documentation:
   ```bash
   make html
   ```

The HTML documentation will be available in `_build/html/index.html`.

## Building with sphinx-multiversion

To build documentation for multiple versions:

```bash
sphinx-multiversion . _build/html
```

This will build documentation for all tagged versions and branches that match the patterns configured in `conf.py`.

## Viewing the Documentation

After building, you can view the documentation by opening `_build/html/index.html` in your web browser:

```bash
python -m http.server --directory _build/html 8000
```

Then navigate to http://localhost:8000 in your browser.

## Continuous Integration

Documentation is automatically built and published to GitHub Pages via GitHub Actions when changes are pushed to the `main` or `master` branch, or when new version tags are created.

See `.github/workflows/documentation.yml` for the CI configuration.

## Documentation Structure

- `index.rst` - Main documentation landing page
- `installation.rst` - Installation instructions
- `examples.rst` - Usage examples and tutorials
- `cli.rst` - Command-line interface reference
- `configuration.rst` - Configuration reference
- `api.rst` - API reference documentation
- `frames.rst` - Frame data documentation
- `calibration.rst` - Calibration data documentation
- `pesummary.rst` - PESummary integration documentation
- `conf.py` - Sphinx configuration

## Adding New Documentation

1. Create a new `.rst` file in this directory
2. Add it to the appropriate `toctree` directive in `index.rst`
3. Rebuild the documentation to see your changes
