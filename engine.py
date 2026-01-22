from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# ============================================================
# App
# ============================================================

app = FastAPI(
    title="PortEngine",
    version="1.0.0",
    description="Backend engine powering portfolio content."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "service": "portEngine"}


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "time": datetime.utcnow().isoformat() + "Z"
    }