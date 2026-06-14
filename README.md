# JeevaKosha

**JeevaKosha** (जीवकोश — *life repository*) is a secure personal medical repository and health intelligence platform. It lets users store clinical documents, extract structured lab data via OCR, chat with an AI assistant over their own records, track health trends, and run a voice-based AI symptom assessment — all scoped to the authenticated user.

---

## Overview

Healthcare generates vast amounts of data: lab reports, prescriptions, imaging summaries, and longitudinal histories. JeevaKosha centralizes that information in one trusted system with strong access controls, AI-assisted retrieval, and actionable health insights.

### Goals

- **Centralize** medical records in one trusted, user-owned system
- **Organize** documents by hospital, category (prescriptions / reports), and report subfolders
- **Extract** structured data from uploaded reports using AI OCR
- **Retrieve** information quickly through RAG chat and health dashboards
- **Assess** symptoms via a multilingual voice interview and MedGemma analysis
- **Protect** sensitive health data with JWT auth and per-user data isolation

---

## Features

### Implemented

| Feature | Description |
|--------|-------------|
| **Authentication** | Register, login, JWT-protected API; all data scoped by `user_id` |
| **Medical Repository** | Hospital folders with prescriptions and reports |
| **Report subfolders** | User-defined categories (e.g. Blood Test, Diabetes) that guide OCR extraction |
| **Document upload** | PDF/image upload stored in MongoDB GridFS |
| **OCR pipeline** | Nebius/Gemma extracts structured fields from Blood Test & Diabetes reports |
| **Health dashboard** | Charts built from OCR `results` (hemoglobin, glucose, etc.) |
| **RAG chatbot** | Vector search over document embeddings + streaming LLM responses |
| **Patient profile** | View/edit portfolio: demographics, conditions, meds, allergies, surgeries |
| **AI Diagnosis** | 10-question voice interview (Sarvam STT/TTS) + MedGemma differential diagnosis |

### Security & privacy

| Feature | Description |
|--------|-------------|
| **User-scoped data** | Hospitals, documents, profiles, and chat context isolated per user |
| **JWT authentication** | Bearer tokens on all protected routes |
| **Orphan cleanup** | Startup purge of records without a valid owner |
| **No secrets in repo** | Environment variables for all API keys and credentials |
| **Medical disclaimers** | Chat and AI Diagnosis include doctor-consultation warnings |

### Planned / roadmap

- FHIR-compatible APIs for interoperability
- Persistent AI Diagnosis session history in MongoDB
- Patient portal sharing with clinicians
- Audit logging for sensitive actions
- Additional OCR report types beyond Blood Test and Diabetes

---

## Architecture

### High-level system diagram

```mermaid
flowchart TB
    subgraph client [Frontend — React + Vite]
        UI[Web App]
        Pages[Dashboard · Repository · Chat · AI Diagnosis · Profile]
    end

    subgraph api [Backend — FastAPI]
        Auth[Auth Router]
        Hospitals[Hospitals & Documents]
        OCR[OCR Worker]
        Chat[Chat / RAG]
        Dashboard[Health Dashboard]
        Profile[Profile]
        AiDx[AI Diagnosis]
    end

    subgraph external [External Services]
        MongoDB[(MongoDB Atlas)]
        GridFS[(GridFS — file storage)]
        Nebius[Nebius API — OCR & embeddings]
        Sarvam[Sarvam AI — STT / TTS]
        HF[HuggingFace — MedGemma]
    end

    UI --> Pages
    Pages --> Auth
    Pages --> Hospitals
    Pages --> Chat
    Pages --> Dashboard
    Pages --> Profile
    Pages --> AiDx

    Auth --> MongoDB
    Hospitals --> MongoDB
    Hospitals --> GridFS
    OCR --> Nebius
    OCR --> MongoDB
    Chat --> Nebius
    Chat --> MongoDB
    Dashboard --> MongoDB
    Profile --> MongoDB
    AiDx --> Sarvam
    AiDx --> HF
```

### AI Diagnosis flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API as FastAPI /ai-diagnosis
    participant Sarvam as Sarvam AI
    participant MedGemma as MedGemma HF

    User->>Frontend: Start assessment (select language)
    Frontend->>API: POST /session/start
    API->>Sarvam: TTS — question 1
    API-->>Frontend: session_id + question + audio

    loop 10 questions
        User->>Frontend: Record answer (mic)
        Frontend->>API: POST /voice/transcribe
        API->>Sarvam: STT
        Sarvam-->>API: transcript
        Frontend->>API: POST /voice/answer
        API->>Sarvam: TTS — next question
    end

    Frontend->>API: POST /diagnosis/analyze
    API->>MedGemma: Symptom JSON
    MedGemma-->>API: Differential + triage
    API-->>Frontend: Structured assessment report
