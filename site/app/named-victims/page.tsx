import type { Metadata } from "next";
import { HashTabs } from "@/components/HashTabs";
import { Oct7List } from "@/components/Oct7List";
import { TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { VictimList } from "@/components/VictimList";
import { fmt, fmtDate, memorialLinksMeta, namedVictimsMeta, oct7Meta, source } from "@/lib/data";

export const metadata: Metadata = { title: "Named victims · Gaza Data Tracker" };

export default function NamedVictims() {
  const gaza = namedVictimsMeta();
  const oct7 = oct7Meta();
  const mem = memorialLinksMeta();
  const pct = (n: number, d: number) => `${(Math.round((n / d) * 1000) / 10).toLocaleString("en-GB")}%`;
  const ext = { target: "_blank", rel: "noopener noreferrer" } as const;
  return (
    <div className="prose">
      <h1>Named victims</h1>
      <p>
        People killed in the war, by name, from two lists kept by different bodies. Each list is shown as its source records
        it, with its own caveats. The two are not added together.
      </p>
      <p className="note">
        The lists also differ in what stands behind each name. On the 7 October list, {fmt(oct7.linked)} of the{" "}
        {fmt(oct7.count)} names ({pct(oct7.linked, oct7.count)}) link to a memorial page, often with the person&apos;s story
        and photograph. On the Gaza list, {fmt(mem.people)} of {fmt(gaza.count)} do ({pct(mem.people, gaza.count)}). This
        reflects what has been published and what could be matched, not a difference in the people named.
      </p>
      {/* The full explanation is folded away so the lists are not far down the page. */}
      <details className="group -mt-2 text-sm rounded-[var(--radius)] border bg-card px-4 py-3 [&_p]:my-3 [&_ul]:my-3">
        <summary className="cursor-pointer list-none text-sm font-medium marker:hidden [&::-webkit-details-marker]:hidden">
          <span className="mr-1.5 inline-block transition-transform group-open:rotate-90" aria-hidden>
            ▸
          </span>
          Why so few Gaza names link to a memorial page, and how the links were made
        </summary>
        <p>
          The difference starts with who writes the pages. In Israel, state bodies publish one for everyone they commemorate:
          the National Insurance Institute for civilians, and the IDF, Israel Police, Shin Bet and Ministry of Defence for
          security personnel. Each page belongs to one person, so oct7database could link nearly every name. No official body
          publishes memorial pages for people killed in Gaza. The Ministry of Health&apos;s lists give a name, age and sex. The
          stories that exist are written by independent projects: families and friends send them to{" "}
          <a href={mem.projects["gaza-shaheed"].url} {...ext}>
            {mem.projects["gaza-shaheed"].name}
          </a>
          , and Gaza&apos;s journalists remember colleagues who were killed on{" "}
          <a href={mem.projects["living-record"].url} {...ext}>
            {mem.projects["living-record"].name}
          </a>
          , by {mem.projects["living-record"].by}. Together they had {fmt(mem.pages_read)} pages when we read them.
        </p>
        <p>Linking those pages to the Ministry&apos;s list was harder than it sounds, and most could not be linked:</p>
        <ul>
          <li>
            Neither project gives the Ministry&apos;s ID numbers, so the only way to connect a page to a name on the list is
            the name itself.
          </li>
          <li>
            Names in Gaza are often shared. The Ministry records a first name, father&apos;s name, grandfather&apos;s name and
            family name, but many pages give only two, and fifteen people on the list are called Ahmed Mansour.
          </li>
          <li>
            The same name is spelled in more than one way, in Arabic and even more so in English, so the spellings have to be
            folded together before they can be compared.
          </li>
          <li>
            Some pages remember a whole family or a couple together, and cannot be tied to one name. On one page, the Arabic
            version carried another person&apos;s name.
          </li>
        </ul>
        <p>
          A wrong link would attach someone&apos;s story to a different person, so we set strict rules. A page is linked only
          when exactly one person on the list fits its name, and when a name of only two parts is backed by something else on
          the page: an age, a year of birth, or the father&apos;s name given in its English text. Anything on the page that
          disagrees with the record, such as a different age, rules the link out. We do not guess between close spellings.
        </p>
        <p>
          Of the {fmt(mem.pages_read)} pages, {fmt(mem.counts.linked)} passed ({fmt(mem.byProject["gaza-shaheed"] ?? 0)} from{" "}
          {mem.projects["gaza-shaheed"].name} and {fmt(mem.byProject["living-record"] ?? 0)} from{" "}
          {mem.projects["living-record"].name}; one person has a page on both). {fmt(mem.counts.ambiguous)} fitted more than
          one person, {fmt(mem.counts["no match"])} fitted nobody on the list, {fmt(mem.counts["not corroborated"])} had a
          two-part name with nothing to confirm it, {fmt(mem.counts.contradicted)} disagreed with the only record that fitted,
          and {fmt(mem.counts.skipped)} were about several people or gave too little of a name. Those pages are still worth
          reading on the projects&apos; own sites.
        </p>
        <p>
          {fmt(mem.byHand)} {mem.byHand === 1 ? "link was" : "links were"} added by hand, for{" "}
          {mem.byHand === 1 ? "a page" : "pages"} the rules could not link because the page gives too little of the name.
          These are marked <span className="font-mono text-xs uppercase">linked by hand</span> in the list, with what the
          identification rests on, and are kept in a separate file so they are never mistaken for matches the rules made.
        </p>
        <p className="note">
          <a href="https://airwars.org/" {...ext}>
            Airwars
          </a>
          , which investigates civilian harm, has matched several thousand names on the Ministry&apos;s list to the
          incidents it documents, using ID numbers; its{" "}
          <a href="https://airwars.org/moh-list/" {...ext}>
            list of identified victims
          </a>{" "}
          shows which. That would give far more links, but it does not state terms for reusing
          that data and we have not asked for permission, so it is not used here.
        </p>
      </details>
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
            ; the Arabic name is the Ministry&apos;s record. ID numbers and dates of birth in the source are not shown.{" "}
            {fmt(mem.people)} names link to a memorial page written by an independent project, matched as described
            above or, where marked, linked by hand; the project&apos;s name is shown under each.
          </p>
          <VictimList
            src="/data/lists/named-victims.json"
            links="/data/lists/gaza-memorial-links.json"
            byHand="/data/lists/gaza-memorial-links-by-hand.json"
          />
          <p className="attr">
            {source(gaza.source).name} via {gaza.document.publisher} ·{" "}
            <a href={gaza.document.url} target="_blank" rel="noopener noreferrer">
              source
            </a>{" "}
            · <a href="/data/lists/named-victims.json">download the list</a> ·{" "}
            <a href="/data/lists/gaza-memorial-links.json">download the memorial links</a> ·{" "}
            <a href="/data/lists/gaza-memorial-links-by-hand.json">links added by hand</a>
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
