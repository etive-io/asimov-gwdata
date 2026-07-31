# Tests Directory

This directory contains the test suite for asimov-gwdata.

## Quick Start

Run all tests:
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Test Modules

- **test_fixtures.py** - Mock fixtures and utilities for testing without external resources
- **test_with_mocks.py** - Examples demonstrating how to use the mock fixtures
- **test_frames.py** - Tests for frame file access and manipulation
- **test_calibration.py** - Tests for calibration data handling
- **test_pesummary.py** - Tests for PESummary metafile operations

## Test Data

The `test_data/` directory contains small test files that are committed to the repository:
- `V1.gwf` - A sample Virgo frame file

Larger test files (like `GW150914.hdf5`) are downloaded on-demand and are not committed.

## Running Tests Offline

The test suite is designed to work without network access by using mock objects. Tests that require network access will be skipped gracefully.

See [../docs/testing.md](../docs/testing.md) for detailed documentation.

## Adding New Tests

1. Use the fixtures in `test_fixtures.py` for mocking external services
2. Follow the existing test patterns
3. Use descriptive test names and docstrings
4. Make tests work offline when possible
5. Skip gracefully if dependencies are unavailable

Example:
```python
from tests.test_fixtures import MockGWDataFind
from unittest.mock import patch

class TestMyFeature(unittest.TestCase):
    def test_with_mock(self):
        """Test description here."""
        with patch('datafind.frames.find_urls', side_effect=mock_func):
            # Your test code
            pass
```
