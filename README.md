---
title: Aaoe Mock Api
emoji: 🔥
colorFrom: indigo
colorTo: indigo
sdk: docker
pinned: false
---

# AI-Assisted Integration Orchestration Engine (Agentic LangChain Version)

An enterprise-grade **design-time AI tool** that reads SOW (Statement of Work) documents — via text, PDF, or DOCX uploads — generates executable JSON configuration blueprints, simulates them against live APIs, and deploys them to a middleware gateway. All with zero manual coding.

---

## Architecture

```
┌──────────────┐        ┌──────────────────┐        ┌──────────────┐
│   Main App   │──────▶ │    Middleware     │──────▶ │   Mock APIs  │
│  (React UI)  │  HTTP  │ (FastAPI Gateway) │  HTTP  │  (FastAPI)   │
│  Port 5173   │        │    Port 8002      │        │  Port 8004   │
└──────────────┘        └──────────────────┘        └──────────────┘
                               ▲
                               │ reads configs from
                               │ /middleware/configs/{tenant_id}/
                               │
                        ┌───────────────────────────┐
                        │      AI Orchestrator      │
                        │ Backend: 8003             │
                        │ Frontend: 5174            │
                        │ (FastAPI + LangChain +    │
                        │ ChromaDB RAG + Any LLM)   │
                        └───────────────────────────┘
```

| Service | Role | Tech | Port |
|---------|------|------|------|
| **Main App** | Test UI — toggles for KYC/GST, sends requests to middleware | React + Vite | 5173 |
| **Middleware** | Runtime gateway — reads JSON configs, transforms data, forwards to APIs | FastAPI | 8002 |
| **AI Orchestrator** | The product — uploads SOW, uses ChromaDB RAG for discovery, generates configs via LangChain, simulates, and deploys | React + FastAPI + LangChain + ChromaDB | 8003 (API), 5174 (UI) |
| **Mock APIs** | Simulates external KYC and GST services | FastAPI | 8004 |

---

## Key Features

- **Multi-format Input**: Paste text directly or upload PDF, DOCX, DOC, TXT, MD, and CSV files — or combine both
- **Multiple File Upload**: Drag-and-drop multiple documents simultaneously — all content is merged and sent to the LLM
- **RAG-Powered Adapter Discovery**: Uses ChromaDB and HuggingFace local embeddings (`all-MiniLM-L6-v2`) for semantic vector search, instantly retrieving the top 3 adapter matches to prevent context window overload.
- **Agentic Generation (LangChain)**: Uses `with_structured_output()` and strict Pydantic models to guarantee 100% compliant JSON blueprint outputs.
- **LangSmith Observability**: Complete tracing of prompt inputs, JSON outputs, tokens, and latency across the pipeline.
- **Mandatory vs Optional Detection**: The AI classifies each integration service as mandatory or optional based on SOW business rules
- **Scope Validation**: The AI rejects out-of-scope or impossible integrations with clear reasons and suggestions
- **Live Simulation**: Test the generated config against real APIs before deploying — see the full request/response pipeline
- **Split Deployment**: Config is saved to middleware (tenant-isolated), and a catalog entry is auto-added to the adapter registry
- **Tenant-Level Config Isolation**: Each tenant gets its own config directory (`middleware/configs/{tenant_id}/`), ensuring complete data isolation
- **API Version Coexistence**: Multiple versions of the same adapter can coexist in the registry — the AI selects the appropriate version
- **Full Audit Trail**: Every action (generate, deploy, reject, reset) is logged with timestamps and tenant context — viewable in the UI
- **Dynamic Registry**: The adapter catalog is built and maintained entirely by the AI — zero manual data entry
- **Switchable LLM**: Default is Ollama (local/free). Can be swapped to Gemini or OpenAI with minimal code changes
- **Demo Reset**: One-click config purge from the Main App for repeatable demos

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **An LLM Backend**: Choose either an **API Key** (OpenAI / NVIDIA NIM) OR a local **Ollama** installation.
- **LangSmith API Key** (optional but highly recommended for tracing)

---

## Project Structure

