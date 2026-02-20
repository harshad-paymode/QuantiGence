"use client";

import { useState, useRef } from "react";
import { 
  ResizableHandle, 
  ResizablePanel, 
  ResizablePanelGroup 
} from "@/components/ui/resizable";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Maximize2, Minimize2, BrainCircuit, Activity, BarChart3 } from "lucide-react"; 

// Import State Management
import { useDashboardStore } from '@/store/useDashboardStore';

const companies = [
  "Apple Inc.", "MICROSOFT CORP", "Alphabet Inc.", "AMAZON COM INC.",
  "Meta Platforms, Inc.", "NVIDIA CORP", "Tesla, Inc.", "ORACLE CORP",
  "Salesforce, Inc.", "NETFLIX INC", "ADOBE INC."
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

const riskMatrixData = [
  [0.82, 0.70, 0.34, 0.27, 0.39],
  [0.24, 0.55, 0.30, 0.18, 0.27],
  [0.83, 0.65, 0.45, 0.30, 0.15],
  [0.85, 0.87, 0.74, 0.55, 0.33],
  [0.88, 0.88, 0.83, 0.36, 0.30],
];

const years = ["2023", "2022", "2021", "2020"];
const periodYears = ["2024", "2025"];
const periodQuarters = ["Q1_2024", "Q2_2024", "Q3_2024", "Q1_2025", "Q2_2025", "Q3_2025"];

type ExpandedWidget = "all" | "tabs" | "risk" | "metrics";

export default function Home() {
  const { 
    quantCompany, quantVariable, quantPeriod, setQuantFilter,
    qualCompany, qualQuarterYear, setQualFilter 
  } = useDashboardStore();

  const [selectedCategory, setSelectedCategory] = useState<keyof typeof ratioGroups>("Valuation");
  const [expandedWidget, setExpandedWidget] = useState<ExpandedWidget>("all");
  const [chatInput, setChatInput] = useState("");
  const [ragResponse, setRagResponse] = useState<any>(null);
  const [isSplitSynced, setIsSplitSynced] = useState(false);

  const [qualPeriodType, setQualPeriodType] = useState<"quarterly" | "yearly">("quarterly");
  const [riskPeriodType, setRiskPeriodType] = useState<"quarterly" | "yearly">("quarterly");
  
  const panelGroupRef = useRef<any>(null);

  const handleSyncSplit = () => {
    setIsSplitSynced(!isSplitSynced);
  };

  const handleChatSubmit = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && chatInput.trim() !== "") {
      setRagResponse({
        text: `Analysis for ${qualCompany} suggests strong liquidity positions in ${qualQuarterYear}, though R&D spending remains a primary focal point for margin compression.`,
        faithfulness: 88,
        relevancy: 94
      });
      setChatInput("");
    }
  };

  const getHeatmapColor = (val: number) => {
    if (val > 0.8) return "bg-green-500 text-green-950";
    if (val > 0.6) return "bg-green-400 text-green-950";
    if (val > 0.4) return "bg-yellow-400 text-yellow-950";
    if (val > 0.2) return "bg-orange-500 text-orange-950";
    return "bg-red-600 text-red-50";
  };

  return (
    <div className="h-screen w-full flex flex-col bg-slate-950 text-slate-50 overflow-hidden font-sans">
      <div className="flex-1 p-3 overflow-hidden">
        <ResizablePanelGroup ref={panelGroupRef} direction="horizontal" className="rounded-xl border border-slate-800 bg-slate-900/10">
          
          {/* LEFT PANEL: QUALITATIVE ANALYSIS (Main focus) */}
          <ResizablePanel defaultSize={isSplitSynced ? 100 : 45} minSize={30}>
            <div className="h-full p-4 flex flex-col gap-4">
              <div className="flex items-center justify-between shrink-0">
                <div className="flex items-center gap-3">
                  <h2 className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Qualitative Analysis</h2>
                  <BrainCircuit size={14} className="text-blue-500 opacity-50" />
                </div>
                {/* Moved Toggle Button to Left Panel when Synced */}
                <Button onClick={handleSyncSplit} size="sm" variant="outline" className={`h-7 text-[10px] border-slate-800 uppercase tracking-wider transition-all ${isSplitSynced ? 'bg-slate-800 text-blue-400 border-blue-900/50 px-4' : ''}`}>
                  {isSplitSynced ? "Enable Quantitative Analysis" : "Sync Split-Screen"}
                </Button>
              </div>

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
                      
              <div className="flex-1 min-h-0 flex flex-col gap-3">
                <ScrollArea className="flex-1 rounded-xl border border-slate-800 bg-slate-950/40 p-4">
                  {!ragResponse ? (
                    <div className="text-sm text-slate-500 italic">Waiting for query...</div>
                  ) : (
                    <div className="text-sm text-slate-300 leading-relaxed">{ragResponse.text}</div>
                  )}
                </ScrollArea>

                <div className="shrink-0 bg-slate-900/50 border border-slate-800 rounded-xl p-4">
                    <h3 className="text-[9px] font-bold uppercase tracking-widest text-slate-500 mb-3 flex items-center gap-2">
                        <BarChart3 size={12} className="text-blue-500" /> DeepEval Scores
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <div className="flex justify-between text-[10px] mb-1.5 uppercase">
                                <span className="text-slate-400">Faithfulness</span>
                                <span className="text-blue-400 font-mono">{ragResponse?.faithfulness || 0}%</span>
                            </div>
                            <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                                <div className="h-full bg-blue-500 transition-all duration-500" style={{ width: `${ragResponse?.faithfulness || 0}%` }} />
                            </div>
                        </div>
                        <div>
                            <div className="flex justify-between text-[10px] mb-1.5 uppercase">
                                <span className="text-slate-400">Relevancy</span>
                                <span className="text-indigo-400 font-mono">{ragResponse?.relevancy || 0}%</span>
                            </div>
                            <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                                <div className="h-full bg-indigo-500 transition-all duration-500" style={{ width: `${ragResponse?.relevancy || 0}%` }} />
                            </div>
                        </div>
                    </div>
                </div>
              </div>

              <input 
                type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} onKeyDown={handleChatSubmit}
                placeholder={`Ask about ${qualCompany}...`}
                className="w-full bg-slate-900 border border-slate-800 rounded-lg py-3 px-4 text-sm outline-none focus:border-blue-500/50 transition-all"
              />
            </div>
          </ResizablePanel>

          {!isSplitSynced && (
            <>
              <ResizableHandle withHandle className="bg-slate-800/50 w-1" />
              {/* RIGHT PANEL: QUANTITATIVE ANALYSIS */}
              <ResizablePanel defaultSize={55} minSize={35}>
                <div className="h-full p-4 flex flex-col gap-4 overflow-hidden">
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
                        <div className="grid grid-cols-2 gap-2">
                            <div className="flex flex-col gap-1">
                                <label className="text-[9px] uppercase tracking-wider text-slate-500 font-bold">Variable</label>
                                <select value={quantVariable} onChange={(e) => setQuantFilter('quantVariable', e.target.value as any)} className="bg-slate-900 border border-slate-800 text-xs text-slate-300 rounded px-2 py-1.5 outline-none">
                                    {['Adjusted Close', 'High', 'Close', 'Return', 'Open', 'Volume', 'Cumulative Return', 'Volatility', 'Dividends', 'Low' ].map(v => <option key={v} value={v}>{v}</option>)}
                                </select>
                            </div>
                            <div className="flex flex-col gap-1">
                                <label className="text-[9px] uppercase tracking-wider text-slate-500 font-bold">Timeframe</label>
                                <select value={quantPeriod} onChange={(e) => setQuantFilter('quantPeriod', e.target.value as any)} className="bg-slate-900 border border-slate-800 text-xs text-slate-300 rounded px-2 py-1.5 outline-none">
                                    <option value="daily">Daily</option><option value="weekly">Weekly</option><option value="monthly">Monthly</option><option value="monthly">Quarterly</option><option value="monthly">Yearly</option>
                                </select>
                            </div>
                        </div>
                        <Card className="flex-1 flex flex-col items-center justify-center bg-slate-950/40 border-slate-800 border-dashed italic text-[11px] text-slate-600">
                          <Activity className="mb-2 opacity-20" size={32} />
                          {quantVariable} chart for {quantCompany}
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
                                  defaultValue="Quarterly"
                                  className="bg-slate-950 border border-slate-800 text-[11px] text-blue-400 rounded px-2 py-1 outline-none cursor-pointer hover:border-slate-700 transition-colors"
                                >
                                  {["Quarterly", "Yearly"].map((p) => (
                                    <option key={p} value={p}>{p}</option>
                                  ))}
                                </select>
                              </div>
                            </div>
                          </div>

                          <div className="flex-1 overflow-hidden relative">
                            <ScrollArea className="h-full w-full">
                              <div className="min-w-[600px] pb-4">
                                <table className="w-full text-left text-[11px]">
                                  <thead className="sticky top-0 bg-slate-900/95 backdrop-blur text-slate-500 uppercase text-[9px] font-bold tracking-widest z-10 border-b border-slate-800 shadow-sm">
                                    <tr>
                                      <th className="p-3">Ratio Name</th>
                                      {years.map(year => (
                                        <th key={year} className="p-3 text-center">{year}</th>
                                      ))}
                                    </tr>
                                  </thead>
                                  <tbody className="divide-y divide-slate-800/50">
                                    {ratioGroups[selectedCategory].map((ratio) => (
                                      <tr key={ratio} className="hover:bg-blue-500/5 transition-colors group">
                                        <td className="p-3 text-slate-300 group-hover:text-blue-300 transition-colors">{ratio}</td>
                                        {years.map(year => (
                                          <td key={year} className="p-3 text-center font-mono text-slate-600">--</td>
                                        ))}
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              </div>
                              <ScrollBar orientation="horizontal" />
                              <ScrollBar orientation="vertical" />
                            </ScrollArea>
                          </div>
                        </Card>
                      </TabsContent>
                    </Tabs>
                  )}

                  {/* BOTTOM SECTION */}
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
                              {(riskPeriodType === "yearly" ? periodYears : periodQuarters).map(p => (
                                <option key={p} value={p}>{p}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                      )}

                      <div className={`${expandedWidget === "all" ? "flex-1 grid grid-cols-2" : "flex-1 flex w-full"} gap-4 overflow-hidden`}>
                        
                        {/* RISK MATRIX */}
                        {(expandedWidget === "all" || expandedWidget === "risk") && (
                          <Card className={`bg-slate-950 border-slate-800 p-4 flex flex-col overflow-hidden ${expandedWidget === 'risk' ? 'flex-1 w-full' : ''}`}>
                            <div className="flex items-center justify-between mb-3">
                              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Risk Matrix</span>
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
                                    {(riskPeriodType === "yearly" ? periodYears : periodQuarters).map(p => <option key={p} value={p}>{p.replace('_', ' ')}</option>)}
                                  </select>
                              </div>
                            )}
                            
                            <div className="flex-1 flex flex-col min-h-0 pt-2 pr-2">
                              <div className="flex-1 flex gap-[2px]">
                                {riskMatrixData.slice(0, 5).map((row, i) => (
                                  <div key={i} className="flex-1 flex flex-col gap-[2px]">
                                      {row.slice(0, 5).map((val, j) => (
                                          <div key={j} className={`flex-1 rounded-sm flex items-center justify-center ${getHeatmapColor(val)} hover:ring-1 ring-white/20 transition-all`}>
                                              <span className="text-[9px] font-bold">{val.toFixed(2)}</span>
                                          </div>
                                      ))}
                                  </div>
                                ))}
                              </div>
                            </div>
                          </Card>
                        )}

                        {/* PERFORMANCE METRICS */}
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
                                    {(riskPeriodType === "yearly" ? periodYears : periodQuarters).map(p => <option key={p} value={p}>{p.replace('_', ' ')}</option>)}
                                  </select>
                              </div>
                            )}
                            
                            <div className="flex-1 min-h-0 overflow-hidden">
                              <ScrollArea className="h-full pr-3">
                                <div className="flex flex-col pb-2">
                                  {performanceMetrics.map((metric) => (
                                    <div key={metric} className="flex justify-between items-center py-1.5 text-[11px] border-b border-slate-900/50 last:border-0 hover:bg-slate-900/30 transition-colors">
                                      <span className="text-slate-400">{metric}</span>
                                      <div className="flex gap-6 font-mono text-[10px]">
                                        <span className="text-blue-400/80">0.00</span>
                                        <span className="text-slate-700">--</span>
                                      </div>
                                    </div>
                                  ))}
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
          )}
        </ResizablePanelGroup>
      </div>
    </div>
  );
}
