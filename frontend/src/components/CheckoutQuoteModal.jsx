import React from 'react';
import { ShieldCheck, X, RefreshCw, AlertTriangle, Clock, Store, CheckCircle, Lock, Truck, Tag } from 'lucide-react';

export default function CheckoutQuoteModal({
  isOpen,
  onClose,
  quote,
  onRefreshQuote,
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
                  Checkout Quote &amp; Revalidation
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  {quote.status || 'PENDING'}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Quote ID: {quote.checkout_session_id || quote.quote_id}
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

        {/* Merchant Banner */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 text-xs">
          <div className="flex items-center gap-2 text-white font-medium">
            <Store className="w-4 h-4 text-cyan-400" />
            <span>Merchant: <strong className="text-cyan-300">{quote.merchant_name} ({quote.merchant_code})</strong></span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px]">
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>Valid for 15 minutes</span>
          </div>
        </div>

        {/* Warnings / Live Price Notices */}
        {(priceChanged || warnings.length > 0) && (
          <div className="p-3.5 rounded-xl bg-amber-950/40 border border-amber-500/40 text-amber-300 text-xs space-y-1">
            <div className="flex items-center gap-1.5 font-semibold">
              <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
              <span>Live Catalog Revalidation Notice</span>
            </div>
            {warnings.map((w, idx) => (
              <p key={idx} className="text-[11px] text-amber-200/90 pl-5">• {w}</p>
            ))}
          </div>
        )}

        {/* Line Items Breakdown */}
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
            Authoritative Line Items ({items.length})
          </h4>
          <div className="space-y-2 max-h-44 overflow-y-auto pr-1">
            {items.map((it, idx) => (
              <div 
                key={idx}
                className="p-3 rounded-xl bg-white/[0.02] border border-white/5 flex items-center justify-between gap-4 text-xs"
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
            <span>Catalog Subtotal:</span>
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

        {/* Security & Terminal Boundary Notice */}
        <div className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-500/20 text-[11px] text-indigo-200 flex items-start gap-2">
          <Lock className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <div>
            <strong>Phase 4 Step 3 Scope:</strong> Pre-checkout quote is verified and immutable. Payment authorization and execution belong to Phase 4 Step 4.
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
            <span>Refresh Live Quote</span>
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
