from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from .database import Base

class Developer(Base):
    __tablename__ = "developers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    git_username = Column(String, unique=True, index=True)
    wakatime_api_key = Column(String, nullable=True)

    metrics = relationship("Metric", back_populates="developer")

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # e.g. "owner/repo"
    url = Column(String, nullable=True)
    token = Column(String, nullable=True)

class Metric(Base):
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    developer_id = Column(Integer, ForeignKey("developers.id"))
    date = Column(Date, index=True)
    
    # Git Metrics
    commits_count = Column(Integer, default=0)
    
    # WakaTime Metrics
    coding_time_seconds = Column(Integer, default=0)
    
    # Review Metrics (could be extended)
    review_count = Column(Integer, default=0)
    
    # Composite Score
    score = Column(Float, default=0.0)
    
    # Tracking
    updated_at = Column(DateTime, nullable=True)

    developer = relationship("Developer", back_populates="metrics")
