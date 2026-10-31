import {
  DashboardStats,
  HealthStatus,
  ModelStatusResponse,
  PatientInfo,
  ReportDetail,
  User,
  AuthResponse,
  AuditLogItem
} from '../types';

const BACKEND_BASE = (((import.meta as any).env?.VITE_API_URL as string) || '').replace(/\/$/, '');
const API_BASE = BACKEND_BASE ? `${BACKEND_BASE}/api` : '/api';

export function getToken(): string | null {
  return localStorage.getItem('dentalai_token');
}

export function setToken(token: string | null) {
  if (token) {
    localStorage.setItem('dentalai_token', token);
  } else {
    localStorage.removeItem('dentalai_token');
  }
}

export function getAuthHeaders(extraHeaders: Record<string, string> = {}): Record<string, string> {
  const token = getToken();
  const headers: Record<string, string> = { ...extraHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// -------------------------------------------------------------
// Authentication Endpoints
// -------------------------------------------------------------

export async function login(username: string, password: string): Promise<AuthResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Authentication failed');
  }
  const data: AuthResponse = await res.json();
  setToken(data.access_token);
  return data;
}

export async function registerUser(userData: {
  username: string;
  email: string;
  password: string;
  full_name: string;
  role?: string;
}): Promise<User> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(userData)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Registration failed');
  }
  return res.json();
}

export async function getCurrentUser(): Promise<User | null> {
  const token = getToken();
  if (!token) return null;
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) {
      setToken(null);
      return null;
    }
    return res.json();
  } catch {
    return null;
  }
}

export async function logout(): Promise<void> {
  const token = getToken();
  if (token) {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: getAuthHeaders()
      });
    } catch {}
  }
  setToken(null);
}

export async function getAuditLogs(limit: number = 50): Promise<AuditLogItem[]> {
  const res = await fetch(`${API_BASE}/auth/audit-logs?limit=${limit}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    throw new Error('Failed to retrieve security audit logs. Admin authorization required.');
  }
  return res.json();
}

// -------------------------------------------------------------
// Health, Model Status, and Dashboard Metrics
// -------------------------------------------------------------

export async function getHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function getModelStatus(): Promise<ModelStatusResponse> {
  const res = await fetch(`${API_BASE}/dental/model-status`);
  if (!res.ok) {
    throw new Error(`Failed to load model status: ${res.statusText}`);
  }
  return res.json();
}

export async function getDashboardStats(): Promise<DashboardStats> {
  const res = await fetch(`${API_BASE}/dental/stats`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    const fallback = await fetch(`${API_BASE}/stats`, { headers: getAuthHeaders() });
    if (!fallback.ok) throw new Error("Failed to load dashboard metrics");
    return fallback.json();
  }
  return res.json();
}

// -------------------------------------------------------------
// Patient Management Endpoints
// -------------------------------------------------------------

export async function getPatients(search?: string): Promise<PatientInfo[]> {
  const url = search ? `${API_BASE}/dental/patients?search=${encodeURIComponent(search)}` : `${API_BASE}/dental/patients`;
  const res = await fetch(url, { headers: getAuthHeaders() });
  if (!res.ok) {
    const fallbackUrl = search ? `${API_BASE}/patients?search=${encodeURIComponent(search)}` : `${API_BASE}/patients`;
    const fallback = await fetch(fallbackUrl, { headers: getAuthHeaders() });
    if (!fallback.ok) throw new Error("Failed to load patients list");
    return fallback.json();
  }
  return res.json();
}

export async function createPatient(patientData: Partial<PatientInfo>): Promise<PatientInfo> {
  const res = await fetch(`${API_BASE}/dental/patients`, {
    method: 'POST',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(patientData)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to register patient");
  }
  return res.json();
}

export async function updatePatient(patientId: string, patientData: Partial<PatientInfo>): Promise<PatientInfo> {
  const res = await fetch(`${API_BASE}/dental/patients/${encodeURIComponent(patientId)}`, {
    method: 'PUT',
    headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(patientData)
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to update patient information");
  }
  return res.json();
}

export async function deletePatient(patientId: string): Promise<{ status: string; message: string }> {
  const res = await fetch(`${API_BASE}/dental/patients/${encodeURIComponent(patientId)}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Failed to delete patient record");
  }
  return res.json();
}

