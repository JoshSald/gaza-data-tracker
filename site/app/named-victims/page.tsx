import type { Metadata } from "next";
import { Disclosure } from "@/components/Disclosure";
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
  const report = "https://github.com/JoshSald/gaza-data-tracker/issues/new?template=named-victim-report.yml";
  const projectLink = (id: string) => (
    <a href={mem.projects[id].url} {...ext}>
      {mem.projects[id].name}
    </a>
  );
  return (
    <div className="prose">
      <h1>Named victims</h1>
      <p>
        People killed in the war, by name, from two lists kept by different bodies. Each list is shown as its source records
        it, with its own caveats. The two are not added together.
      </p>
      <HashTabs id="lists" values={["gaza", "oct7"]} className="gap-4">
        {/* The switcher stays at the top of the screen while a list is scrolled. */}
        <div className="sticky top-0 z-20 -mx-4 border-b bg-[var(--paper)] px-4 py-2 sm:mx-0 sm:rounded-b-[var(--radius)] sm:px-0">
          <TabsList aria-label="Choose a list" className="grid h-auto w-full grid-cols-2 gap-1 rounded-[var(--radius)] border bg-card p-1 group-data-horizontal/tabs:h-auto">
            <TabsTrigger value="gaza" className="flex h-auto flex-col items-center gap-0 rounded-[calc(var(--radius)-1px)] px-3 py-1.5 text-sm font-medium whitespace-normal text-muted-foreground hover:bg-[var(--rule)] hover:text-foreground data-[state=active]:bg-[var(--ink)] data-[state=active]:text-[var(--paper)] data-[state=active]:hover:bg-[var(--ink)] data-[state=active]:hover:text-[var(--paper)] dark:data-[state=active]:hover:text-[var(--paper)] sm:flex-row sm:gap-2">
              <span>Killed in Gaza</span>
              <span className="font-mono text-xs opacity-80">{fmt(gaza.count)} names</span>
            </TabsTrigger>
            <TabsTrigger value="oct7" className="flex h-auto flex-col items-center gap-0 rounded-[calc(var(--radius)-1px)] px-3 py-1.5 text-sm font-medium whitespace-normal text-muted-foreground hover:bg-[var(--rule)] hover:text-foreground data-[state=active]:bg-[var(--ink)] data-[state=active]:text-[var(--paper)] data-[state=active]:hover:bg-[var(--ink)] data-[state=active]:hover:text-[var(--paper)] dark:data-[state=active]:hover:text-[var(--paper)] sm:flex-row sm:gap-2">
              <span>Killed in the 7 October attack</span>
              <span className="font-mono text-xs opacity-80">{fmt(oct7.count)} names</span>
            </TabsTrigger>
          </TabsList>
        </div>
          {/* One box for memorial pages: what a link does and does not mean stays visible; the full explanation folds
              away so the lists are not far down the page. */}
        <div className="rounded-[var(--radius)] border bg-card text-sm">
          <p className="m-0 rounded-t-[var(--radius)] border-b border-l-4 border-l-[var(--red)] px-4 py-3 text-[var(--red)]">
            <strong className="font-semibold">Memorial pages are kept by third parties.</strong> Views expressed on them are
            their own and are not necessarily held by Gaza Data Tracker. A link shows who a page is about; it is not an
            endorsement of the page or of any claim it makes.
          </p>
          <Disclosure
            className="px-4 py-3"
            summary={
              <>
                Memorial pages: {pct(oct7.linked, oct7.count)} of 7 October names link to one, {pct(mem.people, gaza.count)} of
                Gaza names. Why, and how the links were made
              </>
            }
          >
            <p>
              The lists differ in what stands behind each name. On the 7 October list, {fmt(oct7.linked)} of the{" "}
              {fmt(oct7.count)} names link to a memorial page, often with the person&apos;s story and photograph. On the Gaza
              list, {fmt(mem.people)} of {fmt(gaza.count)} do. This reflects what has been published and what could be matched,
              not a difference in the people named.
            </p>
            <p>
              Gaza Data Tracker links to external memorial pages to help visitors learn more about the individuals represented
              in its records, including their lives, photographs, and personal stories. These memorials are maintained by third
              parties and may reflect their own perspectives, interpretations, and political viewpoints. Their content is not
              produced or controlled by Gaza Data Tracker, and linking to a page does not constitute endorsement of every
              statement or claim it contains.
            </p>
            <p>
              The difference starts with who writes the pages. In Israel, state bodies publish one for everyone they commemorate:
              the National Insurance Institute for civilians, and the IDF, Israel Police, Shin Bet and Ministry of Defence for
              security personnel. Each page belongs to one person, so oct7database could link nearly every name. No official body
              publishes memorial pages for people killed in Gaza. The Ministry of Health&apos;s lists give a name, age and sex. The
              stories that exist are written by independent projects: families and friends send them to {projectLink("gaza-shaheed")}
              ; {projectLink("aint-numbers")} keeps a page for each person, often with a photograph and an account from the family
              or the Ministry; and Gaza&apos;s journalists remember colleagues who were killed on {projectLink("living-record")}, by{" "}
              {mem.projects["living-record"].by}. Together they had {fmt(mem.pages_read)} pages when we read them.
            </p>
            <p>Linking those pages to the Ministry&apos;s list was harder than it sounds, and most could not be linked:</p>
            <ul>
              <li>
                Most pages give no Ministry ID number, so the usual way to connect a page to a name on the list is the name itself.
                Where a page does give one, it confirms the match; ID numbers are compared but never stored or shown here.
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
                Some pages remember a whole family or a couple together, and cannot be tied to one name. Some name a brother or
                sister before the person the page is about, and on one, the Arabic version carried another person&apos;s name.
              </li>
            </ul>
            <p>
              A wrong link would attach someone&apos;s story to a different person, so we set strict rules. A page is linked only
              when exactly one person on the list fits its name, and when a name of only two parts is backed by something else on
              the page: an age, a year of birth, or the father&apos;s name given in its English text. A Ministry ID number on the
              page is enough on its own if it belongs to someone with the same name. Anything on the page that disagrees with the
              record, such as a different age, the other sex or a different first name in its English title, rules the link
              out. We do not guess between close spellings.
            </p>
            <p>
              Of the {fmt(mem.pages_read)} pages, {fmt(mem.counts.linked)} passed: {fmt(mem.byProject["aint-numbers"] ?? 0)} from{" "}
              {mem.projects["aint-numbers"].name}, {fmt(mem.byProject["gaza-shaheed"] ?? 0)} from {mem.projects["gaza-shaheed"].name}{" "}
              and {fmt(mem.byProject["living-record"] ?? 0)} from {mem.projects["living-record"].name}. Some people have a page on
              more than one. {fmt(mem.counts.ambiguous)} fitted more than
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
            <p className="note">
              The rules, the sources in use and those set aside are written up in the project&apos;s{" "}
              <a href="https://github.com/JoshSald/gaza-data-tracker/blob/main/docs/memorial-links.md" {...ext}>
                memorial links policy
              </a>
              .
            </p>
            <p className="note">
              Spotted a wrong link, a mistaken identity or a privacy concern?{" "}
              <a href={report} {...ext}>
                Report a mistake
              </a>
              . Why the site links to memorials at all is explained on the <a href="/methodology/#memorials">method page</a>.
            </p>
          </Disclosure>
        </div>

        <TabsContent value="gaza" className="grid gap-4">
          <p>
            The {fmt(gaza.count)} people killed in Gaza whom the {source(gaza.source).name} has identified by name, covering
            deaths to {fmtDate(gaza.includes_until)}; last updated {fmtDate(gaza.list_updated)}. It is an undercount.
          </p>
          <Disclosure className="-mt-2 text-muted-foreground" summary="About this list">
            <p>
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
          </Disclosure>
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
            <a href="/data/lists/gaza-memorial-links-by-hand.json">links added by hand</a> ·{" "}
            <a href={report} {...ext}>
              report a mistake
            </a>
          </p>
        </TabsContent>

        <TabsContent value="oct7" className="grid gap-4">
          <p>
            The {fmt(oct7.count)} people who were killed in the 7 October 2023 attack on Israel from Gaza, or taken hostage that
            day and later died in captivity: civilians, including foreign nationals, and soldiers, police officers and members of local
            security squads. {fmt(oct7.inCaptivity)} of them died in captivity; the list does not record how they died. It is
            a volunteer compilation, not an official list.
          </p>
          <Disclosure className="-mt-2 text-muted-foreground" summary="About this list">
            <p>
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
          </Disclosure>
          <Oct7List src="/data/lists/oct7-victims.json" />
          <p className="attr">
            oct7database ·{" "}
            <a href={oct7.document.url} target="_blank" rel="noopener noreferrer">
              source
            </a>{" "}
            · <a href="/data/lists/oct7-victims.json">download the list</a> ·{" "}
            <a href={report} {...ext}>
              report a mistake
            </a>
          </p>
        </TabsContent>
      </HashTabs>
    </div>
  );
}
