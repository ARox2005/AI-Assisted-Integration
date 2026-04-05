# FinSpark — AI-Assisted Integration Orchestration Engine

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
                               │ /middleware/configs/
                               │
                        ┌──────────────────┐
                        │  AI Orchestrator  │
                        │ Backend: 8003     │
                        │ Frontend: 5174    │
                        │ (React + FastAPI  │
                        │  + Ollama LLM)    │
                        └──────────────────┘
```

| Service | Role | Tech | Port |
|---------|------|------|------|
| **Main App** | Test UI — toggles for KYC/GST, sends requests to middleware | React + Vite | 5173 |
| **Middleware** | Runtime gateway — reads JSON configs, transforms data, forwards to APIs | FastAPI | 8002 |
| **AI Orchestrator** | The product — uploads SOW (text/PDF/DOCX), generates configs via LLM, simulates, and deploys | React + FastAPI + Ollama | 8003 (API), 5174 (UI) |
| **Mock APIs** | Simulates external KYC and GST services | FastAPI | 8004 |

---

## Key Features

- **Multi-format Input**: Paste text directly or upload PDF, DOCX, DOC, TXT, MD, and CSV files — or combine both
- **Multiple File Upload**: Drag-and-drop multiple documents simultaneously — all content is merged and sent to the LLM
- **AI-Powered Adapter Discovery**: Before generating a new config, the AI checks the adapter registry for existing profiles that match the SOW — avoiding duplicates and reusing existing adapters (Path A: existing, Path B: new)
- **AI-Generated Configs**: The LLM reads SOW documents and produces middleware-ready JSON blueprints (no manual coding)
- **Scope Validation**: The AI rejects out-of-scope or impossible integrations with clear reasons and suggestions
- **Live Simulation**: Test the generated config against real APIs before deploying — see the full request/response pipeline
- **Split Deployment**: Config is saved to middleware, and a catalog entry is auto-added to the adapter registry
- **Dynamic Registry**: The adapter catalog is built and maintained entirely by the AI — zero manual data entry
- **Switchable LLM**: Default is Ollama (local/free). Can be swapped to Gemini or OpenAI with minimal code changes
- **Demo Reset**: One-click config purge from the Main App for repeatable demos

---

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **Ollama** installed and running ([ollama.com](https://ollama.com))
- A pulled model (e.g., `ollama pull llama3`)

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
│   ├── configs/                 # AI-generated config blueprints
│   │   ├── kyc_provider.json
│   │   └── gst_service.json
│   └── src/
│       ├── main.py
│       ├── gateway.py           # Includes /simulate endpoint
│       └── credential_resolver.py
│
├── orchestrator/                # Service 3: AI Orchestrator
│   ├── data/                    # Auto-generated registry (created by AI)
│   ├── backend/
│   │   ├── main.py
│   │   ├── llm_engine.py        # LLM integration + scope validation
│   │   ├── adapter_discovery.py # AI-powered adapter matching from SOW
│   │   ├── registry.py          # Dynamic adapter catalog
│   │   ├── deployer.py          # Split deployment logic
│   │   └── text_extractor.py    # PDF/DOCX/TXT text extraction
│   └── frontend/
│       └── src/
│           ├── App.jsx
│           └── components/
│               ├── SowInput.jsx          # Text + file upload input
│               ├── BlueprintPreview.jsx   # Editable JSON preview + discovery banner
│               ├── SimulationView.jsx     # Live simulation results
│               └── StatusBar.jsx          # Ollama + registry status
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
# LLM Configuration (Ollama is default — no key needed)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

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

### Step 4: Start Ollama (Terminal 4)

```bash
ollama serve
```

> If Ollama is already running in the system tray, skip this step.

Verify: `curl http://localhost:8003/health/ollama`

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
2. Check the status bar — Ollama should show as online
3. **Input** — choose one or more:
   - Click **"Load sample SOW"** for a quick test
   - Paste SOW text directly into the text area
   - Drag-and-drop PDF/DOCX files into the upload zone (multiple files supported)
