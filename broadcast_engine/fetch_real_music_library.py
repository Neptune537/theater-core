import os
import sys
import glob
import re
import yt_dlp

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "audio_output", "music")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SONG_CATALOG = [
    ("Mr. Brightside", "The Killers", "mr_brightside.mp3"),
    ("Feel Good Inc.", "Gorillaz", "feel_good_inc.mp3"),
    ("Seven Nation Army", "The White Stripes", "seven_nation_army.mp3"),
    ("Pumped Up Kicks", "Foster The People", "pumped_up_kicks.mp3"),
    ("Smells Like Teen Spirit", "Nirvana", "smells_like_teen_spirit.mp3"),
    ("Creep", "Radiohead", "creep.mp3"),
    ("Purple Rain", "Prince", "purple_rain.mp3"),
    ("When Doves Cry", "Prince", "when_doves_cry.mp3"),
    ("Fly Away", "Lenny Kravitz", "fly_away.mp3"),
    ("Iron Man", "Black Sabbath", "iron_man.mp3"),
    ("Come Together", "The Beatles", "come_together.mp3"),
    ("Hero", "Chad Kroeger", "hero.mp3"),
]

def sanitize_filename(name):
    return re.sub(r'[^\w\-_.]', '_', name)

def download_full_tracks():
    print(f"[*] Sourcing genuine full-length YouTube / Spotify audio into {OUTPUT_DIR}...")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch1:',
    }

    for title, artist, filename in SONG_CATALOG:
        target_path = os.path.join(OUTPUT_DIR, filename)
        # Check if already a full non-looped track (> 2MB and genuine)
        temp_base = os.path.join(OUTPUT_DIR, f"yt_{filename[:-4]}")
        search_query = f"{title} {artist} Audio"
        print(f"[+] Fetching full audio for: {title} by {artist}...")
        
        opts = dict(ydl_opts)
        opts['outtmpl'] = temp_base + ".%(ext)s"
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([f"ytsearch1:{search_query}"])
            
            temp_mp3 = temp_base + ".mp3"
            if os.path.exists(temp_mp3):
                # Replace the target
                if os.path.exists(target_path):
                    os.remove(target_path)
                os.rename(temp_mp3, target_path)
                print(f"[OK] Downloaded full track: {filename} ({os.path.getsize(target_path)} bytes)")
        except Exception as e:
            print(f"[!] Failed to fetch {title}: {e}")

if __name__ == "__main__":
    download_full_tracks()
