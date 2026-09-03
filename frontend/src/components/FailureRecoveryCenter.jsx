import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, AlertTriangle, ShieldCheck, CheckCircle2, XCircle, 
  Play, Cpu, DollarSign, PackageX, CreditCard, Clock, RotateCcw, Link2, ArrowRight 
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const SCENARIO_CARDS = [
  {
    id: 'PRICE_CHANGED',
    title: '1. Price Changed at Checkout',
    icon: DollarSign,
    badge: 'Replanning',
    color: 'amber',
    trigger: 'Price increases from ₹99,999 → ₹104,999 at checkout.',
    recovery: 'Autonomous budget check, federated search replanning, re-ranking, and presenting optimal alternative within budget.'
  },
  {
    id: 'INVENTORY_DISAPPEARED',
    title: '2. Stock Depletion Race Condition',
    icon: PackageX,
    badge: 'SKU Swap',
    color: 'rose',
    trigger: 'Merchant A inventory drops to 0 units right before cart locking.',
    recovery: 'Federated multi-merchant discovery of equivalent 32GB/RTX 4070 spec item from Merchant C.'
  },
  {
    id: 'PAYMENT_FAILED',
    title: '3. Primary Payment Decline',
    icon: CreditCard,
    badge: 'Failover',
    color: 'emerald',
    trigger: 'Primary UPI VPA mandate declined due to issuing bank core outage.',
    recovery: 'Zero-card wallet failover to secondary Virtual Visa Token with single-use delegated mandate.'
  },
  {
    id: 'MERCHANT_API_TIMEOUT',
    title: '4. Merchant API 504 Timeout',
    icon: Clock,
    badge: 'Backoff',
    color: 'cyan',
    trigger: 'Merchant B catalog endpoint drops connection (504 Gateway Error).',
    recovery: 'Exponential backoff retries (t=200ms, 400ms, 800ms) with automatic circuit recovery.'
  },
  {
    id: 'AGENT_TOOL_CRASH',
    title: '5. Subagent Process Interruption',
    icon: Cpu,
    badge: 'Checkpoint',
    color: 'purple',
    trigger: 'Ranking worker crashes on unexpected malformed spec schema.',
    recovery: 'ContextStore working memory snapshot rollback and clean subagent respawn.'
  },
  {
    id: 'WEBHOOK_LOST',
    title: '6. Dropped Carrier Webhook',
    icon: Link2,
    badge: 'Reconcile',
    color: 'indigo',
    trigger: 'Asynchronous shipping notification lost over network.',
    recovery: 'Active state reconciliation machine polls merchant API to confirm order and carrier tracking.'
  }
];

