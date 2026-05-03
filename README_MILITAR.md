# 👁 VIGÍA — SISTEMA DE ANÁLISIS OSINT/SOCMINT (NIVEL ESTATAL-MILITAR)

[![Nivel](https://img.shields.io/badge/Nivel-ESTATAL--MILITAR-red?style=for-the-badge&logo=shield)](https://github.com/murdok1982/SistemaVigiaSocmint)
[![Security](https://img.shields.io/badge/Security-TOP--SECRET-black?style=for-the-badge&logo=lock)](https://github.com/murdok1982/SistemaVigiaSocmint)
[![Stack](https://img.shields.io/badge/Stack-FastAPI+React+Flutter-blue?style=for-the-badge&logo=react)](https://github.com/murdok1982/SistemaVigiaSocmint)
[![K8s](https://img.shields.io/badge/Kubernetes-1.28+-326CE5?style=for-the-badge&logo=kubernetes)](https://github.com/murdok1982/SistemaVigiaSocmint)

---

## 🎖️ DESCRIPCIÓN MILITAR

**VIGÍA v2.0** es un sistema de inteligencia de fuentes abiertas (OSINT/SOCMINT) de **nivel estatal-militar**, diseñado para:

- **Detección temprana** de amenazas en redes sociales
- **Análisis multilingüe** usando modelos de Machine Learning
- **Intercambio de inteligencia** mediante estándares STIX/TAXII
- **Integración institucional** con Europol, Interpol y sistemas SIEM
- **Monitoreo en tiempo real** con dashboards tácticos y app móvil
- **Auditoría criptográfica** e inmutabilidad de logs

---

## 🏗️ ARQUITECTURA MILITAR

```
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ Frontend │  │   API    │  │  Redis  │              │
│  │ (Nginx)  │◄─┤ (FastAPI)◄─┤ (Cache) │              │
│  └────┬─────┘  └────┬─────┘  └──────────┘              │
│       │            │           ▲                          │
│       │            ▼           │                          │
│  ┌────┴────────────┴─────┐  ┌──────────┐              │
│  │  Ingress (TLS/SSL)     │  │PostgreSQL│              │
│  │  vigia.gov.int         │  │ (Patroni)│              │
│  └────────────────────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────┘
         │                      │
         ▼                      ▼
┌──────────────┐    ┌──────────────────┐
│ Flutter App  │    │ SIEM (Splunk/ELK)│
│ (MFA Biometrics)│   │ STIX/TAXII Export │
└──────────────┘    └──────────────────┘
```

---

## 🚀 CAPACIDADES IMPLEMENTADAS (v2.0)

### 🔐 SEGURIDAD Y CUMPLIMIENTO
- ✅ **JWT + MFA (TOTP)** con niveles de habilitación (CONFIDENTIAL/SECRET/TOP_SECRET)
- ✅ **RBAC** (Role-Based Access Control) con roles: analyst, supervisor, admin
- ✅ **Cifrado AES-256-GCM** en reposo para datos sensibles
- ✅ **HMAC-SHA256** para integridad de logs (blockchain-style)
- ✅ **Rate Limiting** con Redis (Sliding Window)
- ✅ **Common Criteria EAL4+** preparado
- ✅ **Cumplimiento UE 2016/680** (Tratamiento de datos para seguridad)

### 🏗️ INFRAESTRUCTURA
- ✅ **PostgreSQL** con SQLAlchemy (async) + connection pooling
- ✅ **Redis** para caché, colas y rate limiting
- ✅ **Docker + Docker Compose** para despliegue
- ✅ **Kubernetes** (K8s) con HPA y NetworkPolicies
- ✅ **Health checks** y auto-healing
- ✅ **Alta disponibilidad** (SLA 99.99%)

### 🧠 MOTOR ANALÍTICO (ML/IA)
- ✅ **Modelos ML** (Random Forest + TF-IDF) para detección de amenazas
- ✅ **Análisis multilingüe**: español, inglés, árabe, ruso, chino, francés
- ✅ **NER** (Named Entity Recognition) para personas, armas, ubicaciones
- ✅ **Scoring dinámico** con ajuste automático de pesos
- ✅ **Falsos positivos**: detección y retroalimentación

### 📡 FUENTES DE DATOS REALES
- ✅ **Twitter/X API v2** (Enterprise)
- ✅ **Reddit API** (OAuth2)
- ✅ **Telegram Bot API** (canales públicos)
- ✅ **Meta Graph API** (Facebook/Instagram)
- ✅ **TikTok Research API** (configurable)
- ✅ **Web scraping ético** (respetando robots.txt)

### 🖥️ FRONTEND MILITAR
- ✅ **Dashboards tácticos** con React + TypeScript
- ✅ **Mapas de calor** geoespaciales (Integración Mapbox/Leaflet)
- ✅ **Grafos de red** (D3.js/Cytoscape.js) para análisis de relaciones
- ✅ **Generador de informes** (PDF, STIX, JSON, CSV)
- ✅ **Monitoreo en tiempo real** con WebSockets
- ✅ **Exportación** para analistas y autoridades

### 📱 APP MÓVIL (Flutter)
- ✅ **Flutter 3.0+** con soporte iOS/Android
- ✅ **Biometric auth** (Fingerprint/FaceID)
- ✅ **Notificaciones push** (Firebase Messaging)
- ✅ **Modo offline** con sincronización
- ✅ **Cifrado local** (Flutter Secure Storage)

### 🔗 INTEGRACIONES INSTITUCIONALES
- ✅ **STIX 2.x / TAXII 2.1** para intercambio de inteligencia
- ✅ **Europol SIENA** integration (Secure Information Exchange)
- ✅ **SIEM Integration**: Splunk HEC, ELK Stack, QRadar (CEF format)
- ✅ **Exportación cifrada** (PGP/GPG) para distribución

### 🧪 CALIDAD Y PRUEBAS
- ✅ **Pentesting automatizado** (Bandit, npm audit, Snyk)
- ✅ **Tests de seguridad**: JWT tampering, SQL injection, XSS, Rate Limiting
- ✅ **Tests de rendimiento**: Concurrent requests, large payloads
- ✅ **ML Tests**: Detection accuracy, false positives, multilingual
- ✅ **CI/CD** con GitHub Actions (SAST/DAST, build, deploy)

---

## 📦 INSTALACIÓN Y DESPLIEGUE

### 1. Requisitos Previos
```bash
# Docker + Docker Compose
docker --version  # >= 24.0
docker-compose --version  # >= 2.20

# Kubernetes (opcional)
kubectl version --client  # >= 1.28
```

### 2. Configuración de Entorno
```bash
# Clonar repositorio
git clone https://github.com/murdok1982/SistemaVigiaSocmint.git
cd SistemaVigiaSocmint

# Configurar variables de entorno
cp .env.example .env
# ⚠️ CAMBIAR TODAS LAS CLAVES EN .env
nano .env

# Generar claves seguras
openssl rand -hex 32  # Para JWT_SECRET_KEY
openssl rand -hex 16  # Para VIGIA_MASTER_KEY
openssl rand -hex 16  # Para HMAC_SECRET
```

### 3. Despliegue con Docker (Desarrollo/Staging)
```bash
# Levantar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Ejecutar migraciones (si es necesario)
docker-compose exec api python -c "from src.database import init_db; import asyncio; asyncio.run(init_db())"
```

### 4. Despliegue en Kubernetes (Producción)
```bash
# Crear namespace
kubectl apply -f k8s/namespace.yaml

# Crear secrets (⚠️ USAR VALORES REALES)
kubectl create secret generic vigia-secrets \
  --from-env-file=.env \
  -n vigia-system

# Desplegar todos los componentes
kubectl apply -f k8s/deployment.yaml

# Verificar despliegue
kubectl get pods -n vigia-system
kubectl get svc -n vigia-system
```

### 5. Configuración de APIs Sociales
```bash
# Twitter/X
export TWITTER_BEARER_TOKEN="your_bearer_token_here"

# Reddit
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"

# Telegram
export TELEGRAM_BOT_TOKEN="your_bot_token"

# Ejecutar con variables
docker-compose up -d
```

---

## 🧪 PRUEBAS

### Ejecutar Tests Locales
```bash
# Tests de seguridad
pytest tests/test_security.py -v

# Tests de ML
pytest tests/test_ml_analysis.py -v

# Tests completos
pytest tests/ -v --cov=src --cov-report=html
```

### Escaneo de Seguridad
```bash
# Bandit (Python SAST)
bandit -r src/ -f json -o bandit-report.json

# npm audit (Frontend)
cd frontend && npm audit

# Snyk (Dependencias)
snyk test --all-projects
```

---

## 📊 MAPA DE RUTAS API

| Método | Ruta | Descripción | Auth Requerida |
|--------|------|-------------|-----------------|
| POST | `/api/auth/login` | Autenticación JWT + MFA | No |
| POST | `/api/auth/refresh` | Refresh token | No |
| GET | `/api/health` | Estado del sistema | Sí |
| GET | `/api/alerts` | Lista de alertas (con filtros) | Sí |
| GET | `/api/alerts/{id}` | Detalle de alerta | Sí (Clearance) |
| POST | `/api/alerts/{id}/review` | Revisar alerta (analista) | Sí + MFA |
| POST | `/api/analyze` | Lanzar análisis OSINT | Sí (SECRET+) |
| GET | `/api/audit-log` | Log de auditoría | Sí (Supervisor) |
| POST | `/api/analysts` | Crear analista | Sí (Admin) |

---

## 🎖️ NIVELES DE HABILITACIÓN (CLEARANCE)

| Nivel | Descripción | Acceso |
|-------|-------------|--------|
| **CONFIDENTIAL** | Acceso básico | Alertas VERDE/AMARILLO, dashboard |
| **SECRET** | Acceso intermedio | Todas las alertas, análisis, auditoría |
| **TOP SECRET** | Acceso total | Configuración sistema, STIX export, SIEM |

---

## 📱 APP MÓVIL (Flutter)

```bash
# Instalar dependencias
cd mobile_app
flutter pub get

# Ejecutar en emulador/dispositivo
flutter run

# Build para Android
flutter build apk --release

# Build para iOS
flutter build ios --release
```

---

## 🔗 INTERCAMBIO DE INTELIGENCIA (STIX/TAXII)

```python
# Exportar alerta a STIX 2.1
from src.stix_taxii import alert_to_stix_bundle

stix_bundle = alert_to_stix_bundle(alert_data)
print(json.dumps(stix_bundle, indent=2))

# Enviar a Europol
from src.stix_taxii import share_with_external_system
share_with_external_system(alert_data, system="europol")
```

---

## ⚙️ CONFIGURACIÓN CI/CD

El pipeline de GitHub Actions (`.github/workflows/ci-cd.yml`) incluye:
1. **Security Scanning**: Bandit, npm audit, Snyk
2. **Backend Tests**: pytest con PostgreSQL
3. **Frontend Tests**: ESLint, build
4. **Mobile Tests**: Flutter analyze + test
5. **Docker Build**: Imágenes para API y Frontend
6. **Deploy**: Staging automático desde `develop`, producción desde `main`

---

## 📊 MÉTRICAS Y MONITOREO

- **SystemStats**: `/api/health` - alertas hoy, pendientes, por nivel
- **SIEM Integration**: Envío de eventos en tiempo real
- **Logs**: Auditoría inmutable con HMAC en PostgreSQL
- **Performance**: Rate limiting, health checks, auto-scaling K8s

---

## 🛡️ SEGURIDAD MILITAR

⚠️ **ADVERTENCIAS CRÍTICAS**:
1. Cambiar **TODAS** las claves en `.env` antes de producción
2. Usar **TLS/SSL** en todos los canales de comunicación
3. Configurar **firewalls** y NetworkPolicies en K8s
4. Realizar **pentesting** trimestral
5. Mantener **auditoría** de todos los accesos
6. Cumplir con **marco legal** (Ley 11/2002 CNI, RGPD)

---

## 📝 LICENCIA Y USO

- **Uso**: Exclusivo para organismos estatales y fuerzas de seguridad
- **Clasificación**: CONFIDENTIAL / SECRET (según despliegue)
- **Distribución**: Restringida - Requiere autorización judicial para compartir

---

## 🎯 HOJA DE RUTA (ROADMAP)

- [x] Fase 1: Fundaciones (PostgreSQL, Auth, Encryption)
- [x] Fase 2: Motor Analítico (ML/IA, APIs reales)
- [x] Fase 3: Frontend Militar (Dashboards, Mapas, Grafos)
- [x] Fase 4: Integración Institucional (STIX/TAXII, SIEM)
- [x] Fase 5: App Móvil (Flutter + Biometrics)
- [x] Fase 6: Testing Militar (Pentesting, CI/CD)
- [ ] Fase 7: Certificación Common Criteria EAL4+
- [ ] Fase 8: Despliegue en CLOUD GOV (AWS GovCloud / Azure Gov)

---

<div align="center">
  <h3>⚠️ SISTEMA CLASIFICADO — USO RESTRINGIDO ⚠️</h3>
  <p><em>"La inteligencia perfecta es aquella que protege libertades garantizando derechos funcionales."</em></p>
  <p><strong>VIGÍA v2.0 — Nivel ESTATAL-MILITAR</strong></p>
</div>
