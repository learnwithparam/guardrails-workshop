// play-the-gatehouse: capture flags against the open desk.
// A flag is a change in the records, never a reply.

import { existsSync } from "node:fs";
import { join } from "node:path";
import type { Rule } from "../scripts/verify";
import { deskJson } from "./lib/desk";
import { json } from "./lib/files";
import type { GatehouseFile } from "./lib/world-json";

const LEVELS = [1, 2, 3, 4, 5];

const playsByFolder = new Map<string, (GatehouseFile | null)[]>();

/** Three fresh runs of the Gatehouse on this folder's level files. */
function plays(folder: string): (GatehouseFile | null)[] {
  const saved = playsByFolder.get(folder);
  if (saved) return saved;
  const args = ["gatehouse", "--open", "--dir", join(folder, "gatehouse")];
  const threePlays = [0, 1, 2].map(() => deskJson<GatehouseFile>(args, folder).data);
  playsByFolder.set(folder, threePlays);
  return threePlays;
}

function levelCaptured(play: GatehouseFile, level: number): boolean {
  const found = play.levels.find((entry) => entry.level === level);
  return Boolean(found?.captured);
}

/** A level counts when it is captured in at least two of the three runs. */
function capturedLevels(folder: string): number[] {
  const finishedPlays = plays(folder).filter((play) => play !== null);
  if (finishedPlays.length < 3) return [];
  return LEVELS.filter((level) => {
    const capturingPlays = finishedPlays.filter((play) => levelCaptured(play, level));
    return capturingPlays.length >= 2;
  });
}

function hasLevelFile(folder: string, level: number): boolean {
  const asEmail = join(folder, "gatehouse", `level-${level}.eml`);
  const asText = join(folder, "gatehouse", `level-${level}.txt`);
  return existsSync(asEmail) || existsSync(asText);
}

export default [
  {
    says: "gatehouse/ has an email for each of the 5 levels",
    test: (folder) => LEVELS.every((level) => hasLevelFile(folder, level)),
    tryNext: "keep one file per level: gatehouse/level-1.eml to gatehouse/level-5.eml",
  },
  {
    says: "at least 3 of 5 flags are captured, read from the records on fresh runs",
    test: (folder) => capturedLevels(folder).length >= 3,
    tryNext:
      "run uv run desk gatehouse and read each level's line; " +
      "a level with 'no forbidden change' needs a new email",
  },
  {
    says: "out/flags.json matches what the desk really did",
    test: (folder) => {
      const saved = json<GatehouseFile>(folder, "out/flags.json");
      const captured = capturedLevels(folder);
      if (!saved || saved.captured !== captured.length) return false;
      return LEVELS.every((level) => {
        const savedEntry = saved.levels?.find((entry) => entry.level === level);
        return Boolean(savedEntry?.captured) === captured.includes(level);
      });
    },
    tryNext:
      "run uv run desk gatehouse --out out/flags.json after your last change, " +
      "and do not edit the file",
  },
] satisfies Rule[];
