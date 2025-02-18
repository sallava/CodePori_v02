"""
Initialize services module for financial management application.
Makes financial services available for import throughout the application.
"""

from .financial_service import FinancialService

__all__ = ['FinancialService']