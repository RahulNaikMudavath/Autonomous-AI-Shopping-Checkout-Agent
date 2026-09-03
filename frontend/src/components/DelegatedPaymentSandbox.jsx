import React, { useState, useEffect } from 'react';
import { 
  CreditCard, ShieldCheck, Zap, AlertTriangle, CheckCircle2, XCircle, 
  Lock, Key, Wallet, ArrowRight, Play, RefreshCw, Layers, Sparkles 
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const PRESET_SCENARIOS = [
  {
    id: 'groceries_850',
    title: 'Groceries: Surf Excel Matic 2L',
    category: 'groceries',
    price: 850,
    merchant_id: 'merchant-c',
    merchant_name: 'OmniStore Online',
    expected: 'AUTO_APPROVE',
    badge: '≤ ₹3,000 Auto-Approve',
    badgeColor: 'emerald'
  },
  {
    id: 'electronics_mouse',
    title: 'Electronics: Logitech MX Master 3S Mouse',
    category: 'electronics',
    price: 8995,
    merchant_id: 'merchant-b',
    merchant_name: 'ElectroBazaar',
    expected: 'AUTO_APPROVE',
    badge: '≤ ₹10,000 Auto-Approve',
    badgeColor: 'emerald'
  },
  {
    id: 'electronics_phone',
    title: 'Electronics: OnePlus Nord CE4 5G',
    category: 'electronics',
    price: 18999,
    merchant_id: 'merchant-b',
    merchant_name: 'ElectroBazaar',
    expected: 'ASK_USER',
    badge: '> ₹10,000 Requires Auth',
    badgeColor: 'amber'
  },
  {
    id: 'laptop_109k',
    title: 'High-Value: ASUS ROG Strix G16 AI Workstation',
    category: 'laptop',
    price: 109999,
    merchant_id: 'merchant-a',
    merchant_name: 'TechHub India',
    expected: 'ASK_USER',
    badge: 'Bounded Autonomy Trigger',
    badgeColor: 'amber'
  },
  {
    id: 'mac_overlimit',
    title: 'Extreme: Apple Mac Studio M2 Ultra (128GB)',
    category: 'electronics',
    price: 399000,
    merchant_id: 'merchant-a',
    merchant_name: 'TechHub India',
    expected: 'BLOCK',
    badge: 'Exceeds Ceiling (> ₹1.5L)',
    badgeColor: 'rose'
  }
];

export default function DelegatedPaymentSandbox() {
  const [wallet, setWallet] = useState([]);
  const [policy, setPolicy] = useState(null);

  // Active Test Scenario
  const [selectedScenario, setSelectedScenario] = useState(PRESET_SCENARIOS[0]);
  const [evaluationResult, setEvaluationResult] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);
  
  // Charge State
  const [chargeReceipt, setChargeReceipt] = useState(null);
  const [isCharging, setIsCharging] = useState(false);
  const [userConfirmedState, setUserConfirmedState] = useState(false);

  useEffect(() => {
    fetchInitialPaymentData();
  }, []);

  const fetchInitialPaymentData = async () => {
    try {
      const wRes = await fetch(`${API_BASE}/api/payment/wallet`);
      if (wRes.ok) setWallet(await wRes.json());

      const pRes = await fetch(`${API_BASE}/api/payment/policy`);
      if (pRes.ok) setPolicy(await pRes.json());
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunEvaluation = async (scenario, confirmed = false) => {
    setIsEvaluating(true);
    setChargeReceipt(null);
    setUserConfirmedState(confirmed);

    try {
      const res = await fetch(`${API_BASE}/api/payment/evaluate-delegated-auth`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item_title: scenario.title,
          category: scenario.category,
          price_inr: scenario.price,
          merchant_id: scenario.merchant_id,
          merchant_name: scenario.merchant_name,
          is_trusted_merchant: true,
          user_confirmed: confirmed,
          auth_pin: confirmed ? "9912" : null
        })
      });

      if (res.ok) {
        const data = await res.json();
        setEvaluationResult(data);

        // If Auto-Approved, immediately execute payment in sandbox
        if (data.action === 'AUTO_APPROVE' && data.delegated_token) {
          await executeSandboxSettlement(data.delegated_token.token_id, scenario);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsEvaluating(false);
    }
  };

  const executeSandboxSettlement = async (tokenId, scenario) => {
    setIsCharging(true);
    try {
      const res = await fetch(`${API_BASE}/api/payment/sandbox/execute-charge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          merchant_id: scenario.merchant_id,
          amount: scenario.price,
          item_title: scenario.title,
          category: scenario.category,
          delegated_token_id: tokenId,
          payment_method_id: "pm_upi_primary",
          user_confirmed: true
        })
      });

      if (res.ok) {
        setChargeReceipt(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsCharging(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header Banner */}
      <div className="glass-panel p-6 border-emerald-500/30 bg-gradient-to-r from-slate-900 via-emerald-950/30 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-emerald-600/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
            <Lock className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-heading">
              Payment Architecture &amp; Delegated Authorization
            </h2>
            <p className="text-xs text-slate-400">
              Zero raw card storage • Bounded autonomy category rules • Scoped mandate tokens
            </p>
          </div>
        </div>

        <span className="badge badge-emerald text-xs py-1 px-3 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-300" />
          Zero Raw PAN / CVV Storage Enforced
        </span>
      </div>

      {/* Tokenized Payment Wallet Vault (Zero Raw Card Numbers) */}
      <div className="glass-panel p-5 space-y-3 border-white/10">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <Wallet className="w-4 h-4 text-indigo-400" />
            User Tokenized Payment Instruments (Vault)
          </h3>
          <span className="text-[11px] text-slate-400 font-mono">
            Network Tokens / UPI Mandates Only
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {wallet.map((method) => (
            <div 
              key={method.method_id}
              className="p-3.5 rounded-xl bg-black/40 border border-white/10 space-y-2 text-xs"
            >
              <div className="flex items-center justify-between font-bold">
                <span className="text-white flex items-center gap-1.5">
                  <CreditCard className="w-3.5 h-3.5 text-cyan-400" />
                  {method.display_label.split('(')[0]}
                </span>
                {method.is_default && (
                  <span className="badge badge-indigo text-[10px] py-0">Default</span>
                )}
              </div>
              <div className="text-[11px] text-slate-400 font-mono bg-white/[0.03] p-1.5 rounded border border-white/5 truncate">
                Handle: {method.token_handle}
              </div>
              <div className="flex items-center justify-between text-[10px] text-slate-500">
                <span>Issuer: {method.issuer}</span>
                <span className="text-emerald-400">Status: {method.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bounded Autonomy Policy Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Preset Scenarios Selector */}
        <div className="glass-panel p-5 space-y-3 border-white/10">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
            Select Test Scenario
          </h3>

          <div className="space-y-2">
            {PRESET_SCENARIOS.map((sc) => (
              <button
                key={sc.id}
                onClick={() => {
                  setSelectedScenario(sc);
                  setEvaluationResult(null);
                  setChargeReceipt(null);
                }}
                className={`w-full text-left p-3 rounded-xl border text-xs transition-all ${
                  selectedScenario.id === sc.id
                    ? 'bg-indigo-950/80 border-indigo-500 text-white shadow-md ring-1 ring-indigo-400'
                    : 'bg-white/[0.02] border-white/5 text-slate-400 hover:text-white hover:border-white/15'
                }`}
              >
                <div className="flex items-center justify-between font-bold">
                  <span className="truncate pr-2">{sc.title}</span>
                  <span className="text-cyan-300 font-mono shrink-0">₹{sc.price.toLocaleString()}</span>
                </div>
                <div className="flex items-center justify-between mt-1.5 text-[10px]">
                  <span className="text-slate-500">{sc.merchant_name}</span>
                  <span className={`px-1.5 py-0.5 rounded font-mono ${
                    sc.badgeColor === 'emerald' ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30' :
                    sc.badgeColor === 'amber' ? 'bg-amber-950 text-amber-300 border border-amber-500/30' :
                    'bg-rose-950 text-rose-300 border border-rose-500/30'
                  }`}>
                    {sc.badge}
                  </span>
                </div>
              </button>
            ))}
          </div>

          <button
            onClick={() => handleRunEvaluation(selectedScenario, false)}
            disabled={isEvaluating}
            className="w-full btn-primary text-xs py-2.5 flex items-center justify-center gap-1.5 mt-3"
          >
            <Play className="w-3.5 h-3.5 fill-white" />
            {isEvaluating ? "Evaluating Rules..." : `Evaluate: ${selectedScenario.title.split(':')[0]}`}
          </button>
        </div>

        {/* Evaluation & Bounded Autonomy Decision Display */}
        <div className="lg:col-span-2 glass-panel p-5 space-y-4 border-white/10">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              Agent Bounded Autonomy Decision
            </h3>
            {evaluationResult && (
              <span className={`badge text-xs font-mono font-bold ${
                evaluationResult.action === 'AUTO_APPROVE' ? 'badge-emerald' :
                evaluationResult.action === 'ASK_USER' ? 'badge-amber' : 'badge-rose'
              }`}>
                {evaluationResult.action}
              </span>
            )}
          </div>

          {/* Scenario Details */}
          <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <div className="text-slate-500 text-[10px]">Item Title:</div>
              <div className="text-slate-200 font-bold truncate">{selectedScenario.title}</div>
            </div>
            <div>
              <div className="text-slate-500 text-[10px]">Category:</div>
              <div className="text-slate-200 font-bold uppercase">{selectedScenario.category}</div>
            </div>
            <div>
              <div className="text-slate-500 text-[10px]">Amount:</div>
              <div className="text-cyan-400 font-bold font-mono">₹{selectedScenario.price.toLocaleString()}</div>
            </div>
            <div>
              <div className="text-slate-500 text-[10px]">Merchant:</div>
              <div className="text-slate-200 font-bold truncate">{selectedScenario.merchant_name}</div>
            </div>
          </div>

          {/* Decision Outcome */}
          {evaluationResult ? (
            <div className="space-y-4 animate-in fade-in duration-200">
              {/* Decision Box */}
              <div className={`p-4 rounded-xl border space-y-2 ${
                evaluationResult.action === 'AUTO_APPROVE' 
                  ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-200' :
                evaluationResult.action === 'ASK_USER'
                  ? 'bg-amber-950/40 border-amber-500/50 text-amber-200' :
                  'bg-rose-950/40 border-rose-500/50 text-rose-200'
              }`}>
                <div className="text-sm font-bold flex items-center gap-2">
                  {evaluationResult.action === 'AUTO_APPROVE' && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                  {evaluationResult.action === 'ASK_USER' && <AlertTriangle className="w-5 h-5 text-amber-400" />}
                  {evaluationResult.action === 'BLOCK' && <XCircle className="w-5 h-5 text-rose-400" />}
                  {evaluationResult.decision_summary}
                </div>

                {/* Audit checklist */}
                <div className="text-xs space-y-1 pt-2 border-t border-white/10 font-mono">
                  {evaluationResult.audit_notes.map((note, i) => (
                    <div key={i} className="text-slate-300">{note}</div>
                  ))}
                </div>
              </div>

              {/* ACTION BUTTONS: If ASK_USER is triggered */}
              {evaluationResult.action === 'ASK_USER' && (
                <div className="p-4 rounded-xl bg-black/60 border border-amber-500/40 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-amber-300 font-bold flex items-center gap-1.5">
                      <Key className="w-4 h-4 text-amber-400" />
                      Delegated Authorization Required:
                    </span>
                    <span className="text-slate-400 text-[11px]">Human-In-The-Loop Security Gate</span>
                  </div>

                  <p className="text-xs text-slate-300">
                    Amount of <strong>₹{selectedScenario.price.toLocaleString()}</strong> exceeds category autonomous spending limit. Authorize payment agent with a single-use delegated mandate?
                  </p>

                  <div className="flex gap-2">
                    <button
                      onClick={() => handleRunEvaluation(selectedScenario, true)}
                      className="btn-primary bg-amber-600 hover:bg-amber-500 text-xs py-2 px-4 font-bold flex items-center gap-1.5 shadow-lg"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      [Authorize Purchase with PIN Token]
                    </button>
                    <button
                      onClick={() => setEvaluationResult(null)}
                      className="btn-secondary text-xs py-2 px-4"
                    >
                      [Cancel]
                    </button>
                  </div>
                </div>
              )}

              {/* Sandbox Settlement Receipt */}
              {chargeReceipt && (
                <div className="p-4 rounded-xl bg-black/80 border border-emerald-500/40 space-y-2 text-xs font-mono">
                  <div className="flex items-center justify-between text-emerald-400 font-bold">
                    <span className="flex items-center gap-1.5">
                      <CheckCircle2 className="w-4 h-4" />
                      Payment Sandbox Settlement Confirmed
                    </span>
                    <span>{chargeReceipt.status}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-300 pt-2 border-t border-white/10">
                    <div>Tx ID: <span className="text-cyan-300">{chargeReceipt.transaction_id}</span></div>
                    <div>Amount: <span className="text-emerald-300 font-bold">₹{chargeReceipt.amount.toLocaleString()}</span></div>
                    <div>Instrument: <span className="text-slate-200">{chargeReceipt.payment_method_used}</span></div>
                    <div>Delegated Mandate: <span className="text-purple-300">{chargeReceipt.delegated_token_used || 'DIRECT_MANDATE'}</span></div>
                  </div>
                  <div className="text-[10px] text-slate-500 truncate pt-1">
                    SHA-256 Audit Hash: {chargeReceipt.audit_hash}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-12 text-center text-slate-500 text-xs italic">
              Select a scenario on the left and click "Evaluate" to test Bounded Autonomy &amp; Delegated Authorizations.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
