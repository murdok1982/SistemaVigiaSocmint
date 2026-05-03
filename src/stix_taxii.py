"""
Módulo de intercambio de inteligencia STIX 2.x y TAXII 2.1.
Permite compartir amenazas con sistemas externos (Europol, Interpol, CISA).
"""
import os
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Estructuras STIX 2.1 (simplificadas)
# ─────────────────────────────────────────────────────────────────────────────

def create_stix_indicator(
    indicator_id: str,
    indicator_type: str,
    pattern: str,
    created: Optional[datetime] = None,
    confidence: float = 50,
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Crea un objeto STIX 2.1 Indicator.
    Ref: https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html
    """
    return {
        "type": "indicator",
        "id": f"indicator--{indicator_id}",
        "created": (created or datetime.now(timezone.utc)).isoformat(),
        "modified": (created or datetime.now(timezone.utc)).isoformat(),
        "name": f"VIGÍA Alert - {indicator_type}",
        "description": f"Threat indicator detected by VIGÍA system: {indicator_type}",
        "pattern": pattern,
        "pattern_type": "stix",
        "valid_from": (created or datetime.now(timezone.utc)).isoformat(),
        "confidence": int(confidence * 100),
        "labels": labels or ["osint", "socmint", "vigia"],
        "external_references": [
            {
                "source_name": "VIGÍA System",
                "external_id": indicator_id,
            }
        ],
    }


def create_stix_threat_actor(
    actor_id: str,
    name: str,
    sophistication: str = "intermediate",
    resource_level: str = "individual",
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Crea un objeto STIX 2.1 Threat Actor."""
    return {
        "type": "threat-actor",
        "id": f"threat-actor--{actor_id}",
        "created": datetime.now(timezone.utc).isoformat(),
        "modified": datetime.now(timezone.utc).isoformat(),
        "name": name,
        "description": f"Threat actor identified via OSINT/SOCMINT monitoring",
        "threat_actor_types": ["activist", "terrorist"],
        "sophistication": sophistication,
        "resource_level": resource_level,
        "labels": labels or ["vigia-detected"],
    }


def create_stix_observable(
    obs_id: str,
    observable_type: str,
    value: str,
) -> Dict[str, Any]:
    """Crea un objeto STIX 2.1 Observed Data (simplified)."""
    return {
        "type": "observed-data",
        "id": f"observed-data--{obs_id}",
        "created": datetime.now(timezone.utc).isoformat(),
        "modified": datetime.now(timezone.utc).isoformat(),
        "first_observed": datetime.now(timezone.utc).isoformat(),
        "last_observed": datetime.now(timezone.utc).isoformat(),
        "number_observed": 1,
        "objects": {
            "0": {
                "type": observable_type,
                "value": value,
            }
        },
    }


def alert_to_stix_bundle(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte una alerta de VIGÍA a un STIX 2.1 Bundle.
    Un Bundle puede contener múltiples objetos STIX relacionados.
    """
    bundle_id = str(uuid.uuid4())
    objects = []

    # 1. Indicator principal
    indicator = create_stix_indicator(
        indicator_id=alert.get("id", str(uuid.uuid4())),
        indicator_type=alert.get("risk_level", "UNKNOWN"),
        pattern=f"[content: '{alert.get('content_excerpt', '')}']",
        confidence=alert.get("risk_score", 0.5) * 100,
        labels=[alert.get("platform", "unknown"), alert.get("risk_level", "UNKNOWN")],
    )
    objects.append(indicator)

    # 2. Observables (si hay indicadores específicos)
    indicators = alert.get("indicators", [])
    for idx, ind in enumerate(indicators[:5]):  # Máximo 5
        obs = create_stix_observable(
            obs_id=str(uuid.uuid4()),
            observable_type="text",
            value=ind.get("value", ""),
        )
        objects.append(obs)

    # 3. Relationship (indicator -> observable)
    if objects:
        relationship = {
            "type": "relationship",
            "id": f"relationship--{str(uuid.uuid4())}",
            "created": datetime.now(timezone.utc).isoformat(),
            "modified": datetime.now(timezone.utc).isoformat(),
            "relationship_type": "indicates",
            "source_ref": objects[0]["id"],
            "target_ref": objects[1]["id"] if len(objects) > 1 else objects[0]["id"],
        }
        objects.append(relationship)

    return {
        "type": "bundle",
        "id": f"bundle--{bundle_id}",
        "objects": objects,
    }


# ─────────────────────────────────────────────────────────────────────────────
# TAXII 2.1 Server (simplificado)
# ─────────────────────────────────────────────────────────────────────────────

class TaxiiServer:
    """
    Servidor TAXII 2.1 simplificado para compartir inteligencia.
    En producción usar librerías como ctitaxii o implementación completa.
    """

    def __init__(self, api_root: str = "https://taxii.example.com/api/v2"):
        self.api_root = api_root
        self.collections: Dict[str, Dict[str, Any]] = {}

    def create_collection(self, title: str, description: str = "") -> str:
        """Crea una colección TAXII."""
        collection_id = str(uuid.uuid4())
        self.collections[collection_id] = {
            "id": collection_id,
            "title": title,
            "description": description,
            "can_read": True,
            "can_write": True,
            "media_types": ["application/vn.oasis.stix+json; version=2.1"],
        }
        return collection_id

    def add_object_to_collection(self, collection_id: str, stix_object: Dict[str, Any]):
        """Añade un objeto STIX a una colección."""
        if collection_id not in self.collections:
            raise ValueError(f"Colección {collection_id} no encontrada")
        # En producción: persistir en BD y hacer accesible via API
        logger.info("TAXII: Objeto STIX añadido a colección %s", collection_id)


# ─────────────────────────────────────────────────────────────────────────────
# Exportación para sistemas externos (Europol/Interpol)
# ─────────────────────────────────────────────────────────────────────────────

def export_to_europol_format(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    Formato simplificado para intercambio con Europol.
    Ref: Europol SIENA / Secure Information Exchange Network Application
    """
    return {
        "alert_id": alert.get("id"),
        "detection_date": alert.get("created_at"),
        "risk_level": alert.get("risk_level"),
        "platform": alert.get("platform"),
        "content_excerpt": alert.get("content_excerpt"),
        "indicators": [ind.get("value") for ind in alert.get("indicators", [])],
        "status": alert.get("status"),
        "reviewed_by": alert.get("reviewed_by"),
        "source_system": "VIGÍA",
        "classification": "CONFIDENTIAL",  # Por defecto
    }


async def share_with_external_system(
    alert: Dict[str, Any],
    system: str = "europol",
    api_endpoint: Optional[str] = None,
    api_key: Optional[str] = None,
) -> bool:
    """
    Comparte una alerta con un sistema externo vía HTTP POST.
    En producción: usar colas seguras y canales cifrados.
    """
    import httpx

    if system == "europol":
        payload = export_to_europol_format(alert)
        endpoint = api_endpoint or "https://api.europol.europa.eu/siena/v1/alerts"
    else:
        logger.warning("Sistema externo no soportado: %s", system)
        return False

    try:
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        headers["Content-Type"] = "application/json"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Alerta %s compartida con %s", alert.get("id"), system)
            return True
    except Exception as e:
        logger.error("Error compartiendo con %s: %s", system, e)
        return False
