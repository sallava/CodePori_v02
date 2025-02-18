from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class DetectionEvent(Base):
    __tablename__ = 'detection_events'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    mask_status = Column(String)
    confidence = Column(Float)
    
    def __repr__(self):
        return f"<DetectionEvent(timestamp={self.timestamp}, "\
               f"mask_status={self.mask_status}, "\
               f"confidence={self.confidence})>"