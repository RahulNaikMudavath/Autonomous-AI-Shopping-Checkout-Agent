import React from 'react';
import { ShoppingBag, X, Trash2, ArrowRight, Zap, Lock, AlertTriangle, Plus, Minus, Store } from 'lucide-react';

export default function CartDrawer({ 
  isOpen, 
  onClose, 
  cart, 
  onRemoveItem, 
  onUpdateQuantity,
  onClearCart, 
  onCheckout, 
  isProcessing = false 
}) {
  if (!isOpen) return null;

  const items = cart?.items || [];
  const itemCount = cart?.items_count ?? items.reduce((acc, it) => acc + (it.quantity || 1), 0);
  
  // Normalization for monetary values (supports Decimal string, number, or legacy inr keys)
  const subtotal = Number(cart?.subtotal ?? cart?.subtotal_inr ?? 0);
  const taxTotal = Number(cart?.tax_total ?? cart?.tax_total_inr ?? 0);
  const shippingTotal = Number(cart?.shipping_total ?? cart?.shipping_total_inr ?? 0);
  const discountTotal = Number(cart?.discount_total ?? cart?.discount_total_inr ?? 0);
  const grandTotal = Number(cart?.grand_total ?? cart?.grand_total_inr ?? (subtotal - discountTotal + shippingTotal + taxTotal));
  const merchantCode = cart?.merchant_code || 'MULTI_MERCHANT';
  const merchantName = cart?.merchant_name || cart?.merchant_code || 'Merchant';
  const warnings = cart?.warnings || [];
  const isStale = cart?.is_stale || false;

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
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white font-heading">
                      Shopping Cart
                    </h3>
                    {merchantCode && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                        {merchantCode}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 font-mono">
                    {itemCount} item(s) • Server Authoritative
                  </p>
                </div>
              </div>

              <button 
                onClick={onClose}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
                title="Close Cart"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Warnings / Staleness Notice */}
            {(isStale || warnings.length > 0) && (
              <div className="mt-3 p-3 rounded-lg bg-amber-950/40 border border-amber-500/30 text-amber-300 text-xs space-y-1">
                <div className="flex items-center gap-1.5 font-semibold">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>Cart Notice (Live Catalog Updates)</span>
                </div>
                {warnings.map((w, i) => (
                  <p key={i} className="text-[11px] text-amber-200/90 pl-5">• {w}</p>
                ))}
              </div>
            )}

            {/* Cart Items List */}
            <div className="mt-4 space-y-3 max-h-[48vh] overflow-y-auto pr-1">
              {items.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500 space-y-2">
                  <ShoppingBag className="w-8 h-8 mx-auto opacity-30" />
                  <p>Your shopping cart is currently empty.</p>
                </div>
              ) : (
                items.map((item, idx) => {
                  const title = item.product_title || item.product?.title || 'Product';
                  const unitPrice = Number(item.unit_price ?? item.unit_price_inr ?? item.product?.current_price ?? 0);
                  const totalPrice = Number(item.total_price ?? item.total_price_inr ?? (unitPrice * (item.quantity || 1)));
                  const itemId = item.id || item.product_id || item.product?.id;
                  const itemMerchant = item.product?.merchant_name || item.merchant_name || merchantName;

                  return (
                    <div 
                      key={item.id || idx}
                      className="p-3.5 rounded-xl bg-white/[0.03] border border-white/5 flex items-start justify-between gap-3 text-xs"
                    >
                      <div className="space-y-1.5 flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="text-[10px] text-cyan-400 font-semibold uppercase flex items-center gap-1">
                            <Store className="w-3 h-3" />
                            {itemMerchant}
                          </span>
                          {item.is_available === false && (
                            <span className="px-1.5 py-0.2 rounded text-[9px] bg-rose-500/20 text-rose-300 border border-rose-500/30">
                              Unavailable
                            </span>
                          )}
                        </div>
                        <h4 className="font-bold text-white line-clamp-1" title={title}>{title}</h4>
                        <div className="text-[11px] text-slate-400 font-mono">
                          ₹{unitPrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })} each
                        </div>

                        {/* Quantity Controls */}
                        <div className="flex items-center gap-2 pt-1">
                          <div className="inline-flex items-center rounded-lg bg-slate-800 border border-slate-700 p-0.5">
                            <button
                              onClick={() => onUpdateQuantity && onUpdateQuantity(item, (item.quantity || 1) - 1)}
                              disabled={isProcessing}
                              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-700 disabled:opacity-40 transition-colors"
                              title="Decrease quantity"
                            >
                              <Minus className="w-3 h-3" />
                            </button>
                            <span className="px-2.5 text-xs font-mono font-bold text-white min-w-[20px] text-center">
                              {item.quantity || 1}
                            </span>
                            <button
                              onClick={() => onUpdateQuantity && onUpdateQuantity(item, (item.quantity || 1) + 1)}
                              disabled={isProcessing || (item.available_quantity !== undefined && item.available_quantity !== null && item.quantity >= item.available_quantity)}
                              className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-700 disabled:opacity-40 transition-colors"
                              title="Increase quantity"
                            >
                              <Plus className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      </div>

                      <div className="text-right space-y-1.5 shrink-0 flex flex-col items-end justify-between self-stretch">
                        <div className="font-mono font-bold text-white text-sm">
                          ₹{totalPrice.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                        <button 
                          onClick={() => onRemoveItem(itemId)}
                          disabled={isProcessing}
                          className="text-rose-400 hover:text-rose-300 p-1 rounded hover:bg-rose-500/10 transition-colors"
                          title="Remove item from cart"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Footer & Checkout Summary */}
          {items.length > 0 && (
            <div className="pt-4 border-t border-white/10 space-y-3 text-xs">
              <div className="space-y-1.5 text-slate-400">
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span className="font-mono text-white">₹{subtotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                {shippingTotal > 0 && (
                  <div className="flex justify-between">
                    <span>Shipping:</span>
                    <span className="font-mono text-white">₹{shippingTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span>GST (18%):</span>
                  <span className="font-mono text-white">₹{taxTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                </div>
                {discountTotal > 0 && (
                  <div className="flex justify-between text-emerald-400 font-medium">
                    <span>Promotional Discount:</span>
                    <span className="font-mono">-₹{discountTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
                  </div>
                )}
                <div className="flex justify-between text-sm font-bold text-white pt-2 border-t border-white/10">
                  <span>Grand Total:</span>
                  <span className="font-mono text-emerald-400 text-base">
                    ₹{grandTotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </span>
                </div>
              </div>

              <div className="p-2.5 rounded-lg bg-indigo-950/40 border border-indigo-500/20 text-[11px] text-indigo-200 flex items-center gap-2">
                <Lock className="w-3.5 h-3.5 text-indigo-400 shrink-0" />
                <span>Protected by Server-Authoritative Integrity &amp; Strict Merchant Isolation</span>
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
                  disabled={isProcessing}
                  className="w-full text-center text-[11px] text-slate-500 hover:text-slate-400 py-1 disabled:opacity-40 transition-colors"
                >
                  Clear Entire Cart
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
