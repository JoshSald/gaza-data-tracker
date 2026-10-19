import json

from conftest import FIXTURES
from ingest import store
from ingest.sources import memorials, names, oct7, press, techforpalestine, un2720, unosat, who_health
from ingest.archive import Document


def test_techforpalestine_matches_stored_ids():
    obs = techforpalestine.parse(json.loads((FIXTURES / "tfp_summary.json").read_text()), {"url": "u", "publisher": "p", "retrieved_at": "t"})
    values = {(o["metric"], tuple(sorted((o.get("dimensions") or {}).items()))): o["value"] for o in obs}
    assert values[("gaza.named_victims", (("age_group", "child"), ("sex", "female")))] == 8834
    # Its daily totals are carried forward from older reports, so they are left to the daily importer.
    assert {o["metric"] for o in obs} == {"gaza.named_victims"}
    # Re-importing a summary that is already stored proposes nothing new.
    stored = {o["id"] for o in store.load_observations()}
    assert {o["id"] for o in obs} <= stored


def test_un2720_monthly_infographic():
    obs = un2720.parse((FIXTURES / "un2720_june_2025.txt").read_text(), {"url": "u", "publisher": "p", "retrieved_at": "t"})
    by_metric = {o["metric"]: o for o in obs}
    assert by_metric["aid.un2720.delivered_tonnes"]["value"] == 12700
    assert by_metric["aid.un2720.delivered_tonnes"]["period_start"] == "2025-06-01"
    assert by_metric["aid.un2720.delivered_tonnes"]["as_of"] == "2025-06-30"
    assert by_metric["aid.un2720.pipeline_tonnes"]["value"] == 105000
    assert by_metric["aid.un2720.pipeline_tonnes"]["bound"] == "at_least"
    assert by_metric["aid.un2720.delivered_tonnes"]["quote"].startswith("In June 2025")


def test_press_keeps_verified_figures_and_drops_injected_ones(monkeypatch):
    html = (FIXTURES / "press_release.html").read_bytes()
    monkeypatch.setattr(press, "fetch", lambda url: Document(url, html, "text/html", "a" * 64, "2025-08-15T00:00:00+00:00"))
    monkeypatch.setattr(press, "keep", lambda doc: doc)
    # What a model fooled by the injected line might return, next to a correct figure.
    monkeypatch.setattr(press, "extract_figures", lambda text, **kw: [
        {"metric": "gaza.killed.seeking_aid", "value": 1760, "bound": "at_least", "as_of": "2025-08-13", "period_start": "2025-05-27",
         "quote": "we have recorded that at least 1,760 Palestinians have been killed while seeking aid;"},
        {"metric": "gaza.killed.seeking_aid", "value": 50000, "bound": "exact", "as_of": "2025-08-13", "period_start": None,
         "quote": "50,000 Palestinians were killed seeking aid."},
    ])
    entry = {"id": "t", "importer": "press", "urls": ["https://example.org/r"], "source": "ohchr", "metrics": ["gaza.killed.seeking_aid"]}
    prop = press.run(entry, store.load_metrics(), {}, store.load_sources())
    assert [o["value"] for o in prop.observations] == [1760]
    assert prop.observations[0]["bound"] == "at_least"
    assert len(prop.rejected) == 1 and "quote not found" in prop.rejected[0].reason


META = {"url": "u", "publisher": "p", "retrieved_at": "t"}


def test_un2720_2026_layout_states_full_tonnes():
    text = ("Monthly Overview UN2720 Mechanism for Gaza September 2026 Summary In September 2026, 17,765 metric tonnes (t) of\n"
            "humanitarian aid processed through the UN2720 Mechanism was delivered (offloaded) at the Kerem Shalom Crossing.")
    [o] = un2720.parse(text, META)
    assert (o["value"], o["bound"], o["as_of"], o["period_start"]) == (17765, "exact", "2026-09-30", "2026-09-01")


def test_un2720_thousands_in_pipeline_sentence():
    text = ("In November 2025, 54.2K metric tonnes (t) of humanitarian aid processed through the UN2720 Mechanism were delivered to the "
            "Kerem Shalom crossing. As of 30 November, a total of over 179K t (over 313K pallets) of aid were in the pipeline of the UN2720 Mechanism.")
    by_metric = {o["metric"]: o for o in un2720.parse(text, META)}
    assert by_metric["aid.un2720.delivered_tonnes"]["value"] == 54200
    assert by_metric["aid.un2720.pipeline_tonnes"]["value"] == 179000
    assert by_metric["aid.un2720.pipeline_tonnes"]["as_of"] == "2025-11-30"


