"use client";

import { useState, useRef, useEffect } from "react";
import { 
  ResizableHandle, 
  ResizablePanel, 
  ResizablePanelGroup 
} from "@/components/ui/resizable";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Maximize2, Minimize2, BrainCircuit, Activity, BarChart3, Send, Check } from "lucide-react"; 

// Import State Management & API
import { useDashboardStore } from '@/store/useDashboardStore';
// ADDED getQualitativeAnalysis to imports
import { getCharts, getRatios, getPerformance, getRiskMatrix, getQualitativeAnalysis } from '@/lib/api';
import QuantitativeChart from '@/components/ui/QuantitativeChart';

const companies = [
  "AAPL", "MSFT", "GOOGL", "AMZN",
  "META", "NVDA", "TSLA", "ORCL",
  "CRM", "NFLX", "ADBE"
];

const ratioGroups = {
  "Valuation": ["Price-to-Earnings", "Price-to-Book", "EV-to-EBITDA", "EV-to-Sales", "Price-to-Free-Cash-Flow"],
  "Profitability": ["Gross Margin", "Operating Margin", "Net Profit Margin", "Return on Equity"],
  "Liquidity": ["Current Ratio", "Quick Ratio", "Cash Ratio"],
  "Efficiency": ["Asset Turnover Ratio", "Inventory Turnover Ratio"],
  "Leverage": ["Debt-to-Equity Ratio", "Debt-to-Assets Ratio"],
  "Cash Flow": ["Cash Conversion Efficiency", "CAPEX Coverage Ratio"]
};

const performanceMetrics = [
  "Beta", "CAPM", "Alpha", "Sharpe Ratio", "Sortino Ratio", 
  "Tracking Error", "Treynor Ratio"
];


const years = ["2023", "2022", "2021", "2020"];
const periodYears = ["2024", "2025"];
const periodQuarters = ["Q1_2024", "Q2_2024", "Q3_2024", "Q1_2025", "Q2_2025", "Q3_2025"];
const periodQuartersQuant = ["Q1_2024", "Q2_2024", "Q3_2024","Q4_2024", "Q1_2025", "Q2_2025", "Q3_2025", "Q4_2025"];


type ExpandedWidget = "all" | "tabs" | "risk" | "metrics";

