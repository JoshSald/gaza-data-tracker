from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OBSERVATIONS = DATA / "observations"
ARCHIVE = ROOT / "archive"
SCHEMA = ROOT / "schema"
WATCHLIST = DATA / "watchlist.json"
WATCH_STATE = DATA / "watch-state.json"
REPORT = ROOT / ".ingest-report.md"
