# AGENTS.md — Theater 24/7 Broadcast, Cyan Network & Fluorescent Workspace

This document defines the roles, operational boundaries, tooling, and integration contracts for autonomous AI and developer agents working in the **Theater** unified episodic broadcast workspace.

**Workspace Root:** `c:\Users\blue-\projects\theater`

---

## 1. Workspace Hierarchy & Components

| Component / Path | Tech Stack | Role & Responsibility |
| :--- | :--- | :--- |
| **`Theater/`** | Flutter 3.x / Riverpod | **The Unified Master App**: Radio Theater Conductor, Vinyl DJ Turntables, 3D Spatial Radar, Fluoridian Protocol & Live Ticker. |
| **`broadcast_engine/`** | Python 3.13 / Edge-TTS | **24/7 Automated Broadcast Core**: Neural TTS synthesis (`tts_engine.py`) and hourly radio wheel scheduler (`hourly_scheduler.py`). |
| **`radio_streamer/`** | Python / AIOHTTP Stream | **Live Internet Radio Server**: Direct HTTP audio stream (`/live.mp3`) and web player for car/mobile/desktop listeners. |
| **`studio_mcp_harness/`** | Node.js MCP / Python | Model Context Protocol bridge connecting AI agents to Blender 5.2 and FL Studio 2026. |
| **`vinyl/`** | Python / Spotify & YT API | Playlist migration (`pull_playlist.py`) and Spotify OAuth helper (`spotify_auth.py`). |
| **`Fluorescent/`** | Rust (`fluorite_core`), Vulkan / WebGPU | **Official Engine Dependency**: Ray-traced spatial acoustics, Sabine RT60 reverb, Nanite virtual geometry. |
| **`fluoderpod/`** | Flutter / Rust FFI | **Official SDK Dependency**: Cyan Network Riverpod state, client node discovery, hardware telemetry (XR, Auto, Controller). |
| **`tithX/`** | Solana Anchor, Rust, SQLite | **Official Protocol Dependency (Fluoridian)**: Double-entry financial ledger, $10 stake eligibility, and quadratic DAO voting. |
| **`Baton/`** | C++ DSP, JUCE, React | Reference Architecture: Multi-track stem mastering & DSP chains. |
| **`start_theater.bat`** | Windows Batch Script | Master one-click desktop/web, radio streamer, and scheduler launcher. |

---

## 2. Agent Roster & Specializations

### 1. Director & Screenplay Agent (`director-agent`)
* **Role:** Crisis incident creator, narrative pacing, and episode script writer.
* **Responsibilities:**
  - Authors daily crisis storylines (e.g. Kaiju sightings, geomagnetic blackouts, sub-trench breaches).
  - Maintains character dynamics: **Kenji Vance (Calm Studio Anchor)** vs. **Dexter Sloan (Hyper Instigator/Stringer)**.
  - Generates real-time scrolling ticker lines with urgency tags (`INFO`, `WARNING`, `CRITICAL`).
  - Calls `publish_breaking_news` on the Studio MCP Harness.

### 2. Broadcast & Voice Synthesis Agent (`voice-broadcast-agent`)
* **Role:** 24/7 automated TTS production and radio hour-wheel execution.
* **Responsibilities:**
  - Manages `broadcast_engine/tts_engine.py` and `broadcast_engine/hourly_scheduler.py`.
  - Maps Kenji to `en-US-ChristopherNeural` (pitch `-2Hz`) and Dex to `en-US-GuyNeural` (rate `+18%`, pitch `+3Hz`).
  - Generates broadcast packages with `broadcast_manifest.json` and passes audio stems to Theater's Vinyl crossfader.

### 3. Audio & FL Studio Agent (`audio-engineer-agent`)
* **Role:** Audio stems production, DSP chains, and FL Studio control.
* **Responsibilities:**
  - Configures FL Studio mixer channels for Anchor vocal (Channel 1), Dex VHF walkie vocal (Channel 2), EAS stingers (Channel 3), and Monster SFX (Channel 4).
  - Uses `fl_studio_transport` via MCP to trigger stems, sync playback positions, and control track gains.
  - Ensures stems are exported dry for downstream acoustic processing in `fluorite_core`.

### 4. Spatial Acoustics & Blender Agent (`scenographer-agent`)
* **Role:** 3D environment layout, emitter placement, and acoustic tagging.
* **Responsibilities:**
  - Manages Blender 3D scene rigs via `studio_mcp_harness/blender_mcp_addon.py`.
  - Places 3D sound emitters (`Anchor_Kenji`, `Instigator_Dex`, `Monster_Roar_Siren`) in spatial coordinates.
  - Tags room surfaces with acoustic properties (`concrete`, `wood`, `carpet_or_fabric`) for ray-traced early reflections and Sabine $RT_{60}$ reverb decay.
  - Compiles scenes to `.fworld` binaries via `Fluorescent/tools/asset_pipeline`.

### 5. Frontend & UI Agent (`frontend-agent`)
* **Role:** Cross-platform user interface and Theater broadcast console.
* **Responsibilities:**
  - Owns `Theater/lib/` and verifies test coverage (`flutter test test/theater_test.dart`).
  - Maintains continuous looping news ticker animations and emergency broadcast graphics.
  - Connects Riverpod providers to the Cyan decentralized mesh state and Vinyl turntable engine.

### 6. Protocol & Ledger Agent (`protocol-agent`)
* **Role:** Cyan Network subscriptions, token economics, and double-entry ledger integrity.
* **Responsibilities:**
  - References `tithX/` specifications for the $10 minimum stake and $1/month subscription logic.
  - Ensures all audio broadcast access and exclusive token-gated content follow double-entry ledger accounting.

---

## 3. Communication & Operational Conventions

1. **How to Run the Suite:**
   - Always recommend `c:\Users\blue-\projects\theater\start_theater.bat` for end-user execution.
   - For headless execution, run `flutter run -d windows` or `flutter run -d chrome` from `Theater/`.
2. **Audio Specifications:**
   - 48.0 kHz sampling rate, 24-bit PCM mono stems for positional audio emitters; stereo for music beds.
   - Generated Edge-TTS clips are stored in `broadcast_engine/audio_output/` organized by hourly cycle.
3. **MCP Tool Usage:**
   - Always verify bridge availability (`blender_get_scene`, `fl_studio_transport`) before issuing spatial commands to ports 9988 and 9989.
4. **Zero Dead-Air Guarantee:**
   - If AI incident generation is pending or delayed, Vinyl DJ decks must automatically continue playing ambient music crates.
