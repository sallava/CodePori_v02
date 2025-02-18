from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime
from database.database import Base

class Income(Base):
    __tablename__ = 'income'
    
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    description = Column(String(200))

class Expense(Base):
    __tablename__ = 'expense'
    
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    description = Column(String(200))

class Savings(Base):
    __tablename__ = 'savings'
    
    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    description = Column(String(200))