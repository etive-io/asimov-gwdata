"""
Regression tests for the Liquid template asimov uses to render a production's
meta into a ``gwdata`` settings file (``datafind/datafind_template.yml``).

These render the template the same way ``asimov.analysis.Analysis.make_config``
does (via ``liquid.Liquid``), using lightweight duck-typed stand-ins for the
``production``/``event`` objects rather than a full asimov ledger/project.
"""
import os
import unittest

import yaml
from liquid import Liquid

TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "datafind",
    "datafind_template.yml",
)


class FakeEvent:
    def __init__(self, name="GW150914_095045"):
        self.name = name
        self.repository = None


class FakeProduction:
    def __init__(self, meta, name="get-data", event=None):
        self.name = name
        self.event = event or FakeEvent()
        self.meta = meta


def render(meta):
    production = FakeProduction(meta)
    liq = Liquid(TEMPLATE)
    rendered = liq.render(production=production, analysis=production, pipeline=None, config=None)
    return yaml.safe_load(rendered)


class TestDatafindTemplate(unittest.TestCase):
    """
    Regression tests for a template bug where the ``locations.datafind server``,
    ``virgo frametype``, and ``virgo timestamp channel`` blocks each emitted the
    wrong YAML key (copy-pasted from a neighbouring block), so a blueprint
    setting any of them independently produced a config file with the wrong
    field silently populated instead.
    """

    def test_locations_datafind_server_key(self):
        rendered = render(
            {
                "event time": 1126259462,
                "locations": {"datafind server": "datafind.example.org"},
            }
        )
        self.assertEqual(rendered["locations"]["datafind server"], "datafind.example.org")
        self.assertNotIn("calibration directory", rendered["locations"])

    def test_locations_both_keys_independent(self):
        rendered = render(
            {
                "event time": 1126259462,
                "locations": {
                    "calibration directory": "/home/cal/archive/",
                    "datafind server": "datafind.example.org",
                },
            }
        )
        self.assertEqual(rendered["locations"]["calibration directory"], "/home/cal/archive/")
        self.assertEqual(rendered["locations"]["datafind server"], "datafind.example.org")

    def test_virgo_frametype_key(self):
        rendered = render(
            {
                "event time": 1126259462,
                "virgo frametype": "V1:HoftAR1",
            }
        )
        self.assertEqual(rendered["virgo frametype"], "V1:HoftAR1")
        self.assertNotIn("virgo prefix", rendered)

    def test_virgo_timestamp_channel_key(self):
        rendered = render(
            {
                "event time": 1126259462,
                "virgo timestamp channel": "V1:Hrec_hoft_U00_lastWriteGPS",
            }
        )
        self.assertEqual(
            rendered["virgo timestamp channel"], "V1:Hrec_hoft_U00_lastWriteGPS"
        )
        self.assertNotIn("virgo prefix", rendered)

    def test_all_virgo_keys_independent(self):
        rendered = render(
            {
                "event time": 1126259462,
                "virgo prefix": "V1:Hrec_hoft_U00",
                "virgo frametype": "V1:HoftAR1",
                "virgo timestamp channel": "V1:Hrec_hoft_U00_lastWriteGPS",
            }
        )
        self.assertEqual(rendered["virgo prefix"], "V1:Hrec_hoft_U00")
        self.assertEqual(rendered["virgo frametype"], "V1:HoftAR1")
        self.assertEqual(
            rendered["virgo timestamp channel"], "V1:Hrec_hoft_U00_lastWriteGPS"
        )

    def test_core_fields_still_render(self):
        rendered = render(
            {
                "event time": 1126259462,
                "file length": 4096,
                "interferometers": ["H1", "L1"],
                "download": ["frames", "calibration"],
                "calibration version": "v1",
            }
        )
        self.assertEqual(rendered["interferometers"], ["H1", "L1"])
        self.assertEqual(rendered["time"], {"start": 1126259461, "end": 1126259463, "duration": 4096})
        self.assertEqual(rendered["data"], ["frames", "calibration"])
        self.assertEqual(rendered["calibration version"], "v1")


if __name__ == "__main__":
    unittest.main()
