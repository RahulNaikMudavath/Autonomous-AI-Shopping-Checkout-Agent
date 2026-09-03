import React from 'react';
import { 
  User, Brain, Calendar, ShieldCheck, Database, GitMerge, 
  Search, BarChart3, Store, ShoppingCart, FileSpreadsheet, 
  Lock, CreditCard, PackageCheck, ArrowDown, Sparkles 
} from 'lucide-react';

export default function AgentBrainMap({ activeStage = "IDLE" }) {
  const isNodeActive = (nodeName) => {
    switch (nodeName) {
      case 'USER':
        return true;
      case 'INTENT':
        return activeStage === 'PLANNING' || activeStage === 'IDLE';
      case 'PLANNER':
        return activeStage === 'PLANNING';
      case 'POLICY':
      case 'CONTEXT':
        return activeStage === 'PLANNING' || activeStage === 'DISCOVERING';
      case 'SUPERVISOR':
        return activeStage !== 'IDLE';
      case 'DISCOVERY':
        return activeStage === 'DISCOVERING';
      case 'RANKING':
        return activeStage === 'RANKING';
      case 'MERCHANT':
        return activeStage === 'NEGOTIATING';
      case 'CART':
        return activeStage === 'CART';
      case 'CHECKOUT':
        return activeStage === 'CHECKOUT';
      case 'AUTHORIZATION':
        return activeStage === 'AUTHORIZATION';
      case 'PAYMENT':
        return activeStage === 'PAYMENT';
      case 'ORDER':
        return activeStage === 'ORDER';
      default:
        return false;
    }
  };

  const getNodeClass = (nodeName, baseColor = "indigo") => {
    const active = isNodeActive(nodeName);
    if (active) {
      return `p-3 rounded-xl border transition-all duration-300 shadow-lg scale-105 bg-${baseColor}-950/80 border-${baseColor}-400 text-white shadow-[0_0_20px_rgba(99,102,241,0.35)] ring-1 ring-${baseColor}-400`;
    }
    return `p-3 rounded-xl border transition-all duration-300 bg-white/[0.02] border-white/10 text-slate-400 hover:border-white/20`;
  };

  return (
    <div className="glass-panel p-6 border-indigo-500/30 bg-slate-900/90 space-y-6">
      <div className="flex items-center justify-between pb-3 border-b border-white/10">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2 font-heading">
            <Brain className="w-5 h-5 text-indigo-400" />
            The Agent Brain: Hierarchical Multi-Agent Topology
          </h3>
          <p className="text-xs text-slate-400">
            Real-time supervisor dispatch, working memory, and stage-gated commerce pipeline
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="badge badge-indigo text-xs font-mono">
            Active Stage: {activeStage}
          </span>
        </div>
      </div>

      {/* Visual Agent Flowchart */}
      <div className="flex flex-col items-center space-y-3 text-xs max-w-2xl mx-auto">
        {/* Node 1: User */}
        <div className="flex flex-col items-center">
          <div className="p-2.5 px-4 rounded-xl bg-white/5 border border-white/10 text-slate-200 flex items-center gap-2 font-semibold">
            <User className="w-4 h-4 text-cyan-400" />
            User Prompt Input
          </div>
          <ArrowDown className="w-4 h-4 text-slate-500 my-1 animate-bounce" />
        </div>

        {/* Node 2: Intent Extractor */}
        <div className="flex flex-col items-center w-full max-w-md">
          <div className="w-full p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/40 text-indigo-200 flex items-center justify-between font-semibold shadow-md">
            <span className="flex items-center gap-2">
              <Brain className="w-4 h-4 text-indigo-400" />
              Intent Extractor
            </span>
            <span className="text-[10px] text-indigo-300 font-mono">Multi-turn Criteria</span>
          </div>
          <ArrowDown className="w-4 h-4 text-slate-500 my-1" />
        </div>

        {/* Node 3: Task Planner */}
        <div className="flex flex-col items-center w-full max-w-md">
          <div className="w-full p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/40 text-indigo-200 flex items-center justify-between font-semibold shadow-md">
            <span className="flex items-center gap-2">
              <Calendar className="w-4 h-4 text-cyan-400" />
              Task Planner
            </span>
            <span className="text-[10px] text-cyan-300 font-mono">DAG Scheduler</span>
          </div>
          <ArrowDown className="w-4 h-4 text-slate-500 my-1" />
        </div>

        {/* Node 4: Split into Policy Engine & Context Store */}
        <div className="w-full grid grid-cols-2 gap-4">
          <div className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/40 text-amber-200 flex items-center justify-between font-semibold shadow-md">
            <span className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              Policy Engine
            </span>
            <span className="text-[10px] text-amber-300 font-mono">Kernel Caps</span>
          </div>

          <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-500/40 text-cyan-200 flex items-center justify-between font-semibold shadow-md">
            <span className="flex items-center gap-2">
              <Database className="w-4 h-4 text-cyan-400" />
              Context Store
            </span>
            <span className="text-[10px] text-cyan-300 font-mono">Working Memory</span>
          </div>
        </div>

        <ArrowDown className="w-4 h-4 text-slate-500 my-1" />

        {/* Node 5: Agent Supervisor */}
        <div className="w-full p-3.5 rounded-xl bg-gradient-to-r from-indigo-900/60 via-purple-900/60 to-indigo-900/60 border border-indigo-400 text-white flex items-center justify-between font-bold shadow-xl">
          <span className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-yellow-300" />
            Agent Supervisor (Central Orchestrator)
          </span>
          <span className="badge badge-indigo text-[10px]">Active Node</span>
        </div>

        <ArrowDown className="w-4 h-4 text-slate-500 my-1" />

        {/* Node 6: 3 Specialized Subagents in Parallel */}
        <div className="w-full grid grid-cols-3 gap-3">
          <div className="p-3 rounded-xl bg-indigo-950/30 border border-indigo-500/30 text-indigo-200 text-center space-y-1">
            <Search className="w-4 h-4 text-indigo-400 mx-auto" />
            <div className="font-bold text-[11px]">Discovery Agent</div>
            <div className="text-[9px] text-slate-400">Federated Catalog</div>
          </div>

          <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-500/30 text-purple-200 text-center space-y-1">
            <BarChart3 className="w-4 h-4 text-purple-400 mx-auto" />
            <div className="font-bold text-[11px]">Ranking Agent</div>
            <div className="text-[9px] text-slate-400">MCDA &amp; Pareto</div>
          </div>

          <div className="p-3 rounded-xl bg-cyan-950/30 border border-cyan-500/30 text-cyan-200 text-center space-y-1">
            <Store className="w-4 h-4 text-cyan-400 mx-auto" />
            <div className="font-bold text-[11px]">Merchant Agent</div>
            <div className="text-[9px] text-slate-400">Promos &amp; Terms</div>
          </div>
        </div>

        <ArrowDown className="w-4 h-4 text-slate-500 my-1" />

        {/* Stage-Gated Commerce Execution Pipeline */}
        <div className="w-full p-3.5 rounded-xl bg-black/40 border border-white/10 space-y-2">
          <div className="text-[10px] text-slate-400 font-mono text-center uppercase tracking-wider">
            Stage-Gated Commerce Execution Pipeline
          </div>
          
          <div className="grid grid-cols-5 gap-1.5 text-center text-[10px] font-semibold font-mono">
            <div className="p-2 rounded bg-white/5 text-slate-300 flex flex-col items-center gap-1">
              <ShoppingCart className="w-3.5 h-3.5 text-indigo-400" />
              <span>1. Cart</span>
            </div>

            <div className="p-2 rounded bg-white/5 text-slate-300 flex flex-col items-center gap-1">
              <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400" />
              <span>2. Checkout</span>
            </div>

            <div className="p-2 rounded bg-white/5 text-slate-300 flex flex-col items-center gap-1">
              <Lock className="w-3.5 h-3.5 text-amber-400" />
              <span>3. Auth</span>
            </div>

            <div className="p-2 rounded bg-white/5 text-slate-300 flex flex-col items-center gap-1">
              <CreditCard className="w-3.5 h-3.5 text-purple-400" />
              <span>4. Payment</span>
            </div>

            <div className="p-2 rounded bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 flex flex-col items-center gap-1">
              <PackageCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>5. Order</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
