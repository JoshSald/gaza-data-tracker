import type { Metadata } from "next";
import { VictimList } from "@/components/VictimList";
import { fmt, fmtDate, namedVictimsMeta, source } from "@/lib/data";

export const metadata: Metadata = { title: "Named victims · Gaza Data Tracker" };

export default function NamedVictims() {
  const meta = namedVictimsMeta();
  return (
    <div className="prose">
      <h1>Named victims</h1>
      <p>
        The {fmt(meta.count)} people killed in Gaza whom the {source(meta.source).name} has identified by name, covering deaths
        to {fmtDate(meta.includes_until)}. The list was last updated on {fmtDate(meta.list_updated)}.
      </p>
      <p className="note">
        This is an undercount. The Ministry&apos;s lists leave out people still missing or under rubble, unidentified bodies,
        and people buried without passing through a hospital, so the list is shorter than the Ministry&apos;s overall death
        toll. The lists give no cause or date of death. English names are translations by{" "}
        <a href="https://data.techforpalestine.org/docs/killed-in-gaza/" target="_blank" rel="noopener noreferrer">
          Tech for Palestine
        </a>
        ; the Arabic name is the Ministry&apos;s record. ID numbers and dates of birth in the source are not shown.
      </p>
      <VictimList src="/data/lists/named-victims.json" />
      <p className="attr">
        {source(meta.source).name} via {meta.document.publisher} ·{" "}
        <a href={meta.document.url} target="_blank" rel="noopener noreferrer">
          source
        </a>{" "}
        · <a href="/data/lists/named-victims.json">download the list</a>
      </p>
    </div>
  );
}
