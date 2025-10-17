from flask import Blueprint, render_template, session, redirect, url_for, request, current_app, send_file, make_response, jsonify, flash
from models import Expense, Income, Category
from routes.ai import get_groq_insight
from datetime import date, timedelta, datetime
import io
import csv

bp = Blueprint('plan', __name__)

@bp.route('/plan', methods=['GET', 'POST'])
def plan():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    categories = Category.get_by_user(user_id)
    today = date.today()
    default_start = today.replace(day=1).isoformat()
    if today.month == 12:
        default_end = date(today.year+1, 1, 1).isoformat()
    else:
        default_end = date(today.year, today.month+1, 1).isoformat()
    user_plan = session.get('user_plan')
    if user_plan and user_plan.get('start_date') and user_plan.get('end_date'):
        start_date = user_plan['start_date']
        end_date = user_plan['end_date']
    else:
        start_date = request.args.get('start_date') or default_start
        end_date = request.args.get('end_date') or default_end
    # Fetch income and expenses in range
    expenses = Expense.get_by_user_and_date(user_id, start_date, end_date)
    income = Income.get_by_user_and_date(user_id, start_date, end_date)
    total_expenses = sum(float(e['amount']) for e in expenses)
    total_income = sum(float(i['amount']) for i in income)
    ai_answer = None
    if request.method == 'POST' and 'ai_question' in request.form:
        ai_question = request.form['ai_question']
        prompt = f"User's plan for {start_date} to {end_date}: income=₹{total_income:,.2f}, expenses=₹{total_expenses:,.2f} (INR). Question: {ai_question}. Answer in INR and Indian formatting only."
        ai_answer = get_groq_insight(prompt)
        session['plan_ai'] = ai_answer
    error_past_plan = None
    if request.method == 'POST' and request.form.get('plan_entry') == '1':
        # Use submitted start_date and end_date for saving
        save_start = request.form.get('start_date') or start_date
        save_end = request.form.get('end_date') or end_date
        try:
            end_dt = date.fromisoformat(save_end)
            if end_dt < date.today():
                error_past_plan = 'Plan end date is in the past. Please select a future date.'
        except Exception:
            pass
        if not error_past_plan:
            # Always start with a fresh plan_data dict
            plan_data = {}
            for cat in categories:
                amt = request.form.get(f'planned_amount_{cat["id"]}')
                note = request.form.get(f'plan_note_{cat["id"]}')
                if amt is not None and amt != '' and float(amt) > 0:
                    plan_data[cat['id']] = {'amount': float(amt), 'note': note or ''}
            new_cat_names = request.form.getlist('new_category_name[]')
            new_cat_amts = request.form.getlist('new_category_amount[]')
            new_cat_notes = request.form.getlist('new_category_note[]')
            for i in range(len(new_cat_names)):
                name = new_cat_names[i].strip()
                amt = new_cat_amts[i] if i < len(new_cat_amts) else None
                note = new_cat_notes[i] if i < len(new_cat_notes) else ''
                if name and amt and float(amt) > 0:
                    Category.create(name, user_id)
            categories = Category.get_by_user(user_id)
            for i in range(len(new_cat_names)):
                name = new_cat_names[i].strip()
                amt = new_cat_amts[i] if i < len(new_cat_amts) else None
                note = new_cat_notes[i] if i < len(new_cat_notes) else ''
                if name and amt and float(amt) > 0:
                    for c in categories:
                        if c['name'].lower() == name.lower():
                            plan_data[c['id']] = {'amount': float(amt), 'note': note or ''}
                            break
            plan_data = {str(k): v for k, v in plan_data.items()}
            session['user_plan'] = {
                'start_date': str(save_start),
                'end_date': str(save_end),
                'plan': plan_data
            }
            flash('Plan saved! You can now add it to your budget.', 'success')
            return redirect(url_for('plan.plan'))
    user_plan = session.get('user_plan', {})
    return render_template('plan.html',
        categories=categories,
        start_date=start_date,
        end_date=end_date,
        income=total_income,
        expenses=total_expenses,
        user_plan=user_plan,
        ai_answer=ai_answer,
        error_past_plan=error_past_plan
    )

@bp.route('/plan/download', methods=['POST'])
def download_plan():
    plan = session.get('user_plan')
    if not plan:
        return redirect(url_for('plan.plan'))
    si = io.StringIO()
    cw = csv.writer(si)
    # Write plan summary without dates
    cw.writerow(['Total Income', 'Total Expenses'])
    total_income = plan.get('income', '')
    total_expenses = plan.get('expenses', '')
    cw.writerow([total_income, total_expenses])
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

