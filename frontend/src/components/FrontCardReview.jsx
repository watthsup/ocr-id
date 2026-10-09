import React, { useState } from 'react';
import {
  AlertTriangle,
  Calendar,
  Check,
  CheckCircle2,
  Clock,
  Code,
  Copy,
  FileCheck2,
  MapPin,
  ShieldAlert,
  ShieldCheck,
  User,
  XCircle,
} from 'lucide-react';
import ConfidenceBadge from './ConfidenceBadge';

const THAI_MONTH_NAMES = [
  '',
  'ม.ค.',
  'ก.พ.',
  'มี.ค.',
  'เม.ย.',
  'พ.ค.',
  'มิ.ย.',
  'ก.ค.',
  'ส.ค.',
  'ก.ย.',
  'ต.ค.',
  'พ.ย.',
  'ธ.ค.',
];

/**
 * Derives clean normalized date representations from normalized attributes
 * (iso_date, normalized_value, day, month, year_be, year_ce), NEVER reading raw OCR text.
 */
function getNormalizedDateDisplay(dateField, fieldConfidence) {
  if (!dateField && !fieldConfidence) {
    return { primary: '—', isoDate: null, isLifetime: false, yearCe: null, yearBe: null };
  }

  // 1. Lifetime Expiry Check
  if (dateField?.is_lifetime || fieldConfidence?.normalized_value?.includes('ตลอดชีพ')) {
    return {
      primary: 'ตลอดชีพ (Lifetime)',
      isoDate: null,
      isLifetime: true,
      yearCe: null,
      yearBe: null,
    };
  }

  // 2. Normalized ISO Date (YYYY-MM-DD)
  const isoDate = dateField?.iso_date || fieldConfidence?.normalized_value || null;

  // 3. Normalized Date components (day, month, year_be, year_ce)
  let day = dateField?.day;
  let month = dateField?.month;
  let yearBe = dateField?.year_be;
  let yearCe = dateField?.year_ce;

  // If numeric components are missing, derive them from normalized isoDate
  if ((!day || !month || !yearBe) && isoDate && /^\d{4}-\d{2}-\d{2}$/.test(isoDate)) {
    const parts = isoDate.split('-').map(Number);
    yearCe = parts[0];
    month = parts[1];
    day = parts[2];
    yearBe = yearCe + 543;
  }

  // 4. Construct normalized Thai formatted date (e.g. "15 ม.ค. 2533")
  let normalizedTh = null;
  if (day && month && yearBe) {
    const mName = THAI_MONTH_NAMES[month] || `${month}`;
    normalizedTh = `${day} ${mName} ${yearBe}`;
  } else if (isoDate) {
    normalizedTh = isoDate;
  }

  return {
    primary: normalizedTh || isoDate || '—',
    isoDate: isoDate || '—',
    yearBe: yearBe,
    yearCe: yearCe,
    isLifetime: false,
  };
}

