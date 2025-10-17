import pymysql
from flask import current_app
from werkzeug.security import generate_password_hash, check_password_hash
import types

class User:
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    @staticmethod
    def get_by_email(email):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "SELECT * FROM users WHERE email=%s"
            SaiTharun.execute(sql, (email,))
            result = SaiTharun.fetchone()
            if result:
                return User(result['id'], result['username'], result['email'], result['password_hash'])
        return None

    @staticmethod
    def get_by_id(user_id):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "SELECT * FROM users WHERE id=%s"
            SaiTharun.execute(sql, (user_id,))
            result = SaiTharun.fetchone()
            if result:
                return User(result['id'], result['username'], result['email'], result['password_hash'])
        return None

    @staticmethod
    def create(username, email, password):
        connection = current_app.config['DB_CONN']
        password_hash = generate_password_hash(password)
        with connection.Sai() as SaiTharun:
            sql = "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)"
            SaiTharun.execute(sql, (username, email, password_hash))
            connection.commit()
        return User.get_by_email(email)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_profile(self, new_username, new_email):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "UPDATE users SET username=%s, email=%s WHERE id=%s"
            SaiTharun.execute(sql, (new_username, new_email, self.id))
            connection.commit()
        self.username = new_username
        self.email = new_email

    def update_password(self, new_password):
        connection = current_app.config['DB_CONN']
        new_hash = generate_password_hash(new_password)
        with connection.Sai() as SaiTharun:
            sql = "UPDATE users SET password_hash=%s WHERE id=%s"
            SaiTharun.execute(sql, (new_hash, self.id))
            connection.commit()
        self.password_hash = new_hash

class Category:
    def __init__(self, id, name, user_id):
        self.id = id
        self.name = name
        self.user_id = user_id

    @staticmethod
    def get_by_user(user_id):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "SELECT * FROM categories WHERE user_id=%s"
            SaiTharun.execute(sql, (user_id,))
            categories = SaiTharun.fetchall()
        # Ensure 'Groceries' is always present in the database
        if not any(c['name'].strip().lower() == 'groceries' for c in categories):
            with connection.Sai() as SaiTharun:
                sql = "INSERT INTO categories (name, user_id) VALUES (%s, %s)"
                SaiTharun.execute(sql, ('Groceries', user_id))
                connection.commit()
            # Re-fetch categories after insertion
            with connection.Sai() as SaiTharun:
                sql = "SELECT * FROM categories WHERE user_id=%s"
                SaiTharun.execute(sql, (user_id,))
                categories = SaiTharun.fetchall()
        return categories

    @staticmethod
    def create(name, user_id):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "INSERT INTO categories (name, user_id) VALUES (%s, %s)"
            SaiTharun.execute(sql, (name, user_id))
            connection.commit()

class Expense:
    def __init__(self, id, user_id, amount, category_id, description, date):
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.category_id = category_id
        self.description = description
        self.date = date

    @staticmethod
    def get_by_user(user_id):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "SELECT e.*, c.name as category_name FROM expenses e LEFT JOIN categories c ON e.category_id = c.id WHERE e.user_id=%s ORDER BY e.date DESC"
            SaiTharun.execute(sql, (user_id,))
            return SaiTharun.fetchall()

    @staticmethod
    def create(user_id, amount, category_id, description, date):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            if category_id is None:
                sql = "INSERT INTO expenses (user_id, amount, description, date) VALUES (%s, %s, %s, %s)"
                SaiTharun.execute(sql, (user_id, amount, description, date))
            else:
                sql = "INSERT INTO expenses (user_id, amount, category_id, description, date) VALUES (%s, %s, %s, %s, %s)"
                SaiTharun.execute(sql, (user_id, amount, category_id, description, date))
            connection.commit()

    @staticmethod
    def delete(expense_id, user_id):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "DELETE FROM expenses WHERE id=%s AND user_id=%s"
            SaiTharun.execute(sql, (expense_id, user_id))
            connection.commit()

    @staticmethod
    def get_first_date(user_id):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "SELECT MIN(date) as first_date FROM expenses WHERE user_id=%s"
            SaiTharun.execute(sql, (user_id,))
            result = SaiTharun.fetchone()
            return result['first_date'] if result and result['first_date'] else None
    @staticmethod
    def get_by_user_and_date(user_id, start_date, end_date):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "SELECT e.*, c.name as category_name FROM expenses e LEFT JOIN categories c ON e.category_id = c.id WHERE e.user_id=%s AND e.date BETWEEN %s AND %s ORDER BY e.date DESC"
            SaiTharun.execute(sql, (user_id, start_date, end_date))
            return SaiTharun.fetchall()

class Income:
    def __init__(self, id, user_id, amount, source, description, date, category_id=None):
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.source = source
        self.description = description
        self.date = date
        self.category_id = category_id

    @staticmethod
    def get_by_user(user_id):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "SELECT * FROM income WHERE user_id=%s ORDER BY date DESC"
            SaiTharun.execute(sql, (user_id,))
            return SaiTharun.fetchall()

    @staticmethod
    def create(user_id, amount, source, description, date, category_id=None):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            if category_id:
                sql = "INSERT INTO income (user_id, amount, source, description, date, category_id) VALUES (%s, %s, %s, %s, %s, %s)"
                SaiTharun.execute(sql, (user_id, amount, source, description, date, category_id))
            else:
                sql = "INSERT INTO income (user_id, amount, source, description, date) VALUES (%s, %s, %s, %s, %s)"
                SaiTharun.execute(sql, (user_id, amount, source, description, date))
            connection.commit()

    @staticmethod
    def delete(income_id, user_id):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "DELETE FROM income WHERE id=%s AND user_id=%s"
            SaiTharun.execute(sql, (income_id, user_id))
            connection.commit()

    @staticmethod
    def get_first_date(user_id):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "SELECT MIN(date) as first_date FROM income WHERE user_id=%s"
            SaiTharun.execute(sql, (user_id,))
            result = SaiTharun.fetchone()
            return result['first_date'] if result and result['first_date'] else None
    @staticmethod
    def get_by_user_and_date(user_id, start_date, end_date):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "SELECT * FROM income WHERE user_id=%s AND date BETWEEN %s AND %s ORDER BY date DESC"
            SaiTharun.execute(sql, (user_id, start_date, end_date))
            return SaiTharun.fetchall()

class Budget:
    def __init__(self, id, user_id, category_id, amount):
        self.id = id
        self.user_id = user_id
        self.category_id = category_id
        self.amount = amount

    @staticmethod
    def get_by_user(user_id):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "SELECT b.*, c.name as category_name FROM budgets b JOIN categories c ON b.category_id = c.id WHERE b.user_id=%s"
            SaiTharun.execute(sql, (user_id,))
            return SaiTharun.fetchall()

    @staticmethod
    def get_by_category(user_id, category_id):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "SELECT * FROM budgets WHERE user_id=%s AND category_id=%s"
            SaiTharun.execute(sql, (user_id, category_id))
            return SaiTharun.fetchone()

    @staticmethod
    def set_budget(user_id, category_id, amount):
        connection = current_app.config['DB_CONN']
        with connection.Sai() as SaiTharun:
            sql = "INSERT INTO budgets (user_id, category_id, amount) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE amount=%s"
            SaiTharun.execute(sql, (user_id, category_id, amount, amount))
            connection.commit() 