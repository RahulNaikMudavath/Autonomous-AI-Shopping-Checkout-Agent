import React from 'react';
import { 
  ShieldCheck, X, RefreshCw, AlertTriangle, Clock, Store, 
  CheckCircle, Lock, Truck, Tag, ArrowRight, XCircle, CheckSquare, Sparkles 
} from 'lucide-react';

export default function CheckoutQuoteModal({
  isOpen,
  onClose,
  quote,
  onRefreshQuote,
  onTransition,
  isLoading = false
}) {
  if (!isOpen || !quote) return null;

  const items = quote.items || [];
  const subtotal = Number(quote.subtotal || 0);
  const discountTotal = Number(quote.discount_total || 0);
  const shippingTotal = Number(quote.shipping_total || 0);
  const taxTotal = Number(quote.tax_total || 0);
  const grandTotal = Number(quote.grand_total || (subtotal - discountTotal + shippingTotal + taxTotal));
  const warnings = quote.warnings || [];
  const priceChanged = quote.price_changed || false;
  const isStale = quote.is_stale || false;
  const status = (quote.status || 'PENDING').toUpperCase();

  const isTerminal = ['COMPLETED', 'CANCELLED', 'EXPIRED', 'FAILED', 'INVALID'].includes(status);

  // Status Badge Styling Helper
  const getStatusBadge = (st) => {
    switch (st) {
      case 'QUOTE_VALID':
      case 'VALID':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'AUTHORIZATION_REQUIRED':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'AUTHORIZED':
        return 'bg-purple-500/20 text-purple-300 border-purple-500/40';
      case 'PAYMENT_PENDING':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      case 'PAID':
      case 'COMPLETED':
        return 'bg-emerald-600/30 text-emerald-200 border-emerald-400/50';
      case 'EXPIRED':
      case 'INVALID':
      case 'FAILED':
      case 'CANCELLED':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      default:
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto flex items-center justify-center p-4">
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal Card */}
      <div className="relative w-full max-w-2xl glass-panel bg-slate-900/95 border border-white/10 rounded-2xl p-6 sm:p-8 shadow-2xl space-y-6 animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-start justify-between border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-bold text-white font-heading">
                  Checkout State Machine
                </h3>
                <span className={`px-2.5 py-0.5 rounded text-[11px] font-mono font-bold border ${getStatusBadge(status)}`}>
                  {status}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Session / Quote ID: {quote.checkout_session_id || quote.quote_id}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
            title="Close modal"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* State Machine Lifecycle Steps */}
        <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>Lifecycle Pipeline</span>
            <span className="text-cyan-400">Server-Authoritative</span>
          </div>
          <div className="grid grid-cols-4 gap-2 text-center text-[10px] font-mono">
            <div className={`p-2 rounded-lg border ${status === 'QUOTE_CREATED' || status === 'PENDING' ? 'bg-cyan-500/20 border-cyan-400 text-cyan-200 font-bold' : 'bg-slate-800/40 border-white/5 text-slate-400'}`}>
              1. Quote Created
            </div>
            <div className={`p-2 rounded-lg border ${status === 'QUOTE_VALID' ? 'bg-emerald-500/20 border-emerald-400 text-emerald-200 font-bold' : 'bg-slate-800/40 border-white/5 text-slate-400'}`}>
              2. Quote Valid
            </div>
            <div className={`p-2 rounded-lg border ${status === 'AUTHORIZATION_REQUIRED' ? 'bg-amber-500/20 border-amber-400 text-amber-200 font-bold' : 'bg-slate-800/40 border-white/5 text-slate-400'}`}>
              3. Auth Required
            </div>
            <div className={`p-2 rounded-lg border ${status === 'AUTHORIZED' ? 'bg-purple-500/20 border-purple-400 text-purple-200 font-bold' : 'bg-slate-800/40 border-white/5 text-slate-400'}`}>
              4. Authorized
            </div>
          </div>
        </div>

        {/* Merchant & Expiration Banner */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 text-xs">
          <div className="flex items-center gap-2 text-white font-medium">
            <Store className="w-4 h-4 text-cyan-400" />
            <span>Merchant: <strong className="text-cyan-300">{quote.merchant_name} ({quote.merchant_code})</strong></span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px]">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>{isTerminal ? 'Session Terminated' : '15-Minute Bounded Window'}</span>
          </div>
        </div>

        {/* Warnings / Live Price / Staleness Notices */}
        {(priceChanged || isStale || warnings.length > 0) && (
          <div className="p-3.5 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-300 text-xs space-y-1">
            <div className="flex items-center gap-1.5 font-semibold">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>State Machine &amp; Catalog Invariant Notice</span>
            </div>
            {warnings.map((w, idx) => (
              <p key={idx} className="text-[11px] text-amber-200/90 pl-5">• {w}</p>
            ))}
          </div>
        )}

        {/* Line Items Breakdown */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
            Snapshot Line Items ({items.length})
          </h4>
          <div className="space-y-2 max-h-36 overflow-y-auto pr-1">
            {items.map((it, idx) => (
              <div 
                key={idx}
                className="p-2.5 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between gap-4 text-xs"
              >
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-white truncate">{it.product_title}</div>
                  <div className="text-[11px] text-slate-400 font-mono">
                    Qty: {it.quantity} × ₹{Number(it.unit_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                </div>
                <div className="font-mono font-bold text-white text-sm shrink-0">
                  ₹{Number(it.total_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Financial Summary */}
        <div className="p-4 rounded-xl bg-slate-950/60 border border-white/10 space-y-2 text-xs">
          <div className="flex justify-between text-slate-300">
            <span>Subtotal:</span>
            <span className="font-mono text-white">₹{subtotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
          </div>
          {shippingTotal > 0 && (
            <div className="flex justify-between text-slate-300">
              <span className="flex items-center gap-1">
                <Truck className="w-3.5 h-3.5 text-cyan-400" />
                Shipping ({quote.shipping_option?.name || 'Standard'}):
              </span>
              <span className="font-mono text-white">₹{shippingTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>
          )}
          <div className="flex justify-between text-slate-300">
            <span>GST Tax (18%):</span>
            <span className="font-mono text-white">₹{taxTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
          </div>
          {discountTotal > 0 && (
            <div className="flex justify-between text-emerald-400 font-medium">
              <span className="flex items-center gap-1">
                <Tag className="w-3.5 h-3.5" />
                Promotional Discount ({quote.applied_promo}):
              </span>
              <span className="font-mono">-₹{discountTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </div>
          )}
          <div className="flex justify-between text-sm font-bold text-white pt-2 border-t border-white/10">
            <span>Grand Total (INR):</span>
            <span className="font-mono text-emerald-400 text-base font-bold">
              ₹{grandTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
            </span>
          </div>
        </div>

        {/* State Machine Transition Trigger Bar */}
        {!isTerminal && (
          <div className="p-3 rounded-xl bg-slate-800/90 border border-cyan-500/30 flex items-center justify-between gap-3 text-xs">
            <div className="text-slate-300">
              <span className="font-semibold text-white">Next Action: </span>
              {status === 'QUOTE_CREATED' || status === 'PENDING' ? 'Validate quote with live inventory & prices' :
               status === 'QUOTE_VALID' ? 'Submit authorization request' :
               status === 'AUTHORIZATION_REQUIRED' ? 'Authorize checkout session' :
               'Session progressing through state machine'}
            </div>
            <div className="flex items-center gap-2">
              {(status === 'QUOTE_CREATED' || status === 'PENDING') && (
                <button
                  onClick={() => onTransition && onTransition('validate_quote')}
                  disabled={isLoading}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                >
                  <CheckSquare className="w-3.5 h-3.5" />
                  <span>Validate Quote</span>
                </button>
              )}
              {status === 'QUOTE_VALID' && (
                <button
                  onClick={() => onTransition && onTransition('request_authorization')}
                  disabled={isLoading}
                  className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Request Authorization</span>
                </button>
              )}
              {status === 'AUTHORIZATION_REQUIRED' && (
                <button
                  onClick={() => onTransition && onTransition('authorize')}
                  disabled={isLoading}
                  className="px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Authorize</span>
                </button>
              )}
              <button
                onClick={() => onTransition && onTransition('cancel')}
                disabled={isLoading}
                className="px-2.5 py-1.5 rounded-lg bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 border border-rose-800 text-xs font-medium transition-colors disabled:opacity-50"
                title="Cancel session"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Security & Terminal Boundary Notice */}
        <div className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-500/20 text-[11px] text-indigo-200 flex items-start gap-2">
          <Lock className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <strong>Phase 4 Step 4 Boundary:</strong> Deterministic state machine active. No payment capture or merchant order creation occurs in this phase.
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between gap-3 pt-2">
          <button
            onClick={onRefreshQuote}
            disabled={isLoading}
            className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-2 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Refresh Quote</span>
          </button>

          <button
            onClick={onClose}
            className="btn-primary text-xs py-2.5 px-6 font-bold"
          >
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
}
