"""
Generador de informes PDF para alertas y periodos.

- build_alert_pdf: PDF de una alerta individual con cabecera de clasificación,
  metadatos, excerpt, tabla de indicadores y pie con HMAC del documento.
- build_period_report_pdf: PDF agregado para informes diario/semanal.
- encrypt_pdf_with_pgp: cifrado opcional con GPG si se proporciona pubkey.

Las dependencias pesadas (reportlab, python-gnupg) se importan a nivel de
módulo: si no están instaladas se levanta ImportError al cargar y los
endpoints devuelven 500 controlado. La importación es ligera (no bloquea
el startup en condiciones normales).
"""
from __future__ import annotations

import io
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Any, Iterable

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.auth import generate_hmac

logger = logging.getLogger(__name__)


VALID_CLASSIFICATIONS = ("CONFIDENTIAL", "SECRET", "TOP_SECRET")


# ─────────────────────────────────────────────────────────────────────────────
# Estilos
# ─────────────────────────────────────────────────────────────────────────────
def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontSize=18, leading=22,
            spaceAfter=8, textColor=colors.HexColor("#0a1f44"),
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Heading2"], fontSize=12, leading=16,
            spaceAfter=6, textColor=colors.HexColor("#444444"),
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"], fontSize=10, leading=14, spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "small", parent=base["BodyText"], fontSize=8, leading=10,
            textColor=colors.HexColor("#555555"),
        ),
        "classification": ParagraphStyle(
            "classification", parent=base["Title"], fontSize=14, leading=18,
            alignment=1, spaceAfter=12, textColor=colors.white,
            backColor=colors.HexColor("#8b0000"),
        ),
    }


def _sanitize_classification(classification: str) -> str:
    classification = (classification or "CONFIDENTIAL").upper()
    if classification not in VALID_CLASSIFICATIONS:
        raise ValueError(f"Clasificación inválida: {classification}")
    return classification


def _classification_color(classification: str) -> colors.Color:
    return {
        "CONFIDENTIAL": colors.HexColor("#0d3b66"),
        "SECRET": colors.HexColor("#c1440e"),
        "TOP_SECRET": colors.HexColor("#7b0d1e"),
    }.get(classification, colors.HexColor("#0d3b66"))


def _classification_banner(classification: str) -> Table:
    banner_color = _classification_color(classification)
    label = f"// {classification.replace('_', ' ')} // VIGIA-OSINT //"
    table = Table([[label]], colWidths=[180 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), banner_color),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _kv_table(rows: Iterable[tuple[str, str]]) -> Table:
    data = [[k, v] for k, v in rows]
    table = Table(data, colWidths=[55 * mm, 125 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f3f8")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#0a1f44")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cdd5e0")),
    ]))
    return table


def _indicators_table(indicators: list[dict]) -> Table:
    header = ["Tipo", "Valor", "Confianza", "Explicación"]
    data: list[list[Any]] = [header]
    if not indicators:
        data.append(["—", "Sin indicadores", "—", "—"])
    else:
        for ind in indicators:
            ind_type = str(ind.get("type", "—"))
            value = str(ind.get("value", ""))[:80]
            confidence = ind.get("confidence", 0.0)
            try:
                conf_str = f"{float(confidence):.2f}"
            except (TypeError, ValueError):
                conf_str = "—"
            explanation = str(ind.get("explanation", ""))[:200]
            data.append([ind_type, value, conf_str, explanation])

    table = Table(data, colWidths=[35 * mm, 60 * mm, 20 * mm, 65 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a1f44")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cdd5e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
    ]))
    return table


def _hmac_footer_table(hmac_signature: str, generated_at: str, version: str = "VIGIA-2.1") -> Table:
    label = (
        f"Firma HMAC-SHA256 (integridad del documento): {hmac_signature}\n"
        f"Generado: {generated_at}  ·  {version}"
    )
    table = Table([[label]], colWidths=[180 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f3f8")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#444444")),
        ("FONTNAME", (0, 0), (-1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#cdd5e0")),
    ]))
    return table


# ─────────────────────────────────────────────────────────────────────────────
# Construcción de PDFs
# ─────────────────────────────────────────────────────────────────────────────
def _normalize_indicators(raw: Any) -> list[dict]:
    """Acepta indicators como list[dict] ya parseado o como JSON string (BD)."""
    if not raw:
        return []
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return []
    else:
        data = raw
    if not isinstance(data, list):
        return []
    return [d for d in data if isinstance(d, dict)]


