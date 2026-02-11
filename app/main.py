from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import articles, categories, health, reports, search, seal_types

app = FastAPI(
    title="SealCheck API",
    description="API for checking tamper-evident safety seal requirements",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow all origins in development; tighten in production
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers — every router is mounted under the /api prefix
# ---------------------------------------------------------------------------
app.include_router(health.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(categories.router, prefix="/api")
app.include_router(seal_types.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(articles.router, prefix="/api")
