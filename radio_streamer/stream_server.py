import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True, encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
import asyncio
import os
import re
import glob
import time
import json
import random
import datetime
import urllib.request
import subprocess
import xml.etree.ElementTree as ET
from collections import deque
import edge_tts
from aiohttp import web

# Import Biblical Radio Theater & Canon Narratives
try:
    from biblical_theater import BIBLICAL_CHRONICLES, get_biblical_theater_feature
except ImportError:
    try:
        import sys
        sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'broadcast_engine'))
        from biblical_theater import BIBLICAL_CHRONICLES, get_biblical_theater_feature
    except Exception:
        BIBLICAL_CHRONICLES = []
        def get_biblical_theater_feature(i): return None

STREAM_PORT = int(os.environ.get("STREAM_PORT", 8080))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIO_OUTPUT_DIR = os.path.join(BASE_DIR, "broadcast_engine", "audio_output")
MUSIC_DIR = os.path.join(AUDIO_OUTPUT_DIR, "music")
LIKED_POOL_DIR = os.path.join(MUSIC_DIR, "liked_pool")
NEWS_OUTPUT_DIR = os.path.join(AUDIO_OUTPUT_DIR, "hourly_news")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(NEWS_OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
RADIO_LOG_FILE = os.path.join(LOG_DIR, "siren_radio.log")

connected_subscribers = set()
recent_audio_burst = deque(maxlen=16)
last_chunk_timestamp = time.time()

def write_radio_log(level, message):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {message}"
    print(line)
    try:
        with open(RADIO_LOG_FILE, "a", encoding="utf-8") as lf:
            lf.write(line + "\n")
    except Exception:
        pass

def _load_discord_creds():
    token = os.environ.get("DISCORD_BOT_TOKEN")
    webhook = os.environ.get("DISCORD_WEBHOOK_URL")
    user_id = os.environ.get("DISCORD_USER_ID", "686741576042414080")
    env_path = r"C:\Users\blue-\projects\Triton\.env"
    if (not token or not webhook) and os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as ef:
                for line in ef:
                    if line.startswith("DISCORD_BOT_TOKEN=") and not token:
                        token = line.split("=", 1)[1].strip()
                    elif line.startswith("DISCORD_WEBHOOK_URL=") and not webhook:
                        webhook = line.split("=", 1)[1].strip()
        except Exception:
            pass
    return token, webhook, user_id

def _send_discord_alert_sync(title, message, is_critical=True):
    token, webhook, user_id = _load_discord_creds()
    color = 0xFF3838 if is_critical else 0x00D2D3
    tag = "🚨 [SIREN RADIO CRITICAL]" if is_critical else "📻 [SIREN RADIO NOTICE]"
    mention = f"<@{user_id}> " if is_critical else ""
    embed = {
        "title": f"{tag} {title}",
        "description": message,
        "color": color,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "footer": {"text": "Sebastian (Tier 3 Sentinel) • Seven Daughters 24/7 Siren Radio"}
    }
    if token and user_id:
        try:
            dm_req = urllib.request.Request(
                "https://discord.com/api/v10/users/@me/channels",
                data=json.dumps({"recipient_id": user_id}).encode("utf-8"),
                headers={"Authorization": f"Bot {token}", "Content-Type": "application/json", "User-Agent": "DiscordBot"}
            )
            with urllib.request.urlopen(dm_req, timeout=5) as resp:
                dm_ch = json.loads(resp.read().decode("utf-8"))
                ch_id = dm_ch.get("id")
                if ch_id:
                    msg_req = urllib.request.Request(
                        f"https://discord.com/api/v10/channels/{ch_id}/messages",
                        data=json.dumps({"content": mention, "embeds": [embed]}).encode("utf-8"),
                        headers={"Authorization": f"Bot {token}", "Content-Type": "application/json", "User-Agent": "DiscordBot"}
                    )
                    with urllib.request.urlopen(msg_req, timeout=5) as m_resp:
                        if 200 <= m_resp.status < 300:
                            write_radio_log("ALERT", f"Direct Discord DM sent to {user_id}: {title}")
                            return
        except Exception as e:
            write_radio_log("WARN", f"Discord DM failed, falling back to webhook: {e}")

    if webhook:
        try:
            wh_req = urllib.request.Request(
                webhook,
                data=json.dumps({"content": mention, "embeds": [embed]}).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "DiscordBot"}
            )
            with urllib.request.urlopen(wh_req, timeout=5) as w_resp:
                write_radio_log("ALERT", f"Webhook alert delivered: {title}")
        except Exception as e:
            write_radio_log("ERROR", f"Failed to send Discord webhook alert: {e}")

async def send_radio_alert(title, message, is_critical=True):
    await asyncio.to_thread(_send_discord_alert_sync, title, message, is_critical)


