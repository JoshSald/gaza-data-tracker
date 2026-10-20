"use client";
// The 36 hospitals with WHO's newest statement naming each, filtered in the browser by status, type, area and how
// recent the statement is. The list is small, so it is passed in from the page rather than fetched.
import { useState } from "react";
import { HospitalStatusBadge, HospitalStatusDot, NO_STATUS, STATUS_LABEL, type HospitalStatus } from "@/components/HospitalStatus";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { fmt, fmtDate } from "@/lib/format";

export interface HospitalRow {
  name: string;
  ar_name: string;
  type: string;
  governorate: string;
  beds: number | null;
  latest?: { status: HospitalStatus; as_of: string; quote: string; url: string };
}

const GOVERNORATES = ["North Gaza", "Gaza", "Deir Albalah", "Khan Younis", "Rafah"];
const areaName = (g: string) => (g === "Deir Albalah" ? "Deir al-Balah" : g);
const STATUSES: HospitalStatus[] = ["partially_functioning", "services_reported", "not_functioning", "destroyed"];
const RECENCY = [
  { key: "any", label: "Any date", months: null },
  { key: "6", label: "Named in the last 6 months", months: 6 },
  { key: "12", label: "Named in the last 12 months", months: 12 },
];

function monthsAgo(n: number) {
  const d = new Date();
  d.setUTCMonth(d.getUTCMonth() - n);
  return d.toISOString().slice(0, 10);
}

export function HospitalList({ hospitals }: { hospitals: HospitalRow[] }) {
  const [status, setStatus] = useState("all");
  const [type, setType] = useState("all");
  const [area, setArea] = useState("all");
  const [recency, setRecency] = useState("any");

  const types = [...new Set(hospitals.map((h) => h.type))].sort();
  const months = RECENCY.find((r) => r.key === recency)?.months ?? null;
  const since = months === null ? null : monthsAgo(months);
  const shown = hospitals.filter(
    (h) =>
      (status === "all" || (status === "none" ? !h.latest : h.latest?.status === status)) &&
      (type === "all" || h.type === type) &&
      (area === "all" || h.governorate === area) &&
      (since === null || (h.latest !== undefined && h.latest.as_of >= since)),
  );
  const filtered = status !== "all" || type !== "all" || area !== "all" || recency !== "any";

  const select = (label: string, value: string, set: (v: string) => void, options: { value: string; label: string }[], width = "sm:w-48") => (
    <Select value={value} onValueChange={set}>
      <SelectTrigger aria-label={label} className={`h-9 w-full ${width} rounded-[var(--radius)] bg-card`}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );

  return (
    <div className="grid grid-cols-[minmax(0,1fr)] gap-3">
      <div className="grid grid-cols-2 items-center gap-2 sm:flex sm:flex-wrap">
        {select("Status", status, setStatus, [
          { value: "all", label: "Any status" },
          ...STATUSES.map((s) => ({ value: s, label: STATUS_LABEL[s] })),
          { value: "none", label: NO_STATUS },
        ], "sm:w-56")}
        {select("Type", type, setType, [{ value: "all", label: "Any type" }, ...types.map((t) => ({ value: t, label: t }))], "sm:w-40")}
        {select("Area", area, setArea, [{ value: "all", label: "Any area" }, ...GOVERNORATES.map((g) => ({ value: g, label: areaName(g) }))], "sm:w-40")}
        {select("How recent", recency, setRecency, RECENCY.map((r) => ({ value: r.key, label: r.label })), "sm:w-60")}
        {filtered && (
          <button
            type="button"
            className="note underline underline-offset-2"
            onClick={() => (setStatus("all"), setType("all"), setArea("all"), setRecency("any"))}
          >
            Clear filters
          </button>
        )}
      </div>
      <p className="note" aria-live="polite">
        {fmt(shown.length)} of {fmt(hospitals.length)} hospitals
      </p>

      <div className="data-table">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Hospital</TableHead>
              <TableHead>Latest status named by WHO</TableHead>
              <TableHead className="hidden sm:table-cell">Date</TableHead>
              <TableHead className="num hidden sm:table-cell">Beds before the war</TableHead>
              <TableHead className="hidden sm:table-cell">Type</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {GOVERNORATES.flatMap((g) => {
              const rows = shown.filter((h) => h.governorate === g);
              if (!rows.length) return [];
              return [
                <TableRow key={g} className="hover:bg-transparent">
                  <TableCell colSpan={5} className="pt-4 font-mono text-[0.6875rem] tracking-[0.06em] text-muted-foreground uppercase">
                    {areaName(g)}
                  </TableCell>
                </TableRow>,
                ...rows.map((h) => (
                  <TableRow key={h.name}>
                    <TableCell className="whitespace-normal">
                      <span className="inline-flex items-baseline gap-2">
                        <HospitalStatusDot status={h.latest?.status} />
                        <span className="font-medium">{h.name}</span>
                      </span>
                      <span className="block font-arabic text-muted-foreground" lang="ar" dir="rtl">
                        {h.ar_name}
                      </span>
                      <span className="block text-xs text-muted-foreground sm:hidden">
                        {h.type}
                        {h.beds !== null && ` · ${fmt(h.beds)} beds before the war`}
                      </span>
                    </TableCell>
                    <TableCell className="min-w-40 whitespace-normal">
                      <HospitalStatusBadge status={h.latest?.status} />
                      {h.latest && <span className="mt-1 block text-xs text-muted-foreground sm:hidden">{fmtDate(h.latest.as_of)}</span>}
                      {h.latest && (
                        <details className="mt-1 text-xs text-muted-foreground">
                          <summary className="cursor-pointer">WHO&apos;s words</summary>
                          <p className="mt-1">
                            &ldquo;{h.latest.quote}&rdquo;{" "}
                            <a href={h.latest.url} target="_blank" rel="noopener noreferrer">
                              source
                            </a>
                          </p>
                        </details>
                      )}
                    </TableCell>
                    <TableCell className="hidden sm:table-cell">{h.latest ? fmtDate(h.latest.as_of) : ""}</TableCell>
                    <TableCell className="num hidden sm:table-cell">{h.beds ?? ""}</TableCell>
                    <TableCell className="hidden sm:table-cell">{h.type}</TableCell>
                  </TableRow>
                )),
              ];
            })}
            {!shown.length && (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={5} className="whitespace-normal text-muted-foreground">
                  No hospital matches these filters.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
