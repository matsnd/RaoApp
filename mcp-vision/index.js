import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { z } from "zod";
import "dotenv/config";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..");
const TEMP_DIR = path.join(REPO_ROOT, "temp", "vision");

// === Vision providers ===
// Strategy: caller decides via `model` param:
//   "auto"   → Nemotron first, Claude fallback (default, cheapest)
//   "free"   → Nemotron only (free, lower quality)
//   "claude" → Claude only (paid, highest quality — use for OCR / document reading)
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY;
const ANTHROPIC_API_KEY = process.env.ANTHROPIC_API_KEY;

const FREE_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free";
const CLAUDE_MODEL = "claude-opus-4-5";

const anthropic = ANTHROPIC_API_KEY ? new Anthropic({ apiKey: ANTHROPIC_API_KEY }) : null;

const server = new McpServer({
  name: "rao-vision",
  version: "2.0.0",
});

// === Prompt builder ===
function buildPrompt({ question, url }) {
  const ctx = url ? `z URL: ${url}` : "aplikacji RAO (system wynajmu maszyn budowlanych)";
  const designSystem = `Design system RAO:
- Kolor primary: #1D2B53 (navy)
- Font: Montserrat
- Border-radius: 12px
- Tło: #F8F9FA lub #FFFFFF`;

  if (question) {
    return `Jesteś senior UI/UX designerem. Przeanalizuj ten screenshot ${ctx}.\n\nPytanie: ${question}\n\n${designSystem}\n\nOdpowiedz konkretnie: co jest OK, co wymaga poprawy, jakie błędy wizualne widzisz.`;
  }
  return `Jesteś senior UI/UX designerem. Przeanalizuj ten screenshot ${ctx}.\n\n${designSystem}\n\nOceń:\n1. Czy design system jest zachowany?\n2. Czy są błędy wizualne (broken layout, overflow, misalignment)?\n3. Czy są problemy UX (brak loading state, error state, pusty state)?\n4. Ogólna ocena: OK / WYMAGA POPRAWY / KRYTYCZNY BŁĄD`;
}

