import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { DisclaimerModal } from './components/DisclaimerModal';
import { LoginModal } from './components/LoginModal';
import { Dashboard } from './pages/Dashboard';
import { NewAnalysis } from './pages/NewAnalysis';
import { AnalysisResult } from './pages/AnalysisResult';
import { PatientHistory } from './pages/PatientHistory';
import { AuditLogs } from './pages/AuditLogs';
import { getHealth, getDashboardStats, getReport, getCurrentUser, logout } from './services/api';
import { DashboardStats, HealthStatus, ReportDetail, PatientInfo, User } from './types';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<'dashboard' | 'new-analysis' | 'patient-history' | 'view-report' | 'audit-logs'>('dashboard');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loadingStats, setLoadingStats] = useState(false);
  const [activeReport, setActiveReport] = useState<ReportDetail | null>(null);
  const [preselectedPatient, setPreselectedPatient] = useState<PatientInfo | null>(null);
  const [isDisclaimerOpen, setIsDisclaimerOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [isLoginOpen, setIsLoginOpen] = useState(false);

  useEffect(() => {
    fetchInitialData();
    checkCurrentUser();
  }, []);

  const checkCurrentUser = async () => {
    try {
      const user = await getCurrentUser();
      setCurrentUser(user);
    } catch {
      setCurrentUser(null);
    }
  };

  const fetchInitialData = async () => {
    try {
      const h = await getHealth();
      setHealth(h);
    } catch (e) {
      console.warn("Could not retrieve health status", e);
    }

    try {
      setLoadingStats(true);
      const s = await getDashboardStats();
      setStats(s);
    } catch (e) {
      console.warn("Could not retrieve dashboard stats", e);
    } finally {
      setLoadingStats(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    setCurrentUser(null);
    if (currentTab === 'audit-logs') {
      setCurrentTab('dashboard');
    }
  };

  const handleAnalysisSuccess = (report: ReportDetail) => {
    setActiveReport(report);
    setCurrentTab('view-report');
    // Refresh stats in background
    getDashboardStats().then(setStats).catch(() => {});
  };

  const handleViewReportById = async (reportId: string) => {
    try {
      const report = await getReport(reportId);
      setActiveReport(report);
      setCurrentTab('view-report');
    } catch (e) {
      alert(`Could not load report: ${e}`);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Navbar */}
      <Navbar
        health={health}
        currentUser={currentUser}
        onOpenNewAnalysis={() => setCurrentTab('new-analysis')}
        onOpenDisclaimer={() => setIsDisclaimerOpen(true)}
        onOpenLogin={() => setIsLoginOpen(true)}
        onLogout={handleLogout}
      />

      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        {/* Left Sidebar */}
        <Sidebar
          currentTab={currentTab}
          currentUser={currentUser}
          onSelectTab={(tab) => setCurrentTab(tab)}
          onOpenDisclaimer={() => setIsDisclaimerOpen(true)}
          onOpenLogin={() => setIsLoginOpen(true)}
        />

        {/* Main Content Area */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto">
          {currentTab === 'dashboard' && (
            <Dashboard
              stats={stats}
              loading={loadingStats}
              onNavigateNewAnalysis={() => setCurrentTab('new-analysis')}
              onViewReport={handleViewReportById}
              onViewPatient={() => setCurrentTab('patient-history')}
            />
          )}

          {currentTab === 'new-analysis' && (
            <NewAnalysis
              onAnalysisSuccess={handleAnalysisSuccess}
              onOpenDisclaimer={() => setIsDisclaimerOpen(true)}
              preselectedPatient={preselectedPatient}
            />
          )}

          {currentTab === 'view-report' && activeReport && (
            <AnalysisResult
              report={activeReport}
              onBackToDashboard={() => setCurrentTab('dashboard')}
              onNewScan={() => {
                setPreselectedPatient(null);
                setCurrentTab('new-analysis');
              }}
              onOpenDisclaimer={() => setIsDisclaimerOpen(true)}
            />
          )}

          {currentTab === 'patient-history' && (
            <PatientHistory
              onViewReport={handleViewReportById}
              onNewScanForPatient={(patient) => {
                setPreselectedPatient(patient);
                setCurrentTab('new-analysis');
              }}
            />
          )}

          {currentTab === 'audit-logs' && (
            <AuditLogs
              currentUser={currentUser}
              onOpenLogin={() => setIsLoginOpen(true)}
            />
          )}
        </main>
      </div>

      {/* Medical Governance Disclaimer Modal */}
      <DisclaimerModal
        isOpen={isDisclaimerOpen}
        onClose={() => setIsDisclaimerOpen(false)}
      />

      {/* Clinician Authentication Modal */}
      <LoginModal
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onSuccess={(user) => {
          setCurrentUser(user);
          // Refresh dashboard stats with newly authenticated session
          getDashboardStats().then(setStats).catch(() => {});
        }}
      />
    </div>
  );
};

export default App;
