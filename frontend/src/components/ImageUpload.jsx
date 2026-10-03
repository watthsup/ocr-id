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
} from 'lucide-react';
import { generateSampleFrontCard, generateSampleLaserCard } from '../utils/sampleImages';
import { rotateImageFile } from '../utils/imageUtils';

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
    <div className="ui-card">
      <div className="card-header">
        <h3>
          <ImageIcon size={18} color="#C41230" />
          <span>{activeTab === 'front' ? 'Front ID Card Image' : 'Back Card Image (Laser ID)'}</span>
        </h3>
        {selectedFile && (
          <div className="header-action-group">
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
          </div>
        )}
      </div>

      <div className="card-body">
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

        {previewUrl && (
          <div className="preview-rotate-hint">
            <RotateCw size={12} />
            <span>If card photo is sideways or upside-down, click Rotate to orient it upright before verifying.</span>
          </div>
        )}

        <div className="sample-picker">
          <div className="sample-label">Or quickly try with synthetic test cards:</div>
          <div className="sample-buttons">
            <button
              type="button"
              className="btn btn-subtle btn-sm"
              onClick={loadSample}
              disabled={isLoading}
            >
              <Sparkles size={14} />
              <span>Load Synthetic {activeTab === 'front' ? 'Thai ID' : 'Laser ID'}</span>
            </button>
          </div>
        </div>

        <div style={{ marginTop: '20px' }}>
          <button
            type="button"
            className="btn btn-primary btn-full"
            onClick={onSubmit}
            disabled={!selectedFile || isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 size={18} className="spinner" />
                <span>Processing Real-Time Inference...</span>
              </>
            ) : (
              <>
                <Play size={18} />
                <span>Verify & Extract {activeTab === 'front' ? 'Front ID' : 'Laser ID'}</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
