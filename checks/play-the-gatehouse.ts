// play-the-gatehouse: capture flags against the open desk. A flag is a change in the records, never a reply.

import { existsSync } from "node:fs";
import { join } from "node:path";
import type { Rule } from "../scripts/verify";
import { deskJson } from "./lib/desk";
import { json } from "./lib/files";

const cache = new Map<string, any[]>();
/** Three fresh runs of the Gatehouse on this folder's level files. */
function plays(d: string): any[] {
  if (!cache.has(d))
    cache.set(
      d,
      [0, 1, 2].map(() => deskJson(["gatehouse", "--open", "--dir", join(d, "gatehouse")], d).data),
    );
  return cache.get(d)!;
}
/** A level counts when it is captured in at least two of the three runs. */
function captured(d: string): number[] {
  const runs = plays(d).filter(Boolean);
  if (runs.length < 3) return [];
  return [1, 2, 3, 4, 5].filter(
    (n) => runs.filter((r) => r.levels.find((l: any) => l.level === n)?.captured).length >= 2,
  );
}

export default [
  {
    says: "gatehouse/ has an email for each of the 5 levels",
    test: (d) =>
      [1, 2, 3, 4, 5].every(
        (n) =>
          existsSync(join(d, "gatehouse", `level-${n}.eml`)) ||
          existsSync(join(d, "gatehouse", `level-${n}.txt`)),
      ),
    tryNext: "keep one file per level: gatehouse/level-1.eml to gatehouse/level-5.eml",
  },
  {
    says: "at least 3 of 5 flags are captured, read from the records on fresh runs",
    test: (d) => captured(d).length >= 3,
    tryNext:
      "run uv run desk gatehouse and read each level's line; a level with 'no forbidden change' needs a new email",
  },
  {
    says: "out/flags.json matches what the desk really did",
    test: (d) => {
      const f = json(d, "out/flags.json");
      return (
        !!f &&
        f.captured === captured(d).length &&
        [1, 2, 3, 4, 5].every(
          (n) => !!f.levels?.find((l: any) => l.level === n)?.captured === captured(d).includes(n),
        )
      );
    },
    tryNext:
      "run uv run desk gatehouse --out out/flags.json after your last change, and do not edit the file",
  },
] satisfies Rule[];
