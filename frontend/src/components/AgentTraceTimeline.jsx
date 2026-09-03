import React, { useState } from 'react';
import { CheckCircle2, AlertTriangle, Clock, ChevronDown, ChevronUp, Cpu, ShieldAlert, Globe, BarChart3, Brain } from 'lucide-react';

export default function AgentTraceTimeline({ trace }) {
  const [expandedSteps, setExpandedSteps] = useState({});

  if (!trace || trace.length === 0) return null;

  const toggleExpand = (index) => {
    setExpandedSteps(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const getStepIcon = (title, status) => {
    if (status === 'warning') return <ShieldAlert className="w-5 h-5 text-amber-400" />;
    if (title.includes('Intent') || title.includes('Requirement')) return <Brain className="w-5 h-5 text-indigo-400" />;
    if (title.includes('Merchant') || title.includes('Discovery')) return <Globe className="w-5 h-5 text-cyan-400" />;
    if (title.includes('MCDA') || title.includes('Scoring')) return <BarChart3 className="w-5 h-5 text-purple-400" />;
    if (title.includes('Security') || title.includes('Guardrail')) return <ShieldAlert className="w-5 h-5 text-amber-400" />;
    return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
  };

  return (
    <div className="glass-panel p-5 my-6 border border-indigo-500/20 bg-slate-900/70">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-white/10">
        <div className="flex items-center gap-2">
          <div className="live-pulse"></div>
          <h3 className="text-base font-semibold text-white font-mono flex items-center gap-2">
            <Cpu className="w-4 h-4 text-indigo-400" />
            Live Autonomous Agent Reasoning Trace
          </h3>
        </div>
        <span className="text-xs text-slate-400 font-mono bg-white/5 px-2.5 py-1 rounded">
          {trace.length} Execution Steps • {trace.reduce((acc, s) => acc + (s.execution_time_ms || 30), 0)}ms Total
        </span>
      </div>

      <div className="space-y-3 relative before:absolute before:left-4 before:top-3 before:bottom-3 before:w-0.5 before:bg-gradient-to-b before:from-indigo-500 before:via-cyan-500 before:to-emerald-500">
        {trace.map((step, idx) => {
          const isExpanded = !!expandedSteps[idx];
          const isWarning = step.status === 'warning';

          return (
            <div key={idx} className="relative pl-10">
              {/* Step Icon Anchor */}
              <div className={`absolute left-1.5 top-2.5 -translate-x-1/2 w-6 h-6 rounded-full flex items-center justify-center bg-slate-950 border ${
                isWarning ? 'border-amber-400 shadow-[0_0_10px_rgba(245,158,11,0.3)]' : 'border-indigo-400 shadow-[0_0_10px_rgba(99,102,241,0.3)]'
              }`}>
                {getStepIcon(step.title, step.status)}
              </div>

              {/* Step Card */}
              <div className={`p-3.5 rounded-lg border transition-all ${
                isWarning 
                  ? 'bg-amber-950/20 border-amber-500/30 text-amber-200' 
                  : 'bg-white/[0.03] border-white/5 hover:border-white/15 text-slate-200'
              }`}>
                <div 
                  className="flex items-center justify-between cursor-pointer"
                  onClick={() => toggleExpand(idx)}
                >
                  <div className="flex items-center gap-2 font-medium text-sm">
                    <span>{step.title}</span>
                    {isWarning && (
                      <span className="badge badge-amber text-[10px] py-0 px-2">Action Required</span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-3 text-xs text-slate-400 font-mono">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {step.execution_time_ms || 35}ms
                    </span>
                    {step.details && (
                      <button className="text-slate-400 hover:text-white p-0.5">
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                    )}
                  </div>
                </div>

                <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">
                  {step.summary}
                </p>

                {/* Collapsible Details */}
                {isExpanded && step.details && (
                  <div className="mt-3 pt-2.5 border-t border-white/10 text-xs font-mono bg-black/40 p-2.5 rounded overflow-x-auto text-cyan-300">
                    <pre>{JSON.stringify(step.details, null, 2)}</pre>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
