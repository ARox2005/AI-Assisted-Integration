Here is the ultimate **"Project Context Document"** designed specifically for an AI coding agent like Claude Opus to read, understand, and immediately start scaffolding your prototype. 

Save the text below as a markdown file (e.g., `FINSPARK_PROJECT_CONTEXT.md`) in your working directory. When you initialize Claude, you can simply say: *"Read `FINSPARK_PROJECT_CONTEXT.md` and let's start building Phase 1."*

***

# FINSPARK HACKATHON: PROJECT CONTEXT & ARCHITECTURE

## 1. Project Overview
**Name:** AI-Assisted Integration Orchestration Engine
**Theme:** Configure Enterprise Integrations from Intent, Not Code
**Objective:** Build an enterprise-grade "Design-Time" AI tool that reads Business Requirement Documents (BRDs) and API Specifications, and automatically generates executable JSON configuration files (Blueprints). These files configure an existing enterprise middleware to connect a core lending platform to 3rd-party APIs (KYC, Fraud, GST) with zero manual coding.

## 2. Core Architectural Philosophy (Strict Constraints)
* **Design-Time vs. Run-Time:** The AI Orchestrator strictly operates at *design-time*. It generates configuration files and deploys them. It **must never** sit in the middle of live customer traffic.
* **Zero Impact to Core Codebase:** The Main Application remains completely ignorant of external APIs. It only talks to the Middleware.
* **Strict Credential Vaulting:** The AI-generated configuration files **must never** contain plain-text passwords or API keys. They must use string references (e.g., `ENV.EXPERIAN_PROD_KEY`) that the middleware resolves at runtime.
* **No Hallucinations:** The AI must use a Retrieval-Augmented Generation (RAG) approach, pulling known system variables from an internal `integration_registry.json` to ensure exact variable matching.

## 3. System Architecture (The 4-Service Model)
The prototype will be divided into four distinct lightweight services to simulate a massive enterprise environment. *Note to Agent: Default to React for frontends and Python (FastAPI) for backends for rapid prototyping.*

### Service 1: The Main App (Client Frontend)
* **Role:** Simulates the enterprise's core lending software.
* **Tech:** React.
* **Functionality:** A simple UI with a "Submit Loan Application" button. It sends a static, generic JSON payload containing applicant data to the Middleware.

### Service 2: The Integration Gateway (Middleware)
* **Role:** The execution engine handling live traffic.
* **Tech:** Python (FastAPI).
* **Functionality:** * Hosts a generic endpoint (e.g., `/api/gateway/execute/{service_name}`).
    * Reads the corresponding AI-generated JSON configuration file from its local `/configs` directory.
    * Transforms the incoming data from Service 1 according to the config rules.
    * Injects the dummy security credentials.
    * Forwards the translated request to Service 4 (Mock APIs) and returns the response.

### Service 3: The AI Orchestrator (The Hackathon Product)
* **Role:** The AI-powered design tool for implementation engineers.
* **Tech:** React (UI) + Python FastAPI (Backend) + LLM Integration.
* **Functionality:**
    * **UI:** Allows dual-upload of a Business Requirement text and an API Sample Response.
    * **Registry:** Maintains a local `integration_registry.json` mapping human-readable API names to secure `.env` references.
    * **AI Engine:** Constructs a strict prompt combining the BRD, API Sample, and Registry data to generate a JSON configuration file.
    * **Deployment:** Saves the generated `.json` file directly into Service 2's `/configs` directory.

### Service 4: The Mock APIs (External World)
* **Role:** Simulates 3rd-party enterprise services.
* **Tech:** Python (FastAPI) or simple Node.js Express.
* **Functionality:** Dumb endpoints that accept specific JSON payloads and return static success/failure JSON responses (e.g., `/mock-experian/v2/verify`, `/mock-lexisnexis/fraud-score`).

## 4. Critical Data Schemas

### A. The Integration Registry (`integration_registry.json`)
This file lives in Service 3. The orchestrator references this to inject secure keys into the LLM prompt.
```json
{
  "adapters": [
    {
      "name": "LexisNexis Fraud Engine",
      "version": "v2.0",
      "credential_reference": "ENV.LEXISNEXIS_PROD_KEY",
      "target_endpoint": "http://localhost:8004/mock-lexisnexis/fraud-score"
    }
  ]
}
```

### B. The AI-Generated Configuration Blueprint
This is the required output format from the LLM. It is saved into Service 2's directory.
```json
{
  "integration_metadata": {
    "target_system": "LexisNexis Fraud Engine",
    "api_version": "v2.0"
  },
  "security_config": {
    "auth_type": "Bearer",
    "credential_vault_reference": "ENV.LEXISNEXIS_PROD_KEY",
    "target_url": "http://localhost:8004/mock-lexisnexis/fraud-score"
  },
  "schema_transformation_rules": {
    "request_mapping": {
      "customer_first_name": "$.applicant_data.firstName",
      "customer_dob": "$.applicant_data.dateOfBirth | format: YYYY-MM-DD"
    },
    "response_logic": "if $.response.fraud_score > 80 then return 'REJECT_LOAN' else return 'APPROVE'"
  }
}
```

## 5. Development Roadmap: Phase 1 (The Fraud Engine Pipeline)
**Agent Instructions for First Prototype:**
1.  **Initialize Monorepo:** Set up a workspace with 4 folders (`main-app`, `middleware`, `orchestrator`, `mock-apis`).
2.  **Scaffold Mock API:** Create a fast Python endpoint for LexisNexis that returns a fraud score of 85.
3.  **Scaffold Middleware:** Create a Python API that can read a local `.json` config file and make outbound HTTP requests.
4.  **Scaffold Orchestrator Backend:** Build the LLM prompt chain. It must take a string of business requirements, a string of an API JSON response, lookup the registry, and output the blueprint schema exactly as defined above.
5.  **Connect & Test:** Verify the flow. Main App -> Middleware (using hand-written config) -> Mock API. Once verified, replace the hand-written config with the LLM-generated config.