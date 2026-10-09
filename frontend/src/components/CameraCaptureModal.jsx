import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  Camera,
  X,
  RotateCcw,
  Check,
  Zap,
  ZapOff,
  FlipHorizontal,
  AlertCircle,
  Sparkles,
  Info,
  Maximize2,
} from 'lucide-react';

export default function CameraCaptureModal({
  isOpen,
  onClose,
  onCapture,
  cardType = 'front', // 'front' | 'laser'
}) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const containerRef = useRef(null);
  const overlayBoxRef = useRef(null);

  const [isLoadingCamera, setIsLoadingCamera] = useState(true);
  const [cameraError, setCameraError] = useState(null);
  const [capturedBlobUrl, setCapturedBlobUrl] = useState(null);
  const [capturedFile, setCapturedFile] = useState(null);
  const [hasTorch, setHasTorch] = useState(false);
  const [isTorchOn, setIsTorchOn] = useState(false);
  const [facingMode, setFacingMode] = useState('environment'); // 'environment' | 'user'
  const [cropToBox, setCropToBox] = useState(true);
  const [isFlashing, setIsFlashing] = useState(false);

  // Stop current video stream
  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // ignore
        }
      });
      streamRef.current = null;
    }
  }, []);

  // Initialize camera
  const startCamera = useCallback(async () => {
    setIsLoadingCamera(true);
    setCameraError(null);
    stopStream();

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error(
          'Camera API is not supported in this browser or environment. Please ensure HTTPS or localhost is used.'
        );
      }

      // First try preferred facing mode and high resolution
      let constraints = {
        video: {
          facingMode: { ideal: facingMode },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      };

      let stream;
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (err) {
        console.warn('Initial camera constraints failed, attempting fallback:', err);
        // Fallback to basic video constraint
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      // Check if torch/flashlight is supported
      const track = stream.getVideoTracks()[0];
      if (track) {
        const capabilities = track.getCapabilities ? track.getCapabilities() : {};
        if (capabilities.torch) {
          setHasTorch(true);
        } else {
          setHasTorch(false);
        }
      }

      setIsLoadingCamera(false);
    } catch (err) {
      console.error('Camera initialization error:', err);
      setIsLoadingCamera(false);
      setCameraError(
        err.message ||
          'Unable to access camera. Please check device permissions and ensure your browser has camera access.'
      );
    }
  }, [facingMode, stopStream]);

  // Manage camera lifecycle based on modal open state
  useEffect(() => {
    if (isOpen) {
      setCapturedBlobUrl(null);
      setCapturedFile(null);
      setIsTorchOn(false);
      startCamera();
    } else {
      stopStream();
      if (capturedBlobUrl) {
        URL.revokeObjectURL(capturedBlobUrl);
      }
    }

    return () => {
      stopStream();
      if (capturedBlobUrl) {
        URL.revokeObjectURL(capturedBlobUrl);
      }
    };
  }, [isOpen, startCamera, stopStream]);

  // Toggle Torch
  const toggleTorch = async () => {
    if (!streamRef.current) return;
    const track = streamRef.current.getVideoTracks()[0];
    if (track && track.applyConstraints) {
      try {
        const nextState = !isTorchOn;
        await track.applyConstraints({
          advanced: [{ torch: nextState }],
        });
        setIsTorchOn(nextState);
      } catch (err) {
        console.warn('Could not toggle torch:', err);
      }
    }
  };

  // Flip Camera (Front / Rear)
  const flipCamera = () => {
    setFacingMode((prev) => (prev === 'environment' ? 'user' : 'environment'));
  };

  // Capture image from video
  const handleShutter = () => {
    const video = videoRef.current;
    if (!video || !streamRef.current) return;

    // Trigger visual shutter flash
    setIsFlashing(true);
    setTimeout(() => setIsFlashing(false), 200);

    const videoWidth = video.videoWidth;
    const videoHeight = video.videoHeight;

    if (!videoWidth || !videoHeight) return;

    const canvas = document.createElement('canvas');

    if (!cropToBox || !overlayBoxRef.current || !containerRef.current) {
      // Full frame capture
      canvas.width = videoWidth;
      canvas.height = videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, videoWidth, videoHeight);
    } else {
      // Calculate overlay box coordinates relative to displayed video
      const containerRect = containerRef.current.getBoundingClientRect();
      const boxRect = overlayBoxRef.current.getBoundingClientRect();

      // Relative position of the box inside container (0 to 1)
      const relLeft = (boxRect.left - containerRect.left) / containerRect.width;
      const relTop = (boxRect.top - containerRect.top) / containerRect.height;
      const relWidth = boxRect.width / containerRect.width;
      const relHeight = boxRect.height / containerRect.height;

      // Handle object-fit: cover scaling
      const videoRatio = videoWidth / videoHeight;
      const containerRatio = containerRect.width / containerRect.height;

      let renderWidth, renderHeight, offsetX, offsetY;

      if (containerRatio > videoRatio) {
        // Container is wider than video
        renderWidth = containerRect.width;
        renderHeight = containerRect.width / videoRatio;
        offsetX = 0;
        offsetY = (containerRect.height - renderHeight) / 2;
      } else {
        // Container is taller than video
        renderHeight = containerRect.height;
        renderWidth = containerRect.height * videoRatio;
        offsetY = 0;
        offsetX = (containerRect.width - renderWidth) / 2;
      }

      // Convert box coords from container space to video pixel space
      const boxPixelX = ((boxRect.left - containerRect.left - offsetX) / renderWidth) * videoWidth;
      const boxPixelY = ((boxRect.top - containerRect.top - offsetY) / renderHeight) * videoHeight;
      const boxPixelW = (boxRect.width / renderWidth) * videoWidth;
      const boxPixelH = (boxRect.height / renderHeight) * videoHeight;

      // Add 4% padding margin so card borders and text near edges are safely included
      const padX = boxPixelW * 0.04;
      const padY = boxPixelH * 0.04;

      const cropX = Math.max(0, boxPixelX - padX);
      const cropY = Math.max(0, boxPixelY - padY);
      const cropW = Math.min(videoWidth - cropX, boxPixelW + padX * 2);
      const cropH = Math.min(videoHeight - cropY, boxPixelH + padY * 2);

      canvas.width = Math.round(cropW);
      canvas.height = Math.round(cropH);

      const ctx = canvas.getContext('2d');
      ctx.drawImage(
        video,
        cropX,
        cropY,
        cropW,
        cropH,
        0,
        0,
        canvas.width,
        canvas.height
      );
    }

    // Convert to JPEG file
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        const filename =
          cardType === 'front'
            ? `thai_id_front_scan_${Date.now()}.jpg`
            : `thai_id_laser_scan_${Date.now()}.jpg`;
        const file = new File([blob], filename, { type: 'image/jpeg' });
        const url = URL.createObjectURL(blob);

        setCapturedFile(file);
        setCapturedBlobUrl(url);

        // Pause live camera while reviewing snapshot
        if (videoRef.current) {
          videoRef.current.pause();
        }
      },
      'image/jpeg',
      0.95
    );
  };

  // Retake photo: discard snapshot and resume live camera
  const handleRetake = () => {
    if (capturedBlobUrl) {
      URL.revokeObjectURL(capturedBlobUrl);
    }
    setCapturedBlobUrl(null);
    setCapturedFile(null);
    if (videoRef.current) {
      videoRef.current.play().catch(() => {});
    }
  };

  // Confirm photo: pass File to parent and close modal
  const handleConfirm = () => {
    if (capturedFile) {
      onCapture(capturedFile);
      onClose();
    }
  };

  if (!isOpen) return null;

  const isFront = cardType === 'front';

  return (
    <div className="camera-modal-backdrop" onClick={onClose}>
      <div
        className="camera-modal-container"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Shutter Visual Flash Feedback */}
        {isFlashing && <div className="camera-shutter-flash" />}

        {/* Modal Top Header */}
        <div className="camera-modal-header">
          <div className="camera-modal-title">
            <Camera size={18} color="#C41230" />
            <span>
              {isFront
                ? 'Camera Scanner: Front ID Card'
                : 'Camera Scanner: Laser ID (Card Back)'}
            </span>
          </div>

          <div className="camera-header-controls">
            {hasTorch && !capturedBlobUrl && (
              <button
                type="button"
                className={`camera-icon-btn ${isTorchOn ? 'active' : ''}`}
                onClick={toggleTorch}
                title={isTorchOn ? 'Turn Flashlight Off' : 'Turn Flashlight On'}
              >
                {isTorchOn ? <Zap size={16} /> : <ZapOff size={16} />}
              </button>
            )}

            {!capturedBlobUrl && (
              <button
                type="button"
                className="camera-icon-btn"
                onClick={flipCamera}
                title="Flip Camera (Front / Rear)"
              >
                <FlipHorizontal size={16} />
              </button>
            )}

            <button
              type="button"
              className="camera-icon-btn"
              onClick={onClose}
              title="Close Camera"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Camera Viewport Body */}
        <div className="camera-viewport-body" ref={containerRef}>
          {isLoadingCamera && !capturedBlobUrl && (
            <div className="camera-state-overlay">
              <div className="spinner-large" />
              <p>Initializing camera video stream...</p>
            </div>
          )}

          {cameraError && !capturedBlobUrl && (
            <div className="camera-state-overlay error">
              <AlertCircle size={36} color="#C41230" />
              <h4>Camera Access Error</h4>
              <p>{cameraError}</p>
              <div style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={startCamera}
                >
                  <RotateCcw size={14} /> Try Again
                </button>
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  onClick={onClose}
                >
                  Upload File Instead
                </button>
              </div>
            </div>
          )}

          {/* Live Video Feed */}
          <video
            ref={videoRef}
            className={`camera-video-feed ${capturedBlobUrl ? 'hidden' : ''}`}
            playsInline
            autoPlay
            muted
          />

          {/* Captured Review Preview Image */}
          {capturedBlobUrl && (
            <div className="camera-captured-preview">
              <img
                src={capturedBlobUrl}
                alt="Captured Card Preview"
                className="camera-preview-img"
              />
              <div className="captured-badge-overlay">
                <Check size={14} />
                <span>Captured Preview Ready</span>
              </div>
            </div>
          )}

          {/* Card Overlay Box (Viewfinder) - shown only during live capture */}
          {!capturedBlobUrl && !cameraError && (
            <div className="card-viewfinder-overlay">
              {/* Center Cutout Guide Box with ID-1 standard ratio ~1.586 */}
              <div
                className="card-overlay-box"
                ref={overlayBoxRef}
                data-card-type={cardType}
              >
                {/* 4 Corner Markers */}
                <span className="corner-bracket top-left" />
                <span className="corner-bracket top-right" />
                <span className="corner-bracket bottom-left" />
                <span className="corner-bracket bottom-right" />

                {/* Subtle Moving Laser Scanning Beam */}
                <div className="viewfinder-scan-beam" />

                {/* In-Frame Context Hints */}
                <div className="card-box-header-tag">
                  {isFront ? 'บัตรประชาชน (Front of Card)' : 'Laser ID หลังบัตร (Card Back)'}
                </div>

                {isFront ? (
                  <div className="card-silhouette-guides">
                    <div className="guide-garuda" title="Garuda Emblem Position">
                      <span>ตราครุฑ</span>
                    </div>
                    <div className="guide-chip" title="Smart Card Chip Position">
                      <span>CHIP</span>
                    </div>
                    <div className="guide-photo" title="Cardholder Photo Position">
                      <span>รูปถ่าย</span>
                    </div>
                  </div>
                ) : (
                  <div className="card-silhouette-guides laser">
                    <div className="guide-laser-field" title="Laser ID code area">
                      <span>JT0-XXXXXXX-XX</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Viewfinder Instructions Beneath Box */}
              <div className="viewfinder-instruction-banner">
                <Info size={14} />
                <span>
                  Align card edges with the red corner brackets • Ensure clear lighting and avoid glare
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Modal Bottom Controls Bar */}
        <div className="camera-modal-footer">
          {capturedBlobUrl ? (
            /* Review & Confirm Controls */
            <div className="camera-review-actions">
              <button
                type="button"
                className="btn btn-outline"
                onClick={handleRetake}
              >
                <RotateCcw size={16} />
                <span>Retake Photo</span>
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleConfirm}
              >
                <Check size={16} />
                <span>Use This Photo</span>
              </button>
            </div>
          ) : (
            /* Active Live Capture Controls */
            <div className="camera-capture-controls">
              <label className="crop-toggle-label" title="Crop exactly to the card frame">
                <input
                  type="checkbox"
                  checked={cropToBox}
                  onChange={(e) => setCropToBox(e.target.checked)}
                />
                <span>Crop to Card Box (Recommended for OCR)</span>
              </label>

              {/* Large Shutter Button */}
              <button
                type="button"
                className="camera-shutter-btn"
                onClick={handleShutter}
                disabled={isLoadingCamera || !!cameraError}
                title="Capture ID Card Photo"
              >
                <div className="shutter-inner-circle">
                  <Camera size={26} color="#FFFFFF" />
                </div>
              </button>

              <div className="shutter-spacer" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
