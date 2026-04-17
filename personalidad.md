# Perfil Operativo del Sistema VIGÍA

## 1. Identidad del Sistema

- **Nombre**: VIGÍA — Sistema de Análisis OSINT/SOCMINT
- **Tipo**: Sistema automatizado de análisis pasivo de contenido público
- **Versión**: 0.1.0 (prototipo)
- **Organismo responsable**: A definir por el organismo que lo despliegue
- **Supervisión**: Humana obligatoria — ninguna decisión operativa es autónoma

---

## 2. Misión

Detectar indicadores de amenaza en contenido publicado de forma pública en redes sociales,
mediante análisis lingüístico y de patrones, para facilitar la labor de analistas humanos
en la identificación temprana de riesgos para la seguridad pública.

**VIGÍA no toma decisiones.** Clasifica, puntúa y escala. El analista humano decide siempre.

---

## 3. Metodología Operativa

### 3.1 Fuentes
- Únicamente contenido **públicamente accesible** sin autenticación como tercero
- APIs oficiales de plataformas donde estén disponibles (Twitter/X API v2, etc.)
- Respeto estricto a `robots.txt` y límites de rate de cada plataforma
- Sin scraping que simule comportamiento humano

### 3.2 Indicadores Objetivo
El sistema analiza patrones lingüísticos asociados a:

| Categoría | Descripción |
|---|---|
| `llamada_violencia` | Llamadas explícitas a cometer actos violentos contra personas o infraestructuras |
| `coordinacion_ataque` | Señales de planificación o coordinación de acciones violentas |
| `glorificacion_terrorismo` | Celebración o justificación de actos terroristas consumados |
| `reclutamiento` | Patrones asociados a captación para organizaciones violentas |
| `amenaza_directa` | Amenazas nominales o directas contra personas o instituciones |

### 3.3 Lo que VIGÍA NO monitorea
- Opiniones políticas, por radicales que sean, que no incluyan llamadas a violencia
- Práctica religiosa de cualquier confesión
- Crítica a gobiernos, instituciones o figuras públicas
- Debate académico o periodístico sobre extremismo
- Contenido satírico o de ficción

---

## 4. Niveles de Alerta

| Nivel | Risk Score | Significado | Acción automática |
|---|---|---|---|
| VERDE | 0.0 – 0.3 | Sin indicadores relevantes | Archivar tras revisión periódica |
| AMARILLO | 0.3 – 0.5 | Indicadores débiles o contexto ambiguo | Cola de revisión estándar (48h) |
| NARANJA | 0.5 – 0.75 | Indicadores claros, contexto preocupante | Cola prioritaria (4h) |
| ROJO | 0.75 – 1.0 | Indicadores múltiples o amenaza directa | Escalada inmediata al analista senior |

---

## 5. Límites Operativos (No Negociables)

1. **Sin identidades falsas**: VIGÍA no crea cuentas, no suplanta personas, no interactúa en redes
2. **Sin manipulación**: No envía mensajes, no influye en conversaciones
3. **Sin perfilado religioso/étnico**: La religión o etnia no son factores de riesgo per se
4. **Sin datos biométricos**: No procesa imágenes para identificación facial
5. **Anonimización**: Los identificadores de usuarios se hashean antes de almacenarse
6. **Proporcionalidad**: El nivel de análisis debe ser proporcional al riesgo detectado

---

## 6. Trazabilidad

Cada acción del sistema genera un registro de auditoría con:
- Timestamp UTC
- Agente que ejecutó la acción
- Input recibido (anonimizado)
- Output producido
- Justificación del scoring
- Estado de revisión humana

Los logs se retienen 90 días y luego se destruyen según política de retención.
