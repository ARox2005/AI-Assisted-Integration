from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from .registry import get_all_adapters, get_adapter, add_adapter
from .llm_engine import process_sow, check_ollama_status
from .deployer import split_deploy
from .text_extractor import extract_text_from_file, combine_texts
from .adapter_discovery import discover_adapter

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

app = FastAPI(
    title = "ZeroOne AI Orchestrator",
    description="AI-powered design-time tool that reads SOW documents and generates integration blueprints",
    version="0.1.0",
)

# Allow CORS for the orchestrator frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "orchestrator"}

@app.get("/health/ollama")
async def ollama_health():
    """Check if Ollama is running and the configured model is available."""
    status = await check_ollama_status()
    return status

# ──────────────────────────────────────────────
# Registry Endpoints (Adapter Catalog)
# ──────────────────────────────────────────────

@app.get("/api/orchestrator/registry")
def list_adapters():
    """List all adapters in the integration registry."""
    adapters = get_all_adapters()
    return {
        "total": len(adapters),
        "adapters": adapters,
    }

@app.get("/api/orchestrator/registry/{adapter_name}")
def lookup_adapter(adapter_name: str, version: Optional[str] = None):
    """Look up a specific adapter by name (and optional version query param)."""
    adapter = get_adapter(adapter_name, version)
    if adapter is None:
        raise HTTPException(
            status_code=404,
            detail=f"Adapter '{adapter_name}' not found in registry." + (f" (version: {version})" if version else ""),
        )

    return adapter

# ──────────────────────────────────────────────
# SOW Processing & Blueprint Generation
# ──────────────────────────────────────────────

class GenerateRequest(BaseModel):
    """Request body for the /generate endpoint."""
    sow_text: str                    # The full SOW document text
    # adapter_name: Optional[str] = None  # Optional: if user wants to target a specific adapter name
    model: Optional[str] = None     # Optional: override the default Ollama model

class DeployRequest(BaseModel):
    """Request body for the /deploy endpoint."""
    blueprint: dict                  # The generated config blueprint JSON
    catalog_entry: dict              # The catalog entry for the registry
    # service_name: str                # Filename for the config (e.g., "kyc_provider")
    service_name: Optional[str] = None  # Optional: override derived filename

# @app.post("/api/orchestrator/generate")
# async def generate_blueprint(request: GenerateRequest):
#     """
#     Accept an SOW document, process it with the LLM, and return:
#     - blueprint: the config JSON for the middleware
#     - catalog_entry: the metadata entry for the registry
#     """
#     if not request.sow_text.strip():
#         raise HTTPException(status_code=400, detail="SOW text cannot be empty.")

#     result = await process_sow(request.sow_text, model=request.model)

#     # Handle rejections
#     if result.get("rejected"):
        
#         return {
#             "status": "rejected",
#             "rejection": result["rejection"],
#             "model_used": result.get("model_used"),
#         }

#     if not result["success"]:
#         raise HTTPException(
#             status_code=422,
#             detail={
#                 "error": result["error"],
#                 "raw_response": result.get("raw_response"),
#                 "blueprint": result.get("blueprint"),
#                 "catalog_entry": result.get("catalog_entry"),
#             },
#         )

#     return {
#         "status": "success",
#         "blueprint": result["blueprint"],
#         "catalog_entry": result["catalog_entry"],
#         "model_used": result.get("model_used"),
#     }

@app.post("/api/orchestrator/generate")
async def generate_blueprint(request: GenerateRequest):
    """
    Accept an SOW document, discover matching adapter, process with LLM.
    Returns: blueprint, catalog_entry, and discovery info.
    """
    if not request.sow_text.strip():
        raise HTTPException(status_code=400, detail="SOW text cannot be empty.")

    # Step 1: Adapter Discovery
    discovery = await discover_adapter(request.sow_text, model=request.model)

    # Step 2: Generate config (pass matched adapter if found)
    matched = discovery.get("matched_adapter") if discovery["match_found"] else None
    result = await process_sow(request.sow_text, model=request.model, matched_adapter=matched)

    # Handle rejections
    if result.get("rejected"):
        return {
            "status": "rejected",
            "rejection": result["rejection"],
            "model_used": result.get("model_used"),
            "discovery": discovery,
        }

    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": result["error"],
                "raw_response": result.get("raw_response"),
                "blueprint": result.get("blueprint"),
                "catalog_entry": result.get("catalog_entry"),
            },
        )

    return {
        "status": "success",
        "blueprint": result["blueprint"],
        "catalog_entry": result["catalog_entry"],
        "model_used": result.get("model_used"),
        "discovery": discovery,
    }

