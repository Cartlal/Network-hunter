import asyncio
import platform
import re


async def get_default_gateway() -> str | None:
    """Best-effort default gateway lookup via OS commands (no elevation needed)."""
    if platform.system() == "Windows":
        proc = await asyncio.create_subprocess_exec(
            "ipconfig", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
        )
        stdout, _ = await proc.communicate()
        text = stdout.decode(errors="ignore")
        match = re.search(r"Default Gateway[ .]*:\s*([\d.]+)", text)
        return match.group(1) if match and match.group(1) != "0.0.0.0" else None

    proc = await asyncio.create_subprocess_exec(
        "ip", "route", "show", "default", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL
    )
    stdout, _ = await proc.communicate()
    match = re.search(r"default via ([\d.]+)", stdout.decode(errors="ignore"))
    return match.group(1) if match else None
