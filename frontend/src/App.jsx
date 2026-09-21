import React, { useState } from 'react';
import Header from './components/Header';
import ImageUpload from './components/ImageUpload';
import FrontCardReview from './components/FrontCardReview';
import LaserIdReview from './components/LaserIdReview';
import { AlertCircle, ScanLine, FileText } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('front'); // 'front' | 'laser'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [frontResult, setFrontResult] = useState(null);
  const [laserResult, setLaserResult] = useState(null);

  const handleTabChange = (newTab) => {
    if (newTab !== activeTab) {
      setActiveTab(newTab);
      setSelectedFile(null);
      setPreviewUrl(null);
      setError(null);
    }
  };

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setError(null);
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleClear = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setError(null);
    if (activeTab === 'front') {
      setFrontResult(null);
    } else {
      setLaserResult(null);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    const endpoint =
      activeTab === 'front' ? '/api/v1/ocr/id-card' : '/api/v1/ocr/laser-id';

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      const json = await response.json();

      if (!response.ok) {
        throw new Error(
          json?.detail || `Inference error: HTTP status ${response.status}`
        );
      }

      if (activeTab === 'front') {
        setFrontResult(json);
      } else {
        setLaserResult(json);
      }
    } catch (err) {
      setError(err.message || 'Failed to process document image.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <Header activeTab={activeTab} onTabChange={handleTabChange} />

      <main className="app-container">
        {error && (
          <div className="error-banner">
            <AlertCircle size={20} style={{ flexShrink: 0, marginTop: '2px' }} />
            <div>
              <strong>Extraction Error:</strong> {error}
            </div>
          </div>
        )}

        <div className="workspace-grid">
          {/* Left Column: Image Upload & Preview Controls */}
          <div>
            <ImageUpload
              activeTab={activeTab}
              selectedFile={selectedFile}
              previewUrl={previewUrl}
              isLoading={isLoading}
              onFileSelect={handleFileSelect}
              onClear={handleClear}
              onSubmit={handleSubmit}
            />
          </div>

          {/* Right Column: Review & Structured Extraction */}
          <div>
            {activeTab === 'front' ? (
              frontResult ? (
                <FrontCardReview
                  data={frontResult.data}
                  processingTimeMs={frontResult.processing_time_ms}
                />
              ) : (
                <div className="ui-card">
                  <div className="card-body empty-state">
                    <div className="empty-state-icon">
                      <ScanLine size={32} />
                    </div>
                    <h4>No Front ID Card Processed</h4>
                    <p>
                      Upload a front-side Thai National ID card image or click "Load Synthetic Thai ID" to test real-time OCR extraction and 13-digit checksum validation.
                    </p>
                  </div>
                </div>
              )
            ) : laserResult ? (
              <LaserIdReview
                data={laserResult.data}
                processingTimeMs={laserResult.processing_time_ms}
              />
            ) : (
              <div className="ui-card">
                <div className="card-body empty-state">
                  <div className="empty-state-icon">
                    <FileText size={32} />
                  </div>
                  <h4>No Laser ID Processed</h4>
                  <p>
                    Upload the back side of a Thai National ID card or click "Load Synthetic Laser ID" to test real-time 12-character alphanumeric Laser code extraction.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
