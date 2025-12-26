# Asimov GWData

This package provides an asimov pipeline for collecting published gravitational wave data for use in parameter estimation studies.

## Installation

```bash
pip install asimov-gwdata
```

For development:
```bash
git clone https://github.com/etive-io/asimov-gwdata
cd asimov-gwdata
pip install -e .
```

## Usage

## Fetching posteriors

To download a posterior file from a known location you'll need to write a YAML configuration file, for example,

```yaml
data: 
  - posterior
source:
  type: pesummary
  location: /home/daniel/GW150914/test.h5
  analysis: C01:IMRPhenomXPHM
```

and then run

`$ gwdata --settings test.yaml`
where `test.yaml` is the configuration file above.

## Usage with asimov

The script can also be called as a pipeline in asimov.
To do this you'll need to apply a blueprint to the project, for example:

```yaml
kind: analysis
name: get-data
pipeline: gwdata
download:
  - posterior
event: GW150914
source:
  type: pesummary
  location: /home/daniel/<event>/test.h5
  analysis: C01:IMRPhenomXPHM
```

## Testing

This package includes a comprehensive test suite that can run without network access using mock fixtures.

Run tests:
```bash
python3 -m unittest discover -s tests -p "test_*.py" -v
```

Or use the convenient test runner script:
```bash
chmod +x run_tests.sh  # Make executable (first time only)
./run_tests.sh
```

For detailed testing documentation, see [docs/testing.md](docs/testing.md).

For CI/CD integration examples, see [docs/ci-testing-examples.md](docs/ci-testing-examples.md).

**Using asimov-gwdata test fixtures in other projects (e.g., asimov):**
See [docs/integration-testing.md](docs/integration-testing.md) for detailed guidance on how to
use asimov-gwdata's mock fixtures when testing projects that call asimov-gwdata.

## Development

See [tests/README.md](tests/README.md) for information on writing tests.
