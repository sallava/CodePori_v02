from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from config.config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, 
                       pool_size=Config.SQLALCHEMY_POOL_SIZE,
                       max_overflow=Config.SQLALCHEMY_MAX_OVERFLOW)

db_session = scoped_session(sessionmaker(autocommit=False,
                                       autoflush=False,
                                       bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

def init_db(app):
    import models.financial_models
    Base.metadata.create_all(bind=engine)
    
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()