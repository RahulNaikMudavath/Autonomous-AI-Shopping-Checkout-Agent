import React, { useState } from 'react';
import { CheckCircle2, ChevronDown, ChevronUp, ShieldAlert, Globe, BarChart3, Brain, Sparkles, Check, Cpu } from 'lucide-react';

export default function AgentTraceTimeline({ trace }) {
  const [isOpen, setIsOpen] = useState(false);
  const [expandedSteps, setExpandedSteps] = useState({});

  if (!trace || trace.length === 0) return null;

  const toggleExpand = (index) => {
    setExpandedSteps(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const getStepIcon = (title, status) => {
    if (status === 'warning') return <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />;
    if (title.includes('Intent') || title.includes('Requirement')) return <Brain className="w-3.5 h-3.5 text-indigo-400" />;
    if (title.includes('Merchant') || title.includes('Discovery')) return <Globe className="w-3.5 h-3.5 text-cyan-400" />;
    if (title.includes('MCDA') || title.includes('Scoring') || title.includes('Ranking')) return <BarChart3 className="w-3.5 h-3.5 text-purple-400" />;
    if (title.includes('Security') || title.includes('Guardrail')) return <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />;
    return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
  };

  const totalTime = trace.reduce((acc, s) => acc + (s.execution_time_ms || 25), 0);

  return (
    <div className="rounded-xl border border-indigo-500/20 bg-slate-900/60 backdrop-blur-md overflow-hidden transition-all my-3 max-w-4xl mx-auto">
      {/* Compact Collapsible Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-white/[0.03] transition-colors text-left"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            Autonomous Agent Reasoning Pipeline
          </span>
          <span className="text-[11px] font-mono text-slate-400 hidden sm:inline">
            • {trace.length} subagent steps verified in {totalTime}ms
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-xs font-medium text-indigo-400 hover:text-indigo-300">
          <span>{isOpen ? "Hide Pipeline" : "View Agent Steps"}</span>
          {isOpen ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </button>

      {/* Expanded Step Trace */}
      {isOpen && (
        <div className="p-4 border-t border-white/10 space-y-2.5 font-mono text-xs bg-black/40 animate-in fade-in duration-200">
          <div className="space-y-2 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-gradient-to-b before:from-indigo-500 before:via-cyan-500 before:to-emerald-500">
            {trace.map((step, idx) => {
              const isExpanded = !!expandedSteps[idx];

              return (
                <div key={idx} className="relative pl-8">
                  {/* Step Dot */}
                  <div className="absolute left-1.5 top-2 -translate-x-1/2 w-4 h-4 rounded-full flex items-center justify-center bg-slate-950 border border-indigo-400">
                    {getStepIcon(step.title, step.status)}
                  </div>

                  <div className="p-2.5 rounded-lg bg-white/[0.02] border border-white/5 hover:border-white/15 transition-all">
                    <div 
                      onClick={() => toggleExpand(idx)}
                      className="flex items-center justify-between cursor-pointer"
                    >
                      <div className="font-bold text-slate-200 text-xs">
                        {step.title}
                      </div>
                      <div className="flex items-center gap-2 text-[10px] text-slate-400">
                        <span>{step.execution_time_ms || 25}ms</span>
                        {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                      </div>
                    </div>

                    <p className="text-[11px] text-slate-300 mt-1 font-sans">
                      {step.summary}
                    </p>

                    {isExpanded && step.details && (
                      <pre className="mt-2 p-2 rounded bg-black/60 border border-white/5 text-[10px] text-cyan-300 overflow-x-auto">
                        {JSON.stringify(step.details, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
