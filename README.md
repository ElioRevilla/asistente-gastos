# Asistente de Gastos 💰

Bot de Telegram multi-usuario para registrar gastos personales enviando **texto, fotos de recibos o mensajes de voz**. La IA extrae automáticamente el monto, categoría y descripción. Costo estimado: ~S/. 0-3/mes.

---

## Arquitectura

```
Telegram
   │  Webhook POST
   ▼
Cloud Run  (FastAPI + python-telegram-bot)
   ├── Gemini 2.0 Flash  → extracción de gastos (texto, imagen, audio)
   └── Firestore         → persistencia
        └── Cloud Scheduler → resumen diario 11pm
```

Código organizado en **Clean Architecture**:

```
app/
├── domain/          # Entidades y contratos — sin dependencias externas
├── application/     # Casos de uso + ports (interfaces)
├── infrastructure/  # Gemini, Firestore, Telegram (implementaciones)
└── presentation/    # FastAPI routes + handlers de Telegram
main.py              # Inyección de dependencias + entry point
```

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Interfaz | Telegram Bot API (Webhook) |
| Backend | Python 3.12 · FastAPI · python-telegram-bot v21 |
| IA | Gemini 2.0 Flash (Google AI Studio) |
| Base de datos | Firestore (Native mode) |
| Hosting | Cloud Run |
| CI/CD | GitHub Actions → Artifact Registry → Cloud Run |
| Scheduler | Cloud Scheduler (cron 11pm) |

---

## Funcionalidades

- **Registrar gastos** enviando:
  - 📝 Texto libre: `"Gasté 12000 en el bus"`
  - 📷 Foto de recibo o factura
  - 🎤 Nota de voz
- **Comandos de consulta:**
  - `/hoy` — resumen del día
  - `/semana` — resumen de la semana
  - `/mes` — resumen del mes
  - `/cat` — gastos por categoría
- **Resumen diario automático** a las 11pm vía Cloud Scheduler
- **Multi-usuario** — datos aislados por `user_id` de Telegram

---

## Requisitos previos

