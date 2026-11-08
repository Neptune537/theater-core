#!/usr/bin/env node

/**
 * Studio MCP Harness Server
 * Connects AI models (Gemini / Antigravity / Claude) to Blender & FL Studio.
 * Exposes tools to:
 * - Generate breaking live event scripts (Reporter vs Instigator)
 * - Broadcast headlines to the live News Ticker
 * - Place spatial acoustic emitters & materials in Blender
 * - Control FL Studio playback, volume, and cue triggering
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import net from "net";

const BLENDER_PORT = 9988;
const FL_PORT = 9989;
const HOST = "127.0.0.1";

// Helper to send TCP command to Blender/FL bridges
function sendTcpCommand(port, payload) {
  return new Promise((resolve, reject) => {
    const client = new net.Socket();
    let dataBuffer = "";

    client.setTimeout(2500);

    client.connect(port, HOST, () => {
      client.write(JSON.stringify(payload));
    });

    client.on("data", (data) => {
      dataBuffer += data.toString();
    });

    client.on("close", () => {
      try {
        resolve(JSON.parse(dataBuffer));
      } catch (e) {
        resolve({ raw: dataBuffer });
      }
    });

    client.on("timeout", () => {
      client.destroy();
      resolve({ status: "bridge_offline", message: `Port ${port} timed out (application bridge not running)` });
    });

    client.on("error", (err) => {
      resolve({ status: "bridge_offline", message: `Cannot connect to port ${port}: ${err.message}` });
    });
  });
}

// In-memory ticker and incident store
let currentIncident = {
  id: "EVT_TOKYO_BAY_01",
  headline: "BREAKING: 45M AMPHIBIOUS ENTITY BREACHES TOKYO HARBOR",
  urgency: "CRITICAL",
  ticker: [
    "BREAKING: 45M AMPHIBIOUS ENTITY BREACHES TOKYO HARBOR",
    "RAINBOW BRIDGE TRANSIT EVACUATED",
    "DEX: 'THEY DREDGED THIS UP FROM THE SUB-TRENCH!'",
    "SDF UNITS MOBILIZING ALONG THE WATERFRONT"
  ]
};

const server = new Server(
  {
    name: "studio-mcp-harness",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "publish_breaking_news",
        description: "Generate and publish an emergency news incident with ticker alerts and dialogue script for the Reporter & Instigator.",
        inputSchema: {
          type: "object",
          properties: {
            headline: { type: "string", description: "Main breaking banner headline" },
            urgency: { type: "string", enum: ["INFO", "WARNING", "CRITICAL"], description: "Severity level" },
            ticker_lines: {
              type: "array",
              items: { type: "string" },
              description: "Array of short scrolling ticker updates"
            },
            script_dialogue: {
              type: "array",
              description: "Turn-by-turn dialogue between Reporter (Kenji) and Instigator (Dex)",
              items: {
                type: "object",
                properties: {
                  speaker: { type: "string", enum: ["reporter", "instigator"] },
                  line: { type: "string" }
                },
                required: ["speaker", "line"]
              }
            }
          },
          required: ["headline", "ticker_lines"]
        }
      },
      {
        name: "get_live_ticker",
        description: "Retrieve currently active ticker items and breaking broadcast incident.",
        inputSchema: { type: "object", properties: {} }
      },
      {
        name: "blender_add_acoustic_emitter",
        description: "Place a spatial audio emitter in Blender (tied to Fluorescent acoustics).",
        inputSchema: {
          type: "object",
          properties: {
            name: { type: "string", description: "Name of emitter (e.g. Anchor_Mic, Dex_Phone, Monster_Roar)" },
            emitter_type: { type: "string", enum: ["reporter", "instigator", "monster", "siren", "music"] },
            location: {
              type: "array",
              items: { type: "number" },
              description: "[X, Y, Z] 3D coordinates in meters"
            }
          },
          required: ["name", "location"]
        }
      },
      {
        name: "blender_get_scene",
        description: "Fetch list of all 3D objects, emitters, and acoustic materials in active Blender scene.",
        inputSchema: { type: "object", properties: {} }
      },
      {
        name: "blender_charakuru_execute",
        description: "Trigger automated Charakuru pipeline actions inside Blender (transfer_weights, spring_setup, expression_studio, vrm_export).",
        inputSchema: {
          type: "object",
          properties: {
            subroutine: {
              type: "string",
              enum: ["transfer_weights", "spring_setup", "expression_studio", "mtoon_export", "export_rig"],
              description: "Specific Charakuru automation step to invoke in Blender"
            },
            project_path: {
              type: "string",
              description: "Path to Charakuru work directory or .charakit folder"
            },
            args: {
              type: "object",
              description: "Additional script arguments passed to the Charakuru Blender subprocess"
            }
          },
          required: ["subroutine"]
        }
      },
      {
        name: "fl_studio_transport",
        description: "Control FL Studio playback transport (play/stop/volume).",
        inputSchema: {
          type: "object",
          properties: {
            command: { type: "string", enum: ["play", "stop", "state"] },
            track: { type: "number", description: "Mixer track number" },
            volume: { type: "number", description: "Volume level from 0.0 to 1.0" }
          },
          required: ["command"]
        }
      }
    ]
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  if (name === "publish_breaking_news") {
    currentIncident.headline = args.headline;
    if (args.urgency) currentIncident.urgency = args.urgency;
    if (args.ticker_lines) currentIncident.ticker = args.ticker_lines;
    if (args.script_dialogue) currentIncident.script = args.script_dialogue;

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            status: "published",
            incident: currentIncident
          }, null, 2)
        }
      ]
    };
  }

  if (name === "get_live_ticker") {
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(currentIncident, null, 2)
        }
      ]
    };
  }

  if (name === "blender_add_acoustic_emitter") {
    const res = await sendTcpCommand(BLENDER_PORT, {
      action: "create_emitter",
      params: {
        name: args.name,
        emitter_type: args.emitter_type || "voice",
        location: args.location || [0, 0, 0]
      }
    });

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(res, null, 2)
        }
      ]
    };
  }

  if (name === "blender_get_scene") {
    const res = await sendTcpCommand(BLENDER_PORT, { action: "get_scene" });
    return {
      content: [{ type: "text", text: JSON.stringify(res, null, 2) }]
    };
  }

  if (name === "blender_charakuru_execute") {
    const res = await sendTcpCommand(BLENDER_PORT, {
      action: "charakuru_execute",
      params: {
        subroutine: args.subroutine,
        project_path: args.project_path,
        args: args.args || {}
      }
    });

    return {
      content: [{ type: "text", text: JSON.stringify(res, null, 2) }]
    };
  }

  if (name === "fl_studio_transport") {
    let action = args.command === "play" ? "play" : args.command === "stop" ? "stop" : "get_transport_state";
    const res = await sendTcpCommand(FL_PORT, {
      action: action,
      params: { track: args.track, volume: args.volume }
    });
    return {
      content: [{ type: "text", text: JSON.stringify(res, null, 2) }]
    };
  }

  throw new Error(`Unknown tool: ${name}`);
});

async function run() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Studio MCP Harness server running on stdio");
}

run().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