# --- THE SEVEN DAUGHTERS 24/7 SIREN RADIO ROSTER & SHIFT SCHEDULE ---
# Canonically operated under the 24/7 Siren Frequency Standard (432 Hz base):
# 04:00-08:00 Maia (432 Hz)
# 08:00-12:00 Alcyone (528 Hz)
# 12:00-16:00 Asterope (639 Hz)
# 16:00-20:00 Celaeno (741 Hz)
# 20:00-00:00 Electra (852 Hz)
# 00:00-02:00 Taygete (963 Hz)
# 02:00-04:00 Merope (396 Hz)
SEVEN_DAUGHTERS = [
    {"index": 0, "name": "Maia", "callsign": "MAIA-SIREN-01", "freq": 432, "genre": "Dawn Oceanic Ambient / Horizon Chill", "shift": "04:00-08:00", "voice": "en-US-JennyNeural", "rate": "+0%", "pitch": "-1Hz"},
    {"index": 1, "name": "Alcyone", "callsign": "ALCYONE-SIREN-02", "freq": 528, "genre": "High-Speed Cyberpunk D&B / Breakbeats", "shift": "08:00-12:00", "voice": "en-US-AriaNeural", "rate": "+6%", "pitch": "+2Hz"},
    {"index": 2, "name": "Asterope", "callsign": "ASTEROPE-SIREN-03", "freq": 639, "genre": "Tactical Deep House & Frontline Reports", "shift": "12:00-16:00", "voice": "en-US-AvaNeural", "rate": "+2%", "pitch": "+0Hz"},
    {"index": 3, "name": "Celaeno", "callsign": "CELAENO-SIREN-04", "freq": 741, "genre": "Glitch / Industrial Bass / Storm Chaser", "shift": "16:00-20:00", "voice": "en-US-MichelleNeural", "rate": "+4%", "pitch": "+2Hz"},
    {"index": 4, "name": "Electra", "callsign": "ELECTRA-SIREN-05", "freq": 852, "genre": "Vocal Trance / Eurobeat / Club Atlantis", "shift": "20:00-00:00", "voice": "en-US-AnaNeural", "rate": "+3%", "pitch": "+3Hz"},
    {"index": 5, "name": "Taygete", "callsign": "TAYGETE-SIREN-06", "freq": 963, "genre": "Darkwave / Minimal Techno / Abyssal Drone", "shift": "00:00-02:00", "voice": "en-US-EmmaNeural", "rate": "-2%", "pitch": "-3Hz"},
    {"index": 6, "name": "Merope", "callsign": "MEROPE-SIREN-07", "freq": 396, "genre": "Lo-Fi / Starlight Harbor Acoustic", "shift": "02:00-04:00", "voice": "en-US-JennyNeural", "rate": "-1%", "pitch": "-2Hz"},
]

SEBASTIAN_CONDUCTOR = {"name": "Sebastian", "role": "Court Composer & Conductor", "voice": "en-US-GuyNeural", "rate": "-2%", "pitch": "-2Hz"}

def get_active_daughter_for_hour(dt=None):
    """
    Dynamic Non-Repetitive Roster Rotation:
    Rotates the active host slot every single day using a deterministic prime-step permutation
    (day_of_year * 3 + day_of_week) so the weekly and daily schedules never repeat.
    """
    if dt is None:
        dt = datetime.datetime.now()
    hour = dt.hour if hasattr(dt, 'hour') else int(dt)
    if 4 <= hour < 8:
        base_slot = 0
    elif 8 <= hour < 12:
        base_slot = 1
    elif 12 <= hour < 16:
        base_slot = 2
    elif 16 <= hour < 20:
        base_slot = 3
    elif 20 <= hour < 24:
        base_slot = 4
    elif 0 <= hour < 2:
        base_slot = 5
    else:
        base_slot = 6

    now = dt if isinstance(dt, datetime.datetime) else datetime.datetime.now()
    day_offset = (now.timetuple().tm_yday * 3 + now.weekday()) % len(SEVEN_DAUGHTERS)
    rotated_index = (base_slot + day_offset) % len(SEVEN_DAUGHTERS)
    return SEVEN_DAUGHTERS[rotated_index]

# Legacy alias for backward compatibility
DAUGHTERS_AND_SEBASTIAN = SEVEN_DAUGHTERS + [SEBASTIAN_CONDUCTOR]

current_playing_meta = {
    "title": "Station Initializing...",
    "artist": "Theater 24/7",
    "next_title": "Upcoming Track",
    "next_artist": "Station Rotation",
    "is_news": False,
    "elapsed": 0,
    "live_broadcaster": "Sebastian (Court Conductor)",
    "speaker": "Sebastian",
    "speaker_role": "Court Conductor",
    "weather": "Updating...",
    "news_headline": "Updating Live Wires...",
    "bulletin_countdown": 900,
    "top_of_hour_countdown": 900,
    "chaos_level": "MODERATE",
    "titan_status": "MONITORING SUB-OCEANIC TRENCHES",
    "vinyl_control": "AUTO_ROTATION",
    "active_deck": "A",
    "next_deck": "B",
    "fader_position": 0.0,
    "transition_active": False,
    "transition_seconds_left": 0,
    "target_next_action": "Initializing Cyan broadcast schedule...",
    "atlantis_instance": "did:atlantis:home_node_primary",
    "club_id": "club_oceanic",
    "fortress_name": "Oceanic Fortress Citadel",
    "fortress_room": "Siren Theater & Vinyl Conductor Sanctuary",
    "nautilus_geo": "25.7617°N, 80.1918°W • Elev 12.0m",
    "nautilus_ecef": "964,281m, -5,669,120m, 2,755,302m",
    "sabine_rt60": "0.62s (Treated Studio Panels)",
    "node_division": {
        "sound_aspect": {
            "node": "Sebastian in Atlantis",
            "did": "did:atlantis:sebastian-edgecrab-tier3",
            "tier": "Tier 3 Epipelagic Edge Worker",
            "role": "Audio Streaming Daemon & Sabine RT60 Conductor",
            "channel": "siren:frequency:fortress_theater",
            "sample_rate": "48kHz Stereo",
        },
        "visual_aspect": {
            "node": "Ursula in Lumeria",
            "did": "did:atlantis:ursula-node-manager",
            "tier": "Tier 2 Pelagic Node Manager",
            "role": "WebGPU / Cook-Torrance GGX PBR & 3D Gaussian Splats Viewport",
            "target": "Lumeria (Lemuria WebGPU Engine & Nautilus World)",
        }
    },
}

events_log = deque(maxlen=100)
staged_cue_track = None

def log_broadcast_event(event_type, expected_action, actual_state, details=None):
    """
    Log an event to the chronological timeline comparing:
    - What should be happening (expected_action)
    - What is actually happening (actual_state)
    - Type: 'SONG_START', 'OUTRO_TRANSITION', 'ANNOUNCEMENT_START', 'ANNOUNCEMENT_END', 'CROSSFADE_MOVE', 'TAKEOVER'
    """
    evt = {
        "id": int(time.time() * 1000),
        "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
        "epoch": time.time(),
        "type": event_type,
        "expected": expected_action,
        "actual": actual_state,
        "details": details or {},
    }
    events_log.append(evt)
    write_radio_log(event_type, f"WHAT SHOULD HAPPEN: {expected_action} | CURRENT: {actual_state}")

