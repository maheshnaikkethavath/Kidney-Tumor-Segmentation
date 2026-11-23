import React, { useState } from 'react';
import { Upload, Download, Zap, BarChart3, Loader2, GitCompare } from 'lucide-react';
import Header from './components/Header';
import ImageUpload from './components/ImageUpload';
import ImageDisplay from './components/ImageDisplay';
import AnalysisResults from './components/AnalysisResults';
import ReportGenerator from './components/ReportGenerator';
import ComparisonView from './components/ComparisonView';
import './index.css';

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [heatmap, setHeatmap] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [maskOpacity, setMaskOpacity] = useState(50);
  const [activeTab, setActiveTab] = useState('segmentation');
  const [compareMode, setCompareMode] = useState(false);
  const [comparisonResults, setComparisonResults] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);

  const handleImageUpload = async (file) => {
    setLoading(true);
    setError(null);
    try {
      // Store the uploaded image
      const reader = new FileReader();
      reader.onload = (e) => {
        setUploadedImage(e.target.result);
      };
      reader.readAsDataURL(file);

      // Call prediction API
      const { predictSegmentation } = await import('./utils/api');
      const result = await predictSegmentation(file);
      setPredictions(result);
      setActiveTab('segmentation');
    } catch (err) {
      setError(err.message);
      console.error('Upload error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateGradCAM = async () => {
    if (!uploadedImage || !predictions) {
      setError('Please upload an image first');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const { generateGradCAM } = await import('./utils/api');
      
      // Convert data URL back to File
      const blob = await (await fetch(uploadedImage)).blob();
      const file = new File([blob], 'image.png', { type: 'image/png' });
      
      const result = await generateGradCAM(file, 2); // Target class 2 (Tumor)
      setHeatmap(result);
      setActiveTab('heatmap');
    } catch (err) {
      setError(err.message);
      console.error('GradCAM error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCompareModels = async () => {
    if (!uploadedImage) {
      setError('Please upload an image first');
      return;
    }

    setCompareLoading(true);
    setError(null);
    try {
      const blob = await (await fetch(uploadedImage)).blob();
      const file = new File([blob], 'image.png', { type: 'image/png' });

      const { compareModels } = await import('./utils/api');
      const result = await compareModels(file);
      setComparisonResults(result);
      setCompareMode(true);
      setActiveTab('comparison');
    } catch (err) {
      setError(err.message);
      console.error('Compare models error:', err);
    } finally {
      setCompareLoading(false);
    }
  };

  const handleCloseComparison = () => {
    setCompareMode(false);
    setComparisonResults(null);
    setActiveTab('segmentation');
  };

  const handleDownloadReport = async (format) => {
    if (!uploadedImage || !predictions) {
      setError('Please upload an image first');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const { generateReport } = await import('./utils/api');
      
      // Convert data URL back to File
      const blob = await (await fetch(uploadedImage)).blob();
      const file = new File([blob], 'image.png', { type: 'image/png' });
      
      const result = await generateReport(file, 'Unknown', 'Unknown', format);

      // Download report
      const element = document.createElement('a');
      const reportBlob = new Blob([result.report], { type: format === 'html' ? 'text/html' : 'text/markdown' });
      element.href = URL.createObjectURL(reportBlob);
      element.download = `report.${format === 'html' ? 'html' : 'md'}`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    } catch (err) {
      setError(err.message);
      console.error('Report download error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-medical-light-bg">
      <Header />
      
      <main className="container mx-auto px-4 py-8 max-w-6xl">
        {error && (
          <div className="mb-6 p-5 bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-l-medical-danger rounded-lg text-medical-danger flex items-start gap-4 shadow-md animate-slideUp">
            <div className="flex-shrink-0 mt-0.5">
              <svg className="w-6 h-6 text-medical-danger" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="flex-1">
              <p className="font-bold text-red-800">Analysis Error</p>
              <p className="text-sm mt-2 text-red-700">{error}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Upload & Controls */}
          <div className="lg:col-span-1">
            <div className="sticky top-24 space-y-5">
              <ImageUpload 
                onUpload={handleImageUpload}
                loading={loading}
              />

              {predictions && (
                <div className="space-y-4 animate-slideUp">
                  <div className="card">
                    <h3 className="flex items-center gap-2 font-bold text-medical-text mb-5 text-sm">
                      <span className="w-2 h-2 bg-gradient-to-r from-medical-accent to-medical-info rounded-full"></span>
                      Advanced Tools
                    </h3>
                    
                    <button
                      onClick={handleGenerateGradCAM}
                      disabled={loading}
                      className="group btn-secondary w-full mb-4 hover:shadow-md transition-all duration-300"
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Generating...
                        </>
                      ) : (
                        <>
                          <Zap className="w-4 h-4 group-hover:scale-110 transition-transform duration-300" />
                          Generate Attention Map
                        </>
                      )}
                    </button>

                    <button
                      onClick={handleCompareModels}
                      disabled={compareLoading}
                      className="group w-full mb-4 px-4 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold rounded-lg hover:from-purple-600 hover:to-pink-600 transition-all duration-300 shadow-sm hover:shadow-md flex items-center justify-center gap-2 text-sm"
                    >
                      {compareLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Comparing...
                        </>
                      ) : (
                        <>
                          <GitCompare className="w-4 h-4 group-hover:scale-110 transition-transform duration-300" />
                          Compare Models
                        </>
                      )}
                    </button>

                    <div>
                      <label className="text-sm font-semibold text-medical-text mb-3 block">Segmentation Opacity</label>
                      <div className="flex items-center gap-3">
                        <input
                          type="range"
                          min="0"
                          max="100"
                          value={maskOpacity}
                          onChange={(e) => setMaskOpacity(Number(e.target.value))}
                          className="flex-1 h-2 bg-gradient-to-r from-medical-light-bg to-medical-accent rounded-full appearance-none cursor-pointer accent-medical-accent hover:h-3 transition-all duration-200"
                        />
                        <span className="text-sm font-bold text-white bg-gradient-to-r from-medical-accent to-medical-info px-3 py-1.5 rounded-lg min-w-12 text-center shadow-md">
                          {maskOpacity}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDownloadReport('markdown')}
                    disabled={loading}
                    className="group btn-primary w-full hover:shadow-lg transition-all duration-300"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Generating Report...
                      </>
                    ) : (
                      <>
                        <Download className="w-4 h-4 group-hover:scale-110 transition-transform duration-300" />
                        Download Report
                      </>
                    )}
                  </button>

                  <ReportGenerator 
                    predictions={predictions}
                    originalImage={uploadedImage}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Image Display & Results */}
          <div className="lg:col-span-2 space-y-6">
            {uploadedImage && (
              <>
                <div className="card">
                  <div className="flex items-center gap-3 mb-6">
                    <span className="w-2 h-2 bg-gradient-to-r from-medical-accent to-medical-info rounded-full"></span>
                    <h2 className="text-lg font-bold text-medical-text">Segmentation Analysis</h2>
                  </div>
                  
          {/* Tabs */}
                  <div className="flex gap-2 mb-6 border-b border-medical-gray">
                    <button
                      onClick={() => setActiveTab('segmentation')}
                      className={`px-5 py-3 font-semibold transition-all duration-300 text-sm border-b-2 relative ${
                        activeTab === 'segmentation'
                          ? 'border-medical-accent text-medical-accent'
                          : 'border-transparent text-gray-600 hover:text-medical-text'
                      }`}
                    >
                      <span className="flex items-center gap-2">
                        📊 Segmentation
                        {activeTab === 'segmentation' && (
                          <span className="inline-block w-2 h-2 bg-gradient-to-r from-medical-accent to-medical-info rounded-full animate-pulse-subtle"></span>
                        )}
                      </span>
                    </button>
                    {heatmap && (
                      <button
                        onClick={() => setActiveTab('heatmap')}
                        className={`px-5 py-3 font-semibold transition-all duration-300 text-sm border-b-2 relative ${
                          activeTab === 'heatmap'
                            ? 'border-medical-info text-medical-info'
                            : 'border-transparent text-gray-600 hover:text-medical-text'
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          🔥 Attention Map
                          {activeTab === 'heatmap' && (
                            <span className="inline-block w-2 h-2 bg-gradient-to-r from-medical-info to-cyan-400 rounded-full animate-pulse-subtle"></span>
                          )}
                        </span>
                      </button>
                    )}
                    {comparisonResults && (
                      <button
                        onClick={() => setActiveTab('comparison')}
                        className={`px-5 py-3 font-semibold transition-all duration-300 text-sm border-b-2 relative ${
                          activeTab === 'comparison'
                            ? 'border-purple-500 text-purple-600'
                            : 'border-transparent text-gray-600 hover:text-medical-text'
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          ⚖️ Model Compare
                          {activeTab === 'comparison' && (
                            <span className="inline-block w-2 h-2 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full animate-pulse-subtle"></span>
                          )}
                        </span>
                      </button>
                    )}
                  </div>

                  {/* Content */}
                  {activeTab === 'segmentation' && predictions && (
                    <ImageDisplay
                      originalImage={uploadedImage}
                      segmentationMask={predictions.mask_b64}
                      opacity={maskOpacity}
                    />
                  )}

                  {activeTab === 'heatmap' && heatmap && (
                    <ImageDisplay
                      originalImage={uploadedImage}
                      segmentationMask={heatmap.overlay_b64}
                      opacity={100}
                      title="Attention Heatmap for Tumor Class"
                    />
                  )}

                  {activeTab === 'comparison' && comparisonResults && (
                    <ComparisonView
                      comparisonResults={comparisonResults}
                      originalImage={uploadedImage}
                      onClose={handleCloseComparison}
                    />
                  )}
                </div>

                {predictions && (
                  <AnalysisResults predictions={predictions} />
                )}
              </>
            )}

            {!uploadedImage && (
              <div className="card h-full flex flex-col items-center justify-center min-h-[400px] bg-gradient-to-br from-medical-light-bg via-white to-cyan-50 border-2 border-dashed border-medical-accent/30 rounded-lg hover:border-medical-accent transition-all duration-300">
                <div className="text-center space-y-5">
                  <div className="mx-auto w-20 h-20 bg-gradient-to-br from-medical-accent-light to-cyan-100 rounded-2xl flex items-center justify-center">
                    <Upload className="w-10 h-10 text-medical-accent/70" />
                  </div>
                  <div>
                    <p className="text-medical-text font-bold text-lg">Ready to Analyze CT Scans</p>
                    <p className="text-sm text-gray-600 mt-2 leading-relaxed">Upload a medical imaging file to begin segmentation and tumor analysis using HybridUNet AI</p>
                  </div>
                  <div className="flex items-center justify-center gap-2 text-xs text-gray-500 mt-4">
                    <span className="flex items-center gap-1">✓ Instant segmentation</span>
                    <span className="w-1 h-1 bg-gray-400 rounded-full"></span>
                    <span className="flex items-center gap-1">✓ AI-powered analysis</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
