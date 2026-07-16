"""FastAPI application factory for local and production inference."""

import os
from importlib.resources import files
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dirty_product_linker.api.schemas import AnalysisResponse, LinkRequest
from dirty_product_linker.api.service import (
    LazyLinkingService,
    LinkingService,
    build_runtime_service,
)

PACKAGED_CATALOG = files("dirty_product_linker").joinpath(
    "data/demo_catalog_v0_2.jsonl"
)


def _default_catalog_path() -> Path:
    configured_path = os.getenv("DPL_CATALOG_PATH")
    if configured_path is not None:
        return Path(configured_path)

    packaged_path = Path(str(PACKAGED_CATALOG))
    if packaged_path.is_file():
        return packaged_path

    # Editable installs resolve resources from src/, before Hatch has copied
    # the release catalog into a wheel. Keep local development reproducible too.
    return Path(__file__).resolve().parents[3] / "data/catalog/demo_catalog_v0_2.jsonl"


DEFAULT_CATALOG = _default_catalog_path()


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
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://ofeliacode.github.io",
        ],
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
