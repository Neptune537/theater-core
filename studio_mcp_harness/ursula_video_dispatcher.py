"""
Ursula Video & 3D Spatial Dispatcher (Team 7 Video Producer)
=============================================================
Bridges Triton's Lore & Weather script generator with Ursula's creative pipeline:
- Ingests Triton Storyteller JSON dispatches (dialogue, weather, lore, active daughter)
- Synthesizes ComfyUI generative video prompts (Wan2.1 / CogVideoX) with character styling
- Controls Blender 3D spatial scene staging via the Studio MCP Bridge (Port 9988)
- Prepares spatial acoustic tags and camera keyframe plans for Lemuria / HeavenlyBound
"""

import os
import sys
import json
import socket
import argparse
from datetime import datetime

# Daughter Visual & Aesthetic Styling Matrix
DAUGHTER_AESTHETICS = {
    "Maia": {
        "freq": 432,
        "style": "Oceanic horizon, sunrise pastel ambient lighting, bioluminescent coral, ethereal flowing silk dress, dawn mist, hyperrealistic 8k anime concept art",
        "camera": "Smooth slow pan across ocean surface towards rising sun, 35mm cinematic lens",
        "blender_emitter_loc": [0.0, 1.5, 0.0]
    },
    "Alcyone": {
        "freq": 528,
        "style": "High-speed cyberpunk skyline, neon cyan and magenta lens flares, breakbeat visual pulses, futuristic techwear visor, holographic monitors, octane render 8k",
        "camera": "Dynamic Dutch angle, fast orbital camera spin with motion blur, 24mm wide angle",
        "blender_emitter_loc": [2.5, 1.8, 1.0]
    },
    "Asterope": {
        "freq": 639,
        "style": "Tactical deep ocean research station, holographic HUD overlays, frontline sonar radar displays, dark metallic armor with cyan trim, cinematic dramatic lighting",
        "camera": "Tactical tracking shot behind glass bulkhead, slow dolly zoom, 50mm portrait lens",
        "blender_emitter_loc": [-2.0, 1.5, 0.5]
    },
    "Celaeno": {
        "freq": 741,
        "style": "Vortex storm chaser, electrical lightning arcing through Karman clouds, industrial bass vibration ripples, tactical pilot jacket, stormy weather, volumetric fog",
        "camera": "Handheld visceral camera shake, tracking lightning strikes in storm clouds, 28mm lens",
        "blender_emitter_loc": [0.0, 2.2, -1.5]
    },
    "Electra": {
        "freq": 852,
        "style": "Club Atlantis abyssal rave, lasers refracting through underwater dome, vocal trance energy rings, glowing iridescent wings, vibrant euphoric atmosphere",
        "camera": "Crane shot descending into crowded holographic dancefloor, 16mm ultra-wide",
        "blender_emitter_loc": [1.5, 1.6, -1.0]
    },
    "Taygete": {
        "freq": 963,
        "style": "Deep abyssal trench, obsidian monoliths, minimal techno stark contrast, deep ocean pressure waves, bioluminescent deep-sea flora, monochromatic with subtle cyan",
        "camera": "Slow creeping vertical ascent out of black abyss, shallow depth of field, 85mm anamorphic",
        "blender_emitter_loc": [0.0, 1.2, 3.0]
    },
    "Merope": {
        "freq": 396,
        "style": "Starlight harbor, peaceful midnight port, lo-fi warm lantern glow, acoustic wooden pier, gentle water reflections, cozy aesthetic, anime Ghibli inspired 8k",
        "camera": "Static gentle breathing camera looking over quiet harbor waters, 50mm lens",
        "blender_emitter_loc": [-1.5, 1.4, -2.0]
    }
}

