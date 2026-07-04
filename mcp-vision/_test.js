// Test rao-vision: screenshot_and_analyze przez Qwen (free) → fallback Claude
const { spawn } = require("child_process");
const path = require("path");

const req = [
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}',
  '{"jsonrpc":"2.0","method":"notifications/initialized"}',
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"screenshot_and_analyze","arguments":{"url":"http://localhost:5173/login","question":"Czy formularz logowania jest widoczny i ma pola email oraz haslo?"}}}',
].join("\n");

const proc = spawn("node", ["index.js"], {
  cwd: __dirname,
  env: { ...process.env },
});

let out = "";
proc.stdout.on("data", (d) => { out += d.toString(); });
proc.stderr.on("data", (d) => { process.stderr.write(d); });
proc.on("close", () => {
  // Wypisz tylko ostatnią odpowiedź (id:2)
  const lines = out.split("\n").filter(Boolean);
  for (const line of lines) {
    try {
      const j = JSON.parse(line);
      if (j.id === 2) {
        const text = j.result?.content?.map(c => c.text).join("\n") || JSON.stringify(j, null, 2);
        console.log("=== RESULT ===");
        console.log(text);
      }
    } catch {}
  }
});

proc.stdin.write(req);
proc.stdin.end();
setTimeout(() => proc.kill(), 90000);