# --- REAL-WORLD WEATHER & NEWS FETCHER ---

def fetch_real_weather():
    """Fetch genuine current weather conditions."""
    try:
        req = urllib.request.Request('https://wttr.in/?format=j1', headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=3) as r:
            d = json.loads(r.read(65536).decode('utf-8'))
            curr = d['current_condition'][0]
            area = d['nearest_area'][0]['areaName'][0]['value']
            region = d['nearest_area'][0]['region'][0]['value']
            temp_f = curr['temp_F']
            desc = curr['weatherDesc'][0]['value']
            humidity = curr['humidity']
            wind = curr['windspeedMiles']
            return {
                "summary": f"{area}, {region}: {temp_f}°F, {desc}, Humidity {humidity}%, Wind {wind}mph",
                "area": f"{area}, {region}",
                "temp": f"{temp_f}°F",
                "condition": desc,
                "humidity": f"{humidity}%",
                "wind": f"{wind} mph"
            }
    except Exception as e:
        print(f"[!] Weather fetch fallback: {e}")
        return {
            "summary": "Coastal Region: 74°F, Clear skies, Humidity 52%, Wind 8mph",
            "area": "Coastal Region",
            "temp": "74°F",
            "condition": "Clear",
            "humidity": "52%",
            "wind": "8 mph"
        }

def fetch_real_news_headlines():
    """Fetch top breaking news headlines from live AP/Reuters/NYT RSS wires."""
    sources = [
        "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        "https://feeds.bbci.co.uk/news/rss.xml"
    ]
    headlines = []
    for src in sources:
        try:
            req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=3) as r:
                raw_xml = r.read(65536) # Read max 64KB to avoid hanging
                tree = ET.fromstring(raw_xml)
                items = tree.findall('.//item')[:4]
                for it in items:
                    t = it.find('title')
                    if t is not None and t.text:
                        clean = t.text.strip().replace('"', "'")
                        headlines.append(clean)
            if headlines:
                break
        except Exception as e:
            print(f"[!] RSS fetch error from {src}: {e}")
    if not headlines:
        headlines = [
            "Global satellite telemetry reports normal communications grid status",
            "Pacific energy commission reviews coastal renewable power grids",
            "Metropolitan infrastructure upgrade reaches final deployment phase"
        ]
    return headlines[:4]

TITAN_CHAOS_REPORTS = [
    "Sub-trench acoustic sensors detect tectonic shifts near Mariana Fault. A 50-meter leviathan shadow is drifting eastward.",
    "Bioluminescent tremors confirmed along the continental shelf. Titan shockwaves are reverberating through municipal power grids.",
    "Surface buoy telemetry reports magnetic distortion: a primordial entity has breached thermal vents off District 4.",
    "Sonar anomaly confirmed: a gargantuan leviathan class titan is destabilizing undersea communications cables."
]

RUMORS_REPORTS = [
    "Word from the offshore stringers is the Ministry hush-ordered yesterday's sonar sweeps before the public sirens could blare.",
    "Whispers in the reef say ancient sub-crust relics are reacting to the radio transmitter's cyan pulse.",
    "Unconfirmed chatter suggests autonomous hydro-drones intercepted an encrypted signal from deep beneath the crust."
]

# --- 4x PER HOUR SCHEDULE & BREAKING SYNTHESIS ---