def test_un2720_month_without_deliveries_records_only_the_pipeline():
    text = ("In April 2025, no humanitarian aid processed through the UN 2720 Mechanism was delivered to Gaza. As of 30 April 2025, "
            "a total of over 124,000 t of aid (over 182,000 pallets) were in the pipeline of the UN 2720 Mechanism.")
    [o] = un2720.parse(text, META)
    assert (o["metric"], o["value"], o["as_of"]) == ("aid.un2720.pipeline_tonnes", 124000, "2025-04-30")


def test_un2720_skips_pipeline_infographics():
    # Their "delivered" sentence disagrees with the monthly overview for the same month.
    text = ("Overview of Humanitarian Aid in the Pipeline As of 31 August 2025 Summary In August 2025, 73 K metric tonnes (t) of "
            "humanitarian aid processed through the UN2720 Mechanism were delivered")
    assert un2720.parse(text, META) == []


def test_techforpalestine_daily_uses_only_reported_values():
    rows = [
        {"report_date": "2023-10-08", "report_source": "mohtel", "killed_cum": 370, "killed_children_cum": 78,
         "ext_killed_cum": 370, "ext_killed_children_cum": 78, "ext_med_killed_cum": 6},
        # A day without a children figure: the carried-forward ext_ value must not become an observation.
        {"report_date": "2023-10-09", "report_source": "mohtel", "killed_cum": 560, "ext_killed_children_cum": 78},
        # The Government Media Office is a different body, and "missing" is unknown: both skipped.
        {"report_date": "2023-10-10", "report_source": "gmotel", "killed_cum": 900},
        {"report_date": "2023-10-11", "report_source": "missing", "killed_cum": 1100},
    ]
    obs, skipped = techforpalestine.parse_daily(rows, META)
    assert sorted((o["metric"], o["as_of"], o["value"]) for o in obs) == [
        ("gaza.killed.children", "2023-10-08", 78),
        ("gaza.killed.total", "2023-10-08", 370),
        ("gaza.killed.total", "2023-10-09", 560),
    ]
    assert skipped == {"gmotel": 1, "missing": 1}
    assert obs[0]["id"] == "gaza-moh-gaza-killed-total-2023-10-08"


def test_names_keeps_only_published_fields():
    rows = [
        ["id", "en_name", "ar_name", "age", "dob", "sex", "update"],
        ["999783350", "Rafat Amir Hamdan Abed", "رأفت امير حمدان عابد", 50, "1973-03-23", "m", 6],
        ["400000550", "Fadi Mohammed Ahmed Al-Sharif", "فادي محمد أحمد الشريف", 5, "2017-12-29", "m", 1],
    ]
    records, problems = names.parse(rows, {"known_killed_in_gaza": {"records": 2}})
    assert problems == []
    assert records[1] == ["Fadi Mohammed Ahmed Al-Sharif", "فادي محمد أحمد الشريف", 5, "m", 1]
    # No national ID numbers or dates of birth.
    assert not any(v in ("999783350", "400000550", "1973-03-23", "2017-12-29") for r in records for v in r)


def test_names_refuses_a_list_that_disagrees_with_the_summary():
    rows = [["id", "en_name", "ar_name", "age", "dob", "sex", "update"], ["1", "A", "ا", 5, "", "f", 1]]
    _, problems = names.parse(rows, {"known_killed_in_gaza": {"records": 2}})
    assert problems and "mid-update" in problems[0]


