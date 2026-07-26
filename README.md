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
| `ANTHROPIC_API_KEY` | backend | Cerebro del agente |
| `ZAVU_API_KEY` / `ZAVU_SEND_URL` / `ZAVU_WEBHOOK_SECRET` | backend | Canal Telegram |
| `ELEVENLABS_API_KEY` | backend | Audio STT/TTS |
| `EXA_API_KEY` + `EXA_ENABLED=true` | backend | Grounding opcional |
| `VITE_API_URL` | frontend | URL del backend |
| `VITE_TELEGRAM_BOT` | frontend | Deep link t.me/... |

Sin claves, `DEMO_MODE=true` responde con plantillas bolivianas y seed de alumnos.

## Regla de debilidad

≥ 2 preguntas del mismo tema → debilidad activa → si el tema lo permite, se crea un mini-experimento casero.
