import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Info,
} from 'lucide-react';

export default function ConfidenceBadge({
  fieldConfidence,
  confidence = null,
  isConfident = null,
  rawText = null,
  normalizedValue = null,
  issues = [],
  compact = false,
}) {
  const [showEvidence, setShowEvidence] = useState(false);

  // If a full FieldConfidence object was provided, extract its fields
  const score = fieldConfidence ? fieldConfidence.confidence : confidence;
  const confident = fieldConfidence ? fieldConfidence.is_confident : isConfident;
  const raw = fieldConfidence ? fieldConfidence.raw_text : rawText;
  const norm = fieldConfidence ? fieldConfidence.normalized_value : normalizedValue;
  const fieldIssues = fieldConfidence ? (fieldConfidence.issues || []) : issues;

  if (score === null || score === undefined) return null;

  const pct = (score * 100).toFixed(0);

  // Status badge config: only green when confident; amber/warning when review needed. NO RED unless failed!
  const isHigh = confident ?? (score >= 0.8);
  const badgeCls = isHigh ? 'badge-success' : 'badge-warning';
  const Icon = isHigh ? CheckCircle2 : AlertTriangle;

  return (
    <div className="confidence-wrapper">
      <div className="confidence-badges-row">
        {/* Clean Confidence Percentage Badge (NO 'In Source' label) */}
        <span
          className={`badge ${badgeCls} ${compact ? 'badge-compact' : ''}`}
          title={`Grounding Confidence Score: ${(score * 100).toFixed(1)}%`}
        >
          <Icon size={12} />
          <span>{pct}%{isHigh ? '' : ' Review'}</span>
        </span>

        {/* Subtle Evidence Toggle Button if raw text or normalization notes exist */}
        {(raw || fieldIssues.length > 0) && (
          <button
            type="button"
            className="evidence-toggle-btn"
            onClick={(e) => {
              e.stopPropagation();
              setShowEvidence(!showEvidence);
            }}
            title="Inspect raw OCR text vs normalized value"
          >
            <Info size={11} />
            <span>Raw</span>
            {showEvidence ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
          </button>
        )}
      </div>

      {/* Expanded Grounding Evidence Card */}
      {showEvidence && (
        <div className="evidence-panel fade-in">
          <div className="evidence-panel-inner">
            {raw && (
              <div className="evidence-line">
                <span className="evidence-key">Raw OCR:</span>
                <span className="evidence-val-raw">"{raw}"</span>
              </div>
            )}
            {norm && norm !== raw && (
              <div className="evidence-line">
                <span className="evidence-key">Normalized:</span>
                <span className="evidence-val-norm">"{norm}"</span>
              </div>
            )}
            {fieldIssues.length > 0 && (
              <div className="evidence-issues">
                {fieldIssues.map((iss, i) => (
                  <span key={i} className="issue-pill">
                    {iss}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
