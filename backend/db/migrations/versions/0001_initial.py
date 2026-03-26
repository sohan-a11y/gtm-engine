"""Initial schema — all tables, indexes, triggers, and materialized views.

This migration creates the complete production schema from scratch.
Run with:  alembic upgrade head
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extensions ─────────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── organizations ──────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)

    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
        sa.Column("permissions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("org_id", "email", name="uq_users_org_email"),
    )
    op.create_index("ix_users_org_id", "users", ["org_id"])
    op.create_index("ix_users_org_role", "users", ["org_id", "role"])

    # ── companies ──────────────────────────────────────────────────────────────
    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("external_crm_id", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("health_score", sa.Float(), nullable=True),
        sa.Column("enrichment_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("icp_score", sa.Float(), nullable=True),
        sa.Column("icp_score_reason", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("org_id", "external_crm_id", name="uq_companies_org_external_crm_id"),
        sa.UniqueConstraint("org_id", "domain", name="uq_companies_org_domain"),
    )
    op.create_index("ix_companies_org_id", "companies", ["org_id"])
    op.create_index("ix_companies_org_health_score", "companies", ["org_id", "health_score"])

    # ── contacts ───────────────────────────────────────────────────────────────
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_crm_id", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("last_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="new"),
        sa.Column("enrichment_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("enrichment_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("icp_score", sa.Float(), nullable=True),
        sa.Column("icp_score_reason", sa.Text(), nullable=True),
        sa.Column("fit_signals", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("gap_signals", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("last_enriched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_scored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("org_id", "email", name="uq_contacts_org_email"),
        sa.UniqueConstraint("org_id", "external_crm_id", name="uq_contacts_org_external_crm_id"),
    )
    op.create_index("ix_contacts_org_id", "contacts", ["org_id"])
    op.create_index("ix_contacts_org_icp_score", "contacts", ["org_id", "icp_score"])
    op.create_index("ix_contacts_org_enrichment_status", "contacts", ["org_id", "enrichment_status"])

    # ── deals ──────────────────────────────────────────────────────────────────
    op.create_table(
        "deals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("primary_contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("external_crm_id", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("stage", sa.String(100), nullable=False, server_default="prospecting"),
        sa.Column("amount_cents", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("close_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("days_in_stage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("risk_level", sa.String(50), nullable=True),
        sa.Column("risk_factors", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("positive_signals", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("recommended_actions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("likely_close_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deal_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("org_id", "external_crm_id", name="uq_deals_org_external_crm_id"),
        sa.CheckConstraint("amount_cents >= 0", name="amount_cents_non_negative"),
    )
    op.create_index("ix_deals_org_id", "deals", ["org_id"])
    op.create_index("ix_deals_org_stage", "deals", ["org_id", "stage"])

    # ── campaigns ──────────────────────────────────────────────────────────────
    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("tone", sa.String(120), nullable=True),
        sa.Column("value_prop", sa.Text(), nullable=True),
        sa.Column("brand_voice", sa.Text(), nullable=True),
        sa.Column("target_roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column("icp_filters", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("slack_channel", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("org_id", "name", name="uq_campaigns_org_name"),
    )
    op.create_index("ix_campaigns_org_id", "campaigns", ["org_id"])
    op.create_index("ix_campaigns_org_status", "campaigns", ["org_id", "status"])

    # ── email_sequences ────────────────────────────────────────────────────────
    op.create_table(
        "email_sequences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("variation_rank", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("hook_type", sa.String(80), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending_approval"),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("org_id", "campaign_id", "contact_id", "variation_rank", name="uq_email_sequence_variation"),
    )
    op.create_index("ix_email_sequences_org_id", "email_sequences", ["org_id"])
    op.create_index("ix_email_sequences_org_status", "email_sequences", ["org_id", "status"])

    # ── content_library ────────────────────────────────────────────────────────
    op.create_table(
        "content_library",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("mode", sa.String(80), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("brand_voice", sa.Text(), nullable=True),
        sa.Column("quality_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_content_library_org_id", "content_library", ["org_id"])
    op.create_index("ix_content_library_org_mode", "content_library", ["org_id", "mode"])
    op.create_index("ix_content_library_org_status", "content_library", ["org_id", "status"])

    # ── agent_audit_log ────────────────────────────────────────────────────────
    # Append-only table — no UPDATE/DELETE triggers on purpose.
    op.create_table(
        "agent_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agent_name", sa.String(120), nullable=False),
        sa.Column("operation", sa.String(120), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=True),
        sa.Column("raw_response", sa.Text(), nullable=True),
        sa.Column("tokens_prompt", sa.Integer(), nullable=True),
        sa.Column("tokens_completion", sa.Integer(), nullable=True),
        sa.Column("cost_usd", sa.Float(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_agent_audit_log_org_id", "agent_audit_log", ["org_id"])
    op.create_index("ix_agent_audit_log_org_agent", "agent_audit_log", ["org_id", "agent_name"])
    op.create_index("ix_agent_audit_log_org_created_at", "agent_audit_log", ["org_id", "created_at"])

    # ── agent_configurations ───────────────────────────────────────────────────
    op.create_table(
        "agent_configurations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent_name", sa.String(120), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("provider", sa.String(120), nullable=True),
        sa.Column("model_name", sa.String(120), nullable=True),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("threshold", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("org_id", "agent_name", name="uq_agent_configurations_org_agent_name"),
    )
    op.create_index("ix_agent_configurations_org_id", "agent_configurations", ["org_id"])
    op.create_index("ix_agent_configurations_org_enabled", "agent_configurations", ["org_id", "enabled"])

    # ── integrations ───────────────────────────────────────────────────────────
    op.create_table(
        "integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(120), nullable=False),
        sa.Column("integration_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="disconnected"),
        sa.Column("credentials_encrypted", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("org_id", "provider", name="uq_integrations_org_provider"),
    )
    op.create_index("ix_integrations_org_id", "integrations", ["org_id"])
    op.create_index("ix_integrations_org_status", "integrations", ["org_id", "status"])

    # ── job_runs ───────────────────────────────────────────────────────────────
    op.create_table(
        "job_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", sa.String(120), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("input_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("result_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_job_runs_org_id", "job_runs", ["org_id"])
    op.create_index("ix_job_runs_org_status", "job_runs", ["org_id", "status"])
    op.create_index("ix_job_runs_org_job_type", "job_runs", ["org_id", "job_type"])

    # ── updated_at auto-update trigger ─────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    for table in [
        "organizations", "users", "companies", "contacts", "deals",
        "campaigns", "email_sequences", "content_library",
        "agent_configurations", "integrations", "job_runs",
    ]:
        op.execute(f"""
            CREATE TRIGGER trg_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at();
        """)

    # ── Materialized view: mv_pipeline_summary ─────────────────────────────────
    # Refreshed every 5 min via Celery beat (CONCURRENTLY requires unique index).
    op.execute("""
        CREATE MATERIALIZED VIEW mv_pipeline_summary AS
        SELECT
            org_id,
            stage,
            COUNT(*)                              AS deal_count,
            COALESCE(SUM(amount_cents), 0)        AS total_amount_cents,
            COALESCE(AVG(amount_cents), 0)        AS avg_amount_cents,
            COALESCE(AVG(days_in_stage), 0)       AS avg_days_in_stage,
            COALESCE(AVG(risk_score), 0)          AS avg_risk_score,
            COUNT(*) FILTER (WHERE risk_level = 'high' OR risk_level = 'critical')
                                                  AS high_risk_count
        FROM deals
        GROUP BY org_id, stage
        WITH NO DATA;
    """)
    op.execute("""
        CREATE UNIQUE INDEX uix_mv_pipeline_summary
        ON mv_pipeline_summary (org_id, stage);
    """)

    # ── Materialized view: mv_outbound_performance ─────────────────────────────
    op.execute("""
        CREATE MATERIALIZED VIEW mv_outbound_performance AS
        SELECT
            es.org_id,
            es.campaign_id,
            DATE_TRUNC('day', es.created_at)      AS day,
            COUNT(*)                              AS emails_generated,
            COUNT(*) FILTER (WHERE es.status = 'approved' OR es.status = 'sent')
                                                  AS emails_approved,
            COUNT(*) FILTER (WHERE es.status = 'sent')
                                                  AS emails_sent,
            COUNT(*) FILTER (WHERE es.status = 'rejected')
                                                  AS emails_rejected,
            COALESCE(AVG(es.confidence), 0)       AS avg_confidence
        FROM email_sequences es
        GROUP BY es.org_id, es.campaign_id, DATE_TRUNC('day', es.created_at)
        WITH NO DATA;
    """)
    op.execute("""
        CREATE UNIQUE INDEX uix_mv_outbound_performance
        ON mv_outbound_performance (org_id, campaign_id, day);
    """)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_outbound_performance")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_pipeline_summary")

    for table in [
        "organizations", "users", "companies", "contacts", "deals",
        "campaigns", "email_sequences", "content_library",
        "agent_configurations", "integrations", "job_runs",
    ]:
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")

    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    for tbl in [
        "job_runs", "integrations", "agent_configurations",
        "agent_audit_log", "content_library", "email_sequences",
        "campaigns", "deals", "contacts", "companies", "users", "organizations",
    ]:
        op.drop_table(tbl)
