# 🛡️ VIGÍA v2.1 — PLATAFORMA DE INTELIGENCIA ESTATAL-MILITAR

<div align="center">

![VIGÍA System](https://img.shields.io/badge/VIGÍA-v2.1-0052FF?style=for-the-badge&logo=shield)
![Status](https://img.shields.io/badge/STATUS-OPERATIONAL-green?style=for-the-badge&logo=checkmarx)
![Security](https://img.shields.io/badge/SECURITY-TOP--SECRET-red?style=for-the-badge&logo=lock)
![License](https://img.shields.io/badge/LICENSE-RESTRICTED-gray?style=for-the-badge&logo=github)

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)
![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react)
![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?style=flat-square&logo=typescript)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-326CE5?style=flat-square&logo=kubernetes)

**"Vigilantia Aeterna, Libertas Garantizada"**

[Instalación](#-instalación) • [Configuración](#-configuración) • [Uso](#-uso) • [API](#-api-documentation) • [Casos de Uso](#-casos-de-uso)

</div>

---

## 📋 TABLA DE CONTENIDOS

- [Visión General](#-visión-general)
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Características Principales](#-características-principales)
- [Requisitos del Sistema](#-requisitos-del-sistema)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Uso del Sistema](#-uso-del-sistema)
- [API Documentation](#-api-documentation)
- [Casos de Uso](#-casos-de-uso)
- [Monitoreo y Observabilidad](#-monitoreo-y-observabilidad)
- [Seguridad](#-seguridad)
- [Troubleshooting](#-troubleshooting)
- [Desarrollo](#-desarrollo)
- [Contribuir](#-contribuir)
- [Licencia](#-licencia)

---

## 👁️ VISIÓN GENERAL

**VIGÍA v2.1** es una plataforma de inteligencia OSINT/SOCMINT de grado militar diseñada para la monitorización masiva de amenazas en el espectro digital. El sistema combina análisis de inteligencia artificial multilingüe, cifrado de grado militar y arquitectura distribuida para proporcionar capacidades de detección de amenazas en tiempo real.

### 🎯 Capacidades Clave

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPACIDADES VIGÍA v2.1                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔐 SEGURIDAD DE GRADO MILITAR                                      │
│     • Cifrado AES-256-GCM para datos en reposo                      │
│     • JWT con HttpOnly cookies + MFA TOTP (RFC 6238)                │
│     • RBAC multinivel: CONFIDENTIAL / SECRET / TOP_SECRET           │
│     • Audit log blockchain-anchored (SHA-256 encadenado)            │
│                                                                     │
│  🧠 INTELIGENCIA ARTIFICIAL MULTILINGÜE                             │
│     • Transformer multilingüe (sentence-transformers)               │
│     • NER con spaCy (Personas, Ubicaciones, Organizaciones)         │
│     • Detección en 5 idiomas: ES, EN, AR, RU, ZH                    │
│     • Análisis semántico + keywords + TF-IDF                        │
│                                                                     │
│  🌐 MONITOREO MULTI-PLATAFORMA                                      │
│     • Twitter/X API v2, Reddit API, Telegram Bot API                │
│     • Facebook Graph API, TikTok, YouTube                           │
│     • Recolección paralela asíncrona (ARQ worker)                   │
│     • Rate limiting adaptativo por plataforma                       │
│                                                                     │
│  📊 VISUALIZACIÓN TÁCTICA                                           │
│     • Dashboard con heatmaps geoespaciales (Leaflet)                │
│     • Grafos de red social (Cytoscape)                              │
│     • Cola de alertas priorizada en tiempo real (WebSocket)         │
│     • Informes PDF con cifrado PGP opcional                         │
│                                                                     │
│  🔗 INTEROPERABILIDAD NATO                                          │
│     • STIX 2.1 / TAXII 2.1 para intercambio de IoCs                 │
│     • Integración SIEM: Splunk, ELK, QRadar, ArcSight               │
│     • Exportación a Europol SIENA, Interpol I-24/7                  │
│     • Prometheus + Grafana para observabilidad                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Diagrama de Arquitectura General

```mermaid
graph TB
    subgraph "🌐 CAPA DE PRESENTACIÓN"
        FE[Frontend React<br/>TypeScript + Tailwind]
        PWA[PWA<br/>Service Worker]
    end

    subgraph "🔌 CAPA DE API"
        API[FastAPI Backend<br/>Python 3.12]
        WS[WebSocket<br/>Alertas Real-time]
        AUTH[Auth Service<br/>JWT + MFA TOTP]
    end

    subgraph "🧠 CAPA DE ANÁLISIS"
        ORCH[Orchestrator<br/>Pipeline ML]
        ML[ML Analysis Agent<br/>Transformer + Keywords]
        NER[NER Agent<br/>spaCy Multilingüe]
        COMP[Compliance Agent<br/>Policy Validation]
        EXEC[Execution Agent<br/>Alert Routing]
    end

    subgraph "📊 CAPA DE DATOS"
        PG[(PostgreSQL 16<br/>Alertas + Audit Logs)]
        RD[(Redis 7<br/>Cache + Sessions + Queue)]
        ARQ[ARQ Worker<br/>Análisis Asíncrono]
    end

    subgraph "🔗 INTEGRACIONES EXTERNAS"
        TW[Twitter API v2]
        RD2[Reddit API]
        TG[Telegram Bot API]
        FB[Facebook Graph API]
        SIEM[SIEM<br/>Splunk/ELK/QRadar]
        NATO[STIX/TAXII<br/>NATO Bridge]
    end

    subgraph "📈 MONITOREO"
        PROM[Prometheus<br/>Métricas]
        GRAF[Grafana<br/>Dashboards]
    end

    FE --> API
    FE --> WS
    API --> AUTH
    API --> ORCH
    ORCH --> ML
    ORCH --> NER
    ORCH --> COMP
    ORCH --> EXEC
    ML --> PG
    NER --> PG
    COMP --> PG
    EXEC --> PG
    API --> PG
    API --> RD
    ARQ --> RD
    ARQ --> PG
    ORCH --> TW
    ORCH --> RD2
    ORCH --> TG
    ORCH --> FB
    EXEC --> SIEM
    EXEC --> NATO
    API --> PROM
    ARQ --> PROM
    PROM --> GRAF

    style FE fill:#3b82f6,stroke:#1e40af,color:#fff
    style API fill:#10b981,stroke:#059669,color:#fff
    style PG fill:#4169E1,stroke:#2c5aa0,color:#fff
    style RD fill:#DC382D,stroke:#b02a1f,color:#fff
    style ORCH fill:#f59e0b,stroke:#d97706,color:#fff
```

### Flujo de Análisis de Amenazas

```mermaid
sequenceDiagram
    participant A as Analista
    participant D as Dashboard
    participant API as FastAPI
    participant O as Orchestrator
    participant W as ARQ Worker
    participant ML as ML Agent
    participant DB as PostgreSQL
    participant WS as WebSocket

    A->>D: Lanzar Análisis
    D->>API: POST /api/analyze/async
    API->>W: Enqueue job (202 Accepted)
    API-->>D: job_id + status
    
    W->>O: run_analysis_pipeline()
    O->>ML: analyze_post_ml(post)
    ML-->>O: ThreatAssessment
    O->>DB: Persist alert
    DB-->>O: alert_id
    
    Note over DB,WS: Alerta ROJO detectada
    DB->>WS: Push notification
    WS->>D: Alerta en tiempo real
    D->>A: Notificación push
    
    A->>D: Revisar alerta
    D->>API: GET /api/alerts/{id}
    API->>DB: Fetch alert
    DB-->>API: alert_data
    API-->>D: Alert details
    D->>A: Mostrar indicadores
```

### Niveles de Clasificación de Seguridad

```
┌─────────────────────────────────────────────────────────────────┐
│                    NIVELES DE HABILITACIÓN                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  TOP_SECRET (Nivel 3)                                     │  │
│  │  • Acceso total al sistema                                │  │
│  │  • Puede lanzar análisis OSINT                            │  │
│  │  • Puede exportar a sistemas externos (STIX/TAXII)        │  │
│  │  • Puede gestionar usuarios y roles                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ▲                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  SECRET (Nivel 2)                                         │  │
│  │  • Acceso a alertas ROJO/NARANJA                          │  │
│  │  • Puede lanzar análisis OSINT                            │  │
│  │  • Puede revisar y escalar alertas                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                          ▲                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CONFIDENTIAL (Nivel 1)                                   │  │
│  │  • Acceso a alertas VERDE/AMARILLO                        │  │
│  │  • Puede ver dashboard y auditoría                        │  │
│  │  • Puede revisar alertas (no escalar)                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ CARACTERÍSTICAS PRINCIPALES

### 🔐 Seguridad de Grado Militar

| Característica | Implementación | Descripción |
|----------------|----------------|-------------|
| **Cifrado en reposo** | AES-256-GCM | Datos sensibles cifrados con AEAD |
| **Autenticación** | JWT + MFA TOTP | Access token 15min + Refresh 7d |
| **Cookies seguras** | HttpOnly + Secure + SameSite | Protección contra XSS y CSRF |
| **RBAC multinivel** | CONFIDENTIAL/SECRET/TOP_SECRET | Control de acceso granular |
| **Audit log inmutable** | HMAC-SHA256 + Blockchain | Integridad criptográfica |
| **Rate limiting** | Sliding window Redis | Protección contra brute force |
| **Account lockout** | 5 intentos → 15min bloqueo | Prevención de ataques |
| **Docker hardened** | cap_drop ALL, non-root, read_only | Contenedores seguros |

### 🧠 Inteligencia Artificial

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE ANÁLISIS ML                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. TRANSFORMER MULTILINGÜE                                     │
│     └─ sentence-transformers (paraphrase-multilingual-MiniLM)   │
│     └─ Similitud coseno contra anchor sentences                 │
│     └─ Soporte: ES, EN, AR, RU, ZH                              │
│                                                                 │
│  2. KEYWORD ANALYZER (Fallback)                                 │
│     └─ TF-IDF + Random Forest                                   │
│     └─ Búsqueda de keywords por categoría                       │
│     └─ Siempre disponible (offline-ready)                       │
│                                                                 │
│  3. NER MULTILINGÜE                                             │
│     └─ spaCy (xx_ent_wiki_sm)                                   │
│     └─ Extracción: Personas, Ubicaciones, Organizaciones        │
│     └─ Detección de armas por keywords multilingües             │
│                                                                 │
│  4. CATEGORÍAS DE AMENAZA                                       │
│     ├─ Amenaza directa (peso: 0.40)                             │
│     ├─ Coordinación de ataque (peso: 0.30)                      │
│     ├─ Llamada a violencia (peso: 0.20)                         │
│     ├─ Glorificación terrorismo (peso: 0.15)                    │
│     └─ Reclutamiento (peso: 0.10)                               │
│                                                                 │
│  5. NIVELES DE ALERTA                                           │
│     ├─ VERDE: score < 0.30 (archivo automático)                 │
│     ├─ AMARILLO: 0.30 ≤ score < 0.50 (revisión 48h)             │
│     ├─ NARANJA: 0.50 ≤ score < 0.75 (revisión 4h)               │
│     └─ ROJO: score ≥ 0.75 (escalada inmediata)                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 🌐 Plataformas Soportadas

| Plataforma | API | Autenticación | Rate Limit | Estado |
|------------|-----|---------------|------------|--------|
| **Twitter/X** | API v2 | Bearer Token | 450 req/15min | ✅ Activo |
| **Reddit** | OAuth2 | Client ID + Secret | 60 req/min | ✅ Activo |
| **Telegram** | Bot API | Bot Token | 30 req/sec | ✅ Activo |
| **Facebook** | Graph API | Access Token | 200 req/hr | ⚠️ Requiere config |
| **TikTok** | Research API | Access Token | 1000 req/day | 🔜 Próximamente |
| **YouTube** | Data API v3 | API Key | 10000 units/day | 🔜 Próximamente |

---

## 💻 REQUISITOS DEL SISTEMA

### Requisitos Mínimos

| Componente | Requisito | Recomendado |
|------------|-----------|-------------|
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 8 GB | 16+ GB |
| **Disco** | 50 GB SSD | 100+ GB SSD |
| **SO** | Linux (Ubuntu 22.04+) | Ubuntu 24.04 LTS |
| **Docker** | 24.0+ | 25.0+ |
| **Docker Compose** | 2.20+ | 2.25+ |
| **Python** | 3.12+ | 3.12.x |
| **Node.js** | 20 LTS | 20.x LTS |

### Requisitos de Red

```
┌─────────────────────────────────────────────────────────────────┐
│                    PUERTOS REQUERIDOS                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PUERTOS DE ENTRADA (Inbound):                                  │
│  ├─ 3000/tcp  → Frontend (HTTP)                                 │
│  ├─ 8000/tcp  → API Backend (HTTPS recomendado)                 │
│  ├─ 9090/tcp  → Prometheus (Opcional, solo admin)               │
│  └─ 3001/tcp  → Grafana (Opcional, solo admin)                  │
│                                                                 │
│  PUERTOS INTERNOS (Docker network):                             │
│  ├─ 5432/tcp  → PostgreSQL (No expuesto al host)                │
│  ├─ 6379/tcp  → Redis (No expuesto al host)                     │
│  └─ 9101/tcp  → Worker metrics (No expuesto al host)            │
│                                                                 │
│  PUERTOS DE SALIDA (Outbound):                                  │
│  ├─ 443/tcp   → APIs externas (Twitter, Reddit, etc.)           │
│  └─ 587/tcp   → SMTP (Notificaciones email, opcional)           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 INSTALACIÓN

### Método 1: Docker Compose (Recomendado)

#### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/murdok1982/SistemaVigiaSocmint.git
cd SistemaVigiaSocmint
```

#### Paso 2: Generar configuración automática

```bash
# Ejecutar script de setup (genera .env con claves aleatorias)
chmod +x scripts/setup.sh
./scripts/setup.sh
```

El script generará automáticamente:
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `JWT_SECRET_KEY`
- `VIGIA_MASTER_KEY`
- `VIGIA_HMAC_KEY`
- `HMAC_SECRET`
- `VIGIA_HASH_SALT`
- `VIGIA_API_KEY`
- `GRAFANA_ADMIN_PASSWORD`

#### Paso 3: Configurar APIs externas (Opcional)

Edita el archivo `.env` y añade tus tokens de APIs:

```bash
nano .env
```

```ini
# Twitter/X API v2
TWITTER_BEARER_TOKEN=AAAAAAAAAAAAAAAAAAAAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Reddit API
REDDIT_CLIENT_ID=xxxxxxxxxxxxxx
REDDIT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx

# Telegram Bot API
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Facebook Graph API
META_ACCESS_TOKEN=EAABsbCS1iHgBAxxxxxxxxxxxxxxxxxxxxxxxx

# SIEM Integration (Opcional)
SIEM_TYPE=splunk
SIEM_API_TOKEN=your-siem-token
SIEM_API_ENDPOINT=https://your-siem:8088/services/collector
```

#### Paso 4: Levantar el sistema

```bash
# Construir y levantar todos los servicios
docker-compose up -d --build

# Verificar estado de los contenedores
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f
```

#### Paso 5: Acceder al sistema

```
Frontend:   http://localhost:3000
API:        http://localhost:8000
API Docs:   http://localhost:8000/docs (solo en desarrollo)
Grafana:    http://localhost:3001
Prometheus: http://localhost:9090
```

**Credenciales iniciales:**
- Usuario: `admin`
- Contraseña: La definida en `VIGIA_ADMIN_BOOTSTRAP_PASSWORD` (o générala con `openssl rand -hex 16`)
- ⚠️ **IMPORTANTE**: El sistema te obligará a cambiar la contraseña en el primer login

### Método 2: Instalación Manual (Desarrollo)

#### Backend (Python)

```bash
# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Descargar modelos ML (opcional, ~470MB)
python -m spacy download xx_ent_wiki_sm

# Configurar variables de entorno
export VIGIA_ENV=development
export DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/vigia_db
export REDIS_URL=redis://localhost:6379
export JWT_SECRET_KEY=$(openssl rand -hex 32)
export VIGIA_MASTER_KEY=$(openssl rand -hex 32)
export VIGIA_HMAC_KEY=$(openssl rand -hex 32)
export HMAC_SECRET=$(openssl rand -hex 32)
export VIGIA_HASH_SALT=$(openssl rand -hex 16)
export VIGIA_API_KEY=$(openssl rand -hex 32)

# Iniciar servidor
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

#### Worker ARQ (Análisis asíncrono)

```bash
# En otra terminal
python -m arq src.worker.WorkerSettings
```

#### Frontend (React)

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm run dev
```

### Método 3: Kubernetes (Producción)

```bash
# Crear namespace
kubectl create namespace vigia-system

# Crear secrets
kubectl create secret generic vigia-secrets \
  --from-literal=POSTGRES_PASSWORD=$(openssl rand -hex 32) \
  --from-literal=REDIS_PASSWORD=$(openssl rand -hex 32) \
  --from-literal=JWT_SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=VIGIA_MASTER_KEY=$(openssl rand -hex 32) \
  --from-literal=VIGIA_HMAC_KEY=$(openssl rand -hex 32) \
  --from-literal=HMAC_SECRET=$(openssl rand -hex 32) \
  --from-literal=VIGIA_HASH_SALT=$(openssl rand -hex 16) \
  --from-literal=VIGIA_API_KEY=$(openssl rand -hex 32) \
  -n vigia-system

# Aplicar manifiestos
kubectl apply -f k8s/deployment.yaml -n vigia-system

# Verificar despliegue
kubectl get pods -n vigia-system
kubectl get services -n vigia-system
```

---

## ⚙️ CONFIGURACIÓN

### Variables de Entorno

#### Obligatorias

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `VIGIA_ENV` | Entorno (development/production) | `production` |
| `POSTGRES_USER` | Usuario PostgreSQL | `vigia` |
| `POSTGRES_PASSWORD` | Contraseña PostgreSQL | `openssl rand -hex 32` |
| `POSTGRES_DB` | Nombre de la base de datos | `vigia_db` |
| `REDIS_PASSWORD` | Contraseña Redis | `openssl rand -hex 32` |
| `JWT_SECRET_KEY` | Clave secreta JWT | `openssl rand -hex 32` |
| `VIGIA_MASTER_KEY` | Clave maestra de cifrado | `openssl rand -hex 32` |
| `VIGIA_HMAC_KEY` | Clave HMAC para audit logs | `openssl rand -hex 32` |
| `HMAC_SECRET` | Clave HMAC adicional | `openssl rand -hex 32` |
| `VIGIA_HASH_SALT` | Salt para hashing de IDs | `openssl rand -hex 16` |
| `VIGIA_API_KEY` | API key para autenticación | `openssl rand -hex 32` |

#### Opcionales

| Variable | Descripción | Default |
|----------|-------------|---------|
| `VIGIA_LOG_LEVEL` | Nivel de logging | `INFO` |
| `VIGIA_ALLOWED_ORIGINS` | Orígenes CORS permitidos | `http://localhost:3000` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Expiración access token | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Expiración refresh token | `7` |
| `WORKERS` | Número de workers Uvicorn | `4` |
| `VIGIA_DISABLE_TRANSFORMERS` | Desactivar modelos ML pesados | `false` |
| `TWITTER_BEARER_TOKEN` | Twitter API Bearer Token | - |
| `REDDIT_CLIENT_ID` | Reddit API Client ID | - |
| `REDDIT_CLIENT_SECRET` | Reddit API Client Secret | - |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | - |
| `SIEM_TYPE` | Tipo de SIEM (splunk/elk/qradar) | `splunk` |
| `SIEM_API_TOKEN` | Token API del SIEM | - |
| `GRAFANA_ADMIN_PASSWORD` | Contraseña admin Grafana | - |

### Configuración de ML

```ini
# Desactivar modelos transformer (ahorra ~470MB de RAM)
VIGIA_DISABLE_TRANSFORMERS=true

# Cambiar modelo transformer
VIGIA_TRANSFORMER_MODEL=paraphrase-multilingual-MiniLM-L12-v2

# Umbral de similitud para transformer (0.0 - 1.0)
VIGIA_TRANSFORMER_THRESHOLD=0.55

# Modelo spaCy para NER
VIGIA_SPACY_MODEL=xx_ent_wiki_sm
```

### Configuración de Rate Limiting

El sistema implementa rate limiting adaptativo por endpoint:

```python
# Configuración en src/api.py
RATE_LIMITS = {
    "/api/auth/login": (5, 60),      # 5 req/min (brute force protection)
    "/api/auth/refresh": (10, 60),   # 10 req/min
    "/api/analyze": (10, 60),        # 10 req/min
    "/api/reports/period": (5, 60),  # 5 req/min
    "/api/alerts": (100, 60),        # 100 req/min
    "/api/audit-log": (50, 60),      # 50 req/min
}
```

---

## 📖 USO DEL SISTEMA

### 1. Primer Login

```
┌─────────────────────────────────────────────────────────────────┐
│                    PANTALLA DE LOGIN                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  🛡️ VIGÍA Monitor                                        │  │
│  │  Acceso restringido — Personal autorizado                │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  Usuario: [___________________________]                  │  │
│  │                                                          │  │
│  │  Contraseña: [___________________________] 👁️            │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  ████████░░░░░░░░  Fuerte                          │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  [          Acceder          ]                           │  │
│  │                                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Pasos:**
1. Accede a `http://localhost:3000`
2. Introduce credenciales de admin
3. Si MFA está activado, introduce el código TOTP de tu app autenticadora
4. Cambia la contraseña obligatoria en el primer login

### 2. Dashboard Principal

```
┌─────────────────────────────────────────────────────────────────┐
│  🛡️ VIGÍA Monitor          [🔍 Buscar...]    [🌙] [👤 admin ▼] │
├──────────┬──────────────────────────────────────────────────────┤
│          │                                                      │
│  📊 Dash │  Centro de Monitoreo Táctico                         │
│          │  Sistema VIGÍA — Nivel: ESTATAL-MILITAR              │
│  📝 Audit│                                                      │
│          │  ┌──────┬──────┬──────┬──────┬──────┬──────┐        │
│  👥 Admin│  │Alertas│Pend. │ ROJO │NARANJ│AMARIL│VERDE │        │
│          │  │  127 │  23  │  5   │  12  │  18  │  92  │        │
│          │  └──────┴──────┴──────┴──────┴──────┴──────┘        │
│  [🚪 Salir]│                                                    │
│          │  [Cola de Alertas] [Mapa Táctico] [Grafos] [Informes]│
│          │                                                      │
│          │  ┌────────────────────────────────────────────────┐ │
│          │  │ 🔴 ROJO  │ Twitter │ "Coordinar ataque..."    │ │
│          │  │ 95%      │ 2h ago  │ 3 indicadores            │ │
│          │  ├────────────────────────────────────────────────┤ │
│          │  │ 🟠 NARANJA│ Reddit │ "Punto de encuentro..."  │ │
│          │  │ 68%       │ 4h ago │ 2 indicadores            │ │
│          │  ├────────────────────────────────────────────────┤ │
│          │  │ 🟡 AMARILLO│ Telegram │ "Hay que eliminar..." │ │
│          │  │ 42%        │ 6h ago  │ 1 indicador            │ │
│          │  └────────────────────────────────────────────────┘ │
│          │                                                      │
│          │  [ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ]  ← Paginación       │
│          │                                                      │
└──────────┴──────────────────────────────────────────────────────┘
```

**Funcionalidades:**
- **StatsBar**: Estadísticas en tiempo real (alertas totales, pendientes, por nivel)
- **Cola de Alertas**: Lista priorizada de alertas con filtros
- **Mapa Táctico**: Visualización geoespacial de alertas (Leaflet)
- **Grafos de Red**: Análisis de relaciones entre entidades (Cytoscape)
- **Informes**: Generador de informes PDF por periodo

### 3. Lanzar Análisis OSINT

```
┌─────────────────────────────────────────────────────────────────┐
│                    LANZAR ANÁLISIS OSINT                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Objetivo del Análisis:                                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Monitoreo de amenazas violentas en redes sociales       │  │
│  │  relacionadas con protestas en Madrid                    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Plataformas:                                                   │
│  ☑ Twitter/X    ☑ Reddit    ☐ Telegram    ☐ Facebook           │
│                                                                 │
│  Máximo de Resultados: [═══════════●══════] 250                │
│                                                                 │
│                              [ Cancelar ] [ 🚀 Lanzar ]         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Pasos:**
1. Click en "Lanzar Análisis" en el dashboard
2. Define el objetivo del análisis (mínimo 5 caracteres)
3. Selecciona las plataformas a monitorear
4. Ajusta el máximo de resultados por plataforma
5. Click en "Lanzar"
6. El análisis se ejecuta asíncronamente (worker ARQ)
7. Las alertas generadas aparecen en tiempo real vía WebSocket

### 4. Revisar Alerta

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Volver a la cola                                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  🔴 ROJO  │  Twitter │ 95.2% de riesgo │ PENDIENTE      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Contenido Completo:                                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  "Coordinar el ataque para el viernes a primera hora.    │  │
│  │   Punto de encuentro en la plaza central. Traed el       │  │
│  │   material necesario. Cuando llegue la señal, todas las   │  │
│  │   unidades ejecutan en simultáneo."                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Risk Score: [████████████████████░] 95.2% (Crítico)           │
│                                                                 │
│  Indicadores Detectados (3):                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  🔗 coordinacion_ataque │ Confianza: 92%                 │  │
│  │  "coordinar el ataque"                                   │  │
│  │  Posible coordinación detectada                          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  🔗 coordinacion_ataque │ Confianza: 88%                 │  │
│  │  "punto de encuentro"                                    │  │
│  │  Posible coordinación detectada                          │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  🔗 coordinacion_ataque │ Confianza: 85%                 │  │
│  │  "ejecutan en simultáneo"                                │  │
│  │  Posible coordinación detectada                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  Acción del Analista:                                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Justificación:                                          │  │
│  │  [____________________________________________________]  │  │
│  │  [____________________________________________________]  │  │
│  │  [____________________________________________________]  │  │
│  │                                                          │  │
│  │  [ 🔴 Escalar ] [ 📁 Archivar ] [ ❌ Falso Positivo ]   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Acciones disponibles:**
- **Escalar**: Remitir a autoridad superior (requiere clearance SECRET+)
- **Archivar**: Registrar sin acción inmediata
- **Falso Positivo**: Marcar como no amenaza

### 5. Generar Informes PDF

```
┌─────────────────────────────────────────────────────────────────┐
│                    GENERADOR DE INFORMES                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Tipo de Informe:                                               │
│  [ Diario ] [ Semanal ] [ Personalizado ]                       │
│                                                                 │
│  Rango de Fechas (solo personalizado):                          │
│  [2024-01-01] → [2024-01-31]                                    │
│                                                                 │
│  Clasificación:                                                 │
│  ◉ CONFIDENCIAL   ○ SECRETO   ○ TOP SECRET                     │
│                                                                 │
│  Formato de Exportación:                                        │
│  [ PDF ] [ STIX ] [ JSON ] [ CSV ]                              │
│                                                                 │
│  [ 📥 Generar Informe ]                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6. Atajos de Teclado

| Atajo | Acción |
|-------|--------|
| `Ctrl + K` | Enfocar búsqueda |
| `Ctrl + 1` | Ir al Dashboard |
| `Ctrl + 2` | Ir a Auditoría |
| `Ctrl + 3` | Ir a Administración |
| `Escape` | Cerrar modales |

### 7. Modo Oscuro/Claro

Click en el icono 🌙/☀️ en el sidebar para alternar entre modos. La preferencia se guarda en `localStorage`.

### 8. Cambiar Idioma

Selecciona el idioma en el dropdown del sidebar:
- 🇪🇸 Español
- 🇬🇧 English

---

## 📡 API DOCUMENTATION

### Autenticación

#### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password",
  "mfa_token": "123456"  // Opcional si MFA está activado
}
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Cookies establecidas:**
- `access_token`: HttpOnly, Secure, SameSite=Lax, Max-Age=900
- `refresh_token`: HttpOnly, Secure, SameSite=Lax, Max-Age=604800

#### Refresh Token

```http
POST /api/auth/refresh
Cookie: refresh_token=eyJhbGciOiJIUzI1NiIs...
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### Logout

```http
POST /api/auth/logout
Cookie: refresh_token=eyJhbGciOiJIUzI1NiIs...
```

### Alertas

#### Listar Alertas

```http
GET /api/alerts?risk_level=ROJO&platform=twitter&status=PENDIENTE&page=1&page_size=20
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Respuesta:**
```json
{
  "items": [
    {
      "id": "abc123...",
      "platform": "Twitter",
      "content_excerpt": "Coordinar el ataque...",
      "indicators": [
        {
          "type": "coordinacion_ataque",
          "value": "coordinar el ataque",
          "explanation": "Posible coordinación detectada",
          "confidence": 0.92
        }
      ],
      "risk_score": 0.952,
      "risk_level": "ROJO",
      "status": "PENDIENTE",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 127,
  "page": 1,
  "page_size": 20
}
```

#### Obtener Detalle de Alerta

```http
GET /api/alerts/{alert_id}
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

#### Revisar Alerta

```http
POST /api/alerts/{alert_id}/review
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "action": "ESCALAR",
  "notes": "Amenaza coordinada detectada. Requiere intervención inmediata.",
  "analyst_id": "ANL-001"
}
```

### Análisis

#### Lanzar Análisis Síncrono

```http
POST /api/analyze?objective=Monitoreo+de+amenazas&platforms=twitter,reddit&max_results=100
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Respuesta:**
```json
{
  "objective": "Monitoreo de amenazas",
  "selected_agents": ["STRATEGY_AGENT", "RESEARCH_AGENT", "ML_ANALYSIS_AGENT"],
  "reasoning_summary": "Se analizaron 150 publicaciones...",
  "actions": [
    {
      "step": 1,
      "agent": "STRATEGY_AGENT",
      "task": "Generar plan de monitoreo",
      "status": "completed"
    }
  ],
  "final_recommendation": "Pipeline completado: 150 posts analizados...",
  "requires_human_approval": true,
  "audit_note": "sesion=abc123..."
}
```

#### Lanzar Análisis Asíncrono (Recomendado)

```http
POST /api/analyze/async?objective=Monitoreo+de+amenazas&platforms=twitter,reddit&max_results=100
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Respuesta (202 Accepted):**
```json
{
  "job_id": "job_abc123...",
  "status": "queued"
}
```

### Informes

#### Generar Informe PDF por Periodo

```http
POST /api/reports/period
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "date_from": "2024-01-01",
  "date_to": "2024-01-31",
  "classification": "CONFIDENTIAL",
  "recipient_pgp_pubkey": "-----BEGIN PGP PUBLIC KEY BLOCK-----..."
}
```

**Respuesta:** `application/pdf` (binary)

### Exportación STIX

#### Exportar Alertas en STIX 2.1

```http
GET /api/alerts/export.stix?ids=abc123,def456
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**Respuesta:**
```json
{
  "type": "bundle",
  "id": "bundle--abc123...",
  "objects": [
    {
      "type": "indicator",
      "id": "indicator--abc123...",
      "name": "VIGÍA Alert - ROJO",
      "pattern": "[content: 'Coordinar el ataque...']",
      "confidence": 95,
      "labels": ["twitter", "ROJO"]
    }
  ]
}
```

### WebSocket

#### Suscripción a Alertas en Tiempo Real

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/alerts?token=YOUR_JWT_TOKEN');

ws.onmessage = (event) => {
  const alerts = JSON.parse(event.data);
  console.log('Nuevas alertas:', alerts);
};
```

---

## 🎯 CASOS DE USO

### Caso de Uso 1: Detección de Amenazas Terroristas

**Escenario:** Agencia de inteligencia necesita monitorear posibles amenazas terroristas en redes sociales durante un evento masivo.

**Flujo:**
1. Analista lanza análisis con objetivo: "Detección de amenazas terroristas durante concierto en Madrid"
2. Sistema recolecta posts de Twitter, Reddit y Telegram con keywords relacionados
3. ML Agent analiza cada post con transformer multilingüe + NER
4. Se detectan 3 alertas ROJO con indicadores de coordinación de ataque
5. Analista revisa alertas y escala a autoridad superior
6. Se genera informe PDF clasificado como SECRETO
7. Informe se exporta en formato STIX 2.1 para compartir con Europol

**Resultado:** Amenaza detectada y neutralizada antes del evento.

### Caso de Uso 2: Monitoreo de Protestas Violentas

**Escenario:** Fuerzas de seguridad necesitan anticipar posibles actos violentos durante protestas.

**Flujo:**
1. Analista configura monitoreo continuo de keywords relacionados con protestas
2. Sistema detecta posts con llamadas a violencia y reclutamiento
3. Alertas NARANJA se generan y se ponen en cola de revisión
4. Analista revisa alertas y marca algunas como falsos positivos
5. Se genera informe semanal con estadísticas de amenazas
6. Informe se envía a SIEM (Splunk) para correlación con otros eventos

**Resultado:** Anticipación de actos violentos y despliegue preventivo de efectivos.

### Caso de Uso 3: Análisis de Redes de Desinformación

**Escenario:** Identificación de campañas coordinadas de desinformación.

**Flujo:**
1. Analista lanza análisis de grafos de red social
2. Sistema identifica entidades (personas, organizaciones) mencionadas en alertas
3. Grafo de relaciones muestra clusters de cuentas coordinadas
4. Analista detecta patrón de coordinación entre 15 cuentas
5. Se exporta grafo en formato JSON para análisis adicional
6. Informe se comparte con unidad de ciberinteligencia

**Resultado:** Red de desinformación identificada y documentada.

### Caso de Uso 4: Integración con Centro de Ciberseguridad

**Escenario:** Centro de operaciones de seguridad (SOC) necesita correlacionar amenazas físicas y cibernéticas.

**Flujo:**
1. VIGÍA detecta amenazas físicas en redes sociales
2. Alertas se envían automáticamente al SIEM vía HEC (Splunk)
3. SIEM correlaciona amenazas físicas con incidentes cibernéticos
4. Dashboard de Grafana muestra métricas combinadas
5. Equipo de seguridad tiene visión 360° de amenazas

**Resultado:** Detección temprana de ataques coordinados físico-cibernéticos.

### Caso de Uso 5: Evidencia Judicial

**Escenario:** Fiscal necesita evidencia digital para proceso judicial.

**Flujo:**
1. Analista genera informe PDF clasificado como SECRETO
2. Informe incluye audit log con HMAC-SHA256 (integridad criptográfica)
3. Informe se cifra con PGP usando clave pública del juzgado
4. Cadena de custodia documentada con blockchain audit chain
5. Evidencia es admisible en proceso judicial

**Resultado:** Evidencia digital con integridad garantizada y cadena de custodia.

---

## 📊 MONITOREO Y OBSERVABILIDAD

### Prometheus Metrics

El sistema expone métricas en formato Prometheus:

```
# API Metrics
vigia_alerts_total 127
vigia_alerts_by_level{level="ROJO"} 5
vigia_alerts_by_level{level="NARANJA"} 12
vigia_alerts_by_level{level="AMARILLO"} 18
vigia_alerts_by_level{level="VERDE"} 92
vigia_alerts_pending 23
vigia_uptime_seconds 86400

# Worker Metrics
vigia_worker_jobs_processed_total{job_name="run_analysis_worker",status="success"} 45
vigia_worker_jobs_processed_total{job_name="run_analysis_worker",status="failed"} 2
vigia_worker_job_duration_seconds{job_name="run_analysis_worker"} 12.5
```

**Endpoint:** `GET /api/metrics` (requiere autenticación)

### Grafana Dashboards

Accede a Grafana en `http://localhost:3001` (credenciales configuradas en `.env`).

**Dashboard preconfigurado:**
- Total de alertas
- Alertas por nivel (gráfico temporal)
- Alertas pendientes (gauge)
- Uptime del sistema

### Logs

Los logs se escriben en `./logs/` con formato estructurado:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "src.api",
  "message": "Alerta persistida en BD",
  "alert_id": "abc123..."
}
```

---

## 🔒 SEGURIDAD

### Modelo de Amenazas

```
┌─────────────────────────────────────────────────────────────────┐
│                    VECTORES DE ATAQUE MITIGADOS                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ XSS (Cross-Site Scripting)                                  │
│     └─ HttpOnly cookies + CSP headers + React auto-escaping     │
│                                                                 │
│  ✅ CSRF (Cross-Site Request Forgery)                           │
│     └─ SameSite=Lax cookies + CORS estricto                     │
│                                                                 │
│  ✅ SQL Injection                                               │
│     └─ SQLAlchemy ORM (queries parametrizadas)                  │
│                                                                 │
│  ✅ Brute Force                                                 │
│     └─ Rate limiting 5/min + account lockout 15min              │
│                                                                 │
│  ✅ JWT Theft                                                   │
│     └─ HttpOnly cookies + short-lived tokens (15min)            │
│                                                                 │
│  ✅ Data at Rest                                                │
│     └─ AES-256-GCM encryption + key rotation                    │
│                                                                 │
│  ✅ Audit Log Tampering                                         │
│     └─ HMAC-SHA256 + blockchain chain hashing                   │
│                                                                 │
│  ✅ Container Escape                                            │
│     └─ cap_drop ALL + non-root + read_only rootfs               │
│                                                                 │
│  ✅ SSRF (Server-Side Request Forgery)                          │
│     └─ URLs externas solo desde configuración                   │
│                                                                 │
│  ✅ Denial of Service                                           │
│     └─ Rate limiting adaptativo + Redis sliding window          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### OWASP Top 10 Compliance

| OWASP | Estado | Implementación |
|-------|--------|----------------|
| A01: Broken Access Control | ✅ | RBAC + clearance levels |
| A02: Cryptographic Failures | ✅ | AES-256-GCM + bcrypt + JWT |
| A03: Injection | ✅ | ORM + Pydantic validation |
| A04: Insecure Design | ✅ | Threat modeling + rate limiting |
| A05: Security Misconfiguration | ✅ | Docker hardened + security headers |
| A06: Vulnerable Components | ✅ | Dependencies audit + PyJWT (no CVE) |
| A07: Authentication Failures | ✅ | MFA TOTP + brute force protection |
| A08: Data Integrity | ✅ | HMAC + blockchain audit chain |
| A09: Logging Failures | ✅ | Structured logs + no secrets |
| A10: SSRF | ✅ | No user-controlled URLs |

### Auditoría de Seguridad

El sistema ha pasado por 3 fases de auditoría:

1. **FASE 1**: OWASP Top 10 básico → 8 hallazgos corregidos
2. **FASE 2**: Auditoría tras 12 mejoras → 2 hallazgos ALTOS corregidos
3. **FASE 3**: GATE FINAL → 0 CRÍTICAS, 0 ALTAS pendientes

**Hallazgos pendientes (BAJOS):**
- SameSite=Lax vs Strict (aceptable con CORS actual)
- WebSocket token en query params (limitación técnica)

---

## 🐛 TROUBLESHOOTING

### Problema: No puedo acceder al frontend

**Síntoma:** `http://localhost:3000` no responde

**Solución:**
```bash
# Verificar que el contenedor frontend está corriendo
docker-compose ps frontend

# Ver logs del frontend
docker-compose logs frontend

# Reiniciar el contenedor
docker-compose restart frontend
```

### Problema: Error de autenticación "Token inválido"

**Síntoma:** Login correcto pero requests a API devuelven 401

**Causa:** Token expirado o cookies no se establecieron correctamente

**Solución:**
```bash
# Verificar que las cookies se establecieron
# En navegador: DevTools → Application → Cookies → localhost:3000
# Debe haber: access_token y refresh_token

# Si no hay cookies, verificar CORS en backend
# En .env:
VIGIA_ALLOWED_ORIGINS=http://localhost:3000

# Reiniciar backend
docker-compose restart api
```

### Problema: Worker no procesa jobs

**Síntoma:** `/api/analyze/async` devuelve 202 pero no se generan alertas

**Solución:**
```bash
# Verificar que el worker está corriendo
docker-compose ps worker

# Ver logs del worker
docker-compose logs worker

# Verificar conexión a Redis
docker-compose exec worker python -c "import redis; r = redis.Redis(host='redis', password='YOUR_PASSWORD'); print(r.ping())"

# Reiniciar worker
docker-compose restart worker
```

### Problema: Modelos ML no cargan

**Síntoma:** Logs muestran "ML: no se pudo cargar el transformer"

**Causa:** Modelos transformer no descargados o RAM insuficiente

**Solución:**
```bash
# Opción 1: Descargar modelos (~470MB)
docker-compose exec api python -m spacy download xx_ent_wiki_sm

# Opción 2: Desactivar transformer (usar solo keywords)
# En .env:
VIGIA_DISABLE_TRANSFORMERS=true

# Reiniciar backend
docker-compose restart api
```

### Problema: PostgreSQL no inicia

**Síntoma:** `docker-compose up` falla con error de PostgreSQL

**Solución:**
```bash
# Verificar logs de PostgreSQL
docker-compose logs db

# Si el error es "database already exists", eliminar volumen
docker-compose down -v
docker-compose up -d

# ⚠️ ADVERTENCIA: Esto elimina todos los datos
```

### Problema: Rate limiting bloquea requests legítimos

**Síntoma:** Requests devuelven 429 "Demasiadas peticiones"

**Solución:**
```bash
# Aumentar límites en src/api.py
RATE_LIMITS = {
    "/api/auth/login": (10, 60),  # Aumentar de 5 a 10
    "/api/analyze": (20, 60),     # Aumentar de 10 a 20
}

# Reiniciar backend
docker-compose restart api
```

### Problema: Grafana no muestra métricas

**Síntoma:** Dashboard de Grafana muestra "No data"

**Solución:**
```bash
# Verificar que Prometheus está scrapeando
curl http://localhost:9090/api/v1/targets

# Verificar que /api/metrics requiere autenticación
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/metrics

# Verificar datasource en Grafana
# Grafana → Configuration → Data Sources → Prometheus
# URL debe ser: http://prometheus:9090
```

---

## 👨‍💻 DESARROLLO

### Estructura del Proyecto

```
SistemaVigiaSocmint/
├── src/                          # Backend Python
│   ├── api.py                    # FastAPI endpoints
│   ├── auth.py                   # Autenticación JWT + MFA
│   ├── database.py               # SQLAlchemy models
│   ├── models.py                 # Pydantic schemas
│   ├── cache.py                  # Redis cache + rate limiting
│   ├── crypto_utils.py           # Cifrado AES-256-GCM
│   ├── orchestrator.py           # Pipeline de análisis
│   ├── worker.py                 # ARQ worker asíncrono
│   ├── audit_chain.py            # Blockchain audit log
│   ├── reports.py                # Generación de PDFs
│   ├── stix_taxii.py             # STIX 2.1 / TAXII 2.1
│   ├── siem_integration.py       # Integración SIEM
│   └── agents/                   # Agentes de análisis
│       ├── strategy_agent.py
│       ├── real_data_collector.py
│       ├── ml_analysis_agent.py
│       ├── compliance_agent.py
│       └── execution_agent.py
├── frontend/                     # Frontend React
│   ├── src/
│   │   ├── App.tsx               # Router + layout
│   │   ├── pages/                # Páginas
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── AlertDetail.tsx
│   │   │   ├── AuditPage.tsx
│   │   │   └── AdminPage.tsx
│   │   ├── components/           # Componentes reutilizables
│   │   │   ├── AlertCard.tsx
│   │   │   ├── AlertQueue.tsx
│   │   │   ├── StatsBar.tsx
│   │   │   ├── MapView.tsx
│   │   │   ├── NetworkGraph.tsx
│   │   │   ├── ReportGenerator.tsx
│   │   │   ├── RunAnalysisModal.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── RiskBadge.tsx
│   │   └── lib/                  # Utilidades
│   │       ├── api.ts            # API client
│   │       ├── auth.ts           # Auth helpers
│   │       ├── AuthContext.tsx   # Auth context
│   │       ├── types.ts          # TypeScript types
│   │       ├── utils.ts          # Utility functions
│   │       ├── useTheme.ts       # Dark/Light mode
│   │       ├── i18n.ts           # Internacionalización
│   │       ├── pushNotifications.ts
│   │       └── useKeyboardShortcuts.ts
│   ├── public/
│   │   ├── manifest.json         # PWA manifest
│   │   └── sw.js                 # Service Worker
│   └── package.json
├── tests/                        # Tests Python
│   ├── test_crypto.py
│   ├── test_auth_unit.py
│   ├── test_audit_chain.py
│   ├── test_worker.py
│   └── test_ml_analysis.py
├── k8s/                          # Kubernetes manifests
│   └── deployment.yaml
├── monitoring/                   # Prometheus + Grafana
│   ├── prometheus.yml
│   └── grafana/
│       ├── datasources/
│       └── dashboards/
├── scripts/                      # Scripts de utilidad
│   ├── setup.sh                  # Setup automático
│   └── entrypoint.sh             # Docker entrypoint
├── docker-compose.yml            # Docker Compose (7 servicios)
├── Dockerfile.api                # Backend Dockerfile
├── Dockerfile.worker             # Worker Dockerfile
├── requirements.txt              # Python dependencies
├── alembic.ini                   # Alembic config
└── README.md                     # Este archivo
```

### Ejecutar Tests

```bash
# Tests unitarios (no requieren servicios externos)
pytest tests/test_crypto.py tests/test_auth_unit.py tests/test_audit_chain.py tests/test_worker.py -v

# Tests de integración (requieren PostgreSQL + Redis)
pytest tests/test_security.py tests/test_ml_analysis.py -v

# Cobertura de código
pytest --cov=src --cov-report=html
```

### Linting y Formateo

```bash
# Python
black src/ tests/
isort src/ tests/
flake8 src/ tests/
mypy src/

# Frontend
cd frontend
npm run lint
npm run format  # Si tienes Prettier configurado
```

### Build de Producción

```bash
# Backend (no necesita build, es Python)

# Frontend
cd frontend
npm run build
# Output: frontend/dist/

# Docker
docker-compose build
```

---

## 🤝 CONTRIBUIR

### Proceso de Contribución

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'Add: AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abre** un Pull Request

### Estándares de Código

- **Python**: Sigue PEP 8, usa type hints, documenta funciones complejas
- **TypeScript**: Usa tipos estrictos, evita `any`, documenta componentes
- **Commits**: Sigue Conventional Commits (`feat:`, `fix:`, `docs:`, etc.)
- **Tests**: Cobertura mínima 80% para código nuevo
- **Seguridad**: Nunca commitear secrets, usar variables de entorno

### Código de Conducta

- Respeto hacia todos los contribuidores
- Comunicación profesional y constructiva
- Enfoque en la calidad y seguridad del código
- Revisión de código obligatoria antes de merge

---

## 📜 LICENCIA

Este producto se distribuye bajo la **Licencia de Uso Restringido Estado-Militar (RSM-L)**.

### Términos Clave

- ✅ **PERMITIDO**: Uso por agencias gubernamentales y de defensa autorizadas
- ❌ **PROHIBIDO**: Redistribución a terceros no autorizados
- ❌ **PROHIBIDO**: Ingeniería inversa o decompilación
- ❌ **PROHIBIDO**: Uso comercial sin licencia explícita
- ⚠️ **RESTRICCIÓN**: Requiere habilitación de seguridad activa para uso

### Contacto para Licencias

Para solicitudes de licencia o consultas legales:
- **Email**: gustavolobatoclara@gmail.com
- **Asunto**: [LICENCIA] - Solicitud de uso

---

## 📞 SOPORTE Y CONTACTO

### Reportar Incidencias

| Tipo | Email | Asunto |
|------|-------|--------|
| **Bug/Error** | gustavolobatoclara@gmail.com | `[BUG] - Descripción breve` |
| **Seguridad** | gustavolobatoclara@gmail.com | `[SEGURIDAD] - Descripción breve` |
| **Feature Request** | gustavolobatoclara@gmail.com | `[FEATURE] - Descripción breve` |
| **Licencia** | gustavolobatoclara@gmail.com | `[LICENCIA] - Descripción breve` |

### Documentación Adicional

- [API Documentation (Swagger)](http://localhost:8000/docs) - Solo en desarrollo
- [Wiki del Proyecto](https://github.com/murdok1982/SistemaVigiaSocmint/wiki)
- [Video Tutorials](https://www.youtube.com/playlist?list=PL...) - Próximamente

---

<div align="center">

## 🛡️ VIGÍA v2.1 — "Vigilantia Aeterna, Libertas Garantizada"

![VIGÍA System](https://img.shields.io/badge/VIGÍA-v2.1-0052FF?style=for-the-badge&logo=shield)
![Status](https://img.shields.io/badge/STATUS-OPERATIONAL-green?style=for-the-badge&logo=checkmarx)
![Security](https://img.shields.io/badge/SECURITY-TOP--SECRET-red?style=for-the-badge&logo=lock)

**Sistema OSINT/SOCMINT de Grado Militar**

[Documentación](#-tabla-de-contenidos) • [Instalación](#-instalación) • [API](#-api-documentation) • [Soporte](#-soporte-y-contacto)

</div>

---

## 🎖️ CENTRO DE COMUNICACIONES Y REPORTES OFICIALES
**NIVEL DE ACCESO:** AUTORIZADO | **DESTINATARIO:** COMANDANCIA DE DESARROLLO (gustavolobatoclara@gmail.com)

A través del siguiente portal de comunicaciones, el personal autorizado puede emitir reportes de incidencias, fallas críticas en despliegue (compilación) o solicitudes de mejoras estratégicas. Seleccione la directiva correspondiente para visualizar los protocolos de envío:

<details>
<summary><b>🚨 REPORTAR QUEJA O INCIDENCIA DISCIPLINARIA / OPERATIVA</b></summary>
<br>
Para tramitar una queja sobre el funcionamiento, estructura o contenido del sistema, envíe un mensaje a <b>gustavolobatoclara@gmail.com</b> siguiendo este protocolo:
<ol>
  <li><b>Asunto:</b> [QUEJA] - Nombre del Sistema - Breve descripción.</li>
  <li><b>Cuerpo del mensaje:</b> Detallar claramente la incidencia, impacto operativo y, si es posible, la evidencia (capturas o logs).</li>
  <li><b>Prioridad:</b> Indicar si es de atención inmediata o diferida.</li>
</ol>
</details>

<details>
<summary><b>🛠️ REPORTE DE PROBLEMAS DE COMPILACIÓN O DESPLIEGUE</b></summary>
<br>
Si experimenta fallos durante la fase de compilación o instalación del sistema, reporte a <b>gustavolobatoclara@gmail.com</b> con la siguiente estructura técnica:
<ol>
  <li><b>Asunto:</b> [COMPILACIÓN] - Falla en entorno &lt;Entorno/OS&gt;.</li>
  <li><b>Especificaciones:</b> Sistema Operativo, versión de dependencias y herramientas de compilación utilizadas.</li>
  <li><b>Traza de Error (Logs):</b> Adjunte el log completo de errores proporcionado por la terminal (en formato texto o captura legible).</li>
  <li><b>Pasos de Reproducción:</b> Secuencia exacta de comandos ejecutados antes del fallo crítico.</li>
</ol>
</details>

<details>
<summary><b>💡 SUGERENCIAS O SOLICITUDES DE DESARROLLO</b></summary>
<br>
Para proponer nuevas capacidades tácticas, módulos de inteligencia o mejoras de arquitectura, envíe su solicitud a <b>gustavolobatoclara@gmail.com</b>:
<ol>
  <li><b>Asunto:</b> [PROPUESTA] - Mejora o Nuevo Módulo.</li>
  <li><b>Objetivo Táctico:</b> ¿Qué problema resuelve o qué ventaja proporciona esta nueva característica?</li>
  <li><b>Viabilidad:</b> (Opcional) Posible enfoque técnico o herramientas recomendadas para su implementación.</li>
</ol>
</details>

---

---

## Support / Apoya este proyecto

I build open-source projects focused on applied AI, automation, and data intelligence.
Over on my GitHub you'll find things like AI-powered analysis engines, OSINT platforms for open-source research, Windows automation tools, and experiments with language models.
Everything is public and free, so anyone can use it, study it, or build on top of it. github.com/murdok1982

Keeping these projects alive takes a lot of hours. If any of them have helped you out or you just like what I'm doing, you can support me with a coffee: ko-fi.com/murdok1982

Every contribution goes straight back into shipping more open-source code.

---

**Última actualización**: 2026-06-16  
**Versión**: 2.1.0  
**Estado**: ✅ Operativo y Verificado