```
FinSpark_Proto_v1/
├── .env                         # API keys & mock credentials
├── README.md                    # This file
│
├── main-app/                    # Service 1: Test frontend
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── ServiceToggle.jsx
│           ├── RequestButton.jsx
│           └── ResponsePanel.jsx
│
├── middleware/                   # Service 2: Integration Gateway
│   ├── configs/                 # AI-generated config blueprints (tenant-isolated)
│   │   ├── default/             # Default tenant configs
│   │   │   ├── kyc_provider.json
│   │   │   └── gst_service.json
│   │   ├── tenant_a/            # Tenant A configs
│   │   └── tenant_b/            # Tenant B configs
│   └── src/
│       ├── main.py
│       ├── gateway.py           # Includes /simulate endpoint + tenant-aware config loading
│       └── credential_resolver.py
│
├── orchestrator/                # Service 3: AI Orchestrator
│   ├── data/                    # Auto-generated registry + audit log
│   │   ├── integration_registry.json  # Adapter catalog (version coexistence)
│   │   └── audit_log.json             # Full audit trail
│   ├── backend/
│   │   ├── main.py
│   │   ├── llm_engine.py        # LLM integration + scope validation + mandatory/optional detection
│   │   ├── adapter_discovery.py # AI-powered adapter matching from SOW
│   │   ├── registry.py          # Dynamic adapter catalog (multi-version support)
│   │   ├── deployer.py          # Split deployment logic (tenant-isolated)
│   │   ├── audit.py             # Audit trail logging
│   │   └── text_extractor.py    # PDF/DOCX/TXT text extraction
│   └── frontend/
│       └── src/
│           ├── App.jsx
│           └── components/
│               ├── SowInput.jsx          # Text + file upload input
│               ├── BlueprintPreview.jsx   # Editable JSON preview + discovery banner
│               ├── SimulationView.jsx     # Live simulation results
│               ├── StatusBar.jsx          # Ollama + registry status
│               └── AuditTrail.jsx         # Audit trail panel
│
└── mock-apis/                   # Service 4: Mock External Services
    └── src/
        ├── main.py
        ├── kyc_provider.py
        └── gst_service.py
```

---

## Quick Start (Full Demo)

### Step 0: Create the `.env` file

Create a `.env` file in the **project root** (`FinSpark_Proto_v1/.env`):

```env
# LLM Configuration - Choose ONE option based on your backend
# Option A: Cloud API (OpenAI, NVIDIA NIM, etc.)
OPENAI_API_KEY="your_api_key_here"  
NVIDIA_API_KEY="your_nvidia_key_here"

# Option B: Local Models (Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# LangSmith Configuration (MLOps)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
LANGCHAIN_API_KEY="your_langsmith_key_here"
LANGCHAIN_PROJECT="FinSpark_Orchestrator_v2"

# Mock credentials (resolved by middleware at runtime)
KYC_PROVIDER_KEY=dummy-kyc-key-12345
GST_SERVICE_KEY=dummy-gst-key-67890
```

### Step 1: Start Mock APIs (Terminal 1)

```bash
cd mock-apis
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8004
```

Verify: `curl http://localhost:8004/health`

### Step 2: Start Middleware (Terminal 2)

```bash
cd middleware
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8002
```

Verify: `curl http://localhost:8002/health`

### Step 3: Start Orchestrator Backend (Terminal 3)

```bash
cd orchestrator
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8003
```

Verify: `curl http://localhost:8003/health`

### Step 4: Verify AI Connection (Terminal 4)

Depending on your configured backend in `llm_engine.py`:
- **For API Providers** (NVIDIA / OpenAI): Ensure your API key is correctly set in `.env`.
- **For Ollama**: Ensure `ollama serve` is running and your model is pulled.

Verify Orchestrator connection: `curl http://localhost:8003/health/ollama` 
*(Note: This single health endpoint detects whichever API provider you have configured).*

### Step 5: Start Main App Frontend (Terminal 5)

```bash
cd main-app
npm install    # first time only
npm run dev
```

Opens at: **http://localhost:5173**

### Step 6: Start Orchestrator Frontend (Terminal 6)

```bash
cd orchestrator/frontend
npm install    # first time only
npm run dev
```

Opens at: **http://localhost:5174**

---

## Demo Walkthrough

### Flow A: Generate, Simulate & Deploy (Orchestrator)