- Python 3.12+
- Cuenta de Google (para GCP y Gemini API)
- Cuenta de Telegram
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) (para deploy)
- [ngrok](https://ngrok.com/download) (solo para desarrollo local)

---

## Configuración local

### 1. Clonar e instalar dependencias

```bash
git clone <repo-url>
cd asistente-de-gastos

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

### 2. Variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con los valores reales:

| Variable | Cómo obtenerla |
|----------|---------------|
| `TELEGRAM_TOKEN` | Crear bot en [@BotFather](https://t.me/BotFather) → `/newbot` |
| `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/apikey) → Create API key |
| `GCP_PROJECT_ID` | [GCP Console](https://console.cloud.google.com) → ID del proyecto |

### 3. Crear Firestore (una sola vez)

Desde [GCP Console](https://console.cloud.google.com):
1. Buscar **Firestore** → Crear base de datos
2. Modo: **Native mode**
3. Ubicación: `nam5`

El nombre de la base de datos será `(default)` — ya está configurado en `.env.example`.

### 4. Autenticación local con GCP

```bash
gcloud auth application-default login
```

### 5. Correr localmente con ngrok

**Terminal 1 — arrancar el bot:**
```bash
python main.py
```

**Terminal 2 — ngrok:**
```bash
ngrok http 8080
```

**Registrar el webhook** (una sola vez, o cuando cambie la URL de ngrok):
```bash
# En el navegador o terminal:
https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://<NGROK_URL>/webhook
```

---

## Deploy en GCP (Cloud Run) via GitHub Actions

Cada push a `main` dispara el workflow `.github/workflows/deploy.yml` que construye la imagen, la sube a Artifact Registry y despliega en Cloud Run automáticamente.

### ✅ Paso 1 — Habilitar APIs

```bash
gcloud config set project asistente-gastos-bot
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
```

### ✅ Paso 2 — Crear Artifact Registry

```bash
gcloud artifacts repositories create bot-repo \
  --repository-format=docker \
  --location=us-central1
```

### Paso 3 — Service Account para GitHub Actions

```bash
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

gcloud projects add-iam-policy-binding asistente-gastos-bot \
  --member="serviceAccount:github-actions@asistente-gastos-bot.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding asistente-gastos-bot \
  --member="serviceAccount:github-actions@asistente-gastos-bot.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding asistente-gastos-bot \
  --member="serviceAccount:github-actions@asistente-gastos-bot.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding asistente-gastos-bot \
  --member="serviceAccount:github-actions@asistente-gastos-bot.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@asistente-gastos-bot.iam.gserviceaccount.com
```

### Paso 4 — Crear secrets en Secret Manager

```bash
echo -n "TU_TELEGRAM_TOKEN" | gcloud secrets create TELEGRAM_TOKEN --data-file=-
echo -n "TU_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo -n "$(python -c 'import secrets; print(secrets.token_hex(32))')" | gcloud secrets create SCHEDULER_SECRET --data-file=-
```

### Paso 5 — Agregar secrets en GitHub

En el repo → **Settings → Secrets and variables → Actions**:

| Secret | Valor |
|--------|-------|
| `GCP_SA_KEY` | contenido completo del archivo `key.json` |
| `TELEGRAM_TOKEN` | token del bot (para registrar el webhook post-deploy) |

> ⚠️ No commitear `key.json` — agregarlo a `.gitignore`.

### Paso 6 — Crear Firestore

Desde [GCP Console](https://console.cloud.google.com/firestore):
1. Crear base de datos → **Native mode**
2. Ubicación: `nam5`
3. Nombre: `(default)`

### Paso 7 — Push y deploy

```bash
git add .
git commit -m "deploy: initial Cloud Run setup"
git push origin main
```

El webhook se registra automáticamente al final del workflow.

### Paso 8 — Cloud Scheduler (resumen diario)

```bash
CLOUD_RUN_URL=$(gcloud run services describe asistente-gastos --region=us-central1 --format='value(status.url)')
SCHEDULER_SECRET=$(gcloud secrets versions access latest --secret=SCHEDULER_SECRET)

gcloud scheduler jobs create http daily-summary \
  --schedule="0 23 * * *" \
  --time-zone="America/Lima" \
  --uri="${CLOUD_RUN_URL}/scheduler/daily-summary" \
  --http-method=POST \
  --headers="X-Scheduler-Secret=${SCHEDULER_SECRET}" \
  --location=us-central1
```

---

## Estructura del proyecto

```
asistente-de-gastos/
├── app/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── expense.py               # Entidad Expense + ExpenseData DTO
│   │   │   └── user.py                  # Entidad User
│   │   ├── value_objects/
│   │   │   └── money.py                 # Value object Money
│   │   └── repositories/
│   │       ├── expense_repository.py    # IExpenseRepository (ABC)
│   │       └── user_repository.py       # IUserRepository (ABC)
│   ├── application/
│   │   ├── ports/
│   │   │   ├── ai_extractor.py          # IAIExtractor (ABC)
│   │   │   └── notifier.py              # INotifier (ABC)
│   │   └── use_cases/
│   │       ├── register_expense.py      # Registrar un gasto
│   │       ├── get_period_summary.py    # Resumen por período
│   │       ├── get_category_summary.py  # Resumen por categoría
│   │       └── send_daily_summary.py    # Enviar resumen diario
│   ├── infrastructure/
│   │   ├── ai/
│   │   │   ├── gemini_extractor.py      # Gemini 2.0 Flash
│   │   │   └── prompts.py               # System prompts
│   │   ├── persistence/
│   │   │   ├── firestore_expense_repository.py
│   │   │   └── firestore_user_repository.py
│   │   └── telegram/
│   │       └── telegram_notifier.py
│   └── presentation/
│       ├── api/
│       │   └── routes.py                # /webhook + /scheduler/daily-summary
│       └── telegram/
│           ├── handlers.py              # Texto, foto, audio
│           └── commands.py              # /start /hoy /semana /mes /cat
├── main.py                              # DI wiring + entry point
├── Dockerfile
├── cloudbuild.yaml
├── requirements.txt
└── .env.example
```

---

## Costo estimado

| Servicio | Costo |
|---------|-------|
| Cloud Run | Gratis (2M requests/mes free tier) |
| Gemini 2.0 Flash | Gratis hasta 15 RPM / 1M tokens/día |
| Firestore | Gratis (50K reads, 20K writes/día) |
| Cloud Scheduler | Gratis (3 jobs/mes) |
| **Total** | **~S/. 0-3/mes** |
