import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { boundPrefix, fmt, fmtDate, fmtPeriod, source, type Kind, type Observation } from "@/lib/data";

const KIND_STYLE: Record<Kind, string> = {
  count: "text-[var(--count)] border-current",
  claim: "text-[var(--claim)] border-current border-dashed",
  estimate: "text-muted-foreground border-current border-dotted",
};

export function KindBadge({ kind }: { kind: Kind }) {
  const title = {
    count: "A tally recorded by the named body",
    claim: "Stated by a party without names or a method others can check. The label is about what can be checked, not a finding that the figure is wrong",
    estimate: "A modeled number with an uncertainty range",
  }[kind];
  return (
    <Badge
      variant="outline"
      title={title}
      className={cn("h-auto rounded-[2px] px-[0.45em] py-[0.25em] align-[0.1em] font-mono text-[0.6875rem] leading-none font-normal tracking-[0.06em] uppercase", KIND_STYLE[kind])}
    >
      {kind}
    </Badge>
  );
}

/** The line under every figure: who published it, for what period, and where to check it. */
export function Attribution({ o, showPeriod = true }: { o: Observation; showPeriod?: boolean }) {
  const s = source(o.source);
  const pub = o.document.publisher;
  // "World Health Organization (HeRAMS)" names the same body more precisely, so it replaces the name instead of "via".
  const name = pub.startsWith(s.name) ? pub : s.name;
  const via = pub !== s.name && !pub.startsWith(s.name) ? ` via ${pub}` : "";
  return (
    <p className="attr">
      <KindBadge kind={o.kind} /> {name}
      {via} · {showPeriod ? fmtPeriod(o) : `as of ${fmtDate(o.as_of)}`} ·{" "}
      <a href={o.document.url} target="_blank" rel="noopener noreferrer">
        source
      </a>
    </p>
  );
}

/** One figure in the stats grid. Pass `current`, the date of the grid's attribution line, to label older figures with their own date. */
export function Stat({ label, o, lead = false, current }: { label: string; o: Observation; lead?: boolean; current?: string }) {
  const prefix = boundPrefix(o.bound);
  return (
    <div className={`stat${lead ? " stat-lead" : ""}`}>
      <span className="stat-label">{label}</span>
      <span className="stat-value">
        {prefix && <span className="stat-bound">{prefix}</span>}
        {fmt(o.value)}
      </span>
      {current && o.as_of !== current && <span className="stat-asof">last reported {fmtDate(o.as_of)}</span>}
    </div>
  );
}

/** A Card in the site's archival style: square-ish corners, a rule instead of a shadow. */
export function Panel({ title, note, children, className }: { title?: string; note?: React.ReactNode; children: React.ReactNode; className?: string }) {
  return (
    <Card className={cn("min-w-0 gap-3 rounded-[var(--radius)] py-5 ring-border", className)}>
      {(title || note) && (
        <CardHeader className="gap-2 px-5">
          {title && <CardTitle className="font-sans text-base font-semibold">{title}</CardTitle>}
          {note && <div className="note">{note}</div>}
        </CardHeader>
      )}
      <CardContent className="grid gap-3 px-5">{children}</CardContent>
    </Card>
  );
}

export function FlagCard({ title, o, detail }: { title: string; o: Observation; detail?: string }) {
  return (
    <Panel title={title}>
      <p className="flag-value">
        {o.bound !== "exact" && <span className="stat-bound">{boundPrefix(o.bound)}</span>}
        {fmt(o.value)}
      </p>
      {detail && <p className="text-sm">{detail}</p>}
      <Attribution o={o} />
      {o.caveat && <p className="caveat">{o.caveat}</p>}
    </Panel>
  );
}


/** One horizontal bar split by status, with the count of each part. Values are drawn as stated; nothing is summed. */
export function StatusBar({ parts, total, label }: { parts: { label: string; o: Observation; color: string }[]; total: number; label: string }) {
  return (
    <div className="grid gap-3">
      <div className="flex h-7 w-full overflow-hidden rounded-[var(--radius)] border" role="img" aria-label={label}>
        {parts.map((p) =>
          p.o.value > 0 ? (
            <div key={p.label} title={`${p.label}: ${fmt(p.o.value)}`} style={{ width: `${(p.o.value / total) * 100}%`, background: p.color }} />
          ) : null,
        )}
      </div>
      <ul className="flex flex-wrap gap-x-5 gap-y-1 text-sm">
        {parts.map((p) => (
          <li key={p.label} className="inline-flex items-center gap-2">
            <span className="inline-block size-3 rounded-[2px]" style={{ background: p.color }} />
            <span className="font-mono tabular-nums">{fmt(p.o.value)}</span> {p.label.toLowerCase()}
          </li>
        ))}
      </ul>
    </div>
  );
}

