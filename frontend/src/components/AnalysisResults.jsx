import React from 'react';
import { AlertCircle, CheckCircle2, BarChart3, Info } from 'lucide-react';

export default function AnalysisResults({ predictions }) {
  const { tumor_detected, tumor_area_pixels, tumor_percentage, class_distribution } = predictions;

  // Calculate tumor area in cm² (assuming pixel size of 0.1mm)
  const pixel_size_mm = 0.1;
  const tumor_area_mm2 = tumor_area_pixels * (pixel_size_mm ** 2);
  const tumor_area_cm2 = tumor_area_mm2 / 100;

  return (
    <div className="space-y-5 animate-slideUp">
      {/* Tumor Status Alert */}
      <div
        className={`card border-l-4 ${
          tumor_detected
            ? 'border-l-medical-danger bg-red-50 hover:shadow-lg'
            : 'border-l-medical-success bg-green-50'
        }`}
      >
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0 mt-1">
            {tumor_detected ? (
              <AlertCircle className="w-7 h-7 text-medical-danger" />
            ) : (
              <CheckCircle2 className="w-7 h-7 text-medical-success" />
            )}
          </div>
          <div className="flex-1">
            <h3 className={`font-bold text-xl ${
              tumor_detected ? 'text-medical-danger' : 'text-medical-success'
            }`}>
              {tumor_detected ? 'Tumor Detected' : 'No Tumor Detected'}
            </h3>
            <p className={`text-sm mt-2 font-medium ${
              tumor_detected ? 'text-red-700' : 'text-green-700'
            }`}>
              {tumor_detected
                ? 'Abnormal tissue growth identified. Please consult a medical professional.'
                : 'No abnormal tissue growth detected. Continue with regular monitoring.'}
            </p>
          </div>
        </div>
      </div>

      {/* Quantitative Results Grid */}
      <div>
        <h3 className="flex items-center gap-2 text-sm font-semibold text-medical-text mb-3">
          <BarChart3 className="w-5 h-5 text-medical-accent" />
          Analysis Metrics
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="stat-box hover:from-medical-accent-light hover:to-cyan-100 tooltip">
            <p className="text-gray-600 text-xs font-semibold mb-2">Tumor Area</p>
            <p className="text-2xl font-bold gradient-text">{tumor_area_pixels?.toLocaleString() || 0}</p>
            <p className="text-gray-600 text-xs mt-1">pixels</p>
            <div className="tooltip-text">Total pixels in tumor region</div>
          </div>

          <div className="stat-box hover:from-cyan-100 hover:to-medical-accent-light tooltip">
            <p className="text-gray-600 text-xs font-semibold mb-2">Area (cm²)</p>
            <p className="text-2xl font-bold gradient-text">{tumor_area_cm2.toFixed(2)}</p>
            <p className="text-gray-600 text-xs mt-1">square cm</p>
            <div className="tooltip-text">Calculated tumor area</div>
          </div>

          <div className="stat-box hover:from-medical-accent-light hover:to-blue-100 tooltip">
            <p className="text-gray-600 text-xs font-semibold mb-2">Coverage</p>
            <p className="text-2xl font-bold gradient-text">{tumor_percentage?.toFixed(2) || 0}%</p>
            <p className="text-gray-600 text-xs mt-1">of image</p>
            <div className="tooltip-text">Tumor percentage</div>
          </div>

          <div className="stat-box hover:from-blue-100 hover:to-medical-accent-light tooltip">
            <p className="text-gray-600 text-xs font-semibold mb-2">Model</p>
            <p className="text-2xl font-bold gradient-text">HybridUNet</p>
            <p className="text-gray-600 text-xs mt-1">AI assisted</p>
            <div className="tooltip-text">Advanced deep learning model</div>
          </div>
        </div>
      </div>

      {/* Class Distribution */}
      <div className="card">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-medical-text mb-5">
          <span className="w-3 h-3 bg-gradient-to-r from-medical-accent to-medical-info rounded-full"></span>
          Class Distribution
        </h3>
        
        <div className="space-y-4">
          {class_distribution && (
            <>
              {/* Background */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-medical-text">Background</span>
                  <span className="badge">
                    {class_distribution.background_pixels?.toLocaleString() || 0} px
                  </span>
                </div>
                <div className="w-full bg-medical-gray rounded-full h-3 overflow-hidden border border-medical-gray">
                  <div
                    className="bg-gradient-to-r from-gray-400 to-gray-500 h-full transition-all duration-700"
                    style={{
                      width: `${
                        ((class_distribution.background_pixels || 0) / (256 * 256)) * 100
                      }%`,
                    }}
                  ></div>
                </div>
              </div>

              {/* Kidney */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-cyan-600">Kidney</span>
                  <span className="badge bg-cyan-100 text-medical-info">
                    {class_distribution.kidney_pixels?.toLocaleString() || 0} px
                  </span>
                </div>
                <div className="w-full bg-medical-gray rounded-full h-3 overflow-hidden border border-medical-gray">
                  <div
                    className="bg-gradient-to-r from-medical-info to-blue-400 h-full transition-all duration-700"
                    style={{
                      width: `${((class_distribution.kidney_pixels || 0) / (256 * 256)) * 100}%`,
                    }}
                  ></div>
                </div>
              </div>

              {/* Tumor */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-medical-danger">Tumor</span>
                  <span className="badge bg-red-100 text-medical-danger">
                    {class_distribution.tumor_pixels?.toLocaleString() || 0} px
                  </span>
                </div>
                <div className="w-full bg-medical-gray rounded-full h-3 overflow-hidden border border-medical-gray">
                  <div
                    className="bg-gradient-to-r from-medical-danger to-red-500 h-full transition-all duration-700"
                    style={{
                      width: `${
                        ((class_distribution.tumor_pixels || 0) / (256 * 256)) * 100
                      }%`,
                    }}
                  ></div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Clinical Notes */}
      <div className="card border-l-4 border-l-medical-warning bg-yellow-50 hover:shadow-lg">
        <div className="flex items-start gap-3">
          <Info className="w-6 h-6 text-medical-warning flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-bold text-medical-warning mb-3">Important Disclaimer</h3>
            <ul className="text-sm text-medical-text space-y-2">
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-medical-warning rounded-full mt-1.5 flex-shrink-0"></span>
                <span><strong>Clinical Review:</strong> Results must be validated by a qualified radiologist</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-medical-warning rounded-full mt-1.5 flex-shrink-0"></span>
                <span><strong>Comparative Analysis:</strong> Compare with previous imaging for assessment</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-medical-warning rounded-full mt-1.5 flex-shrink-0"></span>
                <span><strong>Clinical Context:</strong> Consider patient history and symptoms</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 bg-medical-warning rounded-full mt-1.5 flex-shrink-0"></span>
                <span><strong>Diagnostic Aid:</strong> Use as a supportive tool only</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
