// Bezpośrednia analiza screenshotów przez Anthropic Vision API (omija MCP stdio).
// Użycie: node analyze.js <image_path> "<pytanie>"
import Anthropic from "@anthropic-ai/sdk";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import "dotenv/config";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..");

// Wczytaj klucz z .devin/config.json jeśli nie ma w env
let apiKey = process.env.ANTHROPIC_API_KEY;
if (!apiKey) {
  const cfgPath = path.join(REPO_ROOT, ".devin", "config.json");
  if (fs.existsSync(cfgPath)) {
    const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
    apiKey = cfg.mcpServers?.["rao-vision"]?.env?.ANTHROPIC_API_KEY;
  }
}
// Spróbuj .env w repo root
if (!apiKey) {
  const envPath = path.join(REPO_ROOT, ".env");
  if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, "utf8");
    const m = envContent.match(/ANTHROPIC_API_KEY=(.+)/);
    if (m) apiKey = m[1].trim();
  }
}

if (!apiKey) {
  console.error("ERROR: Brak ANTHROPIC_API_KEY (env, .devin/config.json, .env)");
  process.exit(1);
}

const imagePath = process.argv[2];
const question = process.argv[3] || "Przeanalizuj ten screenshot aplikacji RAO. Sprawdź marginesy, spacing, alignment, czy design system jest zachowany (primary #1D2B53, Montserrat, border-radius 12px, tło #F8F9FA). Wymień konkretne problemy z marginesami/spacing.";

if (!imagePath || !fs.existsSync(imagePath)) {
  console.error(`ERROR: Plik nie istnieje: ${imagePath}`);
  process.exit(1);
}

const ext = path.extname(imagePath).toLowerCase();
const mediaType = ext === ".jpg" || ext === ".jpeg" ? "image/jpeg" : "image/png";
const imageData = fs.readFileSync(imagePath).toString("base64");

const client = new Anthropic({ apiKey });

const prompt = `Jesteś senior UI/UX designerem. Przeanalizuj ten screenshot aplikacji RAO (system wynajmu maszyn budowlanych).

Pytanie: ${question}

Design system RAO:
- Kolor primary: #1D2B53 (navy)
- Font: Montserrat
- Border-radius: 12px
- Tło: #F8F9FA lub #FFFFFF
- Spacing: 4/8/12/16/20/24px

Odpowiedz konkretnie:
1. Czy marginesy/spacing są poprawne? Wymień konkretne problemy (np. "karta X ma 0px padding zamiast 20px").
2. Czy alignment jest OK?
3. Czy są broken layout / overflow / misalignment?
4. Ogólna ocena: OK / WYMAGA POPRAWY / KRYTYCZNY BŁĄD`;

console.log(`Analizuję: ${imagePath} (${(imageData.length / 1024).toFixed(0)}KB base64)...`);

try {
  const response = await client.messages.create({
    model: "claude-opus-4-5",
    max_tokens: 2048,
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
  console.log("\n" + "=".repeat(80));
  console.log(result);
  console.log("=".repeat(80));

  const reportPath = imagePath.replace(/\.(png|jpg|jpeg)$/i, "-vision-report.md");
  fs.writeFileSync(reportPath, `# Vision Report\n\n**Plik:** ${imagePath}\n**Model:** claude-opus-4-5\n**Pytanie:** ${question}\n**Data:** ${new Date().toISOString()}\n\n${result}\n`);
  console.log(`\n📄 Raport zapisany: ${reportPath}`);
} catch (e) {
  console.error("ERROR Anthropic API:", e.message);
  if (e.error) console.error(JSON.stringify(e.error, null, 2));
  process.exit(1);
}
