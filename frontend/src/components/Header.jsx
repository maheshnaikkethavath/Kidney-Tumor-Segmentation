import React from 'react';
import { Heart } from 'lucide-react';

export default function Header() {
  return (
    <header className="border-b border-medical-gray bg-white sticky top-0 z-10 shadow-md">
      <div className="container mx-auto px-4 py-5 max-w-6xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="bg-gradient-to-br from-medical-accent to-medical-info rounded-lg p-2.5 shadow-md">
              <Heart className="w-6 h-6 text-white animate-pulse" />
            </div>
            <div>
              <h1 className="section-title m-0">MedImaging AI</h1>
              <p className="text-sm text-medical-gray-dark font-medium">Advanced Kidney & Tumor Segmentation</p>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-3 px-4 py-2 bg-gradient-to-r from-medical-accent-light to-blue-100 rounded-lg border border-medical-accent/30">
            <span className="w-2 h-2 bg-medical-info rounded-full animate-pulse"></span>
            <span className="text-sm font-semibold text-medical-accent">HybridUNet v1.0</span>
          </div>
        </div>
      </div>
    </header>
  );
}