// === Nemotron Nano 12B v2 VL via OpenRouter (free, first-choice) ===
async function analyzeWithFreeModel({ imageData, mediaType, prompt }) {
  if (!OPENROUTER_API_KEY) {
    return { ok: false, reason: "no OPENROUTER_API_KEY", text: null };
  }
  const dataUrl = `data:${mediaType};base64,${imageData}`;
  const resp = await fetch("https://openrouter.ai/api/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
      "HTTP-Referer": "https://github.com/rao-app",
      "X-Title": "rao-vision MCP",
    },
    body: JSON.stringify({
      model: FREE_MODEL,
      max_tokens: 1024,
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
  if (!resp.ok) {
    const errText = await resp.text().catch(() => "<no body>");
    return { ok: false, reason: `OpenRouter HTTP ${resp.status}: ${errText.slice(0, 200)}`, text: null };
  }
  const json = await resp.json();
  const text = json?.choices?.[0]?.message?.content;
  if (!text || text.trim().length < 20) {
    return { ok: false, reason: "empty/thin response", text: text || null };
  }
  return { ok: true, reason: null, text };
}

// === Claude via Anthropic SDK (fallback) ===
async function analyzeWithClaude({ imageData, mediaType, prompt }) {
  if (!anthropic) {
    return { ok: false, reason: "no ANTHROPIC_API_KEY", text: null };
  }
  const response = await anthropic.messages.create({
    model: CLAUDE_MODEL,
    max_tokens: 1024,
    messages: [
      {
        role: "user",
        content: [
          { type: "image", source: { type: "base64", media_type: mediaType, data: imageData } },
          { type: "text", text: prompt },
        ],
      },
    ],
  });
  const text = response.content[0]?.text;
  if (!text) {
    return { ok: false, reason: "empty Claude response", text: null };
  }
  return { ok: true, reason: null, text };
}

// === Unified analyzer with model selection ===
// model: "auto" (default) | "free" | "claude"
async function analyzeImage({ imageData, mediaType, prompt, metaLine, model = "auto" }) {
  // "claude" → Claude only (skip free model)
  if (model === "claude") {
    const claude = await analyzeWithClaude({ imageData, mediaType, prompt });
    if (claude.ok) {
      return {
        text: claude.text,
        modelUsed: CLAUDE_MODEL,
        provider: "anthropic",
        fallback: false,
        metaLine: metaLine || "",
      };
    }
    return {
      text: `❌ Vision analysis failed (claude-only).\nClaude: ${claude.reason}`,
      modelUsed: "none",
      provider: "none",
      fallback: false,
      metaLine: metaLine || "",
    };
  }

  // "free" → Nemotron only (no fallback to Claude)
  if (model === "free") {
    const free = await analyzeWithFreeModel({ imageData, mediaType, prompt });
    if (free.ok) {
      return {
        text: free.text,
        modelUsed: FREE_MODEL,
        provider: "openrouter (free)",
        fallback: false,
        metaLine: metaLine || "",
      };
    }
    return {
      text: `❌ Vision analysis failed (free-only).\nFree model: ${free.reason}`,
      modelUsed: "none",
      provider: "none",
      fallback: false,
      metaLine: metaLine || "",
    };
  }

  // "auto" (default) → Nemotron first, Claude fallback
  const free = await analyzeWithFreeModel({ imageData, mediaType, prompt });
  if (free.ok) {
    return {
      text: free.text,
      modelUsed: FREE_MODEL,
      provider: "openrouter (free)",
      fallback: false,
      metaLine: metaLine || "",
    };
  }
  // Claude fallback
  const claude = await analyzeWithClaude({ imageData, mediaType, prompt });
  if (claude.ok) {
    return {
      text: claude.text,
      modelUsed: CLAUDE_MODEL,
      provider: "anthropic",
      fallback: true,
      fallbackReason: free.reason,
      metaLine: metaLine || "",
    };
  }
  // Both failed
  return {
    text: `❌ Vision analysis failed.\nFree model: ${free.reason}\nClaude: ${claude.reason}`,
    modelUsed: "none",
    provider: "none",
    fallback: true,
    metaLine: metaLine || "",
  };
}

function writeReport({ reportPath, header, result }) {
  const modelLine = `**Model:** ${result.modelUsed} (${result.provider})${result.fallback ? ` [fallback z free model: ${result.fallbackReason}]` : ""}`;
  fs.writeFileSync(
    reportPath,
    `# Vision Report\n\n${header}\n${modelLine}\n**Data:** ${new Date().toISOString()}\n\n${result.text}\n`
  );
}

// === Tool 1: analyze_screenshot ===
server.tool(
  "analyze_screenshot",
  "Analizuje screenshot UI aplikacji RAO. Model wybierany przez parametr `model`: auto (domyślnie, free→claude fallback), free (Nemotron only), claude (Claude Vision only — najlepszy do OCR/dokumentów). Zwraca ocenę: błędy wizualne, spójność design systemu, UX issues.",
  {
    image_path: z.string().describe("Absolutna ścieżka do pliku PNG/JPG screenshota"),
    question: z.string().optional().describe("Opcjonalne pytanie do analizy, np. 'Czy formularz wygląda poprawnie?'"),
    model: z.enum(["auto", "free", "claude"]).optional().describe("Model vision: auto (default, free→claude fallback), free (Nemotron only), claude (Claude Vision only — best for OCR/document reading)"),
  },
  async ({ image_path, question, model }) => {
    if (!fs.existsSync(image_path)) {
      return { content: [{ type: "text", text: `ERROR: Plik nie istnieje: ${image_path}` }] };
    }

    const ext = path.extname(image_path).toLowerCase();
    const mediaType = ext === ".jpg" || ext === ".jpeg" ? "image/jpeg" : "image/png";
    const imageData = fs.readFileSync(image_path).toString("base64");
    const prompt = buildPrompt({ question, url: null });

    const result = await analyzeImage({ imageData, mediaType, prompt, metaLine: `**Plik:** ${image_path}`, model: model || "auto" });

    const reportPath = image_path.replace(/\.(png|jpg|jpeg)$/i, "-vision-report.md");
    writeReport({ reportPath, header: `**Plik:** ${image_path}`, result });

    const modelTag = result.fallback
      ? ` (fallback → ${result.modelUsed})`
      : ` (${result.provider})`;
    return {
      content: [
        { type: "text", text: result.text },
        { type: "text", text: `\n\n📄 Raport zapisany: ${reportPath}\n🤖 Model: ${result.modelUsed}${modelTag}` },
      ],
    };
  }
);

// === Tool 2: screenshot_and_analyze ===
server.tool(
  "screenshot_and_analyze",
  "Robi screenshot podanego URL przez Playwright, następnie analizuje go. Model wybierany przez parametr `model`: auto (domyślnie), free (Nemotron only), claude (Claude Vision only — best for OCR). Wymaga działającego frontendu.",
  {
    url: z.string().describe("URL do screenshota, np. http://localhost:5173/contracts"),
    question: z.string().optional().describe("Opcjonalne pytanie do analizy"),
    output_path: z.string().optional().describe("Ścieżka gdzie zapisać screenshot (domyślnie: temp/screenshot-{timestamp}.png)"),
    model: z.enum(["auto", "free", "claude"]).optional().describe("Model vision: auto (default), free (Nemotron only), claude (Claude Vision only — best for OCR/document reading)"),
  },
  async ({ url, question, output_path, model }) => {
    const timestamp = Date.now();
    const screenshotPath = output_path || path.join(TEMP_DIR, `screenshot-${timestamp}.png`);

    fs.mkdirSync(path.dirname(screenshotPath), { recursive: true });

    const { chromium } = await import("playwright");
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    try {
      await page.goto(url, { waitUntil: "networkidle", timeout: 15000 });
      await page.screenshot({ path: screenshotPath, fullPage: true });
    } finally {
      await browser.close();
    }

    const imageData = fs.readFileSync(screenshotPath).toString("base64");
    const prompt = buildPrompt({ question, url });

    const result = await analyzeImage({ imageData, mediaType: "image/png", prompt, metaLine: `**URL:** ${url}\n**Screenshot:** ${screenshotPath}`, model: model || "auto" });

    const reportPath = screenshotPath.replace(".png", "-vision-report.md");
    writeReport({ reportPath, header: `**URL:** ${url}\n**Screenshot:** ${screenshotPath}`, result });

    const modelTag = result.fallback
      ? ` (fallback → ${result.modelUsed})`
      : ` (${result.provider})`;
    return {
      content: [
        { type: "text", text: `📸 Screenshot: ${screenshotPath}\n\n${result.text}` },
        { type: "text", text: `\n\n📄 Raport zapisany: ${reportPath}\n🤖 Model: ${result.modelUsed}${modelTag}` },
      ],
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
