"""Database utilities and connection management for Unity AI platform."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import (
    String,
    DateTime,
    Text,
    Boolean,
    Integer,
    Float,
    JSON,
    select,
    update,
    delete,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from uuid import uuid4, UUID as UUIDType

from .config import get_settings
from .logging import get_logger
from .exceptions import DatabaseError

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class UUIDMixin:
    """Mixin for UUID primary key."""
    id: Mapped[UUIDType] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False
    )


class WorkflowExecution(Base, UUIDMixin, TimestampMixin):
    """Workflow execution database model."""
    __tablename__ = "workflow_executions"
    
    workflow_id: Mapped[UUIDType] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    trigger_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    execution_log: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class CodeExecution(Base, UUIDMixin, TimestampMixin):
    """Code execution database model."""
    __tablename__ = "code_executions"
    
    language: Mapped[str] = mapped_column(String(50), nullable=False, default="python")
    code: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timeout: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    environment: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
    requirements: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class AgentExecution(Base, UUIDMixin, TimestampMixin):
    """Agent execution database model."""
    __tablename__ = "agent_executions"
    
    agent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    task: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    execution_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class SystemMetrics(Base, UUIDMixin, TimestampMixin):
    """System metrics database model."""
    __tablename__ = "system_metrics"
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    labels: Mapped[Optional[Dict[str, str]]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class DatabaseManager:
    """Database connection and session management."""
    
    def __init__(self):
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connection."""
        if self._initialized:
            return
        
        try:
            settings = get_settings()
            
            # Create async engine
            self._engine = create_async_engine(
                settings.database.url,
                pool_size=settings.database.pool_size,
                max_overflow=settings.database.max_overflow,
                echo=settings.database.echo,
                future=True
            )
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            self._initialized = True
            logger.info("Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")
    
    async def close(self) -> None:
        """Close database connection."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._initialized = False
            logger.info("Database connection closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session with automatic cleanup."""
        if not self._initialized:
            await self.initialize()
        
        if not self._session_factory:
            raise DatabaseError("Database not initialized")
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise DatabaseError(f"Database operation failed: {e}")
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        if not self._engine:
            await self.initialize()
        
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise DatabaseError(f"Table creation failed: {e}")
    
    async def drop_tables(self) -> None:
        """Drop all database tables."""
        if not self._engine:
            await self.initialize()
        
        try:
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise DatabaseError(f"Table drop failed: {e}")
    
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            async with self.get_session() as session:
                result = await session.execute(select(func.now()))
                result.scalar()
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session (dependency injection helper)."""
    async with db_manager.get_session() as session:
        yield session


async def init_database() -> None:
    """Initialize database and create tables."""
    await db_manager.initialize()
    await db_manager.create_tables()


async def close_database() -> None:
    """Close database connection."""
    await db_manager.close()


# Repository base class
class BaseRepository:
    """Base repository class for database operations."""
    
    def __init__(self, session: AsyncSession, model_class):
        self.session = session
        self.model_class = model_class
    
    async def create(self, **kwargs) -> Any:
        """Create a new record."""
        try:
            instance = self.model_class(**kwargs)
            self.session.add(instance)
            await self.session.flush()
            await self.session.refresh(instance)
            return instance
        except Exception as e:
            logger.error(f"Failed to create {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Create operation failed: {e}")
    
    async def get_by_id(self, id: UUIDType) -> Optional[Any]:
        """Get record by ID."""
        try:
            result = await self.session.execute(
                select(self.model_class).where(self.model_class.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get {self.model_class.__name__} by ID: {e}")
            raise DatabaseError(f"Get operation failed: {e}")
    
    async def update(self, id: UUIDType, **kwargs) -> Optional[Any]:
        """Update record by ID."""
        try:
            kwargs['updated_at'] = datetime.utcnow()
            await self.session.execute(
                update(self.model_class)
                .where(self.model_class.id == id)
                .values(**kwargs)
            )
            return await self.get_by_id(id)
        except Exception as e:
            logger.error(f"Failed to update {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Update operation failed: {e}")
    
    async def delete(self, id: UUIDType) -> bool:
        """Delete record by ID."""
        try:
            result = await self.session.execute(
                delete(self.model_class).where(self.model_class.id == id)
            )
            return result.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to delete {self.model_class.__name__}: {e}")
            raise DatabaseError(f"Delete operation failed: {e}")
    
    async def list_all(self, limit: int = 100, offset: int = 0) -> List[Any]:
        """List all records with pagination."""
        try:
            result = await self.session.execute(
                select(self.model_class)
                .order_by(self.model_class.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Failed to list {self.model_class.__name__}: {e}")
            raise DatabaseError(f"List operation failed: {e}")