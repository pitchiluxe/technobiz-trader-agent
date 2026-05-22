"""Database connection and management."""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config.settings import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self):
        """Initialize database manager."""
        self.engine = None
        self.SessionLocal = None
        self._init_engine()

    def _init_engine(self):
        """Initialize SQLAlchemy engine."""
        try:
            # Use StaticPool for SQLite in-memory or file-based
            if "sqlite" in settings.DATABASE_URL:
                self.engine = create_engine(
                    settings.DATABASE_URL,
                    echo=settings.SQLALCHEMY_ECHO,
                    poolclass=StaticPool if ":memory:" in settings.DATABASE_URL else None,
                )
            else:
                # PostgreSQL or other databases
                self.engine = create_engine(
                    settings.DATABASE_URL,
                    echo=settings.SQLALCHEMY_ECHO,
                )
            
            self.SessionLocal = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            logger.info(f"Database initialized: {settings.DATABASE_URL}")
        except Exception as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    def create_tables(self):
        """Create all database tables."""
        try:
            # Import models here to avoid circular imports
            from .models import Base
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            raise

    def close(self):
        """Close database connections."""
        try:
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {str(e)}")


# Global database manager instance
db_manager = DatabaseManager()
