import json
import os
import re
from typing import Optional

import httpx

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

# ──────────────────────────────────────────────
# System Prompt
# ──────────────────────────────────────────────

# SYSTEM_PROMPT = """You are an enterprise integration architect AI. Your job is to read a Statement of Work (SOW) document and generate two JSON outputs.
# You MUST return ONLY a single valid JSON object with exactly two keys: "blueprint" and "catalog_entry". No explanations, no markdown, no extra text.
# ---
# **SCOPE CHECK — IMPORTANT**
# Before generating, evaluate whether the SOW describes a valid, achievable API integration. If the document:
# - Does NOT describe an API integration (e.g., it's a marketing document, a legal contract, or irrelevant text)
# - Contains contradictory or impossible requirements
# - Lacks the minimum information needed (no endpoint, no field mappings, no clear target system)
# Then return this rejection response instead:
# {
#   "blueprint": null,
#   "catalog_entry": null,
#   "rejection": {
#     "reason": "<Clear explanation of why this cannot be turned into an integration>",
#     "missing_info": ["<list of specific missing pieces, e.g., 'endpoint URL', 'field mapping'>"],
#     "suggestion": "<What the user should provide to make this work>"
#   }
# }
# Only reject if the document genuinely cannot produce a valid integration. If you can reasonably infer missing details, proceed with generation.
# ---

# **Output 1: "blueprint"**
# This is an executable configuration file for a middleware gateway. It MUST follow this exact schema:
# {
#   "integration_metadata": {
#     "target_system": "<Name of the external API/service>",
#     "api_version": "<Version from the SOW>"
#   },
#   "security_config": {
#     "auth_type": "<Bearer | ApiKey | Basic>",
#     "credential_vault_reference": "<ENV.VARIABLE_NAME — extract from SOW>",
#     "target_url": "<Full endpoint URL from the SOW>"
#   },
#   "schema_transformation_rules": {
#     "request_mapping": {
#       "<target_field>": "<JSONPath expression like $.source_object.field_name>"
#     },
#     "response_logic": "<Business rule from SOW, e.g., if $.field > value then return 'ACTION'>"
#   }
# }
# Rules for the blueprint:
# - credential_vault_reference MUST start with "ENV." — never put actual keys or passwords.
# - request_mapping values MUST use JSONPath notation starting with "$."
# - For field concatenation, use: "$.obj.field1 + ' ' + $.obj.field2"
# - response_logic should be a human-readable conditional from the SOW's business rules.
# ---
# **Output 2: "catalog_entry"**
# This is a metadata record for the adapter registry. It MUST follow this schema:
# {
#   "name": "<Human-readable name of the target system>",
#   "version": "<API version>",
#   "description": "<One-line description of what this integration does>",
#   "credential_reference": "<Same ENV.XXX as in the blueprint>",
#   "target_endpoint": "<Same URL as in the blueprint>",
#   "expected_request_fields": ["<list of field names the target API expects>"],
#   "expected_response_fields": ["<list of field names the target API returns>"]
# }
# ---
# **Your complete response must be exactly this structure, nothing else:**

# Success case:
# {
#   "blueprint": { ... },
#   "catalog_entry": { ... }
# }

# Rejection case:
# {
#   "blueprint": null,
#   "catalog_entry": null,
#   "rejection": { ... }
# }
# """

