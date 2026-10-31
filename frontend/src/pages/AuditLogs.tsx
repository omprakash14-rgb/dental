import React, { useState, useEffect } from 'react';
import { Shield, RefreshCw, Search, Filter, Lock, CheckCircle, AlertTriangle, FileSpreadsheet, Activity } from 'lucide-react';
import { getAuditLogs } from '../services/api';
import { AuditLogItem, User } from '../types';

interface AuditLogsProps {
  currentUser: User | null;
  onOpenLogin: () => void;
}

export const AuditLogs: React.FC<AuditLogsProps> = ({ currentUser, onOpenLogin }) => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [actionFilter, setActionFilter] = useState('ALL');

  useEffect(() => {
    if (currentUser?.role === 'admin') {
      fetchLogs();
    }
  }, [currentUser]);

  const fetchLogs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getAuditLogs(100);
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load audit logs.');
    } finally {
      setLoading(false);
    }
  };

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      (log.username && log.username.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (log.action && log.action.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (log.resource_type && log.resource_type.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (log.resource_id && log.resource_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (log.ip_address && log.ip_address.includes(searchTerm));

    const matchesAction =
      actionFilter === 'ALL' ||
      log.action.toUpperCase().includes(actionFilter);

    return matchesSearch && matchesAction;
  });

  const getActionBadge = (action: string) => {
    if (action.includes('DELETE')) {
      return 'bg-rose-50 text-rose-700 border-rose-200';
    }
    if (action.includes('LOGIN') || action.includes('REGISTER') || action.includes('LOGOUT')) {
      return 'bg-sky-50 text-sky-700 border-sky-200';
    }
    if (action.includes('SCREENING')) {
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    }
    if (action.includes('PDF')) {
      return 'bg-purple-50 text-purple-700 border-purple-200';
    }
    return 'bg-slate-100 text-slate-700 border-slate-200';
  };

  if (!currentUser || currentUser.role !== 'admin') {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 sm:p-12 text-center max-w-2xl mx-auto my-12">
        <div className="w-16 h-16 bg-rose-50 border border-rose-200 rounded-2xl flex items-center justify-center mx-auto mb-4 text-rose-600 shadow-sm">
          <Lock className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-2">
          Administrator Privileges Required
        </h2>
        <p className="text-sm text-slate-600 mb-6 leading-relaxed">
          Access to institutional security audit logs is strictly restricted to certified <strong>Administrator</strong> accounts. Clinicians and Staff members do not possess clearance to inspect system-wide forensic trails.
        </p>
        <button
          onClick={onOpenLogin}
          className="inline-flex items-center px-4 py-2.5 bg-sky-600 hover:bg-sky-700 text-white font-medium rounded-xl text-sm shadow-sm transition-all"
        >
          <Shield className="w-4 h-4 mr-2" />
          Authenticate as Administrator
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center space-x-2 text-sky-600 text-xs font-semibold uppercase tracking-wider mb-1">
            <Shield className="w-4 h-4" />
            <span>OWASP Compliance & Forensic Governance</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Security Audit Logs
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Immutable forensic ledger tracking authentication, screening events, records destruction, and report downloads.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={fetchLogs}
            disabled={loading}
            className="inline-flex items-center px-3.5 py-2 border border-slate-300 rounded-xl text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Trail
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 font-medium">Total Audited Events</span>
          <p className="text-2xl font-bold text-slate-900 mt-1">{logs.length}</p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-sky-600 font-medium">Auth & Sessions</span>
          <p className="text-2xl font-bold text-sky-700 mt-1">
            {logs.filter(l => l.action.includes('LOGIN') || l.action.includes('LOGOUT') || l.action.includes('REGISTER')).length}
          </p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-emerald-600 font-medium">Screening Pipeline Runs</span>
          <p className="text-2xl font-bold text-emerald-700 mt-1">
            {logs.filter(l => l.action.includes('SCREENING')).length}
          </p>
        </div>
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-xs text-rose-600 font-medium">Records Destruction</span>
          <p className="text-2xl font-bold text-rose-700 mt-1">
            {logs.filter(l => l.action.includes('DELETE')).length}
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search action, user, IP, ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border border-slate-300 rounded-xl text-xs focus:ring-2 focus:ring-sky-500 focus:border-sky-500"
          />
        </div>

        <div className="flex items-center space-x-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-slate-400" />
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-xl px-3 py-2 bg-white text-slate-700 focus:ring-2 focus:ring-sky-500"
          >
            <option value="ALL">All Actions</option>
            <option value="LOGIN">Logins & Auth</option>
            <option value="SCREENING">Screenings</option>
            <option value="PDF">PDF Downloads</option>
            <option value="DELETE">Deletions</option>
          </select>
        </div>
      </div>

      {/* Forensic Privacy Notice */}
      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 text-xs text-emerald-800 flex items-center space-x-2">
        <CheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
        <span>
          <strong>Data Minimization Verified:</strong> Audit records never store patient names, contact info, clinical notes, or intraoral image buffers. Only strictly pseudonymized identifiers and action metadata are persisted.
        </span>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2 text-sky-600" />
            Loading cryptographic audit entries...
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-600 text-sm">
            <AlertTriangle className="w-6 h-6 mx-auto mb-2" />
            {error}
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-slate-400 text-sm">
            No audit records match your search criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Timestamp (UTC)</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Operator</th>
                  <th className="py-3 px-4">Resource Target</th>
                  <th className="py-3 px-4">Origin IP</th>
                  <th className="py-3 px-4 text-center">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono">
                {filteredLogs.map((log) => {
                  const dateStr = new Date(log.created_at).toLocaleString();
                  return (
                    <tr key={log.id} className="hover:bg-slate-50/70 transition-colors">
                      <td className="py-3 px-4 text-slate-600 whitespace-nowrap">
                        {dateStr}
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold border ${getActionBadge(log.action)}`}>
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-900 font-sans font-medium">
                        {log.username || 'System Anonymous'}
                      </td>
                      <td className="py-3 px-4 text-slate-600">
                        {log.resource_type ? (
                          <span>
                            <span className="font-semibold text-slate-700">{log.resource_type}</span>: {log.resource_id || 'n/a'}
                          </span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-slate-500 whitespace-nowrap">
                        {log.ip_address || '127.0.0.1'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold ${
                          (log.status_code ?? 200) >= 200 && (log.status_code ?? 200) < 300
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}>
                          {log.status_code ?? 200}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
