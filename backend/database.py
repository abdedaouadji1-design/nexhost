"""
NexHost V6 - Database (SQLite - ClawCloud Ready)
"""
import logging
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from config import settings

logger = logging.getLogger(__name__)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    max_python_files = Column(Integer, default=10)
    max_php_files = Column(Integer, default=10)
    max_ready_bots = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    bots = relationship("UserBot", back_populates="user", cascade="all, delete")


class ReadyBot(Base):
    __tablename__ = "ready_bots"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    bot_type = Column(String(50), default="telegram")
    code = Column(Text, nullable=False)
    requirements = Column(Text, default="")
    image_url = Column(String(500), nullable=True)
    icon = Column(String(10), default="robot")
    config_fields = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    is_premium = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usage_count = Column(Integer, default=0)


class UserBot(Base):
    __tablename__ = "user_bots"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    bot_template_id = Column(Integer, ForeignKey("ready_bots.id"))
    name = Column(String(100), nullable=False)
    config = Column(JSON, default={})
    modified_code = Column(Text)
    bot_path = Column(String(500))
    log_path = Column(String(500))
    debug_mode = Column(Boolean, default=False)
    status = Column(String(20), default="stopped")
    pid = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="bots")


# Aliases for compatibility
class BotStatus:
    STOPPED = "stopped"
    RUNNING = "running"
    ERROR = "error"


class UserRole:
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"
    
    @classmethod
    def values(cls):
        return [cls.USER, cls.ADMIN, cls.SUPERADMIN]


# Legacy aliases
Project = None
ProjectStatus = None


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    import os
    os.makedirs("/app/data", exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.BOTS_DIR, exist_ok=True)
    os.makedirs(settings.LOGS_DIR, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        from passlib.context import CryptContext
        from sqlalchemy import select
        pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

        r = await session.execute(select(User).where(User.username == settings.SUPER_ADMIN_USERNAME))
        if not r.scalar_one_or_none():
            session.add(User(
                username=settings.SUPER_ADMIN_USERNAME,
                email="superadmin@nexhost.local",
                password_hash=pwd_ctx.hash(settings.SUPER_ADMIN_PASSWORD),
                role="superadmin", is_active=True,
                max_python_files=999, max_php_files=999, max_ready_bots=999,
            ))
        r2 = await session.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        if not r2.scalar_one_or_none():
            session.add(User(
                username=settings.ADMIN_USERNAME,
                email="admin@nexhost.local",
                password_hash=pwd_ctx.hash(settings.ADMIN_PASSWORD),
                role="admin", is_active=True,
            ))
        await session.commit()
    logger.info("Database initialized successfully")
