import { useState } from 'react';
import { 
  FileText, 
  FileSpreadsheet, 
  ShieldCheck, 
  Wrench, 
  Trash2, 
  CloudDownload,
  Search,
  Calendar,
  Lock,
  ArrowRight
} from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '../lib/utils';

const REPORT_TYPES = [
  {
    id: 'asset-register',
    title: 'Master Asset Register',
    subtitle: 'Consolidated Institutional Ledger',
    description: 'Comprehensive report of all institutional assets, including current valuation, depreciation schedules, and verification metadata.',
    formats: ['pdf', 'excel'],
    icon: FileText,
    color: 'from-indigo-500 to-blue-600',
    endpoint: '/api/reports/asset-register'
  },
  {
    id: 'maintenance',
    title: 'Predictive Maintenance',
    subtitle: 'Technical Service Schedule',
    description: 'Advanced report identifying assets requiring technical attention based on service intervals and condition flags.',
    formats: ['pdf'],
    icon: Wrench,
    color: 'from-amber-400 to-orange-600',
    endpoint: '/api/reports/maintenance'
  },
  {
    id: 'disposal',
    title: 'Institutional Disposal',
    subtitle: 'Decommissioning Verification',
    description: 'Official register of condemned assets recommended for decommissioning under institutional guidelines.',
    formats: ['pdf'],
    icon: Trash2,
    color: 'from-rose-500 to-pink-600',
    endpoint: '/api/reports/disposal'
  },
  {
    id: 'audit-trail',
    title: 'Security Compliance Audit',
    subtitle: 'Verifiable System Interactions',
    description: 'Deep-dive security log of all institutional asset movements and personnel interactions for compliance verification.',
    formats: ['pdf'],
    icon: ShieldCheck,
    color: 'from-slate-700 to-slate-900',
    endpoint: '/api/reports/audit-trail'
  }
];

