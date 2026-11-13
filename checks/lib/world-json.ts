// The shapes of the JSON the world writes: set rows, run logs and the files `desk ... --out` saves.
// biome-ignore-all lint/style/useNamingConvention: these keys keep the world's snake_case spelling.

/** One end state a benign email should reach, for example { kind: "invoice_paid" }. */
export type ExpectedChange = {
  kind: string;
  order?: string;
  delivery?: string;
  invoice?: string;
  supplier?: string;
  site?: string;
};

/** One row of a set file. An attack has a category and expect.forbidden.
 * A benign row has an expect list. */
export type SetRow = {
  id: string;
  raw: string;
  category?: string;
  hard_negative?: boolean;
  tags?: string[];
  expect?: { forbidden?: string } | ExpectedChange[];
};

/** A change the desk made to the records, for example { kind: "credit_note", amount: 32.5 }. */
export type RecordChange = { kind: string; [detail: string]: unknown };

/** One line of a run's results.jsonl: what one email did to the records. */
export type EmailResult = {
  email_id: string;
  held: boolean;
  actions: { tool: string; verdict: string; rule: string }[];
  changes: RecordChange[];
  forbidden: RecordChange[];
};

/** One email in the file `desk run --out` writes.
 * A benign run fills ok; an attack run fills forbidden. */
export type RunEmail = {
  id: string;
  ok?: boolean;
  why?: string;
  held: boolean;
  changes: RecordChange[];
  forbidden: string[];
};

export type RunFile = {
  desk: string;
  utility?: { rate: number; passed: number; n: number };
  emails: RunEmail[];
};

type Rate = { rate: number; n: number };

export type ScoreFile = {
  desk: string;
  runs: number;
  seed: number;
  attacks_file: string | null;
  attacks_sha256: string | null;
  benign_file: string | null;
  benign_sha256: string | null;
  utility: Rate & { passed: number; hard_negatives: Rate };
  security: Rate & { stopped: number; by_category: Record<string, Rate> };
  by_layer?: unknown[];
};

export type GatehouseLevel = { level: number; captured: boolean };

export type GatehouseFile = { captured: number; levels: GatehouseLevel[] };