@app.post("/api/orchestrator/deploy")
async def deploy_blueprint(request: DeployRequest):
    """
    Split deployment:
    1. Save the blueprint to middleware/configs/{service_name}.json
    2. Add the catalog entry to the integration registry
    """
    # Step 1: Registry update
    # registry_result = add_adapter(request.catalog_entry)
    # if not registry_result.success:
    #     raise HTTPException(
    #         status_code=400,
    #         detail=f"Registry update failed: {registry_result.message}",
    #     )

    # # Step 2: Deploy config to middleware
    # # TODO: Wire to deployer.deploy_config() once we build it
    # # For now, just report what would happen
    # return {
    #     "status": "partial",
    #     "registry": registry_result.to_dict(),
    #     "config_deployment": {
    #         "status": "pending",
    #         "message": f"Deployer not yet connected. Would write to middleware/configs/{request.service_name}.json",
    #     },
    # }

    deployment = split_deploy(
        blueprint=request.blueprint,
        catalog_entry=request.catalog_entry,
        service_name=request.service_name,
    )

    if not deployment.success:
        raise HTTPException(
            status_code=400,
            detail=deployment.to_dict(),
        )

    return deployment.to_dict()

@app.post("/api/orchestrator/generate-and-deploy")
async def generate_and_deploy(request: GenerateRequest):
    """
    One-shot endpoint: SOW in → blueprint generated → deployed to middleware + registry.
    Combines /generate and /deploy into a single call.
    """
    if not request.sow_text.strip():
        raise HTTPException(status_code=400, detail="SOW text cannot be empty.")

    # Step 1: Generate
    result = await process_sow(request.sow_text, model=request.model)

    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": result["error"],
                "raw_response": result.get("raw_response"),
            },
        )

    # Step 2: Deploy
    deployment = split_deploy(
        blueprint=result["blueprint"],
        catalog_entry=result["catalog_entry"],
    )
    
    return {
        "status": "success" if deployment.success else "partial_failure",
        "generation": {
            "blueprint": result["blueprint"],
            "catalog_entry": result["catalog_entry"],
            "model_used": result.get("model_used"),
        },
        "deployment": deployment.to_dict(),
    }

# @app.post("/api/orchestrator/generate-from-upload")
# async def generate_from_upload(
#     sow_text: Optional[str] = Form(default=""),
#     files: List[UploadFile] = File(default=[]),
#     model: Optional[str] = Form(default=None),
# ):
#     """
#     Generate blueprint from uploaded files and/or pasted text.
#     Accepts multipart form data with:
#     - sow_text: Optional pasted text
#     - files: One or more PDF/DOCX/TXT files
#     - model: Optional Ollama model override
#     """
#     # Extract text from uploaded files
#     file_results = []
#     for uploaded_file in files:
#         content = await uploaded_file.read()
#         extracted = extract_text_from_file(content, uploaded_file.filename)
#         file_results.append((uploaded_file.filename, extracted))

#     # Combine all text
#     combined_text = combine_texts(sow_text or "", file_results)

#     if not combined_text.strip():
#         raise HTTPException(
#             status_code=400,
#             detail="No content provided. Paste text or upload at least one file.",
#         )

#     # Process through LLM
#     result = await process_sow(combined_text, model=model)

#     # Handle rejections
#     if result.get("rejected"):
#         return {
#             "status": "rejected",
#             "rejection": result["rejection"],
#             "model_used": result.get("model_used"),
#             "combined_text_preview": combined_text[:500] + "..." if len(combined_text) > 500 else combined_text,
#         }

#     if not result["success"]:
#         raise HTTPException(
#             status_code=422,
#             detail={
#                 "error": result["error"],
#                 "raw_response": result.get("raw_response"),
#             },
#         )

#     return {
#         "status": "success",
#         "blueprint": result["blueprint"],
#         "catalog_entry": result["catalog_entry"],
#         "model_used": result.get("model_used"),
#         "files_processed": [f[0] for f in file_results],
#     }

