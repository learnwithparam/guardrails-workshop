// Reads the repo layout once. Every other script asks this file where things are.
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { basename, join } from "node:path";

export const ROOT = join(import.meta.dir, "..");

export type Step = {
  name: string; // verb-the-thing, also the command argument
  dir: string;
  part: string;
  meta: { minutes: number; screen: boolean; solution: boolean };
};
export type Part = { name: string; dir: string; steps: Step[] };

type StepSettings = { minutes?: number; screen?: boolean; solution?: boolean };

// The orientation's step lives in 00-orientation/ and counts as a part named "orientation".
const ORIENTATION = join(ROOT, "00-orientation");

function subfolders(folder: string): string[] {
  if (!existsSync(folder)) return [];
  const entries = readdirSync(folder);
  const folders = entries.filter((entry) => statSync(join(folder, entry)).isDirectory());
  return folders.sort();
}

// Folders keep an order prefix for sorting only. Learners never type it.
export const bareName = (folder: string) => folder.replace(/^\d+-/, "");

const hasSettings = (folder: string) => existsSync(join(folder, "step.toml"));

function readSettings(stepFolder: string): StepSettings {
  const settingsPath = join(stepFolder, "step.toml");
  if (!hasSettings(stepFolder)) return {};
  return Bun.TOML.parse(readFileSync(settingsPath, "utf8")) as StepSettings;
}

function loadStep(partFolder: string, partName: string, stepName: string): Step {
  const stepFolder = join(partFolder, stepName);
  const settings = readSettings(stepFolder);
  return {
    name: bareName(stepName),
    dir: stepFolder,
    part: bareName(partName),
    meta: {
      minutes: Number(settings.minutes ?? 0),
      screen: Boolean(settings.screen),
      solution: Boolean(settings.solution),
    },
  };
}

// A step folder starts with its order number, such as 01-run-the-open-desk. Other folders, such as the
// __pycache__ that Python writes when a lab runs, are not steps.
const looksLikeStep = (folderName: string) => /^\d+-/.test(folderName);

// In the orientation only folders with a step.toml are steps; it also holds images/ and pages.
function stepFolderNames(partFolder: string): string[] {
  const names = subfolders(partFolder).filter(looksLikeStep);
  if (partFolder !== ORIENTATION) return names;
  return names.filter((name) => hasSettings(join(partFolder, name)));
}

function partFolders(): string[] {
  const partsFolder = join(ROOT, "parts");
  const folders = subfolders(partsFolder).map((name) => join(partsFolder, name));
  const orientationHasSteps = stepFolderNames(ORIENTATION).length > 0;
  if (orientationHasSteps) folders.unshift(ORIENTATION);
  return folders;
}

function loadPart(partFolder: string): Part {
  const partName = partFolder === ORIENTATION ? "orientation" : basename(partFolder);
  const steps = stepFolderNames(partFolder).map((stepName) =>
    loadStep(partFolder, partName, stepName),
  );
  return { name: bareName(partName), dir: partFolder, steps };
}

export function parts(): Part[] {
  return partFolders().map(loadPart);
}

export const allSteps = () => parts().flatMap((part) => part.steps);

export function findStep(name: string): Step | undefined {
  return allSteps().find((step) => step.name === name);
}
