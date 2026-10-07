import os
import uuid
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, APIRouter, HTTPException, Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

import market_data as md
import ai_engine
import pdf_export

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

app = FastAPI(title="Artha AI — Investment Intelligence Platform")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("artha")

_insights_cache = {"ts": None, "data": None}


class ValuationRequest(BaseModel):
    ticker: str


class PipelineRunRequest(BaseModel):
    force_issue: bool = False


# --------------------------- Market data ---------------------------
@api_router.get("/")
async def root():
    return {"service": "Artha AI", "status": "ok", "aiEnabled": ai_engine.ai_available()}


@api_router.get("/market/securities")
async def securities():
    feed, universe = await asyncio.gather(
        asyncio.to_thread(md.feed_status),
        asyncio.to_thread(md.get_universe),
    )
    return {"feed": feed, "securities": universe}


@api_router.get("/market/feed-status")
async def feed_status():
    return await asyncio.to_thread(md.feed_status)


@api_router.get("/portfolio")
async def portfolio():
    return await asyncio.to_thread(md.get_portfolio)


@api_router.get("/pipelines")
async def pipelines():
    return await asyncio.to_thread(md.get_pipelines)


@api_router.post("/pipelines/run")
async def run_pipelines(req: PipelineRunRequest):
    result = await asyncio.to_thread(md.get_pipelines, req.force_issue)
    await db.pipeline_runs.insert_one({
        "id": str(uuid.uuid4()),
        "ts": datetime.now(timezone.utc).isoformat(),
        "summary": result["summary"],
    })
    return result


@api_router.get("/monitoring")
async def monitoring():
    return await asyncio.to_thread(md.get_monitoring)


# --------------------------- AI: Market insights ---------------------------
@api_router.get("/market/insights")
async def market_insights():
    return await _build_insights()


async def _build_insights():
    movers = await asyncio.to_thread(md.get_movers)
    now = datetime.now(timezone.utc)
    fresh = (
        _insights_cache["ts"] is not None
        and (now - _insights_cache["ts"]).total_seconds() < 1800
    )
    if fresh and _insights_cache["data"]:
        return {"movers": movers, **_insights_cache["data"]}

    brief, engine = await asyncio.to_thread(ai_engine.market_brief, movers)
    payload = {**brief, "engine": engine, "generatedAt": now.isoformat()}
    _insights_cache["ts"] = now
    _insights_cache["data"] = payload
    return {"movers": movers, **payload}


@api_router.get("/market/insights/pdf")
async def insights_pdf():
    data = await _build_insights()
    pdf = await asyncio.to_thread(pdf_export.market_brief_pdf, data)
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="Artha_Market_Brief.pdf"'},
    )


# --------------------------- AI: Valuation ---------------------------
@api_router.post("/valuation")
async def valuation(req: ValuationRequest):
    sec = await asyncio.to_thread(md.get_security, req.ticker)
    if not sec:
        raise HTTPException(status_code=404, detail="Security not found")

    analysis, engine = await asyncio.to_thread(ai_engine.valuation, sec)
    result = {
        "id": str(uuid.uuid4()),
        "ticker": sec["ticker"],
        "name": sec["name"],
        "currency": sec["currency"],
        "price": sec["price"],
        "engine": engine,
        **analysis,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }
    await db.valuations.insert_one({**result})
    result.pop("_id", None)
    return result


@api_router.get("/valuation/history")
async def valuation_history():
    return await db.valuations.find({}, {"_id": 0}).sort("generatedAt", -1).to_list(20)


@api_router.get("/valuation/{val_id}/pdf")
async def valuation_pdf(val_id: str):
    doc = await db.valuations.find_one({"id": val_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Valuation not found")
    pdf = await asyncio.to_thread(pdf_export.valuation_pdf, doc)
    safe = doc["ticker"].replace(":", "_").replace("/", "-")
    return Response(
        content=pdf, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="Artha_Valuation_{safe}.pdf"'},
    )


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
