import { useEffect, useState } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchDeviceMetrics } from "../api/client";
import type { BandwidthSample } from "../hooks/useNetworkState";
import type { MetricRange } from "../types";

const RANGE_OPTIONS: { label: string; value: MetricRange | "live" }[] = [
  { label: "Live", value: "live" },
  { label: "1h", value: "1h" },
  { label: "6h", value: "6h" },
  { label: "24h", value: "24h" },
  { label: "7d", value: "7d" },
];

function formatMbps(bps: number): string {
  return (bps / 1_000_000).toFixed(2);
}

function formatTime(t: number): string {
  return new Date(t).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

async function fetchHistoricalRange(deviceId: number, range: MetricRange): Promise<BandwidthSample[]> {
  const [rx, tx] = await Promise.all([
    fetchDeviceMetrics(deviceId, "rx_bps", range),
    fetchDeviceMetrics(deviceId, "tx_bps", range),
  ]);
  const txByTs = new Map(tx.map((s) => [s.ts, s.value]));
  return rx.map((s) => ({ t: new Date(s.ts + "Z").getTime(), rx_bps: s.value, tx_bps: txByTs.get(s.ts) ?? 0 }));
}

export function PerformanceChart({ deviceId, liveHistory }: { deviceId: number; liveHistory: BandwidthSample[] }) {
  const [range, setRange] = useState<MetricRange | "live">("live");
  const [historical, setHistorical] = useState<BandwidthSample[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (range === "live") return;
    setLoading(true);
    fetchHistoricalRange(deviceId, range)
      .then(setHistorical)
      .finally(() => setLoading(false));
  }, [deviceId, range]);

  const history = range === "live" ? liveHistory : historical;

  return (
    <div>
      <div className="range-selector">
        {RANGE_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            className={`range-btn${range === opt.value ? " active" : ""}`}
            onClick={() => setRange(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="empty-drawer">Loading history...</div>
      ) : history.length < 2 ? (
        <div className="empty-drawer">
          {range === "live"
            ? "No live bandwidth data yet. This device needs SNMP enabled and at least two poll cycles (~20s)."
            : "No bandwidth history recorded for this range yet."}
        </div>
      ) : (
        <>
          <div className="perf-summary">
            <div>
              <div className="perf-value">{formatMbps(history[history.length - 1].rx_bps)} Mbps</div>
              <div className="perf-label">
                <span className="legend-dot download" /> Download
              </div>
            </div>
            <div>
              <div className="perf-value">{formatMbps(history[history.length - 1].tx_bps)} Mbps</div>
              <div className="perf-label">
                <span className="legend-dot upload" /> Upload
              </div>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <AreaChart data={history.map((s) => ({ ...s, time: formatTime(s.t) }))}>
              <defs>
                <linearGradient id="rxGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="txGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" hide />
              <YAxis tickFormatter={(v: number) => formatMbps(v)} width={40} tick={{ fontSize: 10, fill: "#8b97b0" }} />
              <Tooltip
                formatter={(value) => `${formatMbps(Number(value))} Mbps`}
                contentStyle={{ background: "#111a2e", border: "1px solid #1f2b45", fontSize: 12 }}
              />
              <Area type="monotone" dataKey="rx_bps" stroke="#3b82f6" fill="url(#rxGradient)" strokeWidth={2} />
              <Area type="monotone" dataKey="tx_bps" stroke="#22c55e" fill="url(#txGradient)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </>
      )}
    </div>
  );
}
