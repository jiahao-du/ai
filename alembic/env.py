from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# 导入您的模型
from app.models import Base

# Alembic Config对象，提供访问配置文件值的功能。
config = context.config

# 从文件配置中使用Python内建logging.config工具
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 为自动生成脚本的MetaData对象
target_metadata = Base.metadata

def run_migrations_offline():
    """在不创建数据库连接的情况下运行迁移。
    此时上下文配置与实际的连接无关。
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

def run_migrations_online():
    """上线模式下运行迁移。
    在此模式下，我们需要创建数据库连接并与上下文绑定。
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()

# 根据线上或离线模式调用特定函数
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()