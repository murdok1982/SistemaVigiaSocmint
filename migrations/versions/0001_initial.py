"""initial schema (alerts, audit_logs, analysts, threat_intel_feeds, system_metrics)

Revision ID: 0001
Revises:
Create Date: 2026-05-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("platform", sa.String(length=64), nullable=False),
        sa.Column("content_excerpt", sa.Text(), nullable=False),
        sa.Column("content_full_encrypted", sa.Text(), nullable=False),
        sa.Column("author_id_hash", sa.String(length=64), nullable=False, index=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=10), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False, index=True),
        sa.Column("indicators", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDIENTE", index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by", sa.String(length=64), nullable=True),
        sa.Column("analyst_notes_encrypted", sa.Text(), nullable=True),
        sa.Column("model_version", sa.String(length=20), nullable=False, server_default="1.0.0"),
        sa.Column("session_id", sa.String(length=36), nullable=True),
    )
    op.create_index("ix_alerts_author_id_hash", "alerts", ["author_id_hash"])
    op.create_index("ix_alerts_risk_level", "alerts", ["risk_level"])
    op.create_index("ix_alerts_status", "alerts", ["status"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("session_id", sa.String(length=36), nullable=True, index=True),
        sa.Column("agent", sa.String(length=64), nullable=False, index=True),
        sa.Column("action_type", sa.String(length=64), nullable=False, index=True),
        sa.Column("target_id", sa.String(length=128), nullable=True, index=True),
        sa.Column("alert_id", sa.String(length=36), nullable=True, index=True),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("analyst_id", sa.String(length=64), nullable=True),
        sa.Column("hmac_signature", sa.String(length=64), nullable=False),
    )
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])
    op.create_index("ix_audit_logs_agent", "audit_logs", ["agent"])
    op.create_index("ix_audit_logs_action_type", "audit_logs", ["action_type"])
    op.create_index("ix_audit_logs_target_id", "audit_logs", ["target_id"])
    op.create_index("ix_audit_logs_alert_id", "audit_logs", ["alert_id"])

    op.create_table(
        "analysts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("username", sa.String(length=64), nullable=False, unique=True, index=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="analyst"),
        sa.Column("clearance_level", sa.String(length=20), nullable=False, server_default="CONFIDENTIAL"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("mfa_secret", sa.String(length=255), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_analysts_username", "analysts", ["username"], unique=True)

    op.create_table(
        "threat_intel_feeds",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source", sa.String(length=64), nullable=False, index=True),
        sa.Column("feed_type", sa.String(length=64), nullable=False),
        sa.Column("indicator_value", sa.Text(), nullable=False, index=True),
        sa.Column("indicator_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_threat_intel_feeds_source", "threat_intel_feeds", ["source"])
    op.create_index("ix_threat_intel_feeds_indicator_value", "threat_intel_feeds", ["indicator_value"])
    op.create_index("ix_threat_intel_feeds_last_seen", "threat_intel_feeds", ["last_seen"])

    op.create_table(
        "system_metrics",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("metric_name", sa.String(length=64), nullable=False, index=True),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("tags", sa.Text(), nullable=True),
    )
    op.create_index("ix_system_metrics_timestamp", "system_metrics", ["timestamp"])
    op.create_index("ix_system_metrics_metric_name", "system_metrics", ["metric_name"])


def downgrade() -> None:
    op.drop_table("system_metrics")
    op.drop_table("threat_intel_feeds")
    op.drop_table("analysts")
    op.drop_table("audit_logs")
    op.drop_table("alerts")