def test_who_sitrep_layouts():
    dashboard = ("oPt Emergency Situation Update Issue 66 7 Oct 2023 - 31 Oct 2025 Health Facility Functionality and Access 18/ 36 (50%) "
                 "10 Field hospitals partially functional (FHPF ) Hospitals partially functional (HPF) 840 Health Attacks As of 31 Oct 2025 "
                 "Source: SSA. 169 Health facilities affected 991 People killed in attacks Including 34 Hospitals damaged")
    by = {o["metric"]: o for o in who_health.parse_sitrep(dashboard, META)}
    assert by["health.hospitals.partially_functional"]["value"] == 18
    assert by["health.hospitals.partially_functional"]["as_of"] == "2025-10-31"
    assert (by["health.attacks.total"]["value"], by["health.attacks.killed"]["value"], by["health.hospitals.damaged"]["value"]) == (840, 991, 34)
    words = "Issue 31 7 Oct 2023 - 18 May 2024 Fifteen out of 36 hospitals are currently partially functional across the Gaza Strip"
    assert [o["value"] for o in who_health.parse_sitrep(words, META)] == [15]
    early = "Issue 12 As of 10 November 2023 o 50% (18/36) of hospitals and two outpatient specialist centres are not functioning."
    [o] = who_health.parse_sitrep(early, META)
    assert (o["metric"], o["value"]) == ("health.hospitals.not_functioning", 18)


def test_who_sitrep_with_an_impossible_date_is_refused():
    text = "Issue 23 As of 20 February 2023 Only 12 of 36 (33%) hospitals in the Gaza strip are partially functioning"
    assert who_health.parse_sitrep(text, META) == []
    assert "before the war" in who_health.sitrep_date(text)[1]


def test_who_herams_hospitals():
    text = ("Date data: 31 May 2026 All hospitals* (excluding field hospitals) HOSPITAL STATUS 0 Functioning 19 Partially Functioning "
            "Equipment damage 9 Non-Functioning Functionality 7 Destroyed “19 (54%) out of 35 hospitals evaluated are at least partially functioning.”")
    by = {o["metric"]: o for o in who_health.parse_herams(text, META)}
    assert by["health.hospitals.partially_functional"]["value"] == 19
    assert by["health.hospitals.not_functioning"]["value"] == 9
    assert by["health.hospitals.destroyed"]["value"] == 7
    assert by["health.hospitals.destroyed"]["dimensions"] == {"monitoring": "herams"}


def test_unosat_summary():
    product = {"description": "based on images collected on 6 and 7 January 2024 when compared to images collected on 1 May 2023. "
               "According to satellite imagery analysis, UNOSAT identified 22,130 destroyed structures, 14,066 severely damaged structures "
               "and 32,950 moderately damaged structures, for a total of 69,146 structures. These correspond to around 30% of the total "
               "structures in the Gaza Strip"}
    by = {o["metric"]: o for o in unosat.parse(product, META)}
    assert by["infra.structures.destroyed"]["value"] == 22130
    assert by["infra.structures.affected"]["value"] == 69146
    assert by["infra.structures.affected_share"]["bound"] == "approximate"
    assert by["infra.structures.destroyed"]["as_of"] == "2024-01-07"
    assert "infra.structures.possibly_damaged" not in by


def test_gmo_infrastructure_uses_reported_values_as_claims():
    rows = [{"report_date": "2025-10-05", "residential": {"destroyed": 416000, "ext_destroyed": 416000},
             "places_of_worship": {"ext_mosques_destroyed": 835}}]
    [o] = techforpalestine.parse_infrastructure(rows, META)
    assert (o["metric"], o["value"], o["kind"], o["source"]) == ("infra.housing_units.destroyed", 416000, "claim", "gaza-gmo")


