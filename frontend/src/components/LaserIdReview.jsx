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
  } = data;

  const fieldScores = confidence_summary?.fields || {};
  const laserField = fieldScores.laser_id;
  const threshold = confidence_summary?.confidence_threshold ?? 0.8;

  const copyToClipboard = () => {
    navigator.clipboard.writeText(formatted_laser_id || raw_laser_id || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="ui-card">
      <div className="card-header">
        <h3>
          <QrCode size={18} color="#1E293B" />
          <span>Laser ID Verification Result (รหัสหลังบัตร)</span>
        </h3>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {confidence_summary && (
            <span
              className={`badge ${confidence_summary.is_overall_confident ? 'badge-success' : 'badge-warning'}`}
              title={`Confidence threshold: ${(threshold * 100).toFixed(0)}%`}
            >
              {confidence_summary.is_overall_confident ? <CheckCircle2 size={12} /> : <AlertTriangle size={12} />}
              <span>{confidence_summary.overall_confidence_percentage}% Confidence</span>
            </span>
          )}

          {processingTimeMs && (
            <span className="latency-badge" title="Total Pipeline Latency">
              <Clock size={12} /> {processingTimeMs.toFixed(0)} ms
            </span>
          )}
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={copyToClipboard}
            title="Copy Laser ID to clipboard"
          >
            {copied ? <Check size={14} color="#0D8244" /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      <div className="card-body">
        {/* Laser ID Banner */}
        <div className="id-banner">
          <div>
            <div className="id-label">Laser Code (12 Chars Alphanumeric)</div>
            <div className="laser-code">{formatted_laser_id || raw_laser_id || '—'}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {is_laser_id_valid_format ? (
              <span className="badge badge-success">
                <ShieldCheck size={13} /> DOPA Format Valid
              </span>
            ) : (
              <span className="badge badge-error">
                <XCircle size={13} /> Invalid Format
              </span>
            )}
            {laserField && <ConfidenceBadge fieldConfidence={laserField} />}
          </div>
        </div>

        {/* Breakdown details */}
        <div className="section-block">
          <div className="data-grid-2">
            <div className="field-cell">
              <div className="field-header-row">
                <span className="field-key">Formatted Laser ID</span>
                {laserField && <ConfidenceBadge fieldConfidence={laserField} compact />}
              </div>
              <div className="field-val" style={{ fontFamily: 'var(--font-mono)' }}>
                {formatted_laser_id || '—'}
              </div>
              <div className="field-sub">Standard Pattern: XX0-XXXXXXX-XX</div>
            </div>

            <div className="field-cell">
              <div className="field-key">Raw Extracted String</div>
              <div className="field-val" style={{ fontFamily: 'var(--font-mono)' }}>
                {raw_laser_id || '—'}
              </div>
              <div className="field-sub">Length: {raw_laser_id ? raw_laser_id.length : 0} characters</div>
            </div>
          </div>
        </div>

        {/* Informational Box */}
        <div className="info-box">
          <div className="info-box-title">
            <Info size={16} /> Thai National ID Laser Code Standard
          </div>
          <p>
            The Laser ID printed on the back of Thai National ID cards contains exactly 12 alphanumeric
            characters. The first 2 characters are English uppercase letters (e.g. <code>JT</code>, <code>ME</code>, <code>JC</code>) representing the card batch authority, followed by 10 numeric digits.
          </p>
        </div>

        {/* Toggle JSON */}
        <div className="result-footer">
          <button
            type="button"
            className="btn btn-outline btn-sm"
            onClick={() => setShowJson(!showJson)}
          >
            <Code size={14} />
            <span>{showJson ? 'Hide JSON Contract' : 'View Full JSON Contract'}</span>
          </button>
        </div>

        {showJson && (
          <pre className="json-viewer">{JSON.stringify(data, null, 2)}</pre>
        )}
      </div>
    </div>
  );
}
