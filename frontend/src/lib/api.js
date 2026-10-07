import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API });

export const fetchers = {
  securities: () => api.get("/market/securities").then((r) => r.data),
  portfolio: () => api.get("/portfolio").then((r) => r.data),
  insights: () => api.get("/market/insights").then((r) => r.data),
  pipelines: () => api.get("/pipelines").then((r) => r.data),
  monitoring: () => api.get("/monitoring").then((r) => r.data),
  valuationHistory: () => api.get("/valuation/history").then((r) => r.data),
  runValuation: (ticker) => api.post("/valuation", { ticker }).then((r) => r.data),
  runPipelines: (force_issue = false) =>
    api.post("/pipelines/run", { force_issue }).then((r) => r.data),
};

export const pdfUrls = {
  valuation: (id) => `${API}/valuation/${id}/pdf`,
  insights: () => `${API}/market/insights/pdf`,
};

export const downloadFile = (url) => {
  const a = document.createElement("a");
  a.href = url;
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
};
