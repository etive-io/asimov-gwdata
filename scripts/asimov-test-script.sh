mkdir asimov-050-test
cd asimov-050-test

asimov init "Test Datafind"

asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/defaults/testing-pe.yaml
asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/events/gwtc-2-1/GW150914_095045.yaml
asimov apply -f ../../blueprints/asimov-analysis.yaml \
       -e GW150914_095045