// -------------------------------------------------------------
// Patient History & Report Endpoints
// -------------------------------------------------------------

export async function getPatientHistory(patientId: string): Promise<{
  patient: PatientInfo;
  scans_count: number;
  history: Array<{
    analysis_id: string;
    report_id: string;
    overall_status: string;
    urgency_level: string;
    summary: string;
    created_at: string;
    findings: Array<{
      disease_name: string;
      severity: string;
      confidence_percentage: number;
      affected_views: string[];
    }>;
  }>;
}> {
  const res = await fetch(`${API_BASE}/dental/patients/${encodeURIComponent(patientId)}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    const fallback = await fetch(`${API_BASE}/patients/${encodeURIComponent(patientId)}`, {
      headers: getAuthHeaders()
    });
    if (!fallback.ok) throw new Error("Failed to load patient history");
    return fallback.json();
  }
  return res.json();
}

export async function getReport(reportId: string): Promise<ReportDetail> {
  const res = await fetch(`${API_BASE}/dental/reports/${encodeURIComponent(reportId)}`, {
    headers: getAuthHeaders()
  });
  if (!res.ok) {
    const fallback = await fetch(`${API_BASE}/reports/${encodeURIComponent(reportId)}`, {
      headers: getAuthHeaders()
    });
    if (!fallback.ok) throw new Error(`Failed to load report '${reportId}'`);
    return fallback.json();
  }
  return res.json();
}

export function getReportPdfUrl(reportId: string): string {
  const token = getToken();
  return token
    ? `${API_BASE}/dental/reports/${encodeURIComponent(reportId)}/pdf?token=${encodeURIComponent(token)}`
    : `${API_BASE}/dental/reports/${encodeURIComponent(reportId)}/pdf`;
}

export async function downloadReportPdf(reportId: string): Promise<void> {
  const url = `${API_BASE}/dental/reports/${encodeURIComponent(reportId)}/pdf`;
  const response = await fetch(url, { headers: getAuthHeaders() });
  if (!response.ok) {
    throw new Error(`Failed to download PDF report (${response.status}: ${response.statusText})`);
  }
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = `DentalAI_Report_${reportId}.pdf`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(downloadUrl);
}

export async function analyzeDentalImages(
  formData: FormData,
  onProgress?: (percent: number) => void
): Promise<ReportDetail> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}/dental/analyze-multiple`);

    const token = getToken();
    if (token) {
      xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    }

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          const report = JSON.parse(xhr.responseText) as ReportDetail;
          resolve(report);
        } catch (e) {
          reject(new Error("Failed to parse server response as JSON."));
        }
      } else {
        try {
          const errData = JSON.parse(xhr.responseText);
          reject(new Error(errData.detail || `Analysis request failed with HTTP ${xhr.status}`));
        } catch {
          reject(new Error(`Server returned error ${xhr.status}: ${xhr.statusText}`));
        }
      }
    };

    xhr.onerror = () => {
      reject(new Error("Network connection error. Is the backend server running?"));
    };

    xhr.send(formData);
  });
}

export function getUploadUrl(filename?: string | null): string {
  if (!filename) return '';
  const token = getToken();
  const base = BACKEND_BASE ? `${BACKEND_BASE}/uploads` : '/uploads';
  if (filename.startsWith('sample_') || !token) {
    return `${base}/${encodeURIComponent(filename)}`;
  }
  return `${base}/${encodeURIComponent(filename)}?token=${encodeURIComponent(token)}`;
}