SYSTEM_PROMPT = """You are an enterprise integration architect AI. Your job is to read a Statement of Work (SOW) document and generate configuration JSON for a middleware gateway.

You operate in two modes depending on context provided:

**MODE A — Existing Adapter Profile Provided**
When you receive an "MATCHED ADAPTER PROFILE" section, an existing adapter has been identified. Your job is to generate ONLY the client-level configuration (blueprint) that maps the SOW's data fields into the adapter's expected schema.
- Use the adapter's target_endpoint, credential_reference, and mandatory_fields as your template.
- The catalog_entry should match the existing adapter (same name, same version).
- Focus on generating precise field mappings from the SOW's source data to the adapter's mandatory_fields.

**MODE B — No Adapter Match (New Profile)**
When no matched adapter is provided, you must generate BOTH:
- A blueprint (the client configuration)
- A catalog_entry (the base API profile for the registry — so future SOWs can match against it)
Extract all technical details (endpoint, auth, fields) directly from the SOW.

---
**SCOPE CHECK — IMPORTANT**
Before generating, evaluate whether the SOW describes a valid, achievable API integration. If the document:
- Does NOT describe an API integration (e.g., it's a marketing document, a legal contract, or irrelevant text)
- Contains contradictory or impossible requirements
- Lacks the minimum information needed (no endpoint, no field mappings, no clear target system)
Then return this rejection response instead:
{
  "blueprint": null,
  "catalog_entry": null,
  "rejection": {
    "reason": "<Clear explanation of why this cannot be turned into an integration>",
    "missing_info": ["<list of specific missing pieces, e.g., 'endpoint URL', 'field mapping'>"],
    "suggestion": "<What the user should provide to make this work>"
  }
}
Only reject if the document genuinely cannot produce a valid integration. If you can reasonably infer missing details, proceed with generation.
---

**Output 1: "blueprint"**
This is an executable configuration file for a middleware gateway. It MUST follow this exact schema:
{
  "integration_metadata": {
    "target_system": "<Name of the external API/service>",
    "api_version": "<Version from the SOW>"
  },
  "security_config": {
    "auth_type": "<Bearer | ApiKey | Basic>",
    "credential_vault_reference": "<ENV.VARIABLE_NAME — extract from SOW>",
    "target_url": "<Full endpoint URL from the SOW>"
  },
  "schema_transformation_rules": {
    "request_mapping": {
      "<target_field>": "<JSONPath expression like $.source_object.field_name>"
    },
    "response_logic": "<Business rule from SOW, e.g., if $.field > value then return 'ACTION'>"
  }
}
Rules for the blueprint:
- credential_vault_reference MUST start with "ENV." — never put actual keys or passwords.
- request_mapping values MUST use JSONPath notation starting with "$."
- For field concatenation, use: "$.obj.field1 + ' ' + $.obj.field2"
- response_logic should be a human-readable conditional from the SOW's business rules.
---
**Output 2: "catalog_entry"**
This is the adapter's Technical Profile for the registry. It MUST follow this schema:
{
  "name": "<Human-readable name of the target system>",
  "service_name": "<lowercase_snake_case config filename from the SOW, e.g., kyc_provider, gst_service. This becomes the config file name.>",
  "version": "<API version>",
  "description": "<One-line description of what this integration does>",
  "category": "<Category: e.g., Identity Verification, Payment Gateway, Credit Bureau>",
  "provider": "<Provider name: e.g., Experian, Razorpay>",
  "supported_actions": ["<list of actions: e.g., Verify Identity, Check Credit Score>"],
  "credential_reference": "<Same ENV.XXX as in the blueprint>",
  "target_endpoint": "<Same URL as in the blueprint>",
  "technical_interface": {
    "protocol": "<REST | SOAP | GraphQL>",
    "method": "<POST | GET | PUT>",
    "authentication_methods": ["<Bearer | ApiKey | OAuth2 | Basic>"]
  },
  "data_schema": {
    "mandatory_fields": ["<fields the API requires>"],
    "optional_fields": ["<fields the API can accept but doesn't require>"],
    "output_structure": ["<fields the API returns>"]
  },
  "expected_request_fields": ["<same as mandatory_fields — for backward compatibility>"],
  "expected_response_fields": ["<same as output_structure — for backward compatibility>"]
}
---
**Your complete response must be exactly this structure, nothing else:**

Success case:
{
  "blueprint": { ... },
  "catalog_entry": { ... }
}

Rejection case:
{
  "blueprint": null,
  "catalog_entry": null,
  "rejection": { ... }
}
"""

# ──────────────────────────────────────────────
# JSON Extraction Helpers
# ──────────────────────────────────────────────

