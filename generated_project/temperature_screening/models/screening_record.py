from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ScreeningRecord(Base):
    __tablename__ = 'screening_records'
    
    id = Column(Integer, primary_key=True)
    temperature = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    status = Column(String(10), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'temperature': self.temperature,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status
        }