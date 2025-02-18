from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.screening_record import ScreeningRecord, Base
from config.config import Config
import logging

class DataManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.engine = None
        self.Session = None
        self._init_db()
        
    def _init_db(self):
        """Initialize database connection"""
        try:
            db_url = f'postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}'
            self.engine = create_engine(db_url)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            
        except Exception as e:
            self.logger.error(f'Failed to initialize database: {str(e)}')
            raise
            
    def store_reading(self, temperature, timestamp, status):
        """Store temperature reading in database"""
        try:
            session = self.Session()
            record = ScreeningRecord(
                temperature=temperature,
                timestamp=timestamp,
                status=status
            )
            session.add(record)
            session.commit()
            
        except Exception as e:
            self.logger.error(f'Error storing reading: {str(e)}')
            session.rollback()
            raise
            
        finally:
            session.close()
            
    def get_readings(self, limit=100):
        """Retrieve recent temperature readings"""
        try:
            session = self.Session()
            readings = session.query(ScreeningRecord)\
                              .order_by(ScreeningRecord.timestamp.desc())\
                              .limit(limit)\
                              .all()
            return [reading.to_dict() for reading in readings]
            
        except Exception as e:
            self.logger.error(f'Error retrieving readings: {str(e)}')
            raise
            
        finally:
            session.close()
            
    def close_connection(self):
        """Close database connection"""
        try:
            if self.engine:
                self.engine.dispose()
                
        except Exception as e:
            self.logger.error(f'Error closing database connection: {str(e)}')