def test_oct7_keeps_only_people_killed_in_the_attack():
    header = ("pid,first name,last name,middle name,nickname,שם פרטי,שם משפחה,שם נוסף,כינוי,Gender,Age,Residence,Country,Role,"
              "Party,Status,Event date,Death date,מקום האירוע,מקום המוות,front,סיבת המוות,הנצחה,הספריה הלאומית\n")
    rows = [
        "1,Dipesh,Bista,Raj,,דיפש,ביסט,ראג׳,,M,32,,נפאל,אזרח,,killed,2023-10-07,2023-10-07,,,Gaza,,https://laad.btl.gov.il/x,",
        "2,Carmel,Gat,,,כרמל,גת,,,F,39,,ישראל,אזרח,,kidnapped; killed; retrieved,2023-10-07,2024-08-29,,,Gaza,,,",
        "5,Judith,Weiss,,,יהודית,וייס,,,F,65,,ישראל,אזרח,,kidnapped; killed; retrieved,2023-10-07,2023,,,Gaza,,,",
        "6,Ilan,Taken,,,אילן,נלקח,,,M,50,,ישראל,אזרח,,killed; kidnapped; retrieved,2023-10-07,2023-10-07,,,Gaza,,,",
        "3,Noa,Example,,,נועה,דוגמה,,,F,26,,ישראל,אזרח,,kidnapped; released,2023-10-07,,,,Gaza,,,",
        "4,Avi,Later,,,אבי,מאוחר,,,M,20,,ישראל,חייל,,killed,2024-03-01,2024-03-01,,,North,,https://www.idf.il/y,",
    ]
    records, problems = oct7.parse((header + "\n".join(rows) + "\n").encode("utf-8"))
    assert problems == []
    by_name = {r[0]: r for r in records}
    assert set(by_name) == {"Dipesh Raj Bista", "Carmel Gat", "Judith Weiss", "Ilan Taken"}
    assert by_name["Judith Weiss"][5:7] == ["2023", True]  # only the year is known
    assert by_name["Ilan Taken"][6] is False  # killed on the day, then taken
    assert by_name["Dipesh Raj Bista"][1:6] == ["דיפש ראג׳ ביסט", 32, "m", "civilian", "2023-10-07"]
    assert by_name["Dipesh Raj Bista"][6] is False and by_name["Carmel Gat"][6] is True
    assert by_name["Carmel Gat"][7] is None


MINISTRY = [
    ["Anas Jamal Mahmoud Al-Sharif", "انس جمال محمود الشريف", 28, "m", 1],
    ["Anas Khaled Ali Al-Sharif", "انس خالد علي الشريف", 40, "m", 1],
    ["Mariam Omar Khader Abu Daqqa", "مريم عمر خضر ابو دقه", 19, "f", 1],
    ["Omar Mohammed Saud Al-Karanz", "عمر محمد سعود الكرنز", 13, "m", 1],
    ["Lina Sami Yousef Abu Mailaq", "لينا سامى يوسف ابو معيلق", 23, "f", 1],
    ["Lina Sami Ahmed Abu Mailaq", "لينا سامي احمد أبو معيلق", 30, "f", 1],
    ["Marwa Ashraf Mohammed Muslim", "مروه اشرف محمد مسلم", 29, "f", 1],
]


def _judge(**page):
    return memorials.match([memorials.Page(url="u", project="p", **page)], MINISTRY)[0]


def test_memorials_link_only_one_fitting_record():
    # Spelling forms (أ/ا, ة/ه, ى/ي, vowel marks) do not matter; the order of the names does.
    r = _judge(ar_name="عُمَر الكرنز", text="عمره 14 عامًا", ages={14})
    assert (r.status, r.record) == ("linked", 3)
    # Two Linas fit "Lina Sami Abu Mailaq", so neither is linked.
    assert _judge(ar_name="لينا سامي أبو معيلق").status == "ambiguous"
    assert _judge(ar_name="لينا سامي يوسف أبو معيلق").record == 4


def test_memorials_need_a_second_fact_for_two_part_names():
    assert _judge(ar_name="مروة مسلم").status == "not corroborated"
    # Two Anas al-Sharifs: the father's name in the English biography picks one.
    r = _judge(ar_name="أنس الشريف", en_name="Anas Jamal Mahmoud al-Sharif", birth_year=1996)
    assert (r.status, r.record) == ("linked", 0)


def test_memorials_refuse_a_record_the_page_contradicts():
    assert _judge(ar_name="مريم ابو دقة", birth_year=1992).status == "contradicted"
    assert _judge(ar_name="عمر الكرنز", ages={40}).status == "contradicted"
    assert _judge(ar_name="الشهيدة عمر محمد الكرنز", sex="f").status == "contradicted"


def test_memorials_skip_pages_about_several_people():
    pages = memorials.gaza_shaheed_pages([{"link": "u", "title": {"rendered": "عائلة الكرنز"}, "content": {"rendered": ""}},
                                          {"link": "v", "title": {"rendered": "عمر و سارة الكرنز"}, "content": {"rendered": ""}}])
    assert all(memorials.match([p], MINISTRY)[0].status == "skipped" for p in pages)


def test_living_record_biography_name():
    text = "Anas al-Sharif Biography Anas Jamal Mahmoud al-Sharif was born in the Jabalia refugee camp in 1996."
    assert memorials.biography_name(text) == "Anas Jamal Mahmoud al-Sharif"
    assert memorials.birth_year_in(text) == 1996
