from datetime import datetime
from sqlalchemy.orm import Session
from models.financial_models import Income, Expense, Savings, Budget, Report
import pandas as pd

class FinancialService:
    @staticmethod
    def get_user_balance(db: Session, user_id: int):
        total_income = db.query(Income).filter(Income.user_id == user_id).with_entities(func.sum(Income.amount)).scalar() or 0
        total_expense = db.query(Expense).filter(Expense.user_id == user_id).with_entities(func.sum(Expense.amount)).scalar() or 0
        return total_income - total_expense

    @staticmethod
    def generate_monthly_report(db: Session, user_id: int, month: int, year: int):
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month + 1, 1) if month < 12 else datetime(year + 1, 1, 1)
        
        incomes = db.query(Income).filter(
            Income.user_id == user_id,
            Income.date >= start_date,
            Income.date < end_date
        ).all()
        
        expenses = db.query(Expense).filter(
            Expense.user_id == user_id,
            Expense.date >= start_date,
            Expense.date < end_date
        ).all()
        
        return {
            'incomes': [{'amount': i.amount, 'source': i.source, 'date': i.date} for i in incomes],
            'expenses': [{'amount': e.amount, 'category': e.category, 'date': e.date} for e in expenses],
            'total_income': sum(i.amount for i in incomes),
            'total_expense': sum(e.amount for e in expenses)
        }

    @staticmethod
    def export_to_excel(data, filename):
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        return filename