1. Open **http://localhost:5174** (Orchestrator UI)
2. Check the status bar — the API connection should show as online
3. **Select a tenant** from the dropdown (Default, Tenant A, or Tenant B)
4. **Input** — choose one or more:
   - Click **"Load sample SOW"** for a quick test
   - Paste SOW text directly into the text area
   - Drag-and-drop PDF/DOCX files into the upload zone (multiple files supported)
5. Click **"→ Generate Blueprint"** — wait for the AI (~2–10 seconds)
   - The AI first runs **Adapter Discovery** — checking the registry for existing matching profiles
   - If a match is found (Path A), the AI generates a config tailored to that adapter
   - If no match (Path B), the AI generates both a new adapter profile and the config from scratch
   - The AI classifies the integration as **mandatory** or **optional** based on SOW business rules
6. **Preview** — review the generated Blueprint and Catalog Entry
   - A **discovery banner** shows: 🔗 "Matched Adapter: KYC Provider v1.0 (95%)" or 🆕 "New adapter profile"
   - The blueprint includes a `service_classification` block showing mandatory/optional status
   - Both JSON outputs are editable. Switch between tabs and tweak if needed
7. Click **"▶ Simulate"** — the config is tested against the live mock API
   - See the full pipeline: incoming payload → transformation → API response
8. If satisfied, click **"🚀 Deploy to Middleware"**
9. ✅ Config saved to `middleware/configs/{tenant_id}/`, registry entry created
10. Click **"📋 Show Audit Trail"** to view the logged events

### Flow B: Test the Integration (Main App)

1. Open **http://localhost:5173** (Main App)
2. **Select a tenant** from the dropdown (must match the tenant used during deployment)
3. Toggle **KYC Provider** ON
4. Click **"Send Request"**
5. The request flows: Main App → Middleware (loads tenant-specific config) → Mock KYC API → response displayed
6. Repeat with **GST Service** toggled ON

### Flow C: Test Adapter Discovery (Reuse an Existing Adapter)

After deploying a KYC config (Flow A), test that the AI recognizes it:

1. In the Orchestrator, paste a **different KYC SOW** (different client, same service)
2. Click **"→ Generate Blueprint"**
3. The discovery banner should show: 🔗 **"Matched Adapter: KYC Provider v1.0"** with a confidence %
4. The AI generates a config tailored to the existing adapter rather than creating a new profile

### Flow D: GST Service — Full Demo with Example SOW

This demonstrates the complete pipeline for a new service. Copy-paste this SOW into the Orchestrator:

```
Integration SOW: GST Validation Service

Business Rule:
Before processing a business loan application, validate the applicant's GST registration status.
If gst_status is "INACTIVE" or the registration is not found, reject the application.

API Details:
- Service Name: gst_service
- Version: v1.0
- Endpoint: http://localhost:8004/mock-gst/validate
- Method: POST
- Auth Type: Bearer
- Credential Vault Reference: ENV.GST_SERVICE_KEY

Expected Request Fields:
- gstin (GST Identification Number)
- business_name
- pan_number

Expected Response Fields:
- status
- gst_status (ACTIVE / INACTIVE)
- business_name
- registration_date
- gst_type

Source Data Mapping:
- gstin comes from: $.business_data.gstin
- business_name comes from: $.business_data.businessName
- pan_number comes from: $.business_data.panNumber

Response Logic:
- If $.gst_status == "INACTIVE" then return "REJECTED"
```

**Testing steps:**

1. Open **http://localhost:5174** → paste the SOW above → click **Generate Blueprint**
2. In the **Preview**, verify:
   - `target_url` = `http://localhost:8004/mock-gst/validate`
   - `credential_vault_reference` = `ENV.GST_SERVICE_KEY`
   - `service_name` = `gst_service` in the catalog entry
3. Click **Simulate** → should see a successful response from the mock GST API
4. Click **Deploy** → config saved to `middleware/configs/{tenant_id}/gst_service.json`
5. Open **http://localhost:5173** (Main App) → select the same tenant → toggle **GST Service** ON → click **Send Request**
6. ✅ Full pipeline: Main App → Middleware (reads tenant-specific `gst_service.json`) → Mock GST API → response displayed

### Flow E: Reset Configs (For Repeatable Demos)

1. Open **http://localhost:5173** (Main App)
2. Click **"Reset Configs"** — all deployed config files across all tenants in `middleware/configs/` are deleted
3. This lets you re-run the full demo from scratch without manually deleting files

