import React, { useState, useEffect } from 'react';
import confetti from 'canvas-confetti';
import { 
  Bot, ShoppingBag, Shield, Network, Package, Sparkles, Sliders, 
  ExternalLink, CheckCircle, Zap, RefreshCw, AlertTriangle, Brain, Puzzle, 
  Store, Cable, CreditCard, ShieldAlert, KeyRound, RotateCcw, Database, 
  Activity, FlaskConical, Building2, Settings, ChevronDown, Layers, ArrowLeft, 
  Laptop, Headphones, Smartphone, Monitor, Search, ArrowRight, Sun, Moon, 
  Clock, Check, Scale, ShieldCheck, HelpCircle, MessageSquare, Send, X
} from 'lucide-react';

import ChatInterface from './components/ChatInterface';
import AgentTraceTimeline from './components/AgentTraceTimeline';
import ProductCard from './components/ProductCard';
import ComparisonMatrix from './components/ComparisonMatrix';
import HumanInTheLoopModal from './components/HumanInTheLoopModal';
import SafetyDashboard from './components/SafetyDashboard';
import ProtocolExplorer from './components/ProtocolExplorer';
import OrdersTracker from './components/OrdersTracker';
import CartDrawer from './components/CartDrawer';
import AgentBrainMap from './components/AgentBrainMap';
import SpecializedAgentsConsole from './components/SpecializedAgentsConsole';
import MerchantSimulatorExplorer from './components/MerchantSimulatorExplorer';
import CommerceGatewayExplorer from './components/CommerceGatewayExplorer';
import DelegatedPaymentSandbox from './components/DelegatedPaymentSandbox';
import AgentSecurityCenter from './components/AgentSecurityCenter';
import ToolPermissionsMatrix from './components/ToolPermissionsMatrix';
import FailureRecoveryCenter from './components/FailureRecoveryCenter';
import MemoryConsole from './components/MemoryConsole';
import AgentObservabilityConsole from './components/AgentObservabilityConsole';
import BenchmarkEvaluationConsole from './components/BenchmarkEvaluationConsole';
import SystemArchitectureMap from './components/SystemArchitectureMap';
import ApiSettingsModal from './components/ApiSettingsModal';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('home'); // 'home' | 'search' | 'cart' | 'orders' | 'safety' | 'settings' | dev tabs
  const [isDarkMode, setIsDarkMode] = useState(false);
  
  // Search & Query state
  const [searchQuery, setSearchQuery] = useState('');
  
  // Data State
  const [recommendation, setRecommendation] = useState(null);
  const [cart, setCart] = useState({ items: [], total_inr: 0 });
  const [orders, setOrders] = useState([]);
  const [policy, setPolicy] = useState(null);
  const [auditLedger, setAuditLedger] = useState([]);
  const [brainState, setBrainState] = useState(null);
  const [systemHealth, setSystemHealth] = useState({ status: 'connected', latency_ms: 12 });
  
  // UI State
  const [isLoading, setIsLoading] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDevMenuOpen, setIsDevMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isHitlModalOpen, setIsHitlModalOpen] = useState(false);
  const [selectedHitlProduct, setSelectedHitlProduct] = useState(null);
  const [isCheckingOut, setIsCheckingOut] = useState(false);
  const [successToast, setSuccessToast] = useState(null);

  // Sync Dark mode with DOM
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  // Initial Data Fetch
  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      // 1. Fetch Cart
      const cartRes = await fetch(`${API_BASE}/api/cart`).catch(() => null);
      if (cartRes?.ok) setCart(await cartRes.json());

      // 2. Fetch Orders
      const ordersRes = await fetch(`${API_BASE}/api/orders`).catch(() => null);
      if (ordersRes?.ok) setOrders(await ordersRes.json());

      // 3. Fetch Policy
      const policyRes = await fetch(`${API_BASE}/api/policy`).catch(() => null);
      if (policyRes?.ok) setPolicy(await policyRes.json());

      // 4. Fetch Health
      const healthRes = await fetch(`${API_BASE}/api/v1/ready`).catch(() => null);
      if (healthRes?.ok) {
        const data = await healthRes.json();
        setSystemHealth({ status: data.status, latency_ms: data.database?.latency_ms || 12 });
      }
    } catch (err) {
      console.warn("Initial data fetch error (using fallback defaults):", err);
    }
  };

  const handleSearchQuery = async (queryText) => {
    if (!queryText || !queryText.trim()) return;
    setIsLoading(true);
    setSearchQuery(queryText);
    setActiveTab('search');

    try {
      // Primary: Phase 3 Step 7 End-to-End Shopping Agent
      let res = await fetch(`${API_BASE}/api/v1/agent/shopping`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText, user_id: "default_user" })
      }).catch(() => null);

      if (res && res.ok) {
        const agentResult = await res.json();
        const rec = agentResult.recommendation;
        
        const formatCandidate = (rankedItem) => {
          if (!rankedItem || !rankedItem.candidate) return null;
          return {
            ...rankedItem.candidate,
            badge: rankedItem.badge,
            reasons: rankedItem.score_explanation || [],
            price_inr: Number(rankedItem.candidate.current_price),
            value_score: rankedItem.overall_score
          };
        };

        const topPick = formatCandidate(rec?.best_overall);
        const bestValue = formatCandidate(rec?.best_value);
        const fastestDelivery = formatCandidate(rec?.fastest_delivery);
        const alternativesList = (rec?.alternatives || []).map(formatCandidate).filter(Boolean);

        const comparisonList = (rec?.comparison_matrix || rec?.comparison || []).map(item => ({
          id: item.candidate_id || item.product_id,
          title: item.title,
          merchant_name: item.merchant,
          merchant_code: item.merchant_code,
          price_inr: Number(item.price),
          discount_percentage: item.discount_pct,
          rating: item.rating,
          review_count: item.review_count,
          delivery_days: item.delivery_days,
          in_stock: item.in_stock,
          specs: item.key_specs,
          value_score: item.overall_score,
          badge: item.badge,
          reasons: item.reasons
        }));

        setRecommendation({
          agent_result: agentResult,
          status: agentResult.status,
          intent: agentResult.intent,
          warnings: agentResult.warnings || [],
          clarification_prompt: agentResult.clarification_prompt,
          suggested_action: agentResult.suggested_action,
          rejection_summary: rec?.rejection_summary || {},
          merchant_coverage: rec?.merchant_coverage || [],
          data_completeness: rec?.data_completeness || 'COMPLETE',
          top_recommendation: topPick,
          best_value_recommendation: bestValue,
          fastest_delivery_recommendation: fastestDelivery,
          alternatives: alternativesList,
          comparison_table: comparisonList,
          explanation: rec?.reasons?.best_overall?.join(" • ") || "Deterministic MCDA highest ranked match",
          trade_off_analysis: topPick ? `Top score ${topPick.value_score?.toFixed(1)}/100 across specifications and value` : "",
          trace: agentResult.trace || []
        });
        fetchInitialData();
      } else {
        // Fallback to /api/v1/agent/query
        let queryRes = await fetch(`${API_BASE}/api/v1/agent/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: queryText, user_id: "default_user" })
        }).catch(() => null);

        if (queryRes && queryRes.ok) {
          const rawData = await queryRes.json();
          const topCandidate = rawData.top_recommendation ? {
            ...rawData.top_recommendation.candidate,
            badge: rawData.top_recommendation.badge,
            reasons: rawData.top_recommendation.reasons,
            tradeoffs: rawData.top_recommendation.tradeoffs,
            price_inr: Number(rawData.top_recommendation.candidate.current_price),
            value_score: rawData.top_recommendation.mcda_score?.composite_score || 9.5
          } : null;

          const comparisonList = (rawData.all_recommendations || []).map(item => ({
            ...item.candidate,
            badge: item.badge,
            reasons: item.reasons,
            tradeoffs: item.tradeoffs,
            price_inr: Number(item.candidate.current_price),
            value_score: item.mcda_score?.composite_score || 8.0
          }));

          setRecommendation({
            ...rawData,
            top_recommendation: topCandidate,
            comparison_table: comparisonList,
            explanation: rawData.top_recommendation?.reasons?.join(" • ") || "MCDA highest ranked match",
            trade_off_analysis: rawData.top_recommendation?.tradeoffs?.join(" • ") || "Optimal price-performance balance"
          });
          fetchInitialData();
        } else {
          const err = await (res?.json() || queryRes?.json()).catch(() => ({}));
          alert(`Search error: ${err.detail || "Failed to process shopping request"}`);
        }
      }
    } catch (err) {
      console.error("Query dispatch error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Cart Handlers (Phase 4 Step 1: Recommendation Selection -> Authoritative Server Cart)
  const handleAddToCart = async (product) => {
    if (!product) return;
    try {
      const productId = product.product_id || product.id;
      const merchantCode = product.merchant_code || (product.merchant ? product.merchant.merchant_code : 'AMAZON');
      const expectedPrice = product.current_price !== undefined ? product.current_price : (product.price_inr !== undefined ? product.price_inr : undefined);

      const res = await fetch(`${API_BASE}/api/v1/carts/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: productId,
          merchant_code: merchantCode,
          quantity: 1,
          expected_price: expectedPrice,
          session_id: activeSessionId || 'default_user_session'
        })
      });

      if (res.ok) {
        const data = await res.json();
        const updatedCart = data.cart || data;
        setCart(updatedCart);
        if (data.price_changed) {
          triggerToast(`⚠️ Price updated to ₹${Number(data.current_authoritative_price).toLocaleString()} — added to ${merchantCode} cart`);
        } else {
          triggerToast(`✅ Added ${product.title ? product.title.split('(')[0].trim() : 'Product'} to ${merchantCode} Cart`);
        }
        setIsCartOpen(true);
      } else {
        const errData = await res.json().catch(() => ({ detail: 'Failed to add product to cart' }));
        const errMsg = typeof errData.detail === 'string' ? errData.detail : (errData.message || 'Failed to add item to cart');
        triggerToast(`❌ ${errMsg}`);
      }
    } catch (err) {
      console.error("Error adding to cart:", err);
      triggerToast("❌ Network error connecting to cart service");
    }
  };

  const handleRemoveFromCart = async (productId) => {
    try {
      if (cart && cart.id) {
        const res = await fetch(`${API_BASE}/api/v1/carts/${cart.id}/items/${productId}`, {
          method: 'DELETE'
        });
        if (res.ok) {
          const updatedCart = await res.json();
          setCart(updatedCart);
          return;
        }
      }
      // Fallback
      const res = await fetch(`${API_BASE}/api/cart/items/${productId}`, { method: 'DELETE' }).catch(() => null);
      if (res && res.ok) {
        setCart(await res.json());
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleClearCart = async () => {
    try {
      if (cart && cart.id) {
        const res = await fetch(`${API_BASE}/api/v1/carts/${cart.id}`, { method: 'DELETE' });
        if (res.ok) {
          setCart(await res.json());
          return;
        }
      }
      // Fallback
      const res = await fetch(`${API_BASE}/api/cart`, { method: 'DELETE' }).catch(() => null);
      if (res && res.ok) setCart(await res.json());
    } catch (err) {
      console.error(err);
    }
  };

  // Instant Buy / Autonomous Checkout Trigger
  const handleInstantBuy = (product) => {
    const threshold = policy?.single_item_approval_threshold_inr || 50000;
    if (product.price_inr >= threshold) {
      setSelectedHitlProduct(product);
      setIsHitlModalOpen(true);
    } else {
      executeDirectCheckout(product);
    }
  };

  const handleApproveHitl = async (product) => {
    await executeDirectCheckout(product, true);
    setIsHitlModalOpen(false);
  };

  const executeDirectCheckout = async (product, userConfirmed = true) => {
    setIsCheckingOut(true);
    try {
      const res = await fetch(`${API_BASE}/api/checkout/authorize-and-pay`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: product.id,
          user_confirmed: userConfirmed,
          session_id: "session_default"
        })
      });

      if (res.ok) {
        const newOrder = await res.json();
        setOrders(prev => [newOrder, ...prev]);
        fetchInitialData();

        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 }
        });

        triggerToast(`🎉 Order ${newOrder.order_id} Confirmed! Total: ₹${newOrder.amount_inr.toLocaleString()}`);
        setActiveTab('orders');
      } else {
        const err = await res.json().catch(() => ({}));
        alert(`Checkout blocked: ${err.detail || "Unable to authorize payment"}`);
      }
    } catch (err) {
      console.error("Checkout execution error:", err);
    } finally {
      setIsCheckingOut(false);
    }
  };

  const handleUpdatePolicy = async (newPolicyData) => {
    try {
      const res = await fetch(`${API_BASE}/api/policy`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newPolicyData)
      });
      if (res.ok) {
        const updated = await res.json();
        setPolicy(updated);
        triggerToast("Spending policy updated successfully");
        fetchInitialData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleReturnOrder = async (orderId, reason) => {
    try {
      const res = await fetch(`${API_BASE}/api/orders/${orderId}/return`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason })
      });
      if (res.ok) {
        const updated = await res.json();
        setOrders(prev => prev.map(o => o.order_id === orderId ? updated : o));
        triggerToast(`Return request initiated for ${orderId}`);
        fetchInitialData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const triggerToast = (msg) => {
    setSuccessToast(msg);
    setTimeout(() => setSuccessToast(null), 4000);
  };

  const isDevTab = ![ 'home', 'search', 'cart', 'orders', 'safety', 'settings' ].includes(activeTab);

  return (
    <div className="min-h-screen flex bg-[#f4f7fc] dark:bg-[#090d16] text-slate-900 dark:text-slate-100 transition-colors duration-300">
      
      {/* Toast Notification */}
      {successToast && (
        <div className="fixed top-5 right-5 z-50 bg-indigo-600 text-white px-4 py-2.5 rounded-xl shadow-2xl flex items-center gap-2 text-xs font-semibold animate-in fade-in slide-in-from-top-4 duration-300">
          <CheckCircle className="w-4 h-4 text-emerald-300" />
          <span>{successToast}</span>
        </div>
      )}

      {/* =========================================================================
          LEFT SIDEBAR (Fixed & Pixel-Perfect to Screenshot)
          ========================================================================= */}
      <aside className="w-64 bg-white dark:bg-[#0f172a] border-r border-slate-200/80 dark:border-white/10 flex flex-col justify-between shrink-0 min-h-screen sticky top-0 h-screen overflow-y-auto select-none transition-colors">
        <div>
          {/* Brand Header */}
          <div className="p-6 flex items-center gap-3.5 cursor-pointer" onClick={() => setActiveTab('home')}>
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center text-white shadow-md shadow-indigo-500/25">
              <ShoppingBag className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-xl font-extrabold tracking-tight text-slate-900 dark:text-white brand-font leading-tight">
                AgentCart
              </h1>
              <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">
                AI Shopping Agent
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="px-4 space-y-1 text-sm font-medium">
            <button
              onClick={() => setActiveTab('home')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-all ${
                activeTab === 'home'
                  ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-600/20 dark:text-indigo-400 font-semibold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5'
              }`}
            >
              <Bot className="w-4 h-4" />
              <span>Home</span>
            </button>

            <button
              onClick={() => setActiveTab('search')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-all ${
                activeTab === 'search'
                  ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-600/20 dark:text-indigo-400 font-semibold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5'
              }`}
            >
              <Search className="w-4 h-4" />
              <span>Search</span>
            </button>

            <button
              onClick={() => setIsCartOpen(true)}
              className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5 transition-all"
            >
              <div className="flex items-center gap-3">
                <ShoppingBag className="w-4 h-4" />
                <span>Cart</span>
              </div>
              {cart?.items?.length > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-indigo-600 text-white font-bold text-xs">
                  {cart.items.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('orders')}
              className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl transition-all ${
                activeTab === 'orders'
                  ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-600/20 dark:text-indigo-400 font-semibold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5'
              }`}
            >
              <div className="flex items-center gap-3">
                <Package className="w-4 h-4" />
                <span>Orders</span>
              </div>
              {orders.length > 0 && (
                <span className="px-2 py-0.5 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-bold text-xs">
                  {orders.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('safety')}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl transition-all ${
                activeTab === 'safety'
                  ? 'bg-indigo-50 text-indigo-600 dark:bg-indigo-600/20 dark:text-indigo-400 font-semibold shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5'
              }`}
            >
              <Shield className="w-4 h-4" />
              <span>Spending Policy</span>
            </button>

            <button
              onClick={() => setIsSettingsOpen(true)}
              className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5 transition-all"
            >
              <Settings className="w-4 h-4" />
              <span>Settings</span>
            </button>
          </nav>

          {/* Dev Lab Diagnostics Menu */}
          <div className="mt-4 px-4 pt-4 border-t border-slate-200/80 dark:border-white/10">
            <button
              onClick={() => setIsDevMenuOpen(!isDevMenuOpen)}
              className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl text-xs font-mono text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-white/5 transition-all"
            >
              <div className="flex items-center gap-2">
                <Layers className="w-3.5 h-3.5 text-indigo-500" />
                <span>Dev Lab Tools</span>
              </div>
              <ChevronDown className={`w-3.5 h-3.5 transition-transform ${isDevMenuOpen ? 'rotate-180' : ''}`} />
            </button>

            {isDevMenuOpen && (
              <div className="mt-1.5 space-y-0.5 text-xs font-mono pl-3 text-slate-600 dark:text-slate-400">
                <button onClick={() => setActiveTab('brain')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">🧠 Brain &amp; LangGraph</button>
                <button onClick={() => setActiveTab('specialized')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">🧩 Subagents Console</button>
                <button onClick={() => setActiveTab('memory')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">💾 4-Tier Memory</button>
                <button onClick={() => setActiveTab('observability')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">📈 Observability</button>
                <button onClick={() => setActiveTab('merchants')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">🏪 Merchant Simulator</button>
                <button onClick={() => setActiveTab('gateway')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">🔌 Commerce Gateway</button>
                <button onClick={() => setActiveTab('payments')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">💳 Delegated Payments</button>
                <button onClick={() => setActiveTab('security')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">🛡️ Security &amp; Sanitizer</button>
                <button onClick={() => setActiveTab('permissions')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">🔐 RBAC Matrix</button>
                <button onClick={() => setActiveTab('resiliency')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">🔄 Failure Recovery</button>
                <button onClick={() => setActiveTab('benchmark')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">🧪 Benchmark TC01-TC12</button>
                <button onClick={() => setActiveTab('architecture')} className="w-full text-left py-1.5 px-2 hover:text-indigo-600 dark:hover:text-white rounded">🏗️ 9-Layer Architecture</button>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar Bottom Banner & Footer */}
        <div className="p-4 space-y-3">
          {/* AI-Powered Badge Card */}
          <div className="p-3.5 rounded-2xl bg-gradient-to-br from-indigo-50/80 to-purple-50/80 dark:from-indigo-950/40 dark:to-purple-950/30 border border-indigo-100 dark:border-indigo-500/20 shadow-xs">
            <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-700 dark:text-indigo-300">
              <span className="text-amber-500">👑</span>
              <span>AI-Powered</span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1 leading-snug">
              Smarter shopping. Less effort. More time for what matters.
            </p>
          </div>

          {/* Version Footer */}
          <div className="text-[10px] text-slate-400 font-mono text-center">
            AgentCart v1.0.0 · Build something amazing ❤️
          </div>
        </div>
      </aside>

      {/* =========================================================================
          MAIN CONTENT VIEW AREA
          ========================================================================= */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="h-16 px-6 sm:px-8 border-b border-slate-200/80 dark:border-white/10 flex items-center justify-between bg-white/70 dark:bg-slate-900/60 backdrop-blur-xl sticky top-0 z-30 transition-colors">
          <div>
            {isDevTab && (
              <button
                onClick={() => setActiveTab('home')}
                className="flex items-center gap-2 text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Back to Shopping Home</span>
              </button>
            )}
          </div>

          {/* Right Header Badges: System Online + Theme Toggle + User Badge */}
          <div className="flex items-center gap-3.5">
            {/* System Online Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-500/30 text-emerald-700 dark:text-emerald-400 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              <span>System Online</span>
            </div>

            {/* Theme Toggle (Light / Dark) */}
            <button
              onClick={() => setIsDarkMode(!isDarkMode)}
              className="p-2 rounded-xl text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/10 transition-colors"
              title="Toggle Theme"
            >
              {isDarkMode ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
            </button>

            {/* User Profile Pill */}
            <div className="relative">
              <button
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center gap-2.5 p-1 pr-2.5 rounded-full hover:bg-slate-100 dark:hover:bg-white/5 transition-all text-xs font-semibold text-slate-700 dark:text-slate-200"
              >
                <div className="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center font-bold text-[11px] shadow-xs">
                  RN
                </div>
                <span>Rahul</span>
                <ChevronDown className="w-3 h-3 text-slate-400" />
              </button>

              {isUserMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 p-2 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 shadow-xl z-50 text-xs">
                  <div className="px-3 py-2 border-b border-slate-100 dark:border-white/10">
                    <div className="font-bold text-slate-900 dark:text-white">Rahul Naik</div>
                    <div className="text-[10px] text-slate-500">Autonomous Shopper</div>
                  </div>
                  <button onClick={() => { setActiveTab('safety'); setIsUserMenuOpen(false); }} className="w-full text-left px-3 py-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5">Spending Policy</button>
                  <button onClick={() => { setIsSettingsOpen(true); setIsUserMenuOpen(false); }} className="w-full text-left px-3 py-2 rounded-xl hover:bg-slate-100 dark:hover:bg-white/5">API Settings</button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* =====================================================================
            HOME VIEW (Pixel-Perfect from Screenshot)
            ===================================================================== */}
        {activeTab === 'home' && (
          <main className="p-6 sm:p-8 max-w-6xl mx-auto w-full space-y-8 animate-in fade-in duration-300">
            
            {/* HERO BANNER: Greeting + Title + 3D Robot Mascot */}
            <div className="relative overflow-hidden rounded-3xl p-8 sm:p-10 bg-gradient-to-r from-blue-50/90 via-indigo-50/70 to-purple-50/80 dark:from-indigo-950/40 dark:via-slate-900/60 dark:to-purple-950/30 border border-indigo-100/80 dark:border-indigo-500/20 shadow-xs">
              <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                
                {/* Left Text */}
                <div className="space-y-2 max-w-xl">
                  <div className="text-sm font-semibold text-slate-600 dark:text-slate-400">
                    Hello Rahul! 👋
                  </div>
                  <h2 className="text-3xl sm:text-4xl font-black text-slate-900 dark:text-white tracking-tight leading-tight brand-font">
                    Your Autonomous <span className="bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-600 dark:from-indigo-400 dark:to-cyan-400 bg-clip-text text-transparent">AI Shopping Agent</span>
                  </h2>
                  <p className="text-sm sm:text-base text-slate-600 dark:text-slate-400 font-normal">
                    Find the best products, compare across multiple stores, and shop smarter with AI.
                  </p>
                </div>

                {/* Right Robot Mascot with Speech Bubble */}
                <div className="relative shrink-0 flex flex-col items-center">
                  {/* Floating Speech Bubble */}
                  <div className="speech-bubble mb-2 text-center text-xs font-bold text-indigo-700 dark:text-indigo-300">
                    <div>Search</div>
                    <div>Compare</div>
                    <div>Save Time</div>
                  </div>

                  {/* 3D Cute Shopping Robot SVG */}
                  <div className="w-28 h-28 relative animate-float">
                    <svg viewBox="0 0 160 160" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full drop-shadow-xl">
                      {/* Sparkles */}
                      <path d="M140 30L143 38L151 41L143 44L140 52L137 44L129 41L137 38L140 30Z" fill="#38BDF8" />
                      <path d="M20 70L22 75L27 77L22 79L20 84L18 79L13 77L18 75L20 70Z" fill="#818CF8" />
                      
                      {/* Robot Head */}
                      <rect x="35" y="30" width="90" height="75" rx="36" fill="url(#bot_head_grad)" stroke="#4F46E5" strokeWidth="4"/>
                      <circle cx="80" cy="18" r="7" fill="#6366F1" stroke="#4338CA" strokeWidth="3" />
                      <path d="M80 25V30" stroke="#4338CA" strokeWidth="4" strokeLinecap="round" />
                      
                      {/* Screen Visor */}
                      <rect x="45" y="44" width="70" height="46" rx="20" fill="#090D16" />
                      
                      {/* Glowing Cyan Eyes */}
                      <ellipse cx="64" cy="67" rx="8" ry="10" fill="#38BDF8" className="animate-pulse" />
                      <ellipse cx="96" cy="67" rx="8" ry="10" fill="#38BDF8" className="animate-pulse" />
                      
                      {/* Cheerful Smile */}
                      <path d="M72 78C76 82 84 82 88 78" stroke="#38BDF8" strokeWidth="3" strokeLinecap="round" />

                      {/* Robot Body */}
                      <rect x="50" y="105" width="60" height="40" rx="16" fill="#EEF2FF" stroke="#4F46E5" strokeWidth="3" />
                      <circle cx="80" cy="120" r="8" fill="#6366F1" />

                      {/* Shopping Bags */}
                      <rect x="110" y="100" width="28" height="34" rx="6" fill="#38BDF8" stroke="#0284C7" strokeWidth="2.5" />
                      <path d="M117 100V94C117 91.5 119.5 89 122 89H126C128.5 89 131 91.5 131 94V100" stroke="#0284C7" strokeWidth="2.5" />

                      <defs>
                        <linearGradient id="bot_head_grad" x1="35" y1="30" x2="125" y2="105" gradientUnits="userSpaceOnUse">
                          <stop stopColor="#FFFFFF" />
                          <stop offset="1" stopColor="#E0E7FF" />
                        </linearGradient>
                      </defs>
                    </svg>
                  </div>
                </div>

              </div>

              {/* Prominent Search Bar */}
              <div className="mt-8 bg-white dark:bg-slate-900 p-2 sm:p-2.5 rounded-2xl shadow-xl shadow-indigo-500/10 border border-slate-200/90 dark:border-white/10 flex flex-col sm:flex-row items-center gap-2 transition-all focus-within:ring-2 focus-within:ring-indigo-500/30">
                <div className="flex items-center gap-3 px-3 flex-1 w-full">
                  <MessageSquare className="w-5 h-5 text-slate-400 shrink-0" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearchQuery(searchQuery)}
                    placeholder='What are you looking for? (e.g. "Laptop with 32GB RAM under ₹1.2L")'
                    className="w-full bg-transparent border-none text-slate-900 dark:text-white text-sm focus:outline-none placeholder-slate-400 py-2 font-medium"
                  />
                  {searchQuery && (
                    <button onClick={() => setSearchQuery('')} className="text-slate-400 hover:text-slate-600 p-1">
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>

                <button
                  onClick={() => handleSearchQuery(searchQuery)}
                  disabled={isLoading || !searchQuery.trim()}
                  className="w-full sm:w-auto px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm flex items-center justify-center gap-2 shadow-md shadow-indigo-600/30 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
                >
                  <Send className="w-4 h-4" />
                  <span>Find Best Deals</span>
                </button>
              </div>

              {/* Quick Prompt Pills */}
              <div className="mt-4 flex items-center gap-2 overflow-x-auto no-scrollbar py-1">
                <button
                  onClick={() => handleSearchQuery("I need a laptop for AI/ML development under ₹1.2 lakh with 32GB RAM and RTX GPU.")}
                  className="px-3.5 py-1.5 rounded-full bg-white/80 dark:bg-slate-900/80 hover:bg-white dark:hover:bg-slate-900 border border-slate-200/80 dark:border-white/10 text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 text-xs font-semibold shrink-0 transition-all flex items-center gap-1.5 shadow-2xs"
                >
                  <span>💻</span>
                  <span>Laptop for AI/ML under ₹1.2L</span>
                </button>

                <button
                  onClick={() => handleSearchQuery("Find the best noise cancelling headphones under ₹30,000 with 30+ hour battery life.")}
                  className="px-3.5 py-1.5 rounded-full bg-white/80 dark:bg-slate-900/80 hover:bg-white dark:hover:bg-slate-900 border border-slate-200/80 dark:border-white/10 text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 text-xs font-semibold shrink-0 transition-all flex items-center gap-1.5 shadow-2xs"
                >
                  <span>🎧</span>
                  <span>Noise cancelling headphones</span>
                </button>

                <button
                  onClick={() => handleSearchQuery("I need a flagship 5G smartphone with top tier camera and 12GB RAM under ₹30,000.")}
                  className="px-3.5 py-1.5 rounded-full bg-white/80 dark:bg-slate-900/80 hover:bg-white dark:hover:bg-slate-900 border border-slate-200/80 dark:border-white/10 text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 text-xs font-semibold shrink-0 transition-all flex items-center gap-1.5 shadow-2xs"
                >
                  <span>📱</span>
                  <span>Best 5G smartphone under ₹30K</span>
                </button>

                <button
                  onClick={() => handleSearchQuery("Find me a 4K 144Hz IPS gaming monitor with 1ms response time under ₹50,000.")}
                  className="px-3.5 py-1.5 rounded-full bg-white/80 dark:bg-slate-900/80 hover:bg-white dark:hover:bg-slate-900 border border-slate-200/80 dark:border-white/10 text-slate-700 dark:text-slate-300 hover:text-indigo-600 dark:hover:text-indigo-400 text-xs font-semibold shrink-0 transition-all flex items-center gap-1.5 shadow-2xs"
                >
                  <span>🖥️</span>
                  <span>4K monitor for coding</span>
                </button>
              </div>

            </div>

            {/* 4 HIGHLIGHT VALUE PROPS PILLS */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              
              {/* 1. Multi-store Search */}
              <div className="bg-white dark:bg-[#0f172a] p-4 rounded-2xl border border-slate-200/80 dark:border-white/10 flex items-center gap-3.5 shadow-xs">
                <div className="w-11 h-11 rounded-2xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
                  <Search className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white leading-snug">Multi-store Search</h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Amazon, Flipkart, Croma + more</p>
                </div>
              </div>

              {/* 2. AI Comparison */}
              <div className="bg-white dark:bg-[#0f172a] p-4 rounded-2xl border border-slate-200/80 dark:border-white/10 flex items-center gap-3.5 shadow-xs">
                <div className="w-11 h-11 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0">
                  <Scale className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white leading-snug">AI Comparison</h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Find the best value</p>
                </div>
              </div>

              {/* 3. Safe & Secure */}
              <div className="bg-white dark:bg-[#0f172a] p-4 rounded-2xl border border-slate-200/80 dark:border-white/10 flex items-center gap-3.5 shadow-xs">
                <div className="w-11 h-11 rounded-2xl bg-pink-50 dark:bg-pink-950/60 text-pink-600 dark:text-pink-400 flex items-center justify-center shrink-0">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white leading-snug">Safe &amp; Secure</h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">You stay in control</p>
                </div>
              </div>

              {/* 4. Save Time */}
              <div className="bg-white dark:bg-[#0f172a] p-4 rounded-2xl border border-slate-200/80 dark:border-white/10 flex items-center gap-3.5 shadow-xs">
                <div className="w-11 h-11 rounded-2xl bg-amber-50 dark:bg-amber-950/60 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
                  <Zap className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 dark:text-white leading-snug">Save Time</h4>
                  <p className="text-xs text-slate-500 dark:text-slate-400">Let AI do the research</p>
                </div>
              </div>

            </div>

            {/* 3 COLUMN CONTENT GRID (How it works + Supported stores + Recent searches) */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

              {/* CARD 1: HOW IT WORKS */}
              <div className="bg-white dark:bg-[#0f172a] p-6 rounded-3xl border border-slate-200/80 dark:border-white/10 shadow-xs space-y-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">🚀</span>
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">How It Works</h3>
                  </div>
                  <button onClick={() => setActiveTab('architecture')} className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1">
                    <span>View Guide</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>

                {/* 4 Step Timeline */}
                <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
                  
                  {/* Step 1 */}
                  <div className="relative space-y-0.5">
                    <div className="absolute -left-6 top-0 w-5 h-5 rounded-full bg-blue-500 text-white flex items-center justify-center text-[10px] font-bold shadow-xs">
                      1
                    </div>
                    <div className="text-sm font-bold text-slate-900 dark:text-white">Tell us what you need</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">Describe your requirement in natural language</div>
                  </div>

                  {/* Step 2 */}
                  <div className="relative space-y-0.5">
                    <div className="absolute -left-6 top-0 w-5 h-5 rounded-full bg-purple-500 text-white flex items-center justify-center text-[10px] font-bold shadow-xs">
                      2
                    </div>
                    <div className="text-sm font-bold text-slate-900 dark:text-white">AI searches &amp; compares</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">Finds best products across multiple stores</div>
                  </div>

                  {/* Step 3 */}
                  <div className="relative space-y-0.5">
                    <div className="absolute -left-6 top-0 w-5 h-5 rounded-full bg-pink-500 text-white flex items-center justify-center text-[10px] font-bold shadow-xs">
                      3
                    </div>
                    <div className="text-sm font-bold text-slate-900 dark:text-white">Review &amp; choose</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">See top recommendations with reasoning</div>
                  </div>

                  {/* Step 4 */}
                  <div className="relative space-y-0.5">
                    <div className="absolute -left-6 top-0 w-5 h-5 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[10px] font-bold shadow-xs">
                      4
                    </div>
                    <div className="text-sm font-bold text-slate-900 dark:text-white">Buy safely (your control)</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">Approve purchases, track orders</div>
                  </div>

                </div>
              </div>

              {/* CARD 2: SUPPORTED STORES */}
              <div className="bg-white dark:bg-[#0f172a] p-6 rounded-3xl border border-slate-200/80 dark:border-white/10 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Store className="w-5 h-5 text-indigo-500" />
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">Supported Stores</h3>
                  </div>
                  <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-full">
                    3+ retailers
                  </span>
                </div>

                {/* Retailer Cards */}
                <div className="space-y-2.5">
                  {/* Amazon */}
                  <div 
                    onClick={() => handleSearchQuery("Find best laptop deals on Amazon")}
                    className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 hover:bg-indigo-50/60 dark:hover:bg-indigo-950/30 border border-slate-200/60 dark:border-white/5 flex items-center justify-between cursor-pointer transition-all group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 flex items-center justify-center text-lg font-black text-amber-500 shadow-2xs">
                        a
                      </div>
                      <div>
                        <div className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400">Amazon</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">Wide selection, fast delivery</div>
                      </div>
                    </div>
                    <ChevronDown className="w-4 h-4 text-slate-400 -rotate-90 group-hover:translate-x-0.5 transition-transform" />
                  </div>

                  {/* Flipkart */}
                  <div 
                    onClick={() => handleSearchQuery("Find best smartphone deals on Flipkart")}
                    className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 hover:bg-indigo-50/60 dark:hover:bg-indigo-950/30 border border-slate-200/60 dark:border-white/5 flex items-center justify-between cursor-pointer transition-all group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-[#2874F0] text-white flex items-center justify-center text-sm font-black italic shadow-2xs">
                        fk
                      </div>
                      <div>
                        <div className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400">Flipkart</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">Great deals and offers</div>
                      </div>
                    </div>
                    <ChevronDown className="w-4 h-4 text-slate-400 -rotate-90 group-hover:translate-x-0.5 transition-transform" />
                  </div>

                  {/* Croma */}
                  <div 
                    onClick={() => handleSearchQuery("Find premium electronics on Croma")}
                    className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 hover:bg-indigo-50/60 dark:hover:bg-indigo-950/30 border border-slate-200/60 dark:border-white/5 flex items-center justify-between cursor-pointer transition-all group"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-[#00838F] text-white flex items-center justify-center text-sm font-black shadow-2xs">
                        C
                      </div>
                      <div>
                        <div className="text-sm font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400">Croma</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">Electronics specialist</div>
                      </div>
                    </div>
                    <ChevronDown className="w-4 h-4 text-slate-400 -rotate-90 group-hover:translate-x-0.5 transition-transform" />
                  </div>
                </div>
              </div>

              {/* CARD 3: RECENT SEARCHES */}
              <div className="bg-white dark:bg-[#0f172a] p-6 rounded-3xl border border-slate-200/80 dark:border-white/10 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-indigo-500" />
                    <h3 className="text-base font-bold text-slate-900 dark:text-white">Recent Searches</h3>
                  </div>
                  <button onClick={() => setActiveTab('search')} className="text-xs font-semibold text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1">
                    <span>View All</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>

                {/* Search History Cards */}
                <div className="space-y-2.5">
                  <div 
                    onClick={() => handleSearchQuery("I need a laptop for AI/ML development under ₹1.2 lakh with 32GB RAM and RTX GPU.")}
                    className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200/60 dark:border-white/5 flex items-center justify-between cursor-pointer transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-200">
                        <Laptop className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="text-sm font-bold text-slate-900 dark:text-white">AI/ML Laptop</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">32GB RAM, under ₹1.2L</div>
                      </div>
                    </div>
                    <span className="text-[11px] text-slate-400">2 hours ago</span>
                  </div>

                  <div 
                    onClick={() => handleSearchQuery("Find the best noise cancelling headphones under ₹30,000 with 30+ hour battery life.")}
                    className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200/60 dark:border-white/5 flex items-center justify-between cursor-pointer transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-200">
                        <Headphones className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="text-sm font-bold text-slate-900 dark:text-white">Sony WH-1000XM5</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">Noise cancelling headphones</div>
                      </div>
                    </div>
                    <span className="text-[11px] text-slate-400">1 day ago</span>
                  </div>

                  <div 
                    onClick={() => handleSearchQuery("I need a flagship 5G smartphone with top tier camera and 12GB RAM under ₹1.2 lakh.")}
                    className="p-3 rounded-2xl bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200/60 dark:border-white/5 flex items-center justify-between cursor-pointer transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-xl bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-slate-700 dark:text-slate-200">
                        <Smartphone className="w-5 h-5" />
                      </div>
                      <div>
                        <div className="text-sm font-bold text-slate-900 dark:text-white">iPhone 15</div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">5G smartphone</div>
                      </div>
                    </div>
                    <span className="text-[11px] text-slate-400">2 days ago</span>
                  </div>
                </div>
              </div>

            </div>

            {/* BOTTOM PROMO BANNER: Spending Policy */}
            <div className="p-6 rounded-3xl bg-indigo-50/90 dark:bg-indigo-950/30 border border-indigo-100 dark:border-indigo-500/20 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xs">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-md shadow-indigo-600/25">
                  <Shield className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-base font-bold text-slate-900 dark:text-white">Your spending, your rules</h4>
                  <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400">
                    Set budgets, approval limits and category preferences to ensure 100% safe autonomous shopping.
                  </p>
                </div>
              </div>

              <button
                onClick={() => setActiveTab('safety')}
                className="px-5 py-2.5 rounded-xl bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-indigo-600 dark:text-indigo-400 font-bold text-xs border border-indigo-200 dark:border-indigo-500/30 shadow-xs shrink-0 flex items-center gap-1.5 transition-all"
              >
                <span>Configure Spending Policy</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

          </main>
        )}

        {/* =====================================================================
            SEARCH & RECOMMENDATION RESULTS VIEW
            ===================================================================== */}
        {activeTab === 'search' && (
          <main className="p-6 sm:p-8 max-w-6xl mx-auto w-full space-y-6 animate-in fade-in duration-300">
            <ChatInterface 
              onSubmitQuery={handleSearchQuery}
              isLoading={isLoading}
            />

            {isLoading && (
              <div className="p-12 text-center space-y-4 rounded-3xl bg-white dark:bg-[#0f172a] border border-slate-200/80 dark:border-white/10 shadow-xs">
                <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                <div className="space-y-1">
                  <h3 className="text-base font-bold text-slate-900 dark:text-white">Autonomous Agents at Work</h3>
                  <p className="text-xs text-slate-500 max-w-md mx-auto">
                    Extracting structured intent, querying merchant APIs across Amazon, Flipkart &amp; Croma, applying hard constraints, and scoring trade-offs...
                  </p>
                </div>
              </div>
            )}

            {!isLoading && recommendation && (
              <div className="space-y-8">
                {/* Agent Trace Timeline */}
                {recommendation.trace && recommendation.trace.length > 0 && (
                  <AgentTraceTimeline trace={recommendation.trace} />
                )}

                {/* Warnings Banner */}
                {recommendation.warnings && recommendation.warnings.length > 0 && (
                  <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs space-y-1.5 shadow-xs">
                    <div className="flex items-center gap-2 font-bold text-amber-400">
                      <AlertTriangle className="w-4 h-4" />
                      <span>Execution Notice</span>
                    </div>
                    <ul className="list-disc list-inside space-y-0.5 text-amber-200/90 pl-1 text-[11px]">
                      {recommendation.warnings.map((w, idx) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Merchant Discovery Coverage Badges */}
                {recommendation.merchant_coverage && recommendation.merchant_coverage.length > 0 && (
                  <div className="p-4 rounded-2xl bg-white dark:bg-[#0f172a] border border-slate-200/80 dark:border-white/10 flex flex-wrap items-center justify-between gap-3 shadow-xs">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-200">
                      <Store className="w-4 h-4 text-indigo-500" />
                      <span>Merchant Discovery Coverage:</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      {recommendation.merchant_coverage.map((m, idx) => (
                        <span 
                          key={idx}
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                            m.status === 'SUCCESS' 
                              ? 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30'
                              : 'bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-400 border border-rose-500/30'
                          }`}
                        >
                          {m.status === 'SUCCESS' ? <Check className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
                          <span>{m.merchant}: {m.result_count} items ({m.status})</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Clarification Needed State */}
                {recommendation.status === 'NEEDS_CLARIFICATION' && (
                  <div className="p-6 rounded-3xl bg-indigo-50/80 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-500/30 space-y-3">
                    <div className="flex items-center gap-2.5 text-indigo-700 dark:text-indigo-300 font-bold text-sm">
                      <HelpCircle className="w-5 h-5" />
                      <span>Clarification Needed to Find Best Deals</span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300">
                      {recommendation.clarification_prompt || "Please provide your maximum budget and specific requirements to help us search across retailers."}
                    </p>
                    {recommendation.suggested_action && (
                      <div className="text-[11px] text-indigo-500 dark:text-indigo-400 font-medium">
                        💡 Tip: {recommendation.suggested_action}
                      </div>
                    )}
                  </div>
                )}

                {/* No Match State */}
                {recommendation.status === 'NO_MATCH' && (
                  <div className="p-6 rounded-3xl bg-amber-50/80 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-500/30 space-y-4">
                    <div className="flex items-center gap-2.5 text-amber-700 dark:text-amber-300 font-bold text-sm">
                      <AlertTriangle className="w-5 h-5 text-amber-500" />
                      <span>No Exact Matches Found Under Current Hard Constraints</span>
                    </div>
                    <p className="text-xs text-slate-600 dark:text-slate-300">
                      Our deterministic constraint engine evaluated all discovered products, but zero candidates satisfied 100% of your non-negotiable criteria without violation.
                    </p>

                    {/* Rejection Summary */}
                    {recommendation.rejection_summary && Object.keys(recommendation.rejection_summary).length > 0 && (
                      <div className="space-y-2 pt-2 border-t border-amber-200 dark:border-amber-500/20">
                        <div className="text-xs font-bold text-slate-700 dark:text-slate-300">Candidate Rejection Audit:</div>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(recommendation.rejection_summary).map(([reason, count]) => (
                            <span key={reason} className="px-2.5 py-1 rounded-lg bg-white/80 dark:bg-slate-900 border border-amber-300 dark:border-amber-500/30 text-xs text-slate-700 dark:text-slate-300">
                              <strong>{reason.replace(/_/g, ' ')}:</strong> {count} candidate{count > 1 ? 's' : ''}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {recommendation.suggested_action && (
                      <div className="text-xs text-amber-800 dark:text-amber-300 font-semibold">
                        💡 Suggestion: {recommendation.suggested_action}
                      </div>
                    )}
                  </div>
                )}

                {/* Top Recommendation Product */}
                {recommendation.top_recommendation && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-indigo-500" />
                        <h2 className="text-lg font-bold text-slate-900 dark:text-white">🏆 Best Overall AI Recommendation</h2>
                      </div>
                      <span className="badge badge-indigo text-xs">
                        Deterministic Pick #{recommendation.top_recommendation.rank || 1}
                      </span>
                    </div>

                    <ProductCard
                      product={recommendation.top_recommendation}
                      explanation={recommendation.explanation}
                      tradeOffAnalysis={recommendation.trade_off_analysis}
                      policyStatus={recommendation.policy_status}
                      onAddToCart={() => handleAddToCart(recommendation.top_recommendation)}
                      onInstantBuy={() => handleInstantBuy(recommendation.top_recommendation)}
                      isTopPick={true}
                    />
                  </div>
                )}

                {/* Spotlight Picks: Best Value & Fastest Delivery */}
                {(recommendation.best_value_recommendation || recommendation.fastest_delivery_recommendation) && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {recommendation.best_value_recommendation && recommendation.best_value_recommendation.id !== recommendation.top_recommendation?.id && (
                      <div className="space-y-2">
                        <div className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                          <span>💰</span>
                          <span>Best Value Pick</span>
                        </div>
                        <ProductCard
                          product={{ ...recommendation.best_value_recommendation, badge: 'BEST_VALUE' }}
                          onAddToCart={() => handleAddToCart(recommendation.best_value_recommendation)}
                          onInstantBuy={() => handleInstantBuy(recommendation.best_value_recommendation)}
                          isTopPick={false}
                        />
                      </div>
                    )}

                    {recommendation.fastest_delivery_recommendation && recommendation.fastest_delivery_recommendation.id !== recommendation.top_recommendation?.id && (
                      <div className="space-y-2">
                        <div className="text-xs font-bold text-cyan-600 dark:text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
                          <span>⚡</span>
                          <span>Fastest Delivery Pick</span>
                        </div>
                        <ProductCard
                          product={{ ...recommendation.fastest_delivery_recommendation, badge: 'FASTEST_DELIVERY' }}
                          onAddToCart={() => handleAddToCart(recommendation.fastest_delivery_recommendation)}
                          onInstantBuy={() => handleInstantBuy(recommendation.fastest_delivery_recommendation)}
                          isTopPick={false}
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Why Other Products Were Filtered Out (Rejection Audit) */}
                {recommendation.rejection_summary && Object.keys(recommendation.rejection_summary).length > 0 && recommendation.top_recommendation && (
                  <div className="p-4 rounded-2xl bg-white dark:bg-[#0f172a] border border-slate-200/80 dark:border-white/10 space-y-2 shadow-xs">
                    <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-2">
                      <Scale className="w-4 h-4 text-indigo-500" />
                      <span>Why other products were rejected:</span>
                    </div>
                    <div className="flex flex-wrap gap-2 text-xs">
                      {Object.entries(recommendation.rejection_summary).map(([reason, count]) => (
                        <span key={reason} className="px-3 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-mono text-[11px]">
                          <strong>{reason.replace(/_/g, ' ')}:</strong> {count}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Multi-Merchant Comparison Matrix */}
                {recommendation.comparison_table?.length > 0 && (
                  <ComparisonMatrix 
                    products={recommendation.comparison_table}
                    topProduct={recommendation.top_recommendation}
                    explanation={recommendation.explanation}
                    tradeOffAnalysis={recommendation.trade_off_analysis}
                    onAddToCart={handleAddToCart}
                    onInstantBuy={handleInstantBuy}
                    onSelectProduct={handleInstantBuy}
                  />
                )}
              </div>
            )}
          </main>
        )}

        {/* =====================================================================
            ORDERS VIEW
            ===================================================================== */}
        {activeTab === 'orders' && (
          <main className="p-6 sm:p-8 max-w-6xl mx-auto w-full animate-in fade-in duration-300">
            <OrdersTracker 
              orders={orders}
              onReturnOrder={handleReturnOrder}
            />
          </main>
        )}

        {/* =====================================================================
            SPENDING POLICY & SAFETY VIEW
            ===================================================================== */}
        {activeTab === 'safety' && (
          <main className="p-6 sm:p-8 max-w-6xl mx-auto w-full animate-in fade-in duration-300">
            <SafetyDashboard 
              policy={policy}
              onUpdatePolicy={handleUpdatePolicy}
              auditLedger={auditLedger}
              onVerifyLedger={handleVerifyLedger}
            />
          </main>
        )}

        {/* =====================================================================
            DEV LAB DIAGNOSTICS & SYSTEM ARCHITECTURE
            ===================================================================== */}
        {activeTab === 'brain' && <main className="p-6 max-w-6xl mx-auto w-full"><AgentBrainMap brainState={brainState} onRefresh={fetchInitialData} /></main>}
        {activeTab === 'specialized' && <main className="p-6 max-w-6xl mx-auto w-full"><SpecializedAgentsConsole onTriggerQuery={handleSearchQuery} /></main>}
        {activeTab === 'memory' && <main className="p-6 max-w-6xl mx-auto w-full"><MemoryConsole /></main>}
        {activeTab === 'observability' && <main className="p-6 max-w-6xl mx-auto w-full"><AgentObservabilityConsole /></main>}
        {activeTab === 'merchants' && <main className="p-6 max-w-6xl mx-auto w-full"><MerchantSimulatorExplorer /></main>}
        {activeTab === 'gateway' && <main className="p-6 max-w-6xl mx-auto w-full"><CommerceGatewayExplorer /></main>}
        {activeTab === 'payments' && <main className="p-6 max-w-6xl mx-auto w-full"><DelegatedPaymentSandbox /></main>}
        {activeTab === 'security' && <main className="p-6 max-w-6xl mx-auto w-full"><AgentSecurityCenter /></main>}
        {activeTab === 'permissions' && <main className="p-6 max-w-6xl mx-auto w-full"><ToolPermissionsMatrix /></main>}
        {activeTab === 'resiliency' && <main className="p-6 max-w-6xl mx-auto w-full"><FailureRecoveryCenter /></main>}
        {activeTab === 'benchmark' && <main className="p-6 max-w-6xl mx-auto w-full"><BenchmarkEvaluationConsole /></main>}
        {activeTab === 'architecture' && <main className="p-6 max-w-6xl mx-auto w-full"><SystemArchitectureMap /></main>}
      </div>

      {/* =========================================================================
          MODALS & DRAWERS
          ========================================================================= */}
      {/* Cart Drawer */}
      <CartDrawer 
        isOpen={isCartOpen}
        onClose={() => setIsCartOpen(false)}
        cart={cart}
        onRemoveItem={handleRemoveFromCart}
        onClearCart={handleClearCart}
        onProceedToCheckout={() => {
          if (cart?.items?.[0]) {
            handleInstantBuy(cart.items[0].product);
            setIsCartOpen(false);
          }
        }}
      />

      {/* Human In The Loop Approval Modal */}
      {isHitlModalOpen && (
        <HumanInTheLoopModal 
          isOpen={isHitlModalOpen}
          product={selectedHitlProduct}
          onClose={() => setIsHitlModalOpen(false)}
          onApprove={handleApproveHitl}
          isProcessing={isCheckingOut}
        />
      )}

      {/* Settings Modal */}
      {isSettingsOpen && (
        <ApiSettingsModal 
          isOpen={isSettingsOpen}
          onClose={() => setIsSettingsOpen(false)}
        />
      )}

    </div>
  );
}
