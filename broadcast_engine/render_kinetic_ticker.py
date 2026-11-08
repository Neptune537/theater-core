import os
import subprocess
import json
import logging
from typing import List, Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("render_kinetic_ticker")

def render_kinetic_news_card(
    headline: str,
    sub_headline: str,
    sector: str,
    output_mp4_path: str,
    duration_sec: float = 6.0,
    width: int = 1080,
    height: int = 1920
) -> str:
    """
    Renders a standalone 9:16 vertical video card with scrolling news ticker graphics
    using an FFmpeg filtergraph (text overlay, glowing cyber backdrop, and ticker ribbon).
    Uses explicit Windows fontfile path to prevent Fontconfig initialization errors.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_mp4_path)), exist_ok=True)
    
    clean_headline = headline.replace("'", "").replace(":", "-").upper()
    clean_sub = sub_headline.replace("'", "").replace(":", "-")
    clean_sec = sector.replace("'", "").upper()

    # Fontfile path for Windows FFmpeg
    font_arg = "fontfile='C\\:/Windows/Fonts/arial.ttf'"

    filter_complex = (
        f"color=c=0x07111a:s={width}x{height}:d={duration_sec}[bg];"
        # Top banner
        f"[bg]drawbox=x=0:y=0:w={width}:h=220:color=0x00d4ff@0.15:t=fill[top_bar];"
        f"[top_bar]drawtext={font_arg}:text='CYAN EMERGENCY BROADCAST // {clean_sec}':"
        f"fontsize=42:fontcolor=0x00ffff:x=(w-text_w)/2:y=120[header];"
        # Center Headline Box
        f"[header]drawbox=x=80:y=650:w={width-160}:h=500:color=0x0d2838@0.85:t=fill[card_bg];"
        f"[card_bg]drawbox=x=80:y=650:w={width-160}:h=500:color=0x00ffff@0.6:t=4[card_border];"
        # Main text inside box
        f"[card_border]drawtext={font_arg}:text='{clean_headline}':"
        f"fontsize=52:fontcolor=0xffffff:x=120:y=720:fix_bounds=true[headline_txt];"
        f"[headline_txt]drawtext={font_arg}:text='{clean_sub}':"
        f"fontsize=36:fontcolor=0x7cd8f5:x=120:y=860:fix_bounds=true[sub_txt];"
        # Bottom Scrolling News Ticker Ribbon
        f"[sub_txt]drawbox=x=0:y={height-180}:w={width}:h=120:color=0x0a1c24@0.95:t=fill[ticker_bar];"
        f"[ticker_bar]drawbox=x=0:y={height-180}:w={width}:h=4:color=0x00e5ff@0.8:t=fill[ticker_line];"
        f"[ticker_line]drawtext={font_arg}:text='*** ALERT- {clean_headline} *** SECTOR- {clean_sec} *** SIREN 432HZ FREQUENCY LIVE *** ':"
        f"fontsize=38:fontcolor=0x00ffcc:y={height-135}:x=w-mod(t*280\\,w+text_w+500)[final]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-filter_complex", filter_complex,
        "-map", "[final]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-t", str(duration_sec),
        "-r", "30",
        output_mp4_path
    ]

    logger.info(f"Rendering kinetic 9:16 teaser card -> {output_mp4_path}")
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    logger.info(f"[OK] Kinetic teaser generated: {output_mp4_path} ({os.path.getsize(output_mp4_path)} bytes)")
    return output_mp4_path

if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "teaser_test.mp4"
    render_kinetic_news_card(
        headline="SUB-TRENCH BREACH CONFIRMED",
        sub_headline="Julian Assault Mech Jules-One deployed to protect refinery pylons.",
        sector="SEC-BRAVO",
        output_mp4_path=out,
        duration_sec=4.0
    )
