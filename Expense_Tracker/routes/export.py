import csv
from io import StringIO
from flask import Blueprint, session, redirect, url_for, Response
from models import Expense, Income, Budget
from datetime import datetime

bp = Blueprint('export', __name__)

@bp.route('/export/expenses')
def export_expenses():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    expenses = Expense.get_by_user(user_id)
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Amount', 'Category', 'Description'])
    for e in expenses:
        date_str = e['date']
        try:
            date_str = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            pass
        cw.writerow([date_str, e['amount'], e.get('category_name', 'Uncategorized'), e['description']])
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=expenses.csv'})

@bp.route('/export/income')
def export_income():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    income = Income.get_by_user(user_id)
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Date', 'Amount', 'Source', 'Description'])
    for i in income:
        date_str = i['date']
        try:
            date_str = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m/%Y')
        except Exception:
            pass
        cw.writerow([date_str, i['amount'], i['source'], i['description']])
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=income.csv'})

@bp.route('/export/budgets')
def export_budgets():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    budgets = Budget.get_by_user(user_id)
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Category', 'Budget'])
    for b in budgets:
        # If budgets ever include a date, format it here
        cw.writerow([b['category_name'], b['amount']])
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=budgets.csv'}) 