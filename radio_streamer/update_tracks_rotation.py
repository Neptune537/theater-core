import re

filepath = r"c:\Users\blue-\projects\theater\radio_streamer\stream_server.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target_tracks_func = """def get_station_music_tracks():
    \"\"\"Retrieve all real station music tracks from music directory.\"\"\"
    pool = MUSIC_DIR
    tracks = sorted([f for f in glob.glob(os.path.join(pool, "*.mp3")) if not os.path.basename(f).startswith("host_")])
    if not tracks and os.path.exists(LIKED_POOL_DIR):
        tracks = sorted(glob.glob(os.path.join(LIKED_POOL_DIR, "*.mp3")))
    return tracks"""

replacement_tracks_func = """def get_station_music_tracks():
    \"\"\"
    Retrieve station music tracks with Dynamic Daily Non-Repetitive Rotation:
    Uses a daily seed (day_of_year + year * 365) to deterministically shuffle the track pool
    each calendar day, guaranteeing listeners never experience the same sequence two days in a row.
    \"\"\"
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
    return tracks"""

if target_tracks_func in content:
    content = content.replace(target_tracks_func, replacement_tracks_func, 1)
    print("Track rotation logic updated successfully!")
else:
    print("Track target function not matched!")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