def build_alert_pdf(alert: dict, classification: str = "CONFIDENTIAL") -> bytes:
    """
    Construye el PDF de una alerta individual.
    `alert` puede ser un AlertResponse.dict() o el row de BD serializado.
    Devuelve los bytes del PDF.
    """
    classification = _sanitize_classification(classification)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"VIGIA Alert {alert.get('id', '')}",
        author="VIGIA System",
    )
    styles = _styles()
    story: list[Any] = []

    story.append(_classification_banner(classification))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Informe de alerta OSINT/SOCMINT", styles["title"]))
    story.append(Paragraph("VIGÍA — Sistema de monitoreo pasivo de amenazas", styles["subtitle"]))
    story.append(Spacer(1, 4 * mm))

    created_at = alert.get("created_at") or alert.get("timestamp") or ""
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()

    metadata_rows = [
        ("ID", str(alert.get("id", "—"))),
        ("Plataforma", str(alert.get("platform", "—"))),
        ("Idioma", str(alert.get("language", "—"))),
        ("Fecha", str(created_at)),
        ("Risk score", f"{float(alert.get('risk_score', 0)):.4f}"),
        ("Risk level", str(alert.get("risk_level", "—"))),
        ("Estado", str(alert.get("status", "—"))),
        ("URL", str(alert.get("url", "—"))[:120]),
    ]
    story.append(_kv_table(metadata_rows))
    story.append(Spacer(1, 5 * mm))

    excerpt = str(
        alert.get("content_excerpt")
        or alert.get("content_full")
        or ""
    )[:1000]
    story.append(Paragraph("<b>Extracto del contenido</b>", styles["subtitle"]))
    safe_excerpt = (
        excerpt.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        or "<i>(sin contenido)</i>"
    )
    story.append(Paragraph(safe_excerpt, styles["body"]))
    story.append(Spacer(1, 5 * mm))

    indicators = _normalize_indicators(alert.get("indicators"))
    story.append(Paragraph(f"<b>Indicadores detectados ({len(indicators)})</b>", styles["subtitle"]))
    story.append(_indicators_table(indicators))
    story.append(Spacer(1, 8 * mm))

    # Pre-rellenar HMAC: necesitamos los bytes del documento ANTES del pie
    # Estrategia: render preliminar (sin pie), HMAC sobre esos bytes,
    # luego render final con pie incluido.
    pre_buf = io.BytesIO()
    pre_doc = SimpleDocTemplate(pre_buf, pagesize=A4)
    # Copia "ligera" del story (las flowables son reutilizables si no se han dibujado).
    # Para evitar reutilización, usamos solo metadatos clave para el HMAC.
    hmac_payload = json.dumps(
        {
            "id": alert.get("id"),
            "risk_score": alert.get("risk_score"),
            "risk_level": alert.get("risk_level"),
            "platform": alert.get("platform"),
            "indicators_count": len(indicators),
            "classification": classification,
            "excerpt_prefix": excerpt[:200],
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    document_hmac = generate_hmac(hmac_payload)
    generated_at = datetime.now(timezone.utc).isoformat()

    story.append(_hmac_footer_table(document_hmac, generated_at))
    story.append(Spacer(1, 2 * mm))
    story.append(_classification_banner(classification))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    pre_buf.close()
    logger.info(
        "REPORTS: alert PDF generado id=%s classification=%s bytes=%d",
        alert.get("id"), classification, len(pdf_bytes),
    )
    return pdf_bytes


def build_period_report_pdf(
    alerts: list[dict],
    date_from: str,
    date_to: str,
    classification: str = "CONFIDENTIAL",
) -> bytes:
    """
    Informe agregado por periodo (diario/semanal/mensual).
    `alerts` es la lista de filas de alerta (dict).
    """
    classification = _sanitize_classification(classification)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"VIGIA Period Report {date_from}_{date_to}",
        author="VIGIA System",
    )
    styles = _styles()
    story: list[Any] = []

    story.append(_classification_banner(classification))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Informe periódico VIGÍA", styles["title"]))
    story.append(Paragraph(
        f"Periodo: {date_from} a {date_to} · {len(alerts)} alertas",
        styles["subtitle"],
    ))
    story.append(Spacer(1, 4 * mm))

    # Resumen agregado
    by_level: dict[str, int] = {"VERDE": 0, "AMARILLO": 0, "NARANJA": 0, "ROJO": 0}
    by_platform: dict[str, int] = {}
    for a in alerts:
        lvl = str(a.get("risk_level", "VERDE"))
        by_level[lvl] = by_level.get(lvl, 0) + 1
        plat = str(a.get("platform", "—"))
        by_platform[plat] = by_platform.get(plat, 0) + 1

    story.append(Paragraph("<b>Distribución por nivel de riesgo</b>", styles["subtitle"]))
    level_rows = [(level, str(count)) for level, count in by_level.items()]
    story.append(_kv_table(level_rows))
    story.append(Spacer(1, 4 * mm))

    if by_platform:
        story.append(Paragraph("<b>Distribución por plataforma</b>", styles["subtitle"]))
        platform_rows = [(p, str(c)) for p, c in sorted(by_platform.items(), key=lambda x: -x[1])]
        story.append(_kv_table(platform_rows))
        story.append(Spacer(1, 6 * mm))

    # Tabla de alertas (truncada para evitar PDFs absurdamente grandes)
    max_alerts_in_table = 200
    rows: list[list[Any]] = [["ID", "Plataforma", "Nivel", "Score", "Excerpt"]]
    for a in alerts[:max_alerts_in_table]:
        rows.append([
            str(a.get("id", ""))[:36],
            str(a.get("platform", ""))[:20],
            str(a.get("risk_level", "")),
            f"{float(a.get('risk_score', 0)):.3f}",
            str(a.get("content_excerpt", ""))[:80],
        ])
    if len(alerts) > max_alerts_in_table:
        rows.append([f"... y {len(alerts) - max_alerts_in_table} más (consulte el endpoint /api/alerts)", "", "", "", ""])

    story.append(Paragraph("<b>Detalle de alertas</b>", styles["subtitle"]))
    table = Table(rows, colWidths=[40 * mm, 25 * mm, 22 * mm, 18 * mm, 75 * mm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0a1f44")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cdd5e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7f9fc")]),
    ]))
    story.append(table)
    story.append(Spacer(1, 8 * mm))

    hmac_payload = json.dumps(
        {
            "date_from": date_from,
            "date_to": date_to,
            "total": len(alerts),
            "by_level": by_level,
            "by_platform": by_platform,
            "classification": classification,
        },
        sort_keys=True,
        ensure_ascii=False,
    )
    document_hmac = generate_hmac(hmac_payload)
    generated_at = datetime.now(timezone.utc).isoformat()

    story.append(_hmac_footer_table(document_hmac, generated_at))
    story.append(Spacer(1, 2 * mm))
    story.append(_classification_banner(classification))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    logger.info(
        "REPORTS: period PDF generado from=%s to=%s alerts=%d bytes=%d",
        date_from, date_to, len(alerts), len(pdf_bytes),
    )
    return pdf_bytes


