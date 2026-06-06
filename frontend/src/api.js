const API =
  import.meta.env?.VITE_API_URL ||
  (typeof process !== "undefined" && process.env?.REACT_APP_API_URL) ||
  "http://localhost:5000";

/**
 * Upload a PDF for forensic analysis.
 * @param {File}   file   - The PDF file to analyze
 * @param {string} [token]  - Optional JWT for authenticated uploads
 * @returns {Promise<object>} Analysis result from backend
 */
export async function analyzeDocument(file, token) {
  const formData = new FormData();
  formData.append("file", file);

  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API}/api/analyze`, {
    method: "POST",
    headers,
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Analysis failed");
  return data;
}

/**
 * Fetch paginated report history for the logged-in user.
 */
export async function fetchReports(token, page = 1) {
  const res = await fetch(`${API}/api/reports?page=${page}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to load reports");
  return data;
}

/**
 * Fetch a single report by UUID.
 */
export async function fetchReport(uuid, token) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API}/api/reports/${uuid}`, { headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Report not found");
  return data;
}

/**
 * Delete a report by UUID.
 */
export async function deleteReport(uuid, token) {
  const res = await fetch(`${API}/api/reports/${uuid}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Delete failed");
  return data;
}

/**
 * Fetch dashboard stats for the logged-in user.
 */
export async function fetchDashboardStats(token) {
  const res = await fetch(`${API}/api/dashboard/stats`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Failed to load stats");
  return data;
}
