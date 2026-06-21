"""Baseline schema: entity spine + tenancy + stub tables, with Postgres RLS.

The baseline creates all tables from the platform model metadata (the single
source of truth) rather than hand-maintaining create_table blocks. Subsequent
migrations should use proper autogenerate diffs.

On PostgreSQL it additionally enables row-level security on tenant-scoped tables
with org-scoped policies keyed on the ``app.current_org`` session setting. This
is defense-in-depth behind the application-layer org scoping; in production the
app should connect as a non-owner role and ``SET app.current_org`` per request.
"""

from __future__ import annotations

from alembic import op

from geoready_platform.db.base import Base

# Import models so metadata is populated.
from geoready_platform.db import models  # noqa: F401

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None

_TENANT_TABLES = (
    "business_entity",
    "entity_signal",
    "audit_jobs",
    "org_members",
    "api_keys",
    "perception",
    "intervention",
    "impact",
)


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)

    if bind.dialect.name == "postgresql":
        for table in _TENANT_TABLES:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            op.execute(
                f"""
                CREATE POLICY {table}_org_isolation ON {table}
                USING (org_id = current_setting('app.current_org', true))
                """
            )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for table in _TENANT_TABLES:
            op.execute(f"DROP POLICY IF EXISTS {table}_org_isolation ON {table}")
            op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
    Base.metadata.drop_all(bind=bind)
