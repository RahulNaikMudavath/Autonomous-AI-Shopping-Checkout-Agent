import React, { useState, useEffect } from 'react';
import { 
  Activity, Zap, Clock, DollarSign, Layers, Terminal, 
  CheckCircle2, AlertTriangle, ShieldCheck, Play, Flame, BarChart3, RefreshCw 
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function AgentObservabilityConsole() {
  const [traceData, setTraceData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [animatedStepIndex, setAnimatedStepIndex] = useState(9); // All visible by default
  const [isSimulating, setIsSimulating] = useState(false);

  useEffect(() => {
    fetchLatestTrace();
  }, []);

  const fetchLatestTrace = async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/observability/latest`);
      if (res.ok) {
        setTraceData(await res.json());
      }
    } catch (err) {
      console.error("Observability fetch error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunLiveTrace = () => {
    setIsSimulating(true);
    setAnimatedStepIndex(0);

    let current = 0;
    const interval = setInterval(() => {
      current += 1;
      setAnimatedStepIndex(current);
      if (current >= (traceData?.events?.length || 9)) {
        clearInterval(interval);
        setIsSimulating(false);
      }
    }, 280);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 border-emerald-500/30 bg-gradient-to-r from-slate-900 via-emerald-950/30 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-heading">
              11. Agent Observability &amp; Telemetry
            </h2>
            <p className="text-xs text-slate-400">
              Live operational trace • Waterfall execution logs • Token &amp; cost accounting • Subagent latency flamegraph
            </p>
          </div>
        </div>

        <button
          onClick={handleRunLiveTrace}
          disabled={isSimulating}
          className="btn-primary bg-emerald-600 hover:bg-emerald-500 text-xs py-2 px-4 flex items-center gap-1.5 font-bold shadow-lg"
        >
          <Play className="w-3.5 h-3.5 fill-white" />
          {isSimulating ? "Observing Run..." : "Simulate Live Agent Execution"}
        </button>
      </div>

      {/* Main Grid: Operational Metrics vs Timestamped Waterfall Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Operational Metrics Block */}
        <div className="glass-panel p-5 space-y-4 border-white/10">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <BarChart3 className="w-4 h-4 text-emerald-400" />
              Agent Execution Metrics
            </h3>
            <span className="badge badge-emerald text-[10px] py-0 px-2 font-mono">
              Live Telemetry
            </span>
          </div>

          {/* ASCII-inspired styled KPI Matrix */}
          <div className="p-4 rounded-xl bg-black/60 border border-white/10 font-mono text-xs space-y-2.5">
            <div className="text-slate-400 font-bold border-b border-white/10 pb-1 flex justify-between">
              <span>Metric</span>
              <span>Value</span>
            </div>

            <div className="flex justify-between items-center text-slate-200">
              <span className="text-slate-400">Steps</span>
              <span className="font-bold text-white bg-white/5 px-2 py-0.5 rounded">
                {traceData?.metrics?.steps || 11}
              </span>
            </div>

            <div className="flex justify-between items-center text-slate-200">
              <span className="text-slate-400">Tool Calls</span>
              <span className="font-bold text-cyan-300 bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-500/30">
                {traceData?.metrics?.tool_calls || 17}
              </span>
            </div>

            <div className="flex justify-between items-center text-slate-200">
              <span className="text-slate-400">Latency</span>
              <span className="font-bold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
                {traceData?.metrics?.latency_sec || 2.8} s
              </span>
            </div>

            <div className="flex justify-between items-center text-slate-200">
              <span className="text-slate-400">Tokens</span>
              <span className="font-bold text-purple-300 bg-purple-950/40 px-2 py-0.5 rounded border border-purple-500/30">
                {traceData?.metrics?.total_tokens?.toLocaleString() || '4,823'}
              </span>
            </div>

            <div className="flex justify-between items-center text-slate-200">
              <span className="text-slate-400">Estimated Cost</span>
              <span className="font-bold text-amber-300 bg-amber-950/40 px-2 py-0.5 rounded border border-amber-500/30">
                ${traceData?.metrics?.estimated_cost_usd?.toFixed(2) || '0.04'}
              </span>
            </div>

            <div className="flex justify-between items-center text-slate-200">
              <span className="text-slate-400">Retries</span>
              <span className="font-bold text-slate-300 bg-white/5 px-2 py-0.5 rounded">
                {traceData?.metrics?.retries ?? 1}
              </span>
            </div>

            <div className="flex justify-between items-center text-slate-200">
              <span className="text-slate-400">Policy Violations</span>
              <span className="font-bold text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-500/30">
                {traceData?.metrics?.policy_violations ?? 0}
              </span>
            </div>
          </div>

          <div className="text-[11px] text-slate-400 font-mono p-3 rounded-lg bg-black/40 border border-white/5 space-y-1">
            <div className="font-bold text-slate-300">Throughput:</div>
            <div>⚡ 1,722.5 Tokens/sec • 9 Async Tool Spans</div>
          </div>
        </div>

        {/* Right 2 Columns: Timestamped Execution Waterfall Feed */}
        <div className="lg:col-span-2 glass-panel p-5 space-y-4 border-white/10">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Terminal className="w-4 h-4 text-cyan-400" />
              Agent Execution Waterfall
            </h3>
            <span className="text-xs font-mono text-slate-400">
              Chronological Subagent Dispatch
            </span>
          </div>

          {/* Timestamped Timeline */}
          <div className="space-y-2.5 font-mono text-xs">
            {traceData?.events?.slice(0, animatedStepIndex).map((ev, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-black/50 border border-white/5 flex items-center justify-between gap-3 hover:border-white/20 transition-all animate-in fade-in slide-in-from-left-2 duration-200"
              >
                <div className="flex items-center gap-3">
                  <span className="text-slate-500 text-[11px] font-bold">
                    {ev.timestamp}
                  </span>
                  <span className="font-bold text-white min-w-[120px]">
                    {ev.agent_or_component}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className={`font-bold ${
                      ev.status_icon === '✓' ? 'text-emerald-400' : 'text-amber-400'
                    }`}>
                      {ev.status_icon}
                    </span>
                    <span className="text-slate-300 text-[11px]">
                      {ev.summary}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3 text-[10px] text-slate-500 hidden sm:flex">
                  <span>{ev.duration_ms} ms</span>
                  <span className="text-purple-400">{ev.tokens_used} tok</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Latency Flamegraph & Span Inspector */}
      {traceData?.flamegraph_spans && (
        <div className="glass-panel p-5 space-y-4 border-white/10">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Flame className="w-4 h-4 text-amber-400" />
              Subagent Latency Flamegraph (2.8s Total)
            </h3>
            <span className="text-xs font-mono text-slate-400">
              Distributed Execution Spans
            </span>
          </div>

          <div className="space-y-2.5 font-mono text-xs">
            {traceData.flamegraph_spans.map((span, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-[11px]">
                  <span className="text-slate-300 font-bold">{span.agent}</span>
                  <span className="text-slate-400">{span.ms} ms</span>
                </div>
                <div className="w-full bg-black/60 rounded-full h-3 overflow-hidden flex">
                  <div 
                    style={{ 
                      marginLeft: `${span.start_pct}%`, 
                      width: `${Math.max(4, span.width_pct)}%`,
                      backgroundColor: span.color 
                    }}
                    className="h-full rounded-full shadow-sm"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
