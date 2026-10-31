import React, { useRef, useState, useEffect } from 'react';
import { UploadCloud, CheckCircle2, AlertCircle, X, RefreshCw, Eye, Camera } from 'lucide-react';

interface ImageUploadZoneProps {
  view: 'front' | 'left' | 'right';
  label: string;
  description: string;
  file: File | null;
  onFileSelect: (file: File) => void;
  onFileRemove: () => void;
  error?: string;
}

export const ImageUploadZone: React.FC<ImageUploadZoneProps> = ({
  view,
  label,
  description,
  file,
  onFileSelect,
  onFileRemove,
  error
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [fileDetails, setFileDetails] = useState<{
    width?: number;
    height?: number;
    sizeKb?: number;
    isSharp?: boolean;
  }>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Generate preview & inspect dimensions
  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      setFileDetails({});
      return;
    }

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    const img = new Image();
    img.onload = () => {
      setFileDetails({
        width: img.naturalWidth,
        height: img.naturalHeight,
        sizeKb: Math.round(file.size / 1024),
        isSharp: img.naturalWidth >= 200 && img.naturalHeight >= 200
      });
    };
    img.src = url;

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [file]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelect(e.dataTransfer.files[0]);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSelect(e.target.files[0]);
    }
  };

  const validateAndSelect = (selectedFile: File) => {
    const validExtensions = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
    if (!validExtensions.includes(selectedFile.type) && !selectedFile.name.match(/\.(jpg|jpeg|png|webp)$/i)) {
      alert("Unsupported file format. Please upload JPG, JPEG, PNG, or WebP.");
      return;
    }
    if (selectedFile.size > 25 * 1024 * 1024) {
      alert("File exceeds maximum size of 25MB.");
      return;
    }
    onFileSelect(selectedFile);
  };

  return (
    <div className={`relative flex flex-col rounded-2xl border-2 transition-all overflow-hidden ${
      error
        ? 'border-red-300 bg-red-50/20'
        : file
        ? 'border-sky-300 bg-white shadow-sm'
        : isDragOver
        ? 'border-sky-500 bg-sky-50/50 scale-[1.01]'
        : 'border-dashed border-slate-200 bg-slate-50/50 hover:bg-slate-50 hover:border-slate-300'
    }`}>
      {/* Header Badge */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 bg-white">
        <div className="flex items-center space-x-2">
          <span className={`h-6 w-6 rounded-lg flex items-center justify-center text-xs font-bold ${
            file ? 'bg-sky-100 text-sky-700' : 'bg-slate-100 text-slate-500'
          }`}>
            {view === 'front' ? '1' : view === 'left' ? '2' : '3'}
          </span>
          <span className="text-sm font-semibold text-slate-800">{label}</span>
        </div>
        {file ? (
          <span className="flex items-center text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Ready
          </span>
        ) : (
          <span className="text-[11px] font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
            Required
          </span>
        )}
      </div>

      {/* Main Body: Preview or Upload Prompt */}
      {previewUrl && file ? (
        <div className="p-4 flex flex-col items-center">
          <div className="relative group w-full h-48 bg-slate-900 rounded-xl overflow-hidden flex items-center justify-center border border-slate-200">
            <img
              src={previewUrl}
              alt={label}
              className="w-full h-full object-cover transition-transform group-hover:scale-105 duration-300"
            />
            {/* Overlay Action Buttons */}
            <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center space-x-2">
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-3 py-1.5 bg-white/90 hover:bg-white text-slate-800 rounded-lg text-xs font-medium shadow flex items-center gap-1"
              >
                <RefreshCw className="w-3.5 h-3.5" /> Replace
              </button>
              <button
                type="button"
                onClick={onFileRemove}
                className="px-3 py-1.5 bg-red-600/90 hover:bg-red-600 text-white rounded-lg text-xs font-medium shadow flex items-center gap-1"
              >
                <X className="w-3.5 h-3.5" /> Remove
              </button>
            </div>
          </div>

          {/* Metadata Card */}
          <div className="w-full mt-3 bg-slate-50 rounded-xl p-2.5 border border-slate-100 text-xs text-slate-600 flex justify-between items-center">
            <div className="truncate max-w-[160px]" title={file.name}>
              <span className="font-medium text-slate-800">{file.name}</span>
            </div>
            <div className="flex items-center space-x-2 text-[11px] text-slate-500">
              {fileDetails.width && (
                <span>{fileDetails.width}×{fileDetails.height}px</span>
              )}
              <span>•</span>
              <span>{fileDetails.sizeKb} KB</span>
            </div>
          </div>
        </div>
      ) : (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className="p-6 flex flex-col items-center justify-center text-center cursor-pointer min-h-[220px]"
        >
          <div className="w-12 h-12 rounded-2xl bg-sky-50 border border-sky-100 flex items-center justify-center text-sky-600 mb-3 group-hover:scale-110 transition-transform">
            <Camera className="w-6 h-6 stroke-[1.8]" />
          </div>
          <p className="text-sm font-semibold text-slate-800 mb-1">
            Upload {label}
          </p>
          <p className="text-xs text-slate-500 max-w-[220px] mb-3 leading-relaxed">
            {description}
          </p>
          <div className="flex items-center space-x-1.5">
            <span className="text-[11px] font-medium text-sky-700 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
              Drag & Drop
            </span>
            <span className="text-slate-300">or</span>
            <span className="text-[11px] font-medium text-slate-700 hover:text-sky-600 underline">
              Browse Files
            </span>
          </div>
          <div className="mt-3 text-[10px] text-slate-400">
            JPG, JPEG, PNG, WebP (Max 25MB)
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="px-4 py-2 bg-red-50 border-t border-red-200 flex items-center text-xs text-red-700 space-x-1.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={handleInputChange}
      />
    </div>
  );
};

