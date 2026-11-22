// V8 커버리지를 호출마다 뽑아서 COV_FILE에 "새로 밟은 구간 수"를 기록하는 preload
const inspector = require('inspector'); const fs = require('fs');
const s = new inspector.Session(); s.connect();
s.post('Profiler.enable'); s.post('Profiler.startPreciseCoverage', { callCount: false, detailed: true });
const out = process.env.COV_FILE; const seen = new Set(); let busy = false;
function snap() {
  s.post('Profiler.takePreciseCoverage', (e, r) => {
    let nw = 0; const NEWK = [];
    if (!e) for (const sc of r.result) {
      if (!sc.url.includes('node_modules') && !sc.url.includes('/dist/')) continue;
      if (sc.url.includes('node:') ) continue;
      for (const f of sc.functions) for (const rg of f.ranges) if (rg.count > 0) {
        const k = sc.url + ':' + rg.startOffset + '-' + rg.endOffset;
        if (!seen.has(k)) { seen.add(k); nw++; NEWK.push(k); }
      }
    }
    fs.appendFileSync(out, JSON.stringify({ n: nw, total: seen.size, k: NEWK }) + '\n');
  });
}
const ow = process.stdout.write.bind(process.stdout);
process.stdout.write = function (chunk, ...a) {
  const r = ow(chunk, ...a);
  try { const t = String(chunk); if (t.includes('"jsonrpc"') && (t.includes('"result"') || t.includes('"error"'))) {
    const m = t.split('\n').filter(Boolean).length; for (let i = 0; i < m; i++) snap(); } } catch (e) {}
  return r;
};
