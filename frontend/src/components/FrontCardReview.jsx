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
  ShieldCheck,
  User,
  XCircle,
} from 'lucide-react';
import ConfidenceBadge from './ConfidenceBadge';

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
  } = data;

  const fieldScores = confidence_summary?.fields || {};
  const threshold = confidence_summary?.confidence_threshold ?? 0.8;
  const reviewFields = confidence_summary?.fields_needing_review || [];

  return (
    <div className="ui-card">
      <div className="card-header">
        <h3>
          <FileCheck2 size={18} color="#1E293B" />
          <span>Extraction & Verification Result</span>
        </h3>
        <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
          {/* Quick Confidence Pill */}
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
            title="Copy structured JSON to clipboard"
          >
            {copied ? <Check size={14} color="#0D8244" /> : <Copy size={14} />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>
      </div>

      <div className="card-body">
        {/* Review Alert Banner only when low confidence or failed checksum */}
        {reviewFields.length > 0 && (
          <div className="review-alert-banner">
            <AlertTriangle size={16} />
            <div>
              <strong>Review Required:</strong> The following field(s) scored below the {(threshold * 100).toFixed(0)}% confidence threshold:
              <span className="review-fields-list">
                {reviewFields.map((f) => (
                  <span key={f} className="review-pill">{fieldScores[f]?.field_name_en || f}</span>
                ))}
              </span>
            </div>
          </div>
        )}

        {/* National ID Banner */}
        <div className="id-banner">
          <div>
            <div className="id-label">Citizen Identification Number (เลขประจำตัวประชาชน)</div>
            <div className="id-number">{formatThaiId(identification_number)}</div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {is_id_checksum_valid ? (
              <span className="badge badge-success">
                <ShieldCheck size={13} /> Mod 11 Valid
              </span>
            ) : (
              <span className="badge badge-error">
                <XCircle size={13} /> Checksum Invalid
              </span>
            )}
            <ConfidenceBadge fieldConfidence={fieldScores.identification_number} />
          </div>
        </div>

        {/* Names Section */}
        <div className="section-block">
          <div className="section-title">
            <User size={14} color="#475569" /> Names & Personal Identity
          </div>
          <div className="data-grid-2">
            {/* Thai Name */}
            <div className="field-cell">
              <div className="field-header-row">
                <span className="field-key">ชื่อ-นามสกุล (Thai Name)</span>
                <ConfidenceBadge fieldConfidence={fieldScores.thai_name} />
              </div>
              <div className="field-val thai-text">{thai_name?.full_name || '—'}</div>
              <div className="field-sub">
                คำนำหน้า: {thai_name?.title || '—'} | ชื่อ: {thai_name?.first_name || '—'}{' '}
                {thai_name?.middle_name ? `| กลาง: ${thai_name.middle_name}` : ''} | นามสกุล: {thai_name?.last_name || '—'}
              </div>
            </div>

            {/* English Name */}
            <div className="field-cell">
              <div className="field-header-row">
                <span className="field-key">English Name</span>
                <ConfidenceBadge fieldConfidence={fieldScores.english_name} />
              </div>
              <div className="field-val">{english_name?.full_name || '—'}</div>
              <div className="field-sub">
                Title: {english_name?.title || '—'} | First: {english_name?.first_name || '—'}{' '}
                {english_name?.middle_name ? `| Mid: ${english_name.middle_name}` : ''} | Last: {english_name?.last_name || '—'}
              </div>
            </div>
          </div>
        </div>

        {/* Dates & Demographics */}
        <div className="section-block">
          <div className="section-title">
            <Calendar size={14} color="#475569" /> Dates & Validity
          </div>
          <div className="data-grid-3">
            {/* Date of Birth */}
            <div className="field-cell">
              <div className="field-header-row">
                <span className="field-key">วันเกิด (DOB)</span>
                <ConfidenceBadge fieldConfidence={fieldScores.date_of_birth} />
              </div>
              <div className="field-val thai-text">{date_of_birth?.raw_text_th || '—'}</div>
              <div className="field-sub">
                CE: {date_of_birth?.iso_date || '—'} ({date_of_birth?.year_ce || '—'})
              </div>
              <div className="field-sub">
                BE: {date_of_birth?.year_be || '—'} (พ.ศ.)
              </div>
            </div>

            {/* Date of Issue */}
            <div className="field-cell">
              <div className="field-header-row">
                <span className="field-key">วันออกบัตร (Issue)</span>
                <ConfidenceBadge fieldConfidence={fieldScores.date_of_issue} />
              </div>
              <div className="field-val thai-text">{date_of_issue?.raw_text_th || '—'}</div>
              <div className="field-sub">
                CE: {date_of_issue?.iso_date || '—'} ({date_of_issue?.year_ce || '—'})
              </div>
              <div className="field-sub">
                BE: {date_of_issue?.year_be || '—'} (พ.ศ.)
              </div>
            </div>

            {/* Date of Expiry */}
            <div className="field-cell">
              <div className="field-header-row">
                <span className="field-key">วันหมดอายุ (Expiry)</span>
                <ConfidenceBadge fieldConfidence={fieldScores.date_of_expiry} />
              </div>
              {date_of_expiry?.is_lifetime ? (
                <div style={{ marginTop: '4px' }}>
                  <span className="badge badge-info">ตลอดชีพ (Lifetime)</span>
                </div>
              ) : (
                <>
                  <div className="field-val thai-text">{date_of_expiry?.raw_text_th || '—'}</div>
                  <div className="field-sub">
                    CE: {date_of_expiry?.iso_date || '—'} ({date_of_expiry?.year_ce || '—'})
                  </div>
                  <div className="field-sub">
                    BE: {date_of_expiry?.year_be || '—'} (พ.ศ.)
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Religion */}
        <div className="section-block">
          <div className="data-grid-2">
            <div className="field-cell">
              <div className="field-header-row">
                <span className="field-key">ศาสนา (Religion)</span>
                <ConfidenceBadge fieldConfidence={fieldScores.religion} />
              </div>
              <div className="field-val thai-text">{religion || '—'}</div>
            </div>
          </div>
        </div>

        {/* Address */}
        <div className="section-block">
          <div className="section-title">
            <MapPin size={14} color="#475569" /> ที่อยู่ตามทะเบียนราษฎร (Registered Address)
          </div>
          <div className="address-card">
            <div className="address-header-row">
              <div className="address-raw">
                <strong>ที่อยู่เต็ม:</strong> {address?.raw_address || '—'}
              </div>
              <ConfidenceBadge fieldConfidence={fieldScores.address} />
            </div>
            <div className="address-chips">
              {address?.house_no && (
                <div className="address-chip">
                  บ้านเลขที่: <span>{address.house_no}</span>
                </div>
              )}
              {address?.moo && (
                <div className="address-chip">
                  หมู่ที่: <span>{address.moo}</span>
                </div>
              )}
              {address?.trok_soi && (
                <div className="address-chip">
                  ตรอก/ซอย: <span>{address.trok_soi}</span>
                </div>
              )}
              {address?.road && (
                <div className="address-chip">
                  ถนน: <span>{address.road}</span>
                </div>
              )}
              {address?.sub_district && (
                <div className="address-chip">
                  ตำบล/แขวง: <span>{address.sub_district}</span>
                </div>
              )}
              {address?.district && (
                <div className="address-chip">
                  อำเภอ/เขต: <span>{address.district}</span>
                </div>
              )}
              {address?.province && (
                <div className="address-chip">
                  จังหวัด: <span>{address.province}</span>
                </div>
              )}
              {address?.postal_code && (
                <div className="address-chip">
                  รหัสไปรษณีย์: <span>{address.postal_code}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Toggle JSON */}
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
