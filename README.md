# Thai National ID Card Real-Time OCR & KIE Service

A production-ready, high-accuracy service for real-time OCR and Key Information Extraction (KIE) from **Thai National ID Cards** (both Front of card and Back Laser ID).

Built with **FastAPI**, **Azure Document Intelligence**, and **LLM Structured Outputs** (supporting both **OpenAI** and **Azure AI Foundry**).

---

## 🌟 Key Features

* **High-Accuracy OCR:** Utilizes **Azure Document Intelligence** (`prebuilt-layout`) to extract Thai script and layout.
* **Semantic LLM Extraction (No Brittle Regex):** Employs native OpenAI / Azure AI Foundry **Structured Outputs** (`client.chat.completions.parse`) with Pydantic schemas to extract:
  * 13-digit National Identification Number
  * Thai & English Names (separated into title, first, middle, and last name)
  * Dates of Birth, Issue, and Expiry (with Buddhist Era พ.ศ. $\rightarrow$ Christian Era A.D. conversion and ISO-8601 formatting)
  * Lifetime validity detection (*"ตลอดชีพ"*)
  * Address breakdown (house no, moo, soi, road, sub-district/แขวง, district/เขต, province, postal code)
  * Back-of-card **Laser ID** extraction (12-char code e.g. `JT0-1234567-89`)
* **Domain Validation:**
  * Thai National ID 13-digit Modulo 11 check digit verification
  * Laser ID alphanumeric format validation (`2 uppercase letters + 10 digits`)
* **Clean Architecture:** Strict separation between Outbound Clients (`app/clients/`) and Domain/Business Services (`app/services/`).
* **Multi-Input Support:** Accepts both direct image file uploads (`multipart/form-data`) and Base64 JSON payloads (`application/json`).

---

## 🏗️ System Architecture

```
[ Client Request ]
       │
       ├── Front of Card: POST /api/v1/ocr/id-card
       └── Back of Card:  POST /api/v1/ocr/laser-id
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. FastAPI Controller (app/api/v1/endpoints/id_card.py)     │
│    - Validates MIME type, file size (<10MB), and payload    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Pipeline Orchestrator (app/services/pipeline_service.py) │
│    - In-memory stream processing & latency measurement      │
└──────────────┬──────────────────────────┬───────────────────┘
               │                          │
               ▼                          ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│ 3. Outbound OCR Client       │ │ 4. LLM KIE Service         │
│    (app/clients/ocr_client)  │ │    (app/services/kie)      │
│    - Azure Doc Intelligence  │ │    - Outbound LLM Client   │
│    - Extracts plain text     │ │      (OpenAI / Foundry)    │
└──────────────┬───────────────┘ │    - Pydantic Schema Parse │
               │                 └──────────────┬─────────────┘
               └───────────────┬────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Validation Service (app/services/validation_service.py)  │
│    - 13-digit ID Checksum (Modulo 11 verification)          │
│    - Laser ID format verification & standard hyphen formatting│
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Real-Time Response Assembly                              │
│    - Returns structured JSON data + processing_time_ms      │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Requirements

* **Python:** 3.10 or higher (Tested on Python 3.12 / 3.13)
* **Azure Document Intelligence:** Endpoint & API Key
* **LLM Provider:**
  * **OpenAI:** API Key (supports `gpt-4o`, `gpt-4o-mini`, `gpt-5.4-mini`) **OR**
  * **Azure AI Foundry:** Endpoint, API Key, and Deployment Name

---

## 🚀 Quick Start Guide

### 1. Clone & Navigate to Repository

```bash
cd ocr-id-card
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# On macOS / Linux:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:

```ini
# Application Settings
APP_NAME="Thai ID Card OCR & KIE API"
APP_ENV=development
LOG_LEVEL=INFO
PORT=8000

# 1. OCR Engine: Azure Document Intelligence
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://<your-resource-name>.cognitiveservices.azure.com/"
AZURE_DOCUMENT_INTELLIGENCE_KEY="<your-azure-key>"
AZURE_DOCUMENT_INTELLIGENCE_MODEL_ID="prebuilt-layout"

# 2. LLM Provider ('openai' or 'azure_foundry')
LLM_PROVIDER="openai"

# OpenAI Settings (When LLM_PROVIDER=openai)
OPENAI_API_KEY="sk-proj-..."
OPENAI_MODEL="gpt-4o-mini"
OPENAI_TEMPERATURE=0.0

# Azure AI Foundry Settings (When LLM_PROVIDER=azure_foundry)
AZURE_FOUNDRY_ENDPOINT="https://<your-foundry-resource>.openai.azure.com/"
AZURE_FOUNDRY_API_KEY="<your-foundry-key>"
AZURE_FOUNDRY_DEPLOYMENT_NAME="gpt-4o-mini"
AZURE_FOUNDRY_API_VERSION="2024-08-01-preview"

# Limits & Options
MAX_IMAGE_SIZE_MB=10
```

