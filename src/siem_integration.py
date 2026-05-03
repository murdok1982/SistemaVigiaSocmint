"""
Integración con SIEM (Security Information and Event Management).
Soporte para Splunk, ELK Stack (Elasticsearch, Logstash, Kibana), QRadar, ArcSight.
Envío de logs y alertas en tiempo real.
"""
import os
import json
import logging
import socket
import ssl
from datetime import datetime, timezone
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configuración SIEM (desde variables de entorno)
# ─────────────────────────────────────────────────────────────────────────────
SIEM_TYPE = os.environ.get("SIEM_TYPE", "splunk")  # splunk, elk, qradar, arcsight
SIEM_HOST = os.environ.get("SIEM_HOST", "localhost")
SIEM_PORT = int(os.environ.get("SIEM_PORT", "9997"))
SIEM_API_ENDPOINT = os.environ.get("SIEM_API_ENDPOINT", "https://localhost:8088/services/collector")
SIEM_API_TOKEN = os.environ.get("SIEM_API_TOKEN", "")
SIEM_USE_TLS = os.environ.get("SIEM_USE_TLS", "false").lower() == "true"


# ─────────────────────────────────────────────────────────────────────────────
# Formateo de logs para SIEM
# ─────────────────────────────────────────────────────────────────────────────
def format_splunk_event(
    event_data: Dict[str, Any],
    sourcetype: str = "vigia:alert",
) -> str:
    """Formatea un evento para Splunk HEC (HTTP Event Collector)."""
    return json.dumps({
        "time": datetime.now(timezone.utc).timestamp(),
        "sourcetype": sourcetype,
        "source": "vigia_system",
        "event": event_data,
    })


def format_elk_event(
    event_data: Dict[str, Any],
    index: str = "vigia-logs",
) -> str:
    """Formatea un evento para ELK Stack (Bulk API)."""
    action = {"index": {"_index": index}}
    return json.dumps(action) + "\n" + json.dumps(event_data) + "\n"


def format_cef_event(
    event_data: Dict[str, Any],
    device_vendor: str = "VIGIA",
    device_product: str = "VIGIA_OSINT",
    device_version: str = "2.0",
) -> str:
    """
    Formatea un evento en Common Event Format (CEF) para QRadar/ArcSight.
    CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
    """
    severity_map = {"ROJO": "10", "NARANJA": "7", "AMARILLO": "4", "VERDE": "1"}
    severity = severity_map.get(event_data.get("risk_level", "VERDE"), "1")

    extension = f"alertId={event_data.get('id', '')} "
    extension += f"platform={event_data.get('platform', '')} "
    extension += f"riskScore={event_data.get('risk_score', 0)} "

    cef = (
        f"CEF:0|{device_vendor}|{device_product}|{device_version}|"
        f"VIGIA_ALERT|OSINT Threat Detected|{severity}|{extension}"
    )
    return cef


# ─────────────────────────────────────────────────────────────────────────────
# Envío de eventos a SIEM
# ─────────────────────────────────────────────────────────────────────────────
async def send_to_splunk_hec(event_data: Dict[str, Any]) -> bool:
    """Envía evento a Splunk HEC."""
    import httpx

    if not SIEM_API_TOKEN:
        logger.warning("SIEM: Splunk HEC token no configurado")
        return False

    payload = format_splunk_event(event_data)
    headers = {
        "Authorization": f"Splunk {SIEM_API_TOKEN}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, verify=not SIEM_USE_TLS) as client:
            response = await client.post(SIEM_API_ENDPOINT, data=payload, headers=headers)
            response.raise_for_status()
            logger.info("SIEM: Evento enviado a Splunk HEC")
            return True
    except Exception as e:
        logger.error("SIEM: Error enviando a Splunk: %s", e)
        return False


async def send_to_elk(event_data: Dict[str, Any]) -> bool:
    """Envía evento a ELK Stack via Bulk API."""
    import httpx

    payload = format_elk_event(event_data)
    headers = {"Content-Type": "application/json"}

    if SIEM_API_TOKEN:
        headers["Authorization"] = f"Bearer {SIEM_API_TOKEN}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{SIEM_API_ENDPOINT}/_bulk",
                data=payload,
                headers=headers,
            )
            response.raise_for_status()
            logger.info("SIEM: Evento enviado a ELK")
            return True
    except Exception as e:
        logger.error("SIEM: Error enviando a ELK: %s", e)
        return False


async def send_to_syslog_cef(event_data: Dict[str, Any]) -> bool:
    """
    Envía evento vía Syslog (CEF format).
    Usa UDP o TCP con opcional TLS.
    """
    cef_message = format_cef_event(event_data)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM if SIEM_USE_TLS else socket.SOCK_DGRAM)

        if SIEM_USE_TLS:
            context = ssl.create_default_context()
            secure_sock = context.wrap_socket(sock, server_hostname=SIEM_HOST)
            secure_sock.connect((SIEM_HOST, SIEM_PORT))
            secure_sock.sendall(cef_message.encode())
            secure_sock.close()
        else:
            sock.connect((SIEM_HOST, SIEM_PORT))
            sock.sendall(cef_message.encode())
            sock.close()

        logger.info("SIEM: Evento CEF enviado via Syslog a %s:%s", SIEM_HOST, SIEM_PORT)
        return True
    except Exception as e:
        logger.error("SIEM: Error enviando via Syslog: %s", e)
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Función principal de integración
# ─────────────────────────────────────────────────────────────────────────────
async def forward_to_siem(
    event_type: str,
    event_data: Dict[str, Any],
) -> bool:
    """
    Reenvía un evento del sistema VIGÍA al SIEM configurado.
    """
    enriched_data = {
        **event_data,
        "event_type": event_type,
        "source_system": "VIGIA",
        "classification": "CONFIDENTIAL",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if SIEM_TYPE == "splunk":
        return await send_to_splunk_hec(enriched_data)
    elif SIEM_TYPE == "elk":
        return await send_to_elk(enriched_data)
    elif SIEM_TYPE in ("qradar", "arcsight"):
        return await send_to_syslog_cef(enriched_data)
    else:
        logger.warning("SIEM: Tipo no soportado: %s", SIEM_TYPE)
        return False
