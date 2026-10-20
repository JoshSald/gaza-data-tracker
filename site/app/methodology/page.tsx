import type { Metadata } from "next";
import { KindBadge } from "@/components/Figure";

export const metadata: Metadata = { title: "Method · Gaza Data Tracker" };

export default function Methodology() {
  return (
    <div className="prose">
      <h1>How this site works</h1>
      <p>
        This site collects figures about the war in Gaza from the bodies that publish them and shows each one with its source,
        its date and what it measures. It does not produce figures of its own.
      </p>

      <h2>Three kinds of figure</h2>
      <dl>
        <dt><KindBadge kind="count" /> Count</dt>
        <dd>A tally a named body recorded, such as the Ministry of Health&apos;s death toll or COGAT&apos;s truck count.</dd>
        <dt><KindBadge kind="claim" /> Claim</dt>
        <dd>
          A figure a party states without names, records or a method that others can check, such as IDF figures for combatants
          killed. The label describes what has been published, not whether the figure is right: a claim may well be accurate. It
          applies to any party&apos;s figures in the same way, and a figure would be labelled a count once the names or method
          behind it were published.
        </dd>
        <dt><KindBadge kind="estimate" /> Estimate</dt>
        <dd>A number produced by a statistical model or survey, always shown with its uncertainty range and never added to counts.</dd>
      </dl>

      <h2>Qualified numbers</h2>
      <p>
        When a publisher writes &ldquo;at least&rdquo; or &ldquo;about&rdquo;, the site keeps that wording next to the number.
      </p>

      <h2>About the Gaza Ministry of Health</h2>
      <p>
        The Ministry of Health is part of Gaza&apos;s civil administration, which Hamas has governed since 2007. Hamas has a
        political leadership, which runs that administration, and a separate armed wing. The Ministry&apos;s work, like running
        hospitals and registering deaths, is done by civil servants such as doctors, nurses and administrators. It counts deaths
        from hospital and morgue records, and its list of victims identifies each person by name and ID number, with reports
        from families added later.
      </p>
      <p>
        Its figures do not separate civilians from combatants. Israeli officials have often rejected them as Hamas figures. UN
        agencies have treated its totals as reliable, and in January 2026 a senior IDF official said the IDF believes its overall
        toll is largely accurate. Peer-reviewed studies, shown on the overview page, suggest it undercounts violent deaths.
      </p>

      <h2>Deaths linked to access</h2>
      <p>
        The site shows deaths a named body recorded as caused by malnutrition, by waiting for medical evacuation, or by violence
        while seeking aid. It does not decide which other deaths were preventable. Modeled excess deaths appear only in the
        estimates section.
      </p>

      <h2 id="hospitals">Hospital status</h2>
      <p>
        Hospital status comes from the World Health Organization. Until October 2025 WHO&apos;s situation reports counted the
        hospitals that were partially functioning out of 36. Since late 2024 its monthly HeRAMS snapshots (Health Resources and
        Services Availability Monitoring System) report every hospital it evaluates, currently 35, excluding field hospitals,
        as functioning, partially functioning, not functioning or destroyed. The site shows the two series separately. In
        WHO&apos;s words:
      </p>
      <dl>
        <dt>Fully functioning</dt>
        <dd>
          Functionality is &ldquo;defined by the absence of major or systemic issues impeding the ability to deliver the full range
          of expected services.&rdquo; A hospital &ldquo;may still be considered fully functional if some services are partially or
          temporarily unavailable.&rdquo;
        </dd>
        <dt>Partially functioning</dt>
        <dd>
          A hospital &ldquo;is considered partially functional when its capacity to deliver services is significantly affected,
          potentially due to infrastructure damage, resource shortages, or a surge in service demand.&rdquo; WHO&apos;s situation
          reports put it as being &ldquo;unable to fully provide some or all of the services as normal, or there is an interruption
          in any of the services provided at the facility.&rdquo;
        </dd>
        <dt>Not functioning or destroyed</dt>
        <dd>
          Hospitals &ldquo;reported as destroyed or non-functioning are considered &lsquo;not operational&rsquo; meaning they are
          unable to provide any health service in their current state.&rdquo;
        </dd>
      </dl>
      <p>
        What this means for patients: a partially functioning hospital is open, but WHO records which of its services are
        available, only partly available or missing. A service counts as partly available when the hospital &ldquo;has insufficient
        capacity or resources to meet daily demand, or is unable to provide the full service in accordance with national
        standards.&rdquo; Patients who need a missing service, such as intensive care, surgery or dialysis, may need to be
        moved to another hospital or wait, and a hospital that is not functioning provides no care at all. WHO&apos;s October 2025
        situation report noted that &ldquo;many health facilities remain out of service, due to infrastructure damage,
        inaccessibility, and loss of equipment and supplies.&rdquo;
      </p>
      <p>
        Attacks on health care are counted by WHO&apos;s Surveillance System for Attacks on Health Care, which records attacks on
        facilities, transport, health workers and patients.
      </p>

      <h2 id="buildings">Damage to buildings</h2>
      <dl>
        <dt>UNOSAT (UN Satellite Centre)</dt>
        <dd>
          Compares satellite images taken during the war with images from before it, and classes each structure as destroyed,
          severely, moderately or possibly damaged (the last class added in May 2024). It counts structures, not homes or
          people, and marks its Gaza assessments as preliminary and not validated on the ground. Its early assessments covered
          an &ldquo;area of interest&rdquo; that may not be the whole Strip.
        </dd>
        <dt>Gaza Government Media Office</dt>
        <dd>
          Part of Gaza&apos;s civil administration, which Hamas has governed since 2007. It reports running totals of homes,
          schools, mosques, churches and government buildings destroyed or damaged. It does not publish how these are counted,
          so they are labelled claims; Tech for Palestine, which republishes them, advises treating them as estimates.
        </dd>
      </dl>

      <h2 id="memorials">Memorial links</h2>
      <p>
        The named victims page links names to memorial pages kept by others: official Israeli memorial records for the 7
        October list, and independent projects for the Gaza list. Our aim is to acknowledge the individuals behind the
        statistics while maintaining a consistent, evidence-based approach to the information published on this website.
      </p>
      <p className="note">
        A link shows who a page is about. It never supplies a figure, and it does not endorse the page: memorials are kept by
        third parties and may express views this site does not hold. How pages are matched to names, which projects are used
        and which were set aside are set out in the{" "}
        <a href="https://github.com/JoshSald/gaza-data-tracker/blob/main/docs/memorial-links.md" target="_blank" rel="noopener noreferrer">
          memorial links policy
        </a>
        .
      </p>

      <h2>How figures are added</h2>
      <ul>
        <li>Scheduled importers read structured sources (the Tech for Palestine API) and fixed-format reports (UN2720 monthly PDFs).</li>
        <li>Free-text reports are read by a language model. Each figure it proposes must quote its sentence word for word from an archived copy of the document, and the quote must state the number. Figures that fail are rejected automatically.</li>
        <li>Automatic checks flag running totals that go down and sudden jumps.</li>
        <li>Every change is proposed as a pull request and published only after a person reviews it.</li>
      </ul>

      <h2>Corrections</h2>
      <p>
        Published figures are never edited or deleted. A correction is added as a new figure that names the one it replaces, so the
        history of every number stays visible in the public repository.
      </p>
    </div>
  );
}