class UrsulaVideoDispatcher:
    def __init__(self, mcp_host="127.0.0.1", mcp_port=9988):
        self.mcp_host = mcp_host
        self.mcp_port = mcp_port

    def build_comfy_video_prompt(self, script_payload):
        """Translate Triton's script payload into an actionable ComfyUI text-to-video / image-to-video prompt."""
        daughter_info = script_payload.get("active_daughter", {})
        d_name = daughter_info.get("name", "Celaeno")
        aesthetic = DAUGHTER_AESTHETICS.get(d_name, DAUGHTER_AESTHETICS["Celaeno"])
        
        city = script_payload.get("target_city", "Orlando")
        weather = script_payload.get("weather_bulletin", "Clear")
        headline = script_payload.get("headline_context", "")

        prompt = {
            "workflow": "Wan2.1_T2V_720p_24fps",
            "character": d_name,
            "frequency_hz": aesthetic["freq"],
            "positive_prompt": (
                f"{d_name}, Seraphic anime avatar of the Forgotten Angels, {aesthetic['style']}. "
                f"Setting in planetary sector near {city} with meteorological conditions: {weather}. "
                f"Global broadcast narrative: {headline}. Masterpiece, highly detailed, expressive motion, 24fps smooth."
            ),
            "negative_prompt": (
                "low quality, blurry, deformed anatomy, extra limbs, bad eyes, jitter, artifacting, static image, text, watermark"
            ),
            "camera_directive": aesthetic["camera"],
            "seed": int(datetime.now().timestamp()) % 10000000,
            "frames": 120,
            "fps": 24,
            "audio_sync": {
                "sample_rate": 48000,
                "dialogue_text": script_payload.get("dialogue_lines", {}).get("daughter_report", "")
            }
        }
        return prompt

    def send_blender_command(self, action, params=None):
        """Send command to Blender 3D via Studio MCP Socket (Port 9988)."""
        cmd = {"action": action, "params": params or {}}
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)
                s.connect((self.mcp_host, self.mcp_port))
                s.sendall(json.dumps(cmd).encode('utf-8'))
                response = s.recv(4096)
                return json.loads(response.decode('utf-8'))
        except ConnectionRefusedError:
            return {"status": "offline", "message": f"Blender MCP socket {self.mcp_host}:{self.mcp_port} not listening (Blender not currently open)."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def stage_3d_acoustic_scene(self, script_payload):
        """Stage 3D sound emitters and materials in Blender for acoustic rendering."""
        d_name = script_payload.get("active_daughter", {}).get("name", "Celaeno")
        aesthetic = DAUGHTER_AESTHETICS.get(d_name, DAUGHTER_AESTHETICS["Celaeno"])
        loc = aesthetic["blender_emitter_loc"]

        # Position sound emitter for the Daughter
        res_emitter = self.send_blender_command("create_emitter", {
            "name": f"Emitter_Daughter_{d_name}",
            "location": loc,
            "emitter_type": f"siren_radio_{d_name.lower()}"
        })

        # Position Sebastian Conductor emitter
        res_seb = self.send_blender_command("create_emitter", {
            "name": "Emitter_Sebastian_Conductor",
            "location": [0.0, 1.7, 1.0],
            "emitter_type": "sebastian_conductor"
        })

        return {
            "daughter_emitter": res_emitter,
            "conductor_emitter": res_seb,
            "staged_location": loc
        }

    def dispatch_full_production(self, script_payload):
        """Execute complete Ursula video & 3D staging workflow from a Triton script payload."""
        comfy_prompt = self.build_comfy_video_prompt(script_payload)
        blender_stage = self.stage_3d_acoustic_scene(script_payload)

        production_package = {
            "timestamp_iso": datetime.now().isoformat(),
            "producer": "Ursula Tier-2 Video Producer",
            "daughter": script_payload.get("active_daughter", {}).get("name"),
            "comfyui_generation_payload": comfy_prompt,
            "blender_spatial_stage": blender_stage,
            "status": "QUEUED_FOR_RENDER"
        }
        return production_package

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ursula Video & 3D Spatial Dispatcher")
    parser.add_argument("--script-json", help="Path to input Triton script JSON")
    args = parser.parse_args()

    dispatcher = UrsulaVideoDispatcher()

    if args.script_json and os.path.exists(args.script_json):
        with open(args.script_json, "r", encoding="utf-8") as f:
            script_data = json.load(f)
    else:
        # Default test payload
        script_data = {
            "active_daughter": {"name": "Celaeno", "freq": 741, "genre": "Glitch / Industrial Bass"},
            "target_city": "Orlando",
            "weather_bulletin": "Sunny, crisp and clear, 65°F",
            "headline_context": "Global Electronic Music hubs expanding direct spatial and visual creator integration",
            "dialogue_lines": {
                "daughter_report": "Greetings from Celaeno hosting Glitch / Industrial Bass / Storm Chaser. Ground sensors in Orlando report 65°F."
            }
        }

    pkg = dispatcher.dispatch_full_production(script_data)
    print(json.dumps(pkg, indent=2))
