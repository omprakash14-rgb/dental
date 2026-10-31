import React from 'react';
import {
  Users,
  Activity,
  AlertTriangle,
  Clock,
  ArrowRight,
  TrendingUp,
  ShieldCheck,
  CheckCircle2,
  FileText,
  AlertCircle
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  AreaChart,
  Area
} from 'recharts';
import { DashboardStats } from '../types';

interface DashboardProps {
  stats: DashboardStats | null;
  loading: boolean;
  onNavigateNewAnalysis: () => void;
  onViewReport: (reportId: string) => void;
  onViewPatient: (patientId: string) => void;
}

const COLORS = ['#0284c7', '#0d9488', '#f59e0b', '#ef4444', '#8b5cf6', '#64748b'];

export const Dashboard: React.FC<DashboardProps> = ({
  stats,
  loading,
  onNavigateNewAnalysis,
  onViewReport,
  onViewPatient
}) => {
  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-10 h-10 border-4 border-sky-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-500 font-medium">Loading clinical metrics...</p>
        </div>
      </div>
    );
  }

  // Format data for Recharts bar chart
  const diseaseChartData = stats
    ? Object.entries(stats.disease_distribution).map(([name, count]) => ({
        name: name.replace('Dental ', '').replace(' (Tartar)', '').replace(' (Tooth Decay)', '').replace(' / Missing Tooth', ''),
        fullName: name,
        detections: count
      }))
    : [];

  // Format data for Recharts pie chart
  const urgencyChartData = stats
    ? Object.entries(stats.urgency_distribution).map(([name, value]) => ({
        name,
        value
      }))
    : [];

  const timelineData = stats?.scans_over_time || [];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-sky-900 via-sky-800 to-cyan-900 rounded-3xl p-6 sm:p-8 text-white shadow-xl shadow-sky-950/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-xs text-xs font-semibold text-sky-200 mb-3 border border-white/10">
            <ShieldCheck className="w-4 h-4 text-sky-300" />
            <span>AI Model ResNet-50 v1.0 • Intraoral Calibrated</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Dental Disease Diagnostic Dashboard
          </h1>
          <p className="mt-1 text-sm text-sky-200 max-w-2xl leading-relaxed">
            Multi-angle photographic pre-screening analyzing Front, Left, and Right views to highlight possible caries, calculus, gingivitis, and oral mucosal alterations.
          </p>
        </div>

        <button
          onClick={onNavigateNewAnalysis}
          className="px-6 py-3 rounded-2xl bg-white text-sky-900 hover:bg-sky-50 font-bold text-sm shadow-lg shadow-black/10 flex items-center gap-2 transition-all transform hover:-translate-y-0.5 whitespace-nowrap"
        >
          <span>Initiate 3-View Scan</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600">
            <Users className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{stats?.total_patients ?? 0}</div>
            <div className="text-xs text-slate-500 font-medium">Registered Patients</div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-teal-50 border border-teal-100 flex items-center justify-center text-teal-600">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{stats?.total_scans ?? 0}</div>
            <div className="text-xs text-slate-500 font-medium">Total Multi-Angle Scans</div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">{stats?.completed_scans ?? stats?.total_scans ?? 0}</div>
            <div className="text-xs text-slate-500 font-medium">Completed Screenings</div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-5 border border-slate-200/80 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">
              {stats?.inconclusive_scans ?? 0}
            </div>
            <div className="text-xs text-slate-500 font-medium">Inconclusive Views</div>
          </div>
        </div>
      </div>

      {/* Analytics Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Disease Detections Bar Chart */}
        <div className="lg:col-span-2 bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">Model-Predicted Category Frequency</h3>
              <p className="text-xs text-slate-500">
                Distribution of neural network predictions across scans • <i>Not confirmed clinical prevalence</i>
              </p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700">
              All Views
            </span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={diseaseChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} interval={0} angle={-15} textAnchor="end" />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip
                  formatter={(val: any, _name: any, item: any) => [`${val} detections`, item.payload.fullName]}
                  contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', color: '#fff', fontSize: '12px', border: 'none' }}
                />
                <Bar dataKey="detections" fill="#0284c7" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Urgency Distribution Pie Chart */}
        <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs flex flex-col justify-between">
          <div className="mb-2">
            <h3 className="text-base font-bold text-slate-900">Triage Priority Breakdown</h3>
            <p className="text-xs text-slate-500">Clinical priority categories assigned across scans</p>
          </div>

          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={urgencyChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {urgencyChartData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', color: '#fff', fontSize: '12px', border: 'none' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Screening Trends Over Time Chart */}
      {timelineData.length > 0 && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-sky-600" />
                <span>Screening Activity Over Time</span>
              </h3>
              <p className="text-xs text-slate-500">Daily multi-view photographic screening volume recorded in PostgreSQL</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-sky-50 text-sky-700 border border-sky-100">
              Live DB Records
            </span>
          </div>

          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timelineData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="scanGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0284c7" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#0284c7" stopOpacity={0.0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', color: '#fff', fontSize: '12px', border: 'none' }}
                />
                <Area type="monotone" dataKey="scans" stroke="#0284c7" strokeWidth={2.5} fillOpacity={1} fill="url(#scanGradient)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Recent Analyses Table */}
      <div className="bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="px-6 py-5 border-b border-slate-100 flex justify-between items-center">
          <div>
            <h3 className="text-base font-bold text-slate-900">Recent Dental Analyses</h3>
            <p className="text-xs text-slate-500">Chronological feed of patient multi-view scans</p>
          </div>
          <button
            onClick={onNavigateNewAnalysis}
            className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
          >
            <span>Run New Scan</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {stats && stats.recent_analyses.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100">
              <thead className="bg-slate-50/70 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-left">
                <tr>
                  <th className="px-6 py-3.5">Patient Details</th>
                  <th className="px-6 py-3.5">Analysis / Report ID</th>
                  <th className="px-6 py-3.5">Overall Finding</th>
                  <th className="px-6 py-3.5">Urgency Level</th>
                  <th className="px-6 py-3.5">Timestamp</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
                {stats.recent_analyses.map((scan) => {
                  const isHigh = scan.urgency_level === 'High Priority';
                  const isModerate = scan.urgency_level.includes('Moderate');
                  return (
                    <tr key={scan.analysis_id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="font-semibold text-slate-900">{scan.patient_name}</div>
                        <div className="text-xs text-slate-400 font-mono">{scan.patient_id}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-mono text-xs text-sky-700 font-medium">
                          {scan.report_id}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs font-medium text-slate-800">
                        {scan.overall_status}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          isHigh
                            ? 'bg-red-50 text-red-700 border border-red-200'
                            : isModerate
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        }`}>
                          {scan.urgency_level}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-xs text-slate-500">
                        {new Date(scan.created_at).toLocaleDateString(undefined, {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <button
                          onClick={() => onViewReport(scan.report_id)}
                          className="px-3 py-1.5 rounded-lg bg-sky-50 hover:bg-sky-100 text-sky-700 text-xs font-semibold transition-colors inline-flex items-center gap-1"
                        >
                          <FileText className="w-3.5 h-3.5" />
                          <span>View Report</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-12 text-center text-slate-500">
            <Activity className="w-10 h-10 mx-auto mb-3 text-slate-300 stroke-[1.5]" />
            <h4 className="text-sm font-semibold text-slate-800">No analyses performed yet</h4>
            <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
              Start by uploading the three required intraoral photographs in the New Dental Analysis section.
            </p>
            <button
              onClick={onNavigateNewAnalysis}
              className="mt-4 px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow-xs"
            >
              Start First Scan
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

