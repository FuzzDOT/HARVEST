"""
Database Configuration and Connection Management
Handles SQLAlchemy setup, connection pooling, and database operations.
"""

import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DEBUG,
    poolclass=StaticPool if "sqlite" in settings.DATABASE_URL else None,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db() -> Session:
    """
    Dependency to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def init_db():
    """
    Initialize database tables.
    Creates all tables defined in models.
    """
    try:
        # Import all models to ensure they're registered
        from app.models import user, marketplace, prediction, alert
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def get_db_health() -> dict:
    """
    Check database health status.
    Returns connection status and basic metrics.
    """
    try:
        db = SessionLocal()
        
        # Test connection with a simple query
        result = db.execute("SELECT 1")
        result.fetchone()
        
        # Get connection pool info
        pool = engine.pool
        pool_info = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "invalid": pool.invalid()
        }
        
        db.close()
        
        return {
            "healthy": True,
            "status": "connected",
            "pool_info": pool_info,
            "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "local"
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            "healthy": False,
            "status": "disconnected",
            "error": str(e)
        }


def create_tables():
    """
    Create all database tables.
    Used for initial setup and migrations.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("All database tables created")
    except Exception as e:
        logger.error(f"Failed to create tables: {str(e)}")
        raise


def drop_tables():
    """
    Drop all database tables.
    Used for testing and development reset.
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop tables: {str(e)}")
        raise


class DatabaseManager:
    """Database management utilities."""
    
    @staticmethod
    def get_session() -> Session:
        """Get a new database session."""
        return SessionLocal()
    
    @staticmethod
    def close_session(session: Session):
        """Close a database session."""
        session.close()
    
    @staticmethod
    async def execute_query(query: str, params: dict = None):
        """Execute a raw SQL query."""
        session = SessionLocal()
        try:
            result = session.execute(query, params or {})
            session.commit()
            return result.fetchall()
        except Exception as e:
            session.rollback()
            logger.error(f"Query execution failed: {str(e)}")
            raise
        finally:
            session.close()
    
    @staticmethod
    async def get_table_info():
        """Get information about all tables."""
        try:
            session = SessionLocal()
            
            # Get table names
            if "postgresql" in settings.DATABASE_URL:
                query = """
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                ORDER BY table_name, ordinal_position
                """
            elif "mysql" in settings.DATABASE_URL:
                query = """
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = DATABASE()
                ORDER BY table_name, ordinal_position
                """
            else:  # SQLite
                query = "SELECT name FROM sqlite_master WHERE type='table'"
            
            result = session.execute(query)
            tables = result.fetchall()
            session.close()
            
            return tables
            
        except Exception as e:
            logger.error(f"Failed to get table info: {str(e)}")
            return []