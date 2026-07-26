import logging
from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

logger = logging.getLogger("yachay.database")
settings = get_settings()


def _normalize_database_url(url: str) -> str:
    """Railway/Supabase/Heroku suelen dar 'postgres://', pero SQLAlchemy 2.x
    requiere el driver explícito 'postgresql://'."""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


DATABASE_URL = _normalize_database_url(settings.database_url)
is_sqlite = DATABASE_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if is_sqlite else {}
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    # pool_pre_ping evita errores por conexiones caídas en Postgres remoto
    # (Supabase/Railway cierran conexiones inactivas periódicamente).
    pool_pre_ping=not is_sqlite,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def ensure_schema_upgrades() -> None:
    """create_all no añade columnas nuevas; migraciones mínimas aquí."""
    try:
        insp = inspect(engine)
        if "experiments" not in insp.get_table_names():
            return
        cols = {c["name"] for c in insp.get_columns("experiments")}
        with engine.begin() as conn:
            if "status" not in cols:
                conn.execute(
                    text("ALTER TABLE experiments ADD COLUMN status VARCHAR(20) DEFAULT 'pending'")
                )
                logger.info("Migración: experiments.status añadida")
            if "feedback" not in cols:
                conn.execute(text("ALTER TABLE experiments ADD COLUMN feedback TEXT DEFAULT ''"))
                logger.info("Migración: experiments.feedback añadida")
    except Exception:
        logger.exception("No se pudo aplicar migración liviana de experiments")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
