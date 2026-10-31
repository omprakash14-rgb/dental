import React, { useState } from 'react';
import {
  Printer,
  Download,
  ArrowLeft,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  FileText,
  Calendar,
  Clock,
  Activity,
  Layers,
  Sparkles,
  Info
} from 'lucide-react';
import { ReportDetail } from '../types';
import { GradCamViewOverlay } from '../components/GradCamViewOverlay';
import { downloadReportPdf } from '../services/api';

interface AnalysisResultProps {
  report: ReportDetail;
  onBackToDashboard: () => void;
  onNewScan: () => void;
  onOpenDisclaimer: () => void;
}

export const AnalysisResult: React.FC<AnalysisResultProps> = ({
  report,
  onBackToDashboard,
  onNewScan,
  onOpenDisclaimer
}) => {
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  const hasAbstainedViews = report.screening_summary.has_abstained_views ||
    (report.screening_summary.abstained_views && report.screening_summary.abstained_views.length > 0);

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadPdf = async () => {
    try {
      setDownloadingPdf(true);
      await downloadReportPdf(report.report_id);
    } catch (e: any) {
      alert(`Could not download PDF: ${e.message || e}`);
    } finally {
      setDownloadingPdf(false);
    }
  };

  const detectedConditions = report.conditions_detected || [];

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16 print:p-0 print:space-y-4">
      {/* Top Navigation & Print Actions */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 print:hidden">
        <button
          onClick={onBackToDashboard}
          className="inline-flex items-center space-x-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleDownloadPdf}
            disabled={downloadingPdf}
            className="px-4 py-2 bg-white border border-sky-200 hover:bg-sky-50 text-sky-800 rounded-xl text-xs font-semibold shadow-xs flex items-center gap-2 transition-colors disabled:opacity-60"
          >
            {downloadingPdf ? (
              <div className="w-4 h-4 border-2 border-sky-600 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Download className="w-4 h-4 text-sky-600" />
            )}
            <span>{downloadingPdf ? "Generating PDF..." : "Download PDF Report"}</span>
          </button>
          <button
            onClick={handlePrint}
            className="px-4 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 rounded-xl text-xs font-semibold shadow-xs flex items-center gap-2 transition-colors"
          >
            <Printer className="w-4 h-4 text-slate-500" />
            <span>Print Report</span>
          </button>
          <button
            onClick={onNewScan}
            className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-semibold shadow-sm flex items-center gap-1.5 transition-colors"
          >
            <Activity className="w-4 h-4" />
            <span>New Analysis</span>
          </button>
        </div>
      </div>

      {/* Prominent Mandatory Safety Notice */}
      <div className="p-4 bg-amber-500/10 border-2 border-amber-300 rounded-3xl text-amber-950 flex items-start space-x-3 shadow-xs">
        <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
        <div className="text-xs leading-relaxed">
          <span className="font-bold block text-sm text-amber-900 mb-0.5">Preliminary Pre-Screening Notice</span>
          {report.primary_safety_notice || "AI-generated results are preliminary and may be inaccurate. This system does not provide a confirmed diagnosis. Consult a qualified dental professional for clinical evaluation."}
        </div>
      </div>

      {/* Report Header Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-100 pb-6">
          <div>
            <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono mb-1">
              <span>REPORT REFERENCE:</span>
              <span className="font-bold text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-100">
                {report.report_id}
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Oral Photographic Screening Report
            </h1>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-1.5">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5 text-slate-400" />
                {report.scan_date}
              </span>
              {report.total_inference_time_ms ? (
                <>
                  <span>•</span>
                  <span className="flex items-center gap-1 font-mono text-sky-700">
                    <Clock className="w-3.5 h-3.5 text-sky-500" />
                    Total AI Latency: {report.total_inference_time_ms}ms
                  </span>
                </>
              ) : null}
            </div>
          </div>

          {/* Overall Triage Recommendation Badge */}
          <div className="flex flex-col items-start md:items-end">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Screening Triage Status
            </span>
            <span className={`inline-flex items-center px-4 py-1.5 rounded-full text-sm font-bold shadow-xs ${
              hasAbstainedViews
                ? 'bg-amber-50 text-amber-800 border border-amber-200'
                : 'bg-sky-50 text-sky-800 border border-sky-200'
            }`}>
              <ShieldCheck className="w-4 h-4 mr-1.5 text-sky-600" />
              {report.screening_summary.triage_recommendation || report.screening_summary.urgency_level || 'Clinical Review Advised'}
            </span>
          </div>
        </div>

        {/* Patient Profile Sub-Card */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-50 rounded-2xl p-4 border border-slate-100 text-xs">
          <div>
            <span className="text-slate-400 block font-medium">Patient Name</span>
            <span className="text-slate-900 font-bold text-sm">{report.patient.name}</span>
          </div>
          <div>
            <span className="text-slate-400 block font-medium">Patient ID</span>
            <span className="text-slate-900 font-mono font-bold text-sm">{report.patient.patient_id}</span>
          </div>
          <div>
            <span className="text-slate-400 block font-medium">Age & Gender</span>
            <span className="text-slate-800 font-semibold">
              {report.patient.age ? `${report.patient.age} yrs` : 'N/A'} • {report.patient.gender}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block font-medium">Angles Evaluated</span>
            <span className="text-slate-800 font-semibold">{report.images_analyzed.length} Standard Intraoral Views</span>
          </div>
        </div>

        {report.patient.notes && (
          <div className="text-xs text-slate-600 bg-sky-50/50 p-3.5 rounded-xl border border-sky-100">
            <span className="font-semibold text-sky-900">Patient Symptoms / Notes: </span>
            {report.patient.notes}
          </div>
        )}
      </div>

      {/* Section 1: Executive Summary & Multi-View Notice */}
      <div className="bg-white rounded-3xl p-6 sm:p-7 border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-start space-x-3.5">
          <div className="p-2.5 rounded-2xl bg-sky-100 text-sky-700">
            <Activity className="w-6 h-6 stroke-[2.2]" />
          </div>
          <div className="space-y-1.5 flex-1">
            <h3 className="text-base font-bold text-slate-900">
              {report.screening_summary.overall_status}
            </h3>
            <p className="text-sm text-slate-700 leading-relaxed">
              {report.screening_summary.narrative}
            </p>
          </div>
        </div>

        {/* Multi-View Compilation Disclaimer */}
        <div className="p-3.5 bg-slate-50 rounded-2xl border border-slate-200/70 text-xs text-slate-600 flex items-start space-x-2.5">
          <Info className="w-4 h-4 text-sky-600 mt-0.5 flex-shrink-0" />
          <p className="leading-relaxed">
            {report.screening_summary.multi_view_notice || (
              "This report compiles independent single-image ResNet-50 predictions across the three photographic views. " +
              "The model has not been validated as an integrated multi-view diagnostic system; each angle's output must be evaluated separately by a dental clinician."
            )}
          </p>
        </div>
      </div>

      {/* Section 2: Conditions Detected Across Views */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Primary Model Activations Across Views</h3>
            <p className="text-xs text-slate-500">Summary of conditions flagged by the ResNet-50 network based on top-1 outputs</p>
          </div>
          <span className="text-xs font-semibold px-3 py-1 rounded-full bg-slate-100 text-slate-700">
            {detectedConditions.length} Condition(s) Flagged
          </span>
        </div>

        {detectedConditions.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {detectedConditions.map((item, idx) => {
              const peakScore = item.peak_score ?? (item.peak_confidence || 0);
              const peakPercent = Math.round(peakScore * 100);

              return (
                <div
                  key={idx}
                  className="rounded-2xl p-5 border border-slate-200 bg-slate-50/50 space-y-3"
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="text-base font-bold text-slate-900">{item.disease_name}</h4>
                      <span className="text-xs text-slate-400 font-medium">{item.category}</span>
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-100 text-sky-800 border border-sky-200">
                      Peak Score: {peakPercent}%
                    </span>
                  </div>

                  {/* Score Meter */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs text-slate-600">
                      <span>Model Output Score (Softmax)</span>
                      <span className="font-bold text-slate-900 font-mono">{peakScore.toFixed(4)}</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                      <div
                        className="bg-sky-600 h-1.5 rounded-full"
                        style={{ width: `${Math.min(peakPercent, 100)}%` }}
                      />
                    </div>
                  </div>

                  {/* Views Flagged */}
                  <div className="text-xs text-slate-600 flex items-center space-x-1.5 flex-wrap gap-y-1">
                    <span className="font-semibold text-slate-500">Observed In Views:</span>
                    {item.affected_views.map((v) => (
                      <span
                        key={v}
                        className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-800 font-medium uppercase text-[10px]"
                      >
                        {v} ({item.scores_by_view && item.scores_by_view[v] ? `${Math.round(item.scores_by_view[v] * 100)}%` : ''})
                      </span>
                    ))}
                  </div>

                  {/* Clinical Relevance */}
                  {item.clinical_relevance && (
                    <p className="text-[11px] text-slate-500 pt-1 border-t border-slate-200/60 leading-relaxed">
                      <strong>Clinical Context: </strong>{item.clinical_relevance}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-8 text-center bg-slate-50 rounded-2xl border border-slate-100 text-slate-500">
            <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-500 mb-2" />
            <p className="text-sm font-semibold text-slate-800">No Overt Pathologies Flagged</p>
            <p className="text-xs text-slate-400 mt-0.5">Teeth surfaces appear within normal physiological ranges in the provided field of view.</p>
          </div>
        )}
      </div>

      {/* Section 3: Visual Detection Annotations & Side-by-Side Grad-CAM */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-6">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div>
            <h3 className="text-lg font-bold text-slate-900">Per-View Findings & Side-by-Side Grad-CAM Visualizations</h3>
            <p className="text-xs text-slate-500">
              Side-by-side comparison of original intraoral photographs and Grad-CAM feature salience overlays (layer conv5_block3_out)
            </p>
          </div>
          <span className="text-xs text-sky-700 font-semibold bg-sky-50 px-3 py-1 rounded-full border border-sky-200 flex items-center gap-1">
            <Sparkles className="w-3.5 h-3.5 text-sky-500" />
            Real Neural Saliency
          </span>
        </div>

        {/* 3 Images Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {report.images_analyzed.map((viewData) => (
            <GradCamViewOverlay key={viewData.view} viewData={viewData} />
          ))}
        </div>
      </div>

      {/* Section 4: Recommended Clinical Protocols for Dentist Examination */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/80 shadow-xs space-y-4">
        <div className="flex items-center space-x-2.5 pb-2 border-b border-slate-100">
          <div className="p-2 bg-sky-50 rounded-xl text-sky-600">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Recommended Clinical Examination Procedures</h3>
            <p className="text-xs text-slate-500">Essential procedural steps for chairside validation (no medication/treatment prescriptions)</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
          {(report.recommended_examination_steps || report.clinical_recommendations || []).map((step, rIdx) => (
            <div key={rIdx} className="p-3.5 rounded-2xl bg-slate-50 border border-slate-100 flex items-start space-x-3 text-xs text-slate-700">
              <span className="h-5 w-5 rounded-full bg-sky-100 text-sky-700 font-bold flex items-center justify-center text-[10px] flex-shrink-0 mt-0.5">
                {rIdx + 1}
              </span>
              <span className="leading-relaxed font-medium">{step}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Section 5: Statutory Clinical Disclaimer */}
      <div className="bg-amber-50/70 rounded-3xl p-6 border border-amber-200/80 text-amber-950 space-y-2">
        <div className="flex items-center space-x-2 font-bold text-sm text-amber-900">
          <AlertTriangle className="w-4 h-4 text-amber-600 flex-shrink-0" />
          <span>Statutory Clinical Pre-Screening Disclaimer</span>
        </div>
        <p className="text-xs leading-relaxed text-amber-900/90 font-medium">
          {report.disclaimer}
        </p>
        <button
          onClick={onOpenDisclaimer}
          className="text-xs font-bold text-amber-800 hover:text-amber-900 underline underline-offset-2 pt-1 inline-block"
        >
          View Full Clinical Governance Directives →
        </button>
      </div>
    </div>
  );
};
