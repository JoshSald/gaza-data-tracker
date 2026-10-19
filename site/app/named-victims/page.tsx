import type { Metadata } from "next";
import { HashTabs } from "@/components/HashTabs";
import { Oct7List } from "@/components/Oct7List";
import { TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { VictimList } from "@/components/VictimList";
import { fmt, fmtDate, namedVictimsMeta, oct7Meta, source } from "@/lib/data";

export const metadata: Metadata = { title: "Named victims · Gaza Data Tracker" };

export default function NamedVictims() {
  const gaza = namedVictimsMeta();
  const oct7 = oct7Meta();
  return (
    <div className="prose">
      <h1>Named victims</h1>
      <p>
        People killed in the war, by name, from two lists kept by different bodies. Each list is shown as its source records
        it, with its own caveats. The two are not added together.
      </p>
      <p className="note">
        The lists also differ in what stands behind each name. Israel publishes official memorial pages for its dead, often with
        their stories and photographs, and {fmt(oct7.linked)} of the {fmt(oct7.count)} names on the 7 October list link to
        one. There is no official equivalent for people killed in Gaza: the Ministry of Health&apos;s lists give a name, age
        and sex only, so names on the Gaza list do not link to a memorial page. This reflects what has been published for
        each list, not a difference in the people named.
      </p>
      <HashTabs values={["gaza", "oct7"]} className="gap-4">
        <TabsList className="grid h-auto w-full grid-cols-1 gap-1 rounded-[var(--radius)] group-data-horizontal/tabs:h-auto sm:inline-flex sm:w-fit">
          <TabsTrigger value="gaza" className="h-8 rounded-[calc(var(--radius)-1px)] data-[state=active]:bg-card data-[state=active]:text-foreground data-[state=active]:ring-1 data-[state=active]:ring-border">
            Gaza ({fmt(gaza.count)})
          </TabsTrigger>
          <TabsTrigger value="oct7" className="h-8 rounded-[calc(var(--radius)-1px)] data-[state=active]:bg-card data-[state=active]:text-foreground data-[state=active]:ring-1 data-[state=active]:ring-border">
            7 October attack ({fmt(oct7.count)})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="gaza" className="grid gap-4">
          <p>
            The {fmt(gaza.count)} people killed in Gaza whom the {source(gaza.source).name} has identified by name, covering
            deaths to {fmtDate(gaza.includes_until)}. The list was last updated on {fmtDate(gaza.list_updated)}.
          </p>
          <p className="note">
            This is an undercount. The Ministry&apos;s lists leave out people still missing or under rubble, unidentified
            bodies, and people buried without passing through a hospital, so the list is shorter than the Ministry&apos;s
            overall death toll. The lists give no cause or date of death, and do not separate civilians from combatants.
            English names are translations by{" "}
            <a href="https://data.techforpalestine.org/docs/killed-in-gaza/" target="_blank" rel="noopener noreferrer">
              Tech for Palestine
            </a>
            ; the Arabic name is the Ministry&apos;s record. ID numbers and dates of birth in the source are not shown.
          </p>
          <VictimList src="/data/lists/named-victims.json" />
          <p className="attr">
            {source(gaza.source).name} via {gaza.document.publisher} ·{" "}
            <a href={gaza.document.url} target="_blank" rel="noopener noreferrer">
              source
            </a>{" "}
            · <a href="/data/lists/named-victims.json">download the list</a>
          </p>
        </TabsContent>

        <TabsContent value="oct7" className="grid gap-4">
          <p>
            The {fmt(oct7.count)} people who were killed in the 7 October 2023 attack on Israel from Gaza, or taken hostage that
            day and later died in captivity: civilians, including foreign nationals, and soldiers, police officers and members of local
            security squads. {fmt(oct7.inCaptivity)} of them died in captivity; the list does not record how they died.
          </p>
          <p className="note">
            This list is a volunteer compilation, not an official one. It comes from{" "}
            <a href={oct7.document.page} target="_blank" rel="noopener noreferrer">
              oct7database
            </a>
            , a database kept by volunteers that checks each person against official memorial lists: the National Insurance
            Institute for civilians, and the IDF, Israel Police, Shin Bet and Ministry of Defence for security personnel.{" "}
            {fmt(oct7.linked)} of the {fmt(oct7.count)} names link to their official memorial record; follow a name to see
            it. Hostages who were released or rescued are not included. English and Hebrew names are as oct7database spells
            them, and the English spellings are not official.
          </p>
          <Oct7List src="/data/lists/oct7-victims.json" />
          <p className="attr">
            oct7database ·{" "}
            <a href={oct7.document.url} target="_blank" rel="noopener noreferrer">
              source
            </a>{" "}
            · <a href="/data/lists/oct7-victims.json">download the list</a>
          </p>
        </TabsContent>
      </HashTabs>
    </div>
  );
}
