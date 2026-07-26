import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import get_settings
from app.database import Base, SessionLocal, ensure_schema_upgrades, engine
from app.routers import experiments, stats, students, weaknesses, webhook
from app.seed import clear_demo_seed_data, seed_demo_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("yachay")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_schema_upgrades()
    settings = get_settings()
    db = SessionLocal()
    try:
        if settings.demo_mode:
            seed_demo_data(db)
        else:
            # Si antes estuvo DEMO_MODE=true, los Ana/Luis/María siguen en la DB;
            # los limpiamos para que el dashboard arranque en 0.
            removed = clear_demo_seed_data(db)
            if removed:
                logger.info("DEMO_MODE=false: limpiados %s registros de demo", removed)
            else:
                logger.info("DEMO_MODE=false: sin seed de demo; listo para alumnos reales")
    finally:
        db.close()
    yield


app = FastAPI(
    title="Yachay API",
    description="Tutor conversacional escolar — webhook Zavu + dashboard docente",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
# CORS amplio para el dashboard en Netlify / localhost. Si se restringe
# mal CORS_ORIGINS, el navegador bloquea y el front muestra mock.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
        # Si este valor no aparece en producción, Railway NO redeployó el código nuevo.
        "code_version": "yachay-2026-07-26-v6",
    }
