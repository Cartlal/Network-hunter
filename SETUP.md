# NetMap Live — Setup

Real network discovery and monitoring: live topology, SNMP polling, LLDP/CDP
physical links, alerts/history, and a passive network security posture
scanner (insecure exposed services, weak SNMP credentials).

> **This tool has no login and no access control.** It's built to run on a
> trusted LAN or localhost only. Never expose it to the internet or an
> untrusted network — anyone who can reach its port can see everything it
> discovers about your network, including its security findings.

## Prerequisites

- Python 3.11+
- Node.js 18+
- No admin/elevation required, no Npcap install needed — discovery uses a
  ping sweep + the OS ARP cache + mDNS, none of which need raw sockets on
  Windows.
- (Optional) Docker Desktop, only if you want Postgres+TimescaleDB instead
  of the default SQLite file for metric history.

## Running in development

Two processes, each in its own terminal:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -e .
uvicorn app.main:app
```

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the app opens straight into the dashboard, no
login.

## Environment variables (backend)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | local SQLite file | Set to a Postgres DSN to use TimescaleDB (see below) |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` / `ALERT_EMAIL_TO` | unset | Optional: email delivery for critical alerts. Alerts still show in-app either way. |

## Security posture scanner

Every 5 minutes, the backend probes each known device for a curated list of
legacy/high-risk services (Telnet, FTP, SMB, RDP, VNC, exposed databases,
etc.) using plain unprivileged TCP connects, and checks whether SNMP is
answering on a default community string. Findings, per-device security
scores, and remediation guidance show up on the **Security** page. See
`SECURITY_METHODOLOGY.md` for what's checked and why.

## Using Postgres + TimescaleDB instead of SQLite

SQLite is fine for normal use. Switch to Postgres if you want longer
retention / faster range queries on bandwidth and latency history:

```bash
docker compose up -d db
```

Then set before starting the backend:

```bash
export DATABASE_URL=postgresql+asyncpg://netmap:netmap@localhost:5432/netmap
pip install -e ".[postgres]"
```

The backend detects Postgres automatically and converts `metric_samples`
into a TimescaleDB hypertable on startup (falls back to a plain table with
a log warning if the extension isn't available).

## Don't use `uvicorn --reload` on Windows

Discovery depends on `asyncio.create_subprocess_exec` (`ipconfig`, `arp -a`).
Uvicorn's `--reload` supervisor runs the actual server in a worker process
that forces Windows onto `SelectorEventLoop`, which doesn't support
subprocesses at all — every scan cycle fails with `NotImplementedError`.
Plain `uvicorn app.main:app` (no `--reload`) uses `ProactorEventLoop` and
works correctly. If you want auto-restart on code changes during
development, use an external watcher that restarts the plain command
(e.g. `watchfiles "uvicorn app.main:app" app`) rather than uvicorn's
built-in `--reload`.

## Production build (single process)

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The backend serves the built frontend directly once `frontend/dist`
exists, so only port 8000 needs to be exposed.

**Run the backend natively, not in a container.** Docker Desktop on
Windows puts containers behind NAT, which hides them from the real LAN and
breaks ARP/ICMP-based discovery entirely. Only the database is
containerized in `docker-compose.yml` — the backend/frontend should run
directly on the host. On Linux, running the backend in a container with
`--network host` does work if you need that.

## Known limitations (by design, not bugs)

- **SNMP coverage is partial.** Consumer PCs, phones, and most budget
  routers/switches don't support SNMP at all. Devices that don't respond
  are shown with discovery-only data — this is expected, not an error.
  Enable SNMP on a managed switch or an SNMP-capable router and add its
  community string in Settings to see port/bandwidth data for it.
- **Physical topology (LLDP/CDP) needs at least one managed switch.**
  Without one, all devices show as a star from the gateway, which is a
  reasonable default rather than a guess that happens to be wrong.
- **Hostname resolution** tries reverse DNS, then mDNS, in that order.
  Devices that don't answer either (many IoT gadgets, or phones with
  private/random MAC + mDNS disabled) show only their IP — there's no
  further fallback that would be reliable across vendors.
