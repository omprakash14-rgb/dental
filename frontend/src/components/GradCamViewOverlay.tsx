import React, { useState } from 'react';
import { Layers, Clock, Eye, AlertCircle, Info, Sparkles, Sliders } from 'lucide-react';
import { ImageAnalysisView } from '../types';
import { getUploadUrl } from '../services/api';

interface GradCamViewOverlayProps {
  viewData: ImageAnalysisView;
}

export const GradCamViewOverlay: React.FC<GradCamViewOverlayProps> = ({ viewData }) => {
  const [viewMode, setViewMode] = useState<'side-by-side' | 'blend'>('side-by-side');
  const [blendOpacity, setBlendOpacity] = useState<number>(50); // 0 = only original, 100 = only heatmap

  const origUrl = getUploadUrl(viewData.original_image);
  const heatmapUrl = getUploadUrl(viewData.heatmap_image);

  const topThree = viewData.top_three_predictions || [];
  const primaryScore = viewData.model_output_score ?? (viewData.confidence || 0);
  const primaryPercent = viewData.confidence_percentage ?? Math.round(primaryScore * 100);

  return (
    <div className="bg-white rounded-3xl border border-slate-200/80 overflow-hidden shadow-xs flex flex-col">
      {/* Header */}
      <div className="px-5 py-3.5 bg-slate-50/80 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2.5">
          <span className="font-bold text-slate-900 text-sm">{viewData.label}</span>
          {viewData.is_abstaining ? (
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-200 flex items-center gap-1">
              <AlertCircle className="w-3.5 h-3.5 text-amber-700" />
              Low Confidence ({primaryPercent}%)
            </span>
          ) : (
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-sky-100 text-sky-800 border border-sky-200">
              {viewData.predicted_class} ({primaryPercent}%)
            </span>
          )}
        </div>

        {/* Inference Latency & View Mode Controls */}
        <div className="flex items-center space-x-2">
          {viewData.inference_time_ms > 0 && (
            <span className="text-[11px] font-mono text-slate-500 bg-white px-2 py-1 rounded-lg border border-slate-200 flex items-center gap-1">
              <Clock className="w-3 h-3 text-slate-400" />
              {viewData.inference_time_ms}ms
            </span>
          )}

          <div className="flex items-center space-x-1 bg-white p-0.5 rounded-lg border border-slate-200 text-xs">
            <button
              onClick={() => setViewMode('side-by-side')}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors ${
                viewMode === 'side-by-side'
                  ? 'bg-sky-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Side-by-Side
            </button>
            <button
              onClick={() => setViewMode('blend')}
              className={`px-2.5 py-1 rounded-md font-medium transition-colors flex items-center gap-1 ${
                viewMode === 'blend'
                  ? 'bg-sky-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Sliders className="w-3 h-3" /> Blend
            </button>
          </div>
        </div>
      </div>

      {/* Visual Presentation Area */}
      <div className="p-4 bg-slate-950 flex flex-col justify-center">
        {viewMode === 'side-by-side' ? (
          /* Side-by-Side: Original Photo vs Grad-CAM Overlay */
          <div className="grid grid-cols-2 gap-3 aspect-[8/3]">
            {/* Left: Original Photo */}
            <div className="relative rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 flex flex-col">
              <img
                src={origUrl || heatmapUrl}
                alt={`${viewData.label} Original`}
                className="w-full h-full object-cover"
              />
              <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-black/70 backdrop-blur-xs text-white text-[10px] font-semibold tracking-wide">
                Original Photo
              </div>
            </div>

            {/* Right: Grad-CAM Saliency Overlay */}
            <div className="relative rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 flex flex-col">
              <img
                src={heatmapUrl || origUrl}
                alt={`${viewData.label} Grad-CAM Heatmap`}
                className="w-full h-full object-cover"
              />
              <div className="absolute top-2 left-2 px-2 py-0.5 rounded-md bg-sky-950/80 border border-sky-400/40 backdrop-blur-xs text-sky-200 text-[10px] font-semibold tracking-wide flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-sky-400" />
                Grad-CAM Activation
              </div>
            </div>
          </div>
        ) : (
          /* Interactive Blend Slider Mode */
          <div className="space-y-3">
            <div className="relative aspect-[4/3] rounded-2xl overflow-hidden bg-slate-900 border border-slate-800">
              {/* Base Original */}
              <img
                src={origUrl || heatmapUrl}
                alt="Base"
                className="absolute inset-0 w-full h-full object-cover"
              />
              {/* Heatmap Layer with variable opacity */}
              <img
                src={heatmapUrl || origUrl}
                alt="Heatmap Overlay"
                className="absolute inset-0 w-full h-full object-cover transition-opacity duration-150"
                style={{ opacity: blendOpacity / 100 }}
              />

              <div className="absolute top-2 left-2 px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-xs text-white text-[11px] font-medium">
                Blend: {100 - blendOpacity}% Photo / {blendOpacity}% Heatmap
              </div>
            </div>

            {/* Slider Control */}
            <div className="flex items-center space-x-3 px-2 py-1">
              <span className="text-[11px] text-slate-400 font-medium">Original</span>
              <input
                type="range"
                min="0"
                max="100"
                value={blendOpacity}
                onChange={(e) => setBlendOpacity(Number(e.target.value))}
                className="flex-1 h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500"
              />
              <span className="text-[11px] text-sky-400 font-medium">Heatmap</span>
            </div>
          </div>
        )}
      </div>

      {/* Salience Scientific Disclosure Note */}
      <div className="px-4 py-2.5 bg-slate-50 border-t border-b border-slate-100 text-[11px] text-slate-500 flex items-start space-x-2">
        <Info className="w-3.5 h-3.5 text-sky-600 mt-0.5 flex-shrink-0" />
        <p className="leading-relaxed">
          <strong>Grad-CAM Feature Salience:</strong> Highlights pixel regions that influenced the model's classification score.
          This does <span className="font-semibold text-slate-700">not</span> represent an automated bounding box or confirmed lesion boundary.
        </p>
      </div>

      {/* Top-3 Predictions Breakdown */}
      <div className="p-4 space-y-3 bg-white">
        <div className="flex justify-between items-center text-xs">
          <span className="font-bold text-slate-800">Top-3 Model Output Scores:</span>
          <span className="text-[10px] text-slate-400 font-mono">(Uncalibrated Softmax)</span>
        </div>

        <div className="space-y-2">
          {topThree.map((item) => {
            const isRank1 = item.rank === 1;
            return (
              <div key={item.class_name} className="space-y-1">
                <div className="flex justify-between items-center text-xs">
                  <div className="flex items-center space-x-2">
                    <span className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                      isRank1 ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {item.rank}
                    </span>
                    <span className={`font-semibold ${isRank1 ? 'text-slate-900' : 'text-slate-600'}`}>
                      {item.display_name}
                    </span>
                  </div>
                  <span className="font-mono text-xs font-bold text-slate-700">
                    {item.percentage}% ({item.score.toFixed(4)})
                  </span>
                </div>

                <div className="w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
                  <div
                    className={`h-1.5 rounded-full ${
                      isRank1 ? 'bg-sky-600' : 'bg-slate-300'
                    }`}
                    style={{ width: `${Math.min(item.percentage, 100)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

