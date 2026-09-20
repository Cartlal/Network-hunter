import functools
from pathlib import Path

# IEEE OUI registration data (MA-L assignments), sourced from
# https://regauth.standards.ieee.org/ - same dataset nmap ships as
# nmap-mac-prefixes. ~52k entries, refreshed by replacing this file; not
# auto-updated at runtime since it rarely changes and this keeps discovery
# fully offline (no dependency on an nmap install or a network fetch).
_DATA_FILE = Path(__file__).parent / "data" / "oui_prefixes.txt"


@functools.lru_cache(maxsize=1)
def _load_prefixes() -> dict[str, str]:
    prefixes: dict[str, str] = {}
    with open(_DATA_FILE, encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split(None, 1)
            if len(parts) == 2:
                prefixes[parts[0].upper()] = parts[1].strip()
    return prefixes


def guess_vendor(mac: str | None) -> str | None:
    if not mac:
        return None
    key = mac.upper().replace(":", "").replace("-", "")[:6]
    return _load_prefixes().get(key)
