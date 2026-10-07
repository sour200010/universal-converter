"use client";

import React, { useRef, useState } from "react";
import { UploadCloud, File as FileIcon, X, Plus } from "lucide-react";

interface DropzoneProps {
  accept: string;
  files: File[];
  onFilesChange: (files: File[]) => void;
  disabled?: boolean;
}

export default function FileDropzone({ accept, files, onFilesChange, disabled = false }: DropzoneProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const handleIncomingFiles = (incoming: FileList | null) => {
    if (!incoming) return;
    const fileArray = Array.from(incoming);
    // Append unique files by name and size
    const merged = [...files];
    fileArray.forEach((newFile) => {
      if (!merged.some((f) => f.name === newFile.name && f.size === newFile.size)) {
        merged.push(newFile);
      }
    });
    onFilesChange(merged);
  };

  const removeFile = (index: number) => {
    const updated = files.filter((_, i) => i !== index);
    onFilesChange(updated);
  };

  return (
    <div className="w-full space-y-3">
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        multiple
        disabled={disabled}
        className="hidden"
        onChange={(e) => handleIncomingFiles(e.target.files)}
      />

      {files.length === 0 ? (
        <div
          onDragOver={(e) => { e.preventDefault(); if (!disabled) setIsDragOver(true); }}
          onDragLeave={() => setIsDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setIsDragOver(false);
            if (!disabled) handleIncomingFiles(e.dataTransfer.files);
          }}
          onClick={() => !disabled && inputRef.current?.click()}
          className={`flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl cursor-pointer transition-all ${
            isDragOver 
              ? "border-indigo-600 bg-indigo-50/50" 
              : "border-slate-300 hover:border-slate-400 bg-slate-50/60"
          } ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          <div className="p-3 bg-white border border-slate-200 rounded-full shadow-sm mb-3">
            <UploadCloud className="w-6 h-6 text-indigo-600" />
          </div>
          <p className="text-sm font-semibold text-slate-800">
            Click to upload files <span className="font-normal text-slate-500">or drag & drop</span>
          </p>
          <p className="text-xs text-slate-400 mt-1">Select one or multiple files ({accept})</p>
        </div>
      ) : (
        <div className="space-y-2">
          <div className="max-h-56 overflow-y-auto space-y-2 pr-1">
            {files.map((f, idx) => (
              <div
                key={`${f.name}-${idx}`}
                className="flex items-center justify-between p-3 bg-white border border-slate-200 rounded-xl shadow-xs"
              >
                <div className="flex items-center space-x-3 overflow-hidden">
                  <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg shrink-0">
                    <FileIcon className="w-4 h-4" />
                  </div>
                  <div className="truncate">
                    <p className="text-xs font-medium text-slate-800 truncate">{f.name}</p>
                    <p className="text-[11px] text-slate-400">{formatSize(f.size)}</p>
                  </div>
                </div>
                {!disabled && (
                  <button
                    type="button"
                    onClick={() => removeFile(idx)}
                    className="p-1 hover:bg-slate-100 rounded-md text-slate-400 hover:text-slate-600 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
            ))}
          </div>

          {!disabled && (
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="flex items-center justify-center space-x-1.5 w-full py-2 border border-dashed border-slate-300 hover:border-indigo-400 text-xs text-indigo-600 font-medium rounded-lg hover:bg-indigo-50/30 transition-all cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add more files</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}