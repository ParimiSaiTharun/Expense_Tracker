from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import Category

bp = Blueprint('categories', __name__)

@bp.route('/categories', methods=['GET', 'POST'])
def manage_categories():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    if request.method == 'POST':
        name = request.form['name']
        if name:
            Category.create(name, user_id)
            flash('Category added!')
        return redirect(url_for('categories.manage_categories'))
    categories = Category.get_by_user(user_id)
    return render_template('categories.html', categories=categories)

@bp.route('/delete_category/<int:category_id>')
def delete_category(category_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    user_id = session['user_id']
    # Only allow delete if category belongs to user
    categories = Category.get_by_user(user_id)
    if any(cat['id'] == category_id for cat in categories):
        from flask import current_app
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "DELETE FROM categories WHERE id=%s AND user_id=%s"
            SaiTharun.execute(sql, (category_id, user_id))
            connection.commit()
        flash('Category deleted!')
    return redirect(url_for('categories.manage_categories')) 