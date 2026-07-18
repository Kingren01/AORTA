import React, { useState } from "react";
import { 
  Network, Search, FileText, Upload, Database, 
  MessageSquare, User, Send, ChevronRight, Activity, 
  FlaskConical, Dna, Settings, Menu, LogOut, 
  Bot, Hash, Paperclip, MoreHorizontal, Maximize2
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

export default function ModernClean() {
  const [view, setView] = useState<"login" | "app">("login");

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex flex-col font-sans text-[#111827]">
      {/* Mockup Toggle Bar */}
      <div className="bg-white border-b border-[#E5E7EB] p-2 flex justify-center z-50">
        <Tabs value={view} onValueChange={(v) => setView(v as "login" | "app")} className="w-[400px]">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login">Login View</TabsTrigger>
            <TabsTrigger value="app">App View</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      <div className="flex-1 flex flex-col relative overflow-hidden">
        {view === "login" && <LoginView onLogin={() => setView("app")} />}
        {view === "app" && <AppView />}
      </div>
    </div>
  );
}

function LoginView({ onLogin }: { onLogin: () => void }) {
  return (
    <div className="flex-1 flex items-center justify-center bg-[#F8FAFC] p-4">
      <Card className="w-full max-w-md shadow-xl border-[#E5E7EB] rounded-xl overflow-hidden">
        <div className="h-2 w-full bg-gradient-to-r from-[#6366F1] to-[#818CF8]" />
        <CardHeader className="space-y-4 pt-10 pb-6 text-center">
          <div className="mx-auto w-16 h-16 bg-[#EEF2FF] rounded-2xl flex items-center justify-center border border-[#E0E7FF] shadow-sm">
            <Network className="w-8 h-8 text-[#6366F1]" />
          </div>
          <div className="space-y-2">
            <CardTitle className="text-3xl font-bold tracking-tight text-[#111827]">AORTA</CardTitle>
            <CardDescription className="text-[#6B7280] font-medium text-sm max-w-[250px] mx-auto leading-relaxed">
              Assay Ontology & Retrieval Translation App
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-5 px-8">
          <div className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-[#111827]">Email</label>
              <Input 
                placeholder="scientist@institute.edu" 
                className="h-11 border-[#E5E7EB] focus-visible:ring-[#6366F1] bg-[#F8FAFC]"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium text-[#111827]">Password</label>
                <a href="#" className="text-xs text-[#6366F1] font-medium hover:underline">Forgot password?</a>
              </div>
              <Input 
                type="password" 
                placeholder="••••••••" 
                className="h-11 border-[#E5E7EB] focus-visible:ring-[#6366F1] bg-[#F8FAFC]"
              />
            </div>
          </div>
          <Button 
            className="w-full h-11 bg-gradient-to-r from-[#6366F1] to-[#4F46E5] hover:from-[#4F46E5] hover:to-[#4338CA] text-white shadow-md transition-all rounded-lg"
            onClick={onLogin}
          >
            Sign In to AORTA
          </Button>
        </CardContent>
        <CardFooter className="pb-8 pt-2 px-8 flex flex-col items-center justify-center text-center">
          <p className="text-sm text-[#6B7280]">
            Don't have an account? <a href="#" className="text-[#6366F1] font-medium hover:underline">Request access</a>
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}

function AppView() {
  return (
    <div className="flex-1 flex h-[calc(100vh-53px)] bg-[#FFFFFF]">
      {/* Sidebar */}
      <div className="w-72 flex-shrink-0 bg-[#F8FAFC] border-r border-[#E5E7EB] flex flex-col">
        <div className="p-4 border-b border-[#E5E7EB] flex items-center gap-3">
          <div className="w-8 h-8 bg-[#6366F1] rounded-lg flex items-center justify-center text-white shadow-sm">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-bold text-[#111827] text-sm leading-tight">AORTA</h2>
            <p className="text-[10px] text-[#6B7280] font-medium tracking-wide uppercase">Workspace</p>
          </div>
        </div>

        <div className="p-4 space-y-4 border-b border-[#E5E7EB]">
          <h3 className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-2">New Analysis</h3>
          <div className="grid grid-cols-3 gap-2">
            <button className="flex flex-col items-center justify-center p-3 rounded-xl bg-white border border-[#E5E7EB] hover:bg-[#EEF2FF] hover:border-[#C7D2FE] transition-colors group">
              <Search className="w-5 h-5 text-[#6B7280] group-hover:text-[#6366F1] mb-1" />
              <span className="text-[10px] font-medium text-[#111827]">PubMed</span>
            </button>
            <button className="flex flex-col items-center justify-center p-3 rounded-xl bg-white border border-[#E5E7EB] hover:bg-[#EEF2FF] hover:border-[#C7D2FE] transition-colors group">
              <Upload className="w-5 h-5 text-[#6B7280] group-hover:text-[#6366F1] mb-1" />
              <span className="text-[10px] font-medium text-[#111827]">Upload</span>
            </button>
            <button className="flex flex-col items-center justify-center p-3 rounded-xl bg-white border border-[#E5E7EB] hover:bg-[#EEF2FF] hover:border-[#C7D2FE] transition-colors group">
              <FileText className="w-5 h-5 text-[#6B7280] group-hover:text-[#6366F1] mb-1" />
              <span className="text-[10px] font-medium text-[#111827]">Paste</span>
            </button>
          </div>
        </div>

        <ScrollArea className="flex-1 px-3 py-4">
          <div className="space-y-1">
            <h3 className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider px-2 mb-2">Recent Queries</h3>
            
            <SidebarItem active icon={<Hash className="w-4 h-4" />} title="EGFR Inhibitors Review" date="2h ago" />
            <SidebarItem icon={<Hash className="w-4 h-4" />} title="Kinase Assay Profiling" date="Yesterday" />
            <SidebarItem icon={<Hash className="w-4 h-4" />} title="COVID-19 Targets" date="Oct 12" />
            <SidebarItem icon={<Hash className="w-4 h-4" />} title="JAK/STAT Pathway Analysis" date="Oct 10" />
            <SidebarItem icon={<Hash className="w-4 h-4" />} title="Novel Compound X-45" date="Oct 08" />
          </div>
        </ScrollArea>

        <div className="p-4 border-t border-[#E5E7EB]">
          <button className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-[#E2E8F0] transition-colors">
            <Avatar className="w-8 h-8">
              <AvatarImage src="https://github.com/shadcn.png" />
              <AvatarFallback>DR</AvatarFallback>
            </Avatar>
            <div className="flex-1 text-left">
              <p className="text-sm font-medium text-[#111827]">Dr. Sarah Chen</p>
              <p className="text-xs text-[#6B7280]">Biologist</p>
            </div>
            <Settings className="w-4 h-4 text-[#6B7280]" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden bg-[#FFFFFF]">
        <header className="h-14 border-b border-[#E5E7EB] flex items-center justify-between px-6 bg-white flex-shrink-0">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-[#6B7280]">Projects</span>
            <ChevronRight className="w-4 h-4 text-[#D1D5DB]" />
            <span className="text-[#6B7280]">Oncology</span>
            <ChevronRight className="w-4 h-4 text-[#D1D5DB]" />
            <span className="font-semibold text-[#111827]">EGFR Inhibitors Review</span>
          </div>
          <div className="flex items-center gap-3">
            <Badge variant="outline" className="bg-[#EEF2FF] text-[#6366F1] border-[#C7D2FE]">Analysis Complete</Badge>
            <Button variant="outline" size="sm" className="h-8 text-xs border-[#E5E7EB]">Export Report</Button>
          </div>
        </header>

        <ScrollArea className="flex-1 p-6">
          <div className="max-w-6xl mx-auto space-y-8 pb-32">
            
            {/* Top row: Document info and Quick Stats */}
            <div className="grid grid-cols-12 gap-6">
              <div className="col-span-12 lg:col-span-8">
                <Card className="h-full border-[#E5E7EB] shadow-sm rounded-xl">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-xl font-bold leading-tight">Targeting EGFR in Non-Small Cell Lung Cancer: Recent Advances</CardTitle>
                        <CardDescription className="mt-1 flex items-center gap-2">
                          <span>PMID: 34567890</span>
                          <span>•</span>
                          <span>Nature Reviews Drug Discovery, 2023</span>
                        </CardDescription>
                      </div>
                      <Button variant="ghost" size="icon" className="text-[#6B7280]"><MoreHorizontal className="w-5 h-5"/></Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-[#4B5563] leading-relaxed line-clamp-3">
                      Epidermal growth factor receptor (EGFR) is a major driver of non-small cell lung cancer (NSCLC). 
                      While first and second-generation inhibitors like erlotinib and afatinib improved outcomes, 
                      resistance invariably develops, often through the T790M mutation. Third-generation inhibitors, 
                      such as osimertinib, have transformed the treatment landscape by overcoming this resistance 
                      mechanism while sparing wild-type EGFR.
                    </p>
                    <Button variant="link" className="px-0 text-[#6366F1] h-auto mt-2">Read full abstract</Button>
                  </CardContent>
                </Card>
              </div>

              <div className="col-span-12 lg:col-span-4 grid grid-cols-2 gap-4">
                <StatCard title="Targets" count={12} icon={<Network />} color="border-l-[#6366F1]" bg="bg-[#EEF2FF]" text="text-[#6366F1]" />
                <StatCard title="Compounds" count={28} icon={<FlaskConical />} color="border-l-[#10B981]" bg="bg-[#D1FAE5]" text="text-[#10B981]" />
                <StatCard title="Assays" count={8} icon={<Activity />} color="border-l-[#F59E0B]" bg="bg-[#FEF3C7]" text="text-[#F59E0B]" />
                <StatCard title="Pathways" count={5} icon={<Dna />} color="border-l-[#8B5CF6]" bg="bg-[#EDE9FE]" text="text-[#8B5CF6]" />
              </div>
            </div>

            {/* Extracted Entities List */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-[#111827] flex items-center gap-2">
                  <Database className="w-5 h-5 text-[#6366F1]" />
                  Extracted Entities
                </h3>
                <Input placeholder="Filter entities..." className="w-64 h-9 text-sm bg-white" />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <EntityCard 
                  type="Target" 
                  name="EGFR" 
                  details="Epidermal growth factor receptor"
                  mentions={42}
                  colorClass="border-l-[#6366F1]"
                  badgeClass="bg-[#EEF2FF] text-[#6366F1]"
                />
                <EntityCard 
                  type="Compound" 
                  name="Osimertinib" 
                  details="3rd-generation TKI"
                  mentions={28}
                  colorClass="border-l-[#10B981]"
                  badgeClass="bg-[#D1FAE5] text-[#10B981]"
                />
                <EntityCard 
                  type="Compound" 
                  name="Erlotinib" 
                  details="1st-generation TKI"
                  mentions={15}
                  colorClass="border-l-[#10B981]"
                  badgeClass="bg-[#D1FAE5] text-[#10B981]"
                />
                <EntityCard 
                  type="Assay" 
                  name="Kinase Inhibition Assay" 
                  details="IC50 determination"
                  mentions={8}
                  colorClass="border-l-[#F59E0B]"
                  badgeClass="bg-[#FEF3C7] text-[#F59E0B]"
                />
                <EntityCard 
                  type="Mutation" 
                  name="T790M" 
                  details="Gatekeeper mutation"
                  mentions={31}
                  colorClass="border-l-[#EF4444]"
                  badgeClass="bg-[#FEE2E2] text-[#EF4444]"
                />
                <EntityCard 
                  type="Pathway" 
                  name="MAPK/ERK" 
                  details="Downstream signaling"
                  mentions={12}
                  colorClass="border-l-[#8B5CF6]"
                  badgeClass="bg-[#EDE9FE] text-[#8B5CF6]"
                />
              </div>
            </div>

            {/* Ontology Graph Placeholder */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-[#111827] flex items-center gap-2">
                  <Network className="w-5 h-5 text-[#6366F1]" />
                  Ontology Graph
                </h3>
                <Button variant="outline" size="sm" className="h-8 gap-2">
                  <Maximize2 className="w-4 h-4" /> Fullscreen
                </Button>
              </div>
              <div className="w-full h-80 rounded-xl border border-[#E5E7EB] bg-[#F8FAFC] relative overflow-hidden flex items-center justify-center">
                {/* Simulated Graph Vis */}
                <div className="absolute inset-0 opacity-10" 
                     style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, #6366F1 1px, transparent 0)', backgroundSize: '24px 24px' }}>
                </div>
                
                {/* Nodes */}
                <div className="relative w-full h-full max-w-2xl">
                  {/* Central Node */}
                  <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 rounded-full bg-white border-4 border-[#6366F1] shadow-lg flex items-center justify-center z-10 flex-col">
                    <span className="font-bold text-[#111827]">EGFR</span>
                    <span className="text-[10px] text-[#6B7280]">Target</span>
                  </div>
                  
                  {/* Surrounding Nodes connected by lines */}
                  <svg className="absolute inset-0 w-full h-full -z-0">
                    <line x1="50%" y1="50%" x2="25%" y2="25%" stroke="#CBD5E1" strokeWidth="2" strokeDasharray="4" />
                    <line x1="50%" y1="50%" x2="75%" y2="25%" stroke="#CBD5E1" strokeWidth="2" />
                    <line x1="50%" y1="50%" x2="25%" y2="75%" stroke="#CBD5E1" strokeWidth="2" />
                    <line x1="50%" y1="50%" x2="75%" y2="75%" stroke="#CBD5E1" strokeWidth="2" />
                  </svg>
                  
                  <div className="absolute top-[25%] left-[25%] -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-full bg-white border-2 border-[#10B981] shadow-md flex items-center justify-center flex-col">
                    <span className="font-semibold text-sm">Osimertinib</span>
                  </div>
                  <div className="absolute top-[25%] left-[75%] -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-full bg-white border-2 border-[#10B981] shadow-md flex items-center justify-center flex-col">
                    <span className="font-semibold text-sm">Erlotinib</span>
                  </div>
                  <div className="absolute top-[75%] left-[25%] -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-full bg-white border-2 border-[#EF4444] shadow-md flex items-center justify-center flex-col">
                    <span className="font-semibold text-sm">T790M</span>
                  </div>
                  <div className="absolute top-[75%] left-[75%] -translate-x-1/2 -translate-y-1/2 w-20 h-20 rounded-full bg-white border-2 border-[#F59E0B] shadow-md flex items-center justify-center text-center p-2 flex-col leading-tight">
                    <span className="font-semibold text-xs">Kinase Assay</span>
                  </div>
                </div>
              </div>
            </div>

          </div>
        </ScrollArea>

        {/* Chatbot Overlay Panel */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-3xl bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-[#E5E7EB] flex flex-col overflow-hidden z-20">
          
          <div className="bg-[#F8FAFC] border-b border-[#E5E7EB] p-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-[#6366F1] flex items-center justify-center text-white">
                <Bot className="w-3 h-3" />
              </div>
              <span className="font-semibold text-sm text-[#111827]">GraphRAG Assistant</span>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-[10px] bg-white">Context: EGFR Document</Badge>
              <Button variant="ghost" size="icon" className="w-6 h-6 rounded-full"><MoreHorizontal className="w-3 h-3" /></Button>
            </div>
          </div>

          <div className="p-4 space-y-4 max-h-[250px] overflow-y-auto bg-white">
            <div className="flex gap-3">
              <Avatar className="w-8 h-8 flex-shrink-0">
                <AvatarImage src="https://github.com/shadcn.png" />
                <AvatarFallback>U</AvatarFallback>
              </Avatar>
              <div className="bg-[#6366F1] text-white p-3 rounded-2xl rounded-tl-sm text-sm shadow-sm max-w-[85%]">
                What is the reported IC50 value for Osimertinib against the T790M mutant according to this paper?
              </div>
            </div>

            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-[#F8FAFC] border border-[#E5E7EB] flex items-center justify-center text-[#6366F1] flex-shrink-0">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-[#F8FAFC] border border-[#E5E7EB] text-[#111827] p-3 rounded-2xl rounded-tl-sm text-sm shadow-sm max-w-[85%] space-y-2">
                <p>Based on the extracted entities in this document, the reported <strong>IC50 for Osimertinib</strong> against the EGFR T790M mutant is <strong>~12 nM</strong>.</p>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="outline" className="bg-white text-xs border-[#C7D2FE] text-[#6366F1]">Source: Table 2</Badge>
                  <Badge variant="outline" className="bg-white text-xs border-[#C7D2FE] text-[#6366F1]">Entity: Kinase Assay</Badge>
                </div>
              </div>
            </div>
          </div>

          <div className="p-3 border-t border-[#E5E7EB] bg-white flex items-end gap-2">
            <Button variant="ghost" size="icon" className="flex-shrink-0 text-[#6B7280]">
              <Paperclip className="w-5 h-5" />
            </Button>
            <div className="flex-1 bg-[#F8FAFC] border border-[#E5E7EB] rounded-xl flex items-center focus-within:ring-1 focus-within:ring-[#6366F1] focus-within:border-[#6366F1] transition-all">
              <Input 
                className="border-0 bg-transparent shadow-none focus-visible:ring-0 h-10 w-full" 
                placeholder="Ask about targets, compounds, or assays..." 
              />
            </div>
            <Button className="flex-shrink-0 bg-[#6366F1] hover:bg-[#4F46E5] text-white rounded-xl w-10 h-10 p-0 flex items-center justify-center">
              <Send className="w-4 h-4 ml-0.5" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Subcomponents

function SidebarItem({ active, icon, title, date }: { active?: boolean, icon: React.ReactNode, title: string, date: string }) {
  return (
    <button className={`w-full flex items-center justify-between p-2 rounded-lg text-left transition-colors group ${active ? 'bg-[#EEF2FF] text-[#6366F1]' : 'hover:bg-[#F1F5F9] text-[#4B5563]'}`}>
      <div className="flex items-center gap-3 overflow-hidden">
        <div className={active ? "text-[#6366F1]" : "text-[#9CA3AF] group-hover:text-[#6B7280]"}>
          {icon}
        </div>
        <span className="text-sm font-medium truncate">{title}</span>
      </div>
    </button>
  );
}

function StatCard({ title, count, icon, color, bg, text }: { title: string, count: number, icon: React.ReactNode, color: string, bg: string, text: string }) {
  return (
    <Card className={`border-l-4 ${color} border-y-[#E5E7EB] border-r-[#E5E7EB] shadow-sm`}>
      <CardContent className="p-4 flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-[#6B7280] uppercase tracking-wider mb-1">{title}</p>
          <p className="text-2xl font-bold text-[#111827]">{count}</p>
        </div>
        <div className={`w-10 h-10 rounded-full ${bg} ${text} flex items-center justify-center`}>
          {React.cloneElement(icon as React.ReactElement, { className: "w-5 h-5" })}
        </div>
      </CardContent>
    </Card>
  );
}

function EntityCard({ type, name, details, mentions, colorClass, badgeClass }: { type: string, name: string, details: string, mentions: number, colorClass: string, badgeClass: string }) {
  return (
    <Card className={`border-l-4 ${colorClass} border-y-[#E5E7EB] border-r-[#E5E7EB] shadow-sm hover:shadow-md transition-shadow cursor-pointer`}>
      <CardContent className="p-4">
        <div className="flex justify-between items-start mb-2">
          <Badge className={`text-[10px] uppercase font-bold tracking-wider rounded-md border-0 ${badgeClass}`}>
            {type}
          </Badge>
          <span className="text-xs font-medium text-[#6B7280] bg-[#F3F4F6] px-2 py-0.5 rounded-full">{mentions} mentions</span>
        </div>
        <h4 className="font-bold text-[#111827] text-lg leading-tight mb-1">{name}</h4>
        <p className="text-sm text-[#6B7280] line-clamp-1">{details}</p>
      </CardContent>
    </Card>
  );
}
