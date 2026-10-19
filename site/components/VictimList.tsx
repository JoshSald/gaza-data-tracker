"use client";
// The Ministry's list of named victims, searched and paged in the browser. The list is ~7 MB, so it is fetched
// once from /data/lists/ rather than built into the page. Names that independent projects remember on a memorial page
// link to it; those links come from a separate file, matched to the list by the Ministry's Arabic name, age and sex.
import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { fmt } from "@/lib/format";

type Row = [en: string, ar: string, age: number, sex: "m" | "f", update: number];
type LinkRow = [ar: string, age: number, sex: "m" | "f", url: string, project: string, basis: string];
interface Memorial { url: string; project: string; basis: string }
interface Entry { n: number; en: string; ar: string; age: number; sex: "m" | "f"; key: string; memorials: Memorial[] }

const PAGE = 100;
// Shortcuts that fill in the age range. Ages are whole years as the Ministry records them (0 = under one year old).
const AGE_PRESETS: { key: string; label: string; from: string; to: string }[] = [
  { key: "any", label: "Any age", from: "", to: "" },
  { key: "u5", label: "Under 5", from: "", to: "4" },
  { key: "u10", label: "Under 10", from: "", to: "9" },
  { key: "u18", label: "Children (under 18)", from: "", to: "17" },
  { key: "adult", label: "Adults (18–64)", from: "18", to: "64" },
  { key: "senior", label: "Seniors (65+)", from: "65", to: "" },
];
const toAge = (s: string) => (s.trim() === "" || Number.isNaN(Number(s)) ? null : Math.max(0, Math.floor(Number(s))));

/** Lower-case, drop Latin accents and Arabic diacritics, and fold Arabic letter variants, so searches forgive spelling. */
function normalise(s: string) {
  return s
    .normalize("NFD")
    .replace(/[̀-ًͯ-ٰٟ]/g, "")
    .toLowerCase()
    .replace(/[أإآٱ]/g, "ا")
    .replace(/ة/g, "ه")
    .replace(/ى/g, "ي")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}

