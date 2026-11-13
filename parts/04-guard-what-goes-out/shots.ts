// bun parts/04-guard-what-goes-out/shots.ts: capture the pictures this part's steps show.
// Each picture is the real output of a learner command on the sample solution, in replay mode,
// rendered as a dark terminal about 800 pixels wide. The commands run in throwaway folders.
import { copyFileSync, mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { type Browser, chromium } from "playwright";
import { python } from "../../checks/lib/desk";
import { ROOT } from "../../scripts/structure";

const PART = import.meta.dir;

function replayEnvironment(): Record<string, string | undefined> {
  const environment: Record<string, string | undefined> = { ...process.env };
  environment.PYTHONPATH = `${ROOT}:${join(ROOT, "world")}`;
  environment.MARROWFIELD_STATE = mkdtempSync(join(tmpdir(), "shots-"));
  environment.LLM_PROVIDER = "replay";
  environment.PYTHONDONTWRITEBYTECODE = "1";
  return environment;
}

/** Run python with these arguments in a folder, and keep what it printed, minus "Wrote" lines. */
function printed(folder: string, args: string[]): string {
  const finished = Bun.spawnSync([python(), ...args], { cwd: folder, env: replayEnvironment() });
  const output = finished.stdout.toString();
  return output.replace(/^Wrote .*\n?/gm, "").trimEnd();
}

const emptyFolder = () => mkdtempSync(join(tmpdir(), "shots-work-"));
const stepFolder = (step: string) => join(PART, step);

const ESCAPES: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;" };
const escapeHtml = (text: string) => text.replace(/[&<>]/g, (character) => ESCAPES[character]);

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

type Picture = { step: string; command: string; output: string };

async function shoot(browser: Browser, picture: Picture) {
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  await page.setContent(terminalHtml(picture.command, picture.output));
  const path = join(stepFolder(picture.step), "images", "expected.png");
  mkdirSync(dirname(path), { recursive: true });
  await page.locator("#t").screenshot({ path });
  await page.close();
  console.log(`  ${picture.step}/images/expected.png`);
}

function groundTheReply(): Picture {
  const folder = emptyFolder();
  const step = stepFolder("02-ground-the-reply");
  copyFileSync(join(step, "solution", "guards.py"), join(folder, "guards.py"));
  copyFileSync(join(step, "problem", "messages.jsonl"), join(folder, "messages.jsonl"));
  const output = printed(folder, [join(step, "problem", "try_messages.py")]);
  return { step: "02-ground-the-reply", command: "uv run python try_messages.py", output };
}

const BURST_RUN = "uv run desk run --guards guards.py --set sets/burst.jsonl";

function logEveryDecision(): Picture {
  const folder = emptyFolder();
  const step = stepFolder("03-log-every-decision");
  const guards = join(step, "solution", "guards.py");
  const burst = join(step, "problem", "sets", "burst.jsonl");
  const deskRun = printed(folder, [
    "-m",
    "marrowfield",
    "desk",
    "run",
    "--guards",
    guards,
    "--set",
    burst,
  ]);
  const alert = printed(folder, [join(step, "solution", "alert.py"), "out/decisions.jsonl"]);
  const withoutLogPath = deskRun.replace(/^Run log: .*$/m, "").trimEnd();
  return {
    step: "03-log-every-decision",
    command: `${BURST_RUN} && uv run python alert.py out/decisions.jsonl`,
    output: `${withoutLogPath}\n${alert}`,
  };
}

function defendTheDesk(): Picture {
  const guards = join(stepFolder("04-defend-the-desk"), "solution", "guards.py");
  const outFile = join(emptyFolder(), "score.json");
  const args = ["desk", "score", "--guards", guards, "--heldout", "--by-layer", "--out", outFile];
  return {
    step: "04-defend-the-desk",
    command:
      "uv run desk score --guards guards.py --heldout --by-layer --out out/score-guarded.json",
    output: printed(emptyFolder(), ["-m", "marrowfield", ...args]),
  };
}

const chromiumPath = process.env.PW_CHROMIUM;
const browser = await chromium.launch(chromiumPath ? { executablePath: chromiumPath } : {});
console.log("Capturing:");
for (const picture of [groundTheReply(), logEveryDecision(), defendTheDesk()]) {
  await shoot(browser, picture);
}
await browser.close();
console.log("Done.");
