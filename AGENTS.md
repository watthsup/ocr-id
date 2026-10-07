# Technical Specification: Thai National ID Card OCR & Key Information Extraction (KIE) Service

This document specifies the technical architecture, data contracts, validation rules, and API design for the **Thai National ID Card Real-Time OCR & Key Information Extraction (KIE) Service**.

---

## 1. System Architecture & Real-Time Flow

The service exposes **a single real-time inference endpoint** that takes a Thai National ID card image, extracts full-text layout and coordinates via **Azure Document Intelligence**, and extracts structured semantic fields using an **LLM KIE Engine** (supporting both **OpenAI** and **Azure AI Foundry**).

```
[ Client Request ]
       │
       ▼ (Single Real-time Request: Multipart Image or Base64 JSON)
┌─────────────────────────────────────────────────────────────┐
│ 1. FastAPI Route Layer (app/api/v1/endpoints/id_card.py)    │
│    - Single Endpoint: POST /api/v1/ocr/id-card              │
│    - Validates MIME type, file size, and payload integrity  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Pipeline Orchestration (app/services/pipeline_service.py)│
│    - Controls end-to-end execution & measures step latencies│
│    - Direct stream forwarding (in-memory, zero temp disk)   │
└──────────────┬──────────────────────────┬───────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│ 3. Azure Document            │ │ 4. LLM KIE Engine          │
│    Intelligence Service      │ │    (app/services/kie)      │
│    (app/services/azure_ocr)  │ │    - Dual-Provider Support:│
│    - Prebuilt Read / Layout  │ │      * OpenAI              │
│    - High-precision Thai OCR │ │      * Azure AI Foundry    │
│    - Words, lines, polygons  │ │    - Structured Outputs    │
└──────────────┬───────────────┘ └──────────────┬─────────────┘
               │                                │
               └───────────────┬────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Validation & Normalization Service                       │
│    (app/services/validation_service.py)                     │
│    - Thai National ID 13-digit checksum validation (mod 11) │
│    - Buddhist Era (BE) to Common Era (CE / AD) conversion   │
│    - Thai Address hierarchical parsing & standardisation    │
│    - Name components separation (Title, First, Mid, Last)   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Real-Time Response Assembly                              │
│    - Return structured JSON with card fields & confidence   │
│    - Raw OCR text and bounding polygons                     │
│    - Latency benchmarks (OCR ms, KIE ms, Total ms)          │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack & Dependencies

* **Framework:** FastAPI 0.115+, Uvicorn (ASGI)
* **Language & Runtime:** Python 3.10+ (Validated on Python 3.12/3.13)
* **OCR Engine:** Azure Document Intelligence (`azure-ai-documentintelligence` v1.0.0b4+)
  * Utilizes `prebuilt-layout` or `prebuilt-read` for fast, accurate Thai script layout and word-level polygon extraction.
* **LLM Extraction Engine (Multi-Provider):**
  * **OpenAI:** Native OpenAI SDK (`openai>=1.47.0`), using JSON schema structured outputs (`gpt-4o`, `gpt-4o-mini`).
  * **Azure AI Foundry:** Supported via Azure OpenAI / Azure AI Foundry Model-as-a-Service endpoints (`openai.AzureOpenAI` or `azure-ai-inference`), fully compatible with enterprise private networks and managed identities.
* **Validation & Schemas:** Pydantic v2 (`pydantic>=2.8.0`, `pydantic-settings>=2.5.0`)
* **Image Utilities:** `Pillow>=10.4.0` (format detection, dimension check, rotation correction)

---

## 3. Codebase Structure

```
ocr-id-card/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   └── id_card.py            # Single Real-Time Endpoint: POST /api/v1/ocr/id-card
│   │   └── router.py                 # Mounts /ocr router under /api/v1
│   ├── clients/                      # Outbound External Adapters
│   │   ├── ocr_client.py             # Azure Document Intelligence SDK client with words & polygons
│   │   └── llm_client.py             # OpenAI & Azure AI Foundry client adapter
│   ├── core/
│   │   └── config.py                 # Pydantic BaseSettings (.env, Azure, OpenAI/Foundry, CONFIDENCE_THRESHOLD)
│   ├── models/
│   │   └── schemas.py                # Pydantic request & response contracts (Strict Thai ID, OCRDocument, ConfidenceSummary)
│   ├── services/                     # Pure Business Logic
│   │   ├── kie_service.py            # Thai ID dual-extraction prompt engineering & schema extraction
│   │   ├── grounding_service.py      # Field-level evidence grounding & Azure OCR confidence scoring
│   │   ├── validation_service.py     # Checksum mod 11 calculation & data sanitization
│   │   └── pipeline_service.py       # Core orchestrator: OCR -> KIE -> Checksum -> Grounding -> Stages
│   └── main.py                       # FastAPI entrypoint, CORS, lifespan, healthcheck
├── frontend/                         # Generali-styled React Review Web Application
│   ├── src/
│   │   ├── components/               # Header, ImageUpload, FrontCardReview, LaserIdReview, TopPipelineBar, ConfidenceBadge
│   │   ├── utils/sampleImages.js     # Synthetic ID canvas generator
│   │   ├── App.jsx                   # Review UI logic & API state management with live timer
│   │   └── index.css                 # Generali Design System (Vanilla CSS)
│   ├── index.html                    # Fonts (Outfit, Inter, Prompt) & metadata
│   ├── vite.config.js                # Vite dev server (port 3000) & backend proxy
│   ├── nginx.conf                    # Frontend internal SPA static server config
│   ├── Dockerfile                    # Multi-stage Docker build for React
│   └── package.json
├── nginx/                            # Gateway Reverse Proxy
│   ├── default.conf                  # Production reverse proxy (ports, timeouts, headers)
│   ├── default.dev.conf              # Development reverse proxy with Vite HMR
│   └── Dockerfile                    # Nginx Alpine reverse proxy image
├── tests/
│   ├── test_checksum.py              # Unit tests for 13-digit Thai ID checksum & date conversion
│   ├── test_grounding.py             # Unit tests for GroundingService, confidence scoring & thresholding
│   ├── test_kie_schema.py            # Tests for Pydantic schema validation & LLM response parsing
│   └── test_api.py                   # Integration test for POST /api/v1/ocr/id-card & /laser-id
├── Dockerfile                        # Backend FastAPI production Docker image (Python 3.12-slim)
├── docker-compose.yml                # Production orchestration (nginx + frontend + backend)
├── docker-compose.dev.yml            # Development orchestration with hot reload
├── .dockerignore                     # Docker build context ignore rules
├── AGENTS.md                         # Technical architecture & specification
├── requirements.txt                  # Python dependencies
├── .env.example                      # Configuration template
└── .env                              # Active environment configuration
```

---

## 4. Core Technology Stack Details

### 4.1. OCR Engine: Azure Document Intelligence
* **Endpoint / Client:** `DocumentIntelligenceClient` from `azure-ai-documentintelligence`.
* **Model ID:** `prebuilt-layout` (recommended for reading order and table/key structures) or `prebuilt-read` (optimized for raw text & polygon speed).
* **Processing Flow:**
  1. Image bytes received in memory (no disk I/O required).
  2. Direct call: `begin_analyze_document(model_id=..., body=image_bytes)`.
  3. Extracts:
     - Full document text lines in natural reading order.
     - Individual words with confidence scores and 4-point bounding polygons.
     - Document dimensions (width, height, orientation angle).

### 4.2. LLM Key Information Extraction (KIE) Engine

The KIE engine transforms raw, potentially unordered or noisy Thai OCR text into a strictly typed Thai National ID data structure.

#### Dual-Provider Architecture
The service supports both **OpenAI** and **Azure AI Foundry** seamlessly through a unified provider factory configured via `.env`:

1. **Provider: OpenAI (`LLM_PROVIDER=openai`)**
   ```python
   from openai import OpenAI
   client = OpenAI(api_key=settings.OPENAI_API_KEY)
   # Invokes client.chat.completions.parse(model=settings.OPENAI_MODEL, response_format=ThaiIdCardExtraction, ...)
   ```

2. **Provider: Azure AI Foundry (`LLM_PROVIDER=azure_foundry`)**
   ```python
   from openai import AzureOpenAI
   client = AzureOpenAI(
       azure_endpoint=settings.AZURE_FOUNDRY_ENDPOINT,
       api_key=settings.AZURE_FOUNDRY_API_KEY,
       api_version=settings.AZURE_FOUNDRY_API_VERSION,
   )
   # Invokes client.chat.completions.parse(model=settings.AZURE_FOUNDRY_DEPLOYMENT_NAME, response_format=ThaiIdCardExtraction, ...)
   ```

#### Prompt Strategy & Extraction Rules (Pydantic Structured Outputs)
* **Native Pydantic Schema:** The exact schema (`ThaiIdCardExtraction`) is passed directly to the LLM via `response_format`, enabling constrained decoding without dumping JSON template strings into the system prompt.
* **LLM-Based Semantic Extraction:** The extraction rules for names (title, first, middle, last), dates (day, month, BE, CE, ISO format, lifetime detection), and address components (house_no, moo, trok_soi, road, sub_district, district, province, postal_code) are handled directly by the **LLM** using contextual semantic understanding rather than brittle regular expressions.
* **OCR Noise Robustness:** Handles missing Thai vowel marks (สระ/วรรณยุกต์), confusing characters (e.g., `0` vs `O`, `1` vs `l`, `ข` vs `ช`), and abbreviated address prefixes (`ถ.` -> ถนน, `ต.` -> ตำบล).
* **Deterministic Field Mapping:** Maps extracted Thai dates into structured components: day, month, Buddhist year (BE), and Christian year (CE).

---

## 5. Thai ID Card Domain Logic & Validation

### 5.1. 13-Digit Thai National ID Checksum Algorithm
The 13th digit of the Thai ID card is a check digit calculated using a modulo 11 algorithm:
$$\text{Sum} = \sum_{i=0}^{11} d_i \times (13 - i)$$
$$\text{Remainder} = \text{Sum} \pmod{11}$$
$$\text{Check Digit} = (11 - \text{Remainder}) \pmod{10}$$

* If the extracted 13th digit matches the calculated check digit, `is_id_checksum_valid = true`.
* If invalid (e.g. due to OCR noise), the flag is set to `false` and an alert is flagged in the response.

### 5.2. Date & Address Sanitization (Validation Layer)
* **Validation Layer Scope:** The validation service performs arithmetic checks (checksum calculation, CE = BE - 543 consistency, ISO-8601 formatting) and type casting without relying on regex rules for extraction.
* **Lifetime Expiry:** Detects cards with perpetual validity (*"ตลอดชีพ"* / *"Lifetime"*) and flags `is_lifetime_expiry = true` with `date_of_expiry = null`.

---

## 6. Single Real-Time REST API Specification

### 6.1. Real-Time ID Card OCR & Extraction Endpoint

* **Endpoint:** `POST /api/v1/ocr/id-card`
* **Method:** `POST`
* **Description:** Unified synchronous real-time inference endpoint. Accepts an ID card image, runs Azure Document Intelligence OCR, extracts KIE fields via OpenAI / Azure Foundry LLM, performs validation, and returns the result immediately.
* **Content-Type Support:**
  1. `multipart/form-data` (Direct image file upload)
  2. `application/json` (Base64-encoded image string or remote image URL)

#### Request Example (Multipart Form Upload):
```bash
curl -X POST "http://localhost:8000/api/v1/ocr/id-card" \
  -H "accept: application/json" \
  -F "file=@sample_thai_id.jpg;type=image/jpeg"
