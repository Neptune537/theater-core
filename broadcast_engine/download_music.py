import urllib.request
import json
import os

with open(r"c:\Users\blue-\projects\theater\vinyl\real_songs.json") as f:
    songs = json.load(f)

music_dir = r"c:\Users\blue-\projects\theater\broadcast_engine\audio_output\music"
os.makedirs(music_dir, exist_ok=True)

# Remove the old repetitive station ID from the music directory so it doesn't repeat
old_files = ["cyan_chill_beat_01.mp3", "station_id_music.mp3", "lofi_chill_stream.mp3"]
for old in old_files:
    p = os.path.join(music_dir, old)
    if os.path.exists(p):
        os.remove(p)

downloaded_tracks = []
for i, s in enumerate(songs[:6]):
    p_url = s.get("preview_url")
    title = s.get("title", f"Track {i+1}")
    artist = s.get("artist", "Artist")
    if p_url:
        fname = f"song_{i+1}.mp3"
        outpath = os.path.join(music_dir, fname)
        print(f"Downloading: {title} by {artist}...")
        req = urllib.request.Request(p_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp, open(outpath, "wb") as out_f:
            out_f.write(resp.read())
        downloaded_tracks.append({
            "title": title,
            "artist": artist,
            "bpm": "124.0",
            "source": "Music Library",
            "filename": fname
        })

print(f"Successfully downloaded {len(downloaded_tracks)} real songs!")
