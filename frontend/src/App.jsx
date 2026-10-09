import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import ImageUpload from './components/ImageUpload';
import FrontCardReview from './components/FrontCardReview';
import LaserIdReview from './components/LaserIdReview';
import TopPipelineBar from './components/TopPipelineBar';
import { AlertCircle, ScanLine, FileText } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('front'); // 'front' | 'laser'
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Results state
  const [frontResult, setFrontResult] = useState(null);
  const [laserResult, setLaserResult] = useState(null);

  // Timer & stage tracking state
  const [elapsedMs, setElapsedMs] = useState(0);
  const timerRef = useRef(null);
  const workspaceRef = useRef(null);

  useEffect(() => {
    if (isLoading) {
      const startTime = performance.now();
      timerRef.current = setInterval(() => {
        setElapsedMs(Math.round(performance.now() - startTime));
      }, 50);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [isLoading]);

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
    setPreviewUrl((prev) => {
      if (prev) {
        URL.revokeObjectURL(prev);
      }
      return URL.createObjectURL(file);
    });
  };

  const handleClear = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setError(null);
    setElapsedMs(0);
    if (activeTab === 'front') {
      setFrontResult(null);
    } else {
      setLaserResult(null);
    }
  };

  const scrollToWorkspace = () => {
    if (workspaceRef.current) {
      const rect = workspaceRef.current.getBoundingClientRect();
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      const targetY = scrollTop + rect.top - 70;
      window.scrollTo({ top: Math.max(0, targetY), behavior: 'smooth' });
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;

    setIsLoading(true);
    setError(null);
    setElapsedMs(0);
    scrollToWorkspace();

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

      // Smoothly bring the review workspace into view so the user doesn't have to scroll
      setTimeout(scrollToWorkspace, 50);
    } catch (err) {
      setError(err.message || 'Failed to process document image.');
    } finally {
      setIsLoading(false);
    }
  };

  const currentResult = activeTab === 'front' ? frontResult : laserResult;

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

        <div className="workspace-container" ref={workspaceRef}>
          {/* Compact Top Pipeline Strip: Shows live steps & timings across the top without displacing side-by-side results */}
          <TopPipelineBar
            stages={currentResult?.stages}
            timingsMs={currentResult?.timings_ms}
            isLoading={isLoading}
            elapsedMs={elapsedMs}
            overallTimeMs={currentResult?.processing_time_ms ?? null}
            error={error}
            isRejected={currentResult?.is_rejected || currentResult?.status === 'rejected'}
            rejectionReason={currentResult?.rejection_reason}
          />

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

          {/* Right Column: Result sits directly at the top, perfectly side-by-side with card image */}
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
                      Upload a front-side Thai National ID card image or click "Load Synthetic Thai ID" to test real-time OCR extraction, grounding, and checksum validation.
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
        </div>
      </main>
    </div>
  );
}
