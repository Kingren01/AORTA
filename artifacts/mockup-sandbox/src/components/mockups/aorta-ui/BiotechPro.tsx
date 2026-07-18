import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { 
  Activity, 
  Bot, 
  ChevronRight, 
  Dna, 
  Download, 
  FileText, 
  Link2, 
  Maximize2, 
  MessageSquare, 
  PlusCircle, 
  Search, 
  Send, 
  Settings, 
  Share2, 
  Upload, 
  ZoomIn 
} from 'lucide-react';

export default function BiotechPro() {
  const [view, setView] = useState<'login' | 'app'>('login');

  return (
    <div className="min-h-screen flex flex-col font-sans bg-[#0A1628] text-[#E2E8F0] selection:bg-[#F59E0B]/30">
      <div className="p-2 border-b border-[#1E3A5F] bg-[#0F2040] flex justify-center z-50 shrink-0">
        <div className="inline-flex bg-[#0A1628] p-1 rounded-lg border border-[#1E3A5F]">
          <button 
            onClick={() => setView('login')}
            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${view === 'login' ? 'bg-[#F59E0B] text-white' : 'text-[#94A3B8] hover:text-[#E2E8F0]'}`}
          >
            Login View
          </button>
          <button 
            onClick={() => setView('app')}
            className={`px-4 py-1.5 text-sm font-medium rounded-md transition-colors ${view === 'app' ? 'bg-[#F59E0B] text-white' : 'text-[#94A3B8] hover:text-[#E2E8F0]'}`}
          >
            App View
          </button>
        </div>
      </div>

      {view === 'login' ? <LoginView onLogin={() => setView('app')} /> : <AppView />}
    </div>
  );
}

function LoginView({ onLogin }: { onLogin: () => void }) {
  return (
    <div className="flex-1 flex items-center justify-center relative overflow-hidden bg-[#0A1628]">
      {/* Decorative background elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-[#10B981]/5 blur-[120px]" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-[#F59E0B]/10 blur-[120px]" />
      
      <div className="w-full max-w-md z-10 p-6">
        <div className="flex flex-col items-center mb-8">
          <div className="relative w-20 h-20 mb-6 flex items-center justify-center rounded-2xl bg-[#0F2040] border border-[#1E3A5F] shadow-[0_0_40px_rgba(245,158,11,0.15)] group">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-[#F59E0B]/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <Dna className="w-10 h-10 text-[#F59E0B] animate-[spin_10s_linear_infinite]" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-[#E2E8F0] mb-2 flex items-center gap-2">
            AORTA
          </h1>
          <p className="text-center text-[#94A3B8] text-sm max-w-xs leading-relaxed">
            Assay Ontology & Retrieval <span className="text-[#FDE68A]">Translation App</span>
          </p>
        </div>

        <Card className="bg-[#0F2040]/80 backdrop-blur-xl border-[#1E3A5F] shadow-2xl rounded-xl">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-xl font-semibold text-[#E2E8F0]">Sign in</CardTitle>
            <CardDescription className="text-[#94A3B8]">
              Enter your credentials to access the knowledge graph.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">Work Email</label>
              <Input 
                type="email" 
                placeholder="scientist@institute.edu" 
                className="bg-[#0A1628] border-[#1E3A5F] text-[#E2E8F0] placeholder:text-[#1E3A5F] focus-visible:ring-[#F59E0B] focus-visible:ring-1 focus-visible:border-[#F59E0B] h-11 rounded-md"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider">Password</label>
                <a href="#" className="text-xs text-[#F59E0B] hover:text-[#FDE68A] transition-colors">Forgot password?</a>
              </div>
              <Input 
                type="password" 
                placeholder="••••••••" 
                className="bg-[#0A1628] border-[#1E3A5F] text-[#E2E8F0] placeholder:text-[#1E3A5F] focus-visible:ring-[#F59E0B] focus-visible:ring-1 focus-visible:border-[#F59E0B] h-11 rounded-md"
              />
            </div>
          </CardContent>
          <CardFooter className="pt-2 pb-6">
            <Button 
              onClick={onLogin}
              className="w-full bg-[#F59E0B] hover:bg-[#D97706] text-white shadow-[0_0_20px_rgba(245,158,11,0.2)] h-11 rounded-md font-medium text-base transition-all border-0"
            >
              Sign In to Platform
              <ChevronRight className="w-4 h-4 ml-2" />
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}

function AppView() {
  return (
    <div className="flex-1 flex overflow-hidden bg-[#0A1628]">
      {/* Sidebar */}
      <div className="w-72 bg-[#0F2040] border-r border-[#1E3A5F] flex flex-col shrink-0">
        {/* Header */}
        <div className="h-16 flex items-center px-4 border-b border-[#1E3A5F] shrink-0">
          <div className="flex items-center gap-2 text-[#FDE68A] font-bold text-lg tracking-tight">
            <Dna className="w-5 h-5 text-[#F59E0B]" />
            AORTA
          </div>
        </div>

        <div className="p-4 border-b border-[#1E3A5F] space-y-3 shrink-0">
          <Button className="w-full bg-[#F59E0B]/10 hover:bg-[#F59E0B]/20 text-[#F59E0B] border border-[#F59E0B]/30 justify-start h-10 rounded-md">
            <PlusCircle className="w-4 h-4 mr-2" />
            New Extraction
          </Button>
          
          <div className="grid grid-cols-3 gap-2">
            <button className="flex flex-col items-center justify-center p-2 rounded-md bg-[#0A1628] border border-[#1E3A5F] hover:border-[#F59E0B]/50 hover:bg-[#F59E0B]/5 transition-colors group">
              <Search className="w-4 h-4 text-[#94A3B8] group-hover:text-[#F59E0B] mb-1 transition-colors" />
              <span className="text-[10px] text-[#94A3B8] group-hover:text-[#F59E0B] uppercase tracking-wider font-medium transition-colors">PubMed</span>
            </button>
            <button className="flex flex-col items-center justify-center p-2 rounded-md bg-[#0A1628] border border-[#1E3A5F] hover:border-[#F59E0B]/50 hover:bg-[#F59E0B]/5 transition-colors group">
              <Upload className="w-4 h-4 text-[#94A3B8] group-hover:text-[#F59E0B] mb-1 transition-colors" />
              <span className="text-[10px] text-[#94A3B8] group-hover:text-[#F59E0B] uppercase tracking-wider font-medium transition-colors">Upload</span>
            </button>
            <button className="flex flex-col items-center justify-center p-2 rounded-md bg-[#0A1628] border border-[#1E3A5F] hover:border-[#F59E0B]/50 hover:bg-[#F59E0B]/5 transition-colors group">
              <FileText className="w-4 h-4 text-[#94A3B8] group-hover:text-[#F59E0B] mb-1 transition-colors" />
              <span className="text-[10px] text-[#94A3B8] group-hover:text-[#F59E0B] uppercase tracking-wider font-medium transition-colors">Paste</span>
            </button>
          </div>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-4 space-y-4">
            <div>
              <h4 className="text-xs font-medium text-[#94A3B8] uppercase tracking-wider mb-2">Recent Sessions</h4>
              <div className="space-y-1">
                {[
                  "EGFR Inhibitors & Lung Cancer",
                  "CRISPR-Cas9 Off-target Effects",
                  "PARP Inhibitor Resistance",
                  "Mesenchymal Stem Cell Assays"
                ].map((item, i) => (
                  <button key={i} className="w-full text-left px-3 py-2 rounded-md text-sm text-[#E2E8F0] hover:bg-[#0A1628] hover:text-[#FDE68A] transition-colors truncate flex items-center gap-2 group">
                    <MessageSquare className="w-3 h-3 text-[#1E3A5F] group-hover:text-[#F59E0B] transition-colors shrink-0" />
                    <span className="truncate">{item}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </ScrollArea>
        
        {/* User Profile */}
        <div className="p-4 border-t border-[#1E3A5F] flex items-center gap-3 bg-[#0F2040] shrink-0">
          <Avatar className="w-8 h-8 rounded-md bg-[#0A1628] border border-[#1E3A5F]">
            <AvatarFallback className="bg-[#1E3A5F] text-[#E2E8F0] rounded-md text-xs font-semibold">SC</AvatarFallback>
          </Avatar>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-[#E2E8F0] truncate">Dr. Sarah Chen</p>
            <p className="text-xs text-[#94A3B8] truncate">Lead Researcher</p>
          </div>
          <button className="text-[#94A3B8] hover:text-[#E2E8F0] transition-colors">
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        {/* Topbar */}
        <header className="h-16 flex items-center justify-between px-6 border-b border-[#1E3A5F] bg-[#0F2040]/50 backdrop-blur-sm shrink-0">
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="border-[#10B981]/30 text-[#10B981] bg-[#10B981]/10 uppercase tracking-wider text-[10px] font-semibold rounded-sm py-0.5">Active Source</Badge>
            <h2 className="text-lg font-medium text-[#E2E8F0] truncate max-w-xl">PMID: 34567890 — "Efficacy of Erlotinib in EGFR-mutated NSCLC"</h2>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="h-8 border-[#1E3A5F] bg-[#0F2040] text-[#94A3B8] hover:text-[#E2E8F0] hover:bg-[#0A1628] rounded-md">
              <Download className="w-3 h-3 mr-2" />
              Export
            </Button>
            <Button variant="outline" size="sm" className="h-8 border-[#1E3A5F] bg-[#0F2040] text-[#94A3B8] hover:text-[#E2E8F0] hover:bg-[#0A1628] rounded-md">
              <Share2 className="w-3 h-3 mr-2" />
              Share
            </Button>
          </div>
        </header>

        <div className="flex-1 overflow-hidden flex flex-col lg:flex-row p-4 gap-4">
          {/* Left Column: Entities & Graph */}
          <div className="flex-1 flex flex-col min-w-0 gap-4 h-full">
            
            {/* Extracted Entities */}
            <div className="bg-[#0F2040] border border-[#1E3A5F] rounded-lg p-4 flex flex-col shrink-0 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-[#FDE68A] flex items-center gap-2">
                  <Activity className="w-4 h-4 text-[#F59E0B]" />
                  Extracted Entities
                </h3>
                <Badge variant="secondary" className="bg-[#0A1628] text-[#94A3B8] border border-[#1E3A5F] hover:bg-[#0A1628] rounded-md text-xs font-medium">24 Found</Badge>
              </div>
              
              <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
                {/* Compound Card */}
                <div className="bg-[#0A1628] border border-[#1E3A5F] rounded-md p-3 relative overflow-hidden group hover:border-[#10B981]/50 transition-colors">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#10B981]" />
                  <div className="flex justify-between items-start mb-2 pl-1">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[#10B981]">Compound</span>
                    <Badge variant="secondary" className="bg-[#10B981]/10 text-[#10B981] hover:bg-[#10B981]/20 border-0 text-[9px] px-1.5 py-0 rounded-sm">0.98 conf</Badge>
                  </div>
                  <div className="text-base font-medium text-[#E2E8F0] mb-1 pl-1">Erlotinib</div>
                  <div className="text-xs text-[#94A3B8] flex items-center gap-1 pl-1">
                    <Link2 className="w-3 h-3" /> ChEMBL101
                  </div>
                </div>

                {/* Target Card */}
                <div className="bg-[#0A1628] border border-[#1E3A5F] rounded-md p-3 relative overflow-hidden group hover:border-[#3B82F6]/50 transition-colors">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#3B82F6]" />
                  <div className="flex justify-between items-start mb-2 pl-1">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[#3B82F6]">Target</span>
                    <Badge variant="secondary" className="bg-[#3B82F6]/10 text-[#3B82F6] hover:bg-[#3B82F6]/20 border-0 text-[9px] px-1.5 py-0 rounded-sm">0.99 conf</Badge>
                  </div>
                  <div className="text-base font-medium text-[#E2E8F0] mb-1 pl-1">EGFR</div>
                  <div className="text-xs text-[#94A3B8] flex items-center gap-1 pl-1">
                    <Link2 className="w-3 h-3" /> ENSG00000146648
                  </div>
                </div>

                {/* Assay Card */}
                <div className="bg-[#0A1628] border border-[#1E3A5F] rounded-md p-3 relative overflow-hidden group hover:border-[#F59E0B]/50 transition-colors">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#F59E0B]" />
                  <div className="flex justify-between items-start mb-2 pl-1">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[#F59E0B]">Assay</span>
                    <Badge variant="secondary" className="bg-[#F59E0B]/10 text-[#F59E0B] hover:bg-[#F59E0B]/20 border-0 text-[9px] px-1.5 py-0 rounded-sm">0.92 conf</Badge>
                  </div>
                  <div className="text-base font-medium text-[#E2E8F0] mb-1 pl-1">Kinase Inhibition</div>
                  <div className="text-xs text-[#94A3B8] flex items-center gap-1 pl-1">
                    <Link2 className="w-3 h-3" /> IC50 = 2.0 nM
                  </div>
                </div>

                {/* Disease Card */}
                <div className="bg-[#0A1628] border border-[#1E3A5F] rounded-md p-3 relative overflow-hidden group hover:border-[#EC4899]/50 transition-colors">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#EC4899]" />
                  <div className="flex justify-between items-start mb-2 pl-1">
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-[#EC4899]">Disease</span>
                    <Badge variant="secondary" className="bg-[#EC4899]/10 text-[#EC4899] hover:bg-[#EC4899]/20 border-0 text-[9px] px-1.5 py-0 rounded-sm">0.95 conf</Badge>
                  </div>
                  <div className="text-base font-medium text-[#E2E8F0] mb-1 pl-1">NSCLC</div>
                  <div className="text-xs text-[#94A3B8] flex items-center gap-1 pl-1">
                    <Link2 className="w-3 h-3" /> MONDO:0005233
                  </div>
                </div>
              </div>
            </div>

            {/* Ontology Graph View */}
            <div className="flex-1 bg-[#0F2040] border border-[#1E3A5F] rounded-lg overflow-hidden flex flex-col relative min-h-0 shadow-sm">
              <div className="absolute top-4 left-4 z-10 flex gap-2">
                <h3 className="text-sm font-semibold text-[#FDE68A] bg-[#0A1628]/80 backdrop-blur-md px-3 py-1.5 rounded-md border border-[#1E3A5F] flex items-center gap-2 shadow-lg">
                  <Share2 className="w-4 h-4 text-[#F59E0B]" />
                  Knowledge Graph
                </h3>
              </div>
              
              <div className="absolute top-4 right-4 z-10 flex gap-2">
                <Button variant="outline" size="icon" className="h-8 w-8 bg-[#0A1628]/80 backdrop-blur-md border-[#1E3A5F] text-[#94A3B8] hover:text-[#E2E8F0] hover:bg-[#0A1628] rounded-md">
                  <ZoomIn className="w-4 h-4" />
                </Button>
                <Button variant="outline" size="icon" className="h-8 w-8 bg-[#0A1628]/80 backdrop-blur-md border-[#1E3A5F] text-[#94A3B8] hover:text-[#E2E8F0] hover:bg-[#0A1628] rounded-md">
                  <Maximize2 className="w-4 h-4" />
                </Button>
              </div>

              {/* Placeholder Graph Background */}
              <div className="flex-1 w-full h-full relative bg-[#0A1628] overflow-hidden">
                {/* Grid lines */}
                <div className="absolute inset-0 bg-[linear-gradient(to_right,#1E3A5F20_1px,transparent_1px),linear-gradient(to_bottom,#1E3A5F20_1px,transparent_1px)] bg-[size:24px_24px]" />
                
                {/* SVG Graph Placeholder */}
                <svg className="w-full h-full absolute inset-0" viewBox="0 0 800 500" preserveAspectRatio="xMidYMid slice">
                  <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 0 L 10 5 L 0 10 z" fill="#1E3A5F" />
                    </marker>
                  </defs>
                  
                  {/* Edges */}
                  <line x1="200" y1="150" x2="400" y2="250" stroke="#1E3A5F" strokeWidth="2" markerEnd="url(#arrow)" />
                  <line x1="600" y1="150" x2="400" y2="250" stroke="#1E3A5F" strokeWidth="2" markerEnd="url(#arrow)" />
                  <line x1="400" y1="250" x2="400" y2="400" stroke="#1E3A5F" strokeWidth="2" markerEnd="url(#arrow)" />
                  
                  <text x="290" y="190" fill="#94A3B8" fontSize="12" textAnchor="middle" className="uppercase font-medium tracking-wider">inhibits</text>
                  <text x="510" y="190" fill="#94A3B8" fontSize="12" textAnchor="middle" className="uppercase font-medium tracking-wider">mutated in</text>
                  <text x="410" y="330" fill="#94A3B8" fontSize="12" className="uppercase font-medium tracking-wider">measured by</text>
                  
                  {/* Nodes */}
                  <g transform="translate(200, 150)" className="cursor-pointer hover:opacity-80 transition-opacity">
                    <circle r="30" fill="#10B981" fillOpacity="0.1" stroke="#10B981" strokeWidth="2" />
                    <text y="5" fill="#E2E8F0" fontSize="14" textAnchor="middle" fontWeight="bold">Erlotinib</text>
                  </g>
                  
                  <g transform="translate(600, 150)" className="cursor-pointer hover:opacity-80 transition-opacity">
                    <circle r="35" fill="#EC4899" fillOpacity="0.1" stroke="#EC4899" strokeWidth="2" />
                    <text y="5" fill="#E2E8F0" fontSize="14" textAnchor="middle" fontWeight="bold">NSCLC</text>
                  </g>
                  
                  <g transform="translate(400, 250)" className="cursor-pointer hover:opacity-80 transition-opacity">
                    <circle r="35" fill="#3B82F6" fillOpacity="0.1" stroke="#3B82F6" strokeWidth="2" />
                    <text y="5" fill="#E2E8F0" fontSize="14" textAnchor="middle" fontWeight="bold">EGFR</text>
                  </g>
                  
                  <g transform="translate(400, 400)" className="cursor-pointer hover:opacity-80 transition-opacity">
                    <circle r="30" fill="#F59E0B" fillOpacity="0.1" stroke="#F59E0B" strokeWidth="2" />
                    <text y="5" fill="#E2E8F0" fontSize="12" textAnchor="middle" fontWeight="bold">IC50</text>
                  </g>
                </svg>
              </div>
            </div>
          </div>

          {/* Right Column: Chatbot */}
          <div className="w-full lg:w-96 bg-[#0F2040] border border-[#1E3A5F] rounded-lg flex flex-col shrink-0 overflow-hidden shadow-sm h-full max-h-[800px]">
            <div className="p-4 border-b border-[#1E3A5F] bg-[#0A1628]/50 flex items-center gap-3 shrink-0">
              <div className="w-8 h-8 rounded-md bg-[#F59E0B]/20 flex items-center justify-center border border-[#F59E0B]/30">
                <Bot className="w-4 h-4 text-[#F59E0B]" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-[#E2E8F0]">GraphRAG Assistant</h3>
                <p className="text-[10px] text-[#10B981] flex items-center gap-1 font-medium mt-0.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#10B981] animate-pulse" /> Online
                </p>
              </div>
            </div>

            <ScrollArea className="flex-1 p-4">
              <div className="space-y-6">
                
                {/* Assistant Message */}
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-md bg-[#1E3A5F] flex items-center justify-center shrink-0 border border-[#1E3A5F]">
                    <Bot className="w-3.5 h-3.5 text-[#E2E8F0]" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="bg-[#0A1628] border border-[#1E3A5F] rounded-lg rounded-tl-none p-3.5 text-sm text-[#E2E8F0] leading-relaxed shadow-sm">
                      I've analyzed the document. It discusses Erlotinib's efficacy against EGFR-mutated non-small cell lung cancer. Would you like to extract all kinase assay data?
                    </div>
                  </div>
                </div>

                {/* User Message */}
                <div className="flex gap-3 flex-row-reverse">
                  <Avatar className="w-7 h-7 rounded-md bg-[#F59E0B]/20 border border-[#F59E0B]/50 shrink-0">
                    <AvatarFallback className="bg-transparent text-[#F59E0B] text-[10px] font-semibold">SC</AvatarFallback>
                  </Avatar>
                  <div className="flex-1 flex justify-end">
                    <div className="bg-[#F59E0B]/10 border border-[#F59E0B]/30 rounded-lg rounded-tr-none p-3.5 text-sm text-[#FDE68A] leading-relaxed max-w-[85%] shadow-sm">
                      Yes, list the IC50 values for the T790M mutant specifically.
                    </div>
                  </div>
                </div>

                {/* Assistant Message with citation */}
                <div className="flex gap-3">
                  <div className="w-7 h-7 rounded-md bg-[#1E3A5F] flex items-center justify-center shrink-0 mt-1 border border-[#1E3A5F]">
                    <Bot className="w-3.5 h-3.5 text-[#E2E8F0]" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="bg-[#0A1628] border border-[#1E3A5F] rounded-lg rounded-tl-none p-3.5 text-sm text-[#E2E8F0] leading-relaxed shadow-sm">
                      <p className="mb-2">Found 2 relevant assay results for EGFR(T790M):</p>
                      <ul className="list-disc pl-4 space-y-1 text-[#94A3B8] mb-4">
                        <li>Erlotinib IC50 = 3,000 nM <span className="text-[10px] text-[#F59E0B] ml-1 bg-[#F59E0B]/10 px-1 py-0.5 rounded border border-[#F59E0B]/20">[1]</span></li>
                        <li>Osimertinib IC50 = 12 nM <span className="text-[10px] text-[#F59E0B] ml-1 bg-[#F59E0B]/10 px-1 py-0.5 rounded border border-[#F59E0B]/20">[1]</span></li>
                      </ul>
                      <div className="inline-flex items-center gap-1.5 bg-[#1E3A5F]/40 px-2 py-1 rounded text-xs text-[#94A3B8] border border-[#1E3A5F] hover:bg-[#1E3A5F]/60 transition-colors cursor-pointer">
                        <FileText className="w-3 h-3" /> Page 4, Table 2
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </ScrollArea>

            <div className="p-3 border-t border-[#1E3A5F] bg-[#0F2040] shrink-0">
              <div className="relative flex items-center">
                <Input 
                  placeholder="Ask about the entities or graph..." 
                  className="w-full bg-[#0A1628] border-[#1E3A5F] text-[#E2E8F0] placeholder:text-[#1E3A5F] focus-visible:ring-[#F59E0B] rounded-md pr-10 h-10"
                />
                <Button size="icon" variant="ghost" className="absolute right-1 w-8 h-8 text-[#F59E0B] hover:text-[#FDE68A] hover:bg-[#F59E0B]/10 rounded-md">
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