### 5. Run the Backend API
 
```bash
# Start FastAPI server with live reload
uvicorn app.main:app --port 8000 --reload
```

Backend API will start at: `http://localhost:8000`
Interactive Swagger API docs: **`http://localhost:8000/docs`**

### 6. Run the Frontend Review UI (React)

In a separate terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies (if not yet installed)
npm install

# Start Vite development server
npm run dev
```

Frontend application will start at: **`http://localhost:3000`**
*(Vite proxies API calls to `http://localhost:8000` automatically)*

---

## 📡 API Endpoints & Usage

### 1. Health Check
* **Endpoint:** `GET /health`

```bash
curl -X GET http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Thai ID Card OCR & KIE API",
  "environment": "development",
  "ocr_engine": "azure_document_intelligence",
  "default_llm_provider": "openai"
}
```

---

### 2. Extract Thai ID Card (Front of Card)
* **Endpoint:** `POST /api/v1/ocr/id-card`

#### Option A: Multipart File Upload (Recommended)
```bash
curl -X POST "http://localhost:8000/api/v1/ocr/id-card" \
  -H "accept: application/json" \
  -F "file=@/path/to/thai_id_front.jpg;type=image/jpeg"
```

#### Option B: JSON Base64 Payload
```bash
curl -X POST "http://localhost:8000/api/v1/ocr/id-card" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "/9j/4AAQSkZJRgABAQEASABIAAD..."
  }'
```

#### Sample Response (`200 OK`):
```json
{
  "status": "success",
  "data": {
    "identification_number": "1100701234561",
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
      "iso_date": "1990-01-15",
      "is_lifetime": false
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
      "month": 2,
      "day": 20,
      "iso_date": "2021-02-20",
      "is_lifetime": false
    },
    "date_of_expiry": {
      "raw_text_th": "14 ม.ค. 2572",
      "raw_text_en": "14 Jan. 2029",
      "year_be": 2572,
      "year_ce": 2029,
      "month": 1,
      "day": 14,
      "iso_date": "2029-01-14",
      "is_lifetime": false
    }
  },
  "processing_time_ms": 1420.5
}
```

---

### 3. Extract Laser ID (Back of Card)
* **Endpoint:** `POST /api/v1/ocr/laser-id`

#### Option A: Multipart File Upload
```bash
curl -X POST "http://localhost:8000/api/v1/ocr/laser-id" \
  -H "accept: application/json" \
  -F "file=@/path/to/thai_id_back.jpg;type=image/jpeg"
```

#### Option B: JSON Base64 Payload
```bash
curl -X POST "http://localhost:8000/api/v1/ocr/laser-id" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "/9j/4AAQSkZJRgABAQEASABIAAD..."
  }'
```

#### Sample Response (`200 OK`):
```json
{
  "status": "success",
  "data": {
    "raw_laser_id": "JT0123456789",
    "formatted_laser_id": "JT0-1234567-89",
    "is_laser_id_valid_format": true
  },
  "processing_time_ms": 712.3
}
```

---

## 🧪 Running Tests

The test suite covers:
* Thai 13-digit checksum validation (Modulo 11 algorithm with valid/invalid IDs)
* Laser ID pattern validation & formatting (`XX0-0000000-00`)
* Pydantic Structured Outputs schema serialization & validation
* FastAPI endpoint integration tests with mocked Azure OCR and LLM adapters

Run all tests:
```bash
pytest tests/ -v
```

---

## 📁 Project Structure

```text
ocr-id-card/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   └── id_card.py            # Endpoints: POST /id-card, POST /laser-id
│   │   └── router.py                 # API v1 Router
│   ├── clients/                      # Outbound External Adapters (I/O Layer)
│   │   ├── ocr_client.py             # Azure Document Intelligence SDK client
│   │   └── llm_client.py             # OpenAI & Azure AI Foundry client adapter
│   ├── core/
│   │   └── config.py                 # Pydantic BaseSettings (.env reader)
│   ├── models/
│   │   └── schemas.py                # Pydantic request & response contracts
│   ├── services/                     # Pure Domain & Business Logic
│   │   ├── kie_service.py            # KIE prompts & Structured Output extraction
│   │   ├── validation_service.py     # Checksum Modulo 11 & Laser ID format verification
│   │   └── pipeline_service.py       # Pipeline orchestrator: Ingestion -> OCR -> KIE -> Validation
│   └── main.py                       # FastAPI entrypoint, CORS, health check
├── tests/
│   ├── test_checksum.py              # Unit tests for Checksum & Laser ID format
│   ├── test_kie_schema.py            # Schema instantiation & decoupled KIE tests
│   └── test_api.py                   # Integration tests with mocked pipeline
├── AGENTS.md                         # Full technical architecture specification
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── .env                              # Active environment configuration
└── README.md                         # Project documentation and run guide
```

---

## 🎨 Frontend Review Web Application (Generali Design System)

