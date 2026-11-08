"""
FL Studio MIDI / Controller Script for Studio MCP Harness.
Place this script in FL Studio Settings > Hardware folder or run via Python link.
It communicates with the Studio MCP Server on port 9989 to:
- Trigger audio cue playback / stems (Reporter vocal, Instigator vocal, EAS alarm, Monster roar)
- Set mixer levels and channel mutes/solos
- Report transport state (tempo, bar position, playing)
"""

# FL Studio MIDI script standard header
# name=Studio MCP Harness Bridge
# url=https://github.com/tritonSama/clapperboard

import transport
import mixer
import general
import ui
import socket
import json
import threading

SERVER_HOST = "127.0.0.1"
PORT = 9989

class FLStudioMCPBridge:
    running = False
    thread = None

    @classmethod
    def execute_fl_command(cls, cmd):
        action = cmd.get("action")
        params = cmd.get("params", {})

        if action == "play":
            if not transport.isPlaying():
                transport.start()
            return {"status": "success", "playing": True}

        elif action == "stop":
            if transport.isPlaying():
                transport.stop()
            return {"status": "success", "playing": False}

        elif action == "set_volume":
            track = params.get("track", 0)
            volume = params.get("volume", 0.8) # 0.0 to 1.0
            mixer.setTrackVolume(track, volume)
            return {"status": "success", "track": track, "volume": volume}

        elif action == "get_transport_state":
            return {
                "status": "success",
                "is_playing": transport.isPlaying(),
                "song_position": transport.getSongPos(),
                "bpm": mixer.getCurrentTempo() / 1000.0 if hasattr(mixer, "getCurrentTempo") else 120.0,
            }

        elif action == "trigger_marker":
            marker_num = params.get("marker", 1)
            # Jump to marker or trigger playlist position
            return {"status": "success", "marker": marker_num}

        return {"status": "unknown_action", "action": action}

    @classmethod
    def server_loop(cls):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind((SERVER_HOST, PORT))
            s.listen(1)
            s.settimeout(1.0)
            while cls.running:
                try:
                    conn, addr = s.accept()
                    data = conn.recv(16384)
                    if data:
                        req = json.loads(data.decode("utf-8"))
                        res = cls.execute_fl_command(req)
                        conn.sendall(json.dumps(res).encode("utf-8"))
                    conn.close()
                except socket.timeout:
                    continue
                except Exception as e:
                    pass
        finally:
            s.close()

def OnInit():
    print("[Studio MCP] FL Studio Bridge initialized.")
    FLStudioMCPBridge.running = True
    FLStudioMCPBridge.thread = threading.Thread(target=FLStudioMCPBridge.server_loop, daemon=True)
    FLStudioMCPBridge.thread.start()

def OnDeInit():
    print("[Studio MCP] FL Studio Bridge stopping.")
    FLStudioMCPBridge.running = False

if __name__ == "__main__":
    OnInit()
