import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Activity, Database, FileText, FlaskConical, GitBranch, GitMerge, LayoutDashboard, Link as LinkIcon, MessageSquare, Network, Paperclip, Search, Send, Settings, TerminalSquare, UploadCloud, User } from "lucide-react";

export default function ClinicalDark() {
  const [view, setView] = useState<'login' | 'app'>('login');

  return (
    <div className="min-h-screen bg-[#0F172A] text-[#F8FAFC] font-sans selection:bg-[#06B6D4]/30 flex flex-col overflow-hidden">
      {/* Demo Tab Bar - Only for mockup purposes */}
      <div className="bg-[#020617] border-b border-[#334155] p-2 flex justify-center gap-2 relative z-50 shrink-0">
        <Button 
          variant="outline"
          className={`h-8 text-xs rounded-none border-[#334155] bg-transparent ${view === 'login' ? 'bg-[#06B6D4]/10 text-[#06B6D4] border-[#06B6D4]' : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]'}`}
          onClick={() => setView('login')}
        >
          Login View
        </Button>
        <Button 
          variant="outline"
          className={`h-8 text-xs rounded-none border-[#334155] bg-transparent ${view === 'app' ? 'bg-[#06B6D4]/10 text-[#06B6D4] border-[#06B6D4]' : 'text-[#94A3B8] hover:text-[#F8FAFC] hover:bg-[#1E293B]'}`}
          onClick={() => setView('app')}
        >
          App View
        </Button>
      </div>

      <div className="flex-1 relative overflow-hidden">
        {view === 'login' ? <LoginView onLogin={() => setView('app')} /> : <AppView />}
      </div>
    </div>
  );
}