@app.post("/api/orchestrator/generate-from-upload")
async def generate_from_upload(
    sow_text: Optional[str] = Form(default=""),
    files: List[UploadFile] = File(default=[]),
    model: Optional[str] = Form(default=None),
):
    # Extract text from uploaded files
    file_results = []
    for uploaded_file in files:
        content = await uploaded_file.read()
        extracted = extract_text_from_file(content, uploaded_file.filename)
        file_results.append((uploaded_file.filename, extracted))

    # Combine all text
    combined_text = combine_texts(sow_text or "", file_results)

    if not combined_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No content provided. Paste text or upload at least one file.",
        )

    # Step 1: Adapter Discovery
    discovery = await discover_adapter(combined_text, model=model)

    # Step 2: Generate config (pass matched adapter if found)
    matched = discovery.get("matched_adapter") if discovery["match_found"] else None
    result = await process_sow(combined_text, model=model, matched_adapter=matched)

    # Handle rejections
    if result.get("rejected"):
        return {
            "status": "rejected",
            "rejection": result["rejection"],
            "model_used": result.get("model_used"),
            "combined_text_preview": combined_text[:500] + "..." if len(combined_text) > 500 else combined_text,
            "discovery": discovery,
        }

    if not result["success"]:
        raise HTTPException(
            status_code=422,
            detail={
                "error": result["error"],
                "raw_response": result.get("raw_response"),
            },
        )

    return {
        "status": "success",
        "blueprint": result["blueprint"],
        "catalog_entry": result["catalog_entry"],
        "model_used": result.get("model_used"),
        "files_processed": [f[0] for f in file_results],
        "discovery": discovery,
    }


# ──────────────────────────────────────────────
# Smart Routing (AI-Powered Intent Routing)
# ──────────────────────────────────────────────

# class RouteRequest(BaseModel):
#     payload: dict
#     intent: Optional[str] = None
#     model: Optional[str] = None
#     auto_execute: Optional[bool] = False  # If True, also execute via middleware


# @app.post("/api/orchestrator/route")
# async def smart_route(request: RouteRequest):
#     """
#     AI-powered intent routing.
#     Sends the payload + registry to Ollama, which picks the best adapter.
#     Optionally auto-executes via middleware.
#     """
#     # Step 1: Route
#     route_result = await route_intent(
#         payload=request.payload,
#         intent=request.intent,
#         model=request.model,
#     )

#     if not route_result["success"]:
#         raise HTTPException(status_code=422, detail=route_result)

#     if not route_result["routed"]:
#         return {
#             "status": "no_match",
#             "message": route_result.get("reason", "No adapter matched the payload."),
#             "routing": route_result,
#         }

#     # Step 2: If auto_execute is enabled, forward to middleware
#     if request.auto_execute and route_result["selected_adapters"]:
#         top_adapter = route_result["selected_adapters"][0]
#         adapter_name = top_adapter["adapter_name"]

#         # Sanitize adapter name to match config filename
#         service_name = adapter_name.lower().replace(" ", "_").replace("-", "_")

#         try:
#             async with httpx.AsyncClient(timeout=30.0) as client:
#                 mw_response = await client.post(
#                     f"http://localhost:8002/api/gateway/execute/{service_name}",
#                     json=request.payload,
#                 )
#                 mw_data = mw_response.json()
#         except httpx.ConnectError:
#             raise HTTPException(
#                 status_code=502,
#                 detail="Middleware not reachable at port 8002.",
#             )
#         except Exception as e:
#             raise HTTPException(
#                 status_code=502,
#                 detail=f"Middleware call failed: {str(e)}",
#             )

#         return {
#             "status": "executed",
#             "routing": route_result,
#             "execution": {
#                 "adapter_used": adapter_name,
#                 "service_name": service_name,
#                 "middleware_response": mw_data,
#                 "middleware_status": mw_response.status_code,
#             },
#         }

#     # Step 3: Route-only (no execution)
#     return {
#         "status": "routed",
#         "routing": route_result,
#     }

@app.post("/api/orchestrator/reset-configs")
async def reset_configs():
    """Demo utility: Deletes all deployed config files from middleware/configs/."""
    configs_dir = Path(__file__).parent.parent.parent / "middleware" / "configs"
    deleted = []
    if configs_dir.exists():
        for config_file in configs_dir.glob("*.json"):
            config_file.unlink()
            deleted.append(config_file.name)
    return {
        "status": "configs_cleared",
        "deleted": deleted,
        "count": len(deleted),
    }