```

### Data model (MongoDB collections)

| Collection | Purpose |
|------------|---------|
| `users` | Accounts (email, hashed password, name) |
| `hospitals` | User-owned hospital folders |
| `documents` | Prescription/report metadata + OCR data + embeddings |
| `report_folders` | Subfolders inside Reports (e.g. Blood Test) |
| `profiles` | One patient portfolio document per user |
| `medical_files` (GridFS) | Raw uploaded PDFs and images |

AI Diagnosis sessions are stored **in memory** (not persisted) and are cleared on server restart.

---

## Tech stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, Vite 5, TanStack Query, Axios, Recharts, Lucide icons |
| **Backend** | FastAPI, Uvicorn, Motor (async MongoDB), Pydantic v2 |
| **Database** | MongoDB Atlas (+ Atlas Vector Search index `vector_index`) |
| **File storage** | MongoDB GridFS |
| **OCR & chat LLM** | Nebius API (Gemma) |
| **Embeddings** | Qwen3-Embedding-8B via Nebius |
| **AI Diagnosis STT/TTS** | Sarvam AI (`saarika:v2.5`, `bulbul:v2`) |
| **AI Diagnosis reasoning** | MedGemma via HuggingFace OpenAI-compatible endpoint |
| **Authentication** | JWT (python-jose + bcrypt) |

---

## Project structure

```
JeevaKosha/
├── README.md
├── requirements.txt          # Python backend dependencies
├── .env                      # Environment variables (not committed)
├── .env.example
├── backend/
│   ├── main.py               # FastAPI app entry point
│   ├── database.py           # MongoDB client, indexes, vector search setup
│   ├── voice_agent_prompts.py
│   ├── models/               # Pydantic schemas (user, hospital, document, profile)
│   ├── routes/
│   │   ├── auth.py
│   │   ├── hospitals.py
│   │   ├── documents.py
│   │   ├── report_folders.py
│   │   ├── ocr.py
│   │   ├── chat.py           # RAG chatbot (SSE streaming)
│   │   ├── dashboard.py      # Health charts data
│   │   ├── profile.py
│   │   └── ai_diagnosis.py   # Voice interview + MedGemma analysis
│   └── services/
│       ├── auth.py
│       ├── storage.py        # GridFS upload/download
│       ├── ocr.py            # OCR prompts & extraction
│       ├── ocr_worker.py     # Background OCR processing
│       ├── embedding.py      # Vector embeddings for RAG
│       ├── session_store.py  # In-memory AI Diagnosis sessions
│       ├── sarvam_service.py # Sarvam STT / TTS
│       └── medgemma_service.py
└── frontend/
    ├── index.html
    ├── styles.css
    ├── package.json
    └── src/
        ├── App.jsx             # Routing, sidebar, auth shell
        ├── api.js              # Axios client + API helpers
        ├── pages/
        │   ├── Landing.jsx
        │   ├── HealthDashboard.jsx
        │   ├── Hospitals.jsx
        │   ├── HospitalVault.jsx
        │   ├── ReportFoldersPage.jsx
        │   ├── Documents.jsx
        │   ├── Chat.jsx
        │   ├── Profile.jsx
        │   └── AiDiagnosis.jsx
        └── components/
```

---

## Getting started

### Prerequisites

- **Python** 3.11+
- **Node.js** 20+
- **MongoDB** 6+ (Atlas recommended for vector search)
- **Git**

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/jeevakosha.git
cd jeevakosha

# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install && cd ..
```

### Environment variables

Copy `.env.example` to `.env` in the project root and fill in your values:

```env
# ── MongoDB ───────────────────────────────────────────────────────────────────
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?appName=Cluster0
DB_NAME=jeevakosha

# ── Auth ──────────────────────────────────────────────────────────────────────
JWT_SECRET=generate-a-strong-random-secret

# ── Nebius — OCR, chat LLM, embeddings ───────────────────────────────────────
NEBIUS_API_KEY=your_nebius_api_key

# ── AI Diagnosis — Sarvam (speech-to-text / text-to-speech) ───────────────────
SARVAM_API_KEY=your_sarvam_api_key

# ── AI Diagnosis — MedGemma via HuggingFace ───────────────────────────────────
HF_INFERENCE_ENDPOINT=https://your-endpoint.huggingface.cloud/v1
HF_API_TOKEN=your_huggingface_token
HF_MODEL=google/medgemma-4b-it
```

> **Note:** AI Diagnosis endpoints return `502` if `SARVAM_API_KEY` or HuggingFace credentials are missing. Other features (repository, OCR, chat) work independently as long as MongoDB and Nebius are configured.

