// Reads the repository's data/ folder at build time. Nothing here runs in the browser.
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { fmtDate } from "./format";

export type Kind = "count" | "claim" | "estimate";
export type Bound = "exact" | "at_least" | "approximate";

export interface Source {
  id: string;
  name: string;
  type: string;
  affiliation: string;
  url: string;
  notes?: string;
}

export interface Metric {
  id: string;
  label: string;
  definition: string;
  unit: string;
  cumulative: boolean;
}

export interface Observation {
  id: string;
  metric: string;
  value: number;
  low?: number;
  high?: number;
  kind: Kind;
  bound: Bound;
  source: string;
  as_of: string;
  period_start: string | null;
  period_end: string;
  dimensions?: Record<string, string>;
  document: { url: string; publisher: string; retrieved_at: string; archive?: string; sha256?: string; note?: string };
  quote?: string;
  caveat?: string;
  supersedes?: string;
  added_by: string;
}

const DATA = join(process.cwd(), "..", "data");
const read = <T,>(path: string): T => JSON.parse(readFileSync(path, "utf8")) as T;

let cache: { sources: Source[]; metrics: Metric[]; observations: Observation[] } | null = null;

export function loadAll() {
  if (cache) return cache;
  const sources = read<Source[]>(join(DATA, "sources.json"));
  const metrics = read<Metric[]>(join(DATA, "metrics.json"));
  const dir = join(DATA, "observations");
  const all = readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .flatMap((f) => read<Observation[]>(join(dir, f)));
  // A correction replaces the observation it names; the replaced one stays in the data but is not shown.
  const superseded = new Set(all.map((o) => o.supersedes).filter(Boolean));
  const observations = all.filter((o) => !superseded.has(o.id));
  cache = { sources, metrics, observations };
  return cache;
}

export function source(id: string): Source {
  const s = loadAll().sources.find((x) => x.id === id);
  if (!s) throw new Error(`Unknown source ${id}`);
  return s;
}

export function metric(id: string): Metric {
  const m = loadAll().metrics.find((x) => x.id === id);
  if (!m) throw new Error(`Unknown metric ${id}`);
  return m;
}

interface Filter {
  source?: string;
  kind?: Kind;
  periodStart?: string | null;
  dims?: Record<string, string>;
}

function matches(o: Observation, f: Filter) {
  if (f.source && o.source !== f.source) return false;
  if (f.kind && o.kind !== f.kind) return false;
  if (f.periodStart !== undefined && o.period_start !== f.periodStart) return false;
  if (f.dims) {
    for (const [k, v] of Object.entries(f.dims)) if (o.dimensions?.[k] !== v) return false;
  }
  return true;
}

export function series(metricId: string, f: Filter = {}): Observation[] {
  return loadAll()
    .observations.filter((o) => o.metric === metricId && matches(o, f))
    .sort((a, b) => a.as_of.localeCompare(b.as_of));
}

/** The most recent observation for a metric. Throws at build time if there is none, so a gap never ships silently. */
export function latest(metricId: string, f: Filter = {}): Observation {
  const rows = series(metricId, f);
  if (!rows.length) throw new Error(`No observation for ${metricId} ${JSON.stringify(f)}`);
  return rows[rows.length - 1];
}

export function all(metricId: string): Observation[] {
  return series(metricId);
}

export { fmt, fmtCompact, fmtDate } from "./format";

export function fmtPeriod(o: Observation) {
  if (!o.period_start) return `to ${fmtDate(o.period_end)}`;
  if (o.period_start === o.period_end) return fmtDate(o.period_end);
  return `${fmtDate(o.period_start)} – ${fmtDate(o.period_end)}`;
}

export function boundPrefix(b: Bound) {
  return b === "at_least" ? "at least " : b === "approximate" ? "about " : "";
}

export interface NamedVictimsMeta {
  source: string;
  document: Observation["document"];
  includes_until: string;
  list_updated: string;
  note: string;
  count: number;
}

/** About the named-victims list, without its records (the page loads those in the browser). */
export function namedVictimsMeta(): NamedVictimsMeta {
  const { records, ...meta } = read<NamedVictimsMeta & { records: unknown[] }>(join(DATA, "lists", "named-victims.json"));
  return { ...meta, count: records.length };
}

export type HospitalStatus = "partially_functioning" | "not_functioning" | "destroyed" | "services_reported";

export interface Hospital {
  name: string;
  ar_name: string;
  type: string;
  governorate: string;
  beds: number | null;
  latest?: {
    status: HospitalStatus;
    as_of: string;
    quote: string;
    document: Observation["document"];
  };
}

/** The 36 hospitals, each with WHO's newest statement naming it, if there is one. */
export function hospitals(): { list: Hospital[]; listDate: string | null; listDoc: Observation["document"]; sourceNote: string } {
  const lists = join(DATA, "lists");
  const list = read<{ hospitals: Hospital[]; list_date: string | null; document: Observation["document"]; source_note: string }>(join(lists, "hospitals.json"));
  const statements = read<{ statements: (Hospital["latest"] & { hospital: string })[] }>(join(lists, "hospital-status.json")).statements;
  const latest = new Map<string, Hospital["latest"]>();
  for (const s of [...statements].sort((a, b) => a!.as_of.localeCompare(b!.as_of))) latest.set(s!.hospital, s);
  return {
    list: list.hospitals.map((h) => ({ ...h, latest: latest.get(h.name) })),
    listDate: list.list_date,
    listDoc: list.document,
    sourceNote: list.source_note,
  };
}
