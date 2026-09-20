import { Gauge, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchLatestSpeedTest, runSpeedTest } from "../api/client";
import type { SpeedTestResult } from "../types";
import { formatRelativeTime } from "../utils/time";

export function SpeedTestCard() {
  const [result, setResult] = useState<SpeedTestResult | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    fetchLatestSpeedTest()
      .then(setResult)
      .finally(() => setLoaded(true));
  }, []);

  const handleRun = async () => {
    setRunning(true);
    setError(null);
    try {
      setResult(await runSpeedTest());
    } catch {
      setError("Speed test failed - check the internet connection on this host.");
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <strong>Internet Speed Test</strong>
        <button className="rescan-btn" disabled={running} onClick={handleRun}>
          <RefreshCw size={14} className={running ? "spin" : ""} />
          {running ? "Testing..." : result ? "Run again" : "Run test"}
        </button>
      </div>

      {error && <div className="finding-remediation" style={{ color: "var(--offline)" }}>{error}</div>}

      {!loaded ? null : running ? (
        <div className="empty-drawer">
          <Gauge size={20} style={{ marginBottom: 6 }} />
          <div>Testing download and upload throughput...</div>
        </div>
      ) : !result ? (
        <div className="empty-drawer">No speed test run yet.</div>
      ) : (
        <>
          <div className="perf-summary">
            <div>
              <div className="perf-value">{result.download_mbps.toFixed(1)} Mbps</div>
              <div className="perf-label">
                <span className="legend-dot download" /> Download
              </div>
            </div>
            <div>
              <div className="perf-value">{result.upload_mbps.toFixed(1)} Mbps</div>
              <div className="perf-label">
                <span className="legend-dot upload" /> Upload
              </div>
            </div>
            <div>
              <div className="perf-value">{result.ping_ms.toFixed(0)} ms</div>
              <div className="perf-label">Ping</div>
            </div>
          </div>
          <div className="finding-detail">
            {result.server_name} · {formatRelativeTime(result.tested_at)}
          </div>
        </>
      )}
    </div>
  );
}