### Flow F: Test Rejection (Out-of-Scope Documents)

1. In the Orchestrator, paste irrelevant text (e.g., a marketing document or random text)
2. Click **"→ Generate Blueprint"**
3. The AI will return a **rejection** with:
   - **Reason**: Why this can't be an integration
   - **Missing Info**: What specific details are needed
   - **Suggestion**: What the user should provide

### Flow G: Test Failure Cases (Mock APIs)

- In Main App, change the payload's `panNumber` to `"INVALID123"` (in App.jsx) → KYC returns `kyc_verified: false`
- Change the `gstin` to `"00INVALID"` → GST returns `gst_status: INACTIVE`

---

## Supported File Types

| Extension | Handler |
|-----------|---------|
| `.pdf` | PyPDF2 text extraction (page-by-page) |
| `.docx` / `.doc` | python-docx (paragraphs + tables) |
| `.txt` / `.md` / `.csv` | Direct UTF-8 decode |
| Others | Returned as unsupported with error message |

> **Note:** Scanned/image-based PDFs cannot be extracted. A warning is returned if no text is found.

---

## Switching LLM Providers

Because FinSpark uses **LangChain**, switching underlying models takes just two lines of code (no massive rewrites required!).

### Option 1: Ollama (Default — Local, Free)
No changes needed. Ensure `llama3.2` is running via `ollama serve`.

### Option 2: OpenAI / NVIDIA / Gemma (API Based)
Install the LangChain plugin: `pip install langchain-openai`
Add your key to `.env`: `OPENAI_API_KEY="..."`

Change the engine in `llm_engine.py`:
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",          # Or "google/gemma-3n-e4b-it" 
    base_url="https://api.openai.com/v1",  # Or "https://integrate.api.nvidia.com/v1"
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0
)
```

### What Stays the Same Across All Providers

Regardless of which LLM you use, these parts **never change**:
- `SYSTEM_PROMPT` — same instructions for all models (including scope validation)
- `_extract_json_from_response()` — triple-fallback JSON parser
- `_validate_blueprint()` / `_validate_catalog_entry()` — structural validators
- `text_extractor.py` — file processing is LLM-agnostic
- `check_ollama_status()` — keep it; it just won't be used for non-Ollama providers

---

## API Reference

### Mock APIs (Port 8004)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/mock-kyc/verify` | KYC identity verification |
| POST | `/mock-gst/validate` | GST number validation |

### Middleware (Port 8002)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/gateway/execute/{service_name}?tenant_id=` | Execute integration via deployed config (tenant-aware) |
| POST | `/api/gateway/simulate` | Simulate integration with inline config |

### Orchestrator (Port 8003)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ollama` | Ollama + model status |
| GET | `/api/orchestrator/registry` | List all adapters in catalog |
| GET | `/api/orchestrator/registry/{name}` | Lookup specific adapter |
| GET | `/api/orchestrator/registry/{name}/versions` | List all versions of an adapter |
| GET | `/api/orchestrator/audit?limit=50` | View audit trail (recent events) |
| POST | `/api/orchestrator/generate` | Generate blueprint from SOW text (includes adapter discovery, accepts `tenant_id`) |
| POST | `/api/orchestrator/generate-from-upload` | Generate blueprint from uploaded files + text (includes adapter discovery, accepts `tenant_id`) |
| POST | `/api/orchestrator/deploy` | Deploy blueprint + registry entry (tenant-isolated) |
| POST | `/api/orchestrator/generate-and-deploy` | One-shot generate + deploy (tenant-isolated) |
| POST | `/api/orchestrator/reset-configs` | Delete deployed configs (optional `tenant_id` filter) |

---

## Adding More Mock APIs

You can add any number of mock external services. Here's a step-by-step example adding a **Credit Bureau API**.

### Step 1: Create the Mock Endpoint

Create a new file `mock-apis/src/credit_bureau.py`:

