from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import logging

from config.configuration import Configuration
from models.detection_event import Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.config = Configuration()
        self.engine = self._create_engine()
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
    
    def _create_engine(self):
        db_url = f"postgresql://{self.config.DB_USER}:{self.config.DB_PASSWORD}@"\
                f"{self.config.DB_HOST}:{self.config.DB_PORT}/{self.config.DB_NAME}"
        return create_engine(db_url)
    
    @contextmanager
    def session_scope(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            session.close()
    
    def log_detection(self, event):
        try:
            with self.session_scope() as session:
                session.add(event)
        except Exception as e:
            logger.error(f"Failed to log detection event: {str(e)}")
    
    def close(self):
        if self.engine:
            self.engine.dispose()