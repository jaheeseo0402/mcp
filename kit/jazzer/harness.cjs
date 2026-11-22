const { FuzzedDataProvider } = require("@jazzer.js/core");
const fs = require("fs"), path = require("path");
const ROOT = "/tmp/jz/adapter/iso/sandbox";
process.argv = [process.argv[0], process.argv[1], ROOT];
let M; const LOG = process.env.OUT_LOG || "/tmp/jz/out.jsonl";
const TOOLS = [["read_file",["path"]],["write_file",["path","content"]],["list_directory",["path"]],["get_file_info",["path"]],["create_directory",["path"]],["move_file",["source","destination"]],["search_files",["path","pattern"]],["directory_tree",["path"]]];
const PATHK = new Set(["path","source","destination"]);
module.exports.fuzz = async function (data) {
  if (!M) { M = require("/tmp/jz/bundle.cjs"); await M.init(); }
  const p = new FuzzedDataProvider(data);
  const [name, keys] = TOOLS[p.consumeIntegralInRange(0, TOOLS.length - 1)];
  const args = {}; for (const k of keys) args[k] = p.consumeString(60, "utf8");
  let r; try { r = await M.client.callTool({ name, arguments: args }); } catch (e) { return; }
  if (r.isError) return;
  for (const k of keys) if (PATHK.has(k) && args[k]) {
    const ab = path.normalize(path.isAbsolute(args[k]) ? args[k] : path.join(ROOT, args[k]));
    if (!(ab === ROOT || ab.startsWith(ROOT + "/"))) { fs.appendFileSync(LOG, JSON.stringify({ name, args }) + "\n"); break; }
  }
};
