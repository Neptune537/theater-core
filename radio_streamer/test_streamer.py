import unittest
import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import stream_server

class TestRadioStreamerTools(unittest.TestCase):

    def test_fetch_real_weather_structure(self):
        """Test fetch_real_weather returns dict with required meteorological keys."""
        weather = stream_server.fetch_real_weather()
        self.assertIsInstance(weather, dict)
        self.assertIn("summary", weather)
        self.assertIn("area", weather)
        self.assertIn("temp", weather)
        self.assertIn("condition", weather)
        self.assertIn("humidity", weather)
        self.assertIn("wind", weather)
        self.assertTrue(len(weather["summary"]) > 0)
        self.assertTrue(len(weather["temp"]) > 0)

    def test_fetch_real_news_headlines_structure(self):
        """Test fetch_real_news_headlines returns valid non-empty list of headlines."""
        headlines = stream_server.fetch_real_news_headlines()
        self.assertIsInstance(headlines, list)
        self.assertGreaterEqual(len(headlines), 1)
        for h in headlines:
            self.assertIsInstance(h, str)
            self.assertTrue(len(h.strip()) > 0)

    def test_current_playing_meta_schema(self):
        """Test telemetry metadata schema for live broadcast synchronizer."""
        meta = stream_server.current_playing_meta
        self.assertIn("title", meta)
        self.assertIn("artist", meta)
        self.assertIn("next_title", meta)
        self.assertIn("next_artist", meta)
        self.assertIn("is_news", meta)
        self.assertIn("weather", meta)
        self.assertIn("news_headline", meta)
        self.assertIn("top_of_hour_countdown", meta)
        self.assertIn("active_deck", meta)
        self.assertIn("next_deck", meta)
        self.assertIn("fader_position", meta)
        self.assertIn("transition_active", meta)
        self.assertIn("target_next_action", meta)

    def test_event_logger_and_crossfader(self):
        """Test event logging system comparing target schedule with live state."""
        stream_server.log_broadcast_event(
            "SONG_START",
            "Play 'Test Song' on Deck A until 10s outro (~170s)",
            "On-Air: Test Song [Deck A]",
            {"title": "Test Song", "deck": "A"}
        )
        self.assertGreater(len(stream_server.events_log), 0)
        last_evt = stream_server.events_log[-1]
        self.assertEqual(last_evt["type"], "SONG_START")
        self.assertIn("Play 'Test Song'", last_evt["expected"])
        self.assertIn("On-Air: Test Song", last_evt["actual"])
        self.assertIn("timestamp", last_evt)

    def test_crates_and_web_console_integrity(self):
        """Test crates.json loading and Lemuria pure-web console index.html existence."""
        crates = stream_server.get_cached_crates()
        self.assertIsInstance(crates, list)
        self.assertGreater(len(crates), 0)
        self.assertIn("title", crates[0])
        self.assertIn("artist", crates[0])
        self.assertTrue(os.path.exists(stream_server.INDEX_HTML_PATH))

if __name__ == '__main__':
    unittest.main()