```python
import uuid

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class CreditRequest(BaseModel):
    pan_number: str
    full_name: str
    date_of_birth: Optional[str] = None


@router.post("/mock-credit-bureau/check")
def check_credit(request: CreditRequest):
    """
    Mock credit score check.
    - PAN starting with 'BAD' → low score (reject)
    - Otherwise → good score (approve)
    """
    is_bad = request.pan_number.upper().startswith("BAD")

    if is_bad:
        return {
            "status": "completed",
            "credit_score": 320,
            "risk_category": "HIGH",
            "loan_eligible": False,
            "report_id": str(uuid.uuid4()),
        }

    return {
        "status": "completed",
        "credit_score": 745,
        "risk_category": "LOW",
        "loan_eligible": True,
        "report_id": str(uuid.uuid4()),
    }
```

### Step 2: Register the Router

In `mock-apis/src/main.py`, add:

```python
from .credit_bureau import router as credit_router

app.include_router(credit_router)
```

### Step 3: Add a Credential to `.env`

```env
CREDIT_BUREAU_KEY=dummy-credit-key-99999
```

### Step 4: Write an SOW Document

Create a text file or paste this into the orchestrator:

```
Integration SOW: Credit Bureau

Business Rule:
Before approving a loan, check the applicant's credit score via the Credit Bureau API.
If the credit score is below 500 or loan_eligible is false, reject the loan application.

API Details:
- Service Name: Credit Bureau
- Version: v1.0
- Endpoint: http://localhost:8004/mock-credit-bureau/check
- Method: POST
- Expected Request Fields: pan_number, full_name, date_of_birth
- Expected Response Fields: status, credit_score, risk_category, loan_eligible, report_id

Security:
- Auth Type: Bearer
- Credential Vault Reference: ENV.CREDIT_BUREAU_KEY

Source Data Mapping:
- pan_number comes from: $.applicant_data.panNumber
- full_name comes from: $.applicant_data.firstName + ' ' + $.applicant_data.lastName
- date_of_birth comes from: $.applicant_data.dateOfBirth
```

### Step 5: Generate & Deploy

1. Paste the SOW into the Orchestrator UI (or upload as a file)
2. Click **Generate Blueprint**
3. **Simulate** to verify
4. **Deploy** — config is saved to `middleware/configs/{tenant_id}/credit_bureau.json`

### Step 6: (Optional) Add to Main App

If you want the new API in the Main App's toggle UI, add a new toggle in `main-app/src/App.jsx` following the same pattern as KYC/GST, and add a sample payload for simulation in the orchestrator's `App.jsx` `SAMPLE_PAYLOADS` object.

### Pattern Summary

| What | Where to Add |
|------|-------------|
| Mock endpoint | `mock-apis/src/{service_name}.py` |
| Register router | `mock-apis/src/main.py` |
| Credential | `.env` at project root |
| SOW document | Paste text or upload PDF/DOCX in orchestrator UI |
| Config blueprint | Auto-generated by AI and deployed to `middleware/configs/{tenant_id}/` |
| Registry entry | Auto-created by AI in `orchestrator/data/integration_registry.json` |
| Audit log | Auto-recorded in `orchestrator/data/audit_log.json` |
| Main App toggle | (Optional) `main-app/src/App.jsx` |

> **The key insight:** You only write the mock endpoint by hand. The middleware config and registry entry are generated and deployed entirely by the AI orchestrator from your SOW document.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Cannot connect to AI Backend` | For API providers, check your API key in `.env`. For local, run `ollama serve` |
| `Model not found` | For API providers, verify the exact model string. For Ollama, run `ollama pull <model>` |
| `OpenAIError: API key must be set` | Ensure your `.env` contains the correct key and the FastAPI server was restarted. |
| CORS errors in browser | Make sure all backends have `allow_origins=["*"]` |
| `Credential not found` | Check `.env` file exists in project root with the right keys |
| Middleware returns 404 | Config file missing in `middleware/configs/{tenant_id}/`. Deploy from orchestrator first, and ensure the same tenant is selected in both UIs |
| LLM returns invalid JSON | Try a larger model (e.g., `llama3:70b`) or use Gemini/GPT |
| PDF extraction empty | The PDF may be scanned/image-based. Use a text-based PDF or DOCX instead |
| `Integration Rejected` | The uploaded document doesn't describe a valid API integration. Check the rejection message for details |
| Simulation fails | Ensure the middleware (port 8002) and mock APIs (port 8004) are both running |
| File upload not working | Ensure `python-multipart` is installed: `pip install python-multipart` |

---

## License

Built for the FinSpark Hackathon.