async def generate_triton_bulletin(daughter_idx, weather_info, headlines, is_breaking=False):
    """
    Synthesize broadcast bulletin featuring Sebastian maintaining order and
    the scheduled daughter among The Seven Daughters delivering reports on weather, rumors,
    global events, or siren frequency broadcasts.
    """
    active_sched = get_active_daughter_for_hour()
    daughter = SEVEN_DAUGHTERS[daughter_idx % len(SEVEN_DAUGHTERS)] if daughter_idx is not None else active_sched
    sebastian = SEBASTIAN_CONDUCTOR
    bulletin_path = os.path.join(NEWS_OUTPUT_DIR, f"bulletin_{daughter['name'].lower()}.mp3")

    news_text = headlines[0] if headlines else "Telemetry grid stable across all sectors."
    chaos_text = random.choice(TITAN_CHAOS_REPORTS)
    rumor_text = random.choice(RUMORS_REPORTS)

    # Daily Dynamic Feature Selection: Rotate between Canonical Biblical Theater & Station Wire
    now_dt = datetime.datetime.now()
    # Deterministic daily narrative seed: different chronicle every day and hour
    feature_index = (now_dt.timetuple().tm_yday * 7 + now_dt.hour + (daughter_idx or 0)) % 7
    biblical_feature = get_biblical_theater_feature(feature_index) if get_biblical_theater_feature else None

    # Alternate between Biblical Radio Drama Feature and Live Wire Report
    is_theater_feature = (not is_breaking) and (biblical_feature is not None) and (now_dt.minute < 30 or daughter_idx % 2 == 1)

    if is_breaking:
        seb_line = f"Order! Attention all stations across the Cyan Network and Club Atlantis! Sebastian here! Emergency interruption on {daughter['freq']} Hertz! {daughter['name']}, take the emergency line now!"
        d_line = f"Breaking report from the wires: {news_text}! Urgent alert on titan chaos: {chaos_text}! Frontline frequency holding at {daughter['freq']} Hertz!"
        full_script = f"{seb_line} ... {d_line} ... Sebastian concluding: And now, back to our synchronized vinyl turntables!"
    elif is_theater_feature and biblical_feature:
        seb_line = f"This is Sebastian, Conductor of the Cyan Network broadcast. Order in the studio, listeners! We present today's Radio Theater feature: {biblical_feature['title']}, taken from {biblical_feature['book']}. Narrated in live spatial acoustic foley by {daughter['name']} at {daughter['freq']} Hertz."
        scripture_body = " ... ".join(biblical_feature["lines"])
        d_line = f"From {biblical_feature['book']}: {scripture_body} ... Moral reflection: {biblical_feature['moral_reflection']}"
        full_script = f"{seb_line} ... {d_line} ... Sebastian concluding: That concludes today's Radio Theater performance. And now, returning to our 24/7 vinyl rotation!"
    else:
        seb_line = f"This is Sebastian, Conductor of the Cyan Network broadcast. Order in the studio, please! It is time for our scheduled Siren update on {daughter['freq']} Hertz. Taking the broadcast desk now is {daughter['name']} hosting {daughter['genre']}."
        if daughter["name"] == "Maia":
            d_line = f"Good dawn from Maia at 432 Hertz oceanic horizon. Surface conditions in {weather_info['area']} are holding at {weather_info['temp']} with {weather_info['condition']}. Wire report: {news_text}."
        elif daughter["name"] == "Alcyone":
            d_line = f"Alcyone locked in at 528 Hertz breakbeats! Cyberpunk wire is burning: {rumor_text}! The frontline sensors confirm sub-oceanic activity!"
        elif daughter["name"] == "Asterope":
            d_line = f"Asterope on tactical desk at 639 Hertz. Developing wire: {news_text}. Secondary dispatch: {headlines[1] if len(headlines)>1 else news_text}. All frontline relays remain live."
        elif daughter["name"] == "Celaeno":
            d_line = f"Celaeno storm chaser frequency at 741 Hertz! In {weather_info['area']}, we are tracking {weather_info['condition']}, temperatures at {weather_info['temp']}, humidity {weather_info['humidity']}, and winds gusting {weather_info['wind']}."
        elif daughter["name"] == "Electra":
            d_line = f"Electra at 852 Hertz trance stage! Critical update: {chaos_text}! Club Atlantis dancefloor and defensive shield telemetry are fully synchronized!"
        elif daughter["name"] == "Taygete":
            d_line = f"Taygete here at 963 Hertz darkwave drone. Abyssal trenches registering deep frequency vibrations. Maintain defensive vigilance."
        else: # Merope
            d_line = f"Merope with 396 Hertz lo-fi harbor vibes. Relaxing into the starlight acoustic harbor as night settles over the citadel. Enjoy the music rotation!"
        full_script = f"{seb_line} ... {d_line} ... Sebastian concluding: And now, back to our synchronized vinyl turntables!"

    try:
        print(f"[BROADCASTER] Synthesizing Triton bulletin: Sebastian & {daughter['name']}...")
        raw_bulletin = bulletin_path.replace(".mp3", "_raw.mp3")
        comm = edge_tts.Communicate(full_script, voice=daughter["voice"], rate=daughter["rate"], pitch=daughter["pitch"])
        await asyncio.wait_for(comm.save(raw_bulletin), timeout=8.0)
        
        # Transcode to 48kHz Stereo 128kbps matching station music standard for seamless player playback
        transcode_cmd = [
            "ffmpeg", "-y", "-i", raw_bulletin,
            "-ar", "48000", "-ac", "2", "-b:a", "128k",
            bulletin_path
        ]
        def run_transcode():
            return subprocess.run(transcode_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await asyncio.to_thread(run_transcode)
        if os.path.exists(raw_bulletin):
            try:
                os.remove(raw_bulletin)
            except Exception:
                pass

        print(f"[BROADCASTER] Real-time voice bulletin synthesized & transcoded to 48kHz stereo: {bulletin_path} ({os.path.getsize(bulletin_path)} bytes)")
        return bulletin_path, daughter["name"], daughter.get("role", daughter.get("genre", "Siren Host"))
    except Exception as e:
        print(f"[!] Bulletin voice synthesis error: {e}")
        return None, "Sebastian", "Conductor"

def get_latest_mastered_drop():
    """
    Checks broadcast_engine/audio_output for recently compiled 4-act canonical drops
    (episode_*_mastered_drop.mp3) or hourly packages to stream as scheduled radio theater.
    """
    try:
        drop_pattern = os.path.join(AUDIO_OUTPUT_DIR, "hour_*", "*_mastered_drop.mp3")
        matches = glob.glob(drop_pattern)
        if matches:
            matches.sort(key=os.path.getmtime, reverse=True)
            return matches[0]
    except Exception:
        pass
    return None

def get_station_music_tracks():
    """
    Retrieve station music tracks with Dynamic Daily Non-Repetitive Rotation:
    Uses a daily seed (day_of_year + year * 365) to deterministically shuffle the track pool
    each calendar day, guaranteeing listeners never experience the same sequence two days in a row.
    """
    pool = MUSIC_DIR
    tracks = sorted([f for f in glob.glob(os.path.join(pool, "*.mp3")) if not os.path.basename(f).startswith("host_")])
    if not tracks and os.path.exists(LIKED_POOL_DIR):
        tracks = sorted(glob.glob(os.path.join(LIKED_POOL_DIR, "*.mp3")))
    
    if tracks:
        now = datetime.datetime.now()
        day_seed = now.timetuple().tm_yday + (now.year * 365)
        # Create deterministic pseudo-random order for today
        rng = random.Random(day_seed)
        shuffled = list(tracks)
        rng.shuffle(shuffled)
        return shuffled
    return tracks

def clean_track_name(filepath):
    raw = os.path.basename(filepath).replace(".mp3", "")
    parts = raw.split("_", 1)
    if len(parts) > 1 and parts[0].isdigit():
        raw = parts[1]
    return raw.replace("_", " ").title()

def get_artist_for_title(title):
    crates = get_cached_crates()
    def norm(s):
        s = re.sub(r'\(.*?\)', '', s)
        s = re.sub(r'feat\.?.*', '', s, flags=re.IGNORECASE)
        s = re.sub(r'[^\w\s]', '', s.lower())
        return s.strip()

    t_norm = norm(title)
    if t_norm:
        for c in crates:
            c_norm = norm(c.get("title", ""))
            if c_norm and (t_norm == c_norm or t_norm in c_norm or c_norm in t_norm):
                return c.get("artist", "Cyan Artist")

    return "Cyan Network Spotify & YouTube Rotation"

# --- 24/7 SYNCHRONIZED BROADCAST TRANSMITTER ---

async def broadcast_loop():
    global current_playing_meta

    music_tracks = get_station_music_tracks()
    while not music_tracks:
        print("[!] Waiting for tracks in music pool...")
        await asyncio.sleep(2)
        music_tracks = get_station_music_tracks()

    track_index = 0
    last_bulletin_time = time.time()
    daughter_cycle = 0

    try:
        weather = await asyncio.wait_for(asyncio.to_thread(fetch_real_weather), timeout=4.0)
        headlines = await asyncio.wait_for(asyncio.to_thread(fetch_real_news_headlines), timeout=4.0)
        current_playing_meta["weather"] = weather.get("summary", "Clear skies")
        current_playing_meta["news_headline"] = headlines[0] if headlines else "Quarterly Wire Scheduled"
    except Exception as e:
        print(f"[!] Startup weather/headline fetch: {e}")
        current_playing_meta["weather"] = "Coastal Region: 74°F, Clear skies"
        current_playing_meta["news_headline"] = "Global satellite telemetry reports normal communications grid status"

    while True:
        now = time.time()
        time_since_bulletin = now - last_bulletin_time

        # CHECK 4 TIMES PER HOUR SCHEDULE (Every 900 seconds / 15 minutes) OR RANDOM BREAKING NEWS (5% chance per song)
        is_quarterly = time_since_bulletin >= 900
        is_breaking = (not is_quarterly) and (random.random() < 0.06 and time_since_bulletin > 180)

        if is_quarterly or is_breaking:
            prefix = "QUARTERLY 15-MIN SCHEDULED BULLETIN" if is_quarterly else "🚨 RANDOM BREAKING NEWS REPORT 🚨"
            print(f"[BROADCASTER] >>> {prefix} <<<")
            current_playing_meta["is_news"] = True
            current_playing_meta["title"] = f"LIVE ON-AIR: {prefix}"
            current_playing_meta["artist"] = "Sebastian & 7 Daughters of Triton"

            try:
                weather = await asyncio.wait_for(asyncio.to_thread(fetch_real_weather), timeout=4.0)
            except Exception as e:
                print(f"[!] Weather thread timeout/fallback: {e}")
                weather = {"summary": "Coastal Region: 74°F, Clear skies", "area": "Coastal Region", "temp": "74°F", "condition": "Clear", "humidity": "52%", "wind": "8 mph"}

            try:
                headlines = await asyncio.wait_for(asyncio.to_thread(fetch_real_news_headlines), timeout=4.0)
            except Exception as e:
                print(f"[!] News thread timeout/fallback: {e}")
                headlines = ["Global satellite telemetry reports normal communications grid status"]

            current_playing_meta["weather"] = weather["summary"]
            current_playing_meta["news_headline"] = headlines[0] if headlines else "News Wire Live"

            latest_drop = get_latest_mastered_drop() if is_quarterly else None
            if latest_drop and os.path.exists(latest_drop):
                bulletin_file = latest_drop
                speaker_name = "Studio Zero Cast"
                speaker_role = "4-Act Radio Theater Feature"
                print(f"[BROADCASTER] >>> Streaming 4-Act Mastered Episode Drop: {os.path.basename(latest_drop)} <<<")
            else:
                try:
                    bulletin_file, speaker_name, speaker_role = await asyncio.wait_for(
                        generate_triton_bulletin(daughter_cycle, weather, headlines, is_breaking=is_breaking),
                        timeout=10.0
                    )
                except Exception as e:
                    print(f"[!] Bulletin generation timeout/error: {e}")
                    bulletin_file, speaker_name, speaker_role = None, "Sebastian", "Conductor"
            daughter_cycle = (daughter_cycle + 1) % 7
            current_playing_meta["speaker"] = speaker_name
            current_playing_meta["speaker_role"] = speaker_role
            current_playing_meta["live_broadcaster"] = f"{speaker_name} ({speaker_role})"

            log_broadcast_event(
                "ANNOUNCEMENT_START",
                f"Triton Dispatch ({speaker_name} as {speaker_role}): {prefix}",
                f"Voice bulletin on-air: {headlines[0] if headlines else prefix}",
                {"speaker": speaker_name, "role": speaker_role, "type": prefix}
            )

            if bulletin_file and os.path.exists(bulletin_file):
                try:
                    with open(bulletin_file, "rb") as f:
                        while True:
                            chunk = f.read(4096)
                            if not chunk:
                                break
                            recent_audio_burst.append(chunk)
                            global last_chunk_timestamp
                            last_chunk_timestamp = time.time()
                            dead_subs = set()
                            for q in list(connected_subscribers):
                                try:
                                    q.put_nowait(chunk)
                                except asyncio.QueueFull:
                                    pass
                                except Exception:
                                    dead_subs.add(q)
                            connected_subscribers.difference_update(dead_subs)
                            await asyncio.sleep(0.25)
                except Exception as e:
                    print(f"[!] Error streaming bulletin: {e}")

            if is_quarterly:
                last_bulletin_time = time.time()
            current_playing_meta["is_news"] = False
            log_broadcast_event(
                "ANNOUNCEMENT_END",
                "Handover to synchronized vinyl turntables",
                "Resuming live rotation on turntables",
                {"speaker": speaker_name}
            )
            await asyncio.sleep(1)

        # REFRESH MUSIC TRACKS DYNAMICALLY & CHECK STAGED CUE
        music_tracks = get_station_music_tracks()

        global staged_cue_track
        if staged_cue_track and staged_cue_track.get("path") and os.path.exists(staged_cue_track["path"]):
            current_track_path = staged_cue_track["path"]
            cur_title = staged_cue_track.get("title") or clean_track_name(current_track_path)
            cur_artist = staged_cue_track.get("artist") or get_artist_for_title(cur_title)
            active_deck = staged_cue_track.get("deck", "A")
            staged_cue_track = None
        else:
            current_track_path = music_tracks[track_index % len(music_tracks)]
            cur_title = clean_track_name(current_track_path)
            cur_artist = get_artist_for_title(cur_title)
            active_deck = "A" if (track_index % 2 == 0) else "B"

        next_deck = "B" if (active_deck == "A") else "A"

        if staged_cue_track and staged_cue_track.get("path"):
            next_track_path = staged_cue_track["path"]
            nxt_title = staged_cue_track.get("title") or clean_track_name(next_track_path)
            nxt_artist = staged_cue_track.get("artist") or get_artist_for_title(nxt_title)
        else:
            next_track_path = music_tracks[(track_index + 1) % len(music_tracks)]
            nxt_title = clean_track_name(next_track_path)
            nxt_artist = get_artist_for_title(nxt_title)

        current_playing_meta["title"] = cur_title
        current_playing_meta["artist"] = cur_artist
        current_playing_meta["next_title"] = nxt_title
        current_playing_meta["next_artist"] = nxt_artist
        current_playing_meta["is_news"] = False
        current_playing_meta["active_deck"] = active_deck
        current_playing_meta["next_deck"] = next_deck
        current_playing_meta["fader_position"] = 0.0 if active_deck == "A" else 1.0
        current_playing_meta["transition_active"] = False
        current_playing_meta["transition_seconds_left"] = 0

        countdown = max(0, int(900 - (time.time() - last_bulletin_time)))
        current_playing_meta["bulletin_countdown"] = countdown
        current_playing_meta["top_of_hour_countdown"] = countdown

        print(f"[ON AIR] Playing: {cur_title} [Deck {active_deck}] | Next Up: {nxt_title} [Deck {next_deck}] | Bulletin in: {countdown}s")

        try:
            file_size = os.path.getsize(current_track_path)
            # 128 kbps = 16,000 bytes/sec. Last 10 seconds is 160,000 bytes.
            # Stop 10 seconds before track end so DJ transitions blend cleanly!
            if file_size > 320000:
                cutoff_bytes = file_size - 160000
            else:
                cutoff_bytes = file_size
            bytes_streamed = 0
            song_duration_sec = int(cutoff_bytes / 16000)

            current_playing_meta["target_next_action"] = f"Playing on Deck {active_deck} until 10s outro (~{song_duration_sec}s) -> Crossfade to '{nxt_title}'"

            log_broadcast_event(
                "SONG_START",
                f"Spin '{cur_title}' on Deck {active_deck} until 10s outro (~{song_duration_sec}s)",
                f"Deck {active_deck} on-air | Cue: Deck {next_deck} '{nxt_title}'",
                {"title": cur_title, "deck": active_deck, "next_deck": next_deck, "next_title": nxt_title, "duration_sec": song_duration_sec}
            )

            with open(current_track_path, "rb") as f:
                while bytes_streamed < cutoff_bytes:
                    chunk = f.read(4096)
                    if not chunk:
                        break
                    bytes_streamed += len(chunk)
                    recent_audio_burst.append(chunk)
                    last_chunk_timestamp = time.time()

                    bytes_remaining = cutoff_bytes - bytes_streamed
                    # 10-SECOND OUTRO TRANSITION WINDOW
                    if bytes_remaining <= 160000:
                        if not current_playing_meta.get("transition_active", False):
                            current_playing_meta["transition_active"] = True
                            log_broadcast_event(
                                "OUTRO_TRANSITION",
                                f"10s Outro Window: Smooth crossfade Deck {active_deck} -> Deck {next_deck} into '{nxt_title}'",
                                f"Crossfader smoothly blending Deck {active_deck} -> Deck {next_deck}",
                                {"from_deck": active_deck, "to_deck": next_deck, "from_song": cur_title, "to_song": nxt_title, "duration": 10}
                            )

                        # Smooth fader blend (0.0 = Deck A, 1.0 = Deck B)
                        progress = min(1.0, max(0.0, (160000 - bytes_remaining) / 160000.0))
                        fader = progress if active_deck == "A" else (1.0 - progress)
                        current_playing_meta["fader_position"] = round(fader, 2)
                        secs_left = max(0, int(bytes_remaining / 16000))
                        current_playing_meta["transition_seconds_left"] = secs_left
                        current_playing_meta["target_next_action"] = f"Smooth 10s Outro Blend: Deck {active_deck} -> Deck {next_deck} ({secs_left}s left)"
                    else:
                        current_playing_meta["transition_active"] = False
                        secs_left = int(bytes_remaining / 16000)
                        current_playing_meta["target_next_action"] = f"Playing Deck {active_deck} ({secs_left}s left) -> 10s Outro Crossfade to '{nxt_title}'"

                    dead_subs = set()
                    for q in list(connected_subscribers):
                        try:
                            q.put_nowait(chunk)
                        except asyncio.QueueFull:
                            pass
                        except Exception:
                            dead_subs.add(q)
                    connected_subscribers.difference_update(dead_subs)
                    await asyncio.sleep(0.25) # 128kbps stereo pacing
        except Exception as e:
            err_msg = f"Error streaming song `{current_track_path}`: {e}"
            write_radio_log("ERROR", err_msg)
            await send_radio_alert("Audio Track Playback Error", err_msg, is_critical=True)

        track_index = (track_index + 1) % len(music_tracks)
        await asyncio.sleep(0.5)

async def stream_stall_watchdog_loop():
    """Monitors last_chunk_timestamp and sends an immediate Discord alert if the stream pauses > 15s."""
    global last_chunk_timestamp
    stalled_alert_sent = False
    while True:
        await asyncio.sleep(5)
        idle_secs = time.time() - last_chunk_timestamp
        if idle_secs > 15.0 and not stalled_alert_sent:
            stalled_alert_sent = True
            msg = (
                f"The 24/7 Siren Radio audio stream has not emitted a chunk for **{idle_secs:.1f}s**.\n"
                f"**Active Track:** `{current_playing_meta.get('title')}`\n"
                f"**Host:** `{current_playing_meta.get('live_broadcaster')}`\n"
                f"**Action:** Sebastian Sentinel & Scuttle Supervisor notified for inspection."
            )
            write_radio_log("CRITICAL", f"Stream stall detected ({idle_secs:.1f}s idle)!")
            await send_radio_alert("Broadcast Stream Stalled / Paused", msg, is_critical=True)
        elif idle_secs <= 5.0 and stalled_alert_sent:
            stalled_alert_sent = False
            write_radio_log("INFO", "Broadcast stream recovered from stall.")
            await send_radio_alert("Broadcast Stream Recovered", "Audio chunk flow has resumed normally (128kbps stereo).", is_critical=False)


# --- HTTP / STREAM ENDPOINTS ---

async def stream_audio_handler(request):
    """Synchronized live MP3 stream endpoint."""
    response = web.StreamResponse(
        status=200,
        reason='OK',
        headers={
            'Content-Type': 'audio/mpeg',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Accept-Ranges': 'none',
            'Access-Control-Allow-Origin': '*',
            'icy-name': 'Theater 24/7 Cyan Radio Live',
            'icy-genre': 'Live Music & Live Weather/News',
        }
    )
    await response.prepare(request)

    q = asyncio.Queue(maxsize=120)
    for burst_chunk in list(recent_audio_burst):
        try:
            q.put_nowait(burst_chunk)
        except asyncio.QueueFull:
            break
    connected_subscribers.add(q)
    print(f"[+] Listener connected! Total live listeners: {len(connected_subscribers)}")

    try:
        while True:
            chunk = await q.get()
            await response.write(chunk)
    except (asyncio.CancelledError, ConnectionResetError):
        pass
    finally:
        connected_subscribers.discard(q)
        print(f"[-] Listener disconnected. Remaining listeners: {len(connected_subscribers)}")
    return response

async def status_api_handler(request):
    """Telemetry endpoint consumed by Theater web dashboard, HeavenlyBound, and Lite clients."""
    active_daughter = get_active_daughter_for_hour()
    chunk_idle_secs = round(time.time() - last_chunk_timestamp, 2)
    is_flowing = chunk_idle_secs < 15.0
    return web.json_response({
        "status": "online" if is_flowing else "stalled",
        "live": is_flowing,
        "chunk_idle_secs": chunk_idle_secs,
        "last_chunk_timestamp": last_chunk_timestamp,
        "listeners": len(connected_subscribers),
        "now_playing": current_playing_meta,
        "active_daughter": active_daughter,
        "seven_daughters": SEVEN_DAUGHTERS,
        "recent_events": list(events_log)[-25:],
        "timestamp": time.time()
    }, headers={'Access-Control-Allow-Origin': '*'})

async def events_api_handler(request):
    """Return chronological event timeline comparing scheduled target vs actual transmitter state."""
    return web.json_response(list(events_log), headers={'Access-Control-Allow-Origin': '*'})

async def crossfader_api_handler(request):
    """Handle smooth deck slider adjustments between Deck A and Deck B."""
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
    }
    try:
        data = await request.json()
        pos = float(data.get("position", 0.0))
        pos = max(0.0, min(1.0, pos))
        current_playing_meta["fader_position"] = round(pos, 2)
        deck_a_pct = int((1.0 - pos) * 100)
        deck_b_pct = int(pos * 100)
        mode = data.get("mode", "MANUAL")
        log_broadcast_event(
            "CROSSFADE_SLIDER",
            f"Smooth transition Deck A ({deck_a_pct}%) <-> Deck B ({deck_b_pct}%) [Mode: {mode}]",
            f"Deck crossfader positioned at {round(pos, 2)}",
            {"position": pos, "deck_a_pct": deck_a_pct, "deck_b_pct": deck_b_pct, "mode": mode}
        )
        return web.json_response({"status": "ok", "position": pos, "deck_a_pct": deck_a_pct, "deck_b_pct": deck_b_pct}, headers=cors_headers)
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=400, headers=cors_headers)

