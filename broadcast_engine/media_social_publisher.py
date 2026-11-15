"""
Automated Social Media & Video Distribution Publisher
Handles automated formatting, tagging, and announcement packaging for
new music tracks, station identifiers, breaking news episodes, and 3D scenes.
"""

import os
import sys
import json
import datetime
import urllib.request

class MediaSocialPublisher:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")

    def publish_release(self, title: str, category: str, track_info: dict, stream_url: str = "http://localhost:8080/live.mp3"):
        """Publishes structured video/music metadata card for social streams and Discord relay."""
        payload = {
            "title": f"ðŸŽµ [NEW RELEASE] {title}",
            "category": category,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "stream_url": stream_url,
            "track_details": track_info,
            "platforms": {
                "youtube_live": "24/7 Siren Radio Live Stream (RTMP Ingest)",
                "kuroshio_mesh": "siren:frequency:global_stage (WebTransport / Opus 48kHz)",
                "browser_hud": "HeavenlyBound 3D Viewport Radio Tab"
            }
        }
        
        # Save release manifest locally
        out_dir = r"C:\Users\blue-\projects\theater\broadcast_engine\audio_output\releases"
        os.makedirs(out_dir, exist_ok=True)
        filename = f"release_{int(datetime.datetime.now().timestamp())}.json"
        with open(os.path.join(out_dir, filename), "w") as f:
            json.dump(payload, f, indent=2)

        print(f"[MediaSocialPublisher] Release saved to {filename}")

        if self.webhook_url:
            self._post_webhook(payload)
        else:
            print("[MediaSocialPublisher] DISCORD_WEBHOOK_URL unset; packaged locally for direct broadcast.")
        return payload

    def _post_webhook(self, data: dict):
        try:
            embed = {
                "title": data["title"],
                "description": f"**Category:** {data['category']}\n**Stream:** {data['stream_url']}\n\n**Details:** {json.dumps(data['track_details'], indent=2)}",
                "color": 0x00E5FF,
                "footer": {"text": "Kuroshio Gyre â€¢ 24/7 Siren Radio Network"}
            }
            body = json.dumps({"username": "Siren Media Engine", "embeds": [embed]}).encode("utf-8")
            req = urllib.request.Request(self.webhook_url, data=body, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                print(f"[MediaSocialPublisher] Dispatched to social gateway. Status: {resp.status}")
        except Exception as e:
            print(f"[MediaSocialPublisher] Webhook relay skipped: {e}")

if __name__ == "__main__":
    publisher = MediaSocialPublisher()
    sample_track = {
        "title": "Maia Horizon Chill 432 Hz Station ID",
        "artist": "The Seven Daughters",
        "frequency": "432 Hz",
        "genre": "Dawn Oceanic Ambient / Horizon Chill",
        "duration": "00:00:26",
        "audio_stem": "audio_output/daughters/siren_id_maia_432Hz.mp3"
    }
    publisher.publish_release("Maia 432Hz Station Launch", "Seven Daughters 24/7 Radio", sample_track)
