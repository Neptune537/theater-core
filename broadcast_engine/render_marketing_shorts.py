"""
Generator for:
1. "The Parting of the Red Sea" (Cinematic Biblical Epic Short)
2. "Kuroshio Gyre Ecosystem" (Tech Platform Promo Short)

Generates Edge-TTS speech, draws crisp typography via Pillow onto an overlay card,
and encodes 9:16 vertical 1080x1920 YouTube Shorts using ffmpeg.
"""

import os
import sys
import asyncio
import subprocess
import edge_tts
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = r"C:\Users\blue-\projects\theater\marketing_output"
os.makedirs(OUT_DIR, exist_ok=True)

RED_SEA_SCRIPT = (
    "Trapped between Pharaoh's elite iron chariots and the crushing depths of the Red Sea. "
    "Two million people had nowhere left to run. "
    "Then Moses lifted his staff over the waters. "
    "All through the night, a violent east wind tore through the abyss, "
    "cleaving the ocean in two and turning the seabed into dry ground. "
    "Towering walls of water stood frozen on their right and left. "
    "Faith does not wait for the path to be easy. "
    "Faith walks forward into the impossible."
)

KUROSHIO_SCRIPT = (
    "What if you could turn a twenty-five dollar Raspberry Pi into a sovereign bank and AI powerhouse? "
    "Introducing the Kuroshio Gyre ecosystem. "
    "Powered by the Atlantis Sovereign Node, open raft consensus, and double-entry Tide Ledger accounting. "
    "Zero mock bypasses. Zero centralized choke-points. "
    "From AAA Rust gaming on the Lemuria WebGPU engine, to 24/7 autonomous radio broadcast. "
    "Run your own sovereign node today with a single command. "
    "Claim your freedom in the digital deep."
)

async def generate_voice(text, voice, out_path, rate="+0%", pitch="+0Hz"):
    print(f"[*] Generating voice with {voice} -> {out_path}...")
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(out_path)
    print(f"[+] Saved voiceover: {out_path}")

def create_graphic_card(card_path, title, subtitle, footer, bg_rgb, accent_rgb):
    img = Image.new("RGBA", (1080, 1920), bg_rgb + (255,))
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 52)
        font_mid = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 32)
        font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 26)
    except Exception:
        font_large = ImageFont.load_default()
        font_mid = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Title Banner
    draw.text((540, 360), title, font=font_large, fill=(255, 255, 255), anchor="mm")
    draw.text((540, 440), subtitle, font=font_mid, fill=accent_rgb, anchor="mm")

    # Decorative frame lines
    draw.line([(140, 490), (940, 490)], fill=accent_rgb, width=2)
    draw.line([(140, 1420), (940, 1420)], fill=(80, 90, 115), width=2)

    # Footer CTA
    draw.text((540, 1480), footer, font=font_small, fill=(200, 210, 230), anchor="mm")

    img.save(card_path)
    print(f"[+] Created title graphic card: {card_path}")

def render_short_video(card_img_path, audio_path, output_mp4, wave_hex="0x00e5ff"):
    print(f"[*] Rendering vertical 1080x1920 video -> {output_mp4}...")
    # Overlay audio-reactive waveform onto the pre-rendered typography card
    filter_desc = (
        f"[1:a]showwaves=s=860x340:mode=cline:colors={wave_hex}:scale=cbrt[wave];"
        f"[0:v][wave]overlay=(W-w)/2:(H-h)/2[outv]"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", card_img_path,
        "-i", audio_path,
        "-filter_complex", filter_desc,
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-tune", "stillimage",
        "-b:v", "3500k",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        output_mp4
    ]
    subprocess.run(cmd, check=True)
    print(f"[+] Successfully rendered: {output_mp4}")

async def main():
    # 1. Red Sea Epic Short
    red_sea_audio = os.path.join(OUT_DIR, "red_sea_voiceover.mp3")
    red_sea_card = os.path.join(OUT_DIR, "red_sea_card.png")
    red_sea_video = os.path.join(OUT_DIR, "parting_of_the_red_sea_short.mp4")

    await generate_voice(RED_SEA_SCRIPT, "en-US-ChristopherNeural", red_sea_audio, rate="-4%", pitch="-2Hz")
    create_graphic_card(
        red_sea_card,
        title="THE PARTING OF THE RED SEA",
        subtitle="EXODUS 14 | FAITH IN THE IMPOSSIBLE",
        footer="SUBSCRIBE FOR CINEMATIC BIBLICAL EPICS",
        bg_rgb=(6, 12, 24),
        accent_rgb=(56, 189, 248)
    )
    render_short_video(red_sea_card, red_sea_audio, red_sea_video, wave_hex="0x38bdf8")

    # 2. Kuroshio Gyre Tech Promo Short
    kuroshio_audio = os.path.join(OUT_DIR, "kuroshio_promo_voiceover.mp3")
    kuroshio_card = os.path.join(OUT_DIR, "kuroshio_card.png")
    kuroshio_video = os.path.join(OUT_DIR, "kuroshio_gyre_promo_short.mp4")

    await generate_voice(KUROSHIO_SCRIPT, "en-US-GuyNeural", kuroshio_audio, rate="+2%", pitch="+1Hz")
    create_graphic_card(
        kuroshio_card,
        title="KUROSHIO GYRE ECOSYSTEM",
        subtitle="ATLANTIS SOVEREIGN NODE | LEMURIA WEBGPU",
        footer="GET STARTED: github.com/Neptune537/atlantis-node",
        bg_rgb=(5, 9, 18),
        accent_rgb=(0, 229, 255)
    )
    render_short_video(kuroshio_card, kuroshio_audio, kuroshio_video, wave_hex="0x00e5ff")

    print("\n" + "=" * 60)
    print("[+] ALL MARKETING SHORTS RENDERED & READY TO POST!")
    print(f"1. Red Sea Epic Short:  {red_sea_video}")
    print(f"2. Kuroshio Tech Promo: {kuroshio_video}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
