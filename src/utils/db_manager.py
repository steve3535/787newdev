# src/utils/db_manager.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from ..models.db_models import Base
from pathlib import Path
import logging

class DatabaseManager:
    def __init__(self, db_url: str = None):
        if db_url is None:
            # Default to SQLite database in src directory
            src_dir = Path(__file__).parent.parent
            db_path = src_dir / 'lottery.db'
            db_url = f'sqlite:///{db_path}'
        
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
    def init_db(self):
        """Initialize database tables"""
        Base.metadata.create_all(self.engine)
        
    def get_session(self) -> Session:
        """Get a database session"""
        return self.SessionLocal()