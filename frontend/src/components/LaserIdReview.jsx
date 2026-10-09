import React, { useState } from 'react';
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Clock,
  Code,
  Copy,
  Info,
  QrCode,
  ShieldAlert,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import ConfidenceBadge from './ConfidenceBadge';

export default function LaserIdReview({
  data,
  processingTimeMs,
}) {
  const [copied, setCopied] = useState(false);
  const [showJson, setShowJson] = useState(false);

  if (!data) return null;

  const {
    raw_laser_id,
    formatted_laser_id,
    is_laser_id_valid_format,
    confidence_summary,
    is_rejected,
    rejection_reason,
  } = data;

  const fieldScores = confidence_summary?.fields || {};
  const laserField = fieldScores.laser_id;
  const threshold = confidence_summary?.confidence_threshold ?? 0.8;
  const isQGRejected = is_rejected || confidence_summary?.is_quality_gate_passed === false;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(formatted_laser_id || raw_laser_id || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Split formatted ID into prefix and number if available
  const cleanId = (formatted_laser_id || raw_laser_id || '').replace(/-/g, '');
  const prefix = cleanId.slice(0, 2);
  const numberPart = cleanId.slice(2);

  return (
    <div className="ui-card review-card-compact">
      <div className="card-header compact-card-header">
        <div className="header-title-row">
          <QrCode size={16} color="#C41230" />
          <h3>Laser ID Verification (รหัสหลังบัตร)</h3>
        </div>
        <div className="header-actions-inline">
          {confidence_summary && (
            <span
              className={`badge badge-compact ${
                isQGRejected
                  ? 'badge-error'
                  : confidence_summary.is_overall_confident
                  ? 'badge-success'
                  : 'badge-warning'
              }`}
              title={`Confidence threshold: ${(threshold * 100).toFixed(0)}% | Quality Gate: 40%`}
            >
              {isQGRejected ? (
                <ShieldAlert size={11} />
              ) : confidence_summary.is_overall_confident ? (
                <CheckCircle2 size={11} />
              ) : (
                <AlertTriangle size={11} />
              )}
              <span>
                {isQGRejected
                  ? `${confidence_summary.overall_confidence_percentage}% (Rejected)`
                  : `${confidence_summary.overall_confidence_percentage}% Conf.`}
              </span>
            </span>
          )}

          {processingTimeMs && (
            <span className="latency-badge compact-latency" title="Pipeline Latency">
              <Clock size={11} /> {processingTimeMs.toFixed(0)} ms
            </span>
          )}

          <button
            type="button"
            className="btn btn-outline btn-xs"
            onClick={() => setShowJson(!showJson)}
            title="Toggle JSON Contract"
          >
            <Code size={11} />
            <span>{showJson ? 'Hide JSON' : 'JSON'}</span>
          </button>

          <button
            type="button"
            className="btn btn-outline btn-xs"
            onClick={copyToClipboard}
            title="Copy Laser ID to clipboard"
          >
            {copied ? <Check size={11} color="#0D8244" /> : <Copy size={11} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      <div className="card-body compact-card-body">
        {/* Quality Gate Rejection Banner (< 40% Confidence) */}
        {isQGRejected && (
          <div className="quality-gate-rejected-banner compact-qg-banner">
            <div className="qg-header">
              <div className="qg-icon-wrapper-small">
                <ShieldAlert size={16} color="#C41230" />
              </div>
              <div className="qg-title-group">
                <span className="qg-title">Quality Gate Rejected ({confidence_summary?.overall_confidence_percentage ?? '—'}% &lt; 40%)</span>
              </div>
              <span className="qg-status-pill">REJECTED</span>
            </div>
            <p className="qg-reason-text compact-text">
              {rejection_reason ||
                confidence_summary?.rejection_reason ||
                'The Laser ID on the card back is unreadable or unrecognized. Please recapture a clear, well-lit image.'}
            </p>
          </div>
        )}

        {/* 1. Laser ID Banner (Single Compact Row) */}
        <div className="id-banner compact-id-banner">
          <div className="id-banner-left">
            <span className="id-banner-tag">Laser Code (12 Chars)</span>
            <span className="id-banner-val laser-code-compact">{formatted_laser_id || raw_laser_id || '—'}</span>
          </div>
          <div className="id-banner-right">
            {is_laser_id_valid_format ? (
              <span className="badge badge-success badge-compact">
                <ShieldCheck size={11} /> DOPA Format Valid
              </span>
            ) : (
              <span className="badge badge-error badge-compact">
                <XCircle size={11} /> Format Invalid
              </span>
            )}
            <ConfidenceBadge fieldConfidence={laserField} compact />
          </div>
        </div>

        {/* 2. Structured Breakdown */}
        <div className="compact-data-row two-cols">
          <div className="field-cell compact-cell">
            <div className="field-cell-header">
              <span className="field-key">ตัวอักษร 2 หลักแรก (Letter Prefix)</span>
            </div>
            <div className="field-val font-mono">{prefix || '—'}</div>
            <div className="field-sub-inline">
              <span>มาตรฐาน DOPA ต้องเป็นตัวพิมพ์ใหญ่ (A-Z)</span>
            </div>
          </div>

          <div className="field-cell compact-cell">
            <div className="field-cell-header">
              <span className="field-key">ตัวเลข 10 หลัก (10-Digit Code)</span>
            </div>
            <div className="field-val font-mono">{numberPart || '—'}</div>
            <div className="field-sub-inline">
              <span>เลขลำดับการออกบัตร 10 หลัก</span>
            </div>
          </div>
        </div>

        {/* 3. Subtle Verification Context Note */}
        <div className="compact-note-banner">
          <Info size={13} color="#C41230" />
          <span>
            รหัส Laser ID หลังบัตรถูกตรวจสอบโครงสร้าง 12 หลัก (Letter Prefix 2 ตัว + ตัวเลข 10 ตัว) ตามระเบียบกรมการปกครอง (DOPA)
          </span>
        </div>

        {/* Collapsible JSON Viewer */}
        {showJson && (
          <div className="json-container-compact fade-in">
            <pre className="json-viewer-compact">{JSON.stringify(data, null, 2)}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
