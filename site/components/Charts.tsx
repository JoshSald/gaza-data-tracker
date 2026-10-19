"use client";
// shadcn charts (Recharts). Pages pass plain data in; every chart also has a table or text with the same figures.
import { Bar, BarChart, CartesianGrid, Label, LabelList, Line, LineChart as ReLineChart, ReferenceDot, ReferenceLine, XAxis, YAxis } from "recharts";
import { ChartContainer, ChartLegend, ChartLegendContent, ChartTooltip, type ChartConfig } from "@/components/ui/chart";
import { fmt, fmtCompact, fmtDate } from "@/lib/format";

const day = (iso: string) => Date.parse(iso.slice(0, 10) + "T00:00:00Z");
const monthYear = (t: number) => new Intl.DateTimeFormat("en-GB", { month: "short", year: "2-digit", timeZone: "UTC" }).format(t);
const axisTick = { fontFamily: "var(--font-code)", fontSize: 11 };

/** The tooltip box shared by every chart: a heading and a few label/value lines. */
function TipBox({ title, lines }: { title: string; lines: [string, string][] }) {
  return (
    <div className="grid min-w-36 gap-1 rounded-[var(--radius)] border bg-popover px-2.5 py-1.5 text-xs shadow-md">
      <div className="font-medium">{title}</div>
      {lines.map(([k, v]) => (
        <div key={k} className="flex justify-between gap-4">
          <span className="text-muted-foreground">{k}</span>
          <span className="font-mono tabular-nums">{v}</span>
        </div>
      ))}
    </div>
  );
}

/** Quarterly ticks from the first of a month, so dates read cleanly on a time axis. */
function quarterTicks(x0: number, x1: number) {
  const d = new Date(x0);
  d.setUTCDate(1);
  const ticks: number[] = [];
  while (d.getTime() <= x1) {
    if (d.getTime() >= x0) ticks.push(d.getTime());
    d.setUTCMonth(d.getUTCMonth() + 3);
  }
  return ticks;
}

