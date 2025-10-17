import csv
from io import StringIO
from flask import Blueprint, render_template, session, redirect, url_for, Response
from models import Expense
from collections import defaultdict
from datetime import datetime
from routes.ai import get_groq_insight

bp = Blueprint('report', __name__)

@bp.route('/reports')
def reports():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    expenses = Expense.get_by_user(user_id)
    # Monthly summary
    monthly = defaultdict(float)
    yearly = defaultdict(float)
    for e in expenses:
        month = str(e['date'])[:7]  # YYYY-MM
        year = str(e['date'])[:4]
        monthly[month] += float(e['amount'])
        yearly[year] += float(e['amount'])
    # AI summary
    total_expense = sum(float(e['amount']) for e in expenses)
    from models import Income, Budget
    income = Income.get_by_user(user_id)
    budgets = Budget.get_by_user(user_id)
    total_income = sum(float(i['amount']) for i in income)
    # Category-wise expenses
    category_expenses = {}
    for e in expenses:
        cat = e.get('category_name') or 'Miscellaneous'
        if not cat or cat.lower() == 'none':
            cat = 'Miscellaneous'
        category_expenses[cat] = category_expenses.get(cat, 0) + float(e['amount'])
    category_expenses_str = ", ".join([f"{cat}: ₹{amt:,.2f}" for cat, amt in category_expenses.items()])
    # Budget allocations
    budget_allocations = {b['category_name']: float(b['amount']) for b in budgets}
    budget_allocations_str = ", ".join([f"{cat}: ₹{amt:,.2f}" for cat, amt in budget_allocations.items()])
    # Recent transactions (last 5)
    recent_expenses = expenses[:5] if expenses else []
    recent_expenses_str = "\n".join([
        f"- {e.get('date', '')}: ₹{float(e['amount']):,.2f} on {e.get('category_name', 'Uncategorized')} ({e.get('description', '')})"
        for e in recent_expenses
    ])
    prompt = (
        f"User's Financial Data:\n"
        f"- Total Income: ₹{total_income:,.2f}\n"
        f"- Total Expenses: ₹{total_expense:,.2f}\n"
        f"- Expenses by Category: {category_expenses_str if category_expenses_str else 'N/A'}\n"
        f"- Budget Allocations: {budget_allocations_str if budget_allocations_str else 'N/A'}\n"
        f"- Recent Transactions (latest 5):\n{recent_expenses_str if recent_expenses_str else 'No recent transactions.'}\n"
        "Give me a brief financial summary and one tip to save more, using INR and Indian-style formatting only. Always answer in clear, point-wise format (numbered or bulleted list) for better readability."
    )
    ai_summary = get_groq_insight(prompt)
    return render_template('reports.html', monthly=monthly, yearly=yearly, ai_summary=ai_summary)

@bp.route('/reports/download')
def download_report():
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
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=expense_report.csv'})

@bp.route('/reports/download_plan')
def download_plan_report():
    from flask import session, make_response
    import io, csv
    from datetime import datetime
    plan = session.get('user_plan')
    if not plan:
        return redirect(url_for('report.reports'))
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['Start Date', 'End Date', 'Total Income', 'Total Expenses'])
    try:
        start_str = datetime.strptime(plan['start_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
        end_str = datetime.strptime(plan['end_date'], '%Y-%m-%d').strftime('%d/%m/%Y')
    except Exception:
        start_str = plan['start_date']
        end_str = plan['end_date']
    total_income = session.get('plan', {}).get('income', '')
    total_expenses = session.get('plan', {}).get('expenses', '')
    cw.writerow([start_str, end_str, total_income, total_expenses])
    cw.writerow([])
    cw.writerow(['Category', 'Planned Amount', 'Description'])
    from models import Category
    user_id = session.get('user_id')
    cat_map = {str(cat['id']): cat['name'] for cat in Category.get_by_user(user_id)}
    for cat_id, entry in plan['plan'].items():
        cat_name = cat_map.get(str(cat_id), f'Category {cat_id}')
        cw.writerow([cat_name, entry['amount'], entry['note']])
    output = make_response(si.getvalue())
    output.headers['Content-Disposition'] = 'attachment; filename=plan.csv'
    output.headers['Content-type'] = 'text/csv'
    return output

@bp.route('/reports/download_ai_summary')
def download_ai_summary():
    if 'user_id' not in session:
        return redirect(url_for('report.reports'))
    user_id = session['user_id']
    from models import Expense, Income, Budget
    expenses = Expense.get_by_user(user_id)
    income = Income.get_by_user(user_id)
    budgets = Budget.get_by_user(user_id)
    total_expense = sum(float(e['amount']) for e in expenses)
    total_income = sum(float(i['amount']) for i in income)
    # Category-wise expenses
    category_expenses = {}
    for e in expenses:
        cat = e.get('category_name', 'Uncategorized')
        category_expenses[cat] = category_expenses.get(cat, 0) + float(e['amount'])
    category_expenses_str = ", ".join([f"{cat}: ₹{amt:,.2f}" for cat, amt in category_expenses.items()])
    # Budget allocations
    budget_allocations = {b['category_name']: float(b['amount']) for b in budgets}
    budget_allocations_str = ", ".join([f"{cat}: ₹{amt:,.2f}" for cat, amt in budget_allocations.items()])
    # Recent transactions (last 5)
    recent_expenses = expenses[:5] if expenses else []
    recent_expenses_str = "\n".join([
        f"- {e.get('date', '')}: ₹{float(e['amount']):,.2f} on {e.get('category_name', 'Uncategorized')} ({e.get('description', '')})"
        for e in recent_expenses
    ])
    prompt = (
        f"User's Financial Data:\n"
        f"- Total Income: ₹{total_income:,.2f}\n"
        f"- Total Expenses: ₹{total_expense:,.2f}\n"
        f"- Expenses by Category: {category_expenses_str if category_expenses_str else 'N/A'}\n"
        f"- Budget Allocations: {budget_allocations_str if budget_allocations_str else 'N/A'}\n"
        f"- Recent Transactions (latest 5):\n{recent_expenses_str if recent_expenses_str else 'No recent transactions.'}\n"
        "Give me a brief financial summary and one tip to save more, using INR and Indian-style formatting only. Always answer in clear, point-wise format (numbered or bulleted list) for better readability."
    )
    ai_summary = get_groq_insight(prompt)
    from flask import Response
    return Response(ai_summary, mimetype='text/plain', headers={'Content-Disposition': 'attachment;filename=ai_finance_summary.txt'}) 