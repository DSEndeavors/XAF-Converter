import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 300000, // 5 min for large file uploads
});

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function getSession(sessionId) {
  const response = await api.get(`/session/${sessionId}`);
  return response.data;
}

export async function fetchPreview(sessionId, dataTypes, { search, page, pageSize } = {}) {
  const response = await api.post("/preview", {
    session_id: sessionId,
    data_types: dataTypes,
    ...(search ? { search } : {}),
    ...(page ? { page } : {}),
    ...(pageSize ? { page_size: pageSize } : {}),
  });
  return response.data;
}

export async function exportData(sessionId, dataTypes, format) {
  const response = await api.post("/export", {
    session_id: sessionId,
    data_types: dataTypes,
    format,
  });
  return response.data;
}

export async function restartSession() {
  const response = await api.post("/restart");
  return response.data;
}

export async function healthCheck() {
  const response = await api.get("/health");
  return response.data;
}

export default api;
