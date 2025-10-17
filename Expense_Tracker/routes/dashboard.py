from flask import Blueprint, render_template, session, redirect, url_for
from models import Expense, Income
from collections import defaultdict
from routes.ai import get_groq_insight

bp = Blueprint('dashboard', __name__)

@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    expenses = Expense.get_by_user(user_id)
    income = Income.get_by_user(user_id)
    # Prepare data for charts
    category_totals = defaultdict(float)
    monthly_expenses = defaultdict(float)
    for e in expenses:
        category = e.get('category_name') or 'Miscellaneous'
        if not category or category.lower() == 'none':
            category = 'Miscellaneous'
        category_totals[category] += float(e['amount'])
        month = str(e['date'])[:7]  # YYYY-MM
        monthly_expenses[month] += float(e['amount'])
    monthly_income = defaultdict(float)
    for i in income:
        month = str(i['date'])[:7]
        monthly_income[month] += float(i['amount'])
    # Spending personality
    total_expense = sum(float(e['amount']) for e in expenses)
    total_income = sum(float(i['amount']) for i in income)
    # Prepare more detailed data for AI
    # Category-wise expenses for AI
    category_expenses = defaultdict(float)
    for e in expenses:
        category = e.get('category_name') or 'Miscellaneous'
        if not category or category.lower() == 'none':
            category = 'Miscellaneous'
        category_expenses[category] += float(e['amount'])
    # Recent transactions (last 5)
    recent_expenses = expenses[:5] if expenses else []
    recent_expenses_str = "\n".join([
        f"- {e.get('date', '')}: ₹{float(e['amount']):,.2f} on {e.get('category_name', 'Uncategorized')} ({e.get('description', '')})"
        for e in recent_expenses
    ])
    # Budgets
    from models import Budget
    budgets = Budget.get_by_user(user_id)
    budget_allocations = {b['category_name']: float(b['amount']) for b in budgets}
    budget_allocations_str = ", ".join([f"{cat}: ₹{amt:,.2f}" for cat, amt in budget_allocations.items()])
    category_expenses_str = ", ".join([f"{cat}: ₹{amt:,.2f}" for cat, amt in category_expenses.items()])
    prompt = (
        f"User's Financial Data:\n"
        f"- Total Income: ₹{total_income:,.2f}\n"
        f"- Total Expenses: ₹{total_expense:,.2f}\n"
        f"- Expenses by Category: {category_expenses_str if category_expenses_str else 'N/A'}\n"
        f"- Budget Allocations: {budget_allocations_str if budget_allocations_str else 'N/A'}\n"
        f"- Recent Transactions (latest 5):\n{recent_expenses_str if recent_expenses_str else 'No recent transactions.'}\n"
        "Based on my full financial data, what is my spending personality (Saver, Spender, Planner, etc.)? Give a short label (one word) and a 1-2 sentence explanation. Always answer in clear, point-wise format (numbered or bulleted list) for better readability. Respond in the format: 'Label: <label>\nExplanation: <explanation>'."
    )
    ai_personality = get_groq_insight(prompt)
    personality_label = None
    personality_explanation = None
    if ai_personality:
        try:
            for line in ai_personality.split('\n'):
                if line.lower().startswith('label:'):
                    personality_label = line.split(':',1)[1].strip()
                elif line.lower().startswith('explanation:'):
                    personality_explanation = line.split(':',1)[1].strip()
        except Exception:
            pass
    return render_template('dashboard.html',
        category_labels=list(category_totals.keys()),
        category_data=list(category_totals.values()),
        months=sorted(set(list(monthly_expenses.keys()) + list(monthly_income.keys()))),
        expenses_by_month=[monthly_expenses[m] for m in sorted(set(list(monthly_expenses.keys()) + list(monthly_income.keys())))],
        income_by_month=[monthly_income[m] for m in sorted(set(list(monthly_expenses.keys()) + list(monthly_income.keys())))],
        personality_label=personality_label,
        personality_explanation=personality_explanation
    ) 