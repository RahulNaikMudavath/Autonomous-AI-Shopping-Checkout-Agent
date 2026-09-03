import React, { useState } from 'react';
import { ShieldAlert, CheckCircle, XCircle, KeyRound, Lock, AlertCircle, ShoppingBag, ArrowRight } from 'lucide-react';

export default function HumanInTheLoopModal({ 
  isOpen, 
  product, 
  policyLimit = 50000, 
  onApprove, 
  onReject, 
  isProcessing = false 
}) {
  const [pin, setPin] = useState("8842");

  if (!isOpen || !product) return null;

  const handleApprove = () => {
    onApprove(product, pin);
  };

  return (
    <div className="modal-overlay">
      <div className="glass-panel max-w-lg w-full p-6 border-amber-500/40 shadow-[0_0_50px_rgba(245,158,11,0.2)] animate-in fade-in zoom-in duration-200">
        {/* Header */}
        <div className="flex items-center gap-3 pb-4 border-b border-white/10">
          <div className="w-10 h-10 rounded-full bg-amber-500/20 border border-amber-500/50 flex items-center justify-center text-amber-400 shrink-0">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white font-heading">
              Human-in-the-Loop Authorization Required
            </h3>
            <p className="text-xs text-amber-300/90 font-mono">
              Policy Rule: Single-Item Limit Exceeded (&gt; ₹{policyLimit.toLocaleString()})
            </p>
          </div>
        </div>

        {/* Item Summary */}
        <div className="my-5 p-4 rounded-xl bg-black/40 border border-white/10 space-y-3 text-xs">
          <div className="flex justify-between items-start">
            <div>
              <span className="text-[10px] text-cyan-400 font-semibold uppercase tracking-wider">
                {product.merchant_name}
              </span>
              <h4 className="text-sm font-bold text-white mt-0.5">{product.title}</h4>
              <p className="text-slate-400 text-[11px] mt-1">{product.specs.gpu} • {product.specs.ram_gb}GB RAM • {product.specs.ssd_gb}GB SSD</p>
            </div>
            <div className="text-right">
              <div className="text-lg font-bold font-mono text-emerald-400">
                ₹{product.price_inr.toLocaleString()}
              </div>
              <div className="text-[10px] text-slate-400">Incl. 18% GST</div>
            </div>
          </div>

          <div className="pt-3 border-t border-white/10 flex items-center justify-between text-slate-300">
            <span className="flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-indigo-400" />
              Payment Transport:
            </span>
            <span className="font-mono text-indigo-300 font-semibold">
              Tokenized UPI Autopay (UCP v1)
            </span>
          </div>
        </div>

        {/* Security Prompt */}
        <div className="mb-5 p-3 rounded-lg bg-amber-950/20 border border-amber-500/30 flex items-start gap-2.5 text-xs text-amber-200">
          <AlertCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <p>
            The autonomous agent has paused checkout execution to ensure you have verified this ₹{product.price_inr.toLocaleString()} high-value purchase.
          </p>
        </div>

        {/* PIN Authentication Simulation */}
        <div className="mb-6">
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <KeyRound className="w-3.5 h-3.5 text-cyan-400" />
              Security PIN / Biometric Confirmation
            </span>
            <span className="text-[10px] text-slate-500 font-mono">Demo PIN: 8842</span>
          </label>
          <input 
            type="password" 
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            className="form-input text-center font-mono tracking-widest text-lg"
            maxLength={6}
          />
        </div>

        {/* Actions */}
        <div className="grid grid-cols-2 gap-3">
          <button 
            onClick={onReject}
            disabled={isProcessing}
            className="btn-secondary text-xs py-3 justify-center"
          >
            <XCircle className="w-4 h-4 text-rose-400" />
            Reject / Cancel
          </button>

          <button 
            onClick={handleApprove}
            disabled={isProcessing}
            className="btn-primary btn-buy-instant text-xs py-3 justify-center font-bold"
          >
            {isProcessing ? (
              <span className="flex items-center gap-2">Authorizing...</span>
            ) : (
              <>
                <CheckCircle className="w-4 h-4" />
                Authorize &amp; Pay ₹{product.price_inr.toLocaleString()}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
