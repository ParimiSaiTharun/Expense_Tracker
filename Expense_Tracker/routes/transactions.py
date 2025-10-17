from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import Expense, Income, Category
from datetime import date

bp = Blueprint('transactions', __name__)

@bp.route('/add_expense', methods=['GET', 'POST'])
def add_expense():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    categories = Category.get_by_user(user_id)
    if request.method == 'POST':
        amount = request.form['amount']
        category_id = request.form['category_id']
        new_category = request.form.get('new_category')
        description = request.form['description']
        expense_date = request.form['date'] or date.today().isoformat()
        if category_id == '__new__' and new_category:
            Category.create(new_category, user_id)
            # Get the new category id
            categories = Category.get_by_user(user_id)
            for cat in categories:
                if cat['name'].lower() == new_category.lower():
                    category_id = cat['id']
                    break
        Expense.create(user_id, amount, category_id, description, expense_date)
        flash('Expense added!')
        return redirect(url_for('transactions.view_expenses'))
    return render_template('add_expense.html', categories=categories)

@bp.route('/add_income', methods=['GET', 'POST'])
def add_income():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    if request.method == 'POST':
        amount = request.form['amount']
        source = request.form['source']
        description = request.form['description']
        income_date = request.form['date'] or date.today().isoformat()
        Income.create(user_id, amount, source, description, income_date)
        flash('Income added!')
        return redirect(url_for('transactions.view_income'))
    return render_template('add_income.html')

@bp.route('/expenses')
def view_expenses():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    expenses = Expense.get_by_user(user_id)
    return render_template('expenses.html', expenses=expenses)

@bp.route('/income')
def view_income():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    income = Income.get_by_user(user_id)
    return render_template('income.html', income=income)

@bp.route('/delete_expense/<int:expense_id>')
def delete_expense(expense_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    Expense.delete(expense_id, user_id)
    flash('Expense deleted!')
    return redirect(url_for('transactions.view_expenses'))

@bp.route('/delete_income/<int:income_id>')
def delete_income(income_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    Income.delete(income_id, user_id)
    flash('Income deleted!')
    return redirect(url_for('transactions.view_income')) 