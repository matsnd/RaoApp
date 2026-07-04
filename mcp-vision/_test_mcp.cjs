// Finalny test rao-vision MCP: screenshot_and_analyze przez STDIO
const { spawn } = require("child_process");
const path = require("path");

const req = [
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}\n',
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"screenshot_and_analyze","arguments":{"url":"http://localhost:5173/rao/login","question":"Czy formularz logowania jest widoczny i ma pola username oraz haslo?"}}}\n',
].join("");

const proc = spawn("node", ["index.js"], {
  cwd: __dirname,
  env: {
    ...process.env,
    OPENROUTER_API_KEY: "OPENROUTER_API_KEY_REVOKED",
    ANTHROPIC_API_KEY: "ANTHROPIC_API_KEY_REVOKED",
  },
});

let out = "";
proc.stdout.on("data", (d) => { out += d.toString(); process.stderr.write("[STDOUT] " + d.toString().slice(0,200) + "\n"); });
proc.stderr.on("data", (d) => { process.stderr.write("[STDERR] " + d.toString()); });
proc.on("close", (code) => { process.stderr.write("[EXIT] code=" + code + " out_len=" + out.length + "\n");
  const lines = out.split("\n").filter(Boolean);
  for (const line of lines) {
    try {
      const j = JSON.parse(line);
      if (j.id === 2) {
        const text = j.result?.content?.map(c => c.text).join("\n") || JSON.stringify(j, null, 2);
        console.log("=== MCP RESULT ===");
        console.log(text);
      }
    } catch {}
  }
});

proc.stdin.write(req);
// NIE zamykaj stdin — serwer MCP czyta dalej
setTimeout(() => { proc.kill(); process.exit(0); }, 120000);
