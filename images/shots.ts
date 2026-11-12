// bun run shots: capture every picture the READMEs show, from the real desk page and real command output.
// Uses Playwright's Chromium. Run `bunx playwright install chromium` once, or set PW_CHROMIUM to a Chrome binary.

import { mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { type Browser, chromium } from "playwright";
import { python } from "../checks/lib/desk";
import { ROOT } from "../scripts/structure";

const env = (state: string) => ({
  ...process.env,
  PYTHONPATH: `${ROOT}:${join(ROOT, "world")}`,
  MARROWFIELD_STATE: state,
  LLM_PROVIDER: "replay",
});

/** Run a desk command from a folder and keep its output, for a terminal picture. */
function term(cwd: string, args: string[]): string {
  const p = Bun.spawnSync([python(), "-m", "marrowfield", ...args], {
    cwd: join(ROOT, cwd),
    env: env(mkdtempSync(join(tmpdir(), "shots-"))),
  });
  return p.stdout
    .toString()
    .replace(/^Wrote .*\n?/m, "")
    .trimEnd();
}

const esc = (s: string) =>
  s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" })[c]!);
function terminalHtml(cmd: string, out: string): string {
  return (
    `<html><body style="margin:0;background:#0d1117"><div id="t" style="width:800px;padding:18px 20px;box-sizing:border-box;
    background:#0d1117;color:#d6dde6;font:13px/1.5 ui-monospace,Menlo,Consolas,monospace;white-space:pre-wrap">` +
    `<span style="color:#7ee787">$</span> ${esc(cmd)}\n${esc(out)}</div></body></html>`
  );
}

async function shootTerminal(b: Browser, file: string, cmd: string, out: string) {
  const page = await b.newPage({ deviceScaleFactor: 2 });
  await page.setContent(terminalHtml(cmd, out));
  mkdirSync(dirname(join(ROOT, file)), { recursive: true });
  await page.locator("#t").screenshot({ path: join(ROOT, file) });
  await page.close();
  console.log(`  ${file}`);
}

async function withServer(flag: string, port: number, fn: (url: string) => Promise<void>) {
  const srv = Bun.spawn(
    [python(), "-m", "marrowfield", "desk", "serve", flag, "--port", String(port)],
    { cwd: ROOT, env: env(mkdtempSync(join(tmpdir(), "shots-"))), stdout: "pipe" },
  );
  const url = `http://127.0.0.1:${port}`;
  for (let i = 0; i < 100; i++) {
    try {
      await fetch(`${url}/api/state`);
      break;
    } catch {
      await Bun.sleep(100);
    }
  }
  try {
    await fn(url);
  } finally {
    srv.kill();
  }
}

async function shootPage(b: Browser, url: string, email: string, file: string) {
  const page = await b.newPage({ viewport: { width: 1360, height: 820 }, deviceScaleFactor: 2 });
  await page.goto(`${url}/?email=${email}&run=1`);
  await page.waitForSelector(".note", { timeout: 60_000 });
  await page.waitForSelector("#score:not(.muted)", { timeout: 120_000 });
  await page.screenshot({ path: join(ROOT, file), fullPage: true });
  await page.close();
  console.log(`  ${file}`);
}

const b = await chromium.launch(
  process.env.PW_CHROMIUM ? { executablePath: process.env.PW_CHROMIUM } : {},
);
console.log("Capturing:");
await withServer("--reference", 8311, async (url) => {
  await shootPage(b, url, "MK-07", "images/finished-system.png");
  await shootPage(b, url, "MK-11", "00-orientation/images/first-run.png");
});
await withServer("--open", 8312, async (url) => {
  await shootPage(
    b,
    url,
    "MK-01",
    "parts/01-break-the-desk/01-run-the-open-desk/images/expected.png",
  );
});
const step = (p: string) => `parts/01-break-the-desk/${p}`;
await shootTerminal(
  b,
  "00-orientation/01-meet-the-desk/images/expected.png",
  "uv run desk score --reference --by-layer --out out/reference-score.json",
  term("00-orientation/01-meet-the-desk/solution", [
    "desk",
    "score",
    "--reference",
    "--by-layer",
    "--out",
    join(tmpdir(), "s.json"),
  ]),
);
await shootTerminal(
  b,
  `${step("02-play-the-gatehouse")}/images/expected.png`,
  "uv run desk gatehouse --out out/flags.json",
  term(`${step("02-play-the-gatehouse")}/solution`, [
    "desk",
    "gatehouse",
    "--out",
    join(tmpdir(), "f.json"),
  ]),
);
await shootTerminal(
  b,
  `${step("05-score-the-open-desk")}/images/expected.png`,
  "uv run desk score --open --out out/score-open.json",
  term(`${step("05-score-the-open-desk")}/solution`, [
    "desk",
    "score",
    "--open",
    "--out",
    join(tmpdir(), "o.json"),
  ]),
);
await b.close();
console.log("Done.");
