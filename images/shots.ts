// bun run shots: capture every picture the READMEs show,
// from the real desk page and real command output.
// Uses Playwright's Chromium. Run `bunx playwright install chromium` once,
// or set PW_CHROMIUM to a Chrome binary.

import { mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { type Browser, chromium } from "playwright";
import { python } from "../checks/lib/desk";
import { ROOT } from "../scripts/structure";

const PART_ONE = "parts/01-break-the-desk";

function replayEnvironment(): Record<string, string | undefined> {
  const environment: Record<string, string | undefined> = { ...process.env };
  environment.PYTHONPATH = `${ROOT}:${join(ROOT, "world")}`;
  // Every picture starts from a fresh, throwaway world, so your own state never shows.
  environment.MARROWFIELD_STATE = mkdtempSync(join(tmpdir(), "shots-"));
  environment.LLM_PROVIDER = "replay";
  return environment;
}

/** Run a desk command from a folder and keep its output, for a terminal picture. */
function terminalOutput(folder: string, args: string[]): string {
  const finished = Bun.spawnSync([python(), "-m", "marrowfield", ...args], {
    cwd: join(ROOT, folder),
    env: replayEnvironment(),
  });
  const output = finished.stdout.toString();
  const withoutWroteLine = output.replace(/^Wrote .*\n?/m, "");
  return withoutWroteLine.trimEnd();
}

const HTML_ESCAPES: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;" };

const escapeHtml = (text: string) => text.replace(/[&<>]/g, (character) => HTML_ESCAPES[character]);

const TERMINAL_STYLE = [
  "width:800px",
  "padding:18px 20px",
  "box-sizing:border-box",
  "background:#0d1117",
  "color:#d6dde6",
  "font:13px/1.5 ui-monospace,Menlo,Consolas,monospace",
  "white-space:pre-wrap",
].join(";");

function terminalHtml(command: string, output: string): string {
  const prompt = `<span style="color:#7ee787">$</span> ${escapeHtml(command)}`;
  const terminal = `<div id="t" style="${TERMINAL_STYLE}">${prompt}\n${escapeHtml(output)}</div>`;
  return `<html><body style="margin:0;background:#0d1117">${terminal}</body></html>`;
}

type TerminalPicture = { file: string; command: string; output: string };

async function shootTerminal(browser: Browser, picture: TerminalPicture) {
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  await page.setContent(terminalHtml(picture.command, picture.output));
  const path = join(ROOT, picture.file);
  mkdirSync(dirname(path), { recursive: true });
  await page.locator("#t").screenshot({ path });
  await page.close();
  console.log(`  ${picture.file}`);
}

async function waitUntilServing(url: string) {
  for (let attempt = 0; attempt < 100; attempt++) {
    try {
      await fetch(`${url}/api/state`);
      return;
    } catch {
      await Bun.sleep(100);
    }
  }
}

/** Start the desk page with one desk ("--open" or "--reference"), use it, then stop it. */
async function withServer(desk: string, port: number, useIt: (url: string) => Promise<void>) {
  const command = [python(), "-m", "marrowfield", "desk", "serve", desk, "--port", String(port)];
  const server = Bun.spawn(command, { cwd: ROOT, env: replayEnvironment(), stdout: "pipe" });
  const url = `http://127.0.0.1:${port}`;
  await waitUntilServing(url);
  try {
    await useIt(url);
  } finally {
    server.kill();
  }
}

async function shootPage(browser: Browser, url: string, emailId: string, file: string) {
  const viewport = { width: 1360, height: 820 };
  const page = await browser.newPage({ viewport, deviceScaleFactor: 2 });
  await page.goto(`${url}/?email=${emailId}&run=1`);
  await page.waitForSelector(".note", { timeout: 60_000 });
  await page.waitForSelector("#score:not(.muted)", { timeout: 120_000 });
  await page.screenshot({ path: join(ROOT, file), fullPage: true });
  await page.close();
  console.log(`  ${file}`);
}

const outFile = (name: string) => join(tmpdir(), name);

function terminalPictures(): TerminalPicture[] {
  const meetTheDesk = "00-orientation/01-meet-the-desk";
  const gatehouse = `${PART_ONE}/02-play-the-gatehouse`;
  const scoreOpen = `${PART_ONE}/05-score-the-open-desk`;
  const referenceScore = ["desk", "score", "--reference", "--by-layer"];
  return [
    {
      file: `${meetTheDesk}/images/expected.png`,
      command: "uv run desk score --reference --by-layer --out out/reference-score.json",
      output: terminalOutput(`${meetTheDesk}/solution`, [
        ...referenceScore,
        "--out",
        outFile("s.json"),
      ]),
    },
    {
      file: `${gatehouse}/images/expected.png`,
      command: "uv run desk gatehouse --out out/flags.json",
      output: terminalOutput(`${gatehouse}/solution`, [
        "desk",
        "gatehouse",
        "--out",
        outFile("f.json"),
      ]),
    },
    {
      file: `${scoreOpen}/images/expected.png`,
      command: "uv run desk score --open --out out/score-open.json",
      output: terminalOutput(`${scoreOpen}/solution`, [
        "desk",
        "score",
        "--open",
        "--out",
        outFile("o.json"),
      ]),
    },
  ];
}

const chromiumPath = process.env.PW_CHROMIUM;
const browser = await chromium.launch(chromiumPath ? { executablePath: chromiumPath } : {});
console.log("Capturing:");
await withServer("--reference", 8311, async (url) => {
  await shootPage(browser, url, "MK-07", "images/finished-system.png");
  await shootPage(browser, url, "MK-11", "00-orientation/images/first-run.png");
});
await withServer("--open", 8312, async (url) => {
  await shootPage(browser, url, "MK-01", `${PART_ONE}/01-run-the-open-desk/images/expected.png`);
});
for (const picture of terminalPictures()) await shootTerminal(browser, picture);
await browser.close();
console.log("Done.");
