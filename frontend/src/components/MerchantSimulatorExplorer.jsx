import React, { useState } from 'react';
import { Store, Play, Send, CheckCircle2, Code2, ArrowRight, ShieldCheck, Tag, ShoppingCart, CreditCard, RotateCcw, Package } from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const MERCHANTS = [
  { id: 'merchant-a', name: 'Merchant A (TechHub India)', spec: 'Workstations & High-TGP GPUs', badge: 'TechHub' },
  { id: 'merchant-b', name: 'Merchant B (ElectroBazaar)', spec: 'Consumer Tech & Value Deals', badge: 'ElectroBazaar' },
  { id: 'merchant-c', name: 'Merchant C (OmniStore Online)', spec: 'Mass Retail & Extended Cover', badge: 'OmniStore' },
  { id: 'merchant-d', name: 'Merchant D (ProHardware Direct)', spec: 'Enterprise OEM & 64GB Rigs', badge: 'ProHardware' },
];

export default function MerchantSimulatorExplorer() {
  const [selectedMerchant, setSelectedMerchant] = useState('merchant-a');
  const [selectedEndpoint, setSelectedEndpoint] = useState('get_products');
  
  // Custom params
  const [productId, setProductId] = useState('prod_laptop_b_rog');
  const [cartId, setCartId] = useState('');
  const [quoteId, setQuoteId] = useState('');
  const [orderId, setOrderId] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [promoCode, setPromoCode] = useState('AI_DEVELOPER_5OFF');
  const [returnReason, setReturnReason] = useState('Upgrading to higher RAM configuration');

  const [responseOutput, setResponseOutput] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [requestUrl, setRequestUrl] = useState('');

  const handleExecute = async () => {
    setIsLoading(true);
    let url = '';
    let method = 'GET';
    let body = null;

    try {
      if (selectedEndpoint === 'get_products') {
        url = `${API_BASE}/api/merchants/${selectedMerchant}/products`;
        method = 'GET';
      } else if (selectedEndpoint === 'get_product_by_id') {
        url = `${API_BASE}/api/merchants/${selectedMerchant}/products/${productId}`;
        method = 'GET';
      } else if (selectedEndpoint === 'post_cart') {
        url = `${API_BASE}/api/merchants/${selectedMerchant}/cart`;
        method = 'POST';
        body = JSON.stringify({ product_id: productId, quantity: parseInt(quantity) || 1 });
      } else if (selectedEndpoint === 'patch_cart') {
        url = `${API_BASE}/api/merchants/${selectedMerchant}/cart/${cartId || 'cart_demo'}`;
        method = 'PATCH';
        body = JSON.stringify({ quantity: parseInt(quantity) || 2 });
      } else if (selectedEndpoint === 'post_checkout') {
        url = `${API_BASE}/api/merchants/${selectedMerchant}/checkout`;
        method = 'POST';
        body = JSON.stringify({ cart_id: cartId || 'cart_demo', promo_code: promoCode });
      } else if (selectedEndpoint === 'post_payment') {
        url = `${API_BASE}/api/merchants/${selectedMerchant}/payment`;
        method = 'POST';
        body = JSON.stringify({ quote_id: quoteId || 'quote_demo', payment_method: 'UPI_TOKEN_4829' });
      } else if (selectedEndpoint === 'get_order') {
        url = `${API_BASE}/api/merchants/${selectedMerchant}/orders/${orderId || 'ORD_DEMO'}`;
        method = 'GET';
      } else if (selectedEndpoint === 'post_return') {
        url = `${API_BASE}/api/merchants/${selectedMerchant}/returns/${orderId || 'ORD_DEMO'}`;
        method = 'POST';
        body = JSON.stringify({ reason: returnReason });
      }

      setRequestUrl(`${method} ${url}`);

      const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
      };
      if (body) options.body = body;

      const res = await fetch(url, options);
      const data = await res.json();
      setResponseOutput(data);

      // Auto-populate dependent state for seamless testing
      if (data.cart_id) setCartId(data.cart_id);
      if (data.quote_id) setQuoteId(data.quote_id);
      if (data.order_id) setOrderId(data.order_id);
      if (data.products && data.products.length > 0) setProductId(data.products[0].id);

    } catch (err) {
      setResponseOutput({ error: err.message });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header */}
      <div className="glass-panel p-6 border-cyan-500/30 bg-gradient-to-r from-slate-900 via-cyan-950/30 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <Store className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white font-heading">
              4. Merchant Simulator (Mini Marketplace)
            </h2>
            <p className="text-xs text-slate-400">
              4 standalone merchant backends each exposing the 8 standardized commerce REST endpoints
            </p>
          </div>
        </div>

        <span className="badge badge-emerald flex items-center gap-1.5 py-1 px-3">
          <span className="live-pulse"></span>
          All 4 Merchant Nodes Online
        </span>
      </div>

      {/* Merchant Selector Tabs */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {MERCHANTS.map((m) => (
          <button
            key={m.id}
            onClick={() => {
              setSelectedMerchant(m.id);
              setResponseOutput(null);
            }}
            className={`p-3.5 rounded-xl border text-left transition-all ${
              selectedMerchant === m.id
                ? 'bg-cyan-950/70 border-cyan-400 text-white shadow-[0_0_20px_rgba(6,182,212,0.3)] ring-1 ring-cyan-400'
                : 'bg-white/[0.02] border-white/10 text-slate-400 hover:border-white/20'
            }`}
          >
            <div className="text-xs font-bold text-slate-200">{m.name}</div>
            <div className="text-[10px] text-cyan-400 font-mono mt-0.5">ID: {m.id}</div>
            <div className="text-[10px] text-slate-400 mt-1 truncate">{m.spec}</div>
          </button>
        ))}
      </div>

      {/* Main Console: Endpoint Selector & Request Builder */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Endpoints List */}
        <div className="glass-panel p-5 space-y-2 border-white/10">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">
            8 Commerce REST Endpoints
          </h3>

          {[
            { id: 'get_products', method: 'GET', path: '/products', label: '1. List Catalog' },
            { id: 'get_product_by_id', method: 'GET', path: '/products/{id}', label: '2. Get Product Specs' },
            { id: 'post_cart', method: 'POST', path: '/cart', label: '3. Add Item to Cart' },
            { id: 'patch_cart', method: 'PATCH', path: '/cart/{id}', label: '4. Update Quantity' },
            { id: 'post_checkout', method: 'POST', path: '/checkout', label: '5. Dynamic Quote' },
            { id: 'post_payment', method: 'POST', path: '/payment', label: '6. Settle Payment' },
            { id: 'get_order', method: 'GET', path: '/orders/{id}', label: '7. Track Order' },
            { id: 'post_return', method: 'POST', path: '/returns', label: '8. Request Return' },
          ].map((ep) => (
            <button
              key={ep.id}
              onClick={() => setSelectedEndpoint(ep.id)}
              className={`w-full text-left p-2.5 rounded-lg text-xs font-mono transition-all border flex items-center justify-between ${
                selectedEndpoint === ep.id 
                  ? 'bg-indigo-950/60 border-indigo-500/60 text-white shadow-sm' 
                  : 'bg-white/[0.02] border-white/5 text-slate-400 hover:text-white hover:border-white/15'
              }`}
            >
              <div>
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded mr-2 ${
                  ep.method === 'GET' ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30' :
                  ep.method === 'POST' ? 'bg-indigo-950 text-indigo-300 border border-indigo-500/30' :
                  'bg-amber-950 text-amber-300 border border-amber-500/30'
                }`}>
                  {ep.method}
                </span>
                <span>{ep.path}</span>
              </div>
              <span className="text-[10px] text-slate-500">{ep.label.split('.')[0]}</span>
            </button>
          ))}
        </div>

        {/* Request Parameter Configurator & Live Payload */}
        <div className="lg:col-span-2 glass-panel p-5 space-y-4 border-white/10">
          <div className="flex items-center justify-between pb-3 border-b border-white/10">
            <div className="flex items-center gap-2">
              <Code2 className="w-4 h-4 text-cyan-400" />
              <span className="font-mono text-xs font-bold text-white">
                Target: /api/merchants/{selectedMerchant}/...
              </span>
            </div>

            <button
              onClick={handleExecute}
              disabled={isLoading}
              className="btn-primary text-xs py-1.5 px-3.5 flex items-center gap-1.5"
            >
              <Play className="w-3.5 h-3.5 fill-white" />
              {isLoading ? "Executing Request..." : "Send HTTP Request"}
            </button>
          </div>

          {/* Form Parameters depending on Endpoint */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {selectedEndpoint.includes('product') && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Product ID / SKU:</label>
                <input 
                  type="text" 
                  value={productId} 
                  onChange={(e) => setProductId(e.target.value)}
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {(selectedEndpoint === 'post_cart' || selectedEndpoint === 'patch_cart') && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Quantity:</label>
                <input 
                  type="number" 
                  min={1}
                  value={quantity} 
                  onChange={(e) => setQuantity(e.target.value)}
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {(selectedEndpoint === 'patch_cart' || selectedEndpoint === 'post_checkout') && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Cart ID:</label>
                <input 
                  type="text" 
                  value={cartId} 
                  onChange={(e) => setCartId(e.target.value)}
                  placeholder="e.g. cart_merchant-a_abc123"
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {selectedEndpoint === 'post_checkout' && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Promo Code:</label>
                <input 
                  type="text" 
                  value={promoCode} 
                  onChange={(e) => setPromoCode(e.target.value)}
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {selectedEndpoint === 'post_payment' && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Quote ID:</label>
                <input 
                  type="text" 
                  value={quoteId} 
                  onChange={(e) => setQuoteId(e.target.value)}
                  placeholder="e.g. q_merchant-a_123456"
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {(selectedEndpoint === 'get_order' || selectedEndpoint === 'post_return') && (
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Order ID:</label>
                <input 
                  type="text" 
                  value={orderId} 
                  onChange={(e) => setOrderId(e.target.value)}
                  placeholder="e.g. ORD_MERCHANT_A_1234"
                  className="form-input text-xs font-mono"
                />
              </div>
            )}

            {selectedEndpoint === 'post_return' && (
              <div className="sm:col-span-2">
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Return Reason:</label>
                <input 
                  type="text" 
                  value={returnReason} 
                  onChange={(e) => setReturnReason(e.target.value)}
                  className="form-input text-xs"
                />
              </div>
            )}
          </div>

          {/* Response Console */}
          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span>{requestUrl || 'Output Console:'}</span>
              {responseOutput && <span className="text-emerald-400">HTTP 200 OK</span>}
            </div>

            <div className="p-3.5 rounded-xl bg-black/60 border border-white/10 h-64 overflow-y-auto text-xs font-mono text-cyan-300">
              {responseOutput ? (
                <pre>{JSON.stringify(responseOutput, null, 2)}</pre>
              ) : (
                <div className="text-slate-500 italic mt-24 text-center">
                  Click "Send HTTP Request" to invoke the merchant endpoint.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
