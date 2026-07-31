# Using asimov-gwdata Test Fixtures in Other Projects

This guide explains how to use asimov-gwdata's test fixtures when testing projects that depend on asimov-gwdata, such as the asimov main project.

## Overview

The asimov-gwdata test fixtures provide mock implementations of external services (GWOSC, gwdatafind) that can be used in testing environments. This is particularly useful when:

1. Testing asimov's integration with asimov-gwdata
2. Running CI/CD pipelines without network access
3. Avoiding load on external servers during testing

## Integration Approaches

### Approach 1: Using a Mock gwdatafind Server

The most correct approach is to run a mock gwdatafind HTTP server that implements the gwdatafind API. asimov-gwdata provides `MockGWDataFindServer` for this purpose.

#### Setting up a Mock gwdatafind Server

```python
from tests.mock_gwdatafind_server import MockGWDataFindServer

# Configure frame URLs for your test
frame_configs = {
    ('H', 'H1_LOSC_16_V1'): [
        'file:///tmp/test-frames/H1/H1_LOSC_16_V1/H-H1_LOSC_16_V1-1126256640-4096.gwf'
    ],
    ('L', 'L1_LOSC_16_V1'): [
        'file:///tmp/test-frames/L1/L1_LOSC_16_V1/L-L1_LOSC_16_V1-1126256640-4096.gwf'
    ]
}

# Start the server
with MockGWDataFindServer(port=8765, frame_configs=frame_configs) as server:
    # Set environment variable to use the mock server
    os.environ['GWDATAFIND_SERVER'] = 'http://localhost:8765'
    
    # Now gwdatafind queries will use the mock server
    # Run your asimov commands here
```

#### Example: asimov HTCondor Tests

In asimov's `.github/workflows/htcondor-tests.yml`:

```yaml
- name: Setup mock gwdatafind server
  run: |
    # Install asimov-gwdata with test support
    pip install -e git+https://github.com/etive-io/asimov-gwdata.git#egg=asimov-gwdata[test]
    
    # Create test frame files
    mkdir -p /tmp/test-frames/H1/H1_LOSC_16_V1
    mkdir -p /tmp/test-frames/L1/L1_LOSC_16_V1
    
    python3 << 'EOF'
    from tests.test_fixtures import create_mock_frame_file
    create_mock_frame_file('/tmp/test-frames/H1/H1_LOSC_16_V1/H-H1_LOSC_16_V1-1126256640-4096.gwf')
    create_mock_frame_file('/tmp/test-frames/L1/L1_LOSC_16_V1/L-L1_LOSC_16_V1-1126256640-4096.gwf')
    EOF
    
    # Start the mock server in the background
    python3 << 'EOF' &
    from tests.mock_gwdatafind_server import MockGWDataFindServer
    
    frame_configs = {
        ('H', 'H1_LOSC_16_V1'): ['file:///tmp/test-frames/H1/H1_LOSC_16_V1/H-H1_LOSC_16_V1-1126256640-4096.gwf'],
        ('L', 'L1_LOSC_16_V1'): ['file:///tmp/test-frames/L1/L1_LOSC_16_V1/L-L1_LOSC_16_V1-1126256640-4096.gwf']
    }
    
    server = MockGWDataFindServer(port=8765, frame_configs=frame_configs)
    server.start()
    
    # Keep the server running
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        server.stop()
    EOF
    
    # Give the server time to start
    sleep 2

- name: Add asimov-gwdata job
  env:
    # Point to the mock server
    GWDATAFIND_SERVER: http://localhost:8765
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

### Approach 3: Using asimov-gwdata Test Fixtures Directly

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
from tests.mock_gwdatafind_server import MockGWDataFindServer
import os

# Create a test directory with mock frame files
with temporary_test_directory() as tmpdir:
    # Create mock frames
    os.makedirs(f'{tmpdir}/H1/H1_HOFT_C02', exist_ok=True)
    os.makedirs(f'{tmpdir}/L1/L1_HOFT_C02', exist_ok=True)
    
    # Configure and start the mock server
    frame_configs = {
        ('H', 'H1_HOFT_C02'): [f'file://{tmpdir}/H1/H1_HOFT_C02/H-H1_HOFT_C02-1126256640-4096.gwf'],
        ('L', 'L1_HOFT_C02'): [f'file://{tmpdir}/L1/L1_HOFT_C02/L-L1_HOFT_C02-1126256640-4096.gwf']
    }
    
    with MockGWDataFindServer(port=8765, frame_configs=frame_configs) as server:
        os.environ['GWDATAFIND_SERVER'] = 'http://localhost:8765'
        
        # Now run your asimov commands
        # asimov will use the mock server
```

## Complete Example: Testing asimov with Mock asimov-gwdata