```

#### Request Example (JSON Base64 Payload):
```json
{
  "image_base64": "/9j/4AAQSkZJRgABAQEASABIAAD..."
}
```

#### Response Contract (`200 OK` - `ThaiIdCardResponse`):
```json
{
  "status": "success",
  "data": {
    "identification_number": "1100701234567",
    "is_id_checksum_valid": true,
    "thai_name": {
      "title": "นาย",
      "first_name": "สมชาย",
      "middle_name": null,
      "last_name": "ใจดี",
      "full_name": "นายสมชาย ใจดี"
    },
    "english_name": {
      "title": "Mr.",
      "first_name": "Somchai",
      "middle_name": null,
      "last_name": "Jaidee",
      "full_name": "Mr. Somchai Jaidee"
    },
    "date_of_birth": {
      "raw_text_th": "15 ม.ค. 2533",
      "raw_text_en": "15 Jan. 1990",
      "year_be": 2533,
      "year_ce": 1990,
      "month": 1,
      "day": 15,
      "iso_date": "1990-01-15"
    },
    "religion": "พุทธ",
    "address": {
      "raw_address": "99/1 หมู่ที่ 2 ต.บางตลาด อ.ปากเกร็ด จ.นนทบุรี 11120",
      "house_no": "99/1",
      "moo": "2",
      "trok_soi": null,
      "road": null,
      "sub_district": "บางตลาด",
      "district": "ปากเกร็ด",
      "province": "นนทบุรี",
      "postal_code": "11120"
    },
    "date_of_issue": {
      "raw_text_th": "20 ก.พ. 2564",
      "raw_text_en": "20 Feb. 2021",
      "year_be": 2564,
      "year_ce": 2021,
      "iso_date": "2021-02-20"
    },
    "date_of_expiry": {
      "raw_text_th": "14 ม.ค. 2572",
      "raw_text_en": "14 Jan. 2029",
      "year_be": 2572,
      "year_ce": 2029,
      "iso_date": "2029-01-14",
      "is_lifetime": false
    }
  },
  "processing_time_ms": 1626.9
}
```

### 6.2. Real-Time Laser ID Extraction Endpoint (Back of Card)

* **Endpoint:** `POST /api/v1/ocr/laser-id`
* **Method:** `POST`
* **Description:** Extracts the 12-character alphanumeric Laser ID printed on the back of the Thai National ID card (e.g. `JT0-1234567-89`), validates the format (`2 letters + 10 digits`), and returns structured data.
* **Content-Type Support:** `multipart/form-data` (image upload) or `application/json` (base64 string).

#### Response Contract (`200 OK` - `ThaiIdCardLaserResponse`):
```json
{
  "status": "success",
  "data": {
    "raw_laser_id": "JT0123456789",
    "formatted_laser_id": "JT0-1234567-89",
    "is_laser_id_valid_format": true
  },
  "processing_time_ms": 782.4
}
```

---

## 7. Configuration & Environment Variables (`.env`)

```bash
# Application Settings
APP_NAME="Thai ID Card OCR & KIE API"
APP_ENV=production
LOG_LEVEL=INFO
PORT=8000

