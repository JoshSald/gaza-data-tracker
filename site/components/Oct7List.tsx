"use client";
// People killed in the 7 October 2023 attack, from oct7database, searched and paged in the browser like the Gaza list.
import { useDeferredValue, useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { fmt, fmtDate } from "@/lib/format";

type Row = [en: string, he: string, age: number | null, sex: "m" | "f" | null, role: string, died: string, inCaptivity: boolean, memorial: string | null];
interface Entry { n: number; en: string; he: string; age: number | null; sex: "m" | "f" | null; role: string; died: string; captivity: boolean; memorial: string | null; key: string }

const PAGE = 100;
const ROLES = ["civilian", "soldier", "police officer", "local security squad", "medical staff", "Shin Bet", "firefighter"];
const AGE_PRESETS: { key: string; label: string; from: string; to: string }[] = [
  { key: "any", label: "Any age", from: "", to: "" },
  { key: "u10", label: "Under 10", from: "", to: "9" },
  { key: "u18", label: "Children (under 18)", from: "", to: "17" },
  { key: "adult", label: "Adults (18–64)", from: "18", to: "64" },
  { key: "senior", label: "Seniors (65+)", from: "65", to: "" },
];
const toAge = (s: string) => (s.trim() === "" || Number.isNaN(Number(s)) ? null : Math.max(0, Math.floor(Number(s))));

/** Lower-case, drop Latin accents and Hebrew vowel points, and fold geresh marks, so searches forgive spelling. */
function normalise(s: string) {
  return s
    .normalize("NFD")
    .replace(/[̀-֑ͯ-ׇ]/g, "")
    .toLowerCase()
    .replace(/[׳״'"`]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .trim();
}

/** "2023-10-07" as a date; "2024-02" or "2023" when the source only knows the month or year. */
function died(d: string) {
  if (d.length === 10) return fmtDate(d);
  if (d.length === 7) return `${new Intl.DateTimeFormat("en-GB", { month: "short", year: "numeric", timeZone: "UTC" }).format(Date.parse(d + "-01"))} (exact date not known)`;
  return `${d} (exact date not known)`;
}

export function Oct7List({ src }: { src: string }) {
  const [entries, setEntries] = useState<Entry[] | null>(null);
  const [failed, setFailed] = useState(false);
  const [query, setQuery] = useState("");
  const [role, setRole] = useState("all");
  const [ageFrom, setAgeFrom] = useState("");
  const [ageTo, setAgeTo] = useState("");
  const [page, setPage] = useState(0);
  const deferredQuery = useDeferredValue(query);

  useEffect(() => {
    fetch(src)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
      .then((d: { records: Row[] }) =>
        setEntries(
          d.records.map(([en, he, age, sex, role, died, captivity, memorial], i) => ({
            n: i + 1, en, he, age, sex, role, died, captivity, memorial, key: normalise(`${en} ${he}`),
          })),
        ),
      )
      .catch(() => setFailed(true));
  }, [src]);

  const matches = useMemo(() => {
    if (!entries) return [];
    const terms = normalise(deferredQuery).split(" ").filter(Boolean);
    const lo = toAge(ageFrom), hi = toAge(ageTo);
    return entries.filter(
      (e) =>
        (role === "all" || e.role === role) &&
        (lo === null || (e.age !== null && e.age >= lo)) &&
        (hi === null || (e.age !== null && e.age <= hi)) &&
        terms.every((t) => e.key.includes(t)),
    );
  }, [entries, deferredQuery, role, ageFrom, ageTo]);

  useEffect(() => setPage(0), [deferredQuery, role, ageFrom, ageTo]);
  const preset = AGE_PRESETS.find((p) => p.from === ageFrom.trim() && p.to === ageTo.trim())?.key ?? "custom";

  if (failed)
    return (
      <p className="note">
        The list could not be loaded. You can download it directly: <a href={src}>oct7-victims.json</a>.
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
          placeholder="Search a name, in English or Hebrew"
          aria-label="Search names"
          className="h-9 min-w-0 flex-[1_1_16rem] rounded-[var(--radius)] bg-card"
        />
        <Select value={role} onValueChange={setRole}>
          <SelectTrigger aria-label="Role" className="h-9 w-48 rounded-[var(--radius)] bg-card">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Everyone</SelectItem>
            {ROLES.map((r) => (
              <SelectItem key={r} value={r}>
                {r[0].toUpperCase() + r.slice(1)}
              </SelectItem>
            ))}
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
          <Input type="number" inputMode="numeric" min={0} max={120} value={ageFrom} onChange={(e) => setAgeFrom(e.target.value)} placeholder="from" aria-label="Age from" className="h-9 w-20 rounded-[var(--radius)] bg-card" />
          <span className="note">to</span>
          <Input type="number" inputMode="numeric" min={0} max={120} value={ageTo} onChange={(e) => setAgeTo(e.target.value)} placeholder="to" aria-label="Age to" className="h-9 w-20 rounded-[var(--radius)] bg-card" />
        </fieldset>
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
              <TableHead className="hidden text-right sm:table-cell">שם</TableHead>
              <TableHead className="num">Age</TableHead>
              <TableHead className="hidden sm:table-cell">Role</TableHead>
              <TableHead className="hidden sm:table-cell">Died</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {shown.map((e) => (
              <TableRow key={e.n}>
                <TableCell className="num hidden text-muted-foreground sm:table-cell">{fmt(e.n)}</TableCell>
                <TableCell className="whitespace-normal">
                  {e.memorial ? (
                    <a href={e.memorial} target="_blank" rel="noopener noreferrer" title="Official memorial record">
                      {e.en}
                    </a>
                  ) : (
                    e.en
                  )}
                  <span className="block text-muted-foreground sm:hidden" lang="he" dir="rtl">{e.he}</span>
                  <span className="block text-xs text-muted-foreground sm:hidden">
                    {e.role} · {died(e.died)}
                    {e.captivity && " · killed in captivity"}
                  </span>
                </TableCell>
                <TableCell className="hidden whitespace-normal text-right sm:table-cell" lang="he" dir="rtl">{e.he}</TableCell>
                <TableCell className="num">{e.age ?? ""}</TableCell>
                <TableCell className="hidden sm:table-cell">{e.role}</TableCell>
                <TableCell className="hidden whitespace-normal sm:table-cell">
                  {died(e.died)}
                  {e.captivity && <span className="block text-xs text-muted-foreground">killed in captivity</span>}
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
