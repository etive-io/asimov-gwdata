# Example CI/CD Configuration for Testing asimov-gwdata

This directory contains example configurations for running tests in various CI/CD environments.

## GitLab CI Example

Create or update `.gitlab-ci.yml`:

```yaml
# Test with offline mocks (no network required)
test:offline:
  stage: test
  image: python:3.9
  script:
    - pip install -e .
    - python3 -m unittest discover -s tests -p "test_*.py" -v
  # Tests using mocks will pass, others will skip gracefully
  
# Test with network access (optional)
test:with-network:
  stage: test
  image: python:3.9
  script:
    - pip install -e .
    # Pre-download test data
    - wget -O tests/GW150914.hdf5 "https://zenodo.org/records/6513631/files/IGWN-GWTC2p1-v2-GW150914_095045_PEDataRelease_mixed_cosmo.h5?download=1" || true
    - python3 -m unittest discover -s tests -p "test_*.py" -v
  # This job can fail without failing the pipeline
  allow_failure: true
  only:
    - schedules
    - web
```

## GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test-offline:
    name: Test without network
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
    
    - name: Run tests
      run: |
        python -m unittest discover -s tests -p "test_*.py" -v
  
  test-with-network:
    name: Test with network (optional)
    runs-on: ubuntu-latest
    # Only run on schedule or manual trigger
    if: github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
    
    - name: Download test data
      run: |
        wget -O tests/GW150914.hdf5 \
          "https://zenodo.org/records/6513631/files/IGWN-GWTC2p1-v2-GW150914_095045_PEDataRelease_mixed_cosmo.h5?download=1" \
          || echo "Failed to download test data"
    
    - name: Run tests
      run: |
        python -m unittest discover -s tests -p "test_*.py" -v
      continue-on-error: true
```

## Local Development

For local development, run tests as follows:

```bash
# Install the package in development mode
pip install -e .

# Run all tests (offline-friendly)
python3 -m unittest discover -s tests -p "test_*.py" -v

# Run specific test modules
python3 -m unittest tests.test_with_mocks -v
python3 -m unittest tests.test_frames.TestLIGOFramesWithMocks -v

# With network access, download test data first (one-time)
wget -O tests/GW150914.hdf5 \
  "https://zenodo.org/records/6513631/files/IGWN-GWTC2p1-v2-GW150914_095045_PEDataRelease_mixed_cosmo.h5?download=1"

# Then run all tests
python3 -m unittest discover -s tests -p "test_*.py" -v
```

## Docker Example

For testing in Docker:

```dockerfile
FROM python:3.10

WORKDIR /app

# Copy source code
COPY . .

# Install package
RUN pip install -e .

# Run tests (offline mode)
CMD ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]
```

Build and run:
```bash
docker build -t asimov-gwdata-test .
docker run asimov-gwdata-test
```

## Integration with Other asimov Projects

When using asimov-gwdata as a dependency in other projects (like asimov itself):

For detailed guidance on using asimov-gwdata test fixtures in other projects,
including how to test asimov when it calls asimov-gwdata, see:
**[Integration Testing Guide](integration-testing.md)**

Quick example for installing asimov-gwdata with test support:

```yaml
# In another project's CI/CD
test:with-asimov-gwdata:
  stage: test
  script:
    # Install asimov-gwdata with test fixtures
    - pip install -e git+https://github.com/etive-io/asimov-gwdata.git#egg=asimov-gwdata[test]
    
    # Set up mock data
    - mkdir -p /tmp/test-frames/H1/H1_HOFT_C02
    - python3 -c "from tests.test_fixtures import create_mock_frame_file; create_mock_frame_file('/tmp/test-frames/H1/H1_HOFT_C02/H-H1_HOFT_C02-1126256640-4096.gwf')"
    
    # Configure to use local frames
    - export GWDATAFIND_SERVER=file:///tmp/test-frames
    
    # Run your project's tests (e.g., asimov)
    - python3 -m unittest discover
```

See [integration-testing.md](integration-testing.md) for complete examples including
asimov's HTCondor testing workflow.

## Caching Test Data

To speed up repeated test runs with network access:

### GitLab CI Cache
```yaml
test:
  cache:
    key: test-data
    paths:
      - tests/GW150914.hdf5
  script:
    - if [ ! -f tests/GW150914.hdf5 ]; then wget -O tests/GW150914.hdf5 "..."; fi
    - python3 -m unittest discover -s tests -p "test_*.py" -v
```

### GitHub Actions Cache
```yaml
- name: Cache test data
  uses: actions/cache@v3
  with:
    path: tests/GW150914.hdf5
    key: test-data-${{ hashFiles('tests/test_pesummary.py') }}
    
- name: Download test data if not cached
  run: |
    if [ ! -f tests/GW150914.hdf5 ]; then
      wget -O tests/GW150914.hdf5 "..."
    fi
```

## Best Practices

1. **Primary CI jobs should not require network** - Use offline mocks
2. **Network tests are optional** - Run on schedule or manual trigger
3. **Cache large test files** - Avoid repeated downloads
4. **Test across Python versions** - Use matrix builds
5. **Clear failure messages** - Help developers understand what went wrong
