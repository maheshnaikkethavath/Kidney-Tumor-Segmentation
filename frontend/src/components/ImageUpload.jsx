import React, { useRef, useState } from 'react';
import { Upload, Loader2, FileImage } from 'lucide-react';

export default function ImageUpload({ onUpload, loading }) {
  const fileInputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const validateAndUpload = (file) => {
    if (!file) return;
    if (!['image/jpeg', 'image/png'].includes(file.type)) {
      alert('Please upload a PNG or JPG image');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB');
      return;
    }
    onUpload(file);
  };

  const handleFileChange = (e) => {
    validateAndUpload(e.target.files?.[0]);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (!loading) {
      validateAndUpload(e.dataTransfer.files?.[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  return (
    <div className="card animate-slideUp">
      <h2 className="section-title">Upload CT Scan</h2>
      
      <button
        onClick={handleClick}
        disabled={loading}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        className={`w-full border-2 border-dashed rounded-lg p-10 transition-all duration-300 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed ${
          isDragging
            ? 'border-medical-info bg-gradient-to-br from-cyan-50 to-blue-50 shadow-md'
            : 'border-medical-gray hover:border-medical-accent bg-medical-light-bg hover:bg-medical-accent-light'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".png,.jpg,.jpeg"
          onChange={handleFileChange}
          disabled={loading}
          className="hidden"
        />
        
        <div className="flex flex-col items-center">
          {loading ? (
            <>
              <div className="relative mb-4">
                <Loader2 className="w-12 h-12 text-medical-accent animate-spin" />
              </div>
              <p className="gradient-text font-semibold text-lg">Processing Image...</p>
              <p className="text-sm text-medical-gray-dark mt-2">AI is analyzing your CT scan</p>
            </>
          ) : (
            <>
              <div className="mb-4 p-4 bg-gradient-to-br from-medical-accent to-medical-info rounded-full">
                <Upload className="w-8 h-8 text-white" />
              </div>
              <p className="text-medical-text font-semibold text-lg">Click to upload or drag and drop</p>
              <p className="text-sm text-medical-gray-dark mt-2">PNG, JPG • Max 10MB</p>
            </>
          )}
        </div>
      </button>

      <div className="mt-5 bg-gradient-to-br from-medical-accent-light to-blue-100 rounded-lg border border-medical-accent/30 p-4 animate-fadeIn">
        <div className="flex items-start gap-3 mb-3">
          <FileImage className="w-5 h-5 text-medical-accent flex-shrink-0 mt-0.5" />
          <h3 className="font-semibold text-medical-text">Input Requirements</h3>
        </div>
        <ul className="text-sm text-medical-gray-dark space-y-2">
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-medical-accent rounded-full"></span>
            Image size: 256×256 pixels
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-medical-accent rounded-full"></span>
            Format: Grayscale CT slices
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-medical-accent rounded-full"></span>
            Output: 3-class segmentation
          </li>
          <li className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-medical-accent rounded-full"></span>
            Classes: Background, Kidney, Tumor
          </li>
        </ul>
      </div>
    </div>
  );
}
