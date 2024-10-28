# src/models/db_models.py

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    
    mobile = Column(String, primary_key=True)
    last_name = Column(String, nullable=False)
    other_names = Column(String, nullable=False)
    promotional_consent = Column(String(1), nullable=False)
    created_at = Column(DateTime, nullable=False)
    
    # Relationship
    metrics = relationship("PlayerMetrics", back_populates="player")

class PlayerMetrics(Base):
    __tablename__ = 'player_metrics'
    
    id = Column(Integer, primary_key=True)
    mobile = Column(String, ForeignKey('players.mobile'))
    draw_number = Column(Integer, nullable=False)
    tickets_count = Column(Integer, nullable=False)
    e_score = Column(Integer, nullable=False)
    segment = Column(String(1), nullable=False)
    gear = Column(Integer, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    player = relationship("Player", back_populates="metrics")