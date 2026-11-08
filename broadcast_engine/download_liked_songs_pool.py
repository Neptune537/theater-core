import os
import sys
import json
import re
import yt_dlp

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIKED_JSON = os.path.join(BASE_DIR, "vinyl", "liked_songs_with_yt.json")
MUSIC_DIR = os.path.join(BASE_DIR, "broadcast_engine", "audio_output", "music")
CRATES_FILE = os.path.join(BASE_DIR, "crates.json")

os.makedirs(MUSIC_DIR, exist_ok=True)

def sanitize(name):
    clean = re.sub(r'[^\w\-_.]', '_', name.lower())
    clean = re.sub(r'_+', '_', clean).strip('_')
    return clean[:40]

def populate_liked_library(limit=25):
    print(f"[*] Reading Spotify Liked Songs from {LIKED_JSON}...")
    with open(LIKED_JSON, "r", encoding="utf-8") as f:
        liked_songs = json.load(f)

    print(f"[*] Found {len(liked_songs)} liked songs. Populating default station rotation (top {limit})...")

    # Clean existing non-liked tracks if needed
    for old in ["test_burn.mp3", "test_dl.mp3"]:
        p = os.path.join(MUSIC_DIR, old)
        if os.path.exists(p):
            try: os.remove(p)
            except: pass

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '128'}],
        'quiet': True,
        'no_warnings': True,
    }

    downloaded_tracks = []

    for i, s in enumerate(liked_songs[:limit]):
        title = s.get("title", f"Track {i+1}")
        artist = s.get("artist", "Unknown Artist")
        yt_id = s.get("yt_videoId")
        
        safe_name = f"{i+1:02d}_{sanitize(title)}"
        target_mp3 = os.path.join(MUSIC_DIR, f"{safe_name}.mp3")

        if os.path.exists(target_mp3) and os.path.getsize(target_mp3) > 1000000:
            print(f"[=] ({i+1}/{limit}) Already downloaded: {title} by {artist} ({os.path.getsize(target_mp3)} bytes)")
            downloaded_tracks.append((title, artist, target_mp3, s))
            continue

        url = f"https://www.youtube.com/watch?v={yt_id}" if yt_id else None
        query = [url] if url else [f"ytsearch1:{title} {artist} Audio"]

        print(f"[+] ({i+1}/{limit}) Downloading genuine full audio: '{title}' by {artist}...")
        opts = dict(ydl_opts)
        opts['outtmpl'] = os.path.join(MUSIC_DIR, safe_name) + ".%(ext)s"

        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download(query)
            
            if os.path.exists(target_mp3):
                sz = os.path.getsize(target_mp3)
                print(f"[OK] Downloaded '{title}' ({sz} bytes)")
                downloaded_tracks.append((title, artist, target_mp3, s))
        except Exception as e:
            print(f"[!] Failed to download '{title}': {e}")

    # Remove older placeholder files that are not part of the liked songs
    liked_filenames = set(f"{i+1:02d}_{sanitize(s.get('title'))}.mp3" for i, s in enumerate(liked_songs[:limit]))
    for f in os.listdir(MUSIC_DIR):
        if f.endswith(".mp3") and f not in liked_filenames and not f.startswith("host_"):
            try:
                os.remove(os.path.join(MUSIC_DIR, f))
            except Exception:
                pass

    print(f"\n[DONE] Successfully populated {len(downloaded_tracks)} full-length Spotify Liked tracks as default!")

    # UPDATE crates.json to feature Liked Songs as default first crate
    try:
        existing_crates = []
        if os.path.exists(CRATES_FILE):
            with open(CRATES_FILE, "r", encoding="utf-8") as cf:
                existing_crates = json.load(cf)

        # Filter out old liked songs entries if any
        other_crates = [c for c in existing_crates if c.get("source") != "💚 Liked Songs (Favorites)"]

        liked_crate_items = []
        for s in liked_songs:
            liked_crate_items.append({
                "title": s.get("title"),
                "artist": s.get("artist"),
                "bpm": s.get("bpm", "124.0"),
                "source": "💚 Liked Songs (Favorites)",
                "album": "Spotify Liked Songs",
                "spotify_id": s.get("yt_videoId", ""),
                "cover_url": "https://image-cdn-fa.spotifycdn.com/image/ab67616d00001e02ccdddd46119a4ff53eaf1f5d",
                "spotify_url": s.get("url", ""),
                "spotify_embed_url": ""
            })

        full_crates = liked_crate_items + other_crates
        with open(CRATES_FILE, "w", encoding="utf-8") as cf:
            json.dump(full_crates, cf, indent=2)
        print(f"[CRATES] Added {len(liked_crate_items)} Liked Songs to top of crates.json! Total tracks: {len(full_crates)}")
    except Exception as e:
        print(f"[!] Error updating crates.json: {e}")

if __name__ == "__main__":
    populate_liked_library(limit=25)