A minimal, modern React application built with **Vanilla CSS** featuring Generali brand accents (Generali Red `#C41230`, gold accents, and clean card elevations) is included in the `frontend/` directory for interactive document review.

### Features
* **Dual Review Modes**: Front Thai ID Card (`/api/v1/ocr/id-card`) & Back Laser ID (`/api/v1/ocr/laser-id`).
* **Instant Synthetic Test Cards**: 1-click generation of realistic in-memory test cards (Front and Laser ID) for rapid testing without needing local image files.
* **Laser Scanning Animation**: Visual scanner bar during real-time inference.
* **Checksum & Validation Badges**: Modulo-11 check digit verification and DOPA laser pattern status.
* **JSON Inspection & Copying**: 1-click clipboard export of clean structured data.

### How to Run the Frontend:

1. In a new terminal, navigate to the `frontend/` directory:
   ```bash
   cd frontend
   npm install
   ```

2. Start the Vite development server:
   ```bash
   npm run dev
   ```

3. Open your browser at:
   ```text
   http://localhost:3000
   ```
   *Requests to `/api` and `/health` are automatically proxied to `http://localhost:8000`.*

---

## 🐳 Docker Deployment (Nginx + Frontend + Backend)

The service is fully dockerized with a production-grade 3-tier architecture:
* **`nginx` (Gateway Reverse Proxy - Port 80):** Unified entry point handling CORS-free reverse proxying, SSL-readiness, request timeouts (120s for LLM/OCR), max upload payload up to 25MB, and Gzip compression.
* **`backend` (FastAPI Service - Port 8000):** Python 3.12-slim container running Uvicorn ASGI with non-root security user, built-in health checks (`/health`), and Azure / LLM processing.
* **`frontend` (React + Vite Web App - Port 3000 / Internal Port 80):** Multi-stage Node 20 builder and lightweight Nginx static runner with immutable asset caching and SPA routing.

```text
[ Browser / Client ] :80
           │
           ▼
┌──────────────────────────────────────────────┐
│  Nginx Gateway (:80)                         │
│  - /api/*              ──► Backend (:8000)      │
│  - /health             ──► Backend (:8000)      │
│  - /docs, /redoc       ──► Backend (:8000)      │
│  - /demo/id-card/*       ──► Thai ID Card Frontend (:80)      │
│  - /demo/ocr-group-eb/*   ──► Group EB Claims Frontend (:80)   │
│  - /                     ──► Gateway Hub (Portal)             │
└──────────────────────┬────────────────────────────────────────┘
                       │ Docker Network (ocr-poc)
         ┌─────────────┼─────────────────────────┐
         ▼             ▼                         ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────────┐
│  ID Card Service │ │ ID Card Frontend │ │ Group EB Services        │
│  FastAPI (:8000) │ │ React SPA (:80)  │ │ (claims_eb_frontend/api) │
└──────────────────┘ └──────────────────┘ └──────────────────────────┘
```

### 1. Quick Start (Production Mode)

1. Make sure your `.env` file exists and is configured:
   ```bash
   cp .env.example .env
   # Edit .env with your Azure Document Intelligence and OpenAI/Foundry credentials
   ```

2. Build and start all services in the background:
   ```bash
   docker compose up --build -d
   ```

3. Access the services:
   * **Web Application (Thai ID Card):** [http://localhost/demo/id-card](http://localhost/demo/id-card)
   * **Web Application (Group EB Claims):** [http://localhost/demo/ocr-group-eb](http://localhost/demo/ocr-group-eb)
   * **Gateway Landing Hub:** [http://localhost](http://localhost) (Portal รวมลิงก์ทุกแอป)
   * **Interactive API Documentation:** [http://localhost/docs](http://localhost/docs)
   * **Health Check:** [http://localhost/health](http://localhost/health)
   * **Direct Backend API (optional):** [http://localhost:8000](http://localhost:8000)
   * **Direct Frontend Dev (optional):** [http://localhost:3000](http://localhost:3000) (รันแบบ standalone ปกติ ไม่เพี้ยน)

4. Monitor status and logs:
   ```bash
   # Check service health
   docker compose ps

   # Follow combined or specific service logs
   docker compose logs -f
   docker compose logs -f backend
   docker compose logs -f nginx
   ```

5. Run test suite inside the running container:
   ```bash
   docker compose exec backend pytest
   ```

6. Stop containers:
   ```bash
   docker compose down
   ```

---

### 2. Live Development Mode (Hot-Reload)

To run in development mode with live source-code reloading for both FastAPI (`uvicorn --reload`) and Vite (`npm run dev` with HMR WebSocket support):

```bash
docker compose -f docker-compose.dev.yml up --build
```

---

## 💡 Production Deployment Notes (Bare Metal / VM)

If running without Docker directly on a host machine behind a system reverse proxy:

```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --proxy-headers \
  --forwarded-allow-ips="*"
```


