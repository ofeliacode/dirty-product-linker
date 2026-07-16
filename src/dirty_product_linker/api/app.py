"""FastAPI application factory for local and production inference."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dirty_product_linker.api.schemas import AnalysisResponse, LinkRequest
from dirty_product_linker.api.service import (
    LazyLinkingService,
    LinkingService,
    build_runtime_service,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CATALOG = PROJECT_ROOT / "data/catalog/demo_catalog_v0_2.jsonl"


def create_app(service: LinkingService | None = None) -> FastAPI:
    """Create an app with an injectable runtime for deterministic tests."""

    runtime_mode = os.getenv("DPL_RUNTIME", "full")
    runtime_device = os.getenv("DPL_DEVICE", "cpu")
    local_files_only = os.getenv("DPL_OFFLINE", "0") == "1"
    runtime = service or LazyLinkingService(
        lambda: build_runtime_service(
            runtime_mode,
            catalog_path=DEFAULT_CATALOG,
            device=runtime_device,
            local_files_only=local_files_only,
        )
    )
    application = FastAPI(
        title="Dirty Product Linker API",
        version="0.1.0",
        description="Resolve noisy product mentions to canonical catalog records.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "dirty-product-linker"}

    @application.post("/v1/link", response_model=AnalysisResponse)
    def link_product(request: LinkRequest) -> AnalysisResponse:
        return runtime.analyze(request.text)

    return application


app = create_app()
