import {
  Activity,
  AlertTriangle,
  BarChart3,
  Brain,
  CloudRain,
  LogIn,
  ShieldCheck,
  Users,
} from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { fetchDashboard } from "./api";
import type { DashboardSummary, Severity } from "./types";

const fallbackData: DashboardSummary = {
  total_visits: 0,
  total_admissions: 0,
  active_alerts: 0,
  average_wait_minutes: 0,
  top_conditions: [],
  weekly_volume: [],
  environmental_context: [],
  alerts: [],
  insights: [],
};

const severityLabels: Record<Severity, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

export function App() {
  const [dashboard, setDashboard] = useState<DashboardSummary>(fallbackData);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    fetchDashboard()
      .then((data) => {
        setDashboard(data);
        setStatus("ready");
      })
      .catch(() => {
        setStatus("error");
      });
  }, []);

  const maxVolume = useMemo(
    () => Math.max(...dashboard.weekly_volume.map((item) => item.visits), 1),
    [dashboard.weekly_volume]
  );

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Primary navigation">
        <div className="brand">
          <div className="brand-mark">D2A</div>
          <div>
            <strong>Data to Action</strong>
            <span>Health intelligence</span>
          </div>
        </div>
        <nav>
          <button className="nav-item active" title="Dashboard">
            <BarChart3 size={18} />
            <span>Dashboard</span>
          </button>
          <button className="nav-item" title="Alerts">
            <AlertTriangle size={18} />
            <span>Alerts</span>
          </button>
          <button className="nav-item" title="Insights">
            <Brain size={18} />
            <span>Insights</span>
          </button>
          <button className="nav-item" title="Security">
            <ShieldCheck size={18} />
            <span>Privacy</span>
          </button>
        </nav>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <p className="eyebrow">Citizen First operational dashboard</p>
            <h1>D2A Health Early Warning</h1>
          </div>
          <button className="login-button">
            <LogIn size={17} />
            <span>Demo Login</span>
          </button>
        </header>

        {status === "error" && (
          <div className="status-banner">
            Backend is offline. Start FastAPI on port 8000 to load live synthetic data.
          </div>
        )}

        <section className="metrics-grid">
          <MetricCard icon={<Users />} label="Total Visits" value={dashboard.total_visits} />
          <MetricCard icon={<Activity />} label="Admissions" value={dashboard.total_admissions} />
          <MetricCard icon={<AlertTriangle />} label="Active Alerts" value={dashboard.active_alerts} />
          <MetricCard
            icon={<BarChart3 />}
            label="Avg Wait"
            value={`${dashboard.average_wait_minutes}m`}
          />
        </section>

        <section className="dashboard-grid">
          <div className="panel wide">
            <PanelHeader title="Weekly Patient Volume" icon={<BarChart3 size={18} />} />
            <div className="bar-chart">
              {dashboard.weekly_volume.map((item) => (
                <div className="bar-column" key={item.week}>
                  <div
                    className="bar"
                    style={{ height: `${Math.max((item.visits / maxVolume) * 100, 6)}%` }}
                  />
                  <span>{item.week.replace("2026-", "")}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <PanelHeader title="Top Conditions" icon={<Activity size={18} />} />
            <div className="rank-list">
              {dashboard.top_conditions.slice(0, 4).map((item) => (
                <div className="rank-row" key={item.condition}>
                  <span>{item.condition}</span>
                  <strong>{item.visits}</strong>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <PanelHeader title="Environmental Context" icon={<CloudRain size={18} />} />
            <div className="context-list">
              {dashboard.environmental_context.map((item) => (
                <div className="context-row" key={item.district}>
                  <strong>{item.district}</strong>
                  <span>{item.rainfall_mm} mm rain</span>
                  <span>{item.temperature_c.toFixed(1)} C</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel wide">
            <PanelHeader title="Early Warning Alerts" icon={<AlertTriangle size={18} />} />
            <div className="alert-list">
              {dashboard.alerts.map((alert) => (
                <article className={`alert-card ${alert.severity}`} key={alert.id}>
                  <div>
                    <span className="severity">{severityLabels[alert.severity]}</span>
                    <h2>{alert.title}</h2>
                    <p>{alert.message}</p>
                  </div>
                  <strong>{Math.round(alert.confidence * 100)}%</strong>
                </article>
              ))}
            </div>
          </div>

          <div className="panel tall">
            <PanelHeader title="AI Decision Support" icon={<Brain size={18} />} />
            <div className="insight-list">
              {dashboard.insights.map((insight) => (
                <article className="insight-card" key={insight.id}>
                  <span>{insight.category}</span>
                  <h2>{insight.title}</h2>
                  <p>{insight.summary}</p>
                  <ul>
                    {insight.considerations.slice(0, 2).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

function MetricCard({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: number | string;
}) {
  return (
    <article className="metric-card">
      <div className="metric-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}

function PanelHeader({ title, icon }: { title: string; icon: ReactNode }) {
  return (
    <div className="panel-header">
      <h2>{title}</h2>
      {icon}
    </div>
  );
}
