from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import Budget, Category, Expense
from collections import defaultdict
from datetime import datetime

bp = Blueprint('budget', __name__)

@bp.route('/budgets', methods=['GET', 'POST'])
def manage_budgets():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    categories = Category.get_by_user(user_id)
    budgets = Budget.get_by_user(user_id)
    alerts = []
    # Calculate spending per category and compare to budget
    for b in budgets:
        spent = sum(float(e['amount']) for e in Expense.get_by_user(user_id) if e.get('category_id') == b['category_id'])
        budget_amount = float(b['amount'])
        if spent >= budget_amount:
            exceeded = spent - budget_amount
            alerts.append(f"Alert: You have exceeded your budget for {b['category_name']} by ₹{exceeded:,.2f}!")
        elif spent >= 0.8 * budget_amount:
            left = budget_amount - spent
            alerts.append(f"Warning: You are close to your budget for {b['category_name']}. Only ₹{left:,.2f} left.")
    # Historical trends: for each month, did user stay within total budget?
    expenses = Expense.get_by_user(user_id)
    monthly_expenses = defaultdict(float)
    for e in expenses:
        month = str(e['date'])[:7]  # YYYY-MM
        monthly_expenses[month] += float(e['amount'])
    total_budget = sum(float(b['amount']) for b in budgets)
    months_sorted = sorted(monthly_expenses.keys())
    stayed_within_budget = [1 if monthly_expenses[m] <= total_budget and total_budget > 0 else 0 for m in months_sorted]
    # Optionally, also pass the actual spent and budget for charting
    monthly_spent = [monthly_expenses[m] for m in months_sorted]
    monthly_budget = [total_budget for _ in months_sorted]
    if request.method == 'POST':
        category_id = int(request.form['category_id'])
        amount = float(request.form['amount'])
        # Check if a budget already exists for this category
        existing = next((b for b in budgets if b['category_id'] == category_id), None)
        if existing:
            new_amount = float(existing['amount']) + amount
            Budget.set_budget(user_id, category_id, new_amount)
            flash('Budget updated (added to existing amount)!')
        else:
            Budget.set_budget(user_id, category_id, amount)
            flash('Budget set!')
        return redirect(url_for('budget.manage_budgets'))
    return render_template('budgets.html', categories=categories, budgets=budgets, alerts=alerts, months=months_sorted, stayed_within_budget=stayed_within_budget, monthly_spent=monthly_spent, monthly_budget=monthly_budget) 