@bp.route('/plan/first_txn_date')
def plan_first_txn_date():
    if 'user_id' not in session:
        return jsonify({'start_date': '', 'end_date': ''})
    user_id = session['user_id']
    period = request.args.get('period')
    today = date.today()
    if period == 'month':
        # Get first transaction date in this month
        first_exp = Expense.get_by_user_and_date(user_id, today.replace(day=1).isoformat(), today.isoformat())
        first_inc = Income.get_by_user_and_date(user_id, today.replace(day=1).isoformat(), today.isoformat())
        all_dates = [e['date'] for e in first_exp] + [i['date'] for i in first_inc]
        if all_dates:
            start_date = min(all_dates)
        else:
            start_date = today.replace(day=1).isoformat()
        # End date is same day next month
        if today.month == 12:
            end_date = date(today.year+1, 1, today.day).isoformat()
        else:
            try:
                end_date = date(today.year, today.month+1, today.day).isoformat()
            except:
                # If next month doesn't have this day, use last day of next month
                from calendar import monthrange
                last_day = monthrange(today.year, today.month+1)[1]
                end_date = date(today.year, today.month+1, last_day).isoformat()
    elif period == 'year':
        # Get first transaction date in this year
        first_exp = Expense.get_by_user_and_date(user_id, today.replace(month=1, day=1).isoformat(), today.isoformat())
        first_inc = Income.get_by_user_and_date(user_id, today.replace(month=1, day=1).isoformat(), today.isoformat())
        all_dates = [e['date'] for e in first_exp] + [i['date'] for i in first_inc]
        if all_dates:
            start_date = min(all_dates)
        else:
            start_date = today.replace(month=1, day=1).isoformat()
        # End date is same day next year
        try:
            end_date = date(today.year+1, today.month, today.day).isoformat()
        except:
            end_date = date(today.year+1, today.month, 28).isoformat()
    else:
        start_date = today.isoformat()
        end_date = today.isoformat()
    return jsonify({'start_date': start_date, 'end_date': end_date})

@bp.route('/plan/add_to_budget', methods=['POST'])
def add_to_budget():
    if 'user_id' not in session or 'user_plan' not in session:
        flash('No plan to add to budget.', 'danger')
        return redirect(url_for('plan.plan'))
    user_id = session['user_id']
    plan = session['user_plan']
    from datetime import date
    from models import Budget, Category
    # Always refresh categories to get latest IDs
    categories = Category.get_by_user(user_id)
    cat_name_to_id = {c['name'].strip().lower(): c['id'] for c in categories}
    # Build a new plan dict with only valid category IDs
    valid_plan = {}
    for cat_id, entry in plan['plan'].items():
        resolved_id = None
        # Try to resolve as int
        try:
            resolved_id = int(cat_id)
            if resolved_id not in [c['id'] for c in categories]:
                resolved_id = None
        except Exception:
            pass
        # If not resolved, try by note
        if not resolved_id:
            if 'note' in entry and entry['note']:
                note_name = entry['note'].strip().lower()
                if note_name in cat_name_to_id:
                    resolved_id = cat_name_to_id[note_name]
        # Try by category name string
        if not resolved_id and cat_id.lower() in cat_name_to_id:
            resolved_id = cat_name_to_id[cat_id.lower()]
        if resolved_id:
            valid_plan[str(resolved_id)] = entry
        else:
            flash(f'Could not find category for plan entry: {cat_id}', 'danger')
    # Now set budgets only for valid categories
    existing_budgets = {b['category_id']: float(b['amount']) for b in Budget.get_by_user(user_id)}
    for cat_id, entry in valid_plan.items():
        try:
            cat_id_int = int(cat_id)
            amount = float(entry['amount'])
            if cat_id_int in existing_budgets:
                new_amount = existing_budgets[cat_id_int] + amount
                Budget.set_budget(user_id, cat_id_int, new_amount)
            else:
                Budget.set_budget(user_id, cat_id_int, amount)
        except Exception as e:
            flash(f'Error setting budget for category: {e}', 'danger')
            continue
    flash('Budgets set successfully for your plan period!', 'success')
    session.pop('user_plan', None)
    return redirect(url_for('budget.manage_budgets')) 