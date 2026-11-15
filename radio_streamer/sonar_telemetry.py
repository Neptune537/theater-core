import asyncio
import contextlib
import json
import logging
import math
import os
from pathlib import Path
import time
import urllib.request

import aiohttp
from aiohttp import web
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

TOPICS = {"gyre:sonar:tactical", "gyre:telemetry:gods_eye"}
DID = "did:atlantis:seed-radio"
ALLOWED_ORIGINS = {
    "https://heavenlysent-680ac.web.app", "https://heavenlysent-680ac.firebaseapp.com",
    "https://heavenlysent-lite-680ac.web.app", "https://heavenlysent-lite-680ac.firebaseapp.com",
    "https://tr7n7t7.com", "https://www.tr7n7t7.com", "https://heavenlybound-lite.pages.dev",
    "https://play.tr7n7t7.com", "https://lite.tr7n7t7.com",
}


def wgs84_ecef(lat_deg, lon_deg, alt_meters):
    latitude, longitude = math.radians(lat_deg), math.radians(lon_deg)
    sin_lat, cos_lat = math.sin(latitude), math.cos(latitude)
    semi_major = 6378137.0
    eccentricity_squared = 1.0 / 298.257223563 * (2.0 - 1.0 / 298.257223563)
    normal = semi_major / math.sqrt(1.0 - eccentricity_squared * sin_lat * sin_lat)
    return [(normal + alt_meters) * cos_lat * math.cos(longitude),
            (normal + alt_meters) * cos_lat * math.sin(longitude),
            (normal * (1.0 - eccentricity_squared) + alt_meters) * sin_lat]


def load_identity(directory):
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    key_path = directory / "ed25519.key"
    if not key_path.exists():
        with key_path.open("xb") as output:
            os.chmod(key_path, 0o600)
            output.write(os.urandom(32))
    key = Ed25519PrivateKey.from_private_bytes(key_path.read_bytes())
    return key


def signed_station_event(status, key, now_ms):
    if not isinstance(status, dict):
        return None
    if status.get("live") is not True or status.get("status") != "online":
        return None
    measured = status.get("last_chunk_timestamp", 0)
    if isinstance(measured, bool) or not isinstance(measured, (float, int)) or not 0 <= now_ms / 1000 - measured < 15:
        return None
    now_ms = int(measured * 1000)
    daughter = status.get("active_daughter", {})
    if isinstance(daughter, dict):
        daughter = daughter.get("name", "")
    entity = {
        "entity_id": "seven-daughters", "callsign": "Atlantis · Seven Daughters radio",
        "layer": "SdrSirenRadio",
        "geo": {"lat_deg": 29.614699, "lon_deg": -95.19318, "alt_meters": 0.0},
        "ecef": wgs84_ecef(29.614699, -95.19318, 0.0), "heading_deg": 0.0, "pitch_deg": 0.0, "speed_mps": 0.0,
        "telemetry": {"SdrRadioStation": {
            "frequency_mhz": 0.0, "modulation": "HTTPS MP3",
            "active_daughter_or_op": str(daughter)[:120], "sabine_rt60_sec": 0.0,
        }},
        "attached_bounty_cyan": 0.0, "claimed_by_guild_did": None,
    }
    message = json.dumps({"source_did": DID, "observed_at_unix_ms": now_ms, "entity": entity},
                         separators=(",", ":"), ensure_ascii=False)
    return {
        "id": f"seed-radio-{now_ms}", "did": DID, "eventType": "MESH_SIGNAL",
        "payload": {"node_tier": "Epipelagic", "message": message},
        "signature": key.sign(message.encode()).hex(), "timestamp": now_ms // 1000,
    }


def signed_opensky_flight_event(plane_state, key, now_ms):
    """Emits live Aviation ADS-B telemetry for Cockpit Ride-Along."""
    # OpenSky schema: [icao24, callsign, origin_country, time_pos, last_contact, lon, lat, baro_alt, on_ground, vel, true_track, vert_rate, ...]
    try:
        icao24 = str(plane_state[0]).strip().lower()
        callsign = str(plane_state[1] or icao24).strip()
        position_time = int(plane_state[3])
        if not 0 <= now_ms / 1000 - position_time < 30:
            return None
        lon = float(plane_state[5])
        lat = float(plane_state[6])
        alt = float(plane_state[7])
        speed = float(plane_state[9])
        heading = float(plane_state[10])
        vert_rate = float(plane_state[11])
        if not all(map(math.isfinite, (lon, lat, alt, speed, heading, vert_rate))):
            return None
        if not -90 <= lat <= 90 or not -180 <= lon <= 180 or speed < 0:
            return None
        observed_ms = position_time * 1000

        entity = {
            "entity_id": f"flight-{icao24}",
            "callsign": f"FLIGHT {callsign}",
            "layer": "AviationAdsB",
            "geo": {"lat_deg": lat, "lon_deg": lon, "alt_meters": alt},
            "ecef": wgs84_ecef(lat, lon, alt),
            "heading_deg": heading,
            "pitch_deg": 0.0,
            "speed_mps": speed,
            "telemetry": {"AircraftFlight": {
                "icao24_hex": icao24,
                "origin_airport": "",
                "dest_airport": "",
                "mach_or_knots": round(speed * 1.94384, 1),
                "vertical_rate_fpm": round(vert_rate * 196.85, 1),
                "squawk": str(plane_state[14] or "")
            }},
            "attached_bounty_cyan": 0.0,
            "claimed_by_guild_did": None
        }
        message = json.dumps({"source_did": DID, "observed_at_unix_ms": observed_ms, "entity": entity},
                             separators=(",", ":"), ensure_ascii=False)
        return {
            "id": f"flight-{icao24}-{observed_ms}", "did": DID, "eventType": "MESH_SIGNAL",
            "payload": {"node_tier": "Epipelagic", "message": message},
            "signature": key.sign(message.encode()).hex(), "timestamp": position_time,
        }
    except Exception:
        return None


