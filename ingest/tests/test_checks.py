import datetime as dt

from ingest import checks, store

TODAY = dt.date.today()


def _obs(**kw):
    base = {
        "id": "gaza-moh-gaza-killed-total-2026-10-16", "metric": "gaza.killed.total", "value": 74000, "kind": "count",
        "bound": "exact", "source": "gaza-moh", "as_of": "2026-10-16", "period_start": "2023-10-07", "period_end": "2026-10-16",
        "document": {"url": "https://example.org", "publisher": "x", "retrieved_at": "2026-10-16"}, "added_by": "seed",
    }
    base.update(kw)
    return base


def _run(extra):
    return checks.check(store.load_observations() + extra, store.load_metrics(), store.load_sources(), today=TODAY)


def test_stored_data_passes():
    assert _run([]).ok


def test_running_total_going_down_is_flagged():
    res = _run([_obs()])
    assert res.ok
    assert any("lower than" in r for r in res.flags["gaza-moh-gaza-killed-total-2026-10-16"])


def test_future_dates_and_missing_intervals_fail():
    future = (TODAY + dt.timedelta(days=1)).isoformat()
    assert not _run([_obs(as_of=future, period_end=future, id="x-future")]).ok
    assert not _run([_obs(kind="estimate", id="x-est")]).ok


def test_automated_figures_need_evidence():
    assert not _run([_obs(id="x-auto", added_by="importer:press", value=75000)]).ok



def test_hospital_status_rules():
    from ingest import checks
    hl = {"hospitals": [{"name": "Nasser Hospital", "governorate": "Khan Younis"}]}
    ok = {"statements": [{"hospital": "Nasser Hospital", "status": "services_reported", "as_of": "2026-06-30",
                          "quote": "four operational units (Al Shifa Hospital, Nasser Medical Complex, ...)",
                          "document": {"url": "u", "sha256": "a" * 64}}]}
    assert checks.check_hospitals(hl, ok) == []
    bad = {"statements": [{**ok["statements"][0], "hospital": "Unknown Hospital", "status": "fine"}]}
    errs = checks.check_hospitals(hl, bad)
    assert any("not in hospitals.json" in e for e in errs) and any("unknown status" in e for e in errs)


def test_memorial_links_by_hand_are_checked_like_matched_ones():
    victims = {"records": [["Reem Ali Khalil Badwan", "ريم علي خليل بدوان", 3, "f", 5]]}
    projects = {"gaza-shaheed": {"name": "Martyrs of Gaza", "url": "https://gazashaheed.com/"}}
    hand = {"projects": projects, "fields": ["ar_name", "age", "sex", "url", "project", "basis", "added"],
            "records": [["ريم علي خليل بدوان", 3, "f", "https://gazashaheed.com/reem/", "gaza-shaheed", "why", "2026-10-19"]]}
    assert checks.check_memorial_links(None, victims, hand) == []
    hand["records"][0][6] = ""
    hand["records"][0][1] = 4
    errors = checks.check_memorial_links(None, victims, hand)
    assert any("exactly one name" in e for e in errors) and any("date it was added" in e for e in errors)
