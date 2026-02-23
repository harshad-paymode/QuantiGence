import { create } from 'zustand';

type Period = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
type ChartVariable = 'High' | 'Close' | 'Return' | 'Adj Close' | 'Open' | 'Volume' | 'Cumulative Return' | 'Volatility' | 'Dividends' | 'Low';

interface DashboardState {
  quantCompany: string;
  quantPeriod: Period;
  quantVariable: ChartVariable[];         // <- array now
  quantRatioCategory: string;
  qualCompany: string;
  qualQuarterYear: string;
  qualQuery: string;
  qualResponse: {
    text: string;
    faithfulness: number;
    relevancy: number;
  } | null;
  isAnalyzing: boolean;
  setQuantFilter: (key: keyof DashboardState, value: any) => void;
  setQualFilter: (key: keyof DashboardState, value: any) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  quantCompany: 'AAPL',
  quantPeriod: 'quarterly',               // <- match your parquet timeframe
  quantVariable: ['Close'],               // <- default as array
  quantRatioCategory: 'Valuation',
  qualCompany: 'AAPL',
  qualQuarterYear: 'Q3_2024',
  qualQuery: "",
  qualResponse: null,
  isAnalyzing: false,
  setQuantFilter: (key, value) => set({ [key]: value }),
  setQualFilter: (key, value) => set({ [key]: value }),
}));