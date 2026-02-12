# Testing Framework Documentation

This document describes the testing infrastructure for asimov-gwdata, including how to run tests both with and without network access.

## Overview

The asimov-gwdata testing framework has been improved to support offline testing without requiring access to external resources like:
- GWOSC (Gravitational Wave Open Science Center) servers
- gwdatafind servers
- Zenodo for test data downloads

## Test Structure

### Test Modules

1. **test_fixtures.py** - Provides mock fixtures for testing without network access
   - `MockGWDataFind` - Mock gwdatafind server
   - `MockGWOSC` - Mock GWOSC data access
   - Utility functions for test data management

2. **test_frames.py** - Tests for frame file access
   - Uses mocks to test frame lookup without network
   - Legacy tests kept for integration testing (skipped by default)

3. **test_calibration.py** - Tests for calibration data handling
   - Uses mocks for file system operations

4. **test_pesummary.py** - Tests for PESummary metafile handling
   - Gracefully handles missing test data files

5. **test_with_mocks.py** - Examples demonstrating mock usage

## Running Tests

### Basic Test Execution

Run all tests:
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Run a specific test module:
```bash
python3 -m unittest tests.test_frames -v
```

Run a specific test class:
```bash
python3 -m unittest tests.test_frames.TestLIGOFramesWithMocks -v
```

Run a specific test:
```bash
python3 -m unittest tests.test_frames.TestLIGOFramesWithMocks.test_lookup_gw150914_with_mock -v
```

### Offline Testing

All tests using mocks will work without network access:

```bash
# These tests will pass without network
python3 -m unittest tests.test_with_mocks -v
python3 -m unittest tests.test_frames.TestLIGOFramesWithMocks -v
```

### Integration Testing

Some tests require network access or authentication:

```bash
# Requires IGWN authentication
python3 -m unittest tests.test_calibration.TestFrameCalibration -v

# Requires network to download test data
python3 -m unittest tests.test_pesummary -v
```

## Using Test Fixtures

### Example: Mocking gwdatafind

```python
from tests.test_fixtures import MockGWDataFind
from unittest.mock import patch

def mock_find_urls(site, frametype, gpsstart, gpsend, **kwargs):
    """Custom mock implementation."""
    return ["file:///path/to/frame.gwf"]

# Use in a test
with patch('datafind.frames.find_urls', side_effect=mock_find_urls):
    # Your test code here
    urls, files = get_data_frames_private(...)
```

### Example: Mocking GWOSC

```python
from tests.test_fixtures import MockGWOSC

mock_gwosc = MockGWOSC({
    'H1': ['https://gwosc.org/data/H1-frame.gwf'],
    'L1': ['https://gwosc.org/data/L1-frame.gwf']
})

with mock_gwosc.patch_get_urls():
    # Your test code here
    urls = get_data_frames_gwosc(...)
```

### Example: Temporary Test Directory

```python
from tests.test_fixtures import temporary_test_directory

with temporary_test_directory() as tmpdir:
    # Create test files
    test_file = os.path.join(tmpdir, 'test.txt')
    with open(test_file, 'w') as f:
        f.write('test data')
    
    # Run tests
    # ...
    
# Directory is automatically cleaned up
```

## CI/CD Integration

### Without Network Access

The test suite is designed to work in CI/CD environments without network access:

```yaml
# .gitlab-ci.yml or similar
test:
  script:
    - pip install -e .
    - python3 -m unittest discover -s tests -p "test_*.py" -v
```

All tests will either:
- Pass using mocks (for network-dependent functionality)
- Skip gracefully (if optional dependencies are missing)

### With Network Access

If network access is available, additional integration tests will run:

```yaml
test-with-network:
  script:
    - pip install -e .
    # Download test data first
    - wget -O tests/GW150914.hdf5 "https://zenodo.org/records/6513631/files/IGWN-GWTC2p1-v2-GW150914_095045_PEDataRelease_mixed_cosmo.h5?download=1"
    - python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Test Data

### Included Test Data

- `tests/test_data/V1.gwf` - A sample Virgo frame file

### Downloaded Test Data (Optional)

- `tests/GW150914.hdf5` - PESummary metafile for GW150914 (~12MB)
  - Downloaded automatically if network is available
  - Tests skip gracefully if not present

### Managing Large Test Files

For large test files, consider:

1. **Git LFS** - Store large files using Git Large File Storage
2. **Pre-download** - Download files in CI/CD before running tests
3. **Artifacts** - Cache downloaded files as CI/CD artifacts

## Extending the Test Framework

### Adding New Mocks

To add a new mock for testing:

1. Add the mock class to `tests/test_fixtures.py`:

```python
class MockNewService:
    """Mock for a new external service."""
    
    def __init__(self, mock_data):
        self.mock_data = mock_data
    
    def mock_method(self, *args, **kwargs):
        """Mock implementation."""
        return self.mock_data
    
    @contextmanager
    def patch_method(self):
        """Context manager for patching."""
        with patch('module.method', side_effect=self.mock_method):
            yield self
```

2. Create tests demonstrating its usage in `tests/test_with_mocks.py`

3. Update this documentation

### Adding New Test Data

To add new test data files:

1. Place small files (<1MB) in `tests/test_data/`
2. For large files:
   - Use Git LFS, or
   - Download in `setUpModule()` with graceful failure, or
   - Provide download script

## Best Practices

1. **Prefer Mocks** - Use mocks for external services when possible
2. **Graceful Degradation** - Skip tests if dependencies are unavailable
3. **Clear Messages** - Provide helpful skip messages explaining what's needed
4. **Document Requirements** - Clearly document what each test needs
5. **Minimal Test Data** - Keep test data files as small as possible

## Troubleshooting

### Tests Skip Due to Missing Dependencies

Some tests may skip if optional dependencies are missing:

```
skipped "Cannot access frame file: No module named 'LDAStools'"
```

This is expected. Install the missing dependency if you need to run that test:

```bash
pip install LDAStools
```

### Tests Skip Due to Missing Authentication

Some tests require IGWN authentication:

```
skipped 'No scitoken was found'
```

Set up authentication following the IGWN guidelines if you need to run these tests.

### Network Errors

If tests fail with network errors in an offline environment, ensure you're running the mock-based tests:

```bash
python3 -m unittest tests.test_frames.TestLIGOFramesWithMocks -v
```

Instead of the legacy integration tests:

```bash
# Don't run this offline - it's marked as skipped anyway
python3 -m unittest tests.test_frames.TestLIGOFrames -v
```
