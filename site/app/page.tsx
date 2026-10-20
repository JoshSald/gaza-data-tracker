import { Chapters } from "@/components/Chapters";
import { Attribution, FlagCard, HospitalStatusBadge, KindBadge, Panel, Stat, StatusBar } from "@/components/Figure";
import { GroupedBars, HistoryChart, LineChart, MonthlyBars, RangeChart, StackedBars, StatementChart } from "@/components/Charts";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { all, boundPrefix, fmt, fmtDate, fmtPeriod, hospitals, latest, metric, series, source, type Observation } from "@/lib/data";

const WAR_START = "2023-10-07";
// Tech for Palestine's republication of every Ministry daily report; the full-history chart uses only this.
const DAILY_REPORTS = "https://data.techforpalestine.org/api/v2/casualties_daily.json";
const CEASEFIRE = "2025-10-10";
// The sections below, in order, for the chapters list.
const CHAPTERS = [
  { id: "deaths", label: "Recorded deaths" },
  { id: "access", label: "Access-related deaths" },
  { id: "estimates", label: "Independent estimates" },
  { id: "aid", label: "Aid" },
  { id: "hospitals", label: "Hospitals" },
  { id: "buildings", label: "Buildings and infrastructure" },
  { id: "food", label: "Food security" },
  { id: "israel", label: "Israeli casualties and IDF figures" },
];

function Row({ o, label }: { o: Observation; label?: string }) {
  return (
    <TableRow>
      <TableCell className="label whitespace-normal">
        <a href={o.document.url} target="_blank" rel="noopener noreferrer">
          {label ?? metric(o.metric).label}
        </a>
      </TableCell>
      <TableCell className="num">
        {o.bound !== "exact" && <span className="stat-bound">{boundPrefix(o.bound)}</span>}
        {fmt(o.value)}
      </TableCell>
      <TableCell>
        <KindBadge kind={o.kind} />
      </TableCell>
      <TableCell className="publisher whitespace-normal">{source(o.source).name}</TableCell>
      <TableCell className="period whitespace-normal">{fmtPeriod(o)}</TableCell>
      <TableCell className="wide whitespace-normal">{o.caveat ?? metric(o.metric).definition}</TableCell>
    </TableRow>
  );
}

