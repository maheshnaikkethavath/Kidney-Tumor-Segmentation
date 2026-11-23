import React, { useState } from 'react';
import { Download, FileText, Loader2, AlertCircle, CheckCircle2, Globe } from 'lucide-react';
import { generateReport } from '../utils/api';

export default function ReportGenerator({ predictions, originalImage }) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [format, setFormat] = useState('html');
  const [downloadStatus, setDownloadStatus] = useState(null);

  const handleGenerateReport = async () => {
    if (!predictions || !originalImage) return;

    setIsGenerating(true);
    setDownloadStatus(null);

    try {
      // Convert data URL to blob
      const response = await fetch(originalImage);
      const blob = await response.blob();
      const file = new File([blob], 'image.png', { type: 'image/png' });
      
      const result = await generateReport(file, 'Unknown', 'Unknown', format);
      
      // Download the report
      const reportBlob = new Blob([result.report], { 
        type: format === 'html' ? 'text/html' : 'text/markdown' 
      });
      const url = window.URL.createObjectURL(reportBlob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `medical-report-${new Date().getTime()}.${format === 'pdf' ? 'pdf' : 'md'}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setDownloadStatus('success');
      setTimeout(() => setDownloadStatus(null), 3000);
    } catch (error) {
      console.error('Error generating report:', error);
      setDownloadStatus('error');
      setTimeout(() => setDownloadStatus(null), 3000);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="card animate-slideUp">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-2 h-2 bg-gradient-to-r from-medical-accent to-medical-info rounded-full"></div>
          <h2 className="text-lg font-bold text-medical-text">Generate Medical Report</h2>
        </div>
        <p className="text-sm text-gray-600">Export analysis results in your preferred format</p>
      </div>

      {/* Format Selection */}
      <div className="space-y-4 mb-6">
        <label className="text-sm font-semibold text-medical-text">Select Format</label>
        <div className="grid grid-cols-2 gap-3">
          {[
            {
              id: 'html',
              label: 'Interactive HTML',
              icon: Globe,
              description: 'Rich web format with images',
              gradient: 'from-medical-accent to-blue-500',
            },
            {
              id: 'markdown',
              label: 'Markdown Text',
              icon: FileText,
              description: 'Lightweight document',
              gradient: 'from-cyan-400 to-medical-info',
            },
          ].map((fmt) => {
            const Icon = fmt.icon;
            const isSelected = format === fmt.id;
            return (
              <button
                key={fmt.id}
                onClick={() => setFormat(fmt.id)}
                className={`p-4 rounded-lg border-2 transition-all duration-300 hover:scale-105 ${
                  isSelected
                    ? `border-medical-accent shadow-lg bg-gradient-to-br ${fmt.gradient} bg-opacity-5`
                    : 'border-medical-gray bg-white hover:border-medical-accent-light'
                }`}
              >
                <Icon
                  className={`w-6 h-6 mx-auto mb-2 ${
                    isSelected ? 'text-medical-accent scale-110' : 'text-gray-600'
                  } transition-transform duration-300`}
                />
                <p className={`text-sm font-semibold ${
                  isSelected ? 'text-medical-accent' : 'text-medical-text'
                }`}>
                  {fmt.label}
                </p>
                <p className="text-xs text-gray-600 mt-1">{fmt.description}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* Status Message */}
      {downloadStatus === 'success' && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3 animate-slideUp">
          <CheckCircle2 className="w-5 h-5 text-medical-success flex-shrink-0" />
          <p className="text-sm font-medium text-green-700">Report downloaded successfully!</p>
        </div>
      )}

      {downloadStatus === 'error' && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 animate-slideUp">
          <AlertCircle className="w-5 h-5 text-medical-danger flex-shrink-0" />
          <p className="text-sm font-medium text-red-700">Failed to generate report. Please try again.</p>
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={handleGenerateReport}
        disabled={isGenerating || !predictions}
        className="btn-primary w-full group disabled:opacity-60 disabled:cursor-not-allowed"
      >
        <div className="flex items-center justify-center gap-2">
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin text-white" />
              <span>Generating...</span>
            </>
          ) : (
            <>
              <Download className="w-5 h-5 group-hover:scale-110 transition-transform duration-300" />
              <span>Generate & Download Report</span>
            </>
          )}
        </div>
      </button>

      {/* Info Box */}
      <div className="mt-6 p-4 bg-gradient-to-r from-medical-accent-light to-cyan-50 border border-medical-accent rounded-lg">
        <p className="text-xs text-gray-700 leading-relaxed">
          <span className="font-semibold text-medical-accent">📋 Report includes:</span> Analysis metrics, 
          tumor detection status, class distribution, segmentation visualization, and clinical recommendations. 
          All reports are generated with a timestamp for medical record keeping.
        </p>
      </div>
    </div>
  );
}
