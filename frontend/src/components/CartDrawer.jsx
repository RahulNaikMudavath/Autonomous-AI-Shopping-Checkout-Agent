import React from 'react';
import { ShoppingBag, X, Trash2, ShieldCheck, ArrowRight, Zap, Lock } from 'lucide-react';

export default function CartDrawer({ 
  isOpen, 
  onClose, 
  cart, 
  onRemoveItem, 
  onClearCart, 
  onCheckout, 
  isProcessing = false 
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-md glass-panel border-l border-white/10 bg-slate-900/95 p-6 flex flex-col justify-between shadow-2xl animate-in slide-in-from-right duration-300">
          {/* Header */}
          <div>
            <div className="flex items-center justify-between pb-4 border-b border-white/10">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
                  <ShoppingBag className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white font-heading">
                    Multi-Merchant Cart
                  </h3>
                  <p className="text-[11px] text-slate-400 font-mono">
                    {cart?.items?.length || 0} items aggregated
                  </p>
                </div>
              </div>

              <button 
                onClick={onClose}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Cart Items List */}
            <div className="mt-4 space-y-3 max-h-[50vh] overflow-y-auto pr-1">
              {!cart?.items || cart.items.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500 space-y-2">
                  <ShoppingBag className="w-8 h-8 mx-auto opacity-30" />
                  <p>Your multi-merchant shopping cart is empty.</p>
                </div>
              ) : (
                cart.items.map((item, idx) => (
                  <div 
                    key={idx}
                    className="p-3.5 rounded-xl bg-white/[0.03] border border-white/5 flex items-start justify-between gap-3 text-xs"
                  >
                    <div className="space-y-1">
                      <span className="text-[10px] text-cyan-400 font-semibold uppercase">
                        {item.product.merchant_name}
                      </span>
                      <h4 className="font-bold text-white line-clamp-1">{item.product.title}</h4>
                      <div className="text-[11px] text-slate-400 font-mono">
                        Qty: {item.quantity} × ₹{item.unit_price_inr.toLocaleString()}
                      </div>
                    </div>

                    <div className="text-right space-y-1 shrink-0">
                      <div className="font-mono font-bold text-white">
                        ₹{item.total_price_inr.toLocaleString()}
                      </div>
                      <button 
                        onClick={() => onRemoveItem(item.product.id)}
                        className="text-rose-400 hover:text-rose-300 p-1"
                        title="Remove item"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Footer & Checkout Summary */}
          {cart?.items && cart.items.length > 0 && (
            <div className="pt-4 border-t border-white/10 space-y-3 text-xs">
              <div className="space-y-1.5 text-slate-400">
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span className="font-mono text-white">₹{cart.subtotal_inr.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>GST (18%):</span>
                  <span className="font-mono text-white">₹{cart.tax_total_inr.toLocaleString()}</span>
                </div>
                {cart.discount_total_inr > 0 && (
                  <div className="flex justify-between text-emerald-400 font-medium">
                    <span>AI Dev Discount (5%):</span>
                    <span className="font-mono">-₹{cart.discount_total_inr.toLocaleString()}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm font-bold text-white pt-2 border-t border-white/10">
                  <span>Grand Total:</span>
                  <span className="font-mono text-emerald-400 text-base">
                    ₹{cart.grand_total_inr.toLocaleString()}
                  </span>
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-500/20 text-[11px] text-indigo-200 flex items-center gap-2">
                <Lock className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                <span>Protected by Agent Spending Policy &amp; Tokenized UPI</span>
              </div>

              <div className="space-y-2">
                <button 
                  onClick={onCheckout}
                  disabled={isProcessing}
                  className="btn-primary btn-buy-instant w-full text-xs py-3 justify-center font-bold"
                >
                  <Zap className="w-4 h-4" />
                  {isProcessing ? "Processing Checkout..." : "Proceed to Autonomous Checkout"}
                </button>

                <button 
                  onClick={onClearCart}
                  className="w-full text-center text-[11px] text-slate-500 hover:text-slate-400 py-1"
                >
                  Clear Cart
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