export default function Home() {
  const killed = latest("gaza.killed.total", { source: "gaza-moh", periodStart: WAR_START });
  const sinceCf = latest("gaza.killed.since_ceasefire", { periodStart: CEASEFIRE });
  const recovered = latest("gaza.bodies_recovered.since_ceasefire");
  const cfSeries = series("gaza.killed.since_ceasefire", { periodStart: CEASEFIRE });
  const daily = (id: string) =>
    series(id, { source: "gaza-moh", periodStart: WAR_START })
      .filter((o) => o.document.url === DAILY_REPORTS)
      .map((o) => ({ date: o.as_of, value: o.value }));
  const history = [
    { key: "killed", label: "Killed", points: daily("gaza.killed.total") },
    { key: "children", label: "Children killed", points: daily("gaza.killed.children") },
    { key: "women", label: "Women killed", points: daily("gaza.killed.women") },
  ];
  const historyLast = series("gaza.killed.total", { source: "gaza-moh", periodStart: WAR_START }).filter((o) => o.document.url === DAILY_REPORTS).at(-1)!;
  const childrenLast = history[1].points.at(-1)!;

  const ages = [
    { key: "child", label: "Children (under 18)" },
    { key: "adult", label: "Adults (18–64)" },
    { key: "senior", label: "Seniors (65+)" },
  ];
  const sexes = [
    { key: "male", label: "Male" },
    { key: "female", label: "Female" },
  ];
  const named = (age: string, sex: string) => latest("gaza.named_victims", { dims: { age_group: age, sex } });
  const namedTotal = ages.reduce((t, a) => t + sexes.reduce((s, x) => s + named(a.key, x.key).value, 0), 0);
  const namedChildren = sexes.reduce((s, x) => s + named("child", x.key).value, 0);
  const namedAsOf = named("child", "male");

  const seekingAid = series("gaza.killed.seeking_aid");
  const aidUn = seekingAid.filter((o) => o.source === "ohchr").at(-1)!;
  const aidMoh = seekingAid.filter((o) => o.source === "gaza-moh").at(-1)!;

  const traumatic = latest("gaza.deaths.traumatic", { kind: "estimate" });
  const violent = latest("gaza.deaths.violent", { kind: "estimate" });
  const violentMoh = latest("gaza.deaths.violent", { source: "gaza-moh" });
  const excess = latest("gaza.deaths.excess_nonviolent", { kind: "estimate" });
  const estimates = [traumatic, violent, excess];

  const aidRows = [
    ...all("aid.trucks.entered"),
    ...all("aid.trucks.per_day"),
    ...all("aid.medical.tonnes"),
    ...all("aid.trucks.needed_per_day"),
    ...all("aid.un2720.delivered_tonnes"),
    ...all("aid.un2720.pipeline_tonnes"),
    ...all("aid.un2720.trucks_collected"),
    ...all("aid.un2720.trucks_intercepted"),
    ...all("aid.un2720.trucks_arrived"),
  ];
  const delivered = series("aid.un2720.delivered_tonnes", { source: "un2720" });
  const deliveredLast = delivered.at(-1)!;

  const idfClaims = series("idf.combatants_killed.gaza", { source: "idf", kind: "claim", periodStart: WAR_START });

  // Hospitals (WHO). Situation reports count 36 hospitals; HeRAMS snapshots count the 35 WHO evaluates, so they stay apart.
  const noDims = (o: Observation) => !o.dimensions;
  const herams = { monitoring: "herams" };
  const pts = (rows: Observation[]) => rows.map((o) => ({ date: o.as_of, value: o.value }));
  const sitPartial = series("health.hospitals.partially_functional", { source: "who" }).filter(noDims);
  const hrPartial = series("health.hospitals.partially_functional", { source: "who", dims: herams });
  const hrNon = series("health.hospitals.not_functioning", { source: "who", dims: herams });
  const hrDestroyed = series("health.hospitals.destroyed", { source: "who", dims: herams });
  const sitNon = series("health.hospitals.not_functioning", { source: "who" }).filter(noDims);
  const hrLatest = hrPartial.at(-1)!;
  // The latest month for which WHO stated every status, so the parts all come from one snapshot.
  const hrAt = (m: string) => series(m, { source: "who", dims: herams }).find((o) => o.as_of === hrLatest.as_of);
  const hrNow = {
    evaluated: hrAt("health.hospitals.evaluated"),
    full: hrAt("health.hospitals.fully_functional"),
    partial: hrLatest,
    non: hrAt("health.hospitals.not_functioning"),
    destroyed: hrAt("health.hospitals.destroyed"),
  };
  const hrDefinitions = hrPartial.find((o) => o.as_of === "2026-05-31") ?? hrLatest;
  const attacks = latest("health.attacks.total", { source: "who" });
  // Every hospital in the Ministry/Health Cluster list, north to south, with WHO's newest statement naming it.
  const GOVERNORATES = ["North Gaza", "Gaza", "Deir Albalah", "Khan Younis", "Rafah"];
  const hosp = hospitals();
  const hospNamed = hosp.list.filter((h) => h.latest).length;

  // Buildings: UNOSAT satellite counts, one stacked bar per assessment.
  const unosatRows = series("infra.structures.affected", { source: "unosat" }).map((t) => {
    const at = (m: string) => series(m, { source: "unosat" }).find((o) => o.as_of === t.as_of)?.value;
    return {
      date: t.as_of,
      destroyed: at("infra.structures.destroyed") ?? 0,
      severe: at("infra.structures.severely_damaged") ?? 0,
      moderate: at("infra.structures.moderately_damaged") ?? 0,
      ...(at("infra.structures.possibly_damaged") !== undefined ? { possible: at("infra.structures.possibly_damaged")! } : {}),
      total: t.value,
      ...(at("infra.structures.affected_share") !== undefined ? { share: at("infra.structures.affected_share")! } : {}),
    };
  });
  const unosatLast = series("infra.structures.affected", { source: "unosat" }).at(-1)!;
  const gmoRows = [
    "infra.housing_units.destroyed",
    "infra.schools.destroyed",
    "infra.schools.damaged",
    "infra.government_buildings.destroyed",
    "infra.mosques.destroyed",
    "infra.mosques.damaged",
    "infra.churches.destroyed",
  ].map((m) => latest(m, { source: "gaza-gmo" }));

  const ipcRows = [...all("ipc.people.famine"), ...all("ipc.people.crisis_or_worse")].sort((a, b) => a.as_of.localeCompare(b.as_of));
  const israelRows = [
    ...all("israel.killed.oct7"),
    ...all("israel.hostages.taken"),
    ...all("israel.security.killed"),
    ...all("israel.soldiers.killed_gaza_since_ceasefire"),
    ...all("idf.combatants_killed.gaza"),
    ...all("idf.estimate.gaza_toll"),
    ...all("idf.combatants_killed.since_ceasefire"),
  ];

  return (
    <>
      <section className="hero" id="top">
        <p className="eyebrow">Updated to {fmtDate(killed.as_of)}</p>
        <h1>What the record shows in Gaza</h1>
        <p className="lede">
          Gaza&apos;s Ministry of Health has recorded <strong>{fmt(killed.value)}</strong> deaths since 7 October 2023,{" "}
          <strong>{fmt(sinceCf.value)}</strong> of them since the October 2025 ceasefire.
        </p>
        <p className="note">
          Each figure names the body that published it and links to the document. Figures from different bodies often count
          different things, so they are shown side by side and never merged.
        </p>
        <div className="legend" aria-label="Labels used on this site">
          <span><KindBadge kind="count" /> a tally a named body recorded</span>
          <span><KindBadge kind="claim" /> stated by a party, with no method others can check (not a finding that it is wrong)</span>
          <span><KindBadge kind="estimate" /> modeled, with an uncertainty range</span>
        </div>
      </section>

      <div className="chapters-layout">
      <Chapters items={CHAPTERS} />
      <div className="chapters-body">
      <section className="chapter" id="deaths">
        <div className="block-head">
          <h2>Recorded deaths in Gaza</h2>
          <p className="note">
            Gaza Ministry of Health totals. The Ministry is part of Gaza&apos;s civil administration, which Hamas has governed since
            2007, and its figures do not separate civilians from combatants. See the method page for how the Ministry counts and
            how its figures compare with independent studies.
          </p>
        </div>
        <div className="stats">
          <Stat lead label="Killed" o={killed} />
          <Stat current={killed.as_of} label="Injured" o={latest("gaza.injured.total", { source: "gaza-moh" })} />
          <Stat current={killed.as_of} label="Children killed" o={latest("gaza.killed.children")} />
          <Stat current={killed.as_of} label="Women killed" o={latest("gaza.killed.women")} />
          <Stat current={killed.as_of} label="Medical personnel killed" o={latest("gaza.killed.medical")} />
          <Stat current={killed.as_of} label="Journalists killed" o={latest("gaza.killed.press")} />
        </div>
        <Attribution o={killed} />
        <Panel
          title="Since 7 October 2023"
          note={
            <>
              Running totals from {fmt(history[0].points.length)} Ministry daily reports. The children and women lines stop on{" "}
              {fmtDate(childrenLast.date)} because the daily reports since then give only the overall total, not because those
              deaths stopped: the total has kept rising. Before that, the breakdown was reported less often than the total, and
              the lines join the days it was. Days reported only by the Government Media Office, or with no known source, are
              left out.
            </>
          }
        >
          <HistoryChart label="Deaths recorded by the Gaza Ministry of Health since 7 October 2023" series={history} markers={[{ date: CEASEFIRE, label: "Ceasefire" }]} />
          <Attribution o={historyLast} />
        </Panel>
        <div className="grid-2">
          <Panel
            title="Deaths since the ceasefire"
            note={<>Running total since 10–11 October 2025, as reported on each date. A further {fmt(recovered.value)} bodies recovered from rubble are counted separately.</>}
          >
            <LineChart
              label="Deaths in Gaza since the October 2025 ceasefire"
              start={{ date: CEASEFIRE, value: 0 }}
              points={cfSeries.map((o) => ({ date: o.as_of, value: o.value, note: o.document.publisher }))}
            />
            <Attribution o={sinceCf} />
          </Panel>
          <Panel
            title="Who the named victims were"
            note={<>Age and sex of the {fmt(namedTotal)} people identified by name and ID in Ministry lists. Children are {Math.round((namedChildren / namedTotal) * 100)}% of them.</>}
          >
            <GroupedBars
              label="Named victims by age group and sex"
              groups={ages}
              series={sexes}
              values={Object.fromEntries(ages.map((a) => [a.key, Object.fromEntries(sexes.map((x) => [x.key, named(a.key, x.key).value]))]))}
            />
            <Attribution o={namedAsOf} />
            <p className="text-sm">
              <a href="/named-victims/">Search the list of names</a>
            </p>
          </Panel>
        </div>
      </section>

      <section className="chapter" id="access">
        <div className="block-head">
          <h2>Deaths recorded with an access-related cause</h2>
          <p className="note">
            Deaths a named body attributes to hunger, blocked medical evacuation, or violence while seeking food. Only what was
            recorded with that cause is shown; this site does not judge which other deaths were preventable.
          </p>
        </div>
        <div className="grid-2">
          <FlagCard title="Malnutrition and starvation" o={latest("gaza.deaths.malnutrition")} />
          <FlagCard
            title="Died awaiting medical evacuation"
            o={latest("gaza.deaths.awaiting_medevac")}
            detail="Patients on the evacuation list who died before they could leave Gaza."
          />
          <FlagCard title="Killed while seeking food aid (UN count)" o={aidUn} />
          <FlagCard title="Killed while seeking food aid (Ministry count)" o={aidMoh} />
        </div>
      </section>

      <section className="chapter" id="estimates">
        <div className="block-head">
          <h2>What independent studies estimate</h2>
          <p className="note">
            Peer-reviewed models, shown as ranges and never added to the counts above. The band is each study&apos;s 95%
            interval, the dot its central estimate, and the diamond what the Ministry recorded for the same period.
          </p>
        </div>
        <Panel>
          <RangeChart
            label="Mortality estimates from independent studies"
            rows={[
              { label: metric(traumatic.metric).label, sub: `${source(traumatic.source).name}, ${fmtPeriod(traumatic)}`, low: traumatic.low!, high: traumatic.high!, central: traumatic.value },
              { label: metric(violent.metric).label, sub: `${source(violent.source).name}, ${fmtPeriod(violent)}`, low: violent.low!, high: violent.high!, central: violent.value, recorded: violentMoh.value },
              { label: metric(excess.metric).label, sub: `${source(excess.source).name}, ${fmtPeriod(excess)}`, low: excess.low!, high: excess.high!, central: excess.value },
            ]}
          />
        </Panel>
        <div className="data-table">
          <Table>
            <TableHeader>
              <TableRow><TableHead>Study</TableHead><TableHead>Measures</TableHead><TableHead className="num">Estimate</TableHead><TableHead className="num">95% interval</TableHead><TableHead>Period</TableHead><TableHead>Method and findings</TableHead></TableRow>
            </TableHeader>
            <TableBody>
              {estimates.map((o) => (
                <TableRow key={o.id}>
                  <TableCell className="whitespace-normal"><a href={o.document.url} target="_blank" rel="noopener noreferrer">{source(o.source).name}</a></TableCell>
                  <TableCell className="whitespace-normal">{metric(o.metric).label}</TableCell>
                  <TableCell className="num">{fmt(o.value)}</TableCell>
                  <TableCell className="num">{fmt(o.low!)}–{fmt(o.high!)}</TableCell>
                  <TableCell>{fmtPeriod(o)}</TableCell>
                  <TableCell className="wide whitespace-normal">{o.caveat}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </section>

      <section className="chapter" id="aid">
        <div className="block-head">
          <h2>Aid: what each side counts</h2>
          <p className="note">
            Israel&apos;s COGAT counts every truck it clears, including commercial goods. The UN2720 mechanism counts only
            UN-manifested cargo and tracks whether it arrives. Read the last column before comparing numbers.
          </p>
        </div>
        <Panel
          title="UN-manifested aid delivered each month (UN2720)"
          note="Tonnes offloaded at the crossings, from the UN2720 monthly reports. Months with no stored figure are left empty: the March and April 2025 reports state that no aid was delivered."
        >
          <MonthlyBars
            label="Tonnes of UN-manifested aid delivered to Gaza each month, UN2720 mechanism"
            unit="Tonnes"
            points={delivered.map((o) => ({ month: o.as_of.slice(0, 7), value: o.value, prefix: boundPrefix(o.bound) }))}
          />
          <Attribution o={deliveredLast} />
        </Panel>
        <div className="data-table">
          <Table>
            <TableHeader>
              <TableRow><TableHead>Figure</TableHead><TableHead className="num">Value</TableHead><TableHead>Type</TableHead><TableHead>Publisher</TableHead><TableHead>Period</TableHead><TableHead>What it counts</TableHead></TableRow>
            </TableHeader>
            <TableBody>{aidRows.map((o) => <Row key={o.id} o={o} />)}</TableBody>
          </Table>
        </div>
      </section>

      <section className="chapter" id="hospitals">
        <div className="block-head">
          <h2>Hospitals</h2>
          <p className="note">
            WHO tracks the status of Gaza&apos;s hospitals from reports by the hospitals and its own staff. Its definitions are below
            and on the method page. Two WHO series are shown because they count differently: the situation reports cover 36
            hospitals, while WHO&apos;s monthly HeRAMS snapshots cover the 35 hospitals it evaluates, excluding field hospitals.
          </p>
        </div>
        {hrNow.evaluated && hrNow.full && hrNow.non && hrNow.destroyed && (
          <Panel
            title={`Hospitals today: ${fmt(hrNow.full.value)} fully functioning, ${fmt(hrNow.partial.value)} partially functioning`}
            note={
              <>
                Status on {fmtDate(hrLatest.as_of)} of the {fmt(hrNow.evaluated.value)} hospitals WHO evaluates each month,
                excluding field hospitals. WHO&apos;s situation reports count 36 hospitals in Gaza. A partially functioning
                hospital is open but cannot provide all its usual services; see the definitions below.
              </>
            }
          >
            <StatusBar
              label={`Status of ${hrNow.evaluated.value} hospitals in Gaza, WHO HeRAMS, ${fmtDate(hrLatest.as_of)}`}
              total={hrNow.evaluated.value}
              parts={[
                { label: "Fully functioning", o: hrNow.full, color: "var(--count)" },
                { label: "Partially functioning", o: hrNow.partial, color: "var(--status-partial)" },
                { label: "Not functioning", o: hrNow.non, color: "var(--status-down)" },
                { label: "Destroyed", o: hrNow.destroyed, color: "var(--red)" },
              ]}
            />
            <Attribution o={hrLatest} showPeriod={false} />
          </Panel>
        )}
        <Panel
          title="Each hospital"
          note={
            <>
              All {hosp.list.length} hospitals in the Ministry of Health and Health Cluster list of {fmtDate(hosp.listDate)}, with the
              newest WHO statement that names each one. WHO&apos;s monthly counts above do not say which hospital is in which
              status, so this list uses WHO&apos;s situation reports, which name {hospNamed} of them. Check the date: some statements
              are old, and a hospital&apos;s status can change without WHO naming it again.
            </>
          }
        >
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
                {GOVERNORATES.flatMap((g) => [
                  <TableRow key={g} className="hover:bg-transparent">
                    <TableCell colSpan={5} className="pt-4 font-mono text-[0.6875rem] tracking-[0.06em] text-muted-foreground uppercase">
                      {g === "Deir Albalah" ? "Deir al-Balah" : g}
                    </TableCell>
                  </TableRow>,
                  ...hosp.list
                    .filter((h) => h.governorate === g)
                    .map((h) => (
                      <TableRow key={h.name}>
                        <TableCell className="whitespace-normal">
                          <span className="font-medium">{h.name}</span>
                          <span className="block font-arabic text-muted-foreground" lang="ar" dir="rtl">{h.ar_name}</span>
                        </TableCell>
                        <TableCell className="min-w-40 whitespace-normal">
                          <HospitalStatusBadge status={h.latest?.status} />
                          {h.latest && <span className="mt-1 block text-xs text-muted-foreground sm:hidden">{fmtDate(h.latest.as_of)}</span>}
                          {h.latest && (
                            <details className="mt-1 text-xs text-muted-foreground">
                              <summary className="cursor-pointer">WHO&apos;s words</summary>
                              <p className="mt-1">
                                &ldquo;{h.latest.quote}&rdquo;{" "}
                                <a href={h.latest.document.url} target="_blank" rel="noopener noreferrer">source</a>
                              </p>
                            </details>
                          )}
                        </TableCell>
                        <TableCell className="hidden sm:table-cell">{h.latest ? fmtDate(h.latest.as_of) : ""}</TableCell>
                        <TableCell className="num hidden sm:table-cell">{h.beds ?? ""}</TableCell>
                        <TableCell className="hidden sm:table-cell">{h.type}</TableCell>
                      </TableRow>
                    )),
                ])}
              </TableBody>
            </Table>
          </div>
          <p className="attr">
            Hospital list: {hosp.sourceNote}{" "}
            <a href={hosp.listDoc.url} target="_blank" rel="noopener noreferrer">source</a>. Statuses: WHO situation reports,
            quoted word for word. &ldquo;Services reported&rdquo; means WHO names services running there without stating the
            hospital&apos;s overall status.
          </p>
        </Panel>
        <Panel
          title="Hospital status since October 2023"
          note={
            <>
              Number of hospitals in each status on the date WHO reported it; lines join the reports. In the first weeks WHO
              counted hospitals not functioning instead, from {fmt(sitNon[0].value)} on {fmtDate(sitNon[0].as_of)} to{" "}
              {fmt(sitNon.at(-1)!.value)} on {fmtDate(sitNon.at(-1)!.as_of)}. Some reports between January and May 2024 gave the
              status only in a graphic that cannot be read reliably.
            </>
          }
        >
          <HistoryChart
            label="Gaza hospitals by status, as reported by WHO"
            series={[
              { key: "sitPartial", label: "Partially functioning, of 36", points: pts(sitPartial), color: "var(--chart-1)" },
              { key: "hrPartial", label: "Partially functioning, of 35 (HeRAMS)", points: pts(hrPartial), color: "var(--chart-1)", dashed: true },
              { key: "hrNon", label: "Not functioning", points: pts(hrNon), color: "var(--chart-3)" },
              { key: "hrDestroyed", label: "Destroyed", points: pts(hrDestroyed), color: "var(--chart-2)" },
            ]}
          />
          <Attribution o={hrLatest} showPeriod={false} />
        </Panel>
        <div className="grid-2">
          <Panel title="What the statuses mean (WHO)">
            <dl className="grid gap-3 text-sm">
              <div>
                <dt className="font-semibold">Fully functioning</dt>
                <dd className="text-muted-foreground">
                  &ldquo;defined by the absence of major or systemic issues impeding the ability to deliver the full range of
                  expected services&rdquo;.
                </dd>
              </div>
              <div>
                <dt className="font-semibold">Partially functioning</dt>
                <dd className="text-muted-foreground">
                  &ldquo;when its capacity to deliver services is significantly affected, potentially due to infrastructure damage,
                  resource shortages, or a surge in service demand.&rdquo; The hospital is open, but some services, beds or supplies
                  are missing, so not every patient can be treated there.
                </dd>
              </div>
              <div>
                <dt className="font-semibold">Not functioning or destroyed</dt>
                <dd className="text-muted-foreground">
                  &ldquo;considered &lsquo;not operational&rsquo; meaning they are unable to provide any health service in their current
                  state.&rdquo;
                </dd>
              </div>
            </dl>
            <p className="attr">
              Definitions from WHO&apos;s{" "}
              <a href={hrDefinitions.document.url} target="_blank" rel="noopener noreferrer">
                HeRAMS Gaza infographics
              </a>
              . More on the <a href="/methodology/#hospitals">method page</a>.
            </p>
          </Panel>
          <Panel title="Attacks on health care (WHO)" note="Recorded by WHO's Surveillance System for Attacks on Health Care since 7 October 2023.">
            <div className="stats">
              <Stat label="Attacks on health care" o={attacks} />
              <Stat label="People killed in those attacks" o={latest("health.attacks.killed", { source: "who" })} />
              <Stat label="Hospitals damaged" o={latest("health.hospitals.damaged", { source: "who" })} />
            </div>
            <Attribution o={attacks} />
          </Panel>
        </div>
      </section>

      <section className="chapter" id="buildings">
        <div className="block-head">
          <h2>Buildings and infrastructure</h2>
          <p className="note">
            Two sources that measure different things. UNOSAT, the UN satellite centre, counts damaged structures it can see in
            satellite images. Gaza&apos;s Government Media Office reports totals by type of building without publishing a method,
            so its figures are labelled claims.
          </p>
        </div>
        <Panel
          title="Damaged and destroyed structures, from satellite images (UNOSAT)"
          note={
            <>
              Each bar is one UNOSAT assessment. Hover for the share of all structures in the Gaza Strip. UNOSAT added a
              &ldquo;possibly damaged&rdquo; class in May 2024, which is part of the jump that month. The assessments are marked
              preliminary and not validated on the ground.
            </>
          }
        >
          <StackedBars
            label="Structures in the Gaza Strip by damage class, UNOSAT satellite assessments"
            rows={unosatRows}
            stacks={[
              { key: "destroyed", label: "Destroyed", color: "var(--chart-1)" },
              { key: "severe", label: "Severely damaged", color: "var(--chart-3)" },
              { key: "moderate", label: "Moderately damaged", color: "var(--chart-2)" },
              { key: "possible", label: "Possibly damaged", color: "var(--chart-5)" },
            ]}
            extra={[
              { key: "total", label: "Total affected" },
              { key: "share", label: "Share of all structures", prefix: "about ", suffix: "%" },
            ]}
          />
          <Attribution o={unosatLast} />
        </Panel>
        <div className="data-table">
          <Table>
            <TableHeader>
              <TableRow><TableHead>Figure</TableHead><TableHead className="num">Number</TableHead><TableHead>Type</TableHead><TableHead>Publisher</TableHead><TableHead>Period</TableHead><TableHead>What it counts</TableHead></TableRow>
            </TableHeader>
            <TableBody>{gmoRows.map((o) => <Row key={o.id} o={{ ...o, caveat: undefined }} />)}</TableBody>
          </Table>
        </div>
        <p className="attr">
          Government Media Office figures as republished by Tech for Palestine, latest reported value of each. The office does
          not publish a method, and Tech for Palestine advises treating the figures as estimates. They are not checked against
          satellite counts, and the two sources classify buildings differently.
        </p>
      </section>

      <section className="chapter" id="food">
        <div className="block-head">
          <h2>Food security findings (IPC)</h2>
          <p className="note">
            The Integrated Food Security Phase Classification is the joint UN and NGO standard for measuring hunger.
          </p>
        </div>
        <div className="data-table">
          <Table>
            <TableHeader>
              <TableRow><TableHead>Finding</TableHead><TableHead className="num">People</TableHead><TableHead>Type</TableHead><TableHead>Publisher</TableHead><TableHead>Period</TableHead><TableHead>Notes</TableHead></TableRow>
            </TableHeader>
            <TableBody>{ipcRows.map((o) => <Row key={o.id} o={o} />)}</TableBody>
          </Table>
        </div>
      </section>

      <section className="chapter" id="israel">
        <div className="block-head">
          <h2>Israeli casualties and IDF figures</h2>
          <p className="note">
            Deaths on the Israeli side, and figures the IDF has given about the war in Gaza. Israeli deaths and hostage figures are
            counts recorded by named bodies. Only the IDF&apos;s figures for combatants killed in Gaza are labelled claims, because
            the military has not published names or a method others can check. That label is about what can be checked, not a
            finding that the figures are wrong. The names of those killed in the 7 October attack are on the{" "}
            <a href="/named-victims/#oct7">named victims page</a>.
          </p>
        </div>
        <Panel
          title="Combatants killed in Gaza, as stated by the IDF"
          note={
            <>
              Each dot is a figure the IDF gave publicly on that date; the dashed line only joins them. The IDF does not publish
              a running count, names or method, so these are claims. They count people the IDF says belonged to armed groups and
              are not a share of the Ministry of Health&apos;s total, which does not separate civilians from combatants. Some of
              these statements do not say whether they include attackers killed inside Israel on 7 October; hover a dot, or see
              the table below, for each one&apos;s wording.
            </>
          }
        >
          <StatementChart
            label="Combatants the IDF says it killed in Gaza, by date of statement"
            unit="Combatants"
            points={idfClaims.map((o) => ({ date: o.as_of, value: o.value, prefix: boundPrefix(o.bound), publisher: o.document.publisher }))}
          />
          <Attribution o={idfClaims.at(-1)!} />
        </Panel>
        <div className="data-table">
          <Table>
            <TableHeader>
              <TableRow><TableHead>Figure</TableHead><TableHead className="num">Number</TableHead><TableHead>Type</TableHead><TableHead>Publisher</TableHead><TableHead>Period</TableHead><TableHead>Context</TableHead></TableRow>
            </TableHeader>
            <TableBody>{israelRows.map((o) => <Row key={o.id} o={o} />)}</TableBody>
          </Table>
        </div>
      </section>
      </div>
      </div>
    </>
  );
}