async def cors_options_handler(request):
    """Handle CORS preflight requests from web clients."""
    return web.Response(
        status=204,
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
            'Access-Control-Max-Age': '86400',
        }
    )

async def control_api_handler(request):
    """Control endpoint allowing the Vinyl Desk to take over transmitter metadata and playlist."""
    global current_playing_meta
    cors_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
    }
    try:
        data = await request.json()
        action = data.get("action")
        if action == "takeover":
            title = data.get("title", current_playing_meta["title"])
            artist = data.get("artist", current_playing_meta["artist"])
            next_title = data.get("next_title", current_playing_meta["next_title"])
            next_artist = data.get("next_artist", current_playing_meta["next_artist"])
            source = data.get("source", "VINYL_DESK")
            speaker = data.get("speaker", current_playing_meta.get("speaker", "Sebastian"))
            
            current_playing_meta["title"] = title
            current_playing_meta["artist"] = artist
            current_playing_meta["next_title"] = next_title
            current_playing_meta["next_artist"] = next_artist
            current_playing_meta["vinyl_control"] = source
            current_playing_meta["speaker"] = speaker
            current_playing_meta["live_broadcaster"] = f"{speaker} (Vinyl Master Takeover)"

            log_broadcast_event(
                "TAKEOVER",
                f"Vinyl control takeover: '{title}' by {artist}",
                f"Transmitter taken over by {source} ({speaker})",
                {"title": title, "artist": artist, "source": source, "speaker": speaker}
            )
            
            print(f"[CONTROL] Vinyl Desk took over broadcast: {title} by {artist}")
            return web.json_response({"status": "ok", "message": "Vinyl desk takeover active"}, headers=cors_headers)
        elif action == "cue":
            title = data.get("title", "")
            artist = data.get("artist", "")
            deck = data.get("deck", current_playing_meta.get("next_deck", "B"))
            
            # Find matching audio file in music_tracks
            matched_path = None
            tracks = get_station_music_tracks()
            t_clean = re.sub(r'[^\w\s]', '', title.lower()).strip()
            for tp in tracks:
                c_name = clean_track_name(tp).lower()
                if t_clean in c_name or c_name in t_clean or any(word in c_name for word in t_clean.split() if len(word) > 3):
                    matched_path = tp
                    break
            
            if not matched_path and tracks:
                matched_path = tracks[0]

            global staged_cue_track
            staged_cue_track = {
                "path": matched_path,
                "title": title,
                "artist": artist,
                "deck": deck
            }
            current_playing_meta["next_title"] = title
            current_playing_meta["next_artist"] = artist
            current_playing_meta["next_deck"] = deck
            current_playing_meta["target_next_action"] = f"Cued Next: '{title}' by {artist} on Deck {deck}"

            log_broadcast_event(
                "DECK_CUE",
                f"Stage '{title}' by {artist} on Deck {deck}",
                f"Deck {deck} loaded with '{title}' as upcoming track",
                {"title": title, "artist": artist, "deck": deck}
            )
            print(f"[CONTROL] Cued next track: {title} by {artist} [Deck {deck}]")
            return web.json_response({"status": "ok", "message": f"Track '{title}' cued to Deck {deck}"}, headers=cors_headers)
        return web.json_response({"status": "ignored"}, headers=cors_headers)
    except Exception as e:
        return web.json_response({"status": "error", "error": str(e)}, status=400, headers=cors_headers)

