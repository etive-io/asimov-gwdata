# Using asimov-gwdata Test Fixtures in Other Projects

This guide explains how to use asimov-gwdata's test fixtures when testing projects that depend on asimov-gwdata, such as the asimov main project.

## Overview

The asimov-gwdata test fixtures provide mock implementations of external services (GWOSC, gwdatafind) that can be used in testing environments. This is particularly useful when:

1. Testing asimov's integration with asimov-gwdata
2. Running CI/CD pipelines without network access
3. Avoiding load on external servers during testing

## Integration Approaches

### Approach 1: Using Environment Variables

The simplest approach is to use environment variables to configure asimov-gwdata to use mock servers or local data.

#### Setting up a Mock GWOSC Server

Set the `GWDATAFIND_SERVER` environment variable to point to a local mock server:

```bash
export GWDATAFIND_SERVER=http://localhost:8765
```

#### Example: asimov HTCondor Tests

In asimov's `.github/workflows/htcondor-tests.yml`:

```yaml
- name: Add asimov-gwdata job
  env:
    # Point to a mock server or use file:// URLs
    GWDATAFIND_SERVER: file:///path/to/test/frames
  uses: ./.github/actions/run-asimov-command
  with:
    script: asimov apply -f "$GITHUB_WORKSPACE/tests/test_blueprints/gwosc_get_data.yaml" -e GW150914_095045
```

### Approach 2: Monkey-Patching in Test Setup

For more control, patch the asimov-gwdata functions before asimov calls them:

```python
import sys
from unittest.mock import patch

# Patch gwdatafind before importing asimov-gwdata
def mock_find_urls(site, frametype, gpsstart, gpsend, **kwargs):
    """Return local test frame files."""
    return [f"file:///test/frames/{site}-{frametype}-{gpsstart}-4096.gwf"]

with patch('gwdatafind.find_urls', side_effect=mock_find_urls):
    # Now import and use asimov-gwdata
    from datafind.frames import get_data_frames_private
    
    # This will use the mock
    urls, files = get_data_frames_private(
        types=["H1:H1_HOFT_C02"],
        start=1126259460,
        end=1126259464
    )
```

### Approach 3: Pre-staged Test Data

Create a directory structure with pre-staged test frame files:

```bash
# Create test data directory structure
mkdir -p /tmp/test-frames/H1/H1_HOFT_C02
mkdir -p /tmp/test-frames/L1/L1_HOFT_C02

# Copy or create mock frame files
cp tests/test_data/V1.gwf /tmp/test-frames/H1/H1_HOFT_C02/H-H1_HOFT_C02-1126256640-4096.gwf
cp tests/test_data/V1.gwf /tmp/test-frames/L1/L1_HOFT_C02/L-L1_HOFT_C02-1126256640-4096.gwf
```

Then configure asimov-gwdata to use local files:

```python
# In your test setup
import os
os.environ['GWDATAFIND_SERVER'] = 'file:///tmp/test-frames'
```

### Approach 4: Using asimov-gwdata Test Fixtures Directly

Install asimov-gwdata with test fixtures in your test environment:

```yaml
# In asimov's CI/CD workflow
- name: Install asimov-gwdata with test support
  run: |
    git clone https://github.com/etive-io/asimov-gwdata
    pip install -e asimov-gwdata[test]
```

Then in your test code:

```python
from tests.test_fixtures import MockGWDataFind, temporary_test_directory
import os

# Create a test directory with mock frame files
with temporary_test_directory() as tmpdir:
    # Set up environment
    os.environ['GWDATAFIND_SERVER'] = f'file://{tmpdir}'
    
    # Create mock frames
    os.makedirs(f'{tmpdir}/H1/H1_HOFT_C02', exist_ok=True)
    
    # Now run your asimov commands
    # asimov will use the local frames
```

## Complete Example: Testing asimov with Mock asimov-gwdata

Here's a complete example for asimov's HTCondor tests:

