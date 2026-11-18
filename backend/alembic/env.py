"""Use existing metadata/settings without importing routes or AI services."""

from logging.config import fileConfig

from alembic import context

from app.core.config import settings
from app.db.session import Base, engine
from app import models  # noqa: F401 - register all four existing tables

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def migrate(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()
elif config.attributes.get("connection") is not None:
    migrate(config.attributes["connection"])
else:
    with engine.connect() as connection:
        migrate(connection)
