# Security posture scanner — methodology

Network Hunter's security scanner is a **passive, unprivileged network posture
audit** — not an intrusion detection system and not a vulnerability
exploitation tool. It answers one question: *of the devices on this LAN,
which ones are exposing something that's a well-known attack vector, and
what should be done about it?*

## How it works

Every 5 minutes (`SCAN_INTERVAL_SECONDS` in `backend/app/security/engine.py`),
for every device the discovery engine currently sees as online:

1. **Insecure-service scan** (`backend/app/security/scanner.py`) — a plain,
   unprivileged `asyncio.open_connection()` (the same technique the existing
   discovery ping-sweep already uses) against a curated list of ports. A
   connection succeeding means the service is reachable; no packets beyond a
   normal TCP handshake are sent, and no credentials are ever guessed or
   attempted. If the service sends an unsolicited banner (many legacy
   protocols do), the first line is captured for context.
2. **Weak SNMP credential check** (`backend/app/security/snmp_audit.py`) —
   reuses the SNMP community string the discovery engine already probes
   with. If it's a well-known default (`public`, `private`, `community`,
   `cisco`), that's flagged.
3. Each open port is matched against the catalog in
   `backend/app/security/catalog.py`, which carries a severity and
   remediation string per service.
4. **Scoring** (`backend/app/security/scoring.py`) — each device starts at
   100 and loses points per *active, unacknowledged* finding: critical −40,
   high −25, medium −10, low −5, floored at 0. The network-wide score shown
   on the Security page is the average across all known devices.

## Why these specific ports and not others

| Port | Service | Severity | Rationale |
|---|---|---|---|
| 21 | FTP | high | Plaintext credentials and data in transit. |
| 23 | Telnet | critical | Plaintext remote administration, including the login itself. |
| 139 | NetBIOS | medium | Legacy SMB transport; can leak hostnames/shares. |
| 445 | SMB | high | Vector for critical worms (EternalBlue/WannaCry) when unpatched. |
| 512/513/514 | rexec/rlogin/rsh | critical | Unauthenticated or plaintext remote shell access. |
| 1433 | MSSQL | medium | A database reachable from the LAN is worth knowing about. |
| 3306 | MySQL | medium | Same reasoning as MSSQL. |
| 3389 | RDP | high | One of the most common ransomware/brute-force entry points. |
| 5900 | VNC | high | Frequently deployed with weak or no authentication. |
| 6379 | Redis | high | Commonly deployed with no authentication at all. |

**Deliberately excluded:** SSH (22), HTTP/HTTPS (80/443), and common
alternate web ports (8080). These are ubiquitous, legitimate services on
modern networks — flagging them would just be noise, not a finding.

## Known limitations and false positives

- **A finding is exposure, not proof of compromise.** A home server
  intentionally running MySQL or SSH-tunneled RDP is not "hacked" — it's
  just worth knowing what's reachable. Use the **Acknowledge** action on the
  Security page to accept a known, intentional exposure; it's excluded from
  the score but stays visible for the record.
- **No authentication is attempted.** The scanner never tries default
  credentials against any of these services — that would cross from
  auditing into exploitation and isn't something this tool does.
- **Banner grabbing is best-effort.** Many services (RDP, VNC, SMB) require
  a protocol handshake before they'll say anything, so `banner` is often
  `null` — that's expected, not a scan failure.
- **Coverage is LAN-scale and TCP-only.** No UDP services are probed
  (SNMP's own weak-credential check is the exception, since discovery
  already does that walk). This keeps the scanner fast and privilege-free,
  at the cost of not seeing UDP-only exposures.
- **A device that's offline isn't scanned that cycle.** Findings age out via
  `last_seen` rather than disappearing instantly, and resolve automatically
  once a port stops responding on a later scan.
