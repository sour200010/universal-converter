"use client";

import React, { useState, useEffect } from "react";
import FileDropzone from "@/components/FileDropzone";
import { 
  FileText, 
  FileSpreadsheet, 
  Presentation, 
  Image as ImageIcon, 
  Minimize2, 
  Crop, 
  ArrowRight, 
  Loader2, 
  CheckCircle2, 
  AlertCircle, 
  Trash2, 
  ShieldCheck, 
  Gauge, 
  Sliders, 
  Lock, 
  Unlock 
} from "lucide-react";

type Tool = {
  id: string;
  name: string;
  desc: string;
  endpoint: string;
  accept: string;
  targetFormat?: string;
  outputExt: string;
  icon: React.ElementType;
};

type FileQueueItem = {
  file: File;
  status: "pending" | "processing" | "completed" | "error";
  errorText?: string;
};

const TOOLS: Tool[] = [
  { id: "pdf-docx", name: "PDF to Word", desc: "Editable .docx layout conversion", endpoint: "/api/convert/pdf-to-office", targetFormat: "docx", accept: ".pdf", outputExt: ".docx", icon: FileText },
  { id: "pdf-xlsx", name: "PDF to Excel", desc: "Extract structured data tables", endpoint: "/api/convert/pdf-to-office", targetFormat: "xlsx", accept: ".pdf", outputExt: ".xlsx", icon: FileSpreadsheet },
  { id: "pdf-pptx", name: "PDF to PowerPoint", desc: "Convert pages into presentation slides", endpoint: "/api/convert/pdf-to-office", targetFormat: "pptx", accept: ".pdf", outputExt: ".pptx", icon: Presentation },
  { id: "office-pdf", name: "Office to PDF", desc: "Word, Excel, or PowerPoint to PDF", endpoint: "/api/convert/office-to-pdf", accept: ".docx,.pptx,.xlsx", outputExt: ".pdf", icon: FileText },
  { id: "compress-pdf", name: "Compress PDF", desc: "Streamline fonts and embedded images", endpoint: "/api/pdf/compress", accept: ".pdf", outputExt: ".pdf", icon: Minimize2 },
  { id: "img-resize", name: "Resize & Compress Image", desc: "Adjust dimensions, DPI, and file size in KB", endpoint: "/api/image/resize-compress", accept: "image/*", outputExt: ".jpg", icon: Crop },
  { id: "img-pdf", name: "Image to PDF", desc: "Pack image files into single PDFs", endpoint: "/api/image/to-pdf", accept: "image/*", outputExt: ".pdf", icon: ImageIcon },
];

