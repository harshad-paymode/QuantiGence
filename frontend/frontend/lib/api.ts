// lib/api.ts
import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// Helper function to pause execution
const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

// Universal Polling Function
const pollTaskResult = async (taskId: string) => {
  let attempts = 0;
  const maxAttempts = 180; // Allow up to 3 minutes for complex AI analysis
  while (attempts < maxAttempts) { // Timeout after ~180 seconds
    const { data } = await apiClient.get(`/api/task-status/${taskId}`);
    
    if (data.status === "completed") {
      return data.data;
    } else if (data.status === "failed") {
      throw new Error(`Task failed: ${data.error}`);
    }
    
    // If still 'processing', wait 1 second and try again
    await delay(1000);
    attempts++;
  }
  throw new Error("Request timed out waiting for backend task.");
};

// ---- Charts ----
export const getCharts = async (
  company: string,
  timeframe: string,
  variables: string[]
) => {
  const params = new URLSearchParams();
  params.append("company", company);
  params.append("timeframe", timeframe);
  variables.forEach((v) => params.append("variables", v));

  const { data } = await apiClient.get(`/api/charts?${params.toString()}`);
  return pollTaskResult(data.task_id);
};

// ---- Ratios ----
export const getRatios = async (
  company: string,
  variables: string[],
  timeframe: string
) => {
  const params = new URLSearchParams();
  params.append("company", company);
  params.append("timeframe", timeframe);
  variables.forEach((v) => params.append("variables", v));

  const { data } = await apiClient.get(`/api/ratios?${params.toString()}`);
  return pollTaskResult(data.task_id);
};

// ---- Risk Matrix ----
export const getRiskMatrix = async (
  company: string,
  period: string,
  timeframe: string,
  top_n: number
) => {
  const params = new URLSearchParams();
  params.append("company", company);
  params.append("period", period);
  params.append("timeframe", timeframe);
  params.append("top_n", String(top_n));

  const { data } = await apiClient.get(`/api/risk_matrix?${params.toString()}`);
  return pollTaskResult(data.task_id);
};

// ---- Performance ----
export const getPerformance = async (
  company: string,
  period: string,
  timeframe: string
) => {
  const params = new URLSearchParams();
  params.append("company", company);
  params.append("period", period);
  params.append("timeframe", timeframe);

  const { data } = await apiClient.get(`/api/performance?${params.toString()}`);
  return pollTaskResult(data.task_id);
};

// ----- AI ASSISTANT -----
export const getQualitativeAnalysis = async (
  company: string,
  period: string,
  query: string
) => {
  const { data } = await apiClient.post('/api/qualitative', {
    company,
    period,
    query
  });
  return pollTaskResult(data.task_id); 
};