export default function Home() {
  // DESTRUCTURED NEW FIELDS FROM STORE
  const { 
    quantCompany, quantVariable, quantPeriod, setQuantFilter,
    qualCompany, qualQuarterYear, setQualFilter,
    qualQuery, qualResponse, isAnalyzing 
  } = useDashboardStore();
  
  
  const [selectedCategory, setSelectedCategory] = useState<keyof typeof ratioGroups>("Valuation");
  const [expandedWidget, setExpandedWidget] = useState<ExpandedWidget>("all");
  const [chatInput, setChatInput] = useState("");
  const [ragResponse, setRagResponse] = useState<any>(null);
  const [isSplitSynced, setIsSplitSynced] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const [qualPeriodType, setQualPeriodType] = useState<"quarterly" | "yearly">("quarterly");
  const [riskPeriodType, setRiskPeriodType] = useState<"quarterly" | "yearly">("quarterly");
  
  // NEW STATE: Chart Data and Loading
  const [chartData, setChartData] = useState<any[]>([]);
  const [isChartLoading, setIsChartLoading] = useState(false);
  // page.tsx (inside component, with other useState calls)
  const [ratioPeriod, setRatioPeriod] = useState<'Quarterly' | 'Yearly'>('Quarterly');

    // --- Data pulled from backend for Quantitative widgets ---
  const [ratioData, setRatioData] = useState<any[]>([]); // returned by /api/ratios: array of {metric, date1: val, ...}
  const [perfMap, setPerfMap] = useState<Record<string, number | null>>({}); // returned by /api/performance
  const [riskMatrix, setRiskMatrix] = useState<{metrics: string[]; tickers: string[]; matrix: (number | null)[][]}>({
    metrics: [], tickers: [], matrix: []
  });

  // inside your component in page.tsx — replace the existing effect that fetches ratios
  useEffect(() => {
    async function fetchCategoryRatios() {
      try {
        // ratioGroups[selectedCategory] should be an array of metric names.
        // Defensively coerce to array:
        const vars = Array.isArray(ratioGroups[selectedCategory]) ? ratioGroups[selectedCategory] : [];

        // timeframe expected by backend is lowercase ('quarterly'|'yearly')
        const timeframe = (ratioPeriod || "Quarterly").toLowerCase();

        // if no variables, still call backend (it will return everything or nothing depending on backend)
        const data = await getRatios(quantCompany, vars, timeframe);
        setRatioData(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Failed fetching category ratios:", err);
        setRatioData([]);
      }
    }

    if (quantCompany && selectedCategory) {
      fetchCategoryRatios();
    }
  }, [quantCompany, selectedCategory, ratioPeriod, /* getRatios not in deps if defined outside */]);

  // fetch performance mapping for selected analysis period (qualQuarterYear)
  useEffect(() => {
    async function fetchPerf() {
      try {
        const data = await getPerformance(quantCompany, qualQuarterYear, riskPeriodType);
        setPerfMap(data || {});
      } catch (err) {
        console.error("Failed to fetch performance", err);
        setPerfMap({});
      }
    }
    if (quantCompany && qualQuarterYear) {
      fetchPerf();
    }
  }, [quantCompany, qualQuarterYear, riskPeriodType]);

  // fetch risk-matrix for selected analysis period
  useEffect(() => {
    async function fetchRisk() {
      try {
        const data = await getRiskMatrix(quantCompany, qualQuarterYear, riskPeriodType, 5);
        setRiskMatrix(data || { metrics: [], tickers: [], matrix: [] });
      } catch (err) {
        console.error("Failed to fetch risk matrix", err);
        setRiskMatrix({ metrics: [], tickers: [], matrix: [] });
      }
    }
    if (quantCompany && qualQuarterYear) {
      fetchRisk();
    }
  }, [quantCompany, qualQuarterYear, riskPeriodType, 5]);

  // --- THE REACTIVITY ENGINE (UPDATED FOR MULTI-SELECT) ---
  useEffect(() => {
    const fetchChartData = async () => {
      // Ensure quantVariable is treated as an array
      const variables = Array.isArray(quantVariable) ? quantVariable : [quantVariable];
      
      if (variables.length === 0) return;

      setIsChartLoading(true);
      try {
        const data = await getCharts(quantCompany, quantPeriod, variables);
        setChartData(data);
      } catch (error) {
        console.error("Failed to load chart data:", error);
      } finally {
        setIsChartLoading(false);
      }
    };

    fetchChartData();
  }, [quantCompany, quantPeriod, quantVariable]);
  // -----------------------------

  const handleSyncSplit = () => {
    setIsSplitSynced(!isSplitSynced);
  };

  const submitChat = () => {
    if (chatInput.trim() !== "" && !isGenerating) {
      setIsGenerating(true);
      
      setTimeout(() => {
        setRagResponse({
          text: `Analysis for ${qualCompany} suggests strong liquidity positions in ${qualQuarterYear}, though R&D spending remains a primary focal point for margin compression.`,
          faithfulness: 88,
          relevancy: 94
        });
        setChatInput("");
        setIsGenerating(false);
      }, 1500);
    }
  };

  const handleChatSubmit = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      submitChat();
    }
  };


