// Test bezpośredniego wywołania Qwen2.5-VL przez OpenRouter
const fs = require("fs");
const path = require("path");
require("dotenv").config({ path: path.join(__dirname, "..", ".env") });

// Stwórz mały 1x1 PNG (base64)
const tinyPng = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "base64"
);
const dataUrl = `data:image/png;base64,${tinyPng.toString("base64")}`;

const apiKey = process.env.OPENROUTER_API_KEY;
console.log("OPENROUTER_API_KEY:", apiKey ? `${apiKey.slice(0, 12)}...` : "MISSING");

fetch("https://openrouter.ai/api/v1/chat/completions", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${apiKey}`,
    "HTTP-Referer": "https://github.com/rao-app",
    "X-Title": "rao-vision MCP test",
  },
  body: JSON.stringify({
    model: "nvidia/nemotron-nano-12b-v2-vl:free",
    max_tokens: 256,
    messages: [
      {
        role: "user",
        content: [
          { type: "image_url", image_url: { url: dataUrl } },
          { type: "text", text: "Opisz ten obrazek w 1 zdaniu." },
        ],
      },
    ],
  }),
})
  .then(async (r) => {
    console.log("HTTP:", r.status);
    const text = await r.text();
    console.log("Body:", text.slice(0, 500));
  })
  .catch((e) => console.error("ERR:", e.message));
