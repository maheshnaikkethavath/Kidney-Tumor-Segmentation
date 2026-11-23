import React, { useState } from 'react';
import { CheckCircle2, AlertCircle, X } from 'lucide-react';

const CLASS_COLORS = {
  background: '#6b7280',
  kidney: '#06b6d4',
  tumor: '#ef4444',
};

function ModelCard({ modelKey, result, originalImage }) {
  const { display_name, mask_b64, tumor_detected, tumor_area_pixels, tumor_percentage, confidence_scores, class_distribution } = result;

  const pixel_size_mm = 0.1;
  const tumor_area_mm2 = tumor_area_pixels * (pixel_size_mm ** 2);
  const tumor_area_cm2 = tumor_area_mm2 / 100;

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
      <div className="px-4 py-3 bg-gradient-to-r from-gray-50 to-white border-b border-gray-100">
        <h4 className="font-bold text-sm text-gray-800">{display_name}</h4>
      </div>

      <div className="relative p-3">
        <div className="relative rounded-lg overflow-hidden border border-gray-200">
          <img src={originalImage} alt="Original" className="w-full h-auto block" />
          <img
            src={`data:image/png;base64,${mask_b64}`}
            alt={`${display_name} segmentation`}
            className="absolute inset-0 w-full h-full mix-blend-normal"
            style={{ opacity: 0.6 }}
          />
        </div>
      </div>

      <div className="px-4 pb-4 space-y-3">
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold ${
          tumor_detected ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'
        }`}>
          {tumor_detected ? <AlertCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          {tumor_detected ? 'Tumor Detected' : 'No Tumor'}
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-50 rounded-lg p-2 text-center">
            <p className="text-gray-500 font-medium">Area</p>
            <p className="font-bold text-gray-800">{tumor_area_pixels.toLocaleString()} px</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-2 text-center">
            <p className="text-gray-500 font-medium">Coverage</p>
            <p className="font-bold text-gray-800">{tumor_percentage.toFixed(2)}%</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-2 text-center">
            <p className="text-gray-500 font-medium">Area (cm²)</p>
            <p className="font-bold text-gray-800">{tumor_area_cm2.toFixed(2)}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-2 text-center">
            <p className="text-gray-500 font-medium">Confidence</p>
            <p className="font-bold text-gray-800">{confidence_scores?.tumor?.toFixed(1)}%</p>
          </div>
        </div>

        <div className="space-y-2">
          {class_distribution && (
            <>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: CLASS_COLORS.kidney }}></span>
                <span className="text-gray-600 flex-1">Kidney</span>
                <span className="font-semibold text-gray-800">{class_distribution.kidney_pixels?.toLocaleString()} px</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: CLASS_COLORS.tumor }}></span>
                <span className="text-gray-600 flex-1">Tumor</span>
                <span className="font-semibold text-gray-800">{class_distribution.tumor_pixels?.toLocaleString()} px</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ComparisonView({ comparisonResults, originalImage, onClose }) {
  if (!comparisonResults || !comparisonResults.results) return null;

  const results = Object.entries(comparisonResults.results);

  return (
    <div className="space-y-6 animate-slideUp">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full"></span>
          <h2 className="text-lg font-bold text-medical-text">Model Comparison</h2>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <X className="w-5 h-5 text-gray-500" />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {results.map(([key, result]) => (
          <ModelCard
            key={key}
            modelKey={key}
            result={result}
            originalImage={originalImage}
          />
        ))}
      </div>

      {results.length >= 2 && (
        <div className="card bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200">
          <h3 className="font-bold text-sm text-gray-800 mb-4">Agreement Summary</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-gray-500 text-xs font-medium mb-1">Models Agree</p>
              <p className="font-bold text-lg text-purple-700">
                {(() => {
                  const detections = results.map(([, r]) => r.tumor_detected);
                  const allSame = detections.every(v => v === detections[0]);
                  return allSame ? `${detections.length}/${detections.length}` : `${detections.filter(Boolean).length}/${detections.length}`;
                })()}
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-gray-500 text-xs font-medium mb-1">Avg Tumor Area</p>
              <p className="font-bold text-lg text-purple-700">
                {Math.round(results.reduce((sum, [, r]) => sum + r.tumor_area_pixels, 0) / results.length).toLocaleString()} px
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-gray-500 text-xs font-medium mb-1">Avg Coverage</p>
              <p className="font-bold text-lg text-purple-700">
                {(results.reduce((sum, [, r]) => sum + r.tumor_percentage, 0) / results.length).toFixed(2)}%
              </p>
            </div>
            <div className="bg-white rounded-lg p-3 text-center shadow-sm">
              <p className="text-gray-500 text-xs font-medium mb-1">Avg Confidence</p>
              <p className="font-bold text-lg text-purple-700">
                {(results.reduce((sum, [, r]) => sum + (r.confidence_scores?.tumor || 0), 0) / results.length).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