4. Click **"→ Generate Blueprint"** — wait for Ollama (~10–60 seconds)
   - The AI first runs **Adapter Discovery** — checking the registry for existing matching profiles
   - If a match is found (Path A), the AI generates a config tailored to that adapter
   - If no match (Path B), the AI generates both a new adapter profile and the config from scratch
5. **Preview** — review the generated Blueprint and Catalog Entry
   - A **discovery banner** shows: 🔗 "Matched Adapter: KYC Provider v1.0 (95%)" or 🆕 "New adapter profile"
   - Both JSON outputs are editable. Switch between tabs and tweak if needed
6. Click **"▶ Simulate"** — the config is tested against the live mock API
   - See the full pipeline: incoming payload → transformation → API response
7. If satisfied, click **"🚀 Deploy to Middleware"**
8. ✅ Config saved to `middleware/configs/`, registry entry created

### Flow B: Test the Integration (Main App)

1. Open **http://localhost:5173** (Main App)
2. Toggle **KYC Provider** ON
3. Click **"Send Request"**
4. The request flows: Main App → Middleware → Mock KYC API → response displayed
5. Repeat with **GST Service** toggled ON

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
4. Click **Deploy** → config saved to `middleware/configs/gst_service.json`
5. Open **http://localhost:5173** (Main App) → toggle **GST Service** ON → click **Send Request**
6. ✅ Full pipeline: Main App → Middleware (reads `gst_service.json`) → Mock GST API → response displayed

### Flow E: Reset Configs (For Repeatable Demos)

1. Open **http://localhost:5173** (Main App)
2. Click **"Reset Configs"** — all deployed config files in `middleware/configs/` are deleted
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

The orchestrator defaults to **Ollama** (local). You can switch to any other provider by modifying `orchestrator/backend/llm_engine.py`.

### Option 1: Ollama (Default — Local, Free)

No changes needed. Just ensure Ollama is running:

```bash
ollama serve
ollama pull llama3    # or any model you prefer
```

Set in `.env`:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### Option 2: Google Gemini

