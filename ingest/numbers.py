"""Find numbers in text the way reports write them: 1,760 / 12.7K / 1.4 million / 1.9 million tons."""
from __future__ import annotations

import re

_MULT = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6, "mn": 1e6, "b": 1e9, "billion": 1e9}
_SEP = "[,   ]"
_NUM = re.compile(
    rf"(?<![\w.])(\d{{1,3}}(?:{_SEP}\d{{3}})+|\d+)(?:\.(\d+))?\s*(k|thousand|million|mn|m|billion|b)?(?![\w])",
    re.IGNORECASE,
)


def _matches(text: str) -> list[tuple[float, float]]:
    """(value, rounding tolerance) for each number. '12.7K' may stand for 12,650 to 12,750; '1,760' only for 1,760."""
    out = []
    # PDF text sometimes loses the space before a unit ("73Trucks"); restore it before a capitalised word only, so
    # ordinals such as "5th" are still not read as numbers.
    text = re.sub(r"(\d)(?=[A-Z][a-z]{2,})", r"\1 ", text)
    for m in _NUM.finditer(text):
        whole = re.sub(_SEP, "", m.group(1))
        frac = m.group(2) or ""
        n = float(f"{whole}.{frac}") if frac else float(whole)
        suffix = (m.group(3) or "").lower()
        mult = _MULT[suffix] if suffix else 1
        tol = 0.5 * 10 ** (-len(frac)) * mult if suffix else 0
        out.append((n * mult, tol))
    return out


def numbers_in(text: str) -> list[float]:
    return [n for n, _ in _matches(text)]


def quote_supports(value: float, quote: str) -> bool:
    """True when the quote states `value`, allowing only for the rounding the quote itself shows (12.7K)."""
    return any(abs(n - value) <= tol + 1e-9 for n, tol in _matches(quote))
