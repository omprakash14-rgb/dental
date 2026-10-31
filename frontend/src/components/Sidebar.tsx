import React from 'react';
import { LayoutDashboard, PlusCircle, Users, FileText, Info, ShieldCheck, ShieldAlert } from 'lucide-react';
import { User } from '../types';

interface SidebarProps {
  currentTab: 'dashboard' | 'new-analysis' | 'patient-history' | 'view-report' | 'audit-logs';
  currentUser: User | null;
  onSelectTab: (tab: 'dashboard' | 'new-analysis' | 'patient-history' | 'audit-logs') => void;
  onOpenDisclaimer: () => void;
  onOpenLogin: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  currentUser,
  onSelectTab,
  onOpenDisclaimer,
  onOpenLogin
}) => {
  const navItems = [
    {
      id: 'dashboard' as const,
      label: 'Dashboard',
      icon: LayoutDashboard,
      description: 'Overview & Statistics'
    },
    {
      id: 'new-analysis' as const,
      label: 'New Dental Analysis',
      icon: PlusCircle,
      description: '3-Angle Photo Upload'
    },
    {
      id: 'patient-history' as const,
      label: 'Patient History',
      icon: Users,
      description: 'Previous Scans & Records'
    }
  ];

  const isAdmin = currentUser?.role === 'admin';

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex-shrink-0 flex flex-col justify-between hidden md:flex h-[calc(100vh-4rem)] sticky top-16">
      <div className="p-4 space-y-1">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          Clinical Navigation
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-start space-x-3 px-3 py-2.5 rounded-xl text-left transition-all ${
                isActive
                  ? 'bg-sky-50 text-sky-800 font-medium shadow-sm border border-sky-100'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Icon className={`w-5 h-5 mt-0.5 flex-shrink-0 ${isActive ? 'text-sky-600' : 'text-slate-400'}`} />
              <div>
                <div className="text-sm">{item.label}</div>
                <div className="text-[11px] text-slate-400 font-normal">{item.description}</div>
              </div>
            </button>
          );
        })}

        {/* Admin Audit Logs Nav Section */}
        <div className="pt-4 px-3 py-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
          DevSecOps & Audit
        </div>
        <button
          onClick={() => {
            if (isAdmin) {
              onSelectTab('audit-logs');
            } else {
              onOpenLogin();
            }
          }}
          className={`w-full flex items-start space-x-3 px-3 py-2.5 rounded-xl text-left transition-all ${
            currentTab === 'audit-logs'
              ? 'bg-purple-50 text-purple-800 font-medium shadow-sm border border-purple-100'
              : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
          }`}
        >
          <ShieldCheck className={`w-5 h-5 mt-0.5 flex-shrink-0 ${currentTab === 'audit-logs' ? 'text-purple-600' : 'text-slate-400'}`} />
          <div>
            <div className="text-sm flex items-center space-x-1.5">
              <span>Security Audit Logs</span>
              {!isAdmin && (
                <span className="text-[9px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-mono font-semibold">
                  ADMIN
                </span>
              )}
            </div>
            <div className="text-[11px] text-slate-400 font-normal">OWASP Ledger & Trails</div>
          </div>
        </button>
      </div>

      {/* Bottom Medical Reminder Box */}
      <div className="p-4 border-t border-slate-100 m-3 rounded-2xl bg-slate-50 border border-slate-200">
        <div className="flex items-center space-x-2 text-slate-800 font-medium text-xs mb-1">
          <Info className="w-4 h-4 text-sky-600" />
          <span>Dentist Clinical Protocol</span>
        </div>
        <p className="text-[11px] text-slate-500 leading-relaxed">
          AI findings provide preliminary pre-screening alerts. All predictions must be confirmed clinically with physical examination and radiography.
        </p>
        <button
          onClick={onOpenDisclaimer}
          className="mt-2 text-[11px] text-sky-600 hover:text-sky-700 font-semibold underline underline-offset-2 block"
        >
          Review Full Disclaimer
        </button>
      </div>
    </aside>
  );
};