function LoginView({ onLogin }: { onLogin: () => void }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center bg-[#0F172A] overflow-hidden">
      {/* Subtle Grid Pattern Background */}
      <div 
        className="absolute inset-0 z-0 opacity-20 pointer-events-none" 
        style={{
          backgroundImage: 'radial-gradient(circle at 2px 2px, #334155 1px, transparent 0)',
          backgroundSize: '24px 24px'
        }}
      />
      
      {/* Glow Behind Card */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[#06B6D4]/10 rounded-full blur-[120px] pointer-events-none" />

      <Card className="w-full max-w-md relative z-10 bg-[#1E293B]/80 backdrop-blur-xl border-[#334155] shadow-2xl rounded-sm rounded-tr-3xl overflow-hidden">
        {/* Top Accent Line */}
        <div className="h-1 w-full bg-[#06B6D4]" />
        
        <CardHeader className="space-y-4 pt-10 pb-6 px-8 text-center">
          <div className="mx-auto w-16 h-16 border-2 border-[#06B6D4] rounded-none flex items-center justify-center bg-[#0F172A] shadow-[0_0_15px_rgba(6,182,212,0.3)] mb-2">
            <Network className="w-8 h-8 text-[#06B6D4]" />
          </div>
          <div className="space-y-1">
            <CardTitle className="text-3xl font-bold tracking-tight text-[#F8FAFC]">AORTA</CardTitle>
            <CardDescription className="text-[#94A3B8] text-sm uppercase tracking-widest font-mono">
              Assay Ontology & Retrieval Translation App
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="px-8 pb-8 space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-mono text-[#94A3B8] uppercase">Researcher ID</label>
              <Input 
                placeholder="system.admin" 
                className="bg-[#0F172A] border-[#334155] text-[#F8FAFC] font-mono rounded-none focus-visible:ring-1 focus-visible:ring-[#06B6D4] focus-visible:ring-offset-0 placeholder:text-[#334155]"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-mono text-[#94A3B8] uppercase">Access Key</label>
                <a href="#" className="text-xs font-mono text-[#06B6D4] hover:underline">Reset</a>
              </div>
              <Input 
                type="password" 
                placeholder="••••••••••••" 
                className="bg-[#0F172A] border-[#334155] text-[#F8FAFC] rounded-none focus-visible:ring-1 focus-visible:ring-[#06B6D4] focus-visible:ring-offset-0 placeholder:text-[#334155]"
              />
            </div>
          </div>

          <Button 
            className="w-full bg-[#06B6D4] hover:bg-[#0891B2] text-[#0F172A] rounded-none font-bold uppercase tracking-wider h-12 shadow-[0_0_20px_rgba(6,182,212,0.4)] hover:shadow-[0_0_30px_rgba(6,182,212,0.6)] transition-all"
            onClick={onLogin}
          >
            Authenticate Sequence
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function AppView() {
  return (
    <div className="absolute inset-0 flex bg-[#0F172A]">
      {/* Left Sidebar */}
      <div className="w-72 border-r border-[#334155] bg-[#1E293B] flex flex-col z-10 shadow-[4px_0_24px_rgba(0,0,0,0.5)] shrink-0">
        <div className="h-16 flex items-center px-4 border-b border-[#334155] gap-3">
          <Network className="w-6 h-6 text-[#06B6D4]" />
          <div>
            <h1 className="font-bold text-[#F8FAFC] tracking-tight leading-none">AORTA</h1>
            <p className="text-[10px] text-[#06B6D4] font-mono tracking-wider uppercase mt-1">Workspace alpha-9</p>
          </div>
        </div>

        <div className="p-4 space-y-4 border-b border-[#334155]">
          <h2 className="text-xs font-mono text-[#94A3B8] uppercase tracking-wider mb-2">Ingestion Engine</h2>
          <div className="grid grid-cols-2 gap-2">
            <Button variant="outline" className="bg-[#0F172A] border-[#334155] hover:border-[#06B6D4] hover:bg-[#06B6D4]/10 text-[#94A3B8] hover:text-[#06B6D4] rounded-none h-14 flex flex-col gap-1 items-center justify-center">
              <UploadCloud className="w-4 h-4" />
              <span className="text-[10px] uppercase">Upload PDF</span>
            </Button>
            <Button variant="outline" className="bg-[#0F172A] border-[#334155] hover:border-[#06B6D4] hover:bg-[#06B6D4]/10 text-[#94A3B8] hover:text-[#06B6D4] rounded-none h-14 flex flex-col gap-1 items-center justify-center">
              <Search className="w-4 h-4" />
              <span className="text-[10px] uppercase">PubMed ID</span>
            </Button>
          </div>
        </div>

        <div className="flex-1 flex flex-col min-h-0">
          <div className="px-4 py-3 border-b border-[#334155] flex justify-between items-center">
            <h2 className="text-xs font-mono text-[#94A3B8] uppercase tracking-wider">Analysis History</h2>
            <Badge variant="outline" className="text-[9px] border-[#06B6D4] text-[#06B6D4] rounded-none px-1 py-0">12 TOTAL</Badge>
          </div>
          
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-1">
              {[
                { id: "PMID: 3459102", title: "EGFR mutations in non-small-cell lung cancer", status: "complete", date: "10:42 AM" },
                { id: "PDF-84920", title: "Novel kinase inhibitors screening assay", status: "complete", date: "Yesterday" },
                { id: "PMID: 2984013", title: "Pathway analysis of Erlotinib resistance", status: "processing", date: "Yesterday" },
                { id: "TXT-RAW-9", title: "Lab notes: Compound screening batch 4", status: "failed", date: "Oct 12" },
                { id: "PMID: 1102941", title: "Target identification via mass spec", status: "complete", date: "Oct 10" },
              ].map((item, i) => (
                <button 
                  key={i} 
                  className={`w-full text-left p-3 flex flex-col gap-1 rounded-none border-l-2 transition-colors ${i === 0 ? 'bg-[#0F172A] border-[#06B6D4]' : 'border-transparent hover:bg-[#0F172A] hover:border-[#334155]'}`}
                >
                  <div className="flex justify-between items-center w-full">
                    <span className="text-xs font-mono text-[#06B6D4]">{item.id}</span>
                    <span className="text-[9px] text-[#94A3B8]">{item.date}</span>
                  </div>
                  <span className="text-sm text-[#F8FAFC] truncate">{item.title}</span>
                  <div className="flex items-center gap-2 mt-1">
                    {item.status === 'complete' && <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.8)]" />}
                    {item.status === 'processing' && <div className="w-1.5 h-1.5 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.8)] animate-pulse" />}
                    {item.status === 'failed' && <div className="w-1.5 h-1.5 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]" />}
                    <span className="text-[10px] text-[#94A3B8] uppercase">{item.status}</span>
                  </div>
                </button>
              ))}
            </div>
          </ScrollArea>
        </div>
        
        <div className="p-4 border-t border-[#334155] flex items-center justify-between text-[#94A3B8] hover:text-[#F8FAFC] cursor-pointer">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-none bg-[#0F172A] border border-[#334155] flex items-center justify-center">
              <User className="w-4 h-4" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium">Dr. J. Mercer</span>
              <span className="text-[10px] font-mono">SYS.ADMIN</span>
            </div>
          </div>
          <Settings className="w-4 h-4" />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* Top Header */}
        <header className="h-16 border-b border-[#334155] flex items-center px-6 justify-between shrink-0 bg-[#0F172A]/80 backdrop-blur-md">
          <div className="flex items-center gap-4">
            <Badge variant="outline" className="border-[#06B6D4] text-[#06B6D4] bg-[#06B6D4]/10 rounded-none font-mono">
              <Activity className="w-3 h-3 mr-1" />
              ANALYSIS ACTIVE
            </Badge>
            <h2 className="text-lg font-medium text-[#F8FAFC] flex items-center gap-2">
              <FileText className="w-4 h-4 text-[#94A3B8]" />
              EGFR mutations in non-small-cell lung cancer
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" size="sm" className="bg-[#1E293B] border-[#334155] rounded-none hover:text-[#06B6D4] hover:border-[#06B6D4]">
              <Network className="w-4 h-4 mr-2" /> Export Graph
            </Button>
            <Button size="sm" className="bg-[#06B6D4] hover:bg-[#0891B2] text-[#0F172A] rounded-none font-bold">
              Generate Report
            </Button>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden">
          {/* Main Visual/Data Area */}
          <div className="flex-1 flex flex-col p-6 gap-6 overflow-y-auto">
            
            {/* Entity Stats Row */}
            <div className="grid grid-cols-4 gap-4 shrink-0">
              <StatCard title="Targets Identified" value="14" icon={<GitBranch className="w-4 h-4" />} highlight="EGFR, HER2" />
              <StatCard title="Compounds Found" value="8" icon={<FlaskConical className="w-4 h-4" />} highlight="Erlotinib, Gefitinib" />
              <StatCard title="Assays Extracted" value="23" icon={<Activity className="w-4 h-4" />} highlight="Kinase Inhibition, IC50" />
              <StatCard title="Pathways Mapped" value="3" icon={<Network className="w-4 h-4" />} highlight="MAPK/ERK, PI3K/AKT" />
            </div>

            {/* Ontology Graph Visualization */}
            <Card className="flex-1 min-h-[400px] bg-[#1E293B] border-[#334155] rounded-none flex flex-col relative overflow-hidden group">
              <div className="absolute top-4 left-4 z-10 flex items-center gap-2">
                <Badge variant="outline" className="bg-[#0F172A] border-[#334155] text-[#F8FAFC] rounded-none font-mono text-[10px]">
                  KNOWLEDGE GRAPH
                </Badge>
                <Badge variant="outline" className="bg-[#06B6D4]/10 border-[#06B6D4] text-[#06B6D4] rounded-none font-mono text-[10px]">
                  <Database className="w-3 h-3 mr-1" />
                  SYNCED
                </Badge>
              </div>

              {/* Fake Graph Visualization */}
              <div className="absolute inset-0 bg-[#0F172A] bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-[#1E293B] to-[#0F172A] flex items-center justify-center p-8">
                {/* Connecting lines */}
                <svg className="absolute inset-0 w-full h-full opacity-30" preserveAspectRatio="none">
                  <path d="M 40% 40% L 50% 50% L 60% 40%" stroke="#06B6D4" strokeWidth="2" fill="none" />
                  <path d="M 50% 50% L 50% 70%" stroke="#06B6D4" strokeWidth="2" fill="none" />
                  <path d="M 50% 50% L 30% 60%" stroke="#94A3B8" strokeWidth="1" strokeDasharray="4 4" fill="none" />
                  <path d="M 50% 50% L 70% 60%" stroke="#94A3B8" strokeWidth="1" strokeDasharray="4 4" fill="none" />
                </svg>

                {/* Nodes */}
                <div className="absolute top-[35%] left-[38%] translate-x-[-50%] translate-y-[-50%]">
                  <GraphNode type="compound" label="Erlotinib" value="IC50: 2nM" />
                </div>
                <div className="absolute top-[35%] left-[62%] translate-x-[-50%] translate-y-[-50%]">
                  <GraphNode type="compound" label="Gefitinib" value="IC50: 33nM" />
                </div>
                <div className="absolute top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] z-10">
                  <GraphNode type="target" label="EGFR" value="Gene: 1956" isCenter />
                </div>
                <div className="absolute top-[70%] left-[50%] translate-x-[-50%] translate-y-[-50%]">
                  <GraphNode type="pathway" label="MAPK Signaling" value="Up-regulated" />
                </div>
                <div className="absolute top-[60%] left-[30%] translate-x-[-50%] translate-y-[-50%]">
                  <GraphNode type="assay" label="Cell Proliferation" value="A549 Cell Line" />
                </div>
                <div className="absolute top-[60%] left-[70%] translate-x-[-50%] translate-y-[-50%]">
                  <GraphNode type="assay" label="Kinase Activity" value="In Vitro" />
                </div>
              </div>

              {/* Controls */}
              <div className="absolute bottom-4 right-4 flex gap-2">
                <Button size="icon" variant="outline" className="w-8 h-8 rounded-none bg-[#0F172A] border-[#334155] text-[#94A3B8] hover:text-[#06B6D4] hover:border-[#06B6D4]">
                  +
                </Button>
                <Button size="icon" variant="outline" className="w-8 h-8 rounded-none bg-[#0F172A] border-[#334155] text-[#94A3B8] hover:text-[#06B6D4] hover:border-[#06B6D4]">
                  -
                </Button>
              </div>
            </Card>
          </div>

          {/* Right Chatbot Panel */}
          <div className="w-[400px] border-l border-[#334155] bg-[#1E293B] flex flex-col shrink-0 relative shadow-[-4px_0_24px_rgba(0,0,0,0.3)]">
            <div className="h-12 border-b border-[#334155] flex items-center px-4 bg-[#0F172A]">
              <TerminalSquare className="w-4 h-4 text-[#06B6D4] mr-2" />
              <span className="font-mono text-sm text-[#F8FAFC]">GraphRAG_Terminal</span>
            </div>

            <ScrollArea className="flex-1 p-4">
              <div className="space-y-6">
                
                {/* User Message */}
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-[#06B6D4] uppercase">SYS.ADMIN</span>
                    <div className="h-[1px] flex-1 bg-[#334155]" />
                  </div>
                  <div className="bg-[#0F172A] border border-[#334155] p-3 rounded-none text-sm text-[#F8FAFC]">
                    What is the reported IC50 of Erlotinib against the L858R EGFR mutant in this study?
                  </div>
                </div>

                {/* System Message */}
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-amber-500 uppercase">AORTA_AGENT</span>
                    <div className="h-[1px] flex-1 bg-[#334155]" />
                  </div>
                  <div className="bg-[#1E293B] border-l-2 border-[#06B6D4] p-3 pl-4 rounded-none text-sm text-[#94A3B8] space-y-3">
                    <p>
                      According to the extracted assay data from <span className="text-[#F8FAFC] font-mono bg-[#0F172A] px-1 py-0.5 border border-[#334155]">PMID: 3459102</span>, Erlotinib demonstrates a potent inhibitory effect on the <span className="text-[#06B6D4]">EGFR L858R</span> mutant.
                    </p>
                    <div className="bg-[#0F172A] p-3 border border-[#334155] font-mono text-xs text-[#F8FAFC]">
                      Assay_Type: In Vitro Kinase<br/>
                      Target: EGFR [L858R]<br/>
                      Compound: Erlotinib<br/>
                      <span className="text-[#06B6D4]">Result: IC50 = 2.4 nM</span>
                    </div>
                    <div className="flex gap-2 pt-2">
                      <Badge variant="outline" className="border-[#334155] text-[#94A3B8] bg-[#0F172A] text-[10px] rounded-none hover:bg-[#334155] cursor-pointer">
                        Show Source Text
                      </Badge>
                      <Badge variant="outline" className="border-[#334155] text-[#94A3B8] bg-[#0F172A] text-[10px] rounded-none hover:bg-[#334155] cursor-pointer">
                        Locate in Graph
                      </Badge>
                    </div>
                  </div>
                </div>

              </div>
            </ScrollArea>

            <div className="p-4 bg-[#0F172A] border-t border-[#334155]">
              <div className="relative flex items-center">
                <span className="absolute left-3 text-[#06B6D4] font-mono">{'>'}</span>
                <Input 
                  placeholder="Query knowledge graph..." 
                  className="pl-8 pr-12 bg-[#1E293B] border-[#334155] rounded-none font-mono text-sm text-[#F8FAFC] placeholder:text-[#475569] focus-visible:ring-1 focus-visible:ring-[#06B6D4] h-12"
                />
                <Button size="icon" className="absolute right-1 bg-[#06B6D4] hover:bg-[#0891B2] text-[#0F172A] rounded-none h-10 w-10">
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// Subcomponents

function StatCard({ title, value, icon, highlight }: { title: string, value: string, icon: React.ReactNode, highlight: string }) {
  return (
    <Card className="bg-[#1E293B] border-[#334155] rounded-none hover:border-[#06B6D4] hover:shadow-[0_0_15px_rgba(6,182,212,0.15)] transition-all group cursor-pointer relative overflow-hidden">
      <div className="absolute top-0 right-0 w-16 h-16 bg-[#06B6D4]/5 rounded-bl-full translate-x-8 -translate-y-8 group-hover:bg-[#06B6D4]/20 transition-colors" />
      <CardContent className="p-4 flex flex-col gap-2 relative z-10">
        <div className="flex justify-between items-start">
          <span className="text-[#94A3B8] text-xs font-mono uppercase tracking-wider">{title}</span>
          <div className="text-[#475569] group-hover:text-[#06B6D4] transition-colors">
            {icon}
          </div>
        </div>
        <div className="text-3xl font-mono font-bold text-[#F8FAFC]">
          {value}
        </div>
        <div className="text-[10px] text-[#06B6D4] bg-[#06B6D4]/10 border border-[#06B6D4]/20 inline-block px-1.5 py-0.5 truncate mt-1 max-w-full">
          e.g., {highlight}
        </div>
      </CardContent>
    </Card>
  );
}

function GraphNode({ type, label, value, isCenter = false }: { type: 'compound' | 'target' | 'assay' | 'pathway', label: string, value: string, isCenter?: boolean }) {
  const colors = {
    compound: 'border-emerald-500 text-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.3)]',
    target: 'border-[#06B6D4] text-[#06B6D4] shadow-[0_0_15px_rgba(6,182,212,0.5)]',
    assay: 'border-amber-500 text-amber-500 shadow-[0_0_10px_rgba(245,158,11,0.3)]',
    pathway: 'border-purple-500 text-purple-500 shadow-[0_0_10px_rgba(168,85,247,0.3)]',
  };

  const bgColors = {
    compound: 'bg-emerald-500/10',
    target: 'bg-[#06B6D4]/20',
    assay: 'bg-amber-500/10',
    pathway: 'bg-purple-500/10',
  };

  return (
    <div className={`flex flex-col items-center gap-2 ${isCenter ? 'scale-125' : 'scale-100'} hover:scale-110 transition-transform cursor-pointer`}>
      <div className={`
        ${isCenter ? 'w-16 h-16' : 'w-12 h-12'} 
        rounded-none border-2 flex items-center justify-center
        ${colors[type]} ${bgColors[type]} backdrop-blur-sm
      `}>
        {type === 'target' && <GitBranch className={isCenter ? 'w-8 h-8' : 'w-6 h-6'} />}
        {type === 'compound' && <FlaskConical className="w-5 h-5" />}
        {type === 'assay' && <Activity className="w-5 h-5" />}
        {type === 'pathway' && <Network className="w-5 h-5" />}
      </div>
      <div className="bg-[#0F172A] border border-[#334155] px-2 py-1 rounded-none text-center shadow-lg">
        <div className="text-xs font-bold text-[#F8FAFC] whitespace-nowrap">{label}</div>
        <div className="text-[9px] font-mono text-[#94A3B8] whitespace-nowrap">{value}</div>
      </div>
    </div>
  );
}