// QUALITATIVE ANALYSIS HANDLER
  const handleAIAnalysis = async () => {
    if (!qualQuery.trim() || isAnalyzing) return;

    setQualFilter('isAnalyzing', true);
    try {
      const data = await getQualitativeAnalysis(
        qualCompany, 
        qualQuarterYear, 
        qualQuery
      );
      
      setQualFilter('qualResponse', {
        text: data.final_response,
        faithfulness: data.faithfulness,
        relevancy: data.relevancy
      });
      // Clear the input after success
      setQualFilter('qualQuery', "");
    } catch (error) {
      console.error("AI Analysis failed", error);
    } finally {
      setQualFilter('isAnalyzing', false);
    }
  };

  // Helper for multi-select logic
  const toggleVariable = (v: string) => {
    const current = Array.isArray(quantVariable) ? quantVariable : [quantVariable];
    const next = current.includes(v) 
      ? current.filter(item => item !== v) 
      : [...current, v];
    setQuantFilter('quantVariable', next as any);
  };

  return (
    <div className="h-screen w-full flex flex-col bg-slate-950 text-slate-50 overflow-hidden font-sans">
      <div className="flex-1 p-3 min-h-0 overflow-hidden">
        <ResizablePanelGroup direction="horizontal" className="h-full min-h-0 rounded-xl border border-slate-800 bg-slate-900/10">

          {/* LEFT PANEL: QUALITATIVE ANALYSIS */}
            <ResizablePanel defaultSize={isSplitSynced ? 100 : 45} minSize={30}>
              <div className="h-full p-4 flex flex-col gap-4">
                {/* Header - preserved exactly */}
                <div className="flex items-center justify-between shrink-0">
                  <div className="flex items-center gap-3">
                    <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Qualitative Analysis</h2>
                    <BrainCircuit size={14} className="text-blue-500 opacity-50" />
                  </div>
                  <Button onClick={handleSyncSplit} size="sm" variant="outline" className={`h-7 text-[10px] border-slate-800 uppercase tracking-wider transition-all ${isSplitSynced ? 'bg-slate-800 text-blue-400 border-blue-900/50 px-4' : ''}`}>
                    {isSplitSynced ? "Enable Quantitative Analysis" : "Sync Split-Screen"}
                  </Button>
                </div>

                {/* Context Filters - preserved exactly */}
                <div className="grid grid-cols-3 gap-2 shrink-0">
                  <div className="flex flex-col gap-1">
                    <label className="text-[9px] uppercase tracking-wider text-slate-500 font-bold">Company</label>
                    <select value={qualCompany} onChange={(e) => setQualFilter('qualCompany', e.target.value)} className="bg-slate-900 border border-slate-800 text-xs text-slate-300 rounded px-2 py-2 outline-none h-9">
                      {companies.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                  <div className="flex flex-col gap-1">
                    <label className="text-[9px] uppercase tracking-wider text-slate-500 font-bold">Type</label>
                    <div className="flex bg-slate-900 border border-slate-800 rounded p-0.5 h-9">
                      <button 
                        onClick={() => setQualPeriodType("quarterly")} 
                        className={`flex-1 text-[8px] uppercase font-bold rounded transition-colors ${qualPeriodType === 'quarterly' ? 'bg-slate-800 text-blue-400' : 'text-slate-500 hover:text-slate-400'}`}
                      >
                        Quarterly
                      </button>
                      <button 
                        onClick={() => setQualPeriodType("yearly")} 
                        className={`flex-1 text-[8px] uppercase font-bold rounded transition-colors ${qualPeriodType === 'yearly' ? 'bg-slate-800 text-blue-400' : 'text-slate-500 hover:text-slate-400'}`}
                      >
                        Yearly
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="text-[9px] uppercase tracking-wider text-slate-500 font-bold">Period</label>
                    <select 
                      value={qualQuarterYear} 
                      onChange={(e) => setQualFilter('qualQuarterYear', e.target.value)} 
                      className="bg-slate-900 border border-slate-800 text-xs text-slate-300 rounded px-2 py-2 outline-none h-9 cursor-pointer"
                    >
                      {(qualPeriodType === "quarterly" ? periodQuarters : periodYears).map((p) => (
                        <option key={p} value={p}>
                          {p}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                    
                {/* Main Content Area - Layout preserved, logic updated to use qualResponse */}
                <div className="flex-1 min-h-0 flex flex-col gap-3">
                  <ScrollArea className="flex-1 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                    {isAnalyzing ? (
                      <div className="text-sm text-slate-500 italic">Processing filings...</div>
                    ) : !qualResponse ? (
                      <div className="text-sm text-slate-500 italic">Waiting for query...</div>
                    ) : (
                      <div className="text-sm text-slate-300 leading-relaxed">{qualResponse.text}</div>
                    )}
                  </ScrollArea>

                  {/* DeepEval Scores Card - Restored exactly as per your "Current Code" */}
                  <div className="shrink-0 bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                    <h3 className="text-[9px] font-bold uppercase tracking-widest text-slate-500 mb-3 flex items-center gap-2">
                      <BarChart3 size={12} className="text-blue-500" /> DeepEval Scores
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="flex justify-between text-[10px] mb-1.5 uppercase">
                          <span className="text-slate-400">Faithfulness</span>
                          <span className="text-blue-400 font-mono">
                            {qualResponse ? Math.round(qualResponse.faithfulness * 100) : 0}%
                          </span>
                        </div>
                        <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-blue-500 transition-all duration-500" 
                            style={{ width: `${(qualResponse?.faithfulness || 0) * 100}%` }} 
                          />
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-[10px] mb-1.5 uppercase">
                          <span className="text-slate-400">Relevancy</span>
                          <span className="text-indigo-400 font-mono">
                            {qualResponse ? Math.round(qualResponse.relevancy * 100) : 0}%
                          </span>
                        </div>
                        <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-indigo-500 transition-all duration-500" 
                            style={{ width: `${(qualResponse?.relevancy || 0) * 100}%` }} 
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Chat Input Area - Layout preserved, updated with store variables */}
                <div className="relative flex items-center w-full shrink-0">
                  <input 
                    type="text" 
                    value={qualQuery} 
                    onChange={(e) => setQualFilter('qualQuery', e.target.value)} 
                    onKeyDown={(e) => e.key === "Enter" && handleAIAnalysis()}
                    disabled={isAnalyzing}
                    placeholder={isAnalyzing ? "Generating response..." : `Ask about ${qualCompany}...`}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg py-3 pl-4 pr-12 text-sm text-slate-200 outline-none focus:border-blue-500/50 transition-all disabled:opacity-50"
                  />
                  <Button 
                    onClick={handleAIAnalysis}
                    disabled={isAnalyzing || qualQuery.trim() === ""}
                    size="icon"
                    className="absolute right-2 h-8 w-8 bg-blue-600 hover:bg-blue-500 text-white rounded-md transition-all disabled:opacity-50"
                  >
                    {isAnalyzing ? (
                      <div className="animate-spin h-4 w-4 border-2 border-white/30 border-t-white rounded-full" />
                    ) : (
                      <Send size={14} />
                    )}
                  </Button>
                </div>
              </div>
            </ResizablePanel>

          {!isSplitSynced ? (
            <>
              <ResizableHandle withHandle className="bg-slate-800/50 w-1" />
              <ResizablePanel defaultSize={55} minSize={35}>
                <div className="h-full min-h-0 p-4 flex flex-col gap-4 overflow-hidden">
                  <div className="flex items-center justify-between shrink-0">
                    <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Quantitative Analysis</h2>
                  </div>

                  <div className="shrink-0 flex flex-col gap-1 w-1/3">
                    <label className="text-[9px] uppercase tracking-wider text-slate-500 font-bold">Company</label>
                    <select value={quantCompany} onChange={(e) => setQuantFilter('quantCompany', e.target.value)} className="bg-slate-900 border border-slate-800 text-xs text-slate-300 rounded px-2 py-1.5 outline-none">
                      {companies.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>

                  {expandedWidget !== "risk" && expandedWidget !== "metrics" && (
                    <Tabs defaultValue="charts" className="flex-1 flex flex-col overflow-hidden min-h-0">
                      <div className="flex items-center justify-between shrink-0 mb-2">
                        <TabsList className="bg-slate-950 border border-slate-800 p-1 h-9">
                          <TabsTrigger value="charts" className="text-xs px-4">Charts</TabsTrigger>
                          <TabsTrigger value="ratios" className="text-xs px-4">Ratios</TabsTrigger>
                        </TabsList>
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500" onClick={() => setExpandedWidget(expandedWidget === "tabs" ? "all" : "tabs")}>
                          {expandedWidget === "tabs" ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
                        </Button>
                      </div>
                      
                      <TabsContent value="charts" className="flex-1 overflow-hidden data-[state=active]:flex flex-col min-h-0 m-0 gap-3">
                        <div className="grid grid-cols-1 gap-2 shrink-0">
                            <div className="flex flex-col gap-1">
                            <label className="text-[9px] uppercase tracking-wider text-slate-500 font-bold">Variables (Select Multiple)</label>
                            <ScrollArea className="w-full whitespace-nowrap rounded-md border border-slate-800 bg-slate-900/50 p-2">
                              <div className="flex gap-1.5">
                                
                                {/* 1. Dedicated Candlestick (OHLC) Button using your existing logic */}
                                <button
                                  onClick={() => {
                                    // Manually toggle the 4 required variables
                                    // If your state setter is setQuantFilter, we use that:
                                    setQuantFilter('quantVariable', ['Open', 'High', 'Low', 'Close']);
                                  }}
                                  className="px-3 py-1 rounded-full text-[10px] font-bold transition-all flex items-center gap-1 border bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20"
                                >
                                  Candlestick (OHLC)
                                </button>

                                <div className="w-[1px] bg-slate-800 mx-1" />

                                {/* 2. Your existing Variable Map */}
                                {['Adj Close', 'High', 'Close', 'Return', 'Open', 'Volume', 'Cumulative Return', 'Volatility', 'Dividends', 'Low' ].map(v => {
                                  const isSelected = (Array.isArray(quantVariable) ? quantVariable : [quantVariable]).includes(v);
                                  return (
                                    <button
                                      key={v}
                                      onClick={() => toggleVariable(v)}
                                      className={`px-3 py-1 rounded-full text-[10px] font-medium transition-all flex items-center gap-1 border ${
                                        isSelected 
                                          ? 'bg-blue-500/20 text-blue-400 border-blue-500/50' 
                                          : 'bg-slate-800/50 text-slate-500 border-transparent hover:border-slate-700'
                                      }`}
                                    >
                                      {isSelected && <Check size={10} />}
                                      {v}
                                    </button>
                                  );
                                })}
                              </div>
                              <ScrollBar orientation="horizontal" />
                            </ScrollArea>
                          </div>
                            <div className="flex flex-col gap-1 w-1/3">
                                <label className="text-[9px] uppercase tracking-wider text-slate-500 font-bold">Timeframe</label>
                                <select value={quantPeriod} onChange={(e) => setQuantFilter('quantPeriod', e.target.value as any)} className="bg-slate-900 border border-slate-800 text-xs text-slate-300 rounded px-2 py-1.5 outline-none">
                                    <option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option><option value="quarterly">Quarterly</option><option value="yearly">Yearly</option>
                                </select>
                            </div>
                        </div>
                        
                        <Card className="flex-1 min-h-0 flex flex-col bg-slate-950/40 border-slate-800 overflow-hidden mt-2">
                        {isChartLoading ? (
                          <div className="flex flex-1 items-center justify-center">
                            <Activity className="animate-pulse text-blue-500" size={32} />
                          </div>
                        ) : chartData.length > 0 ? (
                          <div className="flex-1 min-h-0 h-full p-4">
                            <QuantitativeChart 
                              data={chartData} 
                              variables={Array.isArray(quantVariable) ? quantVariable : [quantVariable]} 
                            />
                          </div>
                        ) : (
                          <div className="flex flex-1 items-center justify-center text-slate-600 italic text-[11px]">
                            Select variables to view the analysis.
                          </div>
                        )}
                      </Card>
                      </TabsContent>

                      <TabsContent value="ratios" className="flex-1 overflow-hidden data-[state=active]:flex flex-col min-h-0 m-0">
                        <Card className="flex-1 bg-slate-950 border-slate-800 p-0 flex flex-col overflow-hidden">
                          <div className="p-3 border-b border-slate-800 flex items-center bg-slate-900/20 shrink-0">
                            <div className="flex items-center gap-6">
                              <div className="flex items-center gap-2">
                                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Category:</span>
                                <select
                                  value={selectedCategory}
                                  onChange={(e) => setSelectedCategory(e.target.value as any)}
                                  className="bg-slate-950 border border-slate-800 text-[11px] text-blue-400 rounded px-2 py-1 outline-none cursor-pointer"
                                >
                                  {Object.keys(ratioGroups).map((cat) => (
                                    <option key={cat} value={cat}>{cat}</option>
                                  ))}
                                </select>
                              </div>

                              <div className="flex items-center gap-2">
                                <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">PERIOD:</span>
                               <select
                                value={ratioPeriod}
                                onChange={(e) => setRatioPeriod(e.target.value as 'Quarterly' | 'Yearly')}
                                className="bg-slate-950 border border-slate-800 text-[11px] text-blue-400 rounded px-2 py-1 outline-none cursor-pointer hover:border-slate-700 transition-colors">
                                {["Quarterly", "Yearly"].map((p) => (
                                  <option key={p} value={p}>{p}</option>
                                ))}
                              </select>
                              </div>
                            </div>
                          </div>

                          {/* START - dynamic Ratios table (replace existing .flex-1 overflow-hidden relative block) */}
                            <div className="flex-1 overflow-hidden relative">
                              <ScrollArea className="h-full w-full">
                                <div className="min-w-[600px] pb-4">
                                  <table className="w-full text-left text-[11px]">
                                    <thead className="sticky top-0 bg-slate-900/95 backdrop-blur text-slate-500 uppercase text-[9px] font-bold tracking-widest z-10 border-b border-slate-800 shadow-sm">
                                      <tr>
                                        <th className="p-3">Ratio Name</th>

                                        { (ratioData && ratioData.length > 0) ? (
                                          // build headers from first row keys (excluding metric/index)
                                          Object.keys(ratioData[0])
                                            .filter((k) => k !== "metric" && k !== "index" && k !== "__index_level_1__")
                                            .map((col) => (
                                              <th key={col} className="p-3 text-center">{col}</th>
                                            ))
                                        ) : (
                                          // fallback static headers
                                          years.map((year) => <th key={year} className="p-3 text-center">{year}</th>)
                                        )}
                                      </tr>
                                    </thead>

                                    <tbody className="divide-y divide-slate-800/50">
                                      { (ratioData && ratioData.length > 0) ? (
                                        // render rows from backend records
                                        ratioData.map((row: any) => {
                                          const metricName = row.metric ?? row.index ?? row.__index_level_1__ ?? "Unknown";
                                          const cols = Object.keys(row).filter((k) => k !== "metric" && k !== "index" && k !== "__index_level_1__");
                                          return (
                                            <tr key={metricName} className="hover:bg-blue-500/5 transition-colors group">
                                              <td className="p-3 text-slate-300 group-hover:text-blue-300 transition-colors">{metricName}</td>
                                              { cols.map((col) => {
                                                  const raw = row[col];
                                                  const display = (raw === null || raw === undefined || Number.isNaN(Number(raw))) ? "--" : Number(raw).toFixed(2);
                                                  return <td key={col} className="p-3 text-center font-mono text-slate-600">{display}</td>;
                                                })
                                              }
                                            </tr>
                                          );
                                        })
                                      ) : (
                                        // fallback: show metric names from selectedCategory with empty cells
                                        ratioGroups[selectedCategory].map((ratio) => (
                                          <tr key={ratio} className="hover:bg-blue-500/5 transition-colors group">
                                            <td className="p-3 text-slate-300 group-hover:text-blue-300 transition-colors">{ratio}</td>
                                            { years.map((y) => <td key={y} className="p-3 text-center font-mono text-slate-600">--</td>) }
                                          </tr>
                                        ))
                                      )}
                                    </tbody>
                                  </table>
                                </div>
                                <ScrollBar orientation="horizontal" />
                                <ScrollBar orientation="vertical" />
                              </ScrollArea>
                            </div>
                            {/* END - dynamic Ratios table */}
                        </Card>
                      </TabsContent>
                    </Tabs>
                  )}

                  {expandedWidget !== "tabs" && (
                    <div className="flex flex-col flex-1 min-h-0 gap-3 overflow-hidden">
                      {expandedWidget === "all" && (
                        <div className="flex items-center gap-4 bg-slate-900/40 p-2 rounded-md border border-slate-800/50">
                          <div className="flex bg-slate-950 border border-slate-800 rounded p-0.5 h-7 w-48">
                            <button onClick={() => setRiskPeriodType("quarterly")} className={`flex-1 text-[9px] uppercase font-bold rounded ${riskPeriodType === 'quarterly' ? 'bg-slate-800 text-blue-400' : 'text-slate-500'}`}>Quarterly</button>
                            <button onClick={() => setRiskPeriodType("yearly")} className={`flex-1 text-[9px] uppercase font-bold rounded ${riskPeriodType === 'yearly' ? 'bg-slate-800 text-blue-400' : 'text-slate-500'}`}>Yearly</button>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-[9px] text-slate-500 uppercase font-bold tracking-wider">Analysis Period:</span>
                            <select 
                              value={qualQuarterYear} 
                              onChange={(e) => setQualFilter('qualQuarterYear', e.target.value)}
                              className="bg-slate-950 border border-slate-800 text-[10px] text-blue-400 rounded px-2 py-1 outline-none h-7 cursor-pointer"
                            >
                              {(riskPeriodType === "yearly" ? periodYears : periodQuartersQuant).map(p => (
                                <option key={p} value={p}>{p}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                      )}

                      <div className={`${expandedWidget === "all" ? "flex-1 grid grid-cols-2" : "flex-1 flex w-full"} gap-4 overflow-hidden`}>
                        {(expandedWidget === "all" || expandedWidget === "risk") && (() => {
                          let displayData: { metric: string; value: number }[] = [];

                          if (riskMatrix && typeof riskMatrix === 'object' && Object.keys(riskMatrix).length > 0 && !('matrix' in riskMatrix)) {
                            displayData = Object.entries(riskMatrix).map(([key, val]) => ({
                              metric: key,
                              value: typeof val === 'number' ? val : (isNaN(Number(val)) ? 0 : Number(val))
                            }));
                          }

                          const hasValidData = displayData.length > 0;

                          return (
                            <Card className={`bg-slate-950 border-slate-800 p-4 flex flex-col overflow-hidden ${expandedWidget === 'risk' ? 'flex-1 w-full' : ''}`}>
                              <div className="flex items-center justify-between mb-3">
                                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Risk Chart</span>
                                <Button variant="ghost" size="icon" className="h-6 w-6 text-slate-500" onClick={() => setExpandedWidget(expandedWidget === "risk" ? "all" : "risk")}>
                                  {expandedWidget === "risk" ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                                </Button>
                              </div>

                              {expandedWidget === "risk" && (
                                <div className="flex items-center gap-4 mb-4 pb-3 border-b border-slate-900">
                                  <div className="flex bg-slate-900 border border-slate-800 rounded p-0.5 h-7 w-40">
                                    <button onClick={() => setRiskPeriodType("quarterly")} className={`flex-1 text-[9px] uppercase font-bold rounded ${riskPeriodType === 'quarterly' ? 'bg-slate-800 text-blue-400' : 'text-slate-500'}`}>Quarterly</button>
                                    <button onClick={() => setRiskPeriodType("yearly")} className={`flex-1 text-[9px] uppercase font-bold rounded ${riskPeriodType === 'yearly' ? 'bg-slate-800 text-blue-400' : 'text-slate-500'}`}>Yearly</button>
                                  </div>
                                  <select
                                    value={qualQuarterYear}
                                    onChange={(e) => setQualFilter('qualQuarterYear', e.target.value)}
                                    className="bg-slate-900 border border-slate-800 text-[10px] text-slate-300 rounded px-2 py-1 outline-none h-7"
                                  >
                                    {(riskPeriodType === "yearly" ? periodYears : periodQuartersQuant).map(p => (
                                      <option key={p} value={p}>{p.replace('_', ' ')}</option>
                                    ))}
                                  </select>
                                </div>
                              )}

                              {/* CHART CONTAINER */}
                              <div className="flex-1 flex flex-col min-h-[240px] pt-6 pb-12 pl-6 pr-4 relative">
                                {hasValidData ? (
                                  <div className="flex h-full w-full relative">
                                    
                                    {/* Y-Axis Title */}
                                    <div className="absolute -left-8 top-1/2 -translate-y-1/2 -rotate-90 text-[9px] font-bold text-slate-500 uppercase tracking-tighter whitespace-nowrap">
                                      Risk Score
                                    </div>

                                    {/* Y-Axis Markers */}
                                    <div className="flex flex-col justify-between items-end pr-3 text-[9px] font-mono text-slate-500 w-8 shrink-0 relative z-10">
                                      <span>100</span>
                                      <span>75</span>
                                      <span>50</span>
                                      <span>25</span>
                                      <span>0</span>
                                    </div>

                                    {/* Chart Grid & Bars Area */}
                                    <div className="relative flex-1 border-l border-b border-slate-700 flex items-end justify-between px-2 sm:px-6">
                                      
                                      {/* Horizontal Grid Lines */}
                                      {[0, 0.25, 0.5, 0.75, 1].map((tick) => (
                                        <div key={tick} className="absolute left-0 w-full border-t border-dashed border-slate-800/60" style={{ top: `${tick * 100}%` }} />
                                      ))}

                                      {/* Vertical Bars */}
                                      {displayData.map((item, idx) => {
                                        const height = Math.max(0, Math.min(100, item.value));
                                        return (
                                          <div key={idx} className="relative flex flex-col items-center justify-end h-full w-full max-w-[32px] sm:max-w-[42px] group z-10 mx-1">
                                            
                                            {/* Hover Tooltip */}
                                            <div className="absolute -top-7 bg-slate-800 border border-slate-700 text-white text-[10px] font-mono px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity z-20 pointer-events-none shadow-lg">
                                              {item.value.toFixed(1)}
                                            </div>
                                            
                                            {/* Bar Segment (Solid Amber/Yellow) */}
                                            <div 
                                              className="w-full bg-amber-400 border-t border-amber-200 rounded-t-sm transition-all duration-500 ease-out group-hover:bg-amber-300 group-hover:scale-x-105 cursor-pointer shadow-[0_0_15px_rgba(251,191,36,0.1)]"
                                              style={{ height: `${height}%` }}
                                            />
                                            
                                            {/* X-Axis Labels */}
                                            <div className="absolute -bottom-7 text-center w-24">
                                              <span className="text-[9px] text-slate-400 truncate block w-full px-1">
                                                {item.metric}
                                              </span>
                                            </div>
                                          </div>
                                        );
                                      })}

                                      {/* X-Axis Title */}
                                      <div className="absolute -bottom-11 left-1/2 -translate-x-1/2 text-[9px] font-bold text-slate-500 uppercase tracking-widest">
                                        Metric
                                      </div>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="w-full h-full flex items-center justify-center text-slate-500 text-[11px] italic py-6">
                                    No risk chart data available
                                  </div>
                                )}
                              </div>
                            </Card>
                          );
                        })()}

                        {(expandedWidget === "all" || expandedWidget === "metrics") && (
                          <Card className={`bg-slate-950 border-slate-800 p-4 flex flex-col overflow-hidden ${expandedWidget === 'metrics' ? 'flex-1 w-full' : ''}`}>
                            <div className="flex items-center justify-between mb-3">
                              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Performance Ratios</span>
                              <Button variant="ghost" size="icon" className="h-6 w-6 text-slate-500" onClick={() => setExpandedWidget(expandedWidget === "metrics" ? "all" : "metrics")}>
                                {expandedWidget === "metrics" ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                              </Button>
                            </div>

                            {expandedWidget === "metrics" && (
                              <div className="flex items-center gap-4 mb-4 pb-3 border-b border-slate-900">
                                  <div className="flex bg-slate-900 border border-slate-800 rounded p-0.5 h-7 w-40">
                                    <button onClick={() => setRiskPeriodType("quarterly")} className={`flex-1 text-[9px] uppercase font-bold rounded ${riskPeriodType === 'quarterly' ? 'bg-slate-800 text-blue-400' : 'text-slate-500'}`}>Quarterly</button>
                                    <button onClick={() => setRiskPeriodType("yearly")} className={`flex-1 text-[9px] uppercase font-bold rounded ${riskPeriodType === 'yearly' ? 'bg-slate-800 text-blue-400' : 'text-slate-500'}`}>Yearly</button>
                                  </div>
                                  <select 
                                    value={qualQuarterYear}
                                    onChange={(e) => setQualFilter('qualQuarterYear', e.target.value)}
                                    className="bg-slate-900 border border-slate-800 text-[10px] text-slate-300 rounded px-2 py-1 outline-none h-7"
                                  >
                                    {(riskPeriodType === "yearly" ? periodYears : periodQuartersQuant).map(p => <option key={p} value={p}>{p.replace('_', ' ')}</option>)}
                                  </select>
                              </div>
                            )}
                            
                            <div className="flex-1 min-h-0 overflow-hidden">
                              <ScrollArea className="h-full pr-3">
                                <div className="flex flex-col pb-2">
                                {/* header row */}
                                <div className="flex justify-between items-center mb-2 px-1">
                                  <span className="text-slate-400 text-[11px] uppercase tracking-wider">Metric</span>
                                  <span className="text-slate-400 text-[11px] uppercase tracking-wider">Score</span>
                                </div>

                                {/* compute helper to extract perf value from perfMap */}
                                {(() => {
                                  const getRaw = (metric: string) => {
                                    const mappingKey = `${metric}|${quantCompany}`;
                                    if (Array.isArray(perfMap)) {
                                      const row = perfMap[0] ?? {};
                                      return row[metric] ?? row[mappingKey] ?? row[metric.replace(/\s+/g, ' ')];
                                    }
                                    if (perfMap && typeof perfMap === 'object') {
                                      return perfMap[mappingKey] ?? perfMap[metric] ?? perfMap[metric.replace(/\s+/g, ' ')];
                                    }
                                    return undefined;
                                  };

                                  const hasAny = performanceMetrics.some(m => {
                                    const r = getRaw(m);
                                    return r !== undefined && r !== null && !Number.isNaN(Number(r));
                                  });

                                  if (!hasAny) {
                                    return (
                                      <div className="w-full flex items-center justify-center text-slate-500 text-sm py-6">
                                        No data available for the specific period
                                      </div>
                                    );
                                  }

                                  return (
                                    <>
                                      {performanceMetrics.map((metric) => {
                                        const raw = getRaw(metric);
                                        const value = raw == null || Number.isNaN(Number(raw)) ? "--" : Number(raw).toFixed(2);

                                        return (
                                          <div
                                            key={metric}
                                            className="w-full border-b border-slate-900/50 last:border-0 px-1 py-2 flex justify-between items-center hover:bg-slate-900/30 transition-colors"
                                          >
                                            <span className="text-slate-400 text-[11px]">{metric}</span>
                                            <div className="font-mono text-[11px]">
                                              <span className="text-blue-400/80">{value}</span>
                                            </div>
                                          </div>
                                        );
                                      })}
                                    </>
                                  );
                                })()}
                                </div>
                              </ScrollArea>
                            </div>
                          </Card>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </ResizablePanel>
            </>
          ) : null}
        </ResizablePanelGroup>
      </div>
    </div>
  );
}