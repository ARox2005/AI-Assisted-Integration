from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .kyc_provider import router as kyc_router
from .gst_service import router as gst_router

app = FastAPI(
    title="ZeroOne Mock APIs",
    description="Simulated external services (KYC Provider, GST Service) for testing",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount mock service routers
app.include_router(kyc_router)
app.include_router(gst_router)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "mock-apis"}
