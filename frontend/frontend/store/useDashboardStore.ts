import { create } from 'zustand';

type Period = 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
type ChartVariable = 'High' | 'Close' | 'Return' | 'Adj Close' | 'Open' | 'Volume' | 'Cumulative Return' | 'Volatility' | 'Dividends' | 'Low';

interface DashboardState {
  // Quantitative State
  quantCompany: string;
  quantPeriod: Period;
  quantVariable: ChartVariable;
  quantRatioCategory: string;
  
  // Qualitative State
  qualCompany: string;
  qualQuarterYear: string; // e.g., "Q3 2023"

  // Actions
  setQuantFilter: (key: keyof DashboardState, value: any) => void;
  setQualFilter: (key: keyof DashboardState, value: any) => void;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  quantCompany: 'Apple Inc.',
  quantPeriod: 'daily',
  quantVariable: 'Close',
  quantRatioCategory: 'Valuation',
  qualCompany: 'Apple Inc.',
  qualQuarterYear: 'Q4_2023',
  
  setQuantFilter: (key, value) => set({ [key]: value }),
  setQualFilter: (key, value) => set({ [key]: value }),
}));