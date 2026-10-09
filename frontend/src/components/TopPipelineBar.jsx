import React, { useState, useMemo } from 'react';
import {
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Circle,
  Clock,
  Eye,
  FileCheck2,
  Loader2,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Timer,
  XCircle,
} from 'lucide-react';

export const DEFAULT_STAGES = [
  { key: 'image_validation', label: '1. Ingest', fullLabel: 'Image Validation', Icon: FileCheck2 },
  { key: 'ocr', label: '2. Azure OCR', fullLabel: 'Azure Document Intelligence OCR', Icon: Eye },
  { key: 'kie', label: '3. LLM KIE', fullLabel: 'LLM Key Information Extraction', Icon: Brain },
  { key: 'validation', label: '4. Checksum', fullLabel: 'Domain & Checksum Validation', Icon: ShieldCheck },
  { key: 'grounding', label: '5. Grounding', fullLabel: 'OCR Grounding & Quality Gate', Icon: Sparkles },
];

export default function TopPipelineBar({
  stages = [],
  timingsMs = {},
  isLoading = false,
  elapsedMs = 0,
  overallTimeMs = null,
  error = null,
  isRejected = false,
  rejectionReason = null,
}) {
  const [showDetails, setShowDetails] = useState(false);

  // Determine stage states during loading vs completed
  const displayStages = useMemo(() => {
    if (stages && stages.length > 0 && !isLoading) {
      return DEFAULT_STAGES.map((def) => {
        const found = stages.find((s) => s.key === def.key);
        const ms = found?.ms ?? timingsMs[def.key] ?? null;
        const status = found?.status || 'done';
        return {
          ...def,
          status,
          ms: typeof ms === 'number' ? ms : null,
        };
      });
    }

    if (isLoading) {
      return DEFAULT_STAGES.map((def, idx) => {
        if (elapsedMs < 250) {
          return { ...def, status: idx === 0 ? 'running' : 'pending', ms: null };
        } else if (elapsedMs < 1000) {
          return { ...def, status: idx === 0 ? 'done' : idx === 1 ? 'running' : 'pending', ms: idx === 0 ? 45 : null };
        } else if (elapsedMs < 2000) {
          return { ...def, status: idx < 2 ? 'done' : idx === 2 ? 'running' : 'pending', ms: idx === 0 ? 45 : idx === 1 ? 680 : null };
        } else {
          return { ...def, status: idx < 4 ? 'done' : 'running', ms: idx === 0 ? 45 : idx === 1 ? 680 : idx === 2 ? 890 : 5 };
        }
      });
    }

    return [];
  }, [stages, timingsMs, isLoading, elapsedMs]);

  if (!isLoading && !overallTimeMs && !error) {
    return null;
  }

  const totalMs = overallTimeMs || timingsMs?.total || 1;

  // Proportional distribution segments
  const stageColors = {
    image_validation: '#64748B',
    ocr: '#0284C7',
    kie: '#6366F1',
    validation: '#10B981',
    grounding: '#F59E0B',
  };

  const distSegments = displayStages
    .filter((s) => s.ms && s.ms > 0)
    .map((s) => ({
      key: s.key,
      label: s.label,
      ms: s.ms,
      color: stageColors[s.key] || '#94A3B8',
      widthPct: Math.max(5, Math.round((s.ms / totalMs) * 100)),
      pct: Math.round((s.ms / totalMs) * 100),
    }));

  return (
    <div className="top-pipeline-bar-container fade-in">
      <div className="top-pipeline-bar">
        {/* Left Side: Status & Stepper */}
        <div className="top-bar-left">
          {isLoading ? (
            <div className="top-bar-running-badge">
              <Loader2 size={13} className="spin" color="#0284C7" />
              <span>Processing Pipeline</span>
            </div>
          ) : error ? (
            <div className="top-bar-error-badge">
              <XCircle size={13} />
              <span>Inference Failed</span>
            </div>
          ) : isRejected ? (
            <div className="top-bar-rejected-badge" title={rejectionReason || 'Overall confidence < 40%'}>
              <ShieldAlert size={13} color="#C41230" />
              <span>Quality Gate Rejected (&lt; 40%)</span>
            </div>
          ) : (
            <div className="top-bar-completed-badge">
              <CheckCircle2 size={13} color="#0D8244" />
              <span>Pipeline Completed</span>
            </div>
          )}

          {/* Horizontal Step Pills */}
          <div className="top-stepper-row">
            {displayStages.map((s, idx) => {
              const isDone = s.status === 'done';
              const isRunning = s.status === 'running';
              const isFailed = s.status === 'failed';
              return (
                <div
                  key={s.key}
                  className={`top-step-pill ${s.status}`}
                  title={`${s.fullLabel}${s.ms !== null ? `: ${s.ms.toFixed(1)} ms` : ''}`}
                >
                  <span className="top-step-icon">
                    {isDone ? (
                      <CheckCircle2 size={12} color="#0D8244" />
                    ) : isFailed ? (
                      <XCircle size={12} color="#C41230" />
                    ) : isRunning ? (
                      <Loader2 size={12} className="spin" color="#0284C7" />
                    ) : (
                      <Circle size={10} color="#94A3B8" />
                    )}
                  </span>
                  <span className="top-step-name">{s.label}</span>
                  {s.ms !== null && (
                    <span className="top-step-ms">{s.ms.toFixed(0)}ms</span>
                  )}
                  {idx < displayStages.length - 1 && (
                    <span className="top-step-arrow">→</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Side: Total Timer & Details Toggle */}
        <div className="top-bar-right">
          <div className="top-bar-time-pill" title="Pipeline execution latency">
            {isLoading ? (
              <>
                <Timer size={13} color="#0284C7" />
                <span>{(elapsedMs / 1000).toFixed(1)} s</span>
              </>
            ) : (
              <>
                <Clock size={13} color="#475569" />
                <span>{overallTimeMs ? `${overallTimeMs.toFixed(0)} ms (${(overallTimeMs / 1000).toFixed(2)}s)` : '—'}</span>
              </>
            )}
          </div>

          {!isLoading && displayStages.length > 0 && (
            <button
              type="button"
              className="top-bar-toggle-btn"
              onClick={() => setShowDetails(!showDetails)}
              aria-label="Toggle latency details"
            >
              <span>Timings</span>
              {showDetails ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>
          )}
        </div>
      </div>

      {/* Expandable Mini Latency Distribution Tray */}
      {showDetails && !isLoading && (
        <div className="top-pipeline-tray fade-in">
          {/* Mini Proportional Bar */}
          <div className="mini-dist-bar">
            {distSegments.map((seg) => (
              <div
                key={seg.key}
                className="mini-dist-seg"
                style={{ width: `${seg.widthPct}%`, backgroundColor: seg.color }}
                title={`${seg.label}: ${seg.ms.toFixed(1)} ms (${seg.pct}%)`}
              />
            ))}
          </div>

          {/* Quick Metrics Strip */}
          <div className="tray-metrics-strip">
            {displayStages.map((st) => (
              <div key={st.key} className="tray-metric-item">
                <span className="tray-dot" style={{ backgroundColor: stageColors[st.key] }} />
                <span className="tray-metric-name">{st.label}</span>
                <span className="tray-metric-val">{st.ms !== null ? `${st.ms.toFixed(1)} ms` : '—'}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