# 1. OCR Engine: Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://<your-resource-name>.cognitiveservices.azure.com/"
AZURE_DOCUMENT_INTELLIGENCE_KEY="<your-azure-key>"
AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID="prebuilt-layout"

# 2. LLM KIE Engine Selection ('openai' or 'azure_foundry')
LLM_PROVIDER="openai"

# OpenAI Configuration (Used when LLM_PROVIDER=openai)
OPENAI_API_KEY="sk-proj-..."
OPENAI_MODEL="gpt-4o-mini"
OPENAI_TEMPERATURE=0.0

# Azure AI Foundry Configuration (Used when LLM_PROVIDER=azure_foundry)
AZURE_FOUNDRY_ENDPOINT="https://<your-foundry-resource>.openai.azure.com/"
AZURE_FOUNDRY_API_KEY="<your-foundry-key>"
AZURE_FOUNDRY_DEPLOYMENT_NAME="gpt-4o-mini"
AZURE_FOUNDRY_API_VERSION="2024-08-01-preview"

# Processing Options
DEFAULT_VALIDATE_CHECKSUM=true
MAX_IMAGE_SIZE_MB=10
```

---

## 8. Verification and Testing Guide

* **Run Unit Tests (Checksum, BE/CE Date Parsing, Address Extraction):**
  ```bash
  pytest tests/test_checksum.py tests/test_kie_schema.py -v
  ```

* **Run Local Real-Time API Server (FastAPI):**
  ```bash
  uvicorn app.main:app --port 8000 --reload
  ```

* **Run Frontend Review Web Application (React + Vite):**
  ```bash
  cd frontend
  npm install
  npm run dev
  ```
  Open `http://localhost:3000` in your browser. Requests to `/api` and `/health` will be automatically proxied to port `8000`.

* **Run with Docker Compose (Production - Nginx + Frontend + Backend):**
  ```bash
  docker compose up --build -d
  # Open http://localhost/demo/id-card (Frontend review UI, or http://localhost which redirects)
  # Open http://localhost/docs (API Swagger documentation)
  ```

* **Run with Docker Compose (Development with Hot Reload):**
  ```bash
  docker compose -f docker-compose.dev.yml up --build
  ```

* **Run Tests inside Backend Container:**
  ```bash
  docker compose exec backend pytest -v
  ```

* **Run Interactive API Documentation:**
  Open `http://localhost:8000/docs` (direct) or `http://localhost/docs` (via Nginx proxy) in your browser.


