# Studio MCP Harness: AI Agent Bridge for Blender, FL Studio & Live Broadcasts

This directory contains the **Studio MCP Harness**, an AI Model Context Protocol (MCP) server that empowers AI agents to drive **Blender**, **FL Studio**, and your **Radio Theater/Live Ticker** simultaneously.

---

## Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │  AI Agent (Gemini / Claude / Antigrav)│
                      └──────────────────┬───────────────────┘
                                         │ MCP Protocol (stdio)
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    studio-mcp-harness (server.js)    │
                      └───────┬──────────────┬───────────────┘
          JSON/TCP (9988)     │              │     JSON/TCP (9989)
       ┌──────────────────────┘              └──────────────────────┐
       ▼                                                            ▼
┌───────────────┐                                            ┌───────────────┐
│ BLENDER 5.2+  │                                            │ FL STUDIO 2026│
│ (3D Acoustics │                                            │ (Multi-track  │
│  & Positions) │                                            │  Audio/Stems) │
└───────────────┘                                            └───────────────┘
```

---

## 1. Features & Tools Exposed via MCP

| Tool Name | What the AI Can Do |
| :--- | :--- |
| `publish_breaking_news` | Publishes a daily live incident, generates Kenji vs. Dex dialogue, and updates the real-time news ticker. |
| `get_live_ticker` | Inspects currently active breaking news headlines and script events. |
| `blender_add_acoustic_emitter`| Places a 3D audio emitter in Blender (tied to Fluorescent acoustics: anchor, instigator, monster roar, sirens). |
| `blender_get_scene` | Reads scene objects and acoustic material tags (`concrete`, `wood`, `carpet`). |
| `fl_studio_transport` | Controls playback, stop, and mixer volume tracks in FL Studio. |

---

## 2. Setup Guide

### Step 1: Install the Blender Addon
1. Open **Blender 5.2**.
2. Go to **Edit > Preferences > Add-ons**.
3. Click the arrow/install icon and choose:
   `c:\Users\blue-\projects\clapperboard\studio_mcp_harness\blender_mcp_addon.py`
4. Enable the checkbox for **"Studio MCP Harness Bridge"**.
5. In the 3D Viewport sidebar (`N` key), you will see the **"Studio MCP"** tab showing:
   * **MCP Bridge: Active (Port 9988)**
   * **"Add News Rig"** button (instantly spawns Anchor Kenji, Instigator Dex, and Monster Emitters).

### Step 2: Install the FL Studio Bridge
1. Copy `c:\Users\blue-\projects\clapperboard\studio_mcp_harness\device_StudioMCPBridge.py` to your FL Studio hardware/MIDI scripts folder:
   `%USERPROFILE%\Documents\Image-Line\FL Studio\Settings\Hardware\StudioMCPBridge`
2. In FL Studio, open **Options > MIDI Settings** and select the controller script to activate communication on Port 9989.

### Step 3: Registering with your MCP Client / Agent
Add this to your MCP configuration (`mcp_config.json` or `.gemini/antigravity/mcp.json`):

```json
{
  "mcpServers": {
    "studio-harness": {
      "command": "node",
      "args": [
        "c:/Users/blue-/projects/clapperboard/studio_mcp_harness/server.js"
      ]
    }
  }
}
```

---

## 3. Example AI Prompts Supported

* *"A giant tentacled creature just surfaced in Tokyo Bay. Write today's 2-minute dialogue between Kenji and Dex, update the live ticker, and place the monster emitter 25 meters offshore in Blender."*
* *"Start FL Studio playback and balance the news bed so Dex's walkie vocal cuts through cleanly."*
