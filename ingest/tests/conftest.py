import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ["ARCHIVE_DISABLED"] = "1"

FIXTURES = Path(__file__).parent / "fixtures"
