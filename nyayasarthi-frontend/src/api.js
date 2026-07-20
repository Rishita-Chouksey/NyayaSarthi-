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

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
});

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