def _extract_json_from_response(text: str) -> Optional[dict]:
    """
    Extracts a JSON object from LLM output.
    Handles cases where the LLM wraps JSON in markdown code blocks
    or adds extra text around it.
    """

    # Strategy 1: Try direct parse (best case — clean output)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code block (```json ... ```)
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find the outermost { ... } braces
    brace_start = text.find("{")
    brace_end = text.rfind("}")
    if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
        try:
            return json.loads(text[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass
    return None

def _validate_blueprint(blueprint: dict) -> Optional[str]:
    """Validate that the blueprint has the required structure."""
    required_keys = {"integration_metadata", "security_config", "schema_transformation_rules"}
    missing = required_keys - set(blueprint.keys())
    if missing:
        return f"Blueprint missing keys: {', '.join(missing)}"

    security = blueprint.get("security_config", {})
    if not security.get("credential_vault_reference", "").startswith("ENV."):
        return "Blueprint credential_vault_reference must start with 'ENV.'"
    if not security.get("target_url"):
        return "Blueprint missing target_url in security_config"
    return None

def _validate_catalog_entry(entry: dict) -> Optional[str]:
    """Validate that the catalog entry has the required fields."""
    required = {"name", "version", "credential_reference", "target_endpoint"}
    missing = required - set(entry.keys())
    if missing:
        return f"Catalog entry missing fields: {', '.join(missing)}"

    if not entry.get("credential_reference", "").startswith("ENV."):
        return "Catalog entry credential_reference must start with 'ENV.'"

    return None

# ──────────────────────────────────────────────
# Core LLM Engine
# ──────────────────────────────────────────────

# async def process_sow(sow_text: str, model: Optional[str] = None) -> dict:
async def process_sow(sow_text: str, model: Optional[str] = None, matched_adapter: Optional[dict] = None) -> dict:
    """
    Process a Statement of Work document through the LLM.
    Args:
        sow_text: The full SOW document text.
        model: Override the default Ollama model.
        matched_adapter: If adapter discovery found a match, pass the adapter profile here.
                         The LLM will generate a config targeted to this adapter (Path A).
                         If None, the LLM generates both profile + config from scratch (Path B).
    Returns:
        dict with keys:
        - success: bool
        - blueprint: dict (the middleware config)
        - catalog_entry: dict (the registry entry)
        - error: str (if failed)
        - raw_response: str (the raw LLM output, for debugging)
    """
    model_name = model or OLLAMA_MODEL

    # ── Build the prompt ──
    # user_prompt = f"""Read the following Statement of Work (SOW) document carefully and generate the blueprint and catalog_entry JSON objects as instructed.
    if matched_adapter:
        # Path A: Existing adapter found
        adapter_profile = matched_adapter.get("profile", matched_adapter)
        user_prompt = f"""An existing adapter profile was found in the registry that matches this SOW.

--- MATCHED ADAPTER PROFILE ---
{json.dumps(adapter_profile, indent=2)}
--- END ADAPTER PROFILE ---

Generate the client-level blueprint configuration that maps the SOW's data fields into this adapter's schema.
The catalog_entry should reflect this existing adapter (same name, version).

--- START OF SOW DOCUMENT ---
{sow_text}
--- END OF SOW DOCUMENT ---

Remember: Return ONLY a single JSON object with "blueprint" and "catalog_entry" keys. No other text."""

    else:
        # Path B: No adapter match — generate both profile + config
        user_prompt = f"""No existing adapter matches this SOW. Generate both:
1. A new adapter base profile (catalog_entry) for the registry
2. A client blueprint configuration for the middleware

Read the following Statement of Work (SOW) document carefully and extract all technical details.

--- START OF SOW DOCUMENT ---
{sow_text}
--- END OF SOW DOCUMENT ---

Remember: Return ONLY a single JSON object with "blueprint" and "catalog_entry" keys. No other text."""

    # ── Call Ollama ──
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.1,      # Low temperature for deterministic output
            "num_predict": 4096,     # Enough tokens for the JSON response
        },
    }

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json=payload,
            )
            response.raise_for_status()
    except httpx.ConnectError:
        return {
            "success": False,
            "error": f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. Is Ollama running? Try: ollama serve",
            "blueprint": None,
            "catalog_entry": None,
            "raw_response": None,
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "error": f"Ollama returned HTTP {e.response.status_code}: {e.response.text}",
            "blueprint": None,
            "catalog_entry": None,
            "raw_response": None,
        }
    except httpx.ReadTimeout:
        return {
            "success": False,
            "error": "Ollama request timed out after 120 seconds. The model may be too slow or the SOW too long.",
            "blueprint": None,
            "catalog_entry": None,
            "raw_response": None,
        }

    # ── Parse Ollama response ──
    try:
        ollama_data = response.json()
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Failed to parse Ollama response as JSON.",
            "blueprint": None,
            "catalog_entry": None,
            "raw_response": response.text,
        }

    raw_content = ollama_data.get("message", {}).get("content", "")

    if not raw_content.strip():
        return {
            "success": False,
            "error": "Ollama returned an empty response.",
            "blueprint": None,
            "catalog_entry": None,
            "raw_response": raw_content,
        }

    # ── Extract JSON from LLM output ──
    parsed = _extract_json_from_response(raw_content)

    if parsed is None:
        return {
            "success": False,
            "error": "Could not extract valid JSON from LLM response.",
            "blueprint": None,
            "catalog_entry": None,
            "rejection": None,
            "raw_response": raw_content,
        }

    # ── Check for rejection ──
    rejection = parsed.get("rejection")
    if rejection and parsed.get("blueprint") is None:
        return {
            "success": False,
            "rejected": True,
            "rejection": rejection,
            "blueprint": None,
            "catalog_entry": None,
            "raw_response": raw_content,
            "model_used": model_name,
            "error": None,
        }

    blueprint = parsed.get("blueprint")
    catalog_entry = parsed.get("catalog_entry")

    if blueprint is None:
        return {
            "success": False,
            "error": "LLM response is missing the 'blueprint' key.",
            "blueprint": None,
            "catalog_entry": catalog_entry,
            "raw_response": raw_content,
        }

    if catalog_entry is None:
        return {
            "success": False,
            "error": "LLM response is missing the 'catalog_entry' key.",
            "blueprint": blueprint,
            "catalog_entry": None,
            "raw_response": raw_content,
        }

    # ── Validate structures ──
    blueprint_error = _validate_blueprint(blueprint)
    if blueprint_error:
        return {
            "success": False,
            "error": f"Blueprint validation failed: {blueprint_error}",
            "blueprint": blueprint,
            "catalog_entry": catalog_entry,
            "raw_response": raw_content,
        }

    catalog_error = _validate_catalog_entry(catalog_entry)
    if catalog_error:
        return {
            "success": False,
            "error": f"Catalog entry validation failed: {catalog_error}",
            "blueprint": blueprint,
            "catalog_entry": catalog_entry,
            "raw_response": raw_content,
        }

    # ── Success ──
    return {
        "success": True,
        "blueprint": blueprint,
        "catalog_entry": catalog_entry,
        "raw_response": raw_content,
        "model_used": model_name,
        "error": None,
    }


async def check_ollama_status() -> dict:
    """Check if Ollama is running and the configured model is available."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check Ollama is running
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
            data = response.json()
            available_models = [m["name"] for m in data.get("models", [])]
            model_ready = any(OLLAMA_MODEL in m for m in available_models)
            return {
                "ollama_running": True,
                "configured_model": OLLAMA_MODEL,
                "model_available": model_ready,
                "available_models": available_models,
            }
    except httpx.ConnectError:
        return {
            "ollama_running": False,
            "configured_model": OLLAMA_MODEL,
            "model_available": False,
            "available_models": [],
            "error": "Cannot connect to Ollama. Run: ollama serve",
        }