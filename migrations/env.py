import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool, text
from sqlmodel import SQLModel

from alembic import context
from dotenv import load_dotenv

# Import all models to ensure they are registered with SQLModel metadata
from db.models.alpha import *
from db.models.social import *
from db.connection import get_env_prefix

# Load environment variables
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the sqlalchemy url from environment variable
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    # Get current environment prefix
    env_prefix = get_env_prefix()
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        # Set search_path to ensure we're working with the right schema
        connection.execute(text("SET search_path TO public"))
        
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Include environment prefix in migration context
            include_schemas=True,
            version_table_schema="public"
        )

        with context.begin_transaction():
            # Log the current environment
            print(f"Running migrations with {env_prefix} prefix")
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
