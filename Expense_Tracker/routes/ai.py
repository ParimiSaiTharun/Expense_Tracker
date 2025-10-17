import os
import requests
from flask import Blueprint, render_template, session, redirect, url_for, current_app, flash, request
from models import Expense, Income, Budget, Category
import re
import difflib

bp = Blueprint('ai', __name__)

def get_groq_insight(prompt):
    api_key = current_app.config.get('GROQ_API_KEY') or os.getenv('GROQ_API_KEY')
    if not api_key or api_key == 'your_groq_key':
        return 'AI API key is not set. Please contact support.'
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'llama3-70b-8192',
        'messages': [
            {"role": "system", "content": "You are a helpful financial assistant for an Indian user. Always use INR (₹) and Indian-style comma formatting in all currency values. Do not use USD or dollars."},
            {"role": "user", "content": prompt}
        ],
        'temperature': 0.7
    }
    try:
        response = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            resp_json = response.json()
            return resp_json.get('choices', [{}])[0].get('message', {}).get('content', 'No response from AI.')
        # Try to show Groq's error message if available
        try:
            err_msg = response.json().get('error', {}).get('message')
            if err_msg:
                return f'Error from AI API: {err_msg}'
        except Exception:
            pass
        return f'Error from AI API: {response.status_code} {response.text}'
    except Exception as e:
        return f'Error contacting AI API: {e}'

def extract_category_from_input(user_input, categories):
    user_input = user_input.lower().strip()
    categories_normalized = [cat.lower().strip() for cat in categories]
    match = difflib.get_close_matches(user_input, categories_normalized, n=1, cutoff=0.8)
    if match:
        # Return the original category name (not normalized)
        return categories[categories_normalized.index(match[0])]
    for cat in categories:
        if cat.lower().strip() in user_input:
            return cat
    return None

@bp.route('/ai_insights', methods=['GET', 'POST'])
def ai_insights():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    expenses = Expense.get_by_user(user_id)
    income = Income.get_by_user(user_id)
    budgets = Budget.get_by_user(user_id)

    # Summarize data for AI
    total_expense = sum(float(e['amount']) for e in expenses)
    total_income = sum(float(i['amount']) for i in income)

    # Get all user categories for description matching
    user_categories = [c['name'] for c in Category.get_by_user(user_id)]
    # Robust category-wise expenses
    category_expenses = {}
    for e in expenses:
        cat = e.get('category_name')
        if not cat or cat == 'Uncategorized':
            # Try to infer from description
            desc = (e.get('description') or '').lower()
            matched = None
            for uc in user_categories:
                if uc.lower() in desc:
                    matched = uc
                    break
            cat = matched if matched else 'Miscellaneous'
        category_expenses[cat] = category_expenses.get(cat, 0) + float(e['amount'])

    # Budget allocations
    budget_allocations = {b['category_name']: float(b['amount']) for b in budgets}

    # Income sources
    income_sources = {}
    for i in income:
        src = i.get('source', 'Other')
        income_sources[src] = income_sources.get(src, 0) + float(i['amount'])

    # Format for AI prompt
    category_expenses_numbered = "\n".join([f"{i+1}. {cat}: ₹{amt:,.2f}" for i, (cat, amt) in enumerate(category_expenses.items())])
    budget_allocations_str = ", ".join([f"{cat}: ₹{amt:,.2f}" for cat, amt in budget_allocations.items()])
    income_sources_str = ", ".join([f"{src}: ₹{amt:,.2f}" for src, amt in income_sources.items()])

    # Recent transactions (last 5)
    recent_expenses = expenses[:5] if expenses else []
    recent_expenses_str = "\n".join([
        f"- {e.get('date', '')}: ₹{float(e['amount']):,.2f} on {e.get('category_name', 'Uncategorized')} ({e.get('description', '')})"
        for e in recent_expenses
    ])

    numbered_list_instruction = (
        "Your answer must ONLY be a numbered list. Do not include any narrative or explanations outside the list. "
        "If you need to explain, do so as sub-points under the relevant number. Do not repeat the input data, only analyze and advise in numbered points. "
        "Use only the user's personal information provided above."
    )
    prompt = (
        f"{numbered_list_instruction}\n"
        f"User's Financial Data:\n"
        f"- Total Income: ₹{total_income:,.2f}\n"
        f"- Total Expenses: ₹{total_expense:,.2f}\n"
        f"- Income Sources: {income_sources_str if income_sources_str else 'N/A'}\n"
        f"- Expenses by Category: {category_expenses_numbered if category_expenses_numbered else 'N/A'}\n"
        f"- Budget Allocations: {budget_allocations_str if budget_allocations_str else 'N/A'}\n"
        f"- Recent Transactions (latest 5):\n{recent_expenses_str if recent_expenses_str else 'No recent transactions.'}\n"
        f"Give me a brief financial summary and one tip to save more, using INR and Indian-style formatting only."
    )
    ai_response = get_groq_insight(prompt)
    user_question = None
    user_answer = None
    simulation_scenario = None
    simulation_result = None
    if request.method == 'POST':
        user_question = request.form.get('user_question')
        if user_question:
            full_prompt = (
                f"{numbered_list_instruction}\n"
                f"User's Financial Data:\n"
                f"- Total Income: ₹{total_income:,.2f}\n"
                f"- Total Expenses: ₹{total_expense:,.2f}\n"
                f"- Income Sources: {income_sources_str if income_sources_str else 'N/A'}\n"
                f"- Expenses by Category: {category_expenses_numbered if category_expenses_numbered else 'N/A'}\n"
                f"- Budget Allocations: {budget_allocations_str if budget_allocations_str else 'N/A'}\n"
                f"- Recent Transactions (latest 5):\n{recent_expenses_str if recent_expenses_str else 'No recent transactions.'}\n"
                f"Question: {user_question}\n"
                f"Please answer using only the above data, in INR and Indian formatting."
            )
            user_answer = get_groq_insight(full_prompt)
        simulation_scenario = request.form.get('simulation_scenario')
        if simulation_scenario:
            categories = list(category_expenses.keys())
            category_asked = extract_category_from_input(simulation_scenario, categories)
            if category_asked:
                category_value = category_expenses[category_asked]
                sim_prompt = (
                    f"{numbered_list_instruction}\n"
                    f"User's Financial Data:\n"
                    f"- {category_asked}: ₹{category_value:,.2f}\n"
                    f"Simulation: {simulation_scenario}.\n"
                    f"IMPORTANT: Only use the value for '{category_asked}' above. Do not estimate, assume, or use any other value. "
                    f"If the user asks about a reduction, calculate it based only on this value. "
                    f"If the category is not present, say so."
                )
            else:
                sim_prompt = (
                    f"{numbered_list_instruction}\n"
                    f"User's Financial Data:\n"
                    f"- Categories available: {', '.join(categories)}\n"
                    f"Simulation: {simulation_scenario}.\n"
                    f"IMPORTANT: The category mentioned is not present in the user's data. Please say so."
                )
            simulation_result = get_groq_insight(sim_prompt)
    return render_template('ai_insights.html', ai_response=ai_response, total_expense=total_expense, total_income=total_income, user_question=user_question, user_answer=user_answer, simulation_scenario=simulation_scenario, simulation_result=simulation_result) 