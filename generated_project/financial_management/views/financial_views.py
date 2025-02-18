from flask import Blueprint, request, jsonify
from datetime import datetime
from services.financial_service import FinancialService

financial_bp = Blueprint('financial', __name__)

@financial_bp.route('/income', methods=['POST'])
def add_income():
    data = request.get_json()
    try:
        income = FinancialService.add_income(
            amount=float(data['amount']),
            category=data['category'],
            date=datetime.fromisoformat(data['date']),
            description=data['description']
        )
        return jsonify({'message': 'Income added successfully', 'id': income.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@financial_bp.route('/expense', methods=['POST'])
def add_expense():
    data = request.get_json()
    try:
        expense = FinancialService.add_expense(
            amount=float(data['amount']),
            category=data['category'],
            date=datetime.fromisoformat(data['date']),
            description=data['description']
        )
        return jsonify({'message': 'Expense added successfully', 'id': expense.id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@financial_bp.route('/report/monthly/<int:year>/<int:month>')
def get_monthly_report(year, month):
    try:
        report = FinancialService.generate_monthly_report(year, month)
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@financial_bp.route('/report/export/<int:year>/<int:month>')
def export_report(year, month):
    try:
        report = FinancialService.generate_monthly_report(year, month)
        filename = f'financial_report_{year}_{month}.xlsx'
        FinancialService.export_to_excel(report, filename)
        return jsonify({'message': 'Report exported successfully', 'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 400