export default function FailureRecoveryCenter() {
  const [selectedScenario, setSelectedScenario] = useState(SCENARIO_CARDS[0]);
  const [recoveryTrace, setRecoveryTrace] = useState(null);
  const [isRecovering, setIsRecovering] = useState(false);

  // Auto-run initial scenario
  useEffect(() => {
    handleRunRecovery(SCENARIO_CARDS[0].id);
  }, []);

  const handleRunRecovery = async (scenarioId) => {
    setIsRecovering(true);
    try {
      const res = await fetch(`${API_BASE}/api/resilience/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario: scenarioId,
          session_id: "session_default"
        })
      });

      if (res.ok) {
        setRecoveryTrace(await res.json());
      }
    } catch (err) {
      console.error("Recovery simulation error:", err);
    } finally {
      setIsRecovering(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 border-cyan-500/30 bg-gradient-to-r from-slate-900 via-cyan-950/40 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <RotateCcw className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-heading">
              9. Distributed Failure Recovery &amp; Resiliency
            </h2>
            <p className="text-xs text-slate-400">
              Autonomous replanning • Zero-crash failovers • State checkpoint recovery &amp; active reconciliation
            </p>
          </div>
        </div>

        <span className="badge badge-cyan text-xs py-1 px-3 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-300" />
          Self-Healing Distributed Commerce Engine Active
        </span>
      </div>

      {/* 6 Distributed Failure Scenario Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {SCENARIO_CARDS.map((scenario) => {
          const IconComponent = scenario.icon;
          const isSelected = selectedScenario.id === scenario.id;

          return (
            <div
              key={scenario.id}
              onClick={() => {
                setSelectedScenario(scenario);
                handleRunRecovery(scenario.id);
              }}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? 'bg-slate-900 border-cyan-500 ring-1 ring-cyan-400 shadow-xl'
                  : 'glass-panel border-white/5 hover:border-white/20'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-lg bg-white/5 text-cyan-400">
                    <IconComponent className="w-4 h-4" />
                  </div>
                  <span className="font-bold text-xs text-white truncate max-w-[150px]">
                    {scenario.title}
                  </span>
                </div>
                <span className="badge badge-indigo text-[10px] py-0 px-2 font-mono">
                  {scenario.badge}
                </span>
              </div>

              <div className="space-y-1 text-[11px]">
                <div className="text-rose-300 font-mono flex items-start gap-1">
                  <span className="text-rose-500 font-bold">Trigger:</span>
                  <span className="text-slate-300">{scenario.trigger}</span>
                </div>
                <div className="text-emerald-300 font-mono flex items-start gap-1 pt-1">
                  <span className="text-emerald-400 font-bold">Strategy:</span>
                  <span className="text-slate-400">{scenario.recovery}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Live Recovery Step-by-Step Trace Visualizer */}
      <div className="glass-panel p-6 border-white/10 space-y-5">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3 pb-3 border-b border-white/10">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2 font-mono">
              <RefreshCw className={`w-4 h-4 text-cyan-400 ${isRecovering ? 'animate-spin' : ''}`} />
              Live Self-Healing Execution Trace: {selectedScenario.title}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Simulates distributed fault injection and captures autonomous recovery decisions
            </p>
          </div>

          <button
            onClick={() => handleRunRecovery(selectedScenario.id)}
            disabled={isRecovering}
            className="btn-primary text-xs py-1.5 px-3.5 flex items-center gap-1.5 font-bold"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            {isRecovering ? "Simulating Recovery..." : "Re-Run Scenario"}
          </button>
        </div>

        {recoveryTrace && (
          <div className="space-y-5 animate-in fade-in duration-300">
            {/* Failure Overview Alert */}
            <div className="p-4 rounded-xl bg-slate-900/90 border border-white/10 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-rose-400 font-bold flex items-center gap-1.5 font-mono">
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  Fault Injected: {recoveryTrace.failure_title}
                </span>
                <span className="badge badge-emerald text-xs font-mono font-bold">
                  ✓ RECOVERED
                </span>
              </div>
              <div className="text-slate-300 font-mono text-[11px]">
                {recoveryTrace.failure_description}
              </div>
              <div className="text-cyan-300 font-mono text-[11px] pt-1 border-t border-white/10">
                Applied Strategy: <strong>{recoveryTrace.recovery_strategy}</strong>
              </div>
            </div>

            {/* Step-by-Step Recovery Trace Timeline */}
            <div className="space-y-3">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider font-mono">
                Recovery Pipeline Actions:
              </h4>

              <div className="space-y-2.5">
                {recoveryTrace.steps.map((step) => (
                  <div 
                    key={step.step_number} 
                    className="p-3.5 rounded-xl bg-black/40 border border-white/5 space-y-1.5 text-xs font-mono"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 rounded-full bg-white/10 text-white font-bold text-[10px] flex items-center justify-center">
                          {step.step_number}
                        </span>
                        <span className="font-bold text-white">{step.stage}</span>
                      </div>
                      <span className={`badge text-[10px] py-0 px-2 font-mono ${
                        step.status === 'COMPLETED' ? 'badge-emerald' :
                        step.status === 'FAILED' ? 'badge-rose' :
                        step.status === 'RETRYING' ? 'badge-amber' : 'badge-cyan'
                      }`}>
                        {step.status}
                      </span>
                    </div>

                    <div className="text-slate-300 pl-7 text-[11px]">
                      {step.action_taken}
                    </div>

                    {step.details && Object.keys(step.details).length > 0 && (
                      <div className="pl-7 pt-1">
                        <pre className="text-[10px] text-cyan-300 bg-black/60 p-2 rounded border border-white/5 overflow-x-auto">
                          {JSON.stringify(step.details, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Final Outcome Banner */}
            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-200 text-xs font-mono space-y-1">
              <div className="font-bold text-sm text-emerald-300 flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                Resiliency Verdict:
              </div>
              <div className="text-[11px] text-emerald-100">
                {recoveryTrace.final_outcome}
              </div>
              <div className="text-[10px] text-slate-500 pt-1 truncate">
                Audit Hash: {recoveryTrace.audit_hash}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
