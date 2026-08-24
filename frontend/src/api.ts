import type { DashboardSummary } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchDashboard(): Promise<DashboardSummary> {
  const response = await fetch(`${API_BASE_URL}/api/dashboard`);

  if (!response.ok) {
    throw new Error("Unable to load dashboard data");
  }

  return response.json();
}
