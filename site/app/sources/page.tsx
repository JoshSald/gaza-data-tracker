import type { Metadata } from "next";
import { KindBadge } from "@/components/Figure";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { boundPrefix, fmt, fmtDate, fmtPeriod, loadAll, metric } from "@/lib/data";

export const metadata: Metadata = { title: "Sources · Gaza Data Tracker" };

const TYPE_LABEL: Record<string, string> = {
  authority: "Local authority",
  party: "Party to the conflict",
  un: "United Nations",
  ngo: "NGO",
  study: "Research study",
  aggregator: "Data aggregator",
  media: "News organisation",
};

const LIST_LIMIT = 100;

export default function Sources() {
  const { sources, metrics, observations } = loadAll();
  const used = new Set(observations.map((o) => o.source));
  const sorted = [...observations].sort((a, b) => b.as_of.localeCompare(a.as_of) || a.metric.localeCompare(b.metric));
  // The daily history has thousands of rows; the page lists the newest and the files hold all of them.
  const rows = sorted.slice(0, LIST_LIMIT);
  return (
    <div className="prose">
      <h1>Sources</h1>
      <p>
        Who publishes each figure, and how they relate to the war. Every observation links to the document it was taken
        from. Archived copies are kept in the project repository.
      </p>

      <h2>Publishers</h2>
      <div className="data-table">
        <Table>
          <TableHeader><TableRow><TableHead>Name</TableHead><TableHead>Type</TableHead><TableHead>Affiliation</TableHead><TableHead>Notes</TableHead></TableRow></TableHeader>
          <TableBody>
            {sources.filter((s) => used.has(s.id)).map((s) => (
              <TableRow key={s.id} id={s.id}>
                <TableCell><a href={s.url} target="_blank" rel="noopener noreferrer">{s.name}</a></TableCell>
                <TableCell>{TYPE_LABEL[s.type] ?? s.type}</TableCell>
                <TableCell className="whitespace-normal">{s.affiliation}</TableCell>
                <TableCell className="wide whitespace-normal">{s.notes}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <h2>Download the data</h2>
      <p>
        One JSON file per measure, plus <a href="/data/sources.json">sources.json</a> and{" "}
        <a href="/data/metrics.json">metrics.json</a>. Field definitions are in the project&apos;s schema folder.
      </p>
      <ul>
        {metrics.map((m) => (
          <li key={m.id}>
            <a href={`/data/observations/${m.id}.json`}>{m.label}</a> <span className="note">({m.id})</span>
          </li>
        ))}
      </ul>

      <h2>Latest observations</h2>
      <p className="note">
        The newest {fmt(rows.length)} of {fmt(sorted.length)} observations. Every one, with its quote and source document, is in
        the files above.
      </p>
      <div className="data-table">
        <Table>
          <TableHeader><TableRow><TableHead>As of</TableHead><TableHead>Measure</TableHead><TableHead className="num">Value</TableHead><TableHead>Type</TableHead><TableHead>Period</TableHead><TableHead>Read in</TableHead></TableRow></TableHeader>
          <TableBody>
            {rows.map((o) => (
              <TableRow key={o.id}>
                <TableCell>{fmtDate(o.as_of)}</TableCell>
                <TableCell className="whitespace-normal">
                  {metric(o.metric).label}
                  {o.dimensions && <span className="note"> · {Object.values(o.dimensions).join(", ")}</span>}
                </TableCell>
                <TableCell className="num">
                  {o.bound !== "exact" && <span className="stat-bound">{boundPrefix(o.bound)}</span>}
                  {fmt(o.value)}
                </TableCell>
                <TableCell className="whitespace-normal"><KindBadge kind={o.kind} /></TableCell>
                <TableCell>{fmtPeriod(o)}</TableCell>
                <TableCell className="whitespace-normal"><a href={o.document.url} target="_blank" rel="noopener noreferrer">{o.document.publisher}</a></TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