export function VictimList({ src, links }: { src: string; links: string }) {
  const [entries, setEntries] = useState<Entry[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [query, setQuery] = useState("");
  const [sex, setSex] = useState<"all" | "m" | "f">("all");
  const [onlyLinked, setOnlyLinked] = useState(false);
  const [projects, setProjects] = useState<Record<string, { name: string }>>({});
  const [ageFrom, setAgeFrom] = useState("");
  const [ageTo, setAgeTo] = useState("");
  const [page, setPage] = useState(0);
  const deferredQuery = useDeferredValue(query);

  useEffect(() => {
    const json = (url: string) => fetch(url).then((r) => (r.ok ? r.json() : Promise.reject(r.status)));
    // The list still loads if the links file cannot; the names are then shown without links.
    Promise.all([json(src), json(links).catch(() => ({ projects: {}, records: [] }))])
      .then(([d, l]: [{ records: Row[] }, { projects: Record<string, { name: string }>; records: LinkRow[] }]) => {
        const byKey = new Map<string, Memorial[]>();
        for (const [ar, age, sex, url, project, basis] of l.records) {
          const k = `${ar}|${age}|${sex}`;
          byKey.set(k, [...(byKey.get(k) ?? []), { url, project, basis }]);
        }
        setProjects(l.projects);
        setEntries(
          d.records.map(([en, ar, a, s], i) => ({
            n: i + 1, en, ar, age: a, sex: s, key: normalise(`${en} ${ar}`), memorials: byKey.get(`${ar}|${a}|${s}`) ?? [],
          })),
        );
      })
      .catch(() => setFailed(true));
  }, [src, links]);

  const matches = useMemo(() => {
    if (!entries) return [];
    const terms = normalise(deferredQuery).split(" ").filter(Boolean);
    const lo = toAge(ageFrom) ?? 0, hi = toAge(ageTo) ?? Infinity;
    return entries.filter(
      (e) =>
        (sex === "all" || e.sex === sex) &&
        (!onlyLinked || e.memorials.length > 0) &&
        e.age >= lo &&
        e.age <= hi &&
        terms.every((t) => e.key.includes(t)),
    );
  }, [entries, deferredQuery, sex, onlyLinked, ageFrom, ageTo]);

  useEffect(() => setPage(0), [deferredQuery, sex, onlyLinked, ageFrom, ageTo]);
  const preset = AGE_PRESETS.find((p) => p.from === ageFrom.trim() && p.to === ageTo.trim())?.key ?? "custom";

  if (failed)
    return (
      <p className="note">
        The list could not be loaded. You can download it directly: <a href={src}>named-victims.json</a>.
      </p>
    );

  const pages = Math.max(1, Math.ceil(matches.length / PAGE));
  const shown = matches.slice(page * PAGE, page * PAGE + PAGE);

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search a name, in English or Arabic"
          aria-label="Search names"
          className="h-9 min-w-0 flex-[1_1_16rem] rounded-[var(--radius)] bg-card"
        />
        <Select value={sex} onValueChange={(v) => setSex(v as typeof sex)}>
          <SelectTrigger aria-label="Sex" className="h-9 w-32 rounded-[var(--radius)] bg-card">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All</SelectItem>
            <SelectItem value="f">Female</SelectItem>
            <SelectItem value="m">Male</SelectItem>
          </SelectContent>
        </Select>
        <Select
          value={preset}
          onValueChange={(v) => {
            const p = AGE_PRESETS.find((x) => x.key === v);
            if (p) (setAgeFrom(p.from), setAgeTo(p.to));
          }}
        >
          <SelectTrigger aria-label="Age shortcuts" className="h-9 w-48 rounded-[var(--radius)] bg-card">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {AGE_PRESETS.map((p) => (
              <SelectItem key={p.key} value={p.key}>
                {p.label}
              </SelectItem>
            ))}
            {preset === "custom" && <SelectItem value="custom">Custom range</SelectItem>}
          </SelectContent>
        </Select>
        <fieldset className="flex items-center gap-1.5">
          <legend className="sr-only">Age range</legend>
          <span className="note">Age</span>
          <Input
            type="number"
            inputMode="numeric"
            min={0}
            max={120}
            value={ageFrom}
            onChange={(e) => setAgeFrom(e.target.value)}
            placeholder="from"
            aria-label="Age from"
            className="h-9 w-20 rounded-[var(--radius)] bg-card"
          />
          <span className="note">to</span>
          <Input
            type="number"
            inputMode="numeric"
            min={0}
            max={120}
            value={ageTo}
            onChange={(e) => setAgeTo(e.target.value)}
            placeholder="to"
            aria-label="Age to"
            className="h-9 w-20 rounded-[var(--radius)] bg-card"
          />
        </fieldset>
        <Select value={onlyLinked ? "linked" : "all"} onValueChange={(v) => setOnlyLinked(v === "linked")}>
          <SelectTrigger aria-label="Memorial pages" className="h-9 w-56 rounded-[var(--radius)] bg-card">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">With or without a memorial page</SelectItem>
            <SelectItem value="linked">With a memorial page</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <p className="note" aria-live="polite">
        {entries ? `${fmt(matches.length)} of ${fmt(entries.length)} names` : "Loading the list…"}
      </p>

      <div className="data-table">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="num hidden sm:table-cell">#</TableHead>
              <TableHead>Name</TableHead>
              <TableHead className="hidden text-right sm:table-cell">الاسم</TableHead>
              <TableHead className="num">Age</TableHead>
              <TableHead>Sex</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {shown.map((e) => (
              <TableRow key={e.n}>
                <TableCell className="num hidden text-muted-foreground sm:table-cell">{fmt(e.n)}</TableCell>
                <TableCell className="whitespace-normal">
                  {e.memorials.length ? (
                    <a href={e.memorials[0].url} target="_blank" rel="noopener noreferrer" title={`Memorial page. Matched by: ${e.memorials[0].basis}`}>
                      {e.en}
                    </a>
                  ) : (
                    e.en
                  )}
                  {e.memorials.length > 0 && (
                    <span className="block text-xs text-muted-foreground">
                      {e.memorials.map((m, i) => (
                        <span key={m.url}>
                          {i > 0 && " · "}
                          <a href={m.url} target="_blank" rel="noopener noreferrer" className="text-muted-foreground" title={`Matched by: ${m.basis}`}>
                            {projects[m.project]?.name ?? m.project}
                          </a>
                        </span>
                      ))}
                    </span>
                  )}
                  {/* On narrow screens the Arabic name sits under the English one instead of in its own column. */}
                  <span className="block font-arabic text-muted-foreground sm:hidden" lang="ar" dir="rtl">
                    {e.ar}
                  </span>
                </TableCell>
                <TableCell className="whitespace-normal hidden text-right font-arabic sm:table-cell" lang="ar" dir="rtl">
                  {e.ar}
                </TableCell>
                <TableCell className="num">{e.age}</TableCell>
                <TableCell>
                  <span className="hidden sm:inline">{e.sex === "f" ? "Female" : "Male"}</span>
                  <abbr className="no-underline sm:hidden" title={e.sex === "f" ? "Female" : "Male"}>
                    {e.sex.toUpperCase()}
                  </abbr>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {entries && matches.length > PAGE && (
        <div className="flex items-center justify-between gap-2">
          <Button variant="outline" size="sm" className="rounded-[var(--radius)]" disabled={page === 0} onClick={() => setPage(page - 1)}>
            Previous
          </Button>
          <span className="note">
            Page {fmt(page + 1)} of {fmt(pages)}
          </span>
          <Button variant="outline" size="sm" className="rounded-[var(--radius)]" disabled={page >= pages - 1} onClick={() => setPage(page + 1)}>
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