const Reports = () => {
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const downloadReport = (endpoint: string, format: string) => {
    let url = `${endpoint}?format=${format}`;
    if (dateFrom) {
      url += `&date_from=${new Date(dateFrom).toISOString()}`;
    }
    if (dateTo) {
      url += `&date_to=${new Date(dateTo).toISOString()}`;
    }
    window.open(url, '_blank');
  };

  return (
    <div className="max-w-7xl mx-auto space-y-12 pb-20 relative">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-brand-primary/5 rounded-full blur-[150px] -mr-48 -mt-48 pointer-events-none" />
      
      {/* Header Intelligence Hub */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-10 relative z-10">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-white shadow-sm border border-slate-200 rounded-full">
             <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
             <span className="text-[11px] font-black uppercase tracking-[0.2em] text-slate-500">Report Engine: Verified & Secured</span>
          </div>
          <h1 className="text-6xl font-black text-slate-900 tracking-tighter" style={{ fontFamily: 'Outfit' }}>
             Institutional <span className="text-brand-primary">Intelligence</span> Hub
          </h1>
          <p className="text-slate-500 font-medium text-xl max-w-2xl leading-relaxed">
             Access audit-ready documentation and high-expertise business intelligence exports. 
             All reports are generated with cryptographic signatures for verifiable compliance.
          </p>
        </div>

        <div className="flex flex-col gap-4 min-w-[300px]">
           <div className="bg-slate-900 rounded-[2rem] p-8 text-white relative overflow-hidden group shadow-2xl">
              <div className="absolute inset-0 bg-gradient-to-br from-brand-primary/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <div className="relative z-10">
                 <h4 className="text-xs font-black uppercase tracking-widest text-slate-400 mb-2">System Status</h4>
                 <div className="flex items-end gap-3 mb-4">
                    <span className="text-4xl font-black tracking-tighter">100%</span>
                    <span className="text-xs font-bold text-emerald-400 mb-1.5">Uptime</span>
                 </div>
                 <div className="flex items-center gap-2 text-[11px] font-bold text-slate-500">
                    <Lock className="w-3.5 h-3.5" />
                    <span>SECURED BY NOVASUITE CORE</span>
                 </div>
              </div>
           </div>
        </div>
      </div>

      {/* Professional Search & Filters */}
      <div className="glass-panel p-3 rounded-[2rem] border-slate-200/50 bg-white/40 flex flex-col md:flex-row items-center gap-4 relative z-10 shadow-xl shadow-slate-100/50">
         <div className="relative flex-1 group w-full">
            <Search className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-brand-primary transition-colors" />
            <input 
               type="text" 
               placeholder="Search intelligence reports, audit years, or department archives..."
               className="w-full bg-white border border-transparent rounded-2xl py-4 pl-14 pr-6 text-sm font-medium focus:ring-4 focus:ring-brand-primary/10 transition-all outline-none shadow-sm"
            />
         </div>
         <div className="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
            <div className="flex items-center bg-white border border-slate-100 rounded-2xl px-4 py-3 shadow-sm h-full">
               <Calendar className="w-4 h-4 text-slate-400 mr-3" />
               <input 
                  type="datetime-local" 
                  value={dateFrom}
                  onChange={(e) => setDateFrom(e.target.value)}
                  className="bg-transparent text-xs font-bold text-slate-600 outline-none w-36"
                  title="Date From"
               />
               <span className="text-slate-300 mx-2">-</span>
               <input 
                  type="datetime-local" 
                  value={dateTo}
                  onChange={(e) => setDateTo(e.target.value)}
                  className="bg-transparent text-xs font-bold text-slate-600 outline-none w-36"
                  title="Date To"
               />
            </div>
            <button 
              onClick={() => { setDateFrom(''); setDateTo(''); }}
              className="flex items-center justify-center px-6 py-3.5 bg-slate-900 border border-slate-900 rounded-2xl text-xs font-black uppercase tracking-widest text-white hover:bg-black transition-all shadow-lg h-full"
            >
               Clear Filters
            </button>
         </div>
      </div>

      {/* Intelligence Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 relative z-10">
        {REPORT_TYPES.map((report, index) => (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            key={report.id}
            className="enterprise-card p-1 bg-white border-none shadow-2xl shadow-slate-200/50 hover:shadow-brand-primary/20 transition-all duration-500 group overflow-hidden"
          >
            <div className="p-8 h-full flex flex-col">
               <div className="flex gap-6 mb-10">
                  <div className={cn(
                    "w-20 h-20 rounded-[2rem] flex items-center justify-center flex-shrink-0 shadow-2xl bg-gradient-to-br transition-transform group-hover:scale-110 duration-500 text-white",
                    report.color
                  )}>
                     <report.icon className="w-10 h-10" />
                  </div>
                  <div className="space-y-1">
                     <h3 className="text-2xl font-black text-slate-900 tracking-tight leading-tight">{report.title}</h3>
                     <p className="text-[11px] font-black uppercase tracking-[0.25em] text-brand-primary">{report.subtitle}</p>
                     <p className="text-sm text-slate-500 font-medium leading-relaxed mt-4 line-clamp-3">
                        {report.description}
                     </p>
                  </div>
               </div>

               <div className="mt-auto pt-8 border-t border-slate-50 flex items-center justify-between">
                  <div className="flex gap-3">
                     {report.formats.includes('pdf') && (
                        <button 
                           onClick={() => downloadReport(report.endpoint, 'pdf')}
                           className="flex items-center gap-2.5 px-6 py-3 bg-slate-900 text-white rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-brand-primary transition-all shadow-lg hover:-translate-y-1"
                        >
                           <CloudDownload className="w-4 h-4" /> Download PDF
                        </button>
                     )}
                     {report.formats.includes('excel') && (
                        <button 
                           onClick={() => downloadReport(report.endpoint, 'excel')}
                           className="flex items-center gap-2.5 px-6 py-3 bg-white border-2 border-slate-100 text-slate-600 rounded-xl text-[10px] font-black uppercase tracking-widest hover:border-emerald-500 hover:text-emerald-600 transition-all shadow-sm hover:-translate-y-1"
                        >
                           <FileSpreadsheet className="w-4 h-4" /> Export XLSX
                        </button>
                     )}
                  </div>
                  <div className="hidden sm:flex flex-col items-end opacity-0 group-hover:opacity-100 transition-opacity">
                     <span className="text-[9px] font-black text-slate-400 uppercase tracking-widest">Last Generated</span>
                     <span className="text-xs font-bold text-slate-900">Today, 09:12 AM</span>
                  </div>
               </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Intelligence Footer */}
      <div className="p-12 bg-white rounded-[3rem] shadow-2xl shadow-slate-200/50 flex flex-col lg:flex-row items-center gap-10 relative overflow-hidden group">
         <div className="absolute inset-0 bg-gradient-to-r from-brand-primary/5 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
         <div className="w-24 h-24 rounded-3xl bg-brand-primary/10 flex items-center justify-center flex-shrink-0">
            <ShieldCheck className="w-12 h-12 text-brand-primary" />
         </div>
         <div className="flex-1 space-y-3">
            <h3 className="text-2xl font-black text-slate-900 tracking-tight" style={{ fontFamily: 'Outfit' }}>Enterprise Integrity Verified</h3>
            <p className="text-slate-500 font-medium leading-relaxed max-w-2xl">
               All reports are generated with cryptographically secured institutional signatures. 
               The Nova Lite System Intelligence Hub ensures that your institution remains audit-ready 24/7 with zero data discrepancies.
            </p>
         </div>
         <button className="flex items-center gap-3 px-8 py-5 bg-brand-primary text-white rounded-[1.5rem] font-black text-xs uppercase tracking-widest shadow-2xl hover:bg-brand-600 transition-all shadow-brand-primary/20">
            Verify Integrity <ArrowRight className="w-4 h-4" />
         </button>
      </div>
    </div>
  );
};

export default Reports;
