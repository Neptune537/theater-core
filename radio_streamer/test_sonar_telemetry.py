import json
import math
import time
import unittest

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import sonar_telemetry


class LiveFeedTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.now_ms = int(time.time() * 1000)
        self.plane = [None] * 17
        self.plane[0] = "a12345"
        self.plane[1] = "CALL123"
        self.plane[3] = self.now_ms // 1000
        self.plane[5] = -95.1
        self.plane[6] = 29.6
        self.plane[7] = 1200.0
        self.plane[9] = 82.0
        self.plane[10] = 135.0
        self.plane[11] = 1.5

    def test_flight_has_observed_position_and_no_fabricated_reward(self):
        event = sonar_telemetry.signed_opensky_flight_event(self.plane, self.key, self.now_ms)
        self.assertIsNotNone(event)
        message = event["payload"]["message"]
        self.key.public_key().verify(bytes.fromhex(event["signature"]), message.encode())
        update = json.loads(message)
        entity = update["entity"]
        self.assertEqual(update["observed_at_unix_ms"], self.plane[3] * 1000)
        self.assertEqual(entity["attached_bounty_cyan"], 0.0)
        self.assertAlmostEqual(math.hypot(*entity["ecef"]), 6373000, delta=10000)
        self.assertEqual(entity["telemetry"]["AircraftFlight"]["origin_airport"], "")
        self.assertEqual(entity["telemetry"]["AircraftFlight"]["squawk"], "")

    def test_stale_or_incomplete_flight_is_not_published(self):
        self.plane[3] -= 31
        self.assertIsNone(sonar_telemetry.signed_opensky_flight_event(self.plane, self.key, self.now_ms))
        self.plane[3] = self.now_ms // 1000
        self.plane[7] = None
        self.assertIsNone(sonar_telemetry.signed_opensky_flight_event(self.plane, self.key, self.now_ms))

    def test_no_synthetic_guild_publisher(self):
        self.assertFalse(hasattr(sonar_telemetry, "signed_trading_guild_event"))


if __name__ == "__main__":
    unittest.main()
