import type { Alert, AuthResponse, DashboardSummary, IngestionResult, Insight, PatientRecord, SignupResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

function userHeaders(): HeadersInit {
  const user = JSON.parse(localStorage.getItem("d2a_user") || "null") as { email?: string } | null;
  return user?.email ? { "X-User-Email": user.email } : {};
}

export async function fetchDashboard(): Promise<DashboardSummary> {
  const response = await fetch(`${API_BASE_URL}/api/dashboard`, { headers: userHeaders() });

  if (!response.ok) {
    throw new Error("Unable to load dashboard data");
  }

  return response.json();
}

export async function fetchHealth(): Promise<{ status: string }> {
  return parseResponse(fetch(`${API_BASE_URL}/health`));
}

async function parseResponse<T>(responsePromise: Promise<Response>): Promise<T> {
  const response = await responsePromise;
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? "Request failed");
  }
  return response.json();
}

export async function fetchAlerts(): Promise<Alert[]> {
  return parseResponse(fetch(`${API_BASE_URL}/api/alerts`, { headers: userHeaders() }));
}

export async function fetchInsights(): Promise<Insight[]> {
  return parseResponse(fetch(`${API_BASE_URL}/api/insights`, { headers: userHeaders() }));
}

export async function fetchRecords(): Promise<PatientRecord[]> {
  return parseResponse(fetch(`${API_BASE_URL}/api/records`, { headers: userHeaders() }));
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  return parseResponse(
    fetch(`${API_BASE_URL}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    })
  );
}

export async function signup(name: string, email: string, password: string, healthCenter: string): Promise<SignupResponse & Partial<AuthResponse>> {
  return parseResponse(
    fetch(`${API_BASE_URL}/api/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password, health_center: healthCenter }),
    })
  );
}

export async function verifyEmail(email: string, code: string): Promise<{ message: string }> {
  return parseResponse(
    fetch(`${API_BASE_URL}/api/auth/verify-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code }),
    })
  );
}

export async function requestPasswordReset(email: string): Promise<{ message: string; development_code?: string }> {
  return parseResponse(
    fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    })
  );
}

export async function resetPassword(email: string, code: string, newPassword: string): Promise<{ message: string }> {
  return parseResponse(
    fetch(`${API_BASE_URL}/api/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, code, new_password: newPassword }),
    })
  );
}

export async function uploadPatientCsv(file: File, userEmail?: string): Promise<IngestionResult> {
  const formData = new FormData();
  formData.append("file", file);
  return parseResponse(
    fetch(`${API_BASE_URL}/api/ingestion/patient-csv`, {
      method: "POST",
      headers: userEmail ? { "X-User-Email": userEmail } : undefined,
      body: formData,
    })
  );
}

export async function appendPatientCsv(file: File, userEmail?: string): Promise<IngestionResult> {
  const formData = new FormData();
  formData.append("file", file);
  return parseResponse(
    fetch(`${API_BASE_URL}/api/ingestion/patient-csv/append`, {
      method: "POST",
      headers: userEmail ? { "X-User-Email": userEmail } : undefined,
      body: formData,
    })
  );
}