export default function FrontCardReview({
  data,
  processingTimeMs,
}) {
  const [copied, setCopied] = useState(false);
  const [showJson, setShowJson] = useState(false);

  if (!data) return null;

  // Format 13-digit Thai ID as X-XXXX-XXXXX-XX-X
  const formatThaiId = (idStr) => {
    if (!idStr || idStr.length !== 13) return idStr || '—';
    return `${idStr.slice(0, 1)}-${idStr.slice(1, 5)}-${idStr.slice(5, 10)}-${idStr.slice(10, 12)}-${idStr.slice(12)}`;
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const {
    identification_number,
    is_id_checksum_valid,
    thai_name,
    english_name,
    date_of_birth,
    religion,
    address,
    date_of_issue,
    date_of_expiry,
    confidence_summary,
    is_rejected,
    rejection_reason,
  } = data;

  const fieldScores = confidence_summary?.fields || {};
  const threshold = confidence_summary?.confidence_threshold ?? 0.8;
  const reviewFields = confidence_summary?.fields_needing_review || [];
  const isQGRejected = is_rejected || confidence_summary?.is_quality_gate_passed === false;

  // Compute normalized date representations strictly from normalized fields
  const dobNorm = getNormalizedDateDisplay(date_of_birth, fieldScores.date_of_birth);
  const doiNorm = getNormalizedDateDisplay(date_of_issue, fieldScores.date_of_issue);
  const doeNorm = getNormalizedDateDisplay(date_of_expiry, fieldScores.date_of_expiry);

  return (
    <div className="ui-card review-card-compact">
      <div className="card-header compact-card-header">
        <div className="header-title-row">
          <FileCheck2 size={16} color="#C41230" />
          <h3>Extraction & Verification Result</h3>
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
            title="Copy structured JSON to clipboard"
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
                'Image quality is too low for reliable OCR. Please recapture a clear, well-lit image.'}
            </p>
          </div>
        )}

        {/* Review Alert Banner only when low confidence or failed checksum */}
        {!isQGRejected && reviewFields.length > 0 && (
          <div className="review-alert-banner compact-alert">
            <AlertTriangle size={13} />
            <span>
              <strong>Review Required:</strong>{' '}
              {reviewFields.map((f) => (
                <span key={f} className="review-pill-small">{fieldScores[f]?.field_name_en || f}</span>
              ))}
            </span>
          </div>
        )}

        {/* 1. National ID Banner (Single Compact Row) */}
        <div className="id-banner compact-id-banner">
          <div className="id-banner-left">
            <span className="id-banner-tag">ID No. (เลขประจำตัวประชาชน)</span>
            <span className="id-banner-val">{formatThaiId(identification_number)}</span>
          </div>
          <div className="id-banner-right">
            {is_id_checksum_valid ? (
              <span className="badge badge-success badge-compact">
                <ShieldCheck size={11} /> Mod 11 Valid
              </span>
            ) : (
              <span className="badge badge-error badge-compact">
                <XCircle size={11} /> Checksum Error
              </span>
            )}
            <ConfidenceBadge fieldConfidence={fieldScores.identification_number} compact />
          </div>
        </div>

        {/* 2. Names Section (2 Columns: Thai & English) */}
        <div className="compact-data-row two-cols">
          {/* Thai Name */}
          <div className="field-cell compact-cell">
            <div className="field-cell-header">
              <span className="field-key">ชื่อ-นามสกุล (Thai Name)</span>
              <ConfidenceBadge fieldConfidence={fieldScores.thai_name} compact />
            </div>
            <div className="field-val thai-text primary-name">{thai_name?.full_name || '—'}</div>
            {(thai_name?.title || thai_name?.first_name || thai_name?.last_name) && (
              <div className="field-sub-inline">
                {thai_name?.title && <span>คำนำหน้า: {thai_name.title}</span>}
                {thai_name?.first_name && <span>ชื่อ: {thai_name.first_name}</span>}
                {thai_name?.middle_name && <span>กลาง: {thai_name.middle_name}</span>}
                {thai_name?.last_name && <span>สกุล: {thai_name.last_name}</span>}
              </div>
            )}
          </div>

          {/* English Name */}
          <div className="field-cell compact-cell">
            <div className="field-cell-header">
              <span className="field-key">English Name</span>
              <ConfidenceBadge fieldConfidence={fieldScores.english_name} compact />
            </div>
            <div className="field-val primary-name">{english_name?.full_name || '—'}</div>
            {(english_name?.title || english_name?.first_name || english_name?.last_name) && (
              <div className="field-sub-inline">
                {english_name?.title && <span>Title: {english_name.title}</span>}
                {english_name?.first_name && <span>First: {english_name.first_name}</span>}
                {english_name?.middle_name && <span>Mid: {english_name.middle_name}</span>}
                {english_name?.last_name && <span>Last: {english_name.last_name}</span>}
              </div>
            )}
          </div>
        </div>

        {/* 3. Dates & Demographics (Single 4-Column Grid: DOB | Issue | Expiry | Religion) */}
        <div className="compact-data-row four-cols">
          {/* Date of Birth */}
          <div className="field-cell compact-cell">
            <div className="field-cell-header">
              <span className="field-key">วันเกิด (DOB)</span>
              <ConfidenceBadge fieldConfidence={fieldScores.date_of_birth} compact />
            </div>
            <div className="field-val thai-text">{dobNorm.primary}</div>
            <div className="field-sub-inline">
              {dobNorm.isoDate && dobNorm.isoDate !== '—' && (
                <span>ISO: {dobNorm.isoDate}</span>
              )}
              {dobNorm.yearCe && <span>CE: {dobNorm.yearCe}</span>}
            </div>
          </div>

          {/* Date of Issue */}
          <div className="field-cell compact-cell">
            <div className="field-cell-header">
              <span className="field-key">วันออกบัตร (Issue)</span>
              <ConfidenceBadge fieldConfidence={fieldScores.date_of_issue} compact />
            </div>
            <div className="field-val thai-text">{doiNorm.primary}</div>
            <div className="field-sub-inline">
              {doiNorm.isoDate && doiNorm.isoDate !== '—' && (
                <span>ISO: {doiNorm.isoDate}</span>
              )}
              {doiNorm.yearCe && <span>CE: {doiNorm.yearCe}</span>}
            </div>
          </div>

          {/* Date of Expiry */}
          <div className="field-cell compact-cell">
            <div className="field-cell-header">
              <span className="field-key">วันหมดอายุ (Expiry)</span>
              <ConfidenceBadge fieldConfidence={fieldScores.date_of_expiry} compact />
            </div>
            {doeNorm.isLifetime ? (
              <div className="field-val thai-text lifetime-pill">ตลอดชีพ (Lifetime)</div>
            ) : (
              <>
                <div className="field-val thai-text">{doeNorm.primary}</div>
                <div className="field-sub-inline">
                  {doeNorm.isoDate && doeNorm.isoDate !== '—' && (
                    <span>ISO: {doeNorm.isoDate}</span>
                  )}
                  {doeNorm.yearCe && <span>CE: {doeNorm.yearCe}</span>}
                </div>
              </>
            )}
          </div>

          {/* Religion */}
          <div className="field-cell compact-cell">
            <div className="field-cell-header">
              <span className="field-key">ศาสนา (Religion)</span>
              <ConfidenceBadge fieldConfidence={fieldScores.religion} compact />
            </div>
            <div className="field-val thai-text">{religion || '—'}</div>
            <div className="field-sub-inline">
              <span>สัญชาติไทย (Thai)</span>
            </div>
          </div>
        </div>

        {/* 4. Registered Address (Full Text + Structured Mini-Chips) */}
        <div className="field-cell compact-cell address-cell-compact">
          <div className="field-cell-header">
            <div className="address-label-row">
              <MapPin size={12} color="#C41230" />
              <span className="field-key">ที่อยู่ตามทะเบียนราษฎร (Registered Address)</span>
            </div>
            <ConfidenceBadge fieldConfidence={fieldScores.address} compact />
          </div>

          <div className="address-full-line thai-text">
            {address?.raw_address || '—'}
          </div>

          <div className="address-mini-chips">
            {address?.house_no && <span className="mini-chip">เลขที่ {address.house_no}</span>}
            {address?.moo && <span className="mini-chip">หมู่ {address.moo}</span>}
            {address?.trok_soi && <span className="mini-chip">ซอย {address.trok_soi}</span>}
            {address?.road && <span className="mini-chip">ถ.{address.road}</span>}
            {address?.sub_district && <span className="mini-chip">ต./แขวง {address.sub_district}</span>}
            {address?.district && <span className="mini-chip">อ./เขต {address.district}</span>}
            {address?.province && <span className="mini-chip">จ.{address.province}</span>}
            {address?.postal_code && <span className="mini-chip">{address.postal_code}</span>}
          </div>
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
