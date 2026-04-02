import json
import os
from pathlib import Path

from pydantic import BaseModel
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Request

from .credential_resolver import resolve_credential

router = APIRouter()

# Path to the configs directory (middleware/configs/)
CONFIGS_DIR = Path(__file__).parent.parent / "configs"


def load_config(service_name: str) -> dict:
    """Load a JSON config blueprint from the configs directory."""
    config_path = CONFIGS_DIR / f"{service_name}.json"
    if not config_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"No configuration found for service '{service_name}'. "
                   f"Expected file: {config_path.name}"
        )
    with open(config_path, "r") as f:
        return json.load(f)


def resolve_json_path(data: dict, path: str):
    """
    Simple JSONPath-like resolver.
    Handles paths like '$.applicant_data.firstName'
    and concatenation like "$.applicant_data.firstName + ' ' + $.applicant_data.lastName"
    """
    # Handle concatenation expressions (e.g., "$.x.y + ' ' + $.x.z")
    if "+" in path:
        parts = path.split("+")
        resolved_parts = []
        for part in parts:
            part = part.strip()
            if part.startswith("'") and part.endswith("'"):
                # It's a literal string
                resolved_parts.append(part.strip("'"))
            elif part.startswith('"') and part.endswith('"'):
                resolved_parts.append(part.strip('"'))
            else:
                resolved_parts.append(str(resolve_json_path(data, part)))
        return "".join(resolved_parts)

    # Handle simple dot-notation paths: $.applicant_data.firstName
    if not path.startswith("$."):
        return path

    keys = path[2:].split(".")  # Strip '$.' and split
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            raise ValueError(f"Path '{path}' not found in payload. Failed at key '{key}'.")
    return current


def transform_request(incoming_payload: dict, mapping: dict) -> dict:
    """
    Apply the request_mapping rules from the config to transform
    the incoming payload into the format expected by the target API.
    """
    transformed = {}
    for target_field, source_path in mapping.items():
        try:
            transformed[target_field] = resolve_json_path(incoming_payload, source_path)
        except (ValueError, KeyError) as e:
            transformed[target_field] = None  # Graceful fallback
            print(f"[WARN] Transform failed for '{target_field}': {e}")
    return transformed


@router.post("/api/gateway/execute/{service_name}")
async def execute_gateway(service_name: str, request: Request):
    """
    Main gateway endpoint.
    1. Loads the config for the requested service
    2. Transforms the incoming payload
    3. Resolves credentials
    4. Forwards to the target API
    5. Returns the response
    """
    # 1. Load config
    config = load_config(service_name)

    # 2. Parse incoming payload
    try:
        incoming_payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # 3. Transform the request
    mapping = config.get("schema_transformation_rules", {}).get("request_mapping", {})
    transformed_payload = transform_request(incoming_payload, mapping)

    # 4. Resolve credentials
    security = config.get("security_config", {})
    target_url = security.get("target_url")
    auth_type = security.get("auth_type", "Bearer")

    if not target_url:
        raise HTTPException(status_code=500, detail="No target_url in config")

    try:
        credential = resolve_credential(security.get("credential_vault_reference", ""))
    except (ValueError, EnvironmentError) as e:
        raise HTTPException(status_code=500, detail=str(e))

    # 5. Forward the transformed request to the target API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{auth_type} {credential}",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(target_url, json=transformed_payload, headers=headers)
            target_data = response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot reach target service at {target_url}. Is the mock API running?"
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream call failed: {str(e)}")

    # 6. Return the response with metadata
    return {
        "service": service_name,
        "target_system": config.get("integration_metadata", {}).get("target_system"),
        "api_version": config.get("integration_metadata", {}).get("api_version"),
        "upstream_status_code": response.status_code,
        "data": target_data,
    }

class SimulateRequest(BaseModel):
    """Accepts a config and payload inline for simulation."""
    config: dict          # The blueprint config (not yet deployed)
    payload: dict         # The test payload to transform and forward

@router.post("/api/gateway/simulate")
async def simulate_gateway(request: SimulateRequest):
    """
    Simulate an integration without deploying the config.
    Takes the config and payload inline, runs the full
    transform → resolve credentials → forward → return pipeline.
    """
    config = request.config
    incoming_payload = request.payload

    # 1. Transform the request
    mapping = config.get("schema_transformation_rules", {}).get("request_mapping", {})
    transformed_payload = transform_request(incoming_payload, mapping)

    # 2. Resolve credentials
    security = config.get("security_config", {})
    target_url = security.get("target_url")
    auth_type = security.get("auth_type", "Bearer")

    if not target_url:
        raise HTTPException(status_code=400, detail="No target_url in config")

    try:
        credential = resolve_credential(security.get("credential_vault_reference", ""))
    except (ValueError, EnvironmentError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Forward the transformed request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"{auth_type} {credential}",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(target_url, json=transformed_payload, headers=headers)
            target_data = response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=502,
            detail=f"Cannot reach target service at {target_url}. Is the mock API running?"
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream call failed: {str(e)}")
        
    # 4. Return detailed simulation results
    return {
        "simulation": True,
        "target_system": config.get("integration_metadata", {}).get("target_system"),
        "steps": {
            "1_incoming_payload": incoming_payload,
            "2_transformation_rules": mapping,
            "3_transformed_payload": transformed_payload,
            "4_target_url": target_url,
            "5_auth_type": auth_type,
            "6_api_response": target_data,
            "7_upstream_status": response.status_code,
        },
    }