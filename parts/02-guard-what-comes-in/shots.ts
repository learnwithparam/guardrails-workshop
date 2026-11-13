// bun parts/02-guard-what-comes-in/shots.ts: capture the pictures Part 2's steps show.
// Each picture is real command output from a sample solution, drawn as a dark terminal.
// Uses Playwright's Chromium. Set PW_CHROMIUM to a Chrome binary if Playwright has none.
import { mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { type Browser, chromium } from "playwright";
import { python } from "../../checks/lib/desk";
import { ROOT } from "../../scripts/structure";

const PART = "parts/02-guard-what-comes-in";

function replayEnvironment(): Record<string, string | undefined> {
  const environment: Record<string, string | undefined> = { ...process.env };
  environment.PYTHONPATH = `${ROOT}:${join(ROOT, "world")}`;
  environment.MARROWFIELD_STATE = mkdtempSync(join(tmpdir(), "shots-"));
  environment.LLM_PROVIDER = "replay";
  return environment;
}

/** Run a command from a step's solution folder and keep what it printed. */
function outputOf(stepFolder: string, args: string[]): string {
  const finished = Bun.spawnSync([python(), ...args], {
    cwd: join(ROOT, PART, stepFolder, "solution"),
    env: replayEnvironment(),
  });
  const output = finished.stdout.toString();
  const withoutWroteLine = output.replace(/^Wrote .*\n?/m, "");
  const withoutRunLog = withoutWroteLine.replace(/^Run log: .*\n?/m, "");
  return withoutRunLog.trimEnd();
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

type Picture = { step: string; command: string; args: string[] };

const LAB = "../../guard_lab.py";

const PICTURES: Picture[] = [
  {
    step: "01-detect-injected-email",
    command: "uv run python ../../guard_lab.py curve --guards guards.py --choose 0.5",
    args: [LAB, "curve", "--guards", "guards.py", "--choose", "0.5"],
  },
  {
    step: "02-reveal-hidden-text",
    command: "uv run desk handle A-14 --guards guards.py",
    args: ["-m", "marrowfield", "desk", "handle", "A-14", "--guards", "guards.py"],
  },
  {
    step: "04-redact-guest-data",
    command: "uv run python ../../guard_lab.py redaction --guards guards.py",
    args: [LAB, "redaction", "--guards", "guards.py"],
  },
];

async function shoot(browser: Browser, picture: Picture) {
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  await page.setContent(terminalHtml(picture.command, outputOf(picture.step, picture.args)));
  const file = join(PART, picture.step, "images", "expected.png");
  mkdirSync(dirname(join(ROOT, file)), { recursive: true });
  await page.locator("#t").screenshot({ path: join(ROOT, file) });
  await page.close();
  console.log(`  ${file}`);
}

const chromiumPath = process.env.PW_CHROMIUM;
const browser = await chromium.launch(chromiumPath ? { executablePath: chromiumPath } : {});
console.log("Capturing:");
for (const picture of PICTURES) await shoot(browser, picture);
await browser.close();
console.log("Done.");
