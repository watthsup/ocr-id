import React, { useRef, useState } from 'react';
import {
  UploadCloud,
  Image as ImageIcon,
  Sparkles,
  X,
  Play,
  Loader2,
  RotateCcw,
  RotateCw,
  Camera,
} from 'lucide-react';
import { generateSampleFrontCard, generateSampleLaserCard } from '../utils/sampleImages';
import { rotateImageFile } from '../utils/imageUtils';
import CameraCaptureModal from './CameraCaptureModal';

export default function ImageUpload({
  activeTab,
  selectedFile,
  previewUrl,
  isLoading,
  onFileSelect,
  onClear,
  onSubmit,
}) {
  const fileInputRef = useRef(null);
  const [isDragActive, setIsDragActive] = useState(false);
  const [isRotating, setIsRotating] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('image/')) {
        onFileSelect(file);
      }
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelect(e.target.files[0]);
    }
  };

  const handleRotate = async (degrees) => {
    if (!selectedFile || isLoading || isRotating) return;
    try {
      setIsRotating(true);
      const rotated = await rotateImageFile(selectedFile, degrees);
      onFileSelect(rotated);
    } catch (err) {
      console.error('Failed to rotate image:', err);
    } finally {
      setIsRotating(false);
    }
  };

  const loadSample = async () => {
    if (activeTab === 'front') {
      const sample = await generateSampleFrontCard();
      onFileSelect(sample);
    } else {
      const sample = await generateSampleLaserCard();
      onFileSelect(sample);
    }
  };

  return (
    <>
      <div className="ui-card upload-card">
        <div className="card-header">
          <h3>
            <ImageIcon size={18} color="#C41230" />
            <span>{activeTab === 'front' ? 'Front ID Card Image' : 'Back Card Image (Laser ID)'}</span>
          </h3>
          <div className="header-action-group">
            <button
              type="button"
              className="btn btn-outline btn-sm camera-header-btn"
              onClick={() => setIsCameraOpen(true)}
              disabled={isLoading || isRotating}
              title="Open camera scanner with card overlay box"
            >
              <Camera size={14} color="#C41230" />
              <span>Camera</span>
            </button>
            {selectedFile && (
              <>
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={() => handleRotate(-90)}
                  disabled={isLoading || isRotating}
                  title="Rotate 90° counter-clockwise (Left)"
                >
                  <RotateCcw size={14} className={isRotating ? 'spinner' : ''} />
                  <span>Rotate Left</span>
                </button>
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={() => handleRotate(90)}
                  disabled={isLoading || isRotating}
                  title="Rotate 90° clockwise (Right)"
                >
                  <RotateCw size={14} className={isRotating ? 'spinner' : ''} />
                  <span>Rotate Right</span>
                </button>
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={onClear}
                  disabled={isLoading || isRotating}
                  title="Remove selected image"
                >
                  <X size={14} />
                  <span>Clear</span>
                </button>
              </>
            )}
          </div>
        </div>

        <div className="card-body upload-card-body">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            style={{ display: 'none' }}
            onChange={handleFileInput}
          />

          {!previewUrl ? (
            <div
              className={`dropzone ${isDragActive ? 'drag-active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <div className="dropzone-icon">
                <UploadCloud size={24} />
              </div>
              <div>
                <p className="dropzone-text">Click or drag & drop card image here</p>
                <p className="dropzone-hint">Supports JPEG, PNG, or WEBP up to 10MB</p>
              </div>

              <div className="dropzone-divider">
                <span>or</span>
              </div>

              <button
                type="button"
                className="btn btn-outline btn-sm dropzone-camera-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  setIsCameraOpen(true);
                }}
              >
                <Camera size={15} color="#C41230" />
                <span>Open Camera & Scan</span>
              </button>
            </div>
          ) : (
            <div className="preview-wrapper">
              <img src={previewUrl} alt="Card Preview" className="preview-image" />

              {/* Quick Floating Rotation Controls */}
              {!isLoading && (
                <div className="preview-floating-toolbar">
                  <button
                    type="button"
                    className="preview-action-btn"
                    onClick={() => handleRotate(-90)}
                    disabled={isRotating}
                    title="Rotate Left (90° CCW)"
                  >
                    <RotateCcw size={13} className={isRotating ? 'spinner' : ''} />
                    <span>90° Left</span>
                  </button>
                  <button
                    type="button"
                    className="preview-action-btn"
                    onClick={() => handleRotate(90)}
                    disabled={isRotating}
                    title="Rotate Right (90° CW)"
                  >
                    <RotateCw size={13} className={isRotating ? 'spinner' : ''} />
                    <span>90° Right</span>
                  </button>
                  <button
                    type="button"
                    className="preview-action-btn camera-retake-btn"
                    onClick={() => setIsCameraOpen(true)}
                    title="Open camera to recapture"
                  >
                    <Camera size={13} color="#C41230" />
                    <span>Retake via Camera</span>
                  </button>
                </div>
              )}

              {isLoading && (
                <>
                  <div className="scanning-bar" />
                  <div className="scanning-overlay">
                    <div className="scanning-pill">
                      <Loader2 size={14} className="spinner" />
                      <span>Azure OCR + Structured LLM Extracting...</span>
                    </div>
                  </div>
                </>
              )}
            </div>
          )}

          {/* Primary Action Button placed directly beneath preview image for zero scrolling */}
          <div style={{ marginTop: '10px' }}>
            <button
              type="button"
              className="btn btn-primary btn-full"
              onClick={onSubmit}
              disabled={!selectedFile || isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 size={16} className="spinner" />
                  <span>Processing Real-Time Inference...</span>
                </>
              ) : (
                <>
                  <Play size={16} />
                  <span>Verify & Extract {activeTab === 'front' ? 'Front ID' : 'Laser ID'}</span>
                </>
              )}
            </button>
          </div>

          {previewUrl && (
            <div className="preview-rotate-hint" style={{ marginTop: '6px', fontSize: '0.74rem' }}>
              <RotateCw size={11} />
              <span>Rotate if card is sideways or upside-down before verifying.</span>
            </div>
          )}

          <div className="sample-picker" style={{ marginTop: previewUrl ? '10px' : '14px' }}>
            <div className="sample-label">Or quickly try with synthetic test cards:</div>
            <div className="sample-buttons">
              <button
                type="button"
                className="btn btn-subtle btn-sm"
                onClick={loadSample}
                disabled={isLoading}
              >
                <Sparkles size={13} />
                <span>Load Synthetic {activeTab === 'front' ? 'Thai ID' : 'Laser ID'}</span>
              </button>
              <button
                type="button"
                className="btn btn-subtle btn-sm"
                onClick={() => setIsCameraOpen(true)}
                disabled={isLoading}
              >
                <Camera size={13} color="#C41230" />
                <span>Open Camera</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Camera Capture Modal with Card Viewfinder Overlay */}
      <CameraCaptureModal
        isOpen={isCameraOpen}
        onClose={() => setIsCameraOpen(false)}
        onCapture={(file) => {
          onFileSelect(file);
        }}
        cardType={activeTab}
      />
    </>
  );
}
