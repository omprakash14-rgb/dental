import React from 'react';
import { Activity, ShieldCheck, Stethoscope, AlertTriangle, AlertCircle, User as UserIcon, LogOut, LogIn, Shield } from 'lucide-react';
import { HealthStatus, User } from '../types';

interface NavbarProps {
  health: HealthStatus | null;
  currentUser: User | null;
  onOpenNewAnalysis: () => void;
  onOpenDisclaimer: () => void;
  onOpenLogin: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  health,
  currentUser,
  onOpenNewAnalysis,
  onOpenDisclaimer,
  onOpenLogin,
  onLogout
}) => {
  const isHealthy = health?.status === 'operational';

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'dentist':
        return 'bg-sky-100 text-sky-800 border-sky-200';
      case 'staff':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  return (
    <>
      {/* Top Prominent Medical Safety Notice Banner */}
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-center text-xs text-amber-900 flex items-center justify-center gap-2 font-medium">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0" />
        <span>
          <strong>Medical Notice:</strong> AI-generated results are preliminary and may be inaccurate. This system does not provide a confirmed diagnosis. Consult a qualified dental professional for clinical evaluation.
        </span>
      </div>

      <header className="bg-white border-b border-slate-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo & Brand */}
            <div className="flex items-center space-x-3">
              <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-sky-600 to-cyan-500 flex items-center justify-center text-white shadow-md shadow-sky-500/20">
                <Stethoscope className="h-6 w-6 stroke-[2.2]" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="text-xl font-bold tracking-tight text-slate-900">
                    Dental<span className="text-sky-600">AI</span>
                  </span>
                  <span className="px-2 py-0.5 text-[11px] font-semibold bg-sky-50 text-sky-700 border border-sky-200 rounded-full">
                    ResNet-50 Pipeline
                  </span>
                </div>
                <p className="text-xs text-slate-500 hidden sm:block">
                  Pretrained Intraoral Computer Vision & Grad-CAM Visual Salience
                </p>
              </div>
            </div>

            {/* Right Status, Auth & Actions */}
            <div className="flex items-center space-x-2 sm:space-x-3">
              {/* Live Model & DB Status Indicator */}
              <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-50 border border-slate-200 text-xs">
                <span className={`h-2.5 w-2.5 rounded-full ${isHealthy ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
                <span className="font-medium text-slate-700">
                  {isHealthy ? 'ResNet-50 Active' : 'Model Degraded'}
                </span>
                <span className="text-slate-300">|</span>
                <span className="text-slate-500 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  {health?.database_type || 'PostgreSQL'}
                </span>
              </div>

              {/* Disclaimer Button */}
              <button
                onClick={onOpenDisclaimer}
                className="px-2.5 py-1.5 rounded-lg border border-amber-200 bg-amber-50 hover:bg-amber-100 text-amber-800 text-xs font-semibold flex items-center gap-1.5 transition-colors"
                title="View Clinical Limitations & Disclaimer"
              >
                <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                <span className="hidden sm:inline">Notice</span>
              </button>

              {/* Authentication Status Badge / Sign In Button */}
              {currentUser ? (
                <div className="flex items-center space-x-2 bg-slate-50 border border-slate-200 rounded-xl px-2.5 py-1">
                  <div className="w-7 h-7 rounded-lg bg-sky-600 text-white flex items-center justify-center font-bold text-xs uppercase shadow-sm">
                    {currentUser.username.substring(0, 2)}
                  </div>
                  <div className="hidden md:block text-left pr-1">
                    <div className="text-xs font-semibold text-slate-800 leading-tight">
                      {currentUser.full_name || currentUser.username}
                    </div>
                    <div className="flex items-center gap-1">
                      <span className={`px-1.5 py-0.2 text-[10px] uppercase font-bold rounded border ${getRoleBadge(currentUser.role)}`}>
                        {currentUser.role}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={onLogout}
                    title="Sign Out of Session"
                    className="p-1 hover:bg-slate-200 rounded-lg text-slate-500 hover:text-slate-800 transition-colors ml-1"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={onOpenLogin}
                  className="inline-flex items-center px-3 py-1.5 border border-slate-300 rounded-xl text-xs font-medium text-slate-700 bg-white hover:bg-slate-50 transition-colors shadow-sm"
                >
                  <LogIn className="w-3.5 h-3.5 mr-1 text-sky-600" />
                  <span>Sign In</span>
                </button>
              )}

              {/* Quick Action Button */}
              <button
                onClick={onOpenNewAnalysis}
                className="inline-flex items-center px-3.5 py-1.5 border border-transparent text-xs font-semibold rounded-lg shadow-sm text-white bg-sky-600 hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 transition-all shadow-sky-600/20"
              >
                <Activity className="w-3.5 h-3.5 mr-1.5" />
                <span>New Scan</span>
              </button>
            </div>
          </div>
        </div>
      </header>
    </>
  );
};
