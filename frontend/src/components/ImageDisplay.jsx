import React from 'react';
import { Eye } from 'lucide-react';

export default function ImageDisplay({ originalImage, segmentationMask, opacity, title = null }) {
  return (
    <div className="space-y-5 animate-slideUp">
      {title && (
        <div className="flex items-center gap-3 mb-4">
          <div className="w-2 h-2 bg-gradient-to-r from-medical-accent to-medical-info rounded-full"></div>
          <h3 className="text-lg font-bold text-medical-text">{title}</h3>
        </div>
      )}
      
      <div className="flex gap-5 flex-col lg:flex-row">
        {/* Original Image */}
        <div className="flex-1 group">
          <p className="text-sm font-semibold text-medical-text mb-3">Original CT Slice</p>
          <div className="card p-0 overflow-hidden border-2 border-medical-gray group-hover:border-medical-accent group-hover:shadow-md transition-all duration-300 cursor-zoom-in">
            <img
              src={originalImage}
              alt="Original CT scan"
              className="w-full h-auto group-hover:scale-105 transition-transform duration-500"
            />
          </div>
        </div>

        {/* Segmentation / Overlay */}
        <div className="flex-1 group">
          <p className="text-sm font-semibold text-medical-text mb-3">
            {title ? 'Attention Map' : `Segmentation (${opacity}% opacity)`}
          </p>
          <div className="card p-0 overflow-hidden relative border-2 border-medical-gray group-hover:border-medical-info group-hover:shadow-lg transition-all duration-300 cursor-zoom-in">
            {/* Original Image as Base */}
            <img
              src={originalImage}
              alt="Base"
              className="w-full block group-hover:scale-105 transition-transform duration-500"
            />
            
            {/* Segmentation Mask Overlay */}
            <img
              src={`data:image/png;base64,${segmentationMask}`}
              alt="Segmentation"
              className="absolute inset-0 w-full h-full transition-opacity duration-200"
              style={{ opacity: opacity / 100 }}
            />
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="card bg-gradient-to-br from-medical-light-bg to-cyan-50 border-2 border-medical-accent shadow-md">
        <h3 className="text-sm font-bold text-medical-text mb-5 flex items-center gap-3">
          <span className="w-3 h-3 bg-gradient-to-r from-medical-accent to-medical-info rounded-full animate-pulse-subtle"></span>
          Segmentation Legend
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Background */}
          <div className="group cursor-pointer">
            <div className="flex items-center gap-3 p-4 bg-white rounded-lg border-2 border-gray-300 group-hover:border-gray-400 group-hover:shadow-md transition-all duration-300 transform group-hover:scale-105">
              <div className="w-8 h-8 bg-gradient-to-br from-gray-400 to-gray-500 rounded-lg flex-shrink-0 group-hover:shadow-lg transition-shadow duration-300"></div>
              <div>
                <p className="text-sm font-bold text-medical-text">Background</p>
                <p className="text-xs text-gray-600">Class 0</p>
              </div>
            </div>
          </div>

          {/* Kidney */}
          <div className="group cursor-pointer">
            <div className="flex items-center gap-3 p-4 bg-white rounded-lg border-2 border-cyan-300 group-hover:border-medical-info group-hover:shadow-md transition-all duration-300 transform group-hover:scale-105">
              <div className="w-8 h-8 bg-gradient-to-br from-medical-info to-blue-500 rounded-lg flex-shrink-0 group-hover:shadow-lg transition-shadow duration-300"></div>
              <div>
                <p className="text-sm font-bold text-medical-text">Kidney</p>
                <p className="text-xs text-gray-600">Class 1</p>
              </div>
            </div>
          </div>

          {/* Tumor */}
          <div className="group cursor-pointer">
            <div className="flex items-center gap-3 p-4 bg-white rounded-lg border-2 border-red-300 group-hover:border-medical-danger group-hover:shadow-md transition-all duration-300 transform group-hover:scale-105">
              <div className="w-8 h-8 bg-gradient-to-br from-medical-danger to-red-500 rounded-lg flex-shrink-0 group-hover:shadow-lg transition-shadow duration-300"></div>
              <div>
                <p className="text-sm font-bold text-medical-text">Tumor</p>
                <p className="text-xs text-gray-600">Class 2</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
