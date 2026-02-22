// lib/api.ts
import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

// ---- Charts (unchanged logic) ----
export const getCharts = async (
  company: string,
  timeframe: string,
  variables: string[]
) => {
  const params = new URLSearchParams();
  params.append("company", company);
  params.append("timeframe", timeframe);
  variables.forEach((v) => params.append("variables", v));

  const { data } = await apiClient.get(
    `/api/charts?${params.toString()}`
  );

  return data;
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

  const { data } = await apiClient.get(
    `/api/ratios?${params.toString()}`
  );

  return data;
};

// ---- Risk Matrix ----
export const getRiskMatrix = async (
  company:string,
  period: string,
  timeframe: string,
  top_n: number
) => {
  const params = new URLSearchParams();
  params.append("company",company);
  params.append("period", period);
  params.append("timeframe", timeframe);
  params.append("top_n", String(top_n));

  const { data } = await apiClient.get(
    `/api/risk_matrix?${params.toString()}`
  );

  return data;
};

// ---- Performance ----
export const getPerformance = async (
  company: string,
  period: string,
  timeframe: string
) => {
  const params = new URLSearchParams();
  params.append("company",company)
  params.append("period", period);
  params.append("timeframe", timeframe);

  const { data } = await apiClient.get(
    `/api/performance?${params.toString()}`
  );

  return data;
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
  return data; // Expected: { final_response: string, faithfulness: number, relevancy: number }
};