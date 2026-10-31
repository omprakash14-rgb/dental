import React from 'react';
import { AlertTriangle, ShieldCheck, X, Stethoscope, CheckCircle2 } from 'lucide-react';

interface DisclaimerModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const DisclaimerModal: React.FC<DisclaimerModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-3xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden transform transition-all animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-500 to-amber-600 px-6 py-5 text-white flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-white/20 rounded-xl backdrop-blur-xs">
              <AlertTriangle className="w-6 h-6 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-bold">Medical Safety & Regulatory Notice</h3>
              <p className="text-xs text-amber-100">DentalAI Pre-Screening Protocols</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white p-1.5 rounded-lg hover:bg-white/10 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4 text-slate-600 text-sm leading-relaxed">
          {/* Exact Required Safety Notice */}
          <div className="p-4 bg-amber-50 border-2 border-amber-300 rounded-2xl text-amber-950 text-xs font-semibold space-y-1.5 shadow-xs">
            <p className="font-bold text-sm text-amber-900 flex items-center gap-1.5">
              <Stethoscope className="w-4 h-4 text-amber-700" />
              Primary Medical Safety Notice
            </p>
            <p className="leading-relaxed">
              "AI-generated results are preliminary and may be inaccurate. This system does not provide a confirmed diagnosis. Consult a qualified dental professional for clinical evaluation."
            </p>
          </div>

          <div className="space-y-3 pt-2">
            <h4 className="font-semibold text-slate-900 text-sm">Clinical Protocol Directives:</h4>
            <ul className="space-y-2.5 text-xs text-slate-700">
              <li className="flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-sky-600 mt-0.5 flex-shrink-0" />
                <span>
                  <strong>Chairside Dentist Validation:</strong> All visual predictions and category scores must be verified chairside by a qualified dental professional via physical tactile inspection.
                </span>
              </li>
              <li className="flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-sky-600 mt-0.5 flex-shrink-0" />
                <span>
                  <strong>No Prescription or Surgical Planning:</strong> This software is strictly an assistive screening aid and does not recommend medications, prescribe pharmaceuticals, or generate surgical treatment plans.
                </span>
              </li>
              <li className="flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-sky-600 mt-0.5 flex-shrink-0" />
                <span>
                  <strong>Grad-CAM Interpretation:</strong> Grad-CAM heatmaps illustrate neural network feature activations that influenced the classification; they do not delineate anatomical lesion boundaries or perform object segmentation.
                </span>
              </li>
              <li className="flex items-start space-x-2">
                <CheckCircle2 className="w-4 h-4 text-sky-600 mt-0.5 flex-shrink-0" />
                <span>
                  <strong>Diagnostic Imaging Requirement:</strong> Intraoral photographs cannot substitute for diagnostic bite-wing or periapical X-rays needed to evaluate interproximal caries depth or alveolar bone loss.
                </span>
              </li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-xl text-sm font-semibold transition-colors shadow-sm"
          >
            I Acknowledge & Understand
          </button>
        </div>
      </div>
    </div>
  );
};