### Run locally

From the project root:

```bash
# Start backend (port 8000)
python -m uvicorn backend.main:app --reload --port 8000

# Start frontend (port 5173) — in a second terminal
cd frontend && npm run dev
```

Open **http://localhost:5173** in your browser. The frontend talks to the API at **http://localhost:8000**.

### Build for production

```bash
cd frontend && npm run build
# Static output in frontend/dist/
```

---

## Application navigation

After login, the sidebar provides:

| Item | Screen |
|------|--------|
| **Dashboard** | Health charts from OCR lab data |
| **Medical Repository** | Hospital folders → vault → report subfolders → documents |
| **Chat** | RAG assistant over uploaded records |
| **AI Diagnosis** | Voice symptom interview + assessment report |
| **Profile** | Patient portfolio (view / edit) |
| **Logout** | Clears session |

---

## API overview

Interactive docs: **http://localhost:8000/docs** (Swagger UI)

### Auth
| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Login, returns JWT |
| GET | `/auth/me` | Current user (requires token) |

### Medical repository
| Method | Path | Description |
|--------|------|-------------|
| GET/POST | `/hospitals/` | List / create hospitals |
| GET/DELETE | `/hospitals/{id}` | Get / delete hospital |
| GET | `/hospitals/{id}/{folder}` | List prescriptions or reports |
| POST | `/hospitals/{id}/{folder}/upload` | Upload document |
| GET/POST | `/hospitals/{id}/reports/folders` | Report subfolders |
| GET/DELETE | `/documents/{id}` | Document metadata / delete |
| GET | `/documents/{id}/preview` | File preview |
| GET | `/documents/{id}/ocr` | OCR structured result |

### Chat & dashboard
| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | RAG chat (SSE stream) |
| POST | `/chat/reembed` | Backfill document embeddings |
| GET | `/dashboard/` | Health chart data |

### Profile
| Method | Path | Description |
|--------|------|-------------|
| GET | `/profile/` | Get patient portfolio |
| PUT | `/profile/` | Save patient portfolio |

### AI Diagnosis
| Method | Path | Description |
|--------|------|-------------|
| POST | `/ai-diagnosis/session/start` | Start interview, return Q1 + TTS audio |
| POST | `/ai-diagnosis/voice/transcribe` | Sarvam speech-to-text |
| POST | `/ai-diagnosis/voice/speak` | Sarvam text-to-speech |
| POST | `/ai-diagnosis/voice/answer` | Submit answer, advance question |
| POST | `/ai-diagnosis/diagnosis/analyze` | MedGemma differential diagnosis |

**Diagnosis response fields:**

```json
{
  "urgency": "emergency | urgent | routine | monitor",
  "clinical_summary": "Plain-language summary",
  "urgency_reason": "Why this priority was assigned",
  "care_timeline": "Immediately | Within 24 hours | This week | Monitor at home",
  "red_flags_detected": ["..."],
  "differentials": [
    { "condition_name": "...", "brief_reason": "...", "confidence": "likely | possible | less likely" }
  ],
  "next_steps": ["..."],
  "when_to_seek_care": "...",
  "reassuring_notes": "...",
  "disclaimer": "...",
  "answers": { "chief_complaint": "...", "...": "..." }
}
```

### Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |

---

## Security & privacy

JeevaKosha is designed with healthcare data protection in mind:

- **Least privilege** — users access only their own hospitals, documents, and profile
- **JWT on protected routes** — unauthenticated requests receive `401`
- **No secrets in repo** — use `.env` and secret managers in production
- **Compliance readiness** — structure supports alignment with applicable regulations; formal compliance requires legal review and operational controls
- **AI disclaimers** — Chat and AI Diagnosis outputs are preliminary and not a substitute for professional medical care

**Do not commit** `.env` files, credentials, or real patient data.

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes with clear messages
4. Open a pull request with a short description and test notes

Please avoid including PHI (protected health information) in issues, PRs, or test fixtures.

---

## Roadmap

- [x] Authentication and user-scoped data
- [x] Hospital / document repository with GridFS
- [x] OCR for Blood Test and Diabetes reports
- [x] Health dashboard with charts
- [x] RAG chatbot with vector search
- [x] Patient profile (view / edit)
- [x] AI Diagnosis voice interview + MedGemma analysis
- [ ] Persistent AI Diagnosis history
- [ ] Additional OCR report types
- [ ] Audit logging
- [ ] OpenAPI export / client SDK
- [ ] FHIR interoperability

---

## License

TBD — add your chosen license (e.g. MIT, Apache 2.0, or proprietary).

---

## Contact

For questions or collaboration, open an issue or contact the maintainers.

---

*JeevaKosha — preserving life's medical story, securely.*
