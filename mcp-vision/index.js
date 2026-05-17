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

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const server = new McpServer({
  name: "rao-vision",
  version: "1.0.0",
});

server.tool(
  "analyze_screenshot",
  "Analizuje screenshot UI aplikacji RAO przez Claude Vision. Zwraca ocenę: błędy wizualne, spójność design systemu, UX issues.",
  {
    image_path: z.string().describe("Absolutna ścieżka do pliku PNG/JPG screenshota"),
    question: z.string().optional().describe("Opcjonalne pytanie do analizy, np. 'Czy formularz wygląda poprawnie?'"),
  },
  async ({ image_path, question }) => {
    if (!fs.existsSync(image_path)) {
      return { content: [{ type: "text", text: `ERROR: Plik nie istnieje: ${image_path}` }] };
    }

    const ext = path.extname(image_path).toLowerCase();
    const mediaType = ext === ".jpg" || ext === ".jpeg" ? "image/jpeg" : "image/png";
    const imageData = fs.readFileSync(image_path).toString("base64");

    const prompt = question
      ? `Jesteś senior UI/UX designerem. Przeanalizuj ten screenshot aplikacji RAO (system wynajmu maszyn budowlanych).\n\nPytanie: ${question}\n\nDesign system RAO:\n- Kolor primary: #1D2B53 (navy)\n- Font: Montserrat\n- Border-radius: 12px\n- Tło: #F8F9FA lub #FFFFFF\n\nOdpowiedz konkretnie: co jest OK, co wymaga poprawy, jakie błędy wizualne widzisz.`
      : `Jesteś senior UI/UX designerem. Przeanalizuj ten screenshot aplikacji RAO (system wynajmu maszyn budowlanych).\n\nDesign system RAO:\n- Kolor primary: #1D2B53 (navy)\n- Font: Montserrat\n- Border-radius: 12px\n- Tło: #F8F9FA lub #FFFFFF\n\nOceń:\n1. Czy design system jest zachowany?\n2. Czy są błędy wizualne (broken layout, overflow, misalignment)?\n3. Czy są problemy UX (brak loading state, error state, pusty state)?\n4. Ogólna ocena: OK / WYMAGA POPRAWY / KRYTYCZNY BŁĄD`;

    const response = await client.messages.create({
      model: "claude-opus-4-5",
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

    const result = response.content[0].text;

    const reportPath = image_path.replace(/\.(png|jpg|jpeg)$/i, "-vision-report.md");
    fs.writeFileSync(reportPath, `# Vision Report\n\n**Plik:** ${image_path}\n**Model:** claude-opus-4-5\n**Data:** ${new Date().toISOString()}\n\n${result}\n`);

    return {
      content: [
        { type: "text", text: result },
        { type: "text", text: `\n\n📄 Raport zapisany: ${reportPath}` },
      ],
    };
  }
);

server.tool(
  "screenshot_and_analyze",
  "Robi screenshot podanego URL przez Playwright, następnie analizuje go przez Claude Vision. Wymaga działającego frontendu.",
  {
    url: z.string().describe("URL do screenshota, np. http://localhost:5173/contracts"),
    question: z.string().optional().describe("Opcjonalne pytanie do analizy"),
    output_path: z.string().optional().describe("Ścieżka gdzie zapisać screenshot (domyślnie: temp/screenshot-{timestamp}.png)"),
  },
  async ({ url, question, output_path }) => {
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

    const prompt = question
      ? `Jesteś senior UI/UX designerem. Przeanalizuj screenshot z URL: ${url}\n\nPytanie: ${question}\n\nDesign system RAO: primary #1D2B53, Montserrat, border-radius 12px. Odpowiedz konkretnie.`
      : `Jesteś senior UI/UX designerem. Przeanalizuj screenshot aplikacji RAO z URL: ${url}\n\nDesign system: primary #1D2B53, Montserrat, border-radius 12px, tło #F8F9FA.\n\nOceń: design system, błędy wizualne, problemy UX. Ogólna ocena: OK / WYMAGA POPRAWY / KRYTYCZNY BŁĄD`;

    const response = await client.messages.create({
      model: "claude-opus-4-5",
      max_tokens: 1024,
      messages: [
        {
          role: "user",
          content: [
            { type: "image", source: { type: "base64", media_type: "image/png", data: imageData } },
            { type: "text", text: prompt },
          ],
        },
      ],
    });

    const result = response.content[0].text;
    const reportPath = screenshotPath.replace(".png", "-vision-report.md");
    fs.writeFileSync(reportPath, `# Vision Report\n\n**URL:** ${url}\n**Screenshot:** ${screenshotPath}\n**Model:** claude-opus-4-5\n**Data:** ${new Date().toISOString()}\n\n${result}\n`);

    return {
      content: [
        { type: "text", text: `📸 Screenshot: ${screenshotPath}\n\n${result}` },
        { type: "text", text: `\n\n📄 Raport zapisany: ${reportPath}` },
      ],
    };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