export function LineChart({
  points,
  start,
  label,
}: {
  points: { date: string; value: number; note?: string }[];
  start: { date: string; value: number };
  label: string;
}) {
  const data = [start, ...points].map((p) => ({ t: day(p.date), date: p.date, value: p.value, note: "note" in p ? p.note : undefined }));
  const x0 = data[0].t, x1 = data[data.length - 1].t;
  const config = { value: { label: "Deaths", color: "var(--chart-1)" } } satisfies ChartConfig;
  return (
    <ChartContainer config={config} className="aspect-auto h-64 w-full" role="img" aria-label={label}>
      <ReLineChart data={data} margin={{ top: 12, right: 56, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="t" type="number" scale="time" domain={[x0, x1]} ticks={quarterTicks(x0, x1)} tickFormatter={monthYear} tick={axisTick} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={fmtCompact} tick={axisTick} tickLine={false} axisLine={false} width={44} />
        <ChartTooltip
          cursor={false}
          content={({ active, payload }) => {
            const p = active && payload?.[0]?.payload;
            if (!p) return null;
            return <TipBox title={fmtDate(p.date)} lines={[["Deaths", fmt(p.value)], ...(p.note ? [["Reported by", p.note] as [string, string]] : [])]} />;
          }}
        />
        <Line dataKey="value" type="linear" stroke="var(--color-value)" strokeWidth={2} dot={{ r: 4, fill: "var(--card)", strokeWidth: 2 }} activeDot={{ r: 5 }} isAnimationActive={false}>
          <LabelList
            dataKey="value"
            content={(props) => {
              // Label only the latest point.
              if (props.index !== data.length - 1) return null;
              return (
                <text x={Number(props.x) + 10} y={Number(props.y)} dy="0.32em" className="fill-foreground" fontSize={13}>
                  {fmt(Number(props.value))}
                </text>
              );
            }}
          />
        </Line>
      </ReLineChart>
    </ChartContainer>
  );
}

export function GroupedBars({
  groups,
  series,
  values,
  label,
}: {
  groups: { key: string; label: string }[];
  series: { key: string; label: string }[];
  values: Record<string, Record<string, number>>;
  label: string;
}) {
  const data = groups.map((g) => ({ group: g.label, ...values[g.key] }));
  const config = Object.fromEntries(series.map((s, i) => [s.key, { label: s.label, color: `var(--chart-${i + 1})` }])) satisfies ChartConfig;
  return (
    <ChartContainer config={config} className="aspect-auto w-full" style={{ height: groups.length * 72 + 40 }} role="img" aria-label={label}>
      <BarChart data={data} layout="vertical" margin={{ top: 0, right: 56, bottom: 0, left: 0 }} barGap={4}>
        <XAxis type="number" hide />
        <YAxis type="category" dataKey="group" width={128} tick={{ fontSize: 13, fill: "var(--foreground)" }} tickLine={false} axisLine={false} />
        <ChartTooltip
          cursor={false}
          content={({ active, payload }) => {
            const p = active && payload?.[0]?.payload;
            if (!p) return null;
            return <TipBox title={p.group} lines={series.map((s) => [s.label, fmt(p[s.key])])} />;
          }}
        />
        <ChartLegend itemSorter={null} content={<ChartLegendContent className="flex-wrap gap-x-4 gap-y-1" />} />
        {series.map((s) => (
          <Bar key={s.key} dataKey={s.key} fill={`var(--color-${s.key})`} radius={2} barSize={20} isAnimationActive={false}>
            <LabelList dataKey={s.key} position="right" offset={6} className="fill-muted-foreground font-mono" fontSize={12} formatter={(v) => fmt(Number(v))} />
          </Bar>
        ))}
      </BarChart>
    </ChartContainer>
  );
}

export interface RangeRow {
  label: string;
  sub: string;
  low: number;
  high: number;
  central: number;
  recorded?: number;
}

function niceMax(max: number) {
  const mag = 10 ** Math.floor(Math.log10(max));
  return [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10].map((m) => m * mag).find((v) => v >= max) ?? max;
}

/** Each study's 95% interval as a band, its central estimate as a dot, and the Ministry's own count as a diamond.
 *  One small chart per study on a shared scale, so labels wrap as text on narrow screens. */
export function RangeChart({ rows, label }: { rows: RangeRow[]; label: string }) {
  const max = niceMax(Math.max(...rows.map((r) => r.high)));
  const config = { range: { label: "95% interval", color: "var(--chart-1)" } } satisfies ChartConfig;
  return (
    <div className="grid gap-4" role="img" aria-label={label}>
      {rows.map((r, i) => {
        const last = i === rows.length - 1;
        const data = [{ name: r.label, range: [r.low, r.high] }];
        return (
          <div key={r.label + r.sub} className="grid gap-1">
            <p className="text-sm">
              <span className="font-medium">{r.label}</span> <span className="text-muted-foreground">· {r.sub}</span>
            </p>
            <ChartContainer config={config} className="aspect-auto w-full" style={{ height: last ? 56 : 32 }}>
              <BarChart data={data} layout="vertical" margin={{ top: 4, right: 12, bottom: 0, left: 12 }}>
                <CartesianGrid horizontal={false} />
                <XAxis type="number" domain={[0, max]} tickCount={6} tickFormatter={fmtCompact} tick={axisTick} tickLine={false} axisLine={false} hide={!last} />
                <YAxis type="category" dataKey="name" hide />
                <ChartTooltip
                  cursor={false}
                  content={({ active }) =>
                    active ? (
                      <TipBox
                        title={r.label}
                        lines={[
                          ["Central estimate", fmt(r.central)],
                          ["95% interval", `${fmt(r.low)}–${fmt(r.high)}`],
                          ...(r.recorded !== undefined ? [["Ministry recorded", fmt(r.recorded)] as [string, string]] : []),
                        ]}
                      />
                    ) : null
                  }
                />
                <Bar dataKey="range" fill="var(--color-range)" fillOpacity={0.3} radius={5} barSize={10} isAnimationActive={false} />
                <ReferenceDot x={r.central} y={r.label} r={6} fill="var(--chart-1)" stroke="none" />
                {r.recorded !== undefined && (
                  <ReferenceDot
                    x={r.recorded}
                    y={r.label}
                    shape={(p: { cx?: number; cy?: number }) => (
                      <path d={`M${p.cx},${(p.cy ?? 0) - 7}l7,7l-7,7l-7,-7z`} fill="var(--card)" stroke="var(--foreground)" strokeWidth={1.5} />
                    )}
                  />
                )}
              </BarChart>
            </ChartContainer>
          </div>
        );
      })}
    </div>
  );
}

/** Monthly totals as bars. Months with no stored figure are left empty, never drawn as zero. */
export function MonthlyBars({
  points,
  label,
  unit,
}: {
  points: { month: string; value: number; prefix: string }[];
  label: string;
  unit: string;
}) {
  const byMonth = new Map(points.map((p) => [p.month, p]));
  const months: string[] = [];
  const d = new Date(points[0].month + "-01T00:00:00Z");
  const end = points[points.length - 1].month;
  while (d.toISOString().slice(0, 7) <= end) {
    months.push(d.toISOString().slice(0, 7));
    d.setUTCMonth(d.getUTCMonth() + 1);
  }
  const data = months.map((m) => ({ month: m, t: day(m + "-01"), value: byMonth.get(m)?.value ?? null, prefix: byMonth.get(m)?.prefix ?? "" }));
  const config = { value: { label: unit, color: "var(--chart-1)" } } satisfies ChartConfig;
  return (
    <ChartContainer config={config} className="aspect-auto h-64 w-full" role="img" aria-label={label}>
      <BarChart data={data} margin={{ top: 8, right: 0, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="month" tickFormatter={(m: string) => monthYear(day(m + "-01"))} tick={axisTick} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={16} />
        <YAxis tickFormatter={fmtCompact} tick={axisTick} tickLine={false} axisLine={false} width={44} />
        <ChartTooltip
          cursor={false}
          content={({ active, payload }) => {
            const p = active && payload?.[0]?.payload;
            if (!p) return null;
            const title = new Intl.DateTimeFormat("en-GB", { month: "long", year: "numeric", timeZone: "UTC" }).format(p.t);
            return <TipBox title={title} lines={[[unit, p.value === null ? "no figure stored" : `${p.prefix}${fmt(p.value)}`]]} />;
          }}
        />
        <Bar dataKey="value" fill="var(--color-value)" radius={[2, 2, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ChartContainer>
  );
}

/** Several running totals on one time axis. Each line joins only the days its figure was reported. */
export function HistoryChart({
  series,
  markers = [],
  label,
}: {
  series: { key: string; label: string; points: { date: string; value: number }[]; color?: string; dashed?: boolean }[];
  markers?: { date: string; label: string }[];
  label: string;
}) {
  const rows = new Map<number, Record<string, number | string>>();
  for (const s of series)
    for (const p of s.points) {
      const t = day(p.date);
      rows.set(t, { ...(rows.get(t) ?? { t, date: p.date }), [s.key]: p.value });
    }
  const data = [...rows.values()].sort((a, b) => Number(a.t) - Number(b.t));
  const x0 = Number(data[0].t), x1 = Number(data[data.length - 1].t);
  const config = Object.fromEntries(series.map((s, i) => [s.key, { label: s.label, color: s.color ?? ["var(--chart-1)", "var(--chart-3)", "var(--chart-2)"][i % 3] }])) satisfies ChartConfig;
  return (
    <ChartContainer config={config} className="aspect-auto h-80 w-full" role="img" aria-label={label}>
      <ReLineChart data={data} margin={{ top: 16, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="t" type="number" scale="time" domain={[x0, x1]} ticks={quarterTicks(x0, x1)} tickFormatter={monthYear} tick={axisTick} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={12} />
        <YAxis tickFormatter={fmtCompact} tick={axisTick} tickLine={false} axisLine={false} width={44} />
        {markers.map((m) => (
          <ReferenceLine key={m.date} x={day(m.date)} stroke="var(--muted-foreground)" strokeDasharray="3 3">
            <Label value={m.label} position="insideTopLeft" offset={6} fontSize={11} fill="var(--muted-foreground)" />
          </ReferenceLine>
        ))}
        <ChartTooltip
          cursor={{ stroke: "var(--border)" }}
          content={({ active, payload }) => {
            const p = active && payload?.[0]?.payload;
            if (!p) return null;
            const lines = series.filter((s) => typeof p[s.key] === "number").map((s) => [s.label, fmt(p[s.key])] as [string, string]);
            return <TipBox title={fmtDate(p.date)} lines={lines} />;
          }}
        />
        <ChartLegend itemSorter={null} content={<ChartLegendContent className="flex-wrap gap-x-4 gap-y-1" />} />
        {series.map((s) => (
          <Line key={s.key} dataKey={s.key} type="linear" stroke={`var(--color-${s.key})`} strokeWidth={2} strokeDasharray={s.dashed ? "5 4" : undefined} dot={false} connectNulls isAnimationActive={false} />
        ))}
        {/* A line that stops before the others ends in a marked dot, so the gap reads as "no longer reported", not "no more deaths".
            One short label sits above the highest such dot, ending at it, so it fits on narrow screens. */}
        {(() => {
          const ended = series.map((s) => ({ s, end: s.points.at(-1) })).filter((e) => e.end && day(e.end.date) < x1);
          const top = ended.reduce<(typeof ended)[number] | null>((m, e) => (!m || e.end!.value > m.end!.value ? e : m), null);
          return ended.map(({ s, end }) => (
            <ReferenceDot key={`end-${s.key}`} x={day(end!.date)} y={end!.value} r={3.5} fill="var(--card)" stroke={`var(--color-${s.key})`} strokeWidth={2}>
              {top?.s.key === s.key && (
                <Label value={`last reported ${fmtDate(end!.date)}`} position="top" offset={10} fontSize={11} fill="var(--muted-foreground)" textAnchor="end" />
              )}
            </ReferenceDot>
          ));
        })()}
      </ReLineChart>
    </ChartContainer>
  );
}

/** Dated statements by one party, drawn as dots joined by a dashed line in the claim colour: each dot is a statement, not a running count. */
export function StatementChart({
  points,
  label,
  unit,
}: {
  points: { date: string; value: number; prefix: string; publisher: string }[];
  label: string;
  unit: string;
}) {
  const data = points.map((p) => ({ ...p, t: day(p.date) }));
  const x0 = data[0].t, x1 = data[data.length - 1].t;
  const config = { value: { label: unit, color: "var(--claim)" } } satisfies ChartConfig;
  return (
    <ChartContainer config={config} className="aspect-auto h-64 w-full" role="img" aria-label={label}>
      <ReLineChart data={data} margin={{ top: 16, right: 28, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="t" type="number" scale="time" domain={[x0, x1]} ticks={quarterTicks(x0, x1)} tickFormatter={monthYear} tick={axisTick} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={12} />
        <YAxis tickFormatter={fmtCompact} tick={axisTick} tickLine={false} axisLine={false} width={44} domain={[0, "auto"]} />
        <ChartTooltip
          cursor={false}
          content={({ active, payload }) => {
            const p = active && payload?.[0]?.payload;
            if (!p) return null;
            return <TipBox title={fmtDate(p.date)} lines={[[unit, `${p.prefix}${fmt(p.value)}`], ["Reported by", p.publisher]]} />;
          }}
        />
        <Line dataKey="value" type="linear" stroke="var(--color-value)" strokeWidth={2} strokeDasharray="5 4" dot={{ r: 4, fill: "var(--card)", strokeWidth: 2 }} activeDot={{ r: 5 }} isAnimationActive={false} />
      </ReLineChart>
    </ChartContainer>
  );
}


/** Counts in several classes per date, stacked into one bar per date (for example UNOSAT damage classes). */
export function StackedBars({
  rows,
  stacks,
  label,
  extra,
}: {
  rows: Record<string, number | string>[];
  stacks: { key: string; label: string; color: string }[];
  label: string;
  extra?: { key: string; label: string; suffix?: string; prefix?: string }[];
}) {
  const data = rows.map((r) => ({ ...r, t: day(String(r.date)) }));
  const config = Object.fromEntries(stacks.map((s) => [s.key, { label: s.label, color: s.color }])) satisfies ChartConfig;
  return (
    <ChartContainer config={config} className="aspect-auto h-72 w-full" role="img" aria-label={label}>
      <BarChart data={data} margin={{ top: 8, right: 0, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} />
        <XAxis dataKey="date" tickFormatter={(d: string) => monthYear(day(d))} tick={axisTick} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={12} />
        <YAxis tickFormatter={fmtCompact} tick={axisTick} tickLine={false} axisLine={false} width={44} />
        <ChartTooltip
          cursor={false}
          content={({ active, payload }) => {
            const p = active && payload?.[0]?.payload;
            if (!p) return null;
            const lines: [string, string][] = stacks.filter((s) => typeof p[s.key] === "number").map((s) => [s.label, fmt(p[s.key])]);
            for (const e of extra ?? []) if (typeof p[e.key] === "number") lines.push([e.label, `${e.prefix ?? ""}${fmt(p[e.key])}${e.suffix ?? ""}`]);
            return <TipBox title={fmtDate(p.date)} lines={lines} />;
          }}
        />
        <ChartLegend itemSorter={null} content={<ChartLegendContent className="flex-wrap gap-x-4 gap-y-1" />} />
        {stacks.map((s, i) => (
          <Bar key={s.key} dataKey={s.key} stackId="a" fill={`var(--color-${s.key})`} radius={i === stacks.length - 1 ? [2, 2, 0, 0] : 0} isAnimationActive={false} />
        ))}
      </BarChart>
    </ChartContainer>
  );
}