# ─────────────────────────────────────────────────────────────────────────────
# Cifrado GPG opcional
# ─────────────────────────────────────────────────────────────────────────────
def encrypt_pdf_with_pgp(pdf_bytes: bytes, recipient_pubkey: str) -> bytes:
    """
    Cifra los bytes del PDF con la clave pública PGP del destinatario.
    Devuelve los bytes cifrados (ASCII-armored binario válido).
    Si el cifrado falla, levanta RuntimeError.
    """
    try:
        import gnupg
    except ImportError as exc:
        raise RuntimeError("python-gnupg no está instalado") from exc

    if not recipient_pubkey or "BEGIN PGP PUBLIC KEY" not in recipient_pubkey:
        raise ValueError("recipient_pgp_pubkey no es una clave pública PGP válida")

    with tempfile.TemporaryDirectory(prefix="vigia_gpg_") as gnupghome:
        try:
            gpg = gnupg.GPG(gnupghome=gnupghome)
        except Exception as exc:
            raise RuntimeError(
                "GPG binario no disponible en el sistema. Instale gnupg."
            ) from exc

        import_result = gpg.import_keys(recipient_pubkey)
        if not import_result.fingerprints:
            raise ValueError("No se pudo importar la clave pública PGP")
        fingerprint = import_result.fingerprints[0]

        # Confiamos en la clave recién importada para esta sesión efímera
        try:
            gpg.trust_keys([fingerprint], "TRUST_ULTIMATE")
        except Exception:
            pass

        encrypted = gpg.encrypt(
            pdf_bytes,
            recipients=[fingerprint],
            always_trust=True,
            armor=False,
        )
        if not encrypted.ok:
            raise RuntimeError(f"Error cifrando PDF con PGP: {encrypted.status}")

        out_bytes = bytes(encrypted.data)
        logger.info(
            "REPORTS: PDF cifrado con PGP recipient=%s in=%d out=%d",
            fingerprint[-16:], len(pdf_bytes), len(out_bytes),
        )
        return out_bytes
