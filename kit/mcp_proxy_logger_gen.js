#!/usr/bin/env node
// mcp_proxy_logger.js
//
// Transparent stdio JSON-RPC proxy between an MCP client (mcp-fuzzer) and the
// real Filesystem MCP server. Forwards every byte unchanged in both
// directions (so mcp-fuzzer sees the exact same server it always did), while
// also logging every JSON-RPC line to a per-connection .jsonl file so that
// ALL request/response pairs (not just self-flagged findings) can later be
// reclassified with the same classifyError() logic used throughout the
// paper's other experiments.
//
// The very first line written to each log file is a "meta" record stating
// the exact sandboxPath argv this particular process instance received.
// mcp-fuzzer (v0.7.0) has been observed to occasionally spawn a stdio
// transport connection with a stale/incorrect endpoint command under
// concurrent connection setup (Max Concurrency > 1) -- this meta record lets
// downstream analysis detect and discard any run where that happened,
// instead of silently mixing in data captured against the wrong sandbox
// root.
//
// Usage: node mcp_proxy_logger.js <sandboxPath> <logDir>

import { spawn } from "child_process";
import fs from "fs";
import path from "path";
import readline from "readline";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const sandboxPath = process.argv[2];
const logDir = process.argv[3];

if (!sandboxPath || !logDir) {
  process.stderr.write("usage: node mcp_proxy_logger.js <sandboxPath> <logDir>\n");
  process.exit(1);
}

fs.mkdirSync(logDir, { recursive: true });

const logFile = path.join(logDir, `proxy_${Date.now()}_${process.pid}.jsonl`);
const logStream = fs.createWriteStream(logFile, { flags: "a" });
logStream.write(
  JSON.stringify({ dir: "meta", t: Date.now(), sandboxPath, logDir, pid: process.pid, argv: process.argv }) + "\n"
);

const serverEntry = path.join(
  __dirname,
  "node_modules/mcp-server-filesystem/dist/index.js"
);

const _pre = (process.env.SERVER_PRE ? process.env.SERVER_PRE.split(" ") : []);
const child = process.env.SERVER_BIN ? spawn(process.env.SERVER_BIN, [..._pre, sandboxPath], {
  stdio: ["pipe", "pipe", "pipe"], cwd: sandboxPath,
}) : spawn("node", [process.env.SERVER_ENTRY || serverEntry, ..._pre, sandboxPath], {
  stdio: ["pipe", "pipe", "pipe"], cwd: sandboxPath,
});

// ---- client(mcp-fuzzer) -> server, logged as "req" ----
const rlIn = readline.createInterface({ input: process.stdin, terminal: false });
rlIn.on("line", (line) => {
  if (line.trim().length > 0) {
    logStream.write(JSON.stringify({ dir: "req", t: Date.now(), raw: line }) + "\n");
  }
  let out = line;
  try {
    const mm = JSON.parse(line);
    if (mm.method === "initialize" && mm.params && mm.params.capabilities) {
      delete mm.params.capabilities.roots;
      out = JSON.stringify(mm);
    }
  } catch (e) {}
  child.stdin.write(out + "\n");
});
rlIn.on("close", () => {
  try {
    child.stdin.end();
  } catch (e) {}
});

// ---- server -> client(mcp-fuzzer), logged as "res" ----
const rlOut = readline.createInterface({ input: child.stdout, terminal: false });
rlOut.on("line", (line) => {
  if (line.trim().length > 0) {
    logStream.write(JSON.stringify({ dir: "res", t: Date.now(), raw: line }) + "\n");
  }
  process.stdout.write(line + "\n");
});

child.stderr.on("data", (chunk) => {
  process.stderr.write(chunk);
});

let closed = false;
function finish(code) {
  if (closed) return;
  closed = true;
  logStream.end(() => {
    process.exit(code || 0);
  });
}

child.on("exit", (code) => finish(code));
child.on("error", (err) => {
  logStream.write(JSON.stringify({ dir: "meta", t: Date.now(), error: String(err) }) + "\n");
  finish(1);
});
process.on("exit", () => {
  try {
    child.kill();
  } catch (e) {}
});
process.stdin.on("error", () => {});
process.stdout.on("error", () => {});