async def sonar_socket(request):
    app = request.app
    protocols = [value.strip() for value in request.headers.get("Sec-WebSocket-Protocol", "").split(",")]
    if request.headers.get("Origin") not in ALLOWED_ORIGINS or "sonar.v1" not in protocols:
        raise web.HTTPForbidden()
    if len(app["clients"]) >= 64:
        raise web.HTTPServiceUnavailable()
    ws = web.WebSocketResponse(protocols=["sonar.v1"], heartbeat=20, max_msg_size=4096)
    app["clients"][ws] = set()
    try:
        await ws.prepare(request)
        async for message in ws:
            if message.type != aiohttp.WSMsgType.TEXT:
                continue
            try:
                frame = json.loads(message.data)
            except (ValueError, TypeError):
                await ws.close(code=1008, message=b"Invalid subscription")
                break
            topic = frame.get("topic") if isinstance(frame, dict) else None
            if not isinstance(topic, str) or topic not in TOPICS:
                await ws.close(code=1008, message=b"Topic denied")
                break
            if frame.get("action") == "subscribe":
                app["clients"][ws].add(topic)
            elif frame.get("action") == "unsubscribe":
                app["clients"][ws].discard(topic)
            else:
                await ws.close(code=1008, message=b"Read-only feed")
                break
    finally:
        app["clients"].pop(ws, None)
    return ws


async def send_frame(ws, frame):
    try:
        await asyncio.wait_for(ws.send_str(frame), timeout=1)
    except (ConnectionError, RuntimeError, asyncio.TimeoutError):
        with contextlib.suppress(ConnectionError, RuntimeError, asyncio.TimeoutError):
            await asyncio.wait_for(ws.close(), timeout=1)


async def broadcast_event(app, event):
    if not event:
        return
    await asyncio.gather(*(
        send_frame(ws, json.dumps({
            "action": "publish",
            "topic": "gyre:sonar:tactical" if "gyre:sonar:tactical" in subscriptions else "gyre:telemetry:gods_eye",
            "event": event,
        }))
        for ws, subscriptions in list(app["clients"].items())
        if subscriptions & TOPICS
    ))


async def publish_telemetry(app):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=4)) as session:
        cached_flights = []
        last_flight_fetch = 0

        while True:
            now = time.time()
            now_ms = int(now * 1000)

            # 1. Publish Station Telemetry (SdrSirenRadio)
            try:
                async with session.get("http://127.0.0.1:8082/api/status") as response:
                    response.raise_for_status()
                    status = await response.json()
                event = signed_station_event(status, app["signing_key"], now_ms)
                if event:
                    await broadcast_event(app, event)
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, TypeError) as error:
                logging.warning("Station telemetry poll failed (%s)", type(error).__name__)

            # 2. Publish Live OpenSky ADS-B Flights (AviationAdsB)
            # Poll OpenSky every 25 seconds to respect rate limits
            if now - last_flight_fetch >= 25.0:
                try:
                    url = "https://opensky-network.org/api/states/all?lamin=28.0&lomin=-98.0&lamax=32.0&lomax=-94.0"
                    async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            cached_flights = data.get("states", [])[:3]  # Stream top 3 live aircraft in the corridor
                            last_flight_fetch = now
                except Exception as e:
                    logging.warning("OpenSky fetch failed (%s)", type(e).__name__)

            for plane in cached_flights:
                flight_event = signed_opensky_flight_event(plane, app["signing_key"], now_ms)
                if flight_event:
                    await broadcast_event(app, flight_event)

            await asyncio.sleep(5)


async def lifecycle(app):
    task = asyncio.create_task(publish_telemetry(app))
    yield
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task
    for ws in list(app["clients"]):
        await ws.close(code=1001)


def make_app(directory):
    key = load_identity(directory)
    app = web.Application(client_max_size=4096)
    app["signing_key"], app["clients"] = key, {}
    app.router.add_get("/ws/sonar", sonar_socket)
    app.cleanup_ctx.append(lifecycle)
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
    (directory / "sonar-config.json").write_text(json.dumps({
        "endpoints": ["wss://radio.tr7n7t7.com/ws/sonar"],
        "publisher_keys": {DID: public}, "public_read_only": True,
    }, indent=2))
    return app


if __name__ == "__main__":
    state = Path(os.environ.get("SONAR_STATE_DIR", str(Path.home() / ".local/state/atlantis-sonar")))
    web.run_app(make_app(state), host="127.0.0.1", port=8086, access_log=None)
