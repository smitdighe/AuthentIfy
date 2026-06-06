import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

const TOKEN_KEY = 'authentify_token';
const REFRESH_TOKEN_KEY = 'authentify_refresh_token';

// ─── Axios Instance ─────────────────────────────────────────────────────────

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Request Interceptor ────────────────────────────────────────────────────

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ─── Response Interceptor ───────────────────────────────────────────────────

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response && error.response.status === 401) {
      clearTokens();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ─── Token Helpers ──────────────────────────────────────────────────────────

/**
 * Persist access and refresh tokens to localStorage.
 * @param {string} access  - JWT access token.
 * @param {string} refresh - JWT refresh token.
 */
export function setTokens(access, refresh) {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
}

/**
 * Retrieve the stored access token.
 * @returns {string|null} The access token or null.
 */
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * Retrieve the stored refresh token.
 * @returns {string|null} The refresh token or null.
 */
export function getRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Remove both tokens from localStorage.
 */
export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

// ─── Auth Endpoints ─────────────────────────────────────────────────────────

/**
 * Register a new user account.
 * @param {string} email    - User email address.
 * @param {string} password - User password.
 * @param {string} fullName - User full name.
 * @returns {Promise<object>} Registration response data.
 */
export async function registerUser(email, password, fullName) {
  try {
    const data = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return data;
  } catch (error) {
    throw new Error(
      error.response?.data?.message || 'Registration failed. Please try again.'
    );
  }
}

/**
 * Authenticate user and receive tokens.
 * @param {string} email    - User email address.
 * @param {string} password - User password.
 * @returns {Promise<object>} Login response with access and refresh tokens.
 */
export async function loginUser(email, password) {
  try {
    const data = await api.post('/auth/login', { email, password });
    return data;
  } catch (error) {
    throw new Error(
      error.response?.data?.message || 'Login failed. Check your credentials.'
    );
  }
}

/**
 * Log out the current user and invalidate the token.
 * @returns {Promise<object>} Logout confirmation.
 */
export async function logoutUser() {
  try {
    const data = await api.post('/auth/logout');
    clearTokens();
    return data;
  } catch (error) {
    clearTokens();
    throw new Error(
      error.response?.data?.message || 'Logout failed.'
    );
  }
}

/**
 * Refresh the access token using the stored refresh token.
 * @returns {Promise<object>} New access token data.
 */
export async function refreshToken() {
  try {
    const refresh = getRefreshToken();
    const data = await api.post('/auth/refresh', null, {
      headers: { Authorization: `Bearer ${refresh}` },
    });
    return data;
  } catch (error) {
    clearTokens();
    throw new Error(
      error.response?.data?.message || 'Session expired. Please log in again.'
    );
  }
}

/**
 * Fetch the currently authenticated user's profile.
 * @returns {Promise<object>} User profile data.
 */
export async function getCurrentUser() {
  try {
    const data = await api.get('/auth/me');
    return data;
  } catch (error) {
    throw new Error(
      error.response?.data?.message || 'Failed to fetch user profile.'
    );
  }
}

// ─── Analysis Endpoint ──────────────────────────────────────────────────────

/**
 * Upload a PDF file for tamper analysis.
 * @param {File}        file  - The PDF File object to analyze.
 * @param {string|null} token - Optional access token override.
 * @returns {Promise<object>} Full analysis result.
 */
export async function analyzeDocument(file, token = null) {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: { 'Content-Type': 'multipart/form-data' },
    };

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    const data = await api.post('/analyze', formData, config);
    return data;
  } catch (error) {
    throw new Error(
      error.response?.data?.message || 'Document analysis failed.'
    );
  }
}

// ─── Report Endpoints ───────────────────────────────────────────────────────

/**
 * Retrieve a public analysis report by ID.
 * @param {string} reportId - The report identifier.
 * @returns {Promise<object>} Report data.
 */
export async function getReportById(reportId) {
  try {
    const data = await api.get(`/report/${reportId}`);
    return data;
  } catch (error) {
    throw new Error(
      error.response?.data?.message || 'Failed to fetch report.'
    );
  }
}

/**
 * Fetch paginated report history for the authenticated user.
 * @param {number} page  - Page number (default 1).
 * @param {number} limit - Items per page (default 10).
 * @returns {Promise<object>} Paginated report history.
 */
export async function getReportHistory(page = 1, limit = 10) {
  try {
    const data = await api.get('/report/history', {
      params: { page, limit },
    });
    return data;
  } catch (error) {
    throw new Error(
      error.response?.data?.message || 'Failed to fetch report history.'
    );
  }
}

/**
 * Fetch aggregate analysis statistics for the authenticated user.
 * @returns {Promise<object>} User analysis stats.
 */
export async function getReportStats() {
  try {
    const data = await api.get('/report/stats');
    return data;
  } catch (error) {
    throw new Error(
      error.response?.data?.message || 'Failed to fetch report stats.'
    );
  }
}

/**
 * Delete a specific report by UUID.
 * @param {string} reportUuid - The report UUID to delete.
 * @returns {Promise<object>} Deletion confirmation.
 */
export async function deleteReport(reportUuid) {
  try {
    const data = await api.delete(`/report/history/${reportUuid}`);
    return data;
  } catch (error) {
    throw new Error(
      error.response?.data?.message || 'Failed to delete report.'
    );
  }
}

// ─── Health Endpoint ────────────────────────────────────────────────────────

/**
 * Check backend service health.
 * @returns {Promise<object>} Health status.
 */
export async function checkHealth() {
  try {
    const data = await api.get('/health');
    return data;
  } catch (error) {
    throw new Error(
      error.response?.data?.message || 'Health check failed. Server may be down.'
    );
  }
}

export default api;
