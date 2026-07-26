import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.routers import experiments, stats, students, weaknesses, webhook
from app.seed import seed_demo_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("yachay")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    settings = get_settings()
    if settings.demo_mode:
        db = SessionLocal()
        try:
            seed_demo_data(db)
        finally:
            db.close()
    else:
        logger.info("DEMO_MODE=false: se omite el seed de datos de ejemplo")
    yield


app = FastAPI(
    title="Yachay API",
    description="Tutor conversacional escolar — webhook Zavu + dashboard docente",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
origins = settings.cors_origin_list or ["http://localhost:5173"]
if settings.demo_mode and "*" not in origins:
    origins = list(set(origins + ["http://localhost:5173", "http://127.0.0.1:5173"]))
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router)
app.include_router(students.router)
app.include_router(weaknesses.router)
app.include_router(experiments.router)
app.include_router(stats.router)


@app.get("/health")
def health():
    s = get_settings()
    db_ok = True
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
    except Exception:
        logger.exception("Fallo el ping a la base de datos en /health")
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "database": db_ok,
        "demo_mode": s.demo_mode,
        "claude": s.has_claude,
        "groq": s.has_groq,
        "elevenlabs": s.has_elevenlabs,
        "exa": s.has_exa,
        "zavu": s.has_zavu,
        "telegram_bot": s.telegram_bot_username,
    }
