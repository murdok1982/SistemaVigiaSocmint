"""
ORQUESTADOR PRINCIPAL — Sistema VIGÍA de Monitoreo OSINT/SOCMINT

Coordina el pipeline de análisis:
  STRATEGY → RESEARCH → ANALYSIS → COMPLIANCE → EXECUTION

Cada acción genera un registro de auditoría. La revisión humana
es OBLIGATORIA para alertas AMARILLO, NARANJA y ROJO.
"""
import logging
import uuid
from datetime import datetime, timezone

from src.agents.analysis_agent import analyze_post
from src.agents.compliance_agent import check_compliance
from src.agents.execution_agent import prepare_execution
from src.agents.research_agent import collect_public_content
from src.agents.strategy_agent import build_strategy
from src.models import OrchestratorAction, OrchestratorResponse, SocialPost, ThreatAssessment

logger = logging.getLogger(__name__)


class VigiaOrchestrator:
    """
    Orquestador del sistema VIGÍA.

    Gestiona el pipeline de análisis completo desde la estrategia
    hasta la generación de alertas para revisión humana.
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
    ) -> OrchestratorResponse:
        """
        Ejecuta el pipeline completo de análisis OSINT/SOCMINT.

        Args:
            objective: Objetivo de análisis para esta ejecución.
            platforms: Plataformas a monitorear. None = todas.
            max_results: Máximo de resultados por plataforma.

        Returns:
            OrchestratorResponse con el resultado completo del pipeline.
        """
        logger.info("ORQUESTADOR: iniciando pipeline — objetivo: %s", objective)
        self._log_audit("ORCHESTRATOR", "pipeline_start", f"objetivo='{objective}' plataformas={platforms}")

        actions: list[OrchestratorAction] = []
        step = 0

        # ── PASO 1: STRATEGY_AGENT ─────────────────────────────────────────────
        step += 1
        actions.append(OrchestratorAction(
            step=step,
            agent="STRATEGY_AGENT",
            task="Generar plan de monitoreo con indicadores y estrategia por plataforma",
            status="pending",
        ))

        strategy = build_strategy(objective)
        selected_platforms = platforms or list(strategy["channel_strategy"].keys())
        keywords = [kw for kws in strategy["threat_indicators"].values() for kw in kws[:3]]

        actions[-1].status = "completed"
        self._log_audit("STRATEGY_AGENT", "strategy_built", f"plataformas={selected_platforms}")

        # ── PASO 2: RESEARCH_AGENT ─────────────────────────────────────────────
        step += 1
        actions.append(OrchestratorAction(
            step=step,
            agent="RESEARCH_AGENT",
            task="Recopilar contenido público de plataformas seleccionadas",
            status="pending",
        ))

        posts: list[SocialPost] = await collect_public_content(
            platforms=selected_platforms,
            keywords=keywords,
            max_results=max_results,
        )

        actions[-1].status = "completed"
        self._log_audit("RESEARCH_AGENT", "content_collected", f"posts={len(posts)}")

        # ── PASOS 3-5: ANALYSIS + COMPLIANCE + EXECUTION (por post) ───────────
        self._results = []
        results = self._results
        for post in posts:
            # ANALYSIS_AGENT
            assessment: ThreatAssessment = analyze_post(post)

            # COMPLIANCE_AGENT
            proposed_action = _propose_action(assessment)
            compliance = check_compliance(post, assessment, proposed_action)

            # EXECUTION_AGENT
            execution = prepare_execution(post, assessment, compliance)

            excerpt = post.content[:120] + ("..." if len(post.content) > 120 else "")
            results.append({
                "post_id": post.id,
                "platform": post.platform,
                "risk_score": assessment.risk_score,
                "alert_level": assessment.alert_level,
                "action": execution["action"],
                "requires_human_approval": execution["requires_human_approval"],
                # Datos completos para persistencia en API
                "_alert_data": {
                    "id": assessment.id,
                    "platform": post.platform.capitalize(),
                    "content_excerpt": excerpt,
                    "content_full": post.content,
                    "indicators": [ind.model_dump() for ind in assessment.indicators_found],
                    "risk_score": assessment.risk_score,
                    "risk_level": assessment.alert_level,
                    "alert_status": execution["alert_status"],
                    "action": execution["action"],
                },
            })

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
            agent="ANALYSIS_AGENT + COMPLIANCE_AGENT + EXECUTION_AGENT",
            task=f"Analizar {len(posts)} posts, verificar compliance y preparar ejecución",
            status="completed",
        ))

        # ── RESUMEN ────────────────────────────────────────────────────────────
        pending_review = sum(1 for r in results if r["requires_human_approval"])
        critical = sum(1 for r in results if r["alert_level"] == "ROJO")
        high = sum(1 for r in results if r["alert_level"] == "NARANJA")

        final_recommendation = (
            f"Pipeline completado: {len(posts)} posts analizados. "
            f"{pending_review} requieren revisión humana "
            f"({critical} ROJO, {high} NARANJA). "
            f"Revisar cola de alertas en el dashboard."
        )

        self._log_audit(
            "ORCHESTRATOR",
            "pipeline_complete",
            f"posts={len(posts)} pendientes={pending_review} críticos={critical}",
        )

        return OrchestratorResponse(
            objective=objective,
            selected_agents=["STRATEGY_AGENT", "RESEARCH_AGENT", "ANALYSIS_AGENT",
                             "COMPLIANCE_AGENT", "EXECUTION_AGENT"],
            reasoning_summary=(
                f"Se analizaron {len(posts)} publicaciones públicas en {len(selected_platforms)} "
                f"plataformas. Se detectaron {pending_review} alertas que requieren revisión "
                f"humana. Ninguna acción fue tomada de forma autónoma."
            ),
            actions=actions,
            final_recommendation=final_recommendation,
            requires_human_approval=pending_review > 0,
            audit_note=f"sesion={self.session_id} entradas_audit={len(self._audit_log)}",
        )

    @property
    def audit_log(self) -> list[dict]:
        """Devuelve el log de auditoría completo de la sesión."""
        return list(self._audit_log)


def _propose_action(assessment: ThreatAssessment) -> str:
    """Propone una acción inicial basada en el nivel de alerta."""
    action_map = {
        "VERDE": "archive_auto",
        "AMARILLO": "queue_for_approval",
        "NARANJA": "queue_for_approval",
        "ROJO": "escalate",
    }
    return action_map.get(assessment.alert_level, "queue_for_approval")
