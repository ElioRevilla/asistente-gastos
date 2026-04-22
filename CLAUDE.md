# Asistente de Gastos — CLAUDE.md

Bot de Telegram multi-usuario para registrar gastos personales (texto, foto de recibo, audio). Desplegado en Cloud Run (GCP). Objetivo de costo: ~S/. 0–3/mes usando free tiers.

## Stack

- Python 3.12 · FastAPI · uvicorn
- python-telegram-bot v21 (webhook mode)
- Gemini 2.0 Flash via `google-generativeai` — extracción de gastos desde texto, imagen y audio
- Firestore (Native mode) — colecciones: `expenses`, `users`
- GCP: Cloud Run · Cloud Build · Artifact Registry · Cloud Scheduler

## Arquitectura (Clean Architecture)

```
app/
  domain/           # entidades puras + interfaces (ABC) — sin dependencias externas
    entities/       # Expense, User
    repositories/   # IExpenseRepository, IUserRepository (ABCs)
    value_objects/  # Money
  application/
    ports/          # IAIExtractor, INotifier (ABCs)
    use_cases/      # RegisterExpense, GetPeriodSummary, GetCategorySummary, SendDailySummary
  infrastructure/
    ai/             # GeminiExtractor, prompts
    persistence/    # FirestoreExpenseRepository, FirestoreUserRepository
    telegram/       # TelegramNotifier
  presentation/
    api/            # FastAPI routes (webhook, scheduler trigger)
    telegram/       # handlers (texto/foto/voz), commands (/start /hoy /semana /mes /cat)
main.py             # DI wiring + FastAPI app factory
```

**Regla:** el dominio no importa nada externo. Los casos de uso solo dependen de ports (ABCs). Las implementaciones concretas viven en infrastructure. Los handlers en presentation son delgados.

## Variables de entorno requeridas

```
TELEGRAM_TOKEN       # BotFather
GEMINI_API_KEY       # Google AI Studio
GCP_PROJECT_ID       # ID del proyecto GCP
SCHEDULER_SECRET     # Secret para autenticar llamadas de Cloud Scheduler (opcional en local)
```

En local usar `.env` (no commitear). En Cloud Run configurar como secrets/env vars.

## Comandos útiles

```bash
# Instalar dependencias
pip install -r requirements.txt

# Correr local (necesita .env)
python main.py

# Build imagen Docker
docker build -t asistente-gastos .

# Deploy manual a Cloud Run (después de configurar gcloud)
gcloud run deploy asistente-gastos \
  --image REGION-docker.pkg.dev/PROJECT/REPO/asistente-gastos \
  --region us-central1 \
  --allow-unauthenticated
```

## CI/CD

`cloudbuild.yaml` define el pipeline de Cloud Build: build imagen → push a Artifact Registry → deploy a Cloud Run.

## Convenciones

- Código en inglés, mensajes al usuario en español
- Type hints en todo el código nuevo
- No agregar manejo de errores especulativo — solo en boundaries reales (handlers de Telegram, routes de FastAPI)
- No abstraer para casos de uso hipotéticos futuros
