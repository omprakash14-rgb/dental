import React, { useState, useEffect } from 'react';
import {
  Users,
  Search,
  Calendar,
  FileText,
  Activity,
  AlertTriangle,
  ArrowRight,
  Clock,
  User,
  ShieldCheck,
  ChevronRight,
  Plus,
  Edit2,
  Trash2,
  Download,
  Phone,
  Mail,
  Heart,
  FileCheck2,
  X
} from 'lucide-react';
import { PatientInfo } from '../types';
import { getPatients, getPatientHistory, createPatient, updatePatient, deletePatient, downloadReportPdf } from '../services/api';

interface PatientHistoryProps {
  onViewReport: (reportId: string) => void;
  onNewScanForPatient?: (patient: PatientInfo) => void;
}

export const PatientHistory: React.FC<PatientHistoryProps> = ({
  onViewReport,
  onNewScanForPatient
}) => {
  const [patients, setPatients] = useState<PatientInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);
  const [patientDetail, setPatientDetail] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [downloadingReportId, setDownloadingReportId] = useState<string | null>(null);

  // Modals state
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  // Patient form state
  const [formName, setFormName] = useState('');
  const [formId, setFormId] = useState('');
  const [formAge, setFormAge] = useState('');
  const [formDob, setFormDob] = useState('');
  const [formGender, setFormGender] = useState('Not Specified');
  const [formContact, setFormContact] = useState('');
  const [formEmail, setFormEmail] = useState('');
  const [formMedHistory, setFormMedHistory] = useState('');
  const [formDentHistory, setFormDentHistory] = useState('');
  const [formNotes, setFormNotes] = useState('');

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async (selectPid?: string) => {
    try {
      setLoading(true);
      const data = await getPatients(searchQuery.trim() || undefined);
      setPatients(data);
      const targetPid = selectPid || (data.length > 0 ? (selectedPatientId || data[0].patient_id) : null);
      if (targetPid) {
        handleSelectPatient(targetPid);
      } else {
        setPatientDetail(null);
        setSelectedPatientId(null);
      }
    } catch (e) {
      console.error("Failed to fetch patients", e);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    await loadPatients();
  };

  const handleSelectPatient = async (pid: string) => {
    try {
      setSelectedPatientId(pid);
      setDetailLoading(true);
      const detail = await getPatientHistory(pid);
      setPatientDetail(detail);
    } catch (e) {
      console.error("Failed to load patient history", e);
    } finally {
      setDetailLoading(false);
    }
  };

  const openRegisterModal = () => {
    setFormName('');
    setFormId(`PT-${Math.floor(1000 + Math.random() * 9000)}`);
    setFormAge('');
    setFormDob('');
    setFormGender('Not Specified');
    setFormContact('');
    setFormEmail('');
    setFormMedHistory('');
    setFormDentHistory('');
    setFormNotes('');
    setModalError(null);
    setIsRegisterOpen(true);
  };

  const openEditModal = () => {
    if (!patientDetail) return;
    const p = patientDetail.patient;
    setFormName(p.name || '');
    setFormId(p.patient_id || '');
    setFormAge(p.age ? String(p.age) : '');
    setFormDob(p.date_of_birth || '');
    setFormGender(p.gender || 'Not Specified');
    setFormContact(p.contact_number || '');
    setFormEmail(p.email || '');
    setFormMedHistory(p.medical_history || '');
    setFormDentHistory(p.dental_history || '');
    setFormNotes(p.notes || '');
    setModalError(null);
    setIsEditOpen(true);
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalError(null);
    if (!formName.trim() || !formId.trim()) {
      setModalError("Patient Name and Medical ID are mandatory.");
      return;
    }
    try {
      setModalLoading(true);
      const newPat = await createPatient({
        name: formName.trim(),
        patient_id: formId.trim(),
        age: formAge ? parseInt(formAge) : undefined,
        date_of_birth: formDob.trim() || undefined,
        gender: formGender,
        contact_number: formContact.trim() || undefined,
        email: formEmail.trim() || undefined,
        medical_history: formMedHistory.trim() || undefined,
        dental_history: formDentHistory.trim() || undefined,
        notes: formNotes.trim() || undefined
      });
      setIsRegisterOpen(false);
      await loadPatients(newPat.patient_id);
    } catch (err: any) {
      setModalError(err.message || "Failed to register patient");
    } finally {
      setModalLoading(false);
    }
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientDetail) return;
    setModalError(null);
    try {
      setModalLoading(true);
      await updatePatient(patientDetail.patient.patient_id, {
        name: formName.trim(),
        age: formAge ? parseInt(formAge) : undefined,
        date_of_birth: formDob.trim() || undefined,
        gender: formGender,
        contact_number: formContact.trim() || undefined,
        email: formEmail.trim() || undefined,
        medical_history: formMedHistory.trim() || undefined,
        dental_history: formDentHistory.trim() || undefined,
        notes: formNotes.trim() || undefined
      });
      setIsEditOpen(false);
      await handleSelectPatient(patientDetail.patient.patient_id);
      const updatedList = await getPatients();
      setPatients(updatedList);
    } catch (err: any) {
      setModalError(err.message || "Failed to update patient");
    } finally {
      setModalLoading(false);
    }
  };

  const handleDeletePatient = async () => {
    if (!patientDetail) return;
    try {
      setModalLoading(true);
      await deletePatient(patientDetail.patient.patient_id);
      setIsDeleteConfirmOpen(false);
      await loadPatients();
    } catch (err: any) {
      alert(`Could not delete patient: ${err.message || err}`);
    } finally {
      setModalLoading(false);
    }
  };

  const handleDownloadPdf = async (reportId: string) => {
    try {
      setDownloadingReportId(reportId);
      await downloadReportPdf(reportId);
    } catch (e: any) {
      alert(`Failed to download report PDF: ${e.message || e}`);
    } finally {
      setDownloadingReportId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Patient Management & Clinical Screening Records
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Register new patients, maintain anamnesis profiles, and retrieve historical multi-angle scan reports.
          </p>
        </div>

        <button
          onClick={openRegisterModal}
          className="px-4 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow-xs flex items-center gap-2 transition-colors whitespace-nowrap"
        >
          <Plus className="w-4 h-4" />
          <span>Register New Patient</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Patient Directory & Search */}
        <div className="lg:col-span-5 bg-white rounded-3xl border border-slate-200/80 shadow-xs overflow-hidden flex flex-col h-[750px]">
          {/* Search Bar */}
          <form onSubmit={handleSearch} className="p-4 border-b border-slate-100 bg-slate-50/50">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input
                type="text"
                placeholder="Search by name, Medical ID, or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3.5 py-2 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
              />
            </div>
          </form>

          {/* Patient Scroll List */}
          <div className="flex-1 overflow-y-auto divide-y divide-slate-100 p-2 space-y-1">
            {loading ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading directory...</div>
            ) : patients.length > 0 ? (
              patients.map((p) => {
                const isSelected = selectedPatientId === p.patient_id;
                return (
                  <button
                    key={p.patient_id}
                    onClick={() => handleSelectPatient(p.patient_id)}
                    className={`w-full text-left p-3.5 rounded-2xl transition-all flex items-center justify-between ${
                      isSelected
                        ? 'bg-sky-50 border border-sky-200 shadow-xs'
                        : 'hover:bg-slate-50 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-xs ${
                        isSelected ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {p.name.slice(0, 2).toUpperCase()}
                      </div>
                      <div>
                        <div className="font-semibold text-slate-900 text-sm">{p.name}</div>
                        <div className="text-xs text-slate-400 font-mono">{p.patient_id}</div>
                      </div>
                    </div>

                    <div className="text-right">
                      <span className="text-[11px] font-semibold text-sky-700 bg-sky-100/60 px-2.5 py-0.5 rounded-full">
                        {p.analyses_count ?? 0} Scan(s)
                      </span>
                    </div>
                  </button>
                );
              })
            ) : (
              <div className="p-8 text-center text-xs text-slate-400">
                No patients found matching '{searchQuery}'
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Selected Patient Details & History */}
        <div className="lg:col-span-7 space-y-6">
          {detailLoading ? (
            <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 text-slate-400">
              <div className="w-8 h-8 border-3 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto mb-2" />
              <span>Loading patient profile & historical records...</span>
            </div>
          ) : patientDetail ? (
            <>
              {/* Comprehensive Patient Profile Card */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-5">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <div className="flex items-center space-x-3.5">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-sky-600 to-cyan-500 flex items-center justify-center text-white font-bold text-base shadow-sm">
                      {patientDetail.patient.name.slice(0, 2).toUpperCase()}
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-slate-900">{patientDetail.patient.name}</h2>
                      <p className="text-xs text-slate-400 font-mono">
                        Medical ID: {patientDetail.patient.patient_id}
                      </p>
                    </div>
                  </div>

                  {/* Patient Action Buttons */}
                  <div className="flex items-center space-x-2">
                    {onNewScanForPatient && (
                      <button
                        onClick={() => onNewScanForPatient(patientDetail.patient)}
                        className="px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow-xs flex items-center gap-1.5 transition-colors"
                      >
                        <Activity className="w-3.5 h-3.5" />
                        <span>Start Scan</span>
                      </button>
                    )}
                    <button
                      onClick={openEditModal}
                      className="p-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl text-xs transition-colors"
                      title="Edit Patient Information"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setIsDeleteConfirmOpen(true)}
                      className="p-2 bg-rose-50 hover:bg-rose-100 text-rose-600 rounded-xl text-xs transition-colors"
                      title="Delete Patient Record"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Patient Demographics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3 text-xs border-t border-slate-100">
                  <div>
                    <span className="text-slate-400 block font-medium">Age / DOB</span>
                    <span className="font-semibold text-slate-800">
                      {patientDetail.patient.age ? `${patientDetail.patient.age} yrs` : 'N/A'}{' '}
                      {patientDetail.patient.date_of_birth ? `(${patientDetail.patient.date_of_birth})` : ''}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Gender</span>
                    <span className="font-semibold text-slate-800">{patientDetail.patient.gender}</span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Contact Phone</span>
                    <span className="font-semibold text-slate-800">
                      {patientDetail.patient.contact_number || 'Not provided'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block font-medium">Email</span>
                    <span className="font-semibold text-slate-800 truncate block">
                      {patientDetail.patient.email || 'Not provided'}
                    </span>
                  </div>
                </div>

                {/* Medical & Dental History */}
                {(patientDetail.patient.medical_history || patientDetail.patient.dental_history) && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                    {patientDetail.patient.medical_history && (
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="font-semibold text-slate-700 block mb-0.5">Medical Anamnesis:</span>
                        <p className="text-slate-600">{patientDetail.patient.medical_history}</p>
                      </div>
                    )}
                    {patientDetail.patient.dental_history && (
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="font-semibold text-slate-700 block mb-0.5">Dental History:</span>
                        <p className="text-slate-600">{patientDetail.patient.dental_history}</p>
                      </div>
                    )}
                  </div>
                )}

                {patientDetail.patient.notes && (
                  <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-600 border border-slate-100">
                    <span className="font-semibold text-slate-700">Clinical Notes: </span>
                    {patientDetail.patient.notes}
                  </div>
                )}
              </div>

              {/* Scans Timeline */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200/80 shadow-xs space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <Activity className="w-4 h-4 text-sky-600" />
                    <span>Chronological Screening Sessions ({patientDetail.scans_count})</span>
                  </h3>
                  <span className="text-xs text-slate-400">Stored in PostgreSQL</span>
                </div>

                {patientDetail.history.length > 0 ? (
                  <div className="space-y-4 relative before:absolute before:inset-0 before:left-5 before:w-0.5 before:bg-slate-200">
                    {patientDetail.history.map((scan: any, sIdx: number) => {
                      const isHigh = scan.urgency_level.includes('High');
                      const isModerate = scan.urgency_level.includes('Moderate');
                      const isPdfLoading = downloadingReportId === scan.report_id;

                      return (
                        <div key={sIdx} className="relative pl-11 group">
                          {/* Timeline node */}
                          <div className={`absolute left-3.5 top-2.5 w-3.5 h-3.5 rounded-full border-2 bg-white ${
                            isHigh ? 'border-red-500' : isModerate ? 'border-amber-500' : 'border-sky-500'
                          }`} />

                          <div className="bg-slate-50/70 hover:bg-slate-50 rounded-2xl p-4 border border-slate-200/70 transition-all space-y-2.5">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <span className="font-mono text-xs font-bold text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-100">
                                {scan.report_id}
                              </span>
                              <span className="text-xs text-slate-400 flex items-center gap-1">
                                <Calendar className="w-3.5 h-3.5" />
                                {new Date(scan.created_at).toLocaleDateString(undefined, {
                                  month: 'short',
                                  day: 'numeric',
                                  year: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                })}
                              </span>
                            </div>

                            <div className="flex items-center justify-between">
                              <div className="text-sm font-bold text-slate-800">
                                {scan.overall_status}
                              </div>
                              <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                                isHigh ? 'bg-red-100 text-red-800' : isModerate ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                              }`}>
                                {scan.urgency_level}
                              </span>
                            </div>

                            {scan.summary && (
                              <p className="text-xs text-slate-600 leading-relaxed">
                                {scan.summary}
                              </p>
                            )}

                            {scan.findings && scan.findings.length > 0 && (
                              <div className="pt-1 flex flex-wrap gap-1.5 border-t border-slate-200/50">
                                {scan.findings.map((f: any, fIdx: number) => (
                                  <span
                                    key={fIdx}
                                    className="px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200 text-[10px] font-medium"
                                  >
                                    {f.disease_name} ({f.confidence_percentage}%)
                                  </span>
                                ))}
                              </div>
                            )}

                            <div className="pt-2 flex justify-end items-center gap-2">
                              <button
                                onClick={() => handleDownloadPdf(scan.report_id)}
                                disabled={isPdfLoading}
                                className="px-3 py-1.5 bg-white hover:bg-sky-50 text-slate-700 hover:text-sky-700 border border-slate-200 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50"
                              >
                                {isPdfLoading ? (
                                  <div className="w-3.5 h-3.5 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
                                ) : (
                                  <Download className="w-3.5 h-3.5 text-sky-600" />
                                )}
                                <span>PDF Report</span>
                              </button>

                              <button
                                onClick={() => onViewReport(scan.report_id)}
                                className="px-3 py-1.5 bg-sky-600 hover:bg-sky-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                              >
                                <FileText className="w-3.5 h-3.5" />
                                <span>Open Full Viewer</span>
                              </button>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-8 text-center text-xs text-slate-400">
                    No scan records found for this patient. Click "Start Scan" to perform their first screening.
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="bg-white rounded-3xl p-12 text-center border border-slate-200 text-slate-400">
              <Users className="w-8 h-8 mx-auto mb-2 text-slate-300" />
              <span>Select a patient on the left or click "Register New Patient" to begin.</span>
            </div>
          )}
        </div>
      </div>

      {/* Register Patient Modal */}
      {isRegisterOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Register New Dental Patient</h3>
              <button onClick={() => setIsRegisterOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="p-3 bg-rose-50 text-rose-700 text-xs rounded-xl border border-rose-200">
                {modalError}
              </div>
            )}

            <form onSubmit={handleRegisterSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Full Name *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. John Doe"
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Patient ID *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. PT-2026-101"
                    value={formId}
                    onChange={(e) => setFormId(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 font-mono outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Age</label>
                  <input
                    type="number"
                    min="0"
                    max="125"
                    value={formAge}
                    onChange={(e) => setFormAge(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Date of Birth</label>
                  <input
                    type="date"
                    value={formDob}
                    onChange={(e) => setFormDob(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Gender</label>
                  <select
                    value={formGender}
                    onChange={(e) => setFormGender(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  >
                    <option value="Not Specified">Not Specified</option>
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Contact Number</label>
                  <input
                    type="tel"
                    placeholder="+1-555-0100"
                    value={formContact}
                    onChange={(e) => setFormContact(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Email Address</label>
                  <input
                    type="email"
                    placeholder="patient@example.com"
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Medical Anamnesis (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="Systemic conditions, allergies, current medications..."
                  value={formMedHistory}
                  onChange={(e) => setFormMedHistory(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Dental History (Optional)</label>
                <textarea
                  rows={2}
                  placeholder="Previous restorations, periodontal issues, orthodontic history..."
                  value={formDentHistory}
                  onChange={(e) => setFormDentHistory(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Additional Notes</label>
                <input
                  type="text"
                  placeholder="Patient preferences, scheduling notes..."
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsRegisterOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl font-semibold disabled:opacity-60"
                >
                  {modalLoading ? "Saving..." : "Save Patient"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Patient Modal */}
      {isEditOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Edit Patient Details</h3>
              <button onClick={() => setIsEditOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="p-3 bg-rose-50 text-rose-700 text-xs rounded-xl border border-rose-200">
                {modalError}
              </div>
            )}

            <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Full Name *</label>
                  <input
                    type="text"
                    required
                    value={formName}
                    onChange={(e) => setFormName(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Patient ID</label>
                  <input
                    type="text"
                    disabled
                    value={formId}
                    className="w-full px-3 py-2 rounded-xl border border-slate-100 bg-slate-100 text-slate-500 font-mono outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Age</label>
                  <input
                    type="number"
                    min="0"
                    max="125"
                    value={formAge}
                    onChange={(e) => setFormAge(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Date of Birth</label>
                  <input
                    type="date"
                    value={formDob}
                    onChange={(e) => setFormDob(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Gender</label>
                  <select
                    value={formGender}
                    onChange={(e) => setFormGender(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  >
                    <option value="Not Specified">Not Specified</option>
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Contact Number</label>
                  <input
                    type="tel"
                    value={formContact}
                    onChange={(e) => setFormContact(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-semibold text-slate-700">Email Address</label>
                  <input
                    type="email"
                    value={formEmail}
                    onChange={(e) => setFormEmail(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Medical Anamnesis</label>
                <textarea
                  rows={2}
                  value={formMedHistory}
                  onChange={(e) => setFormMedHistory(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Dental History</label>
                <textarea
                  rows={2}
                  value={formDentHistory}
                  onChange={(e) => setFormDentHistory(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="font-semibold text-slate-700">Clinical Notes</label>
                <input
                  type="text"
                  value={formNotes}
                  onChange={(e) => setFormNotes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 focus:border-sky-500 outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsEditOpen(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={modalLoading}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl font-semibold disabled:opacity-60"
                >
                  {modalLoading ? "Updating..." : "Update Patient"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Patient Confirmation Modal */}
      {isDeleteConfirmOpen && patientDetail && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-4">
            <div className="flex items-center space-x-3 text-rose-600">
              <div className="w-10 h-10 rounded-2xl bg-rose-50 border border-rose-100 flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="w-5 h-5 text-rose-600" />
              </div>
              <h3 className="text-base font-bold text-slate-900">Delete Patient Record?</h3>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Are you sure you want to permanently delete patient{' '}
              <span className="font-bold text-slate-800">{patientDetail.patient.name}</span> (
              <span className="font-mono text-slate-800">{patientDetail.patient.patient_id}</span>)?
              This action will permanently delete all {patientDetail.scans_count} associated screening sessions,
              uploaded photographs, and generated reports from PostgreSQL.
            </p>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 text-xs">
              <button
                type="button"
                onClick={() => setIsDeleteConfirmOpen(false)}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl font-semibold"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeletePatient}
                disabled={modalLoading}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl font-semibold disabled:opacity-60"
              >
                {modalLoading ? "Deleting..." : "Permanently Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
