# Asimov GWData

This package provides an asimov pipeline for collecting published gravitational wave data for use in parameter estimation studies.

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
