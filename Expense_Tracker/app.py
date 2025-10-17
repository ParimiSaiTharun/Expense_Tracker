import os
from flask import Flask, render_template, session, redirect, url_for, request, flash
from dotenv import load_dotenv
import pymysql
from routes.auth import bp as auth_bp
from routes.transactions import bp as transactions_bp
from routes.categories import bp as categories_bp
from routes.ai import bp as ai_bp
from routes.dashboard import bp as dashboard_bp
from routes.budget import bp as budget_bp
from routes.export import bp as export_bp
from routes.report import bp as report_bp
from routes.plan import bp as plan_bp
from models import User
import types
import re

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# MySQL connection
connection = pymysql.connect(
    host=os.getenv('MYSQL_HOST'),
    user=os.getenv('MYSQL_USER'),
    password=os.getenv('MYSQL_PASSWORD'),
    db=os.getenv('MYSQL_DB'),
    cursorclass=pymysql.cursors.DictCursor
)

connection.Sai = types.MethodType(lambda self: self.cursor(), connection)

app.config['DB_CONN'] = connection
app.register_blueprint(auth_bp)
app.register_blueprint(transactions_bp)
app.register_blueprint(categories_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(budget_bp)
app.register_blueprint(export_bp)
app.register_blueprint(report_bp)
app.register_blueprint(plan_bp)

def inr_format(value):
    try:
        value = float(value)
        # Indian comma formatting
        s = f"{value:,.2f}"
        x = s.split('.')
        int_part = x[0]
        dec_part = x[1] if len(x) > 1 else ''
        if len(int_part) > 3:
            int_part = int_part[:-3].replace(',', '')[::-1]
            int_part = ','.join([int_part[i:i+2] for i in range(0, len(int_part), 2)])[::-1] + ',' + s[-6:-3]
        return f"₹{int_part}.{dec_part}"
    except Exception:
        return f"₹{value}"
app.jinja_env.filters['inr'] = inr_format

def inr_text(text):
    # Find all ₹-prefixed numbers and reformat them
    def repl(match):
        num = match.group(1).replace(',', '')
        try:
            return inr_format(float(num))
        except Exception:
            return match.group(0)
    return re.sub(r'₹([0-9][0-9,]*\.?[0-9]*)', repl, text)
app.jinja_env.filters['inr_text'] = inr_text

def format_ddmmyyyy(value):
    try:
        from datetime import datetime
        if isinstance(value, str):
            value = datetime.strptime(value, '%Y-%m-%d')
        return value.strftime('%d-%m-%Y')
    except Exception:
        return value
app.jinja_env.filters['ddmmyyyy'] = format_ddmmyyyy

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/profile', methods=['GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user = User.get_by_id(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user = User.get_by_id(session['user_id'])
    new_username = request.form['username']
    if not new_username.isalpha():
        flash('Username must contain only letters (no numbers or special characters).', 'danger')
        return redirect(url_for('profile'))
    new_email = request.form['email']
    # Only update if changed
    if new_username != user.username or new_email != user.email:
        try:
            user.update_profile(new_username, new_email)
            session['username'] = new_username
            flash('Profile updated!', 'success')
        except Exception as e:
            flash(f'Error updating profile: {e}', 'danger')
    else:
        flash('No changes made.', 'info')
    return redirect(url_for('profile'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user = User.get_by_id(session['user_id'])
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    confirm_password = request.form['confirm_password']
    if not user.check_password(current_password):
        flash('Current password is incorrect.', 'danger')
        return redirect(url_for('profile'))
    if new_password != confirm_password:
        flash('New passwords do not match.', 'danger')
        return redirect(url_for('profile'))
    try:
        user.update_password(new_password)
        flash('Password changed successfully!', 'success')
    except Exception as e:
        flash(f'Error changing password: {e}', 'danger')
    return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True) 