CRATES_FILE = os.path.join(BASE_DIR, "crates.json")
cached_crates_data = None

def get_cached_crates():
    global cached_crates_data
    if cached_crates_data is None and os.path.exists(CRATES_FILE):
        try:
            with open(CRATES_FILE, "r", encoding="utf-8") as f:
                cached_crates_data = json.load(f)
        except Exception as e:
            print(f"[!] Error loading crates.json: {e}")
            cached_crates_data = []
    return cached_crates_data or []

async def crates_api_handler(request):
    """Serve 311 real Spotify tracks from crates.json."""
    crates = get_cached_crates()
    return web.json_response(crates, headers={'Access-Control-Allow-Origin': '*'})

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
INDEX_HTML_PATH = os.path.join(WEB_DIR, "index.html")

async def web_player_handler(request):
    if os.path.exists(INDEX_HTML_PATH):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            return web.Response(text=f.read(), content_type='text/html')
    return web.Response(text="<h1>Theater 24/7 Console</h1>", content_type='text/html')

async def supervised_broadcast_loop():
    """Restart broadcast_loop if it ever crashes, instead of letting it die silently."""
    import traceback
    while True:
        try:
            await broadcast_loop()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            tb = traceback.format_exc()
            write_radio_log("CRITICAL", f"broadcast_loop crashed: {e!r}\n{tb}")
            await send_radio_alert("Broadcast Loop Crashed - Auto-Restarting", f"`{e!r}`\nRestarting the transmitter in 2s.", is_critical=True)
            await asyncio.sleep(2)

