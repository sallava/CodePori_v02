from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from typing import List, Optional
from datetime import datetime, timedelta
from models.screening_record import Base, ScreeningRecord
from config.config import config

class DataManager:
    def __init__(self):
        db_url = f'postgresql://{config.database.user}:{config.database.password}@'\
                 f'{config.database.host}:{config.database.port}/{config.database.database}'
        
        self.engine = create_engine(
            db_url,
            pool_size=config.database.pool_size,
            max_overflow=config.database.max_overflow
        )
        
        Base.metadata.create_all(self.engine)
        session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(session_factory)

    def save_temperature_reading(self, temperature: float, status: str,
                               alert_triggered: bool = False) -> ScreeningRecord:
        session = self.Session()
        try:
            record = ScreeningRecord(
                temperature=temperature,
                status=status,
                alert_triggered=alert_triggered,
                timestamp=datetime.now()
            )
            session.add(record)
            session.commit()
            return record
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_recent_readings(self, hours: int = 24) -> List[ScreeningRecord]:
        session = self.Session()
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return session.query(ScreeningRecord)\
                          .filter(ScreeningRecord.timestamp >= cutoff_time)\
                          .order_by(ScreeningRecord.timestamp.desc())\
                          .all()
        finally:
            session.close()

    def get_alerts(self, start_date: datetime,
                   end_date: Optional[datetime] = None) -> List[ScreeningRecord]:
        session = self.Session()
        try:
            query = session.query(ScreeningRecord)\
                          .filter(ScreeningRecord.alert_triggered == True)\
                          .filter(ScreeningRecord.timestamp >= start_date)
            
            if end_date:
                query = query.filter(ScreeningRecord.timestamp <= end_date)
                
            return query.order_by(ScreeningRecord.timestamp.desc()).all()
        finally:
            session.close()

    def get_statistics(self, period: timedelta) -> dict:
        session = self.Session()
        try:
            start_time = datetime.now() - period
            records = session.query(ScreeningRecord)\
                            .filter(ScreeningRecord.timestamp >= start_time)\
                            .all()
            
            total = len(records)
            if total == 0:
                return {
                    'total': 0,
                    'normal': 0,
                    'elevated': 0,
                    'fever': 0,
                    'alerts': 0
                }
            
            return {
                'total': total,
                'normal': sum(1 for r in records if r.status == 'NORMAL'),
                'elevated': sum(1 for r in records if r.status == 'ELEVATED'),
                'fever': sum(1 for r in records if r.status == 'FEVER'),
                'alerts': sum(1 for r in records if r.alert_triggered)
            }
        finally:
            session.close()