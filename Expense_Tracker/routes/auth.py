from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from models import User

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']
        if password != confirm:
            flash('Passwords do not match.')
            return render_template('register.html')
        if User.get_by_email(email):
            flash('Email already registered.')
            return render_template('register.html')
        if len(password) < 4:
            flash('Password must be at least 4 characters long.', 'danger')
            return render_template('register.html')
        if not username.isalpha():
            flash('Username must contain only letters (no numbers or special characters).', 'danger')
            return render_template('register.html')
        User.create(username, email, password)
        flash('Registration successful! Please log in.')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.get_by_email(email)
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['username'] = user.username
            return redirect(url_for('home'))
        flash('Invalid email or password.')
    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.')
    return redirect(url_for('home')) 