# Yachay

Tutor conversacional escolar por Telegram (vía Zavu) + dashboard docente.

Flujo: Landing → Telegram (código alumno) → agente clasifica / detecta debilidad / mini-experimento → dashboard.

## Estructura

```
backend/   FastAPI + SQLite + Claude + webhooks
frontend/  React + Tailwind (Vite) — landing + dashboard
```

## Arranque local (MVP sin claves)

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Prueba rápida (Postman/curl):

```bash
curl -X POST http://localhost:8000/webhook/simulate -H "Content-Type: application/json" -d "{\"telegram_id\":\"u1\",\"message\":\"UEBOL-3A-99\"}"

curl -X POST http://localhost:8000/webhook/simulate -H "Content-Type: application/json" -d "{\"telegram_id\":\"u1\",\"message\":\"Por que un huevo se hunde en el agua?\"}"

curl -X POST http://localhost:8000/webhook/simulate -H "Content-Type: application/json" -d "{\"telegram_id\":\"u1\",\"message\":\"Y si le pongo sal flota?\"}"
```

Dashboard API: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Abre http://localhost:5173 — Landing y `/dashboard`.

## Variables de entorno (cuando tengas APIs)

Ver `backend/.env.example` y `frontend/.env.example`.

| Variable | Dónde | Para qué |
|----------|--------|----------|
| `GROQ_API_KEY` | backend | Cerebro del agente (gratis, sin tarjeta) |
| `ANTHROPIC_API_KEY` | backend | Cerebro alternativo (Claude), opcional |
| `ZAVU_API_KEY` / `ZAVU_SEND_URL` / `ZAVU_WEBHOOK_SECRET` | backend | Canal Telegram |
| `DATABASE_URL` | backend | SQLite local o Postgres en producción |
| `ELEVENLABS_API_KEY` | backend | Audio STT/TTS |
| `EXA_API_KEY` + `EXA_ENABLED=true` | backend | Grounding opcional |
| `VITE_API_URL` | frontend | URL del backend |
| `VITE_TELEGRAM_BOT` | frontend | Deep link t.me/... |

Sin claves, `DEMO_MODE=true` responde con plantillas bolivianas y seed de alumnos.

## Regla de debilidad

≥ 2 preguntas del mismo tema → debilidad activa → si el tema lo permite, se crea un mini-experimento casero.

## Producción (Railway + Netlify)

### Backend en Railway

1. Sube el repo a GitHub (ya hecho si estás leyendo esto desde ahí).
2. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → selecciona el repo.
3. En **Settings** del servicio creado:
   - **Root Directory**: `backend`
   - Railway detecta Python (Nixpacks) automáticamente y usa `backend/railway.json` para el start command (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`) y el healthcheck (`/health`). Si no lo detecta, también hay un `Procfile` de respaldo.
4. En **Variables** → **Raw Editor**, pega el contenido de `backend/.env.railway.example` (reemplazando los `<...>` con tus claves reales).
5. Base de datos: SQLite se pierde en cada redeploy (filesystem efímero). Para producción:
   - **Opción simple**: en el mismo proyecto Railway, **+ New → Database → Add PostgreSQL**, y en las variables del backend pon `DATABASE_URL=${{Postgres.DATABASE_URL}}` (Railway resuelve la referencia solo).
   - **Alternativa**: Supabase, pegando su connection string (modo "Session pooler") directo en `DATABASE_URL`.
   - El backend acepta ambos formatos de URL (`postgres://` y `postgresql://`) automáticamente.
6. Railway te da una URL pública, ej. `https://yachay-backend.up.railway.app`. Verifica: `curl https://yachay-backend.up.railway.app/health` → debe mostrar `"status": "ok"` y `"database": true`.

### Frontend en Netlify

1. Netlify → **Add new site** → base directory `frontend`, build `npm run build`, publish `dist` (ya configurado en `netlify.toml`).
2. Variables: `VITE_API_URL` (URL de Railway) y `VITE_TELEGRAM_BOT`.
3. En Railway, actualiza `CORS_ORIGINS` con la URL final de Netlify.

### Notas

- En producción usa `DEMO_MODE=false` para no mezclar el seed de alumnos de ejemplo con datos reales de Telegram.
- El endpoint `/webhook/simulate` es solo para pruebas locales (Postman/curl); no lo expongas como única vía de entrada en producción.
