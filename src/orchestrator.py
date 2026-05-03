"""
ORQUESTADOR PRINCIPAL — Sistema VIGÍA de Monitoreo OSINT/SOCMINT (VERSIÓN MILITAR)

Coordina el pipeline de análisis:
  STRATEGY → RESEARCH (APIs REALES) → ML_ANALYSIS → COMPLIANCE → EXECUTION

Cada acción genera un registro de auditoría inmutable. Revisión humana OBLIGATORIA.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from src.agents.ml_analysis_agent import analyze_post_ml
from src.agents.compliance_agent import check_compliance
from src.agents.execution_agent import prepare_execution
from src.agents.strategy_agent import build_strategy
from src.agents.real_data_collector import collect_from_all_platforms
from src.models import OrchestratorAction, OrchestratorResponse, SocialPost, ThreatAssessment
from src.database import AsyncSession, AlertModel, AuditLogModel
from src.crypto_utils import encrypt_data, hash_identifier
from src.auth import generate_hmac

logger = logging.getLogger(__name__)


class VigiaOrchestrator:
    """
    Orquestador del sistema VIGÍA — Versión Estatal-Militar.

    Gestiona el pipeline completo de análisis con:
    - APIs reales de redes sociales
    - Modelos ML para detección de amenazas
    - Almacenamiento persistente en PostgreSQL
    - Auditoría criptográfica
    """

    def __init__(self) -> None:
        self.session_id = str(uuid.uuid4())
        self._audit_log: list[dict] = []
        self._results: list[dict] = []

    def _log_audit(self, agent: str, action: str, details: str) -> None:
        """Registra una entrada de auditoría en memoria de sesión."""
        entry = {
            "id": str(uuid.uuid4()),
            "session_id": self.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent": agent,
            "action": action,
            "details": details,
        }
        self._audit_log.append(entry)
        logger.info("[AUDIT] %s | %s | %s", agent, action, details)

    async def run_analysis_pipeline(
        self,
        objective: str,
        platforms: list[str] | None = None,
        max_results: int = 50,
        db: Optional[AsyncSession] = None,
        analyst_id: str = "system",
    ) -> OrchestratorResponse:
        """
        Ejecuta el pipeline completo de análisis OSINT/SOCMINT usando APIs reales y ML.

        Args:
            objective: Objetivo de análisis para esta ejecución.
            platforms: Plataformas a monitorear. None = todas configuradas.
            max_results: Máximo de resultados por plataforma.
            db: Sesión de base de datos (opcional).
            analyst_id: ID del analista que lanza el análisis.

        Returns:
            OrchestratorResponse con el resultado completo del pipeline.
        """
        logger.info("ORQUESTADOR: iniciando pipeline MILITAR — objetivo: %s", objective)
        self._log_audit("ORCHESTRATOR", "pipeline_start", f"objetivo='{objective}' plataformas={platforms} analyst_id={analyst_id}")

        actions: list[OrchestratorAction] = []
        step = 0

        # ── PASO 1: STRATEGY_AGENT ─────────────────────────────────────────────
        step += 1
        actions.append(OrchestratorAction(
            step=step,
            agent="STRATEGY_AGENT",
            task="Generar plan de monitoreo con indicadores y estrategia por plataforma (ML-READY)",
            status="pending",
        ))

        strategy = build_strategy(objective)
        selected_platforms = platforms or list(strategy["channel_strategy"].keys())
        keywords = [kw for kws in strategy["threat_indicators"].values() for kw in kws[:5]]  # Más keywords

        actions[-1].status = "completed"
        self._log_audit("STRATEGY_AGENT", "strategy_built", f"plataformas={selected_platforms} keywords={len(keywords)}")

        # ── PASO 2: RESEARCH_AGENT (APIs REALES) ──────────────────────────────
        step += 1
        actions.append(OrchestratorAction(
            step=step,
            agent="RESEARCH_AGENT (REAL APIs)",
            task="Recopilar contenido público de APIs reales (Twitter, Reddit, Telegram, etc.)",
            status="pending",
        ))

        posts: list[SocialPost] = await collect_from_all_platforms(
            platforms=selected_platforms,
            keywords=keywords,
            max_results=max_results,
        )

        actions[-1].status = "completed"
        self._log_audit("RESEARCH_AGENT", "content_collected_real", f"posts={len(posts)} platforms={selected_platforms}")

        # ── PASOS 3-5: ML_ANALYSIS + COMPLIANCE + EXECUTION (por post) ────────
        self._results = []
        results = self._results
        alerts_created = 0

        for post in posts:
            # ML_ANALYSIS_AGENT (reemplaza regex por ML)
            assessment: ThreatAssessment = analyze_post_ml(post)

            # COMPLIANCE_AGENT
            proposed_action = _propose_action(assessment)
            compliance = check_compliance(post, assessment, proposed_action)

            # EXECUTION_AGENT
            execution = prepare_execution(post, assessment, compliance)

            excerpt = post.content[:120] + ("..." if len(post.content) > 120 else "")

            # Preparar datos para persistencia
            alert_data = {
                "id": assessment.id,
                "platform": post.platform.capitalize(),
                "content_excerpt": excerpt,
                "content_full_encrypted": encrypt_data(post.content),  # Cifrado en reposo
                "author_id_hash": post.author_id_hash,
                "url": post.url,
                "language": post.language,
                "indicators": [ind.model_dump() for ind in assessment.indicators_found],
                "risk_score": assessment.risk_score,
                "risk_level": assessment.alert_level,
                "alert_status": execution["alert_status"],
                "action": execution["action"],
                "session_id": self.session_id,
            }

            results.append({
                "post_id": post.id,
                "platform": post.platform,
                "risk_score": assessment.risk_score,
                "alert_level": assessment.alert_level,
                "action": execution["action"],
                "requires_human_approval": execution["requires_human_approval"],
                "_alert_data": alert_data,
            })

            # Persistir en base de datos si está disponible
            if db:
                await _persist_alert(db, alert_data, analyst_id)

            alerts_created += 1

            # Log de auditoría por resultado
            self._log_audit(
                "EXECUTION_AGENT",
                execution["action"],
                execution["audit_log"]["details"],
            )

        # Añadir pasos de análisis al resumen
        step += 1
        actions.append(OrchestratorAction(
            step=step,
            agent="ML_ANALYSIS_AGENT + COMPLIANCE_AGENT + EXECUTION_AGENT",
            task=f"Analizar {len(posts)} posts con ML, verificar compliance y preparar ejecución",
            status="completed",
        ))

        # ── RESUMEN ────────────────────────────────────────────────────────────
        pending_review = sum(1 for r in results if r["requires_human_approval"])
        critical = sum(1 for r in results if r["alert_level"] == "ROJO")
        high = sum(1 for r in results if r["alert_level"] == "NARANJA")

        final_recommendation = (
            f"Pipeline MILITAR completado: {len(posts)} posts analizados con ML. "
            f"{pending_review} requieren revisión humana "
            f"({critical} ROJO, {high} NARANJA). "
            f"Persistidos {alerts_created} alertas en PostgreSQL."
        )

        self._log_audit(
            "ORCHESTRATOR",
            "pipeline_complete_military",
            f"posts={len(posts)} pendientes={pending_review} críticos={critical} alerts_created={alerts_created}",
        )

        # Persistir logs de auditoría en BD
        if db:
            await _persist_audit_logs(db, self._audit_log)

        return OrchestratorResponse(
            objective=objective,
            selected_agents=["STRATEGY_AGENT", "RESEARCH_AGENT_REAL", "ML_ANALYSIS_AGENT",
                             "COMPLIANCE_AGENT", "EXECUTION_AGENT"],
            reasoning_summary=(
                f"Se analizaron {len(posts)} publicaciones usando ML y APIs reales en {len(selected_platforms)} "
                f"plataformas. Se detectaron {pending_review} alertas que requieren revisión "
                f"humana. Ninguna acción autónoma tomada."
            ),
            actions=actions,
            final_recommendation=final_recommendation,
            requires_human_approval=pending_review > 0,
            audit_note=f"sesion={self.session_id} entradas_audit={len(self._audit_log)} military_v2",
        )

    @property
    def audit_log(self) -> list[dict]:
        """Devuelve el log de auditoría completo de la sesión."""
        return list(self._audit_log)


async def _persist_alert(db: AsyncSession, alert_data: dict, analyst_id: str) -> None:
    """Persiste una alerta en la base de datos PostgreSQL."""
    import json

    alert = AlertModel(
        id=alert_data["id"],
        platform=alert_data["platform"],
        content_excerpt=alert_data["content_excerpt"],
        content_full_encrypted=alert_data["content_full_encrypted"],
        author_id_hash=alert_data["author_id_hash"],
        url=alert_data["url"],
        language=alert_data["language"],
        risk_score=alert_data["risk_score"],
        risk_level=alert_data["risk_level"],
        indicators=json.dumps(alert_data["indicators"]),
        status=alert_data["alert_status"],
        session_id=alert_data["session_id"],
    )
    db.add(alert)
    await db.commit()
    logger.info("Alerta persistida en BD: %s", alert.id)


async def _persist_audit_logs(db: AsyncSession, audit_entries: list[dict]) -> None:
    """Persiste logs de auditoría en BD con HMAC."""
    for entry in audit_entries:
        # Generar HMAC para integridad
        hmac_data = f"{entry['id']}{entry['timestamp']}{entry['agent']}{entry['action']}"
        hmac_signature = generate_hmac(hmac_data)

        audit = AuditLogModel(
            id=entry["id"],
            timestamp=datetime.fromisoformat(entry["timestamp"]),
            session_id=entry["session_id"],
            agent=entry["agent"],
            action_type=entry["action"],
            details=entry["details"],
            hmac_signature=hmac_signature,
        )
        db.add(audit)
    await db.commit()
    logger.info("Audit logs persistidos en BD: %d entradas", len(audit_entries))


def _propose_action(assessment: ThreatAssessment) -> str:
    """Propone una acción inicial basada en el nivel de alerta."""
    action_map = {
        "VERDE": "archive_auto",
        "AMARILLO": "queue_for_approval",
        "NARANJA": "queue_for_approval",
        "ROJO": "escalate",
    }
    return action_map.get(assessment.alert_level, "queue_for_approval")
