import React, { useState, useEffect } from 'react';
import { 
  Store, Play, Send, CheckCircle2, Code2, ArrowRight, ShieldCheck, 
  Tag, ShoppingCart, CreditCard, RotateCcw, Package, Search, 
  Layers, RefreshCw, AlertTriangle, ExternalLink, Cpu, Check, Copy
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const MERCHANTS = [
  { 
    code: 'AMAZON', 
    name: 'Amazon India', 
    badge: 'Amazon', 
    color: 'from-amber-500/20 to-orange-500/10 border-amber-500/30 text-amber-400',
    description: 'Electronics, Computing & Flagship Devices. Express Prime Shipping.'
  },
  { 
    code: 'FLIPKART', 
    name: 'Flipkart', 
    badge: 'Flipkart', 
    color: 'from-blue-500/20 to-sky-500/10 border-blue-500/30 text-blue-400',
    description: 'Smartphones, Audio & Appliances. SuperCoins & Bank Offers.'
  },
  { 
    code: 'CROMA', 
    name: 'Croma Electronics', 
    badge: 'Croma', 
    color: 'from-emerald-500/20 to-teal-500/10 border-emerald-500/30 text-emerald-400',
    description: 'Premium Consumer Tech, Home Audio & Appliances. Express Store Pickup.'
  },
];

const POPULAR_MODELS = [
  { model: 'ASUS-ROG-G16-2025', name: 'ASUS ROG Strix G16 (2025)' },
  { model: 'APPLE-MBP-16-M3MAX', name: 'Apple MacBook Pro 16 M3 Max' },
  { model: 'APPLE-IPHONE-15-PRO-MAX', name: 'Apple iPhone 15 Pro Max' },
  { model: 'SAMSUNG-S24-ULTRA', name: 'Samsung Galaxy S24 Ultra' },
  { model: 'SONY-WH-1000XM5', name: 'Sony WH-1000XM5 ANC' },
  { model: 'LOGITECH-MX-MASTER-3S', name: 'Logitech MX Master 3S' }
];

const ENDPOINTS = [
  { id: 'list_merchants', method: 'GET', path: '/api/v1/merchants', label: '1. List Merchants', desc: 'Active merchants, policies, and health' },
  { id: 'get_merchant', method: 'GET', path: '/api/v1/merchants/{code}', label: '2. Get Merchant Details', desc: 'Metadata, return window, shipping rates' },
  { id: 'search_catalog', method: 'GET', path: '/api/v1/products', label: '3. Search Products', desc: 'Filter by category, price, rating, query' },
  { id: 'get_product', method: 'GET', path: '/api/v1/products/{id}', label: '4. Get Product Details', desc: 'Specifications, brand, images, warranties' },
  { id: 'compare_models', method: 'GET', path: '/api/v1/products/compare/{model}', label: '5. Compare Across Merchants', desc: 'Cross-merchant price & rating matrix' },
  { id: 'check_inventory', method: 'GET', path: '/api/v1/inventory/{id}', label: '6. Check Inventory', desc: 'Real-time stock status & threshold' },
  { id: 'create_cart', method: 'POST', path: '/api/v1/carts', label: '7. Create Cart', desc: 'Initializes isolated merchant cart' },
  { id: 'add_cart_item', method: 'POST', path: '/api/v1/carts/{id}/items', label: '8. Add Item to Cart', desc: 'Server-authoritative item addition & subtotal' },
  { id: 'prepare_checkout', method: 'POST', path: '/api/v1/checkout/prepare', label: '9. Prepare Checkout', desc: 'Validates stock, taxes (18% GST), promos & shipping' },
  { id: 'place_order', method: 'POST', path: '/api/v1/orders', label: '10. Create Order', desc: 'Commits inventory and transitions state' },
  { id: 'get_order', method: 'GET', path: '/api/v1/orders/{id}', label: '11. Get Order Status', desc: 'Inspects order lifecycle & verification' },
  { id: 'get_order_tracking', method: 'GET', path: '/api/v1/orders/{id}/tracking', label: '12. Track Order Timeline', desc: 'Carrier ETA, milestone progression' },
];

export default function MerchantSimulatorExplorer() {
  const [selectedMerchant, setSelectedMerchant] = useState('AMAZON');
  const [selectedEndpoint, setSelectedEndpoint] = useState('search_catalog');
  
  // Interactive Params
  const [productId, setProductId] = useState('');
  const [modelNumber, setModelNumber] = useState('ASUS-ROG-G16-2025');
  const [category, setCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('laptop');
  const [cartId, setCartId] = useState('');
  const [orderId, setOrderId] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [promoCode, setPromoCode] = useState('SAVE10');
  const [shippingMethod, setShippingMethod] = useState('STANDARD');

  // Response state
  const [responseOutput, setResponseOutput] = useState(null);
  const [statusCode, setStatusCode] = useState(null);
  const [responseTime, setResponseTime] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [requestUrl, setRequestUrl] = useState('');
  const [copied, setCopied] = useState(false);

  // Quick live merchant overview
  const [merchantsList, setMerchantsList] = useState([]);

  useEffect(() => {
    fetchMerchants();
  }, []);

  const fetchMerchants = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/merchants`);
      if (res.ok) {
        const data = await res.json();
        setMerchantsList(data);
      }
    } catch (err) {
      console.warn('Backend not ready or loading offline simulator:', err);
    }
  };

  const handleExecute = async () => {
    setIsLoading(true);
    setResponseOutput(null);
    setStatusCode(null);
    const startTime = performance.now();

    let url = '';
    let method = 'GET';
    let body = null;

    try {
      if (selectedEndpoint === 'list_merchants') {
        url = `${API_BASE}/api/v1/merchants`;
        method = 'GET';
      } else if (selectedEndpoint === 'get_merchant') {
        url = `${API_BASE}/api/v1/merchants/${selectedMerchant}`;
        method = 'GET';
      } else if (selectedEndpoint === 'search_catalog') {
        const params = new URLSearchParams();
        if (selectedMerchant) params.append('merchant_code', selectedMerchant);
        if (category) params.append('category', category);
        if (searchQuery) params.append('query', searchQuery);
        params.append('page', '1');
        params.append('page_size', '10');
        url = `${API_BASE}/api/v1/products?${params.toString()}`;
        method = 'GET';
      } else if (selectedEndpoint === 'get_product') {
        url = `${API_BASE}/api/v1/products/${productId || 'prod-amz-001'}`;
        method = 'GET';
      } else if (selectedEndpoint === 'compare_models') {
        url = `${API_BASE}/api/v1/products/compare/${modelNumber || 'iphone-15-pro-128'}`;
        method = 'GET';
      } else if (selectedEndpoint === 'check_inventory') {
        url = `${API_BASE}/api/v1/inventory/${productId || 'prod-amz-001'}`;
        method = 'GET';
      } else if (selectedEndpoint === 'create_cart') {
        url = `${API_BASE}/api/v1/carts`;
        method = 'POST';
        body = JSON.stringify({
          merchant_code: selectedMerchant,
          user_id: 'user-agent-sim-01',
          currency: 'INR'
        });
      } else if (selectedEndpoint === 'add_cart_item') {
        url = `${API_BASE}/api/v1/carts/${cartId || 'cart-placeholder'}/items`;
        method = 'POST';
        body = JSON.stringify({
          product_id: productId || 'prod-amz-001',
          quantity: parseInt(quantity, 10) || 1
        });
      } else if (selectedEndpoint === 'prepare_checkout') {
        url = `${API_BASE}/api/v1/checkout/prepare`;
        method = 'POST';
        body = JSON.stringify({
          cart_id: cartId || 'cart-demo',
          merchant_code: selectedMerchant,
          user_id: 'user-agent-sim-01',
          shipping_method: shippingMethod,
          promo_codes: promoCode ? [promoCode] : [],
          items: [
            {
              product_id: productId || 'prod-amz-001',
              sku: 'SKU-SAMPLE',
              title: 'Sample Item for Checkout Simulation',
              unit_price: '54999.00',
              quantity: parseInt(quantity, 10) || 1
            }
          ]
        });
      } else if (selectedEndpoint === 'place_order') {
        url = `${API_BASE}/api/v1/orders`;
        method = 'POST';
        body = JSON.stringify({
          cart_id: cartId || 'cart-demo',
          merchant_code: selectedMerchant,
          user_id: 'user-agent-sim-01',
          shipping_method: shippingMethod,
          shipping_address: {
            street: '128 Tech Avenue, Suite 4B',
            city: 'Bengaluru',
            state: 'Karnataka',
            postal_code: '560100',
            country: 'India'
          },
          items: [
            {
              product_id: productId || 'prod-amz-001',
              sku: 'SKU-ORDER',
              title: 'Autonomous Shopping Checkout Item',
              unit_price: '54999.00',
              quantity: parseInt(quantity, 10) || 1
            }
          ]
        });
      } else if (selectedEndpoint === 'get_order') {
        url = `${API_BASE}/api/v1/orders/${orderId || 'ord-placeholder'}`;
        method = 'GET';
      } else if (selectedEndpoint === 'get_order_tracking') {
        url = `${API_BASE}/api/v1/orders/${orderId || 'ord-placeholder'}/tracking`;
        method = 'GET';
      }

      setRequestUrl(`${method} ${url}`);

      const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
      };
      if (body) options.body = body;

      const res = await fetch(url, options);
      const endTime = performance.now();
      setResponseTime(Math.round(endTime - startTime));
      setStatusCode(res.status);

      const data = await res.json();
      setResponseOutput(data);

      // Cascade auto-fills
      if (data.cart_id || data.id?.startsWith('cart-')) {
        setCartId(data.cart_id || data.id);
      }
      if (data.order_id || data.id?.startsWith('ord-')) {
        setOrderId(data.order_id || data.id);
      }
      if (data.items && data.items.length > 0 && data.items[0].id) {
        setProductId(data.items[0].id);
      } else if (Array.isArray(data) && data.length > 0 && data[0].id) {
        setProductId(data[0].id);
      }
    } catch (err) {
      const endTime = performance.now();
      setResponseTime(Math.round(endTime - startTime));
      setStatusCode(500);
      setResponseOutput({ error: err.message, hint: 'Ensure FastAPI backend is running on port 8000' });
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (responseOutput) {
      navigator.clipboard.writeText(JSON.stringify(responseOutput, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      {/* Header Panel */}
      <div className="glass-panel p-6 border-cyan-500/30 bg-gradient-to-r from-slate-900 via-cyan-950/20 to-slate-900 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="w-12 h-12 rounded-xl bg-cyan-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
            <Store className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-white tracking-wide">Merchant Marketplace Simulator</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                Phase 2
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Simulated realistic multi-merchant commerce endpoints with Amazon, Flipkart, and Croma.
            </p>
          </div>
        </div>

        {/* Quick Merchant Status Badges */}
        <div className="flex items-center gap-2">
          {MERCHANTS.map((m) => (
            <button
              key={m.code}
              onClick={() => setSelectedMerchant(m.code)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                selectedMerchant === m.code
                  ? `bg-gradient-to-r ${m.color} ring-1 ring-white/20`
                  : 'bg-slate-900/60 border-white/10 text-slate-400 hover:text-white'
              }`}
            >
              <Store className="w-3.5 h-3.5" />
              {m.name}
            </button>
          ))}
        </div>
      </div>

      {/* Cross-Merchant Model Quick Selector */}
      <div className="glass-panel p-4 border-white/10 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
            <Layers className="w-4 h-4 text-cyan-400" />
            Cross-Merchant Price Comparison Shortcuts (Phase 2 Seeded Overlaps)
          </span>
          <span className="text-[11px] text-slate-500 font-mono">
            GET /api/v1/products/compare/:model
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {POPULAR_MODELS.map((item) => (
            <button
              key={item.model}
              onClick={() => {
                setModelNumber(item.model);
                setSelectedEndpoint('compare_models');
              }}
              className={`p-2 rounded-lg border text-left transition-all text-xs ${
                modelNumber === item.model && selectedEndpoint === 'compare_models'
                  ? 'bg-cyan-950/60 border-cyan-500/40 text-cyan-300'
                  : 'bg-slate-900/40 border-white/5 text-slate-400 hover:border-white/20 hover:text-white'
              }`}
            >
              <div className="font-semibold truncate">{item.name}</div>
              <div className="text-[10px] font-mono text-slate-500 truncate">{item.model}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Main Grid: Endpoint Selector & Request Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Endpoint Navigation */}
        <div className="glass-panel p-4 space-y-1.5 border-white/10">
          <div className="text-xs font-bold text-slate-300 mb-3 px-2 flex items-center justify-between">
            <span>Marketplace API Endpoints</span>
            <span className="text-[10px] text-cyan-400 font-mono">v1</span>
          </div>

          {ENDPOINTS.map((ep) => (
            <button
              key={ep.id}
              onClick={() => setSelectedEndpoint(ep.id)}
              className={`w-full p-2.5 rounded-xl text-left border transition-all flex items-center justify-between ${
                selectedEndpoint === ep.id
                  ? 'bg-cyan-950/40 border-cyan-500/40 text-cyan-300 ring-1 ring-cyan-500/20'
                  : 'bg-slate-900/40 border-white/5 text-slate-400 hover:border-white/10 hover:text-white'
              }`}
            >
              <div className="space-y-0.5 min-w-0 pr-2">
                <div className="flex items-center gap-1.5 font-mono text-xs font-semibold">
                  <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                    ep.method === 'GET' ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30' :
                    ep.method === 'POST' ? 'bg-indigo-950 text-indigo-300 border border-indigo-500/30' :
                    'bg-amber-950 text-amber-300 border border-amber-500/30'
                  }`}>
                    {ep.method}
                  </span>
                  <span className="truncate text-slate-200">{ep.path}</span>
                </div>
                <div className="text-[10px] text-slate-500 truncate">{ep.desc}</div>
              </div>
              <ArrowRight className={`w-3.5 h-3.5 shrink-0 ${selectedEndpoint === ep.id ? 'text-cyan-400' : 'text-slate-600'}`} />
            </button>
          ))}
        </div>

        {/* Request Parameter Configurator & Live Payload */}
        <div className="lg:col-span-2 glass-panel p-5 space-y-4 border-white/10 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <div className="flex items-center gap-2">
                <Code2 className="w-4 h-4 text-cyan-400" />
                <span className="font-mono text-xs font-bold text-white">
                  Target: {ENDPOINTS.find(e => e.id === selectedEndpoint)?.path}
                </span>
              </div>

              <button
                onClick={handleExecute}
                disabled={isLoading}
                className="btn-primary text-xs py-1.5 px-4 flex items-center gap-1.5 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40"
              >
                {isLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-white" />}
                {isLoading ? "Executing..." : "Send Request"}
              </button>
            </div>

            {/* Dynamic Form Parameters */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <label className="block text-slate-400 font-mono text-[11px] mb-1">Target Merchant:</label>
                <select
                  value={selectedMerchant}
                  onChange={(e) => setSelectedMerchant(e.target.value)}
                  className="form-input text-xs font-mono bg-slate-900"
                >
                  <option value="AMAZON">AMAZON (Amazon India)</option>
                  <option value="FLIPKART">FLIPKART (Flipkart)</option>
                  <option value="CROMA">CROMA (Croma Electronics)</option>
                </select>
              </div>

              {selectedEndpoint === 'search_catalog' && (
                <>
                  <div>
                    <label className="block text-slate-400 font-mono text-[11px] mb-1">Category Filter:</label>
                    <input 
                      type="text" 
                      value={category} 
                      onChange={(e) => setCategory(e.target.value)}
                      placeholder="e.g. smartphones, laptops, audio"
                      className="form-input text-xs font-mono"
                    />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="block text-slate-400 font-mono text-[11px] mb-1">Search Query:</label>
                    <input 
                      type="text" 
                      value={searchQuery} 
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="e.g. macbook, iphone, wireless"
                      className="form-input text-xs font-mono"
                    />
                  </div>
                </>
              )}

              {selectedEndpoint === 'compare_models' && (
                <div className="sm:col-span-2">
                  <label className="block text-slate-400 font-mono text-[11px] mb-1">Model Number / Family:</label>
                  <input 
                    type="text" 
                    value={modelNumber} 
                    onChange={(e) => setModelNumber(e.target.value)}
                    placeholder="e.g. iphone-15-pro-128"
                    className="form-input text-xs font-mono"
                  />
                </div>
              )}

              {(selectedEndpoint === 'get_product' || selectedEndpoint === 'check_inventory' || selectedEndpoint === 'add_cart_item' || selectedEndpoint === 'prepare_checkout' || selectedEndpoint === 'place_order') && (
                <div>
                  <label className="block text-slate-400 font-mono text-[11px] mb-1">Product ID:</label>
                  <input 
                    type="text" 
                    value={productId} 
                    onChange={(e) => setProductId(e.target.value)}
                    placeholder="e.g. prod-amz-001"
                    className="form-input text-xs font-mono"
                  />
                </div>
              )}

              {(selectedEndpoint === 'add_cart_item' || selectedEndpoint === 'prepare_checkout' || selectedEndpoint === 'place_order') && (
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

              {(selectedEndpoint === 'add_cart_item' || selectedEndpoint === 'prepare_checkout' || selectedEndpoint === 'place_order') && (
                <div>
                  <label className="block text-slate-400 font-mono text-[11px] mb-1">Cart ID:</label>
                  <input 
                    type="text" 
                    value={cartId} 
                    onChange={(e) => setCartId(e.target.value)}
                    placeholder="Auto-populated or enter cart ID"
                    className="form-input text-xs font-mono"
                  />
                </div>
              )}

              {selectedEndpoint === 'prepare_checkout' && (
                <div>
                  <label className="block text-slate-400 font-mono text-[11px] mb-1">Promo Code:</label>
                  <input 
                    type="text" 
                    value={promoCode} 
                    onChange={(e) => setPromoCode(e.target.value)}
                    placeholder="e.g. SAVE10, TECH500"
                    className="form-input text-xs font-mono"
                  />
                </div>
              )}

              {(selectedEndpoint === 'prepare_checkout' || selectedEndpoint === 'place_order') && (
                <div>
                  <label className="block text-slate-400 font-mono text-[11px] mb-1">Shipping Option:</label>
                  <select
                    value={shippingMethod}
                    onChange={(e) => setShippingMethod(e.target.value)}
                    className="form-input text-xs font-mono bg-slate-900"
                  >
                    <option value="STANDARD">STANDARD (Standard Delivery)</option>
                    <option value="EXPRESS">EXPRESS (Express / Next-Day)</option>
                    <option value="SAME_DAY">SAME_DAY (Same Day Express)</option>
                  </select>
                </div>
              )}

              {(selectedEndpoint === 'get_order' || selectedEndpoint === 'get_order_tracking') && (
                <div className="sm:col-span-2">
                  <label className="block text-slate-400 font-mono text-[11px] mb-1">Order ID:</label>
                  <input 
                    type="text" 
                    value={orderId} 
                    onChange={(e) => setOrderId(e.target.value)}
                    placeholder="e.g. ord-amz-12345"
                    className="form-input text-xs font-mono"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Response Inspector Console */}
          <div className="space-y-2 pt-4">
            <div className="flex items-center justify-between text-[11px] font-mono">
              <span className="text-slate-400 truncate max-w-md">{requestUrl || 'HTTP Console'}</span>
              <div className="flex items-center gap-2">
                {responseTime !== null && (
                  <span className="text-slate-500">{responseTime}ms</span>
                )}
                {statusCode !== null && (
                  <span className={`px-2 py-0.5 rounded font-bold ${
                    statusCode >= 200 && statusCode < 300 ? 'bg-emerald-950 text-emerald-400 border border-emerald-500/30' :
                    'bg-rose-950 text-rose-400 border border-rose-500/30'
                  }`}>
                    {statusCode}
                  </span>
                )}
                {responseOutput && (
                  <button
                    onClick={copyToClipboard}
                    className="text-slate-400 hover:text-white flex items-center gap-1 text-[10px] bg-slate-800 px-2 py-0.5 rounded border border-white/10"
                  >
                    {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    {copied ? 'Copied' : 'Copy'}
                  </button>
                )}
              </div>
            </div>

            <div className="p-4 rounded-xl bg-black/70 border border-white/10 h-72 overflow-y-auto text-xs font-mono text-cyan-300">
              {responseOutput ? (
                <pre>{JSON.stringify(responseOutput, null, 2)}</pre>
              ) : (
                <div className="text-slate-500 italic mt-28 text-center flex flex-col items-center gap-2">
                  <Code2 className="w-6 h-6 text-slate-600" />
                  <span>Select an endpoint above and click "Send Request" to test simulated commerce responses.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
