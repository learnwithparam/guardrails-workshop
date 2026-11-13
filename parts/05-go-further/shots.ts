// bun parts/05-go-further/shots.ts: capture the pictures this part's steps show.
// Each picture is the real output of a learner command on the sample solution, in replay mode,
// rendered as a dark terminal about 800 pixels wide. The commands run in throwaway folders.
// biome-ignore-all lint/style/useNamingConvention: keys keep the world's snake_case and file names.
import { mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { type Browser, chromium } from "playwright";
import { replayEnvironment, type Switches, spawnPython } from "./guard-calls";

const PART = import.meta.dir;
const solutionOf = (step: string) => join(PART, step, "solution");
const emptyFolder = () => mkdtempSync(join(tmpdir(), "shots-work-"));

/** Run python in a folder and keep what it printed, minus lines that name a temporary path. */
function printed(folder: string, args: string[], guards = "", switches: Switches = {}): string {
  const environment = replayEnvironment(emptyFolder(), guards, switches);
  const ran = spawnPython(args, environment, folder, switches.withPackage);
  const withoutPaths = ran.out.replace(/^(Wrote|Run log:) .*\n?/gm, "");
  return withoutPaths.replace(/^\{.*\}\n?/gm, "").trimEnd();
}

const ESCAPES: Record<string, string> = { "&": "&amp;", "<": "&lt;", ">": "&gt;" };
const escapeHtml = (value: string) => value.replace(/[&<>]/g, (character) => ESCAPES[character]);

const TERMINAL_STYLE = [
  "width:800px",
  "padding:18px 20px",
  "box-sizing:border-box",
  "background:#0d1117",
  "color:#d6dde6",
  "font:13px/1.5 ui-monospace,Menlo,Consolas,monospace",
  "white-space:pre-wrap",
].join(";");

type Picture = { step: string; commands: { command: string; output: string }[] };

function terminalHtml(picture: Picture): string {
  const blocks = picture.commands.map(({ command, output }) => {
    const prompt = `<span style="color:#7ee787">$</span> ${escapeHtml(command)}`;
    return `${prompt}\n${escapeHtml(output)}`;
  });
  const terminal = `<div id="t" style="${TERMINAL_STYLE}">${blocks.join("\n\n")}</div>`;
  return `<html><body style="margin:0;background:#0d1117">${terminal}</body></html>`;
}

async function shoot(browser: Browser, picture: Picture) {
  const page = await browser.newPage({ deviceScaleFactor: 2 });
  await page.setContent(terminalHtml(picture));
  const path = join(PART, picture.step, "images", "expected.png");
  mkdirSync(dirname(path), { recursive: true });
  await page.locator("#t").screenshot({ path });
  await page.close();
  console.log(`  ${picture.step}/images/expected.png`);
}

const switchFile = join(PART, "switches.py");
const deskRun = (set: string) => [
  "-m",
  "marrowfield",
  "desk",
  "run",
  "--guards",
  switchFile,
  "--set",
  set,
];
const firstLines = (output: string, count: number) => output.split("\n").slice(0, count).join("\n");

function blockUntrustedPayees(): Picture {
  const solution = solutionOf("02-block-untrusted-payees");
  const guards = join(solution, "guards.py");
  const detectorOff: Switches = { detector: "off" };
  const prefix =
    "GUARDS_UNDER_TEST=guards.py DETECTOR=off uv run desk run --guards ../../switches.py";
  const commands = ["attacks", "heldout", "benign"].map((set) => ({
    command: `${prefix} --set ${set}`,
    output: printed(solution, deskRun(set), guards, detectorOff),
  }));
  return { step: "02-block-untrusted-payees", commands };
}

const SWITCHED_ATTACKS = "--guards ../../switches.py --set attacks";

function swapInAGuardFramework(): Picture {
  const solution = solutionOf("03-swap-in-a-guard-framework");
  const switches: Switches = { layers: "output", withPackage: "nemoguardrails==0.24.1" };
  const commandFor: Record<string, string> = {
    "own_guards.py": "uv run desk run",
    "nemo_guards.py": "uv run --with nemoguardrails==0.24.1 desk run",
  };
  const commands = Object.entries(commandFor).map(([file, deskCommand]) => ({
    command: `GUARDS_UNDER_TEST=${file} LAYERS=output ${deskCommand} ${SWITCHED_ATTACKS}`,
    output: firstLines(printed(solution, deskRun("attacks"), join(solution, file), switches), 1),
  }));
  return { step: "03-swap-in-a-guard-framework", commands };
}

function runTheAgentdojoBankingSuite(): Picture {
  const solution = solutionOf("05-run-the-agentdojo-banking-suite");
  const probe = [join(PART, "agentdojo_probe.py"), "agentdojo_defence.py"];
  const output = printed(solution, probe, "", { withPackage: "agentdojo==0.1.35" });
  const command =
    "uv run --with agentdojo==0.1.35 python ../../agentdojo_probe.py agentdojo_defence.py";
  return { step: "05-run-the-agentdojo-banking-suite", commands: [{ command, output }] };
}

function priceTheGuards(): Picture {
  const solution = solutionOf("07-price-the-guards");
  const output = printed(solution, [join(solution, "price.py")]);
  return { step: "07-price-the-guards", commands: [{ command: "uv run python price.py", output }] };
}

const chromiumPath = process.env.PW_CHROMIUM;
const browser = await chromium.launch(chromiumPath ? { executablePath: chromiumPath } : {});
console.log("Capturing:");
const pictures = [
  blockUntrustedPayees(),
  swapInAGuardFramework(),
  runTheAgentdojoBankingSuite(),
  priceTheGuards(),
];
for (const picture of pictures) await shoot(browser, picture);
await browser.close();
console.log("Done.");
