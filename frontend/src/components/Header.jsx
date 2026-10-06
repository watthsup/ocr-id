import React, { useEffect, useState } from 'react';
import { ShieldCheck, Server, AlertCircle, RefreshCw } from 'lucide-react';

export default function Header({ activeTab, onTabChange }) {
  const [healthStatus, setHealthStatus] = useState('checking'); // 'checking' | 'online' | 'offline'

  const checkHealth = async () => {
    try {
      const res = await fetch('/health', { method: 'GET' });
      if (res.ok) {
        setHealthStatus('online');
      } else {
        setHealthStatus('offline');
      }
    } catch {
      setHealthStatus('offline');
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 20000);
    return () => clearInterval(interval);
  }, []);

  return (
    <>
      <div className="top-ribbon" />
      <header className="site-header">
        <div className="header-inner">
          <div className="brand-section">
            <div className="brand-logo-badge" title="Generali ID Intelligence">
              G
            </div>
            <div className="brand-info">
              <h1>GenWings OCR Demo</h1>
              <div className="brand-subtitle">
                <ShieldCheck size={14} color="#C41230" />
                <span>Thai National ID & Laser OCR Engine</span>
              </div>
            </div>
          </div>

          <div className="header-actions">
            <div
              className={`health-pill ${healthStatus === 'online'
                ? 'online'
                : healthStatus === 'offline'
                  ? 'offline'
                  : ''
                }`}
              title={
                healthStatus === 'online'
                  ? 'FastAPI OCR & KIE Backend Online'
                  : 'Backend Disconnected'
              }
            >
              <span className="status-dot" />
              <span>
                {healthStatus === 'online'
                  ? 'API Online (8000)'
                  : healthStatus === 'offline'
                    ? 'API Offline'
                    : 'Connecting...'}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="app-container">
        <div className="hero-controls">
          <div className="hero-title-row">
            <div>
              <h2>ID Card Extraction & Review</h2>
              <p className="hero-description">
                Synchronous OCR + LLM Key Information Extraction with Thai ID Checksum & DOPA Format Validation
              </p>
            </div>

            <div className="tab-group" role="tablist">
              <button
                type="button"
                className={`tab-button ${activeTab === 'front' ? 'active' : ''}`}
                onClick={() => onTabChange('front')}
              >
                Front ID Card (หน้าบัตร)
              </button>
              <button
                type="button"
                className={`tab-button ${activeTab === 'laser' ? 'active' : ''}`}
                onClick={() => onTabChange('laser')}
              >
                Laser ID (หลังบัตร)
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
