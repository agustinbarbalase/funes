# Funes

> *"Pensar es olvidar diferencias, es generalizar, abstraer. En el abarrotado mundo de Funes no había sino detalles, casi inmediatos."*
>
> — Jorge Luis Borges, *Funes el memorioso*

Funes es una aplicación de efemérides históricas potenciada por RAG (Retrieval-Augmented Generation). Dado un día del año, recupera y curada eventos históricos relevantes usando búsqueda vectorial y un LLM. También permite buscar eventos por consulta en lenguaje natural.

## Arquitectura

```
+-------------+     +--------------------------------------------------+     +--------------+
|   Frontend  |---->|                  Backend                         |---->|  PostgreSQL  |
|  React/Vite |     |              FastAPI + RAG                       |     |  + pgvector  |
+-------------+     +--------------------------------------------------+     +--------------+
                                         ^
                                         |
                    +--------------------+-----------------------------+
                    |                  Pipeline                        |
                    |                                                  |
                    |  Wikipedia API                                   |
                    |       |                                          |
                    |       v                                          |
                    |  [fetch] -> [transform] -> [validate] -> [load]  |
                    |       |          |             |           |     |
                    |       +----------+-------------+-----------+     |
                    |                       |                          |
                    |                   RabbitMQ                       |
                    +--------------------------------------------------+
```

El pipeline procesa ~366 días del año en paralelo mediante workers distribuidos conectados por RabbitMQ. Cada efeméride se embebe con `fastembed` y se almacena en PostgreSQL con pgvector para búsqueda por similitud semántica.

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | FastAPI, Python 3.13 |
| Base de datos | PostgreSQL 16 + pgvector |
| Embeddings | fastembed (`paraphrase-multilingual-MiniLM-L12-v2`) |
| LLM | Ollama cloud (`gpt-oss:20b`) |
| Cache | Redis |
| Pipeline | RabbitMQ + workers Docker |
| Deploy | Render (backend), Vercel (frontend) |

## Estructura del proyecto

```
funes/
├── backend/          # API FastAPI + RAG
├── frontend/         # React + Vite
└── pipelines/        # Workers de ingesta
    ├── workers/
    │   ├── fetch/    # Descarga datos de Wikipedia
    │   ├── transform/# Extrae y normaliza efemérides
    │   ├── validate/ # Valida y sanitiza
    │   └── load/     # Embebe e inserta en PostgreSQL
    ├── producer/     # Emite tareas a la cola
    └── common/       # Broker abstraction + modelos compartidos
```

## Desarrollo local

### Requisitos

- Docker y Docker Compose
- Node.js 20+ y pnpm
- Python 3.13

### Backend

```bash
cd backend
cp .env.example .env   # completar variables
make dev               # levanta API + Postgres con hot reload
```

Variables de entorno requeridas:

```env
DATABASE_URL=postgresql://postgres:postgres@db:5432/funes
OLLAMA_API_KEY=...
REDIS_URL=redis://localhost:6379
ALLOWED_ORIGINS=http://localhost:5173
```

### Frontend

```bash
cd frontend
pnpm install
cp .env.example .env   # completar VITE_API_URL
pnpm dev
```

### Pipeline

```bash
cd pipelines
cp .env.example .env   # completar variables
make up                # levanta RabbitMQ + workers
make produce           # emite tareas para todo el año
```

Para un día específico:

```bash
make produce day=20 month=6
```

Variables de entorno del pipeline:

```env
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
API_URL=http://funes-api:8000
```

## Pipeline de ingesta

El pipeline procesa efemérides en cuatro etapas:

1. **fetch** — descarga los datos de la API `onthisday` de Wikipedia en español para cada día del año, con caché local en `cache/raw/`
2. **transform** — extrae eventos, nacimientos y fallecimientos; filtra imágenes y normaliza el formato
3. **validate** — valida títulos, tipos y fechas; sanitiza texto e imágenes
4. **load** — embebe los textos con fastembed y los inserta en PostgreSQL vía la API del backend

El tamaño de batch del worker `load` es dinámico: se ajusta automáticamente según la tasa de llegada de mensajes, escalando entre `MIN_BUFFER_SIZE` y `MAX_BUFFER_SIZE`.

## API

| Endpoint | Descripción |
|---|---|
| `GET /ephemeris/{month}/{day}` | Efemérides del día, curadas por el LLM |
| `GET /ephemeris/search?query=...` | Búsqueda híbrida (vectorial + full-text) |
| `POST /ingest/{day}/{month}` | Ingesta de efemérides (uso interno del pipeline) |
| `GET /health` | Health check |

## Deploy

El backend se despliega en **Render** y el frontend en **Vercel** vía GitHub Actions al hacer push a `main` con cambios en `frontend/`.
