from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db
from logic import get_expiry_alerts, get_fefo_batches


app = FastAPI(
    title="Smart Pharma FEFO Service",
    version="1.0.0",
    description="Lightweight standalone backend for FEFO and expiry alerts",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {
        "service": "smart-pharma-fefo",
        "status": "running",
        "endpoints": {
            "fefo": "/fefo/{product_id}",
            "expiry_alerts": "/alerts/expiry",
        },
    }


@app.get("/fefo/{product_id}")
def fefo(product_id: int, db: Session = Depends(get_db)) -> dict:
    batches = get_fefo_batches(db, product_id)
    return {
        "product_id": product_id,
        "total_batches": len(batches),
        "batches": batches,
    }


@app.get("/alerts/expiry")
def expiry_alerts(db: Session = Depends(get_db)) -> dict:
    alerts = get_expiry_alerts(db, days=30)
    return {
        "window_days": 30,
        "total_alerts": len(alerts),
        "alerts": alerts,
    }
