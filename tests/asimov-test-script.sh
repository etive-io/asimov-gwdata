mkdir asimov-test
cd asimov-test

asimov init "Test Datafind"

asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/defaults/testing-pe-osg.yaml
asimov apply -f https://git.ligo.org/asimov/data/-/raw/main/events/gwtc-2-1/GW150914_095045.yaml
asimov apply -f ../test-blueprint.yaml -e GW150914_095045