1. **Get an API key** from [Google AI Studio](https://aistudio.google.com/apikey)

2. **Install the SDK:**
   ```bash
   cd orchestrator
   pip install google-generativeai
   ```

3. **Add to `.env`:**
   ```env
   GEMINI_API_KEY=your-gemini-api-key-here
   ```

4. **Replace the `process_sow` function** in `llm_engine.py`:

   ```python
   import google.generativeai as genai

   genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

   async def process_sow(sow_text: str, model: Optional[str] = None) -> dict:
       model_name = model or "gemini-2.0-flash"

       llm = genai.GenerativeModel(
           model_name=model_name,
           system_instruction=SYSTEM_PROMPT,
           generation_config=genai.GenerationConfig(
               response_mime_type="application/json",
               temperature=0.1,
           ),
       )

       user_prompt = f"""Read the following SOW document and generate the blueprint and catalog_entry.

   --- START OF SOW DOCUMENT ---
   {sow_text}
   --- END OF SOW DOCUMENT ---

   Return ONLY a JSON object with "blueprint" and "catalog_entry" keys."""

       try:
           response = llm.generate_content(user_prompt)
           raw_content = response.text
       except Exception as e:
           return {
               "success": False,
               "error": f"Gemini API error: {str(e)}",
               "blueprint": None, "catalog_entry": None, "raw_response": None,
           }

       # Use the same extraction + validation logic below...
       parsed = _extract_json_from_response(raw_content)
       # (keep all existing validation code unchanged)
   ```

   > **Key advantage:** Gemini supports `response_mime_type="application/json"` which forces JSON output natively, just like Ollama's `"format": "json"`.

### Option 3: OpenAI (GPT-4o / GPT-4o-mini)

1. **Get an API key** from [platform.openai.com](https://platform.openai.com/api-keys)

2. **Install the SDK:**
   ```bash
   cd orchestrator
   pip install openai
   ```

3. **Add to `.env`:**
   ```env
   OPENAI_API_KEY=sk-your-openai-key-here
   ```

4. **Replace the `process_sow` function** in `llm_engine.py`:

   ```python
   from openai import AsyncOpenAI

   client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

   async def process_sow(sow_text: str, model: Optional[str] = None) -> dict:
       model_name = model or "gpt-4o-mini"

       user_prompt = f"""Read the following SOW document and generate the blueprint and catalog_entry.

   --- START OF SOW DOCUMENT ---
   {sow_text}
   --- END OF SOW DOCUMENT ---

   Return ONLY a JSON object with "blueprint" and "catalog_entry" keys."""

       try:
           response = await client.chat.completions.create(
               model=model_name,
               messages=[
                   {"role": "system", "content": SYSTEM_PROMPT},
                   {"role": "user", "content": user_prompt},
               ],
               response_format={"type": "json_object"},
               temperature=0.1,
               max_tokens=4096,
           )
           raw_content = response.choices[0].message.content
       except Exception as e:
           return {
               "success": False,
               "error": f"OpenAI API error: {str(e)}",
               "blueprint": None, "catalog_entry": None, "raw_response": None,
           }

       # Use the same extraction + validation logic below...
       parsed = _extract_json_from_response(raw_content)
       # (keep all existing validation code unchanged)
   ```

   > **Key advantage:** OpenAI's `response_format={"type": "json_object"}` also forces JSON output.

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
| POST | `/api/gateway/execute/{service_name}` | Execute integration via deployed config |
| POST | `/api/gateway/simulate` | Simulate integration with inline config |

### Orchestrator (Port 8003)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/ollama` | Ollama + model status |
| GET | `/api/orchestrator/registry` | List all adapters in catalog |
| GET | `/api/orchestrator/registry/{name}` | Lookup specific adapter |
| POST | `/api/orchestrator/generate` | Generate blueprint from SOW text (includes adapter discovery) |
| POST | `/api/orchestrator/generate-from-upload` | Generate blueprint from uploaded files + text (includes adapter discovery) |
| POST | `/api/orchestrator/deploy` | Deploy blueprint + registry entry |
| POST | `/api/orchestrator/generate-and-deploy` | One-shot generate + deploy |
| POST | `/api/orchestrator/reset-configs` | Delete all deployed configs from middleware (demo utility) |

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
4. **Deploy** — config is saved to `middleware/configs/credit_bureau.json`

### Step 6: (Optional) Add to Main App

If you want the new API in the Main App's toggle UI, add a new toggle in `main-app/src/App.jsx` following the same pattern as KYC/GST, and add a sample payload for simulation in the orchestrator's `App.jsx` `SAMPLE_PAYLOADS` object.

### Pattern Summary

| What | Where to Add |
|------|-------------|
| Mock endpoint | `mock-apis/src/{service_name}.py` |
| Register router | `mock-apis/src/main.py` |
| Credential | `.env` at project root |
| SOW document | Paste text or upload PDF/DOCX in orchestrator UI |
| Config blueprint | Auto-generated by AI and deployed to `middleware/configs/` |
| Registry entry | Auto-created by AI in `orchestrator/data/integration_registry.json` |
| Main App toggle | (Optional) `main-app/src/App.jsx` |

> **The key insight:** You only write the mock endpoint by hand. The middleware config and registry entry are generated and deployed entirely by the AI orchestrator from your SOW document.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Cannot connect to Ollama` | Run `ollama serve` or check if it's in system tray |
| `Model not found` | Run `ollama pull llama3` (or your chosen model) |
| CORS errors in browser | Make sure all backends have `allow_origins=["*"]` |
| `Credential not found` | Check `.env` file exists in project root with the right keys |
| Middleware returns 404 | Config file missing in `middleware/configs/`. Deploy from orchestrator first |
| LLM returns invalid JSON | Try a larger model (e.g., `llama3:70b`) or use Gemini/GPT |
| PDF extraction empty | The PDF may be scanned/image-based. Use a text-based PDF or DOCX instead |
| `Integration Rejected` | The uploaded document doesn't describe a valid API integration. Check the rejection message for details |
| Simulation fails | Ensure the middleware (port 8002) and mock APIs (port 8004) are both running |
| File upload not working | Ensure `python-multipart` is installed: `pip install python-multipart` |

---

## License

Built for the FinSpark Hackathon.
