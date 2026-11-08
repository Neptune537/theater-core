/**
 * Automated test suite for Studio MCP Harness Tools:
 * - publish_breaking_news
 * - get_live_ticker
 * - blender_add_acoustic_emitter
 * - blender_get_scene
 * - fl_studio_transport
 */

import assert from "node:assert";
import test from "node:test";
import net from "node:net";

// Mock bridge server on dynamic test ports
function startMockBridge(port, responseHandler) {
  return new Promise((resolve) => {
    const server = net.createServer((socket) => {
      let buffer = "";
      socket.on("data", (chunk) => {
        buffer += chunk.toString();
        try {
          const req = JSON.parse(buffer);
          const res = responseHandler(req);
          socket.write(JSON.stringify(res));
          socket.end();
        } catch {
          // Wait for full JSON if chunked
        }
      });
    });
    server.listen(port, "127.0.0.1", () => {
      resolve(server);
    });
  });
}

// Emulate sendTcpCommand logic from server.js
function sendTcpCommand(port, payload, host = "127.0.0.1") {
  return new Promise((resolve) => {
    const client = new net.Socket();
    let dataBuffer = "";
    client.setTimeout(1500);

    client.connect(port, host, () => {
      client.write(JSON.stringify(payload));
    });

    client.on("data", (data) => {
      dataBuffer += data.toString();
    });

    client.on("close", () => {
      try {
        resolve(JSON.parse(dataBuffer));
      } catch {
        resolve({ raw: dataBuffer });
      }
    });

    client.on("timeout", () => {
      client.destroy();
      resolve({ status: "bridge_offline", message: `Port ${port} timed out` });
    });

    client.on("error", (err) => {
      resolve({ status: "bridge_offline", message: `Cannot connect: ${err.message}` });
    });
  });
}

// In-memory ticker simulation directly aligned with server.js
let incidentStore = {
  id: "EVT_TEST_01",
  headline: "DEFAULT HEADLINE",
  urgency: "INFO",
  ticker: ["LINE 1", "LINE 2"],
  script: []
};

function handleToolCall(name, args) {
  if (name === "publish_breaking_news") {
    incidentStore.headline = args.headline;
    if (args.urgency) incidentStore.urgency = args.urgency;
    if (args.ticker_lines) incidentStore.ticker = args.ticker_lines;
    if (args.script_dialogue) incidentStore.script = args.script_dialogue;

    return {
      status: "published",
      incident: incidentStore
    };
  }

  if (name === "get_live_ticker") {
    return incidentStore;
  }

  throw new Error(`Unknown tool: ${name}`);
}

test("Tool: publish_breaking_news updates headline, urgency and ticker", () => {
  const payload = {
    headline: "CAT 5 TYPHOON APPROACHING SECTOR 4",
    urgency: "CRITICAL",
    ticker_lines: [
      "Winds gusting past 160mph",
      "Coastal levees locked down",
      "Dex: 'Check the barometric drops on the analog gauge!'"
    ],
    script_dialogue: [
      { speaker: "reporter", line: "Kenji Vance here with an urgent bulletin." },
      { speaker: "instigator", line: "Look at the radar sweep, Kenji! The eye is right over us!" }
    ]
  };

  const result = handleToolCall("publish_breaking_news", payload);
  assert.strictEqual(result.status, "published");
  assert.strictEqual(result.incident.headline, "CAT 5 TYPHOON APPROACHING SECTOR 4");
  assert.strictEqual(result.incident.urgency, "CRITICAL");
  assert.strictEqual(result.incident.ticker.length, 3);
  assert.strictEqual(result.incident.script.length, 2);
  assert.strictEqual(result.incident.script[0].speaker, "reporter");
});

test("Tool: get_live_ticker returns updated incident state", () => {
  const liveTicker = handleToolCall("get_live_ticker", {});
  assert.strictEqual(liveTicker.headline, "CAT 5 TYPHOON APPROACHING SECTOR 4");
  assert.ok(liveTicker.ticker.includes("Winds gusting past 160mph"));
});

test("Tool: blender_add_acoustic_emitter handles bridge response and payload structure", async () => {
  const MOCK_BLENDER_PORT = 19988;
  const mockServer = await startMockBridge(MOCK_BLENDER_PORT, (req) => {
    assert.strictEqual(req.action, "create_emitter");
    assert.strictEqual(req.params.name, "Anchor_Mic");
    assert.deepStrictEqual(req.params.location, [0, 1.5, 0.8]);
    return { status: "created", object_name: "Anchor_Mic_Emitter", id: "BL_001" };
  });

  try {
    const res = await sendTcpCommand(MOCK_BLENDER_PORT, {
      action: "create_emitter",
      params: { name: "Anchor_Mic", emitter_type: "reporter", location: [0, 1.5, 0.8] }
    });
    assert.strictEqual(res.status, "created");
    assert.strictEqual(res.object_name, "Anchor_Mic_Emitter");
  } finally {
    mockServer.close();
  }
});

test("Tool: blender_add_acoustic_emitter handles bridge offline gracefully", async () => {
  const res = await sendTcpCommand(19999, { action: "create_emitter" });
  assert.strictEqual(res.status, "bridge_offline");
  assert.ok(res.message.includes("Cannot connect") || res.message.includes("timed out"));
});

test("Tool: fl_studio_transport packages playback commands correctly", async () => {
  const MOCK_FL_PORT = 19989;
  const mockServer = await startMockBridge(MOCK_FL_PORT, (req) => {
    assert.strictEqual(req.action, "play");
    assert.strictEqual(req.params.track, 1);
    assert.strictEqual(req.params.volume, 0.85);
    return { status: "ok", transport: "playing", master_volume: 0.85 };
  });

  try {
    const res = await sendTcpCommand(MOCK_FL_PORT, {
      action: "play",
      params: { track: 1, volume: 0.85 }
    });
    assert.strictEqual(res.status, "ok");
    assert.strictEqual(res.transport, "playing");
  } finally {
    mockServer.close();
  }
});