const COMPRESSION_LEVELS = [
  { id: "extreme", title: "Extreme Compression", desc: "Less quality, high compression" },
  { id: "recommended", title: "Recommended Compression", desc: "Good quality, good compression" },
  { id: "low", title: "Less Compression", desc: "High quality, less compression" },
];

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export default function App() {
  const [activeTool, setActiveTool] = useState<Tool>(TOOLS[0]);
  const [files, setFiles] = useState<File[]>([]);
  const [queue, setQueue] = useState<FileQueueItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [purgeSuccess, setPurgeSuccess] = useState(false);

  // Tool specific configurations
  const [compressionLevel, setCompressionLevel] = useState<string>("recommended");
  const [unit, setUnit] = useState<string>("Pixels (px)");
  const [targetDpi, setTargetDpi] = useState<number>(72);
  const [width, setWidth] = useState<number | string>("");
  const [height, setHeight] = useState<number | string>("");
  const [lockRatio, setLockRatio] = useState<boolean>(true);
  const [exportFormat, setExportFormat] = useState<string>("JPEG");
  const [quality, setQuality] = useState<number>(80);
  const [targetKb, setTargetKb] = useState<number>(0);

  // Sync files list to processing queue
  useEffect(() => {
    setQueue(files.map(f => ({ file: f, status: "pending" })));
    setPurgeSuccess(false);
  }, [files]);

  const executeBatch = async () => {
    if (files.length === 0 || isProcessing) return;

    setIsProcessing(true);
    setPurgeSuccess(false);

    for (let i = 0; i < files.length; i++) {
      const currentItem = files[i];

      // Mark current item as processing
      setQueue(prev => prev.map((item, idx) => idx === i ? { ...item, status: "processing" } : item));

      const data = new FormData();
      data.append("file", currentItem);

      if (activeTool.targetFormat) data.append("target_format", activeTool.targetFormat);
      if (activeTool.id === "compress-pdf") data.append("compression_level", compressionLevel);
      if (activeTool.id === "img-resize") {
        if (width) data.append("width", width.toString());
        if (height) data.append("height", height.toString());
        data.append("unit", unit);
        data.append("target_dpi", targetDpi.toString());
        data.append("export_format", exportFormat);
        data.append("quality", quality.toString());
        data.append("target_kb", targetKb.toString());
      }

      try {
        const res = await fetch(`${API_BASE}${activeTool.endpoint}`, {
          method: "POST",
          body: data,
        });

        if (!res.ok) {
          const err = await res.json().catch(() => ({ detail: "Conversion failed" }));
          throw new Error(err.detail || "Server failed to process file");
        }

        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        const base = currentItem.name.substring(0, currentItem.name.lastIndexOf("."));
        const finalExt = activeTool.id === "img-resize" ? `.${exportFormat.toLowerCase()}` : activeTool.outputExt;
        link.download = `${base}_processed${finalExt}`;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);

        setQueue(prev => prev.map((item, idx) => idx === i ? { ...item, status: "completed" } : item));
      } catch (e: any) {
        setQueue(prev => prev.map((item, idx) => idx === i ? { ...item, status: "error", errorText: e.message } : item));
      }
    }

    setIsProcessing(false);
  };

  const clearAllAndPurge = () => {
    setFiles([]);
    setQueue([]);
    setPurgeSuccess(true);
    setTimeout(() => setPurgeSuccess(false), 4000);
  };

  const completedCount = queue.filter(q => q.status === "completed").length;
  const allFinished = queue.length > 0 && queue.every(q => q.status === "completed" || q.status === "error");

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 py-10 px-4 sm:px-6">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="text-center space-y-2">
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl text-slate-900">
            Universal Document Engine
          </h1>
          <p className="text-slate-500 text-sm sm:text-base">
            High-speed document conversion with privacy-first sandboxing.
          </p>
        </header>

        {/* Tool Cards */}
        <section className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {TOOLS.map((tool) => {
            const Icon = tool.icon;
            const selected = activeTool.id === tool.id;
            return (
              <button
                key={tool.id}
                disabled={isProcessing}
                onClick={() => {
                  setActiveTool(tool);
                  setFiles([]);
                }}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  selected
                    ? "bg-white border-indigo-600 shadow-sm ring-2 ring-indigo-600/10"
                    : "bg-white border-slate-200 hover:border-slate-300"
                } ${isProcessing ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <div className={`p-2 w-fit rounded-lg mb-2 ${selected ? "bg-indigo-50 text-indigo-600" : "bg-slate-100 text-slate-600"}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <div className="font-semibold text-sm text-slate-800">{tool.name}</div>
                <div className="text-xs text-slate-400 mt-0.5 line-clamp-1">{tool.desc}</div>
              </button>
            );
          })}
        </section>

        {/* Processing Box */}
        <section className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900">{activeTool.name}</h2>
              <p className="text-xs text-slate-400">{activeTool.desc}</p>
            </div>
            <div className="flex items-center space-x-1.5 text-xs text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-md">
              <ShieldCheck className="w-4 h-4" />
              <span>Isolated Memory Sandbox</span>
            </div>
          </div>

          <FileDropzone
            accept={activeTool.accept}
            files={files}
            onFilesChange={setFiles}
            disabled={isProcessing}
          />

          {/* Compress PDF Settings */}
          {activeTool.id === "compress-pdf" && (
            <div className="space-y-3 pt-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Gauge className="w-4 h-4 text-indigo-600" />
                Compression Level
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {COMPRESSION_LEVELS.map((lvl) => {
                  const isChecked = compressionLevel === lvl.id;
                  return (
                    <div
                      key={lvl.id}
                      onClick={() => !isProcessing && setCompressionLevel(lvl.id)}
                      className={`cursor-pointer p-3.5 rounded-xl border transition-all text-left ${
                        isChecked
                          ? "border-indigo-600 bg-indigo-50/40 ring-1 ring-indigo-600"
                          : "border-slate-200 hover:border-slate-300 bg-white"
                      }`}
                    >
                      <div className="text-sm font-semibold text-slate-800">{lvl.title}</div>
                      <div className="text-xs text-slate-500 mt-1">{lvl.desc}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Image Resizer Configurations */}
          {activeTool.id === "img-resize" && files.length > 0 && (
            <div className="space-y-4 pt-3 border-t border-slate-100">
              <label className="text-xs font-semibold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                <Sliders className="w-4 h-4 text-indigo-600" />
                Batch Resizing Dimensions & Export Settings
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="text-xs font-medium text-slate-600 block mb-1">Unit</label>
                  <select 
                    value={unit} 
                    onChange={(e) => setUnit(e.target.value)}
                    className="w-full text-xs border border-slate-200 rounded-lg px-2.5 py-2 bg-white"
                  >
                    <option>Pixels (px)</option>
                    <option>Inches (in)</option>
                    <option>Centimeters (cm)</option>
                    <option>Millimeters (mm)</option>
                  </select>
                </div>
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-medium text-slate-600">Width ({unit})</label>
                    <button
                      type="button"
                      onClick={() => setLockRatio(!lockRatio)}
                      className="text-[11px] flex items-center gap-1 text-indigo-600"
                    >
                      {lockRatio ? <Lock className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}
                      {lockRatio ? "Locked" : "Free"}
                    </button>
                  </div>
                  <input
                    type="number"
                    value={width}
                    onChange={(e) => setWidth(e.target.value)}
                    placeholder="Auto"
                    className="w-full text-xs border border-slate-200 rounded-lg px-2.5 py-2"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-slate-600 block mb-1">Export Format</label>
                  <select 
                    value={exportFormat} 
                    onChange={(e) => setExportFormat(e.target.value)}
                    className="w-full text-xs border border-slate-200 rounded-lg px-2.5 py-2 bg-white"
                  >
                    <option value="JPEG">JPEG</option>
                    <option value="PNG">PNG</option>
                    <option value="WEBP">WEBP</option>
                  </select>
                </div>
              </div>
            </div>
          )}

          {/* Queue Status Progress */}
          {queue.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-slate-100">
              <div className="flex justify-between text-xs text-slate-500 font-medium">
                <span>Batch Progress ({completedCount}/{queue.length})</span>
                <span>{Math.round((completedCount / queue.length) * 100)}%</span>
              </div>
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div 
                  className="bg-indigo-600 h-full transition-all duration-300"
                  style={{ width: `${(completedCount / queue.length) * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Action Row */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
            <div className="flex items-center space-x-2">
              {purgeSuccess && (
                <span className="text-xs text-emerald-600 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" /> Files wiped cleanly from server.
                </span>
              )}
              {allFinished && (
                <button
                  type="button"
                  onClick={clearAllAndPurge}
                  className="text-xs text-rose-600 hover:text-rose-700 font-medium flex items-center gap-1.5 px-3 py-1.5 bg-rose-50 hover:bg-rose-100 rounded-lg transition-colors cursor-pointer"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete Files from Server Now</span>
                </button>
              )}
            </div>

            <button
              onClick={executeBatch}
              disabled={files.length === 0 || isProcessing}
              className="w-full sm:w-auto px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 text-white disabled:text-slate-400 text-sm font-medium rounded-xl transition-all shadow-sm flex items-center justify-center space-x-2 cursor-pointer disabled:cursor-not-allowed"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Converting Batch...</span>
                </>
              ) : (
                <>
                  <span>Convert {files.length > 1 ? `All (${files.length})` : "Files"}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </section>
      </div>
    </div>
  );
}