```yaml
name: Tests with HTCondor (with Mock GWData)
on: [push, pull_request]

jobs:
  tests:
    name: "HTCondor Testing with Mocks"
    runs-on: ubuntu-latest
    container:
      image: htcondor/mini:latest
      options: --privileged
    
    steps:
      - uses: actions/checkout@v5
      
      - name: Install asimov-gwdata with test support
        run: |
          git clone https://github.com/etive-io/asimov-gwdata /tmp/asimov-gwdata
          pip install -e /tmp/asimov-gwdata[test]
      
      - name: Set up mock frame files
        run: |
          # Create test frame directory structure
          mkdir -p /tmp/test-frames/H1/H1_GWOSC_16KHZ_R1
          mkdir -p /tmp/test-frames/L1/L1_GWOSC_16KHZ_R1
          
          # Create minimal mock frame files
          python3 << EOF
          from tests.test_fixtures import create_mock_frame_file
          import os
          
          # Create mock frames for H1 and L1
          os.makedirs('/tmp/test-frames/H1/H1_GWOSC_16KHZ_R1', exist_ok=True)
          os.makedirs('/tmp/test-frames/L1/L1_GWOSC_16KHZ_R1', exist_ok=True)
          
          create_mock_frame_file(
              '/tmp/test-frames/H1/H1_GWOSC_16KHZ_R1/H-H1_GWOSC_16KHZ_R1-1126256640-4096.gwf'
          )
          create_mock_frame_file(
              '/tmp/test-frames/L1/L1_GWOSC_16KHZ_R1/L-L1_GWOSC_16KHZ_R1-1126256640-4096.gwf'
          )
          EOF
      
      - name: Set up patch for gwdatafind
        run: |
          # Create a sitecustomize.py to patch gwdatafind on import
          cat > /usr/local/lib/python3.10/site-packages/sitecustomize.py << 'EOF'
          from unittest.mock import patch
          
          def mock_find_urls(site, frametype, gpsstart, gpsend, **kwargs):
              """Return local test frame files."""
              import glob
              pattern = f'/tmp/test-frames/{site}/{frametype}/*.gwf'
              files = glob.glob(pattern)
              return [f'file://{f}' for f in files]
          
          # Apply the patch globally
          patch('gwdatafind.find_urls', side_effect=mock_find_urls).start()
          EOF
      
      - name: Add asimov-gwdata job
        uses: ./.github/actions/run-asimov-command
        with:
          script: asimov apply -f "$GITHUB_WORKSPACE/tests/test_blueprints/gwosc_get_data.yaml" -e GW150914_095045
      
      - name: Build and submit gwdata job
        uses: ./.github/actions/run-asimov-command
        with: 
          script: asimov manage build submit
      
      - name: Wait for frame files
        uses: ./.github/actions/wait-for-files
        with:
          patterns: "*.gwf"
          directory: "working/GW150914_095045/get-data/frames"
          timeout: "300"
          interval: "10"
```

## Testing Without Network Access

For completely offline testing:

```bash
# In your CI/CD pipeline
export GWDATAFIND_SERVER="file:///tmp/test-frames"
export GWOSC_ENDPOINT="file:///tmp/test-frames"

# Create the test frame structure
python3 -c "
from tests.test_fixtures import create_mock_frame_file
import os

# Set up frame directories
for ifo in ['H1', 'L1', 'V1']:
    for frametype in ['HOFT_C02', 'GWOSC_16KHZ_R1']:
        framedir = f'/tmp/test-frames/{ifo}/{ifo}_{frametype}'
        os.makedirs(framedir, exist_ok=True)
        create_mock_frame_file(f'{framedir}/{ifo[0]}-{ifo}_{frametype}-1126256640-4096.gwf')
"

# Now run asimov tests
asimov manage build submit
```

## Recommended Approach for asimov

Based on the current asimov HTCondor tests, I recommend:

1. **Pre-stage test frames**: Create a directory with mock frame files before running asimov
2. **Use environment variables**: Configure `GWDATAFIND_SERVER` to point to the local frames
3. **Optionally patch**: Use sitecustomize.py or similar to globally patch gwdatafind

### Example Update to asimov's htcondor-tests.yml

```yaml
      - name: Setup test frame files
        run: |
          # Install asimov-gwdata with test support
          pip install -e git+https://github.com/etive-io/asimov-gwdata.git#egg=asimov-gwdata[test]
          
          # Create mock frame files
          mkdir -p /tmp/test-frames/{H1,L1}/{H1_LOSC_16_V1,L1_LOSC_16_V1}
          
          python3 << 'PYTHON'
          from tests.test_fixtures import create_mock_frame_file
          
          # Create H1 frames
          create_mock_frame_file('/tmp/test-frames/H1/H1_LOSC_16_V1/H-H1_LOSC_16_V1-1126256640-4096.gwf')
          
          # Create L1 frames  
          create_mock_frame_file('/tmp/test-frames/L1/L1_LOSC_16_V1/L-L1_LOSC_16_V1-1126256640-4096.gwf')
          PYTHON

      - name: Add asimov-gwdata job
        env:
          # Use local frames instead of GWOSC
          GWDATAFIND_SERVER: file:///tmp/test-frames
        uses: ./.github/actions/run-asimov-command
        with:
          script: asimov apply -f "$GITHUB_WORKSPACE/tests/test_blueprints/gwosc_get_data.yaml" -e GW150914_095045
```

## Troubleshooting

### Frames Not Found

If asimov-gwdata can't find frames, check:

1. Directory structure matches: `/path/{IFO}/{FRAMETYPE}/{IFO}-{FRAMETYPE}-{GPS}-{DURATION}.gwf`
2. Environment variable is set correctly
3. File permissions allow reading

### Mock Not Being Used

If the real servers are still being contacted:

1. Verify patches are applied before import
2. Check environment variables are exported correctly
3. Ensure mock server is running (if using server approach)

## Future Enhancements

The asimov-gwdata team is working on:

1. A standalone mock gwdatafind server that can be run as a service
2. Better integration with asimov's testing framework
3. Pre-built Docker images with mock data included

For now, the approaches above provide reliable offline testing capabilities.
