import { useState } from 'react';
import { 
  TrendingUp, 
  Zap, 
  Download, 
  Filter, 
  Maximize2, 
  History,
  Activity,
  Box,
  Map,
  ShieldCheck,
  Cpu
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { StatsCard } from '../components/ui/StatsCard';
import { MovementTrendsChart } from '../components/ui/MovementTrendsChart';
import { AIInsights } from '../components/ui/AIInsights';
import { useDashboardSummary } from '../hooks/useDashboard';
import { cn } from '../lib/utils';

const Analytics = () => {
  const { data, isLoading } = useDashboardSummary();
  const [activeTab, setActiveTab] = useState('performance');

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-8 pb-10 max-w-[1600px] mx-auto"
    >
      {/* 1. Header Section with BI Switcher */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-8 relative">
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-brand-primary/10 rounded-full blur-[120px] pointer-events-none" />
        
        <div className="space-y-3 relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-brand-primary/10 text-brand-primary rounded-full text-[10px] font-black uppercase tracking-widest border border-brand-primary/20">
            <Cpu className="w-3 h-3 animate-spin-slow" /> AI Intelligence Hub
          </div>
          <h1 className="text-5xl font-black text-slate-900 tracking-tighter" style={{ fontFamily: 'Outfit' }}>
            System Intelligence
          </h1>
          <p className="text-slate-500 font-medium tracking-tight text-lg max-w-xl">
            Real-time business intelligence and predictive analytics for institutional resource management.
          </p>
        </div>

        <div className="flex items-center gap-4 relative z-10">
          <div className="flex bg-white/80 backdrop-blur-md p-1.5 rounded-2xl border border-slate-200/60 shadow-xl">
            {['performance', 'geospatial', 'compliance'].map(tab => (
              <button 
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "px-6 py-2.5 text-xs font-black uppercase tracking-widest rounded-xl transition-all duration-300",
                  activeTab === tab ? "bg-slate-900 text-white shadow-lg" : "text-slate-400 hover:text-slate-600 hover:bg-slate-50"
                )}
              >
                {tab}
              </button>
            ))}
          </div>
          <button className="p-3.5 bg-white border border-slate-200 rounded-2xl text-slate-400 hover:text-brand-primary hover:border-brand-primary/50 transition-all shadow-lg hover:shadow-xl group">
             <Download className="w-5 h-5 group-hover:scale-110 transition-transform" />
          </button>
        </div>
      </div>

      {/* 2. Main Intelligence Grid */}
      <AnimatePresence mode="wait">
        <motion.div 
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
          className="grid grid-cols-1 xl:grid-cols-4 gap-8"
        >
          {activeTab === 'performance' && (
            <>
              {/* Left 3 Columns: Charts and Metrics */}
              <div className="xl:col-span-3 space-y-8">
                {/* Top Level Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                   <StatsCard 
                    title="System Efficiency" 
                    value="94.2%" 
                    icon={Zap} 
                    color="amber"
                    description="Optimal throughput"
                    loading={isLoading}
                    trend={{ value: 4.2, isUp: true }}
                  />
                  <StatsCard 
                    title="Asset ROI" 
                    value="22.5%" 
                    icon={TrendingUp} 
                    color="emerald"
                    description="Value recovery rate"
                    loading={isLoading}
                    trend={{ value: 1.8, isUp: true }}
                  />
                </div>

                {/* Central Visualization Hub */}
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                   {/* Main Area Chart (3/5) */}
                   <div className="lg:col-span-3 enterprise-card p-0 overflow-hidden bg-white/40 backdrop-blur-md shadow-2xl shadow-slate-200/50 flex flex-col h-[600px] border-none group">
                      <div className="p-8 border-b border-slate-100/50 flex justify-between items-center">
                         <div className="space-y-1">
                            <h3 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-3">
                               <div className="w-2 h-8 bg-brand-primary rounded-full group-hover:scale-y-125 transition-transform origin-center" />
                               Resource Utilization Trends
                            </h3>
                            <p className="text-xs text-slate-400 font-bold uppercase tracking-widest">Real-time Movement Analytics</p>
                         </div>
                      </div>
                      <div className="p-8 flex-1">
                         <MovementTrendsChart data={data?.movement_stats || {}} loading={isLoading} />
                      </div>
                      <div className="px-8 py-6 bg-slate-50/50 border-t border-slate-100/50 flex items-center justify-between">
                         <div className="flex items-center gap-6">
                            <div className="flex items-center gap-2">
                               <div className="w-2.5 h-2.5 rounded-full bg-brand-500" />
                               <span className="text-xs font-bold text-slate-600">Inbound Flow</span>
                            </div>
                            <div className="flex items-center gap-2">
                               <div className="w-2.5 h-2.5 rounded-full bg-brand-300" />
                               <span className="text-xs font-bold text-slate-600">Outbound Flow</span>
                            </div>
                         </div>
                         <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Updated 3s ago</span>
                      </div>
                   </div>

                   {/* Status Distribution */}
                   <div className="lg:col-span-2 space-y-8">
                      <div className="enterprise-card h-[600px] p-8 bg-white shadow-xl shadow-slate-200/50 border-none group flex flex-col">
                         <div className="flex items-center gap-3 mb-8">
                            <div className="p-2.5 bg-indigo-50 rounded-xl text-indigo-600 group-hover:rotate-12 transition-transform">
                               <Box className="w-5 h-5" />
                            </div>
                            <h4 className="font-bold text-slate-800 tracking-tight">Status Distribution</h4>
                         </div>
                         <div className="space-y-8 flex-1 flex flex-col justify-center">
                            {[
                              { label: 'In Use', count: 48, color: 'bg-emerald-500', pct: 65 },
                              { label: 'Maintenance', count: 12, color: 'bg-amber-500', pct: 15 },
                              { label: 'Reserved', count: 24, color: 'bg-indigo-500', pct: 20 },
                            ].map(item => (
                              <div key={item.label} className="space-y-3">
                                 <div className="flex justify-between items-center text-[11px] font-black uppercase tracking-wider">
                                    <span className="text-slate-400">{item.label}</span>
                                    <span className="text-slate-900">{item.count} Assets</span>
                                 </div>
                                 <div className="w-full h-2 bg-slate-50 rounded-full overflow-hidden">
                                    <motion.div 
                                      initial={{ width: 0 }}
                                      animate={{ width: `${item.pct}%` }}
                                      transition={{ duration: 1, delay: 0.2 }}
                                      className={cn("h-full", item.color)}
                                    />
                                 </div>
                              </div>
                            ))}
                         </div>
                      </div>
                   </div>
                </div>
              </div>

              {/* Right 1 Column: Intelligence & Feed */}
              <div className="space-y-8">
                {/* Real-time Activity Hub */}
                <div className="enterprise-card p-0 overflow-hidden bg-white border-none shadow-xl shadow-slate-200/50 h-[700px] flex flex-col">
                   <div className="p-6 border-b border-slate-100 flex items-center justify-between">
                      <h4 className="font-bold text-slate-800 flex items-center gap-3 text-sm">
                         <Activity className="w-4 h-4 text-brand-primary animate-pulse" />
                         Live Intelligence Stream
                      </h4>
                      <div className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                   </div>
                   <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
                      {[1, 2, 3, 4, 5, 6, 7].map(i => (
                        <div key={i} className="flex gap-4 group/item">
                           <div className="w-1.5 h-12 bg-slate-100 rounded-full group-hover/item:bg-brand-primary transition-colors flex-shrink-0" />
                           <div className="space-y-1">
                              <p className="text-[11px] font-black text-slate-400 uppercase tracking-widest">3m ago • Warehouse A</p>
                              <h5 className="text-xs font-bold text-slate-800 leading-tight">Asset Scan: Verification successful.</h5>
                              <div className="flex items-center gap-2 mt-2">
                                 <div className="w-4 h-4 rounded-full bg-indigo-50 flex items-center justify-center">
                                    <History className="w-2.5 h-2.5 text-indigo-600" />
                                 </div>
                                 <span className="text-[10px] font-bold text-indigo-600 uppercase">Movement Detected</span>
                              </div>
                           </div>
                        </div>
                      ))}
                   </div>
                   <div className="p-4 bg-slate-50 text-center border-t border-slate-100">
                      <button className="text-[10px] font-black text-brand-primary uppercase tracking-widest hover:underline">View Full Activity Log</button>
                   </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'geospatial' && (
            <div className="xl:col-span-4 grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Geolocation Card */}
              <div className="enterprise-card h-[600px] bg-slate-900 text-white p-12 relative overflow-hidden group shadow-2xl shadow-brand-primary/20 border-none">
                 <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-10" />
                 <div className="relative z-10 flex flex-col h-full">
                    <div className="flex justify-between items-start mb-6">
                       <div className="space-y-2">
                          <h4 className="text-3xl font-bold tracking-tight">Geospatial Nodes</h4>
                          <p className="text-xs font-black uppercase tracking-[0.2em] text-brand-primary">Active Institutional Maps</p>
                       </div>
                       <div className="p-4 bg-white/10 rounded-2xl backdrop-blur-md">
                          <Map className="w-8 h-8 text-brand-primary" />
                       </div>
                    </div>
                    <div className="mt-auto space-y-6">
                       <div className="flex items-end justify-between">
                          <span className="text-7xl font-black">12</span>
                          <span className="text-sm font-bold text-brand-400">+2 New Nodes Active</span>
                       </div>
                       <div className="w-full h-3 bg-white/5 rounded-full overflow-hidden">
                          <motion.div 
                             initial={{ width: 0 }}
                             animate={{ width: '85%' }}
                             transition={{ duration: 1.5 }}
                             className="h-full bg-brand-primary shadow-[0_0_15px_rgba(14,165,233,0.8)]"
                          />
                       </div>
                    </div>
                 </div>
                 {/* Animated Background Pulse */}
                 <div className="absolute bottom-0 right-0 w-64 h-64 bg-brand-primary/20 rounded-full blur-[80px] animate-pulse" />
              </div>
              
              {/* Geospatial Stats */}
              <div className="enterprise-card p-12 bg-white shadow-xl shadow-slate-200/50 border-none h-[600px] flex flex-col justify-center">
                 <h3 className="text-2xl font-bold text-slate-800 mb-8">Location Distribution</h3>
                 <div className="space-y-6">
                   <div className="flex justify-between items-center p-4 bg-slate-50 rounded-xl border border-slate-100">
                     <span className="font-bold text-slate-600">HQ Warehouse</span>
                     <span className="px-3 py-1 bg-brand-50 text-brand-600 rounded-md font-black text-xs">65%</span>
                   </div>
                   <div className="flex justify-between items-center p-4 bg-slate-50 rounded-xl border border-slate-100">
                     <span className="font-bold text-slate-600">Branch Office A</span>
                     <span className="px-3 py-1 bg-brand-50 text-brand-600 rounded-md font-black text-xs">20%</span>
                   </div>
                   <div className="flex justify-between items-center p-4 bg-slate-50 rounded-xl border border-slate-100">
                     <span className="font-bold text-slate-600">Remote Sites</span>
                     <span className="px-3 py-1 bg-brand-50 text-brand-600 rounded-md font-black text-xs">15%</span>
                   </div>
                 </div>
              </div>
            </div>
          )}

          {activeTab === 'compliance' && (
            <>
              <div className="xl:col-span-3 space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <StatsCard 
                    title="Audit Variance" 
                    value="0.02%" 
                    icon={ShieldCheck} 
                    color="indigo"
                    description="Physical vs Digital Records"
                    loading={isLoading}
                    trend={{ value: 0.01, isUp: false }}
                  />
                  <StatsCard 
                    title="Compliance Score" 
                    value="98.5%" 
                    icon={TrendingUp} 
                    color="emerald"
                    description="Regulatory Alignment"
                    loading={isLoading}
                    trend={{ value: 0.5, isUp: true }}
                  />
                </div>
                <div className="enterprise-card p-10 bg-white border-none shadow-xl shadow-slate-200/50 min-h-[500px]">
                   <AIInsights />
                </div>
              </div>
              <div className="xl:col-span-1 space-y-8">
                <div className="enterprise-card p-8 bg-rose-600 text-white border-none shadow-xl shadow-rose-200 min-h-[500px]">
                   <h4 className="text-xs font-black uppercase tracking-[0.2em] mb-6 flex items-center gap-2">
                      <Activity className="w-5 h-5" /> Security Alerts
                   </h4>
                   <div className="space-y-4">
                      <div className="bg-white/10 p-5 rounded-2xl border border-white/20">
                         <p className="text-sm font-bold leading-relaxed">No critical anomalies detected in the current audit cycle.</p>
                      </div>
                   </div>
                </div>
              </div>
            </>
          )}

        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
};

export default Analytics;
