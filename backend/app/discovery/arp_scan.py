import asyncio
import re

# Windows: "  192.168.1.10          aa-bb-cc-dd-ee-ff     dynamic"
_WINDOWS_ARP_RE = re.compile(
    r"^\s*(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+(?P<mac>[0-9a-fA-F]{2}(?:-[0-9a-fA-F]{2}){5})",
    re.MULTILINE,
)
# Unix/BSD/macOS: "? (192.168.1.10) at aa:bb:cc:dd:ee:ff [ether] on eth0"
_UNIX_ARP_RE = re.compile(
    r"\((?P<ip>\d{1,3}(?:\.\d{1,3}){3})\)\s+at\s+(?P<mac>[0-9a-fA-F]{2}(?::[0-9a-fA-F]{2}){5})",
)


async def read_arp_table() -> dict[str, str]:
    """Read the OS ARP cache (populated by a prior ping sweep) and return an
    {ip: mac} map. Uses `arp -a`, which requires no elevated privileges."""
    proc = await asyncio.create_subprocess_exec(
        "arp", "-a", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    stdout, _ = await proc.communicate()
    output = stdout.decode(errors="ignore")

    mapping: dict[str, str] = {}
    for match in _WINDOWS_ARP_RE.finditer(output):
        mapping[match.group("ip")] = match.group("mac").replace("-", ":").upper()
    for match in _UNIX_ARP_RE.finditer(output):
        mapping[match.group("ip")] = match.group("mac").upper()
    return mapping