Here's a complete example for asimov's HTCondor tests using the mock server:

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
          mkdir -p /tmp/test-frames/H1/H1_LOSC_16_V1
          mkdir -p /tmp/test-frames/L1/L1_LOSC_16_V1
          
          # Create minimal mock frame files
          python3 << EOF
          from tests.test_fixtures import create_mock_frame_file
          create_mock_frame_file('/tmp/test-frames/H1/H1_LOSC_16_V1/H-H1_LOSC_16_V1-1126256640-4096.gwf')
          create_mock_frame_file('/tmp/test-frames/L1/L1_LOSC_16_V1/L-L1_LOSC_16_V1-1126256640-4096.gwf')
          EOF
      
      - name: Start mock gwdatafind server
        run: |
          # Start the server in the background
          python3 << 'EOF' &
          from tests.mock_gwdatafind_server import MockGWDataFindServer
          import time
          
          frame_configs = {
              ('H', 'H1_LOSC_16_V1'): ['file:///tmp/test-frames/H1/H1_LOSC_16_V1/H-H1_LOSC_16_V1-1126256640-4096.gwf'],
              ('L', 'L1_LOSC_16_V1'): ['file:///tmp/test-frames/L1/L1_LOSC_16_V1/L-L1_LOSC_16_V1-1126256640-4096.gwf']
          }
          
          server = MockGWDataFindServer(port=8765, frame_configs=frame_configs)
          server.start()
          
          try:
              while True:
                  time.sleep(1)
          except KeyboardInterrupt:
              server.stop()
          EOF
          
          # Wait for server to start
          sleep 2
      
      - name: Add asimov-gwdata job
        env:
          GWDATAFIND_SERVER: http://localhost:8765
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

For completely offline testing using the mock server:

```bash
# In your CI/CD pipeline or test script
# 1. Create test frames
python3 << 'EOF'
from tests.test_fixtures import create_mock_frame_file
import os

for ifo in ['H1', 'L1', 'V1']:
    for frametype in ['HOFT_C02', 'GWOSC_16KHZ_R1']:
        framedir = f'/tmp/test-frames/{ifo}/{ifo}_{frametype}'
        os.makedirs(framedir, exist_ok=True)
        create_mock_frame_file(f'{framedir}/{ifo[0]}-{ifo}_{frametype}-1126256640-4096.gwf')
EOF

# 2. Start the mock server
python3 << 'EOF' &
from tests.mock_gwdatafind_server import MockGWDataFindServer
import time

frame_configs = {
    ('H', 'H1_HOFT_C02'): ['file:///tmp/test-frames/H1/H1_HOFT_C02/H-H1_HOFT_C02-1126256640-4096.gwf'],
    ('L', 'L1_HOFT_C02'): ['file:///tmp/test-frames/L1/L1_HOFT_C02/L-L1_HOFT_C02-1126256640-4096.gwf'],
    # Add more frame types as needed
}

server = MockGWDataFindServer(port=8765, frame_configs=frame_configs)
server.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    server.stop()
EOF

# 3. Set environment variable
export GWDATAFIND_SERVER=http://localhost:8765

# 4. Run asimov tests
asimov manage build submit
```

## Recommended Approach for asimov

Based on the current asimov HTCondor tests, I recommend:

1. **Use MockGWDataFindServer**: Run the mock gwdatafind server as a background service
2. **Pre-stage test frames**: Create frame files in a known location
3. **Use environment variables**: Set `GWDATAFIND_SERVER=http://localhost:8765`

### Example Update to asimov's htcondor-tests.yml

```yaml
      - name: Setup mock gwdatafind infrastructure
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
          
          # Start mock server in background
          python3 << 'PYTHON' &
          from tests.mock_gwdatafind_server import MockGWDataFindServer
          import time
          
          frame_configs = {
              ('H', 'H1_LOSC_16_V1'): ['file:///tmp/test-frames/H1/H1_LOSC_16_V1/H-H1_LOSC_16_V1-1126256640-4096.gwf'],
              ('L', 'L1_LOSC_16_V1'): ['file:///tmp/test-frames/L1/L1_LOSC_16_V1/L-L1_LOSC_16_V1-1126256640-4096.gwf']
          }
          
          server = MockGWDataFindServer(port=8765, frame_configs=frame_configs)
          server.start()
          
          try:
              while True:
                  time.sleep(1)
          except KeyboardInterrupt:
              server.stop()
          PYTHON
          
          sleep 2  # Wait for server to start

      - name: Add asimov-gwdata job
        env:
          # Use local mock server instead of GWOSC
          GWDATAFIND_SERVER: http://localhost:8765
        uses: ./.github/actions/run-asimov-command
        with:
          script: asimov apply -f "$GITHUB_WORKSPACE/tests/test_blueprints/gwosc_get_data.yaml" -e GW150914_095045
```

## Troubleshooting

### Frames Not Found

If asimov-gwdata can't find frames, check:

1. Mock server is running: `curl http://localhost:8765/api/v1/gwf/H/H1_LOSC_16_V1/1126259460,1126259464/file.json`
2. Frame files exist at the paths configured in `frame_configs`
3. Environment variable is set correctly: `echo $GWDATAFIND_SERVER`
4. Server URL includes protocol: `http://localhost:8765` not `localhost:8765`

### Server Not Responding

If the mock server isn't responding:

1. Check if port is available: `netstat -an | grep 8765`
2. Verify server started successfully
3. Check for errors in the server startup script
4. Try a different port if 8765 is in use

### Mock Not Being Used

If the real servers are still being contacted:

1. Verify `GWDATAFIND_SERVER` environment variable is set before running gwdatafind
2. Check that asimov-gwdata is using the environment variable
3. Ensure no hardcoded server URLs in configuration

## Future Enhancements

The asimov-gwdata team is working on:

1. A standalone mock gwdatafind server Docker image
2. Better integration with asimov's testing framework
3. Pre-built test data packages

For now, the MockGWDataFindServer provides reliable offline testing capabilities.
