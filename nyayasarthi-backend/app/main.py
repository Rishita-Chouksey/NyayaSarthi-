"""
This is the file you run to start the whole backend server.
Command: uvicorn app.main:app --reload
Then open http://localhost:8000/docs to see and try every API endpoint live.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import auth, cases, verification, actions, audit, departments

# Creates all tables in Postgres if they don't already exist.
# For real production use, switch to Alembic migrations (see alembic/ folder).
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="NyayaSarthi API",
    description="Court Order Execution System — converts judgment PDFs into tracked, accountable government action.",
    version="0.1.0",
)

# Allows the React frontend (running on a different port) to call this API.
import os

# Local dev origins always allowed, plus whatever real deployed frontend URL
# you set as FRONTEND_URL in your hosting provider's environment variables
# (e.g. https://nyayasarthi.vercel.app) — comma-separate if you have more than one.
allowed_origins = ["http://localhost:3000", "http://localhost:5173"]
extra_origins = os.getenv("FRONTEND_URL", "")
if extra_origins:
    allowed_origins.extend([o.strip() for o in extra_origins.split(",")])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(verification.router)
app.include_router(actions.router)
app.include_router(audit.router)
app.include_router(departments.router)


@app.get("/healthz")
def health_check():
    return {"status": "ok"}
