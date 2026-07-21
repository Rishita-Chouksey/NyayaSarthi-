/**
 * Every call to the real backend goes through this one file.
 *
 * The backend URL comes from an environment variable (VITE_API_URL) so the
 * exact same code works locally and once deployed — you never edit this file
 * again, you just set VITE_API_URL differently in each environment:
 *   - Locally: .env file with VITE_API_URL=http://localhost:8000/api/v1
 *   - Deployed: set VITE_API_URL in your hosting provider's dashboard
 *     (e.g. https://nyayasarthi-backend.onrender.com/api/v1)
 */
import axios from "axios";

// The key both AuthContext and this interceptor read/write the session under.
// Centralized here so there's exactly one source of truth for the token.
export const TOKEN_KEY = "nyayasarthi_token";
export const USER_KEY = "nyayasarthi_user";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
});

// Attach the officer's session token to every request automatically, so the
// rest of the app never has to think about auth headers.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// If the backend ever says the session is invalid/expired (401), clear it
// locally and reload — App.jsx will then show the login screen again.
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      window.location.reload();
    }
    return Promise.reject(err);
  }
);

export const login = (email, password) => api.post("/auth/login", { email, password });
export const signup = (payload) => api.post("/auth/signup", payload);
export const googleAuth = (credential) => api.post("/auth/google", { credential });
export const getMe = () => api.get("/auth/me");

export const uploadJudgment = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/cases/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const listCases = (status) => api.get("/cases", { params: status ? { status } : {} });
export const getCase = (caseId) => api.get(`/cases/${caseId}`);

export const approveDirective = (directiveId) => api.post(`/verification/${directiveId}/approve`);
export const editApproveDirective = (directiveId, edits) => api.post(`/verification/${directiveId}/edit-approve`, edits);
export const rejectDirective = (directiveId, reason) => api.post(`/verification/${directiveId}/reject`, { reason });

export const listActions = (params) => api.get("/actions", { params });
export const updateActionStatus = (actionId, status, notes) => api.patch(`/actions/${actionId}/status`, { status, notes });
export const dashboardStats = () => api.get("/actions/dashboard/stats");

export const listDepartments = () => api.get("/departments");

export const getAuditHistory = (entityType, entityId) => api.get(`/audit/${entityType}/${entityId}`);

export default api;
