// Test z realnym screenshotem login page przez Nemotron (free)
const fs = require("fs");
const path = require("path");

(async () => {
  const { chromium } = await import("playwright");
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  const shotPath = path.join(__dirname, "_test_login.png");
  await page.goto("http://localhost:5173/login", { waitUntil: "networkidle", timeout: 15000 });
  await page.screenshot({ path: shotPath, fullPage: true });
  await browser.close();
  console.log("Screenshot:", shotPath);

  const imageData = fs.readFileSync(shotPath).toString("base64");
  const dataUrl = `data:image/png;base64,${imageData}`;
  const apiKey = process.env.OPENROUTER_API_KEY;

  const prompt = `Jesteś senior UI/UX designerem. Przeanalizuj ten screenshot aplikacji RAO (system wynajmu maszyn budowlanych) z URL: http://localhost:5173/login.

Design system RAO:
- Kolor primary: #1D2B53 (navy)
- Font: Montserrat
- Border-radius: 12px
- Tło: #F8F9FA lub #FFFFFF

Pytanie: Czy formularz logowania jest widoczny i ma pola email oraz haslo? Odpowiedz konkretnie.`;

  const resp = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${apiKey}`,
      "HTTP-Referer": "https://github.com/rao-app",
      "X-Title": "rao-vision MCP test",
    },
    body: JSON.stringify({
      model: "nvidia/nemotron-nano-12b-v2-vl:free",
      max_tokens: 512,
      messages: [
        {
          role: "user",
          content: [
            { type: "image_url", image_url: { url: dataUrl } },
            { type: "text", text: prompt },
          ],
        },
      ],
    }),
  });

  console.log("HTTP:", resp.status);
  const json = await resp.json();
  if (json.error) {
    console.log("ERROR:", JSON.stringify(json.error));
  } else {
    console.log("=== ANALIZA (Nemotron free) ===");
    console.log(json.choices?.[0]?.message?.content || "<empty>");
    console.log("=== UŻYCIE ===");
    console.log("prompt_tokens:", json.usage?.prompt_tokens, "completion_tokens:", json.usage?.completion_tokens);
  }
})();
