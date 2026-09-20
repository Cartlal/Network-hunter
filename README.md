# Network Hunter

A live network discovery and **security posture monitor** for your LAN.
Network Hunter finds every device on your network the moment it connects,
maps how it's physically wired in, watches its health, and — the core of the
project — continuously audits every device for insecure exposed services and
weak SNMP credentials, scoring your network's overall security posture.

No agents to install, no admin/root privileges, no packet capture. Just a
ping sweep, the OS ARP cache, mDNS, optional SNMP, and plain unprivileged TCP
connects.

> **This tool has no login and no access control by design.** It's built to
> run on a trusted LAN or on localhost. Never expose it to the internet or an
> untrusted network — anyone who can reach its port can see everything it
> knows about your network, including its security findings.

## What it does

- **Security posture scanner (headline feature)** — every 5 minutes, audits
  every known device for legacy/high-risk exposed services (Telnet, FTP,
  SMB, RDP, VNC, exposed databases, etc.) and SNMP answering on a default
  community string. Each device gets a 0–100 security score with concrete
  remediation guidance; findings can be acknowledged as accepted risk. See
  [SECURITY_METHODOLOGY.md](SECURITY_METHODOLOGY.md) for exactly what's
  checked and why.
- **Live topology** — automatic device discovery (ARP/ping/mDNS), physical
  link inference via LLDP/CDP when a managed switch is present, real-time
  updates over a websocket, and a manual **Refresh** button to force an
  immediate rescan instead of waiting for the next cycle.
- **Internet speed test** — on-demand download/upload throughput and ping
  test from the Dashboard, backed by speedtest.net's public infrastructure;
  results are saved so you can see how the connection trends over time.
- **Device & port monitoring** — SNMP-based interface stats, bandwidth
  history, latency tracking.
- **Alerting** — device-down, high-latency, and high-bandwidth-utilization
  alerts, with optional email delivery.
- **Dashboard, maps, reports, and activity/alert history** for day-to-day
  network visibility.

## Quick start

See [SETUP.md](SETUP.md) for prerequisites, running the backend/frontend in
development, environment variables, and the production single-process build.

```bash
cd backend && pip install -e . && uvicorn app.main:app
cd frontend && npm install && npm run dev
```

Open http://localhost:5173 — it opens straight into the Security dashboard,
no login required.

## How it's built

- **Backend**: FastAPI + SQLAlchemy (async), SQLite by default (optional
  Postgres/TimescaleDB for longer metric retention).
- **Frontend**: React + TypeScript + Vite, `@xyflow/react` for the topology
  graph, `recharts` for performance charts.
- **Discovery**: ping sweep + OS ARP cache + mDNS (no elevated privileges,
  no Npcap); SNMP (`pysnmp`) for switches/routers that support it; LLDP/CDP
  walks for physical link inference.
- **Security scanner**: `backend/app/security/` — unprivileged TCP connects
  against a curated risky-service catalog, plus an SNMP weak-credential
  check. See the methodology doc above.

## Project layout

```
backend/app/
  discovery/   ping sweep, ARP, mDNS, SNMP, LLDP/CDP, the scan scheduler
  security/    the posture scanner: catalog, scanner, scoring, engine
  alerts/      device-down / latency / bandwidth alert rules + notifier
  api/         FastAPI routers (one per resource)
  models.py    SQLAlchemy models
frontend/src/
  pages/       one component per sidebar page (Security, Topology, ...)
  components/  shared UI (Sidebar, TopBar, DeviceDrawer, charts, ...)
  hooks/       useNetworkState (data + websocket) , useTopologySocket
```

## Testing

```bash
cd backend && pip install -e ".[dev]" && pytest
```

Currently covers the security scoring/catalog logic (pure functions, no
network I/O) — see `backend/tests/`.

## License

MIT — see [LICENSE](LICENSE).
