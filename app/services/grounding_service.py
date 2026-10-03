"""Grounding and confidence scoring service connecting LLM extractions to Azure OCR metadata."""

import logging
import re
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.models.schemas import (
    ConfidenceSummary,
    FieldConfidence,
    OCRDocument,
    OCRWord,
    ThaiIdCardExtraction,
    ThaiIdCardLaserExtraction,
)

logger = logging.getLogger(__name__)


class GroundingService:
    """Provides evidence grounding and field-level confidence scoring against Azure Document Intelligence OCR metadata."""

    def __init__(self, confidence_threshold: Optional[float] = None):
        self.threshold = (
            confidence_threshold
            if confidence_threshold is not None
            else settings.CONFIDENCE_THRESHOLD
        )

    def _normalize_thai_text(self, text: str) -> str:
        """Removes spaces, zero-width characters, and common punctuation for clean comparison."""
        if not text:
            return ""
        return re.sub(r"[\s\u200b\u200c\u200d\uFEFF\-\.]+", "", str(text)).lower()

    def _match_sliding_window(
        self, target: str, ocr_doc: OCRDocument
    ) -> Optional[Tuple[float, Optional[List[float]], List[OCRWord]]]:
        """Finds a sequence of words in ocr_doc.words whose concatenated normalized text matches target."""
        target_norm = self._normalize_thai_text(target)
        if not target_norm or not ocr_doc.words:
            return None

        words = ocr_doc.words

        # Sliding window search bounded naturally by target_norm length
        for i in range(len(words)):
            accum = ""
            cand = []
            for j in range(i, len(words)):
                w_norm = self._normalize_thai_text(words[j].content)
                if not w_norm:
                    continue
                accum += w_norm
                cand.append(words[j])
                if accum == target_norm:
                    avg_conf = sum(w.confidence for w in cand) / len(cand)
                    polygon = self._combine_polygons([w.polygon for w in cand if w.polygon])
                    return avg_conf, polygon, cand
                if len(accum) > len(target_norm):
                    break

        return None

    def _match_by_span(
        self, target: str, ocr_doc: OCRDocument
    ) -> Optional[Tuple[float, Optional[List[float]], List[OCRWord]]]:
        """Tries to find the target in ocr_doc.content with whitespace tolerance and overlaps with word spans."""
        if not target or not ocr_doc.content:
            return None

        clean_target = target.strip()
        tokens = [t for t in clean_target.split() if t]
        if not tokens:
            return None

        # Whitespace-insensitive regex search
        pattern = r"\s*".join(re.escape(t) for t in tokens)
        m = re.search(pattern, ocr_doc.content, re.IGNORECASE)
        if not m:
            return None

        start_offset, end_offset = m.start(), m.end()

        matched_words: List[OCRWord] = []
        for w in ocr_doc.words:
            if w.span_offset is not None and w.span_length is not None:
                w_start = w.span_offset
                w_end = w.span_offset + w.span_length
                if not (w_end <= start_offset or w_start >= end_offset):
                    matched_words.append(w)

        if not matched_words:
            # Check by content containment in matched slice
            slice_text = ocr_doc.content[start_offset:end_offset]
            slice_norm = self._normalize_thai_text(slice_text)
            for w in ocr_doc.words:
                w_norm = self._normalize_thai_text(w.content)
                if w_norm and w_norm in slice_norm:
                    matched_words.append(w)

        if not matched_words:
            return None

        avg_conf = sum(w.confidence for w in matched_words) / len(matched_words)
        polygon = self._combine_polygons([w.polygon for w in matched_words if w.polygon])
        return avg_conf, polygon, matched_words

    def _match_strict_tokens(
        self, tokens: List[str], ocr_doc: OCRDocument
    ) -> Optional[Tuple[float, Optional[List[float]], List[OCRWord]]]:
        """Matches a set of distinct semantic tokens strictly against OCR words."""
        if not tokens or not ocr_doc.words:
            return None

        valid_tokens = [t.strip() for t in tokens if len(t.strip()) > 0]
        if not valid_tokens:
            return None

        matched_words: List[OCRWord] = []
        matched_tokens_count = 0

        for tok in valid_tokens:
            tok_norm = self._normalize_thai_text(tok)
            if not tok_norm:
                continue

            found = False
            for w in ocr_doc.words:
                w_norm = self._normalize_thai_text(w.content)
                if not w_norm:
                    continue

                # For short tokens (e.g. '1', '2', 'ส.ค.'), require strict equality
                if len(tok_norm) <= 3:
                    is_match = (tok_norm == w_norm)
                else:
                    is_match = (tok_norm == w_norm) or (tok_norm in w_norm and len(tok_norm) / len(w_norm) > 0.7)

                if is_match:
                    if w not in matched_words:
                        matched_words.append(w)
                    found = True
                    break

            if found:
                matched_tokens_count += 1

        match_ratio = matched_tokens_count / len(valid_tokens)
        if match_ratio >= 0.6 and matched_words:
            raw_avg = sum(w.confidence for w in matched_words) / len(matched_words)
            confidence = raw_avg * (0.85 + 0.15 * match_ratio)
            polygon = self._combine_polygons([w.polygon for w in matched_words if w.polygon])
            return confidence, polygon, matched_words

        return None

    def _combine_polygons(self, polygons: List[List[float]]) -> Optional[List[float]]:
        """Computes bounding envelope polygon [x_min, y_min, x_max, y_min, x_max, y_max, x_min, y_max] from words."""
        valid_polys = [p for p in polygons if p and len(p) >= 4]
        if not valid_polys:
            return None

        all_x: List[float] = []
        all_y: List[float] = []

        for p in valid_polys:
            for i in range(0, len(p), 2):
                all_x.append(p[i])
                if i + 1 < len(p):
                    all_y.append(p[i + 1])

        if not all_x or not all_y:
            return None

        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        return [min_x, min_y, max_x, min_y, max_x, max_y, min_x, max_y]

    def evaluate_field(
        self,
        field_code: str,
        field_name_en: str,
        field_name_th: str,
        raw_text: Optional[str],
        normalized_value: Optional[str],
        ocr_doc: OCRDocument,
        tokens_to_match: Optional[List[str]] = None,
        is_date_field: bool = False,
    ) -> FieldConfidence:
        """Evaluates confidence and evidence grounding for a single field against OCR metadata."""
        issues: List[str] = []

        if not raw_text and not normalized_value:
            return FieldConfidence(
                field_code=field_code,
                field_name_en=field_name_en,
                field_name_th=field_name_th,
                raw_text=None,
                normalized_value=None,
                confidence=0.0,
                confidence_percentage=0.0,
                is_confident=False,
                verification="not_in_source",
                status="not_found",
                polygon=None,
                issues=["Field value was not found in document"],
            )

        match_result = None

        # Priority 1: Sliding window word sequence match on raw_text
        if raw_text:
            match_result = self._match_sliding_window(raw_text, ocr_doc)

        # Priority 2: Whitespace-tolerant span match in content
        if not match_result and raw_text:
            match_result = self._match_by_span(raw_text, ocr_doc)

        # Priority 3: Sliding window on normalized_value (if not a date where format differs)
        if not match_result and normalized_value and not is_date_field:
            match_result = self._match_sliding_window(normalized_value, ocr_doc)

        # Priority 4: Strict token matching
        if not match_result:
            candidates: List[str] = []
            if tokens_to_match:
                candidates.extend(tokens_to_match)
            if raw_text:
                candidates.extend(raw_text.split())
            elif normalized_value and not is_date_field:
                candidates.extend(normalized_value.split())

            match_result = self._match_strict_tokens(candidates, ocr_doc)

        # Determine verification & confidence
        if match_result:
            calc_conf, polygon, matched_words = match_result
            verification = "in_source"
            confidence = min(max(calc_conf, 0.05), 1.0)

            # Check if LLM performed typo correction (ONLY for non-date fields where formats are directly comparable)
            if not is_date_field and raw_text and normalized_value:
                raw_clean = self._normalize_thai_text(raw_text)
                norm_clean = self._normalize_thai_text(normalized_value)
                if raw_clean and norm_clean and raw_clean != norm_clean:
                    issues.append(f"Corrected from raw OCR text: '{raw_text}'")
        else:
            # Fallback: check if normalized text or raw text exists in content
            check_val = raw_text or (normalized_value if not is_date_field else "")
            if check_val and self._normalize_thai_text(check_val) in self._normalize_thai_text(ocr_doc.content):
                verification = "in_source"
                confidence = 0.90
                polygon = None
            else:
                verification = "not_in_source"
                confidence = 0.40
                polygon = None
                issues.append("Field text could not be verified directly in OCR source text")

        confidence_pct = round(confidence * 100, 1)
        is_confident = (confidence >= self.threshold) and (verification == "in_source")
        status = "confident" if is_confident else "needs_review"

        if not is_confident and f"Confidence {confidence_pct}% below threshold {round(self.threshold * 100, 1)}%" not in issues:
            issues.append(f"Confidence {confidence_pct}% is below threshold {round(self.threshold * 100, 1)}%")

        return FieldConfidence(
            field_code=field_code,
            field_name_en=field_name_en,
            field_name_th=field_name_th,
            raw_text=raw_text,
            normalized_value=normalized_value,
            confidence=round(confidence, 4),
            confidence_percentage=confidence_pct,
            is_confident=is_confident,
            verification=verification,
            status=status,
            polygon=polygon,
            issues=issues,
        )

    def ground_thai_id_card(
        self,
        extracted: ThaiIdCardExtraction,
        ocr_doc: OCRDocument,
        is_id_checksum_valid: Optional[bool] = None,
    ) -> ConfidenceSummary:
        """Performs comprehensive grounding and confidence evaluation across all front ID card fields."""
        fields: Dict[str, FieldConfidence] = {}

        # 1. Identification Number
        id_raw = extracted.raw_identification_number or extracted.identification_number
        id_norm = extracted.identification_number
        fc_id = self.evaluate_field(
            field_code="identification_number",
            field_name_en="National ID Number",
            field_name_th="เลขประจำตัวประชาชน",
            raw_text=id_raw,
            normalized_value=id_norm,
            ocr_doc=ocr_doc,
        )
        if is_id_checksum_valid is False:
            fc_id.issues.append("13-digit checksum (Mod 11) failed")
            fc_id.confidence = round(min(fc_id.confidence, 0.49), 4)
            fc_id.confidence_percentage = round(fc_id.confidence * 100, 1)
            fc_id.is_confident = False
            fc_id.status = "needs_review"
        fields["identification_number"] = fc_id

        # 2. Thai Name
        th_name = extracted.thai_name
        th_tokens = []
        if th_name:
            th_tokens = [th_name.title, th_name.first_name, th_name.middle_name, th_name.last_name]
        fc_th_name = self.evaluate_field(
            field_code="thai_name",
            field_name_en="Thai Full Name",
            field_name_th="ชื่อ-นามสกุลภาษาไทย",
            raw_text=th_name.raw_text if th_name else None,
            normalized_value=th_name.full_name if th_name else None,
            ocr_doc=ocr_doc,
            tokens_to_match=[t for t in th_tokens if t],
        )
        fields["thai_name"] = fc_th_name
        if th_name:
            th_name.confidence = fc_th_name.confidence
            th_name.is_confident = fc_th_name.is_confident

        # 3. English Name
        en_name = extracted.english_name
        en_tokens = []
        if en_name:
            en_tokens = [en_name.title, en_name.first_name, en_name.middle_name, en_name.last_name]
        fc_en_name = self.evaluate_field(
            field_code="english_name",
            field_name_en="English Full Name",
            field_name_th="ชื่อ-นามสกุลภาษาอังกฤษ",
            raw_text=en_name.raw_text if en_name else None,
            normalized_value=en_name.full_name if en_name else None,
            ocr_doc=ocr_doc,
            tokens_to_match=[t for t in en_tokens if t],
        )
        fields["english_name"] = fc_en_name
        if en_name:
            en_name.confidence = fc_en_name.confidence
            en_name.is_confident = fc_en_name.is_confident

        # 4. Date of Birth
        dob = extracted.date_of_birth
        dob_tokens = []
        if dob:
            dob_tokens = [t for t in (dob.raw_text_th or "").split() if t]
        fc_dob = self.evaluate_field(
            field_code="date_of_birth",
            field_name_en="Date of Birth",
            field_name_th="วันเกิด",
            raw_text=dob.raw_text_th if dob else None,
            normalized_value=dob.iso_date if dob else None,
            ocr_doc=ocr_doc,
            tokens_to_match=dob_tokens,
            is_date_field=True,
        )
        fields["date_of_birth"] = fc_dob
        if dob:
            dob.confidence = fc_dob.confidence
            dob.is_confident = fc_dob.is_confident

        # 5. Religion
        fc_rel = self.evaluate_field(
            field_code="religion",
            field_name_en="Religion",
            field_name_th="ศาสนา",
            raw_text=extracted.raw_religion or extracted.religion,
            normalized_value=extracted.religion,
            ocr_doc=ocr_doc,
        )
        fields["religion"] = fc_rel

        # 6. Address
        addr = extracted.address
        addr_tokens = []
        if addr:
            addr_tokens = [
                addr.house_no,
                addr.sub_district,
                addr.district,
                addr.province,
                addr.postal_code,
            ]
        fc_addr = self.evaluate_field(
            field_code="address",
            field_name_en="Registered Address",
            field_name_th="ที่อยู่",
            raw_text=addr.raw_address if addr else None,
            normalized_value=addr.raw_address if addr else None,
            ocr_doc=ocr_doc,
            tokens_to_match=[t for t in addr_tokens if t],
        )
        fields["address"] = fc_addr
        if addr:
            addr.confidence = fc_addr.confidence
            addr.is_confident = fc_addr.is_confident

        # 7. Date of Issue
        doi = extracted.date_of_issue
        doi_tokens = []
        if doi:
            doi_tokens = [t for t in (doi.raw_text_th or "").split() if t]
        fc_doi = self.evaluate_field(
            field_code="date_of_issue",
            field_name_en="Date of Issue",
            field_name_th="วันออกบัตร",
            raw_text=doi.raw_text_th if doi else None,
            normalized_value=doi.iso_date if doi else None,
            ocr_doc=ocr_doc,
            tokens_to_match=doi_tokens,
            is_date_field=True,
        )
        fields["date_of_issue"] = fc_doi
        if doi:
            doi.confidence = fc_doi.confidence
            doi.is_confident = fc_doi.is_confident

        # 8. Date of Expiry
        doe = extracted.date_of_expiry
        doe_tokens = []
        if doe:
            if doe.is_lifetime:
                doe_tokens = ["ตลอดชีพ", "Lifetime"]
            else:
                doe_tokens = [t for t in (doe.raw_text_th or "").split() if t]
        fc_doe = self.evaluate_field(
            field_code="date_of_expiry",
            field_name_en="Date of Expiry",
            field_name_th="วันหมดอายุ",
            raw_text="ตลอดชีพ" if (doe and doe.is_lifetime) else (doe.raw_text_th if doe else None),
            normalized_value="ตลอดชีพ (Lifetime)" if (doe and doe.is_lifetime) else (doe.iso_date if doe else None),
            ocr_doc=ocr_doc,
            tokens_to_match=doe_tokens,
            is_date_field=True,
        )
        fields["date_of_expiry"] = fc_doe
        if doe:
            doe.confidence = fc_doe.confidence
            doe.is_confident = fc_doe.is_confident

        # Summary calculations
        total_fields = len(fields)
        overall_conf = sum(f.confidence for f in fields.values()) / max(total_fields, 1)
        overall_pct = round(overall_conf * 100, 1)
        confident_count = sum(1 for f in fields.values() if f.is_confident)
        review_fields = [f.field_code for f in fields.values() if not f.is_confident]

        return ConfidenceSummary(
            overall_confidence=round(overall_conf, 4),
            overall_confidence_percentage=overall_pct,
            confidence_threshold=self.threshold,
            is_overall_confident=(overall_conf >= self.threshold and len(review_fields) == 0),
            total_fields=total_fields,
            confident_fields_count=confident_count,
            review_fields_count=len(review_fields),
            fields=fields,
            fields_needing_review=review_fields,
        )

    def ground_laser_id(
        self,
        extracted: ThaiIdCardLaserExtraction,
        ocr_doc: OCRDocument,
        is_laser_id_valid_format: Optional[bool] = None,
    ) -> ConfidenceSummary:
        """Performs grounding and confidence evaluation for Laser ID (back of card)."""
        fields: Dict[str, FieldConfidence] = {}

        raw_val = extracted.raw_text or extracted.formatted_laser_id or extracted.raw_laser_id
        norm_val = extracted.formatted_laser_id or extracted.raw_laser_id

        fc = self.evaluate_field(
            field_code="laser_id",
            field_name_en="Laser ID (Back of Card)",
            field_name_th="รหัส Laser ID หลังบัตร",
            raw_text=raw_val,
            normalized_value=norm_val,
            ocr_doc=ocr_doc,
        )

        if is_laser_id_valid_format is False:
            fc.issues.append("Laser ID did not match 12-char DOPA format (2 uppercase letters + 10 digits)")
            fc.confidence = round(min(fc.confidence, 0.45), 4)
            fc.confidence_percentage = round(fc.confidence * 100, 1)
            fc.is_confident = False
            fc.status = "needs_review"

        fields["laser_id"] = fc

        review_fields = [f.field_code for f in fields.values() if not f.is_confident]
        overall_conf = fc.confidence
        overall_pct = round(overall_conf * 100, 1)

        return ConfidenceSummary(
            overall_confidence=round(overall_conf, 4),
            overall_confidence_percentage=overall_pct,
            confidence_threshold=self.threshold,
            is_overall_confident=(overall_conf >= self.threshold and len(review_fields) == 0),
            total_fields=1,
            confident_fields_count=1 if fc.is_confident else 0,
            review_fields_count=len(review_fields),
            fields=fields,
            fields_needing_review=review_fields,
        )
