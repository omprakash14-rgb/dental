import React, { useState, useEffect } from 'react';
import {
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  User,
  Hash,
  Calendar,
  FileText,
  Activity,
  ArrowRight,
  RefreshCw,
  Info,
  Users
} from 'lucide-react';
import { ImageUploadZone } from '../components/ImageUploadZone';
import { analyzeDentalImages, getPatients } from '../services/api';
import { ReportDetail, PatientInfo } from '../types';

interface NewAnalysisProps {
  onAnalysisSuccess: (report: ReportDetail) => void;
  onOpenDisclaimer: () => void;
  preselectedPatient?: PatientInfo | null;
}

export const NewAnalysis: React.FC<NewAnalysisProps> = ({
  onAnalysisSuccess,
  onOpenDisclaimer,
  preselectedPatient
}) => {
  // Registered patients cache
  const [existingPatients, setExistingPatients] = useState<PatientInfo[]>([]);
  const [selectedPatientPid, setSelectedPatientPid] = useState<string>('new');

  // Patient form states
  const [patientName, setPatientName] = useState('');
  const [patientId, setPatientId] = useState('');
  const [age, setAge] = useState<string>('');
  const [gender, setGender] = useState('Not Specified');
  const [notes, setNotes] = useState('');

  // Three images states
  const [frontImage, setFrontImage] = useState<File | null>(null);
  const [leftImage, setLeftImage] = useState<File | null>(null);
  const [rightImage, setRightImage] = useState<File | null>(null);

  // Status & Progress states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    getPatients().then((pats) => {
      setExistingPatients(pats);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (preselectedPatient) {
      applyPatient(preselectedPatient);
      setSelectedPatientPid(preselectedPatient.patient_id);
    }
  }, [preselectedPatient]);

  const applyPatient = (p: PatientInfo) => {
    setPatientName(p.name || '');
    setPatientId(p.patient_id || '');
    setAge(p.age ? String(p.age) : '');
    setGender(p.gender || 'Not Specified');
    setNotes(p.notes || '');
  };

  const handlePatientSelectChange = (pid: string) => {
    setSelectedPatientPid(pid);
    if (pid === 'new') {
      setPatientName('');
      setPatientId(`PT-${Math.floor(1000 + Math.random() * 9000)}`);
      setAge('');
      setGender('Not Specified');
      setNotes('');
    } else {
      const match = existingPatients.find((p) => p.patient_id === pid);
      if (match) {
        applyPatient(match);
      }
    }
  };

  // Check whether all required inputs are present
  const isFormValid =
    patientName.trim().length > 0 &&
    patientId.trim().length > 0 &&
    frontImage !== null &&
    leftImage !== null &&
    rightImage !== null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!patientName.trim()) {
      setFormError("Patient name is required.");
      return;
    }
    if (!patientId.trim()) {
      setFormError("Patient ID is required.");
      return;
    }
    if (!frontImage || !leftImage || !rightImage) {
      setFormError("All three views (Front, Left, and Right) are mandatory for accurate multi-angle assessment.");
      return;
    }

    try {
      setIsSubmitting(true);
      setUploadProgress(10);

      const formData = new FormData();
      formData.append('patient_name', patientName.trim());
      formData.append('patient_id', patientId.trim());
      if (age) formData.append('age', age);
      formData.append('gender', gender);
      if (notes.trim()) formData.append('notes', notes.trim());

      formData.append('front_image', frontImage);
      formData.append('left_image', leftImage);
      formData.append('right_image', rightImage);

      const report = await analyzeDentalImages(formData, (percent) => {
        setUploadProgress(percent);
      });

      onAnalysisSuccess(report);
    } catch (err: any) {
      setFormError(err.message || "An unexpected error occurred during analysis.");
    } finally {
      setIsSubmitting(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      {/* Page Title & Intro */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            New Dental Photographic Analysis
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Select a registered patient or enter new details, then upload the 3 standardized intraoral arch views.
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Section 1: Patient Selection & Details */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pb-3 border-b border-slate-100">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 bg-sky-50 rounded-xl text-sky-600">
                <User className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">Patient Demographics & Anamnesis</h2>
                <p className="text-xs text-slate-500">PostgreSQL patient records link screening sessions to patients</p>
              </div>
            </div>

            {/* Existing Patient Dropdown */}
            {existingPatients.length > 0 && (
              <div className="flex items-center space-x-2 text-xs">
                <Users className="w-4 h-4 text-slate-400" />
                <span className="font-semibold text-slate-600">Patient Source:</span>
                <select
                  value={selectedPatientPid}
                  onChange={(e) => handlePatientSelectChange(e.target.value)}
                  className="px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-800 font-medium focus:border-sky-500 outline-none"
                >
                  <option value="new">+ Enter New Patient</option>
                  {existingPatients.map((p) => (
                    <option key={p.patient_id} value={p.patient_id}>
                      {p.name} ({p.patient_id})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Patient Name */}
            <div className="space-y-1.5 sm:col-span-2">
              <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                Full Patient Name <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  placeholder="e.g. Sarah Jenkins"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-sky-500 focus:ring-2 focus:ring-sky-100 text-sm text-slate-800 placeholder:text-slate-400 outline-none transition-all"
                />
              </div>
            </div>

            {/* Patient ID */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700 flex items-center gap-1">
                Medical Record ID <span className="text-rose-500">*</span>
              </label>
              <div className="relative">
                <input
                  type="text"
                  required
                  placeholder="e.g. PT-2026-091"
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-sky-500 focus:ring-2 focus:ring-sky-100 text-sm font-mono text-slate-800 placeholder:text-slate-400 outline-none transition-all"
                />
              </div>
            </div>

            {/* Age */}
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-700">
                Age (Years)
              </label>
              <input
                type="number"
                min="1"
                max="125"
                placeholder="e.g. 34"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-sky-500 focus:ring-2 focus:ring-sky-100 text-sm text-slate-800 placeholder:text-slate-400 outline-none transition-all"
              />
            </div>
          </div>

          {/* Clinical Notes */}
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-slate-700">
              Clinical Observations / Symptom Notes (Optional)
            </label>
            <textarea
              rows={2}
              placeholder="e.g. Patient reports cold sensitivity on premolars, bleeding on brushing, last dental visit 14 months ago..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 focus:border-sky-500 focus:ring-2 focus:ring-sky-100 text-sm text-slate-800 placeholder:text-slate-400 outline-none transition-all"
            />
          </div>
        </div>

        {/* Section 2: Three Intraoral Photographs */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 pb-3 border-b border-slate-100">
            <div>
              <h2 className="text-base font-bold text-slate-900">Three-Angle Intraoral Photographs</h2>
              <p className="text-xs text-slate-500">
                Front, Left, and Right views required for multi-angle AI pre-screening (JPG, JPEG, PNG, WebP)
              </p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 bg-amber-50 text-amber-800 border border-amber-200 rounded-full">
              All 3 Angles Required
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <ImageUploadZone
              view="front"
              label="Front Anterior View"
              description="Direct frontal shot displaying incisors, canines, and anterior occlusion"
              file={frontImage}
              onFileSelect={(f) => setFrontImage(f)}
              onFileRemove={() => setFrontImage(null)}
            />

            <ImageUploadZone
              view="left"
              label="Left Lateral / Buccal View"
              description="Lateral shot capturing left premolars, molars, and gingival margin"
              file={leftImage}
              onFileSelect={(f) => setLeftImage(f)}
              onFileRemove={() => setLeftImage(null)}
            />

            <ImageUploadZone
              view="right"
              label="Right Lateral / Buccal View"
              description="Lateral shot capturing right premolars, molars, and gingival margin"
              file={rightImage}
              onFileSelect={(f) => setRightImage(f)}
              onFileRemove={() => setRightImage(null)}
            />
          </div>
        </div>

        {/* Form Error Banner */}
        {formError && (
          <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-start space-x-3 text-rose-800 text-xs">
            <AlertCircle className="w-5 h-5 text-rose-600 mt-0.5 flex-shrink-0" />
            <div>
              <span className="font-bold block text-sm">Submission Incomplete</span>
              <p className="mt-0.5">{formError}</p>
            </div>
          </div>
        )}

        {/* Progress Bar (Visible during upload/inference) */}
        {isSubmitting && (
          <div className="bg-white rounded-2xl p-5 border border-sky-100 shadow-xs space-y-3">
            <div className="flex justify-between items-center text-xs font-semibold text-slate-700">
              <span className="flex items-center gap-2">
                <div className="w-4 h-4 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
                <span>Running ResNet-50 Inference Pipeline & Grad-CAM Mapping...</span>
              </span>
              <span className="font-mono text-sky-700">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
              <div
                className="bg-sky-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Submission Controls */}
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4 pt-2">
          <div className="flex items-center space-x-2 text-xs text-slate-500">
            <Info className="w-4 h-4 text-sky-600 flex-shrink-0" />
            <span>AI outputs do not formulate a final diagnosis. A licensed dentist must confirm findings.</span>
          </div>

          <button
            type="submit"
            disabled={!isFormValid || isSubmitting}
            className={`w-full sm:w-auto px-8 py-3.5 rounded-2xl font-bold text-sm shadow-md flex items-center justify-center space-x-2 transition-all ${
              isFormValid && !isSubmitting
                ? 'bg-sky-600 hover:bg-sky-700 text-white cursor-pointer shadow-sky-600/20'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
            }`}
          >
            <span>Execute 3-View Pre-Screening</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};


