"""Add Google identity without replacing users or modifying ownership IDs."""

from alembic import context, op
import sqlalchemy as sa

revision = "0002_google_identity"
down_revision = "0001_existing_schema"
branch_labels = None
depends_on = None


def _require_postgresql():
    if op.get_bind().dialect.name != "postgresql":
        raise RuntimeError("This migration uses PostgreSQL ALTER TABLE; no table-recreation fallback is allowed")


def upgrade():
    _require_postgresql()
    op.add_column("users", sa.Column("firebase_uid", sa.String(128), nullable=True))
    op.create_unique_constraint("uq_users_firebase_uid", "users", ["firebase_uid"])
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=True)
    op.create_check_constraint(
        "ck_users_has_authentication", "users", "password_hash IS NOT NULL OR firebase_uid IS NOT NULL"
    )


def downgrade():
    _require_postgresql()
    if context.is_offline_mode():
        raise RuntimeError("Downgrade requires online data checks; offline downgrade is unsafe")
    bind = op.get_bind()
    # Prevent an insertion/link racing the guards and NOT NULL restoration.
    bind.execute(sa.text("LOCK TABLE users IN ACCESS EXCLUSIVE MODE"))
    if bind.scalar(sa.text("SELECT EXISTS (SELECT 1 FROM users WHERE password_hash IS NULL)")):
        raise RuntimeError("Cannot downgrade while Google-only users exist; no accounts were changed")
    linked = bind.scalar(sa.text("SELECT EXISTS (SELECT 1 FROM users WHERE firebase_uid IS NOT NULL)"))
    if linked and context.get_x_argument(as_dictionary=True).get("allow_google_unlink") != "true":
        raise RuntimeError("Downgrade would discard Google links; explicit -x allow_google_unlink=true is required")
    op.drop_constraint("ck_users_has_authentication", "users", type_="check")
    op.alter_column("users", "password_hash", existing_type=sa.String(255), nullable=False)
    op.drop_constraint("uq_users_firebase_uid", "users", type_="unique")
    op.drop_column("users", "firebase_uid")
