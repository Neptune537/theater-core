import urllib.request
import urllib.parse
import json
import os

tracks = [
    ("Mr. Brightside The Killers", "mr_brightside.mp3"),
    ("Feel Good Inc Gorillaz", "feel_good_inc.mp3"),
    ("Seven Nation Army White Stripes", "seven_nation_army.mp3"),
    ("Pumped Up Kicks Foster The People", "pumped_up_kicks.mp3"),
    ("Smells Like Teen Spirit Nirvana", "smells_like_teen_spirit.mp3"),
    ("Creep Radiohead", "creep.mp3"),
    ("Purple Rain Prince", "purple_rain.mp3"),
]

music_dir = r"c:\Users\blue-\projects\theater\broadcast_engine\audio_output\music"
os.makedirs(music_dir, exist_ok=True)

# Remove old synthetic files
for old in ["midnight_harbor_beat.wav", "station_ambient_groove.wav", "song_1.mp3", "song_2.mp3", "song_3.mp3"]:
    p = os.path.join(music_dir, old)
    if os.path.exists(p):
        try:
            os.remove(p)
        except Exception:
            pass

for query, filename in tracks:
    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&entity=song&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            if results and results[0].get("previewUrl"):
                p_url = results[0]["previewUrl"]
                out_path = os.path.join(music_dir, filename)
                p_req = urllib.request.Request(p_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(p_req) as p_resp, open(out_path, "wb") as f:
                    f.write(p_resp.read())
                print(f"Populated: {filename} from {results[0].get('trackName')}")
    except Exception as e:
        print(f"Failed {query}: {e}")
print("Music library ready!")
