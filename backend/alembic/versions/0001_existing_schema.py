"""Register the existing schema; never create or drop business tables.

For an existing unversioned database, upgrade validates the legacy layout
before recording the baseline. Empty databases must be provisioned separately.
"""

from alembic import context, op
import sqlalchemy as sa

revision = "0001_existing_schema"
down_revision = None
branch_labels = None
depends_on = None

EXPECTED_COLUMNS = {
    "users": {"id", "name", "email", "password_hash", "created_at"},
    "reports": {"id", "user_id", "report_name", "report_date", "upload_date", "file_url", "raw_text"},
    "biomarkers": {"id", "report_id", "name", "value", "unit", "ref_low", "ref_high", "status"},
    "chat_history": {"id", "user_id", "report_id", "question", "answer", "timestamp"},
}


def upgrade():
    if context.is_offline_mode():
        return
    inspector = sa.inspect(op.get_bind())
    for table, expected in EXPECTED_COLUMNS.items():
        if not inspector.has_table(table):
            raise RuntimeError(f"Missing legacy table {table}; baseline does not provision tables")
        actual = {column["name"] for column in inspector.get_columns(table)}
        if actual != expected:
            raise RuntimeError(f"Legacy schema mismatch in {table}; inspect before adopting Alembic")
    columns = {column["name"]: column for column in inspector.get_columns("users")}
    if columns["password_hash"]["nullable"]:
        raise RuntimeError("Legacy users.password_hash must be NOT NULL")
    if inspector.get_pk_constraint("users")["constrained_columns"] != ["id"]:
        raise RuntimeError("Legacy users.id primary key differs from the application model")
    uniques = inspector.get_unique_constraints("users") + inspector.get_indexes("users")
    if not any(item.get("column_names") == ["email"] and item.get("unique", True) for item in uniques):
        raise RuntimeError("Legacy users.email uniqueness is missing")


def downgrade():
    # Removing only Alembic history must never drop the existing business data.
    pass