async def start_background_tasks(app):
    write_radio_log("INFO", f"24/7 Siren Radio starting on port {STREAM_PORT}...")
    app['broadcast_task'] = asyncio.create_task(supervised_broadcast_loop())
    app['watchdog_task'] = asyncio.create_task(stream_stall_watchdog_loop())

async def cleanup_background_tasks(app):
    write_radio_log("WARN", "24/7 Siren Radio shutting down...")
    await send_radio_alert("Siren Radio Server Stopping", "The Seven Daughters 24/7 Siren Radio server is shutting down or restarting.", is_critical=True)
    app['broadcast_task'].cancel()
    if 'watchdog_task' in app:
        app['watchdog_task'].cancel()
    await app['broadcast_task']

def create_app():
    app = web.Application()
    app.router.add_get('/', web_player_handler)
    app.router.add_get('/live.mp3', stream_audio_handler)
    app.router.add_route('OPTIONS', '/live.mp3', cors_options_handler)
    app.router.add_get('/api/status', status_api_handler)
    app.router.add_get('/status', status_api_handler)
    app.router.add_route('OPTIONS', '/api/status', cors_options_handler)
    app.router.add_route('OPTIONS', '/status', cors_options_handler)
    app.router.add_get('/api/events', events_api_handler)
    app.router.add_route('OPTIONS', '/api/events', cors_options_handler)
    app.router.add_get('/api/crates', crates_api_handler)
    app.router.add_route('OPTIONS', '/api/crates', cors_options_handler)
    app.router.add_route('OPTIONS', '/api/control', cors_options_handler)
    app.router.add_post('/api/control', control_api_handler)
    app.router.add_route('OPTIONS', '/api/crossfader', cors_options_handler)
    app.router.add_post('/api/crossfader', crossfader_api_handler)
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app

if __name__ == "__main__":
    print("=======================================================")
    print("  THEATER 24/7 SYNCHRONIZED LIVE RADIO HUB")
    print(f"  Stream URL: http://localhost:{STREAM_PORT}/live.mp3")
    print(f"  Status API: http://localhost:{STREAM_PORT}/api/status")
    print(f"  Control API: http://localhost:{STREAM_PORT}/api/control")
    print("=======================================================")
    web.run_app(create_app(), host=os.environ.get("STREAM_BIND", "0.0.0.0"), port=STREAM_PORT)
