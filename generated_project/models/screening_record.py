from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ScreeningRecord(Base):
    __tablename__ = 'screening_records'

    id = Column(Integer, primary_key=True)
    temperature = Column(Float, nullable=False)
    status = Column(String(20), nullable=False)
    alert_triggered = Column(Boolean, default=False)
    timestamp = Column(DateTime, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'temperature': self.temperature,
            'status': self.status,
            'alert_triggered': self.alert_triggered,
            'timestamp': self.timestamp.isoformat()
        }