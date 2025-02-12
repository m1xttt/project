from flask import Flask, render_template, request, redirect, url_for, flash, session,  jsonify
import sqlite3
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
import random
import threading
import time
import qrcode
from io import BytesIO
from smtplib import SMTP
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import hashlib
#from extensions import csrf

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
#def create_app():
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)



random_numbers = []
#    csrf.init_app(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static/uploads')
#    register_routes(app)

def generate_random_numbers():
    global random_numbers
    while True:
        random_numbers = [random.randint(1, 9) for _ in range(11)]
        time.sleep(600)

def send_email_with_qr(recipient_email, qr_data):
    try:
        # Создание QR-кода
        qr = qrcode.make(qr_data)
        qr_buffer = BytesIO()
        qr.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        # Настройки SMTP
        sender_email = "m1xt.offical@gmail.com"  # Замените на ваш email
        sender_password = "mamv nojo cnyo byjy"       # Замените на ваш пароль приложения
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        # Формирование письма
        subject = "Ваш QR-код бронирования"
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText("Спасибо за бронирование! Ваш QR-код приложен.", "plain"))

        # Прикрепляем QR-код
        attachment = MIMEBase("application", "octet-stream")
        attachment.set_payload(qr_buffer.read())
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", "attachment; filename=qr_code.png")
        msg.attach(attachment)

        # Отправка письма
        with SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print(f"Письмо успешно отправлено на {recipient_email}")
    except Exception as e:
        print(f"Ошибка отправки письма: {e}")
        raise

#    return app
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            remember_token TEXT,
            avatar TEXT
        )
    ''')
    conn.commit()
    conn.close()

def house_db():
    conn = sqlite3.connect('houses.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS houses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


# Функция для добавления хэша в таблицу
#def insert_hash(conn, hash_value):
    #sql_insert_hash = """ INSERT INTO houses (code_hash) VALUES (?); """
    #cursor = conn.cursor()
    #cursor.execute(sql_insert_hash, (hash_value,))
    #conn.commit()
    #return cursor.lastrowid


# Функция для генерации хэша из строки
def generate_hash(input_string):
    return hashlib.sha256(input_string.encode()).hexdigest()

def view_users():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    rows = cursor.fetchall()
    conn.close()

    print("Содержимое таблицы 'users':")
    for row in rows:
        print(row)

#def view_users_code():
    #conn = sqlite3.connect('houses.db')
    #cursor = conn.cursor()
    #cursor.execute('SELECT * FROM houses')
    #rows = cursor.fetchall()
    #conn.close()

    print("Содержимое таблицы 'houses':")
    for row in rows:
        print(row)

#def register_routes(app):
    @app.route("/")
    @app.route("/main")
    def main():
        return render_template("qr-code.html")

    @app.route("/testpage")
    def testpage():
        return render_template("test.html")

    @app.route("/Nightview-Residence")
    def firsthouse():
        return render_template("firsthouse.html")

    @app.route("/Skyline-Retreat")
    def secondhouse():
        return render_template("secondhouse.html")

    @app.route("/Starlit-Villa")
    def thirdhouse():
        return render_template("thirdhouse.html")

    @app.route("/contacts")
    def contacts():
        return render_template("contacts.html")

    @app.route('/upload_avatar', methods=['POST'])
    def upload_avatar():
        if 'user_id' not in session:
            flash('Вы должны войти в аккаунт', 'error')
            return redirect(url_for('login'))

        file = request.files.get('avatar')
        if not file or file.filename == '':
            flash('Файл не выбран', 'error')
            return redirect(url_for('user_dashboard'))

        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            user_id = session['user_id']

            # Generate unique filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"user_{user_id}_{filename}")

            # Save the file
            file.save(filepath)

            # Update user's avatar in the database
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            # Retrieve the current avatar
            cursor.execute('SELECT avatar FROM users WHERE id = ?', (user_id,))
            old_avatar = cursor.fetchone()[0]

            # Update the avatar path
            cursor.execute('UPDATE users SET avatar = ? WHERE id = ?', (filepath, user_id))
            conn.commit()
            conn.close()

            # Remove old avatar file if it exists
            if old_avatar and os.path.exists(old_avatar):
                os.remove(old_avatar)

            flash('Аватар успешно загружен!', 'success')
            return redirect(url_for('user_dashboard'))

        flash('Недопустимый формат файла', 'error')
        return redirect(url_for('user_dashboard'))

    @app.route("/userpage")
    def user_dashboard():
        if 'user_id' not in session:
            flash('Вы должны войти в аккаунт', 'error')
            return redirect(url_for('login'))

        # Fetch user data from the database
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()

        if not user:
            flash('Ошибка: Пользователь не найден', 'error')
            return redirect(url_for('login'))

        # Render the dashboard with user-specific data
        return render_template('user.html', name=user[1], email=user[2], avatar=user[5])

    @app.route("/login", methods=['POST', 'GET'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            # Check user credentials
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user[3], password):
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                flash('Вы успешно вошли в аккаунт', 'success')
                return redirect(url_for('user_dashboard'))
            else:
                flash('Неверный email или пароль', 'error')

        return render_template('login.html')

    @app.route("/register", methods=['POST', 'GET'])
    def register():
        if request.method == 'POST':
            name = request.form.get('name')
            email = request.form.get('email')
            password1 = request.form.get('password1')
            password2 = request.form.get('password2')

            if password1 != password2:
                flash('Пароли не совпадают', 'error')
                return redirect(url_for('register'))

            hashed_password = generate_password_hash(password1)

            try:
                conn = sqlite3.connect('users.db')
                cursor = conn.cursor()
                cursor.execute('INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                               (name, email, hashed_password))
                conn.commit()
                conn.close()
                flash('Вы успешно зарегистрировались', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Пользователь с таким email уже существует', 'error')
                return redirect(url_for('register'))

        return render_template('register.html')

    @app.route("/logout")
    def logout():
        session.clear()
        flash('Вы успешно вышли из аккаунта', 'success')
        return redirect(url_for('main'))

    @app.route("/newpassword", methods=['POST', 'GET'])
    def newpassword():
        return render_template("newpassword.html")

    @app.route("/rent")
    def rent():
        return render_template("rent.html")

    @app.route("/aboutproject")
    def aboutproject():
        return render_template("aboutproject.html")

    @app.route("/reservationNightview-Residence", methods=["POST", "GET"])
    def reservation_nightview():
        if request.method == "POST":
            # Проверка авторизации
            user_id = session.get("user_id")
            if not user_id:
                flash("Пожалуйста, войдите в систему для бронирования.", "error")
                return redirect(url_for("login"))

            # Получение email пользователя из базы
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                flash("Пользователь не найден.", "error")
                return redirect(url_for("login"))

            user_email = user[0]
            qr_data = "-".join(map(str, random_numbers))  # Формируем данные QR-кода

            # Отправка QR-кода на email
            try:
                send_email_with_qr(user_email, qr_data)
                flash("Бронирование успешно! QR-код отправлен на ваш email.", "success")
            except Exception as e:
                flash(f"Ошибка отправки QR-кода: {e}", "error")

            return redirect(url_for("main"))

        return render_template("firsthousereservation.html")

    @app.route("/reservationSkyline-Retreat", methods=["POST", "GET"])
    def reservation_skyline():
        if request.method == "POST":
            # Проверка авторизации
            user_id = session.get("user_id")
            if not user_id:
                flash("Пожалуйста, войдите в систему для бронирования.", "error")
                return redirect(url_for("login"))

            # Получение email пользователя из базы
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                flash("Пользователь не найден.", "error")
                return redirect(url_for("login"))

            user_email = user[0]
            qr_data = "-".join(map(str, random_numbers))  # Формируем данные QR-кода

            # Отправка QR-кода на email
            try:
                send_email_with_qr(user_email, qr_data)
                flash("Бронирование успешно! QR-код отправлен на ваш email.", "success")
            except Exception as e:
                flash(f"Ошибка отправки QR-кода: {e}", "error")

            return redirect(url_for("main"))

        return render_template("secondhousereservation.html")

    @app.route("/reservationStarlit-Villa", methods=["POST", "GET"])
    def reservation_starlit():
        if request.method == "POST":
            # Проверка авторизации
            user_id = session.get("user_id")
            if not user_id:
                flash("Пожалуйста, войдите в систему для бронирования.", "error")
                return redirect(url_for("login"))

            # Получение email пользователя из базы
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                flash("Пользователь не найден.", "error")
                return redirect(url_for("login"))

            user_email = user[0]
            qr_data = "-".join(map(str, random_numbers))  # Формируем данные QR-кода

            # Отправка QR-кода на email
            try:
                send_email_with_qr(user_email, qr_data)
                flash("Бронирование успешно! QR-код отправлен на ваш email.", "success")
            except Exception as e:
                flash(f"Ошибка отправки QR-кода: {e}", "error")

            return redirect(url_for("main"))

        return render_template("thirdhousereservation.html")

    @app.route("/user")
    def userpage():
        return render_template("user.html")

    @app.route("/test")
    def test():
        return render_template("qr-codetest.html")

    @app.route('/get_numbers', methods=['GET'])
    def get_numbers():
        return jsonify(random_numbers)

    @app.route("/view_db")
    def view_db():
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users')
        rows = cursor.fetchall()
        conn.close()

        return "<br>".join([str(row) for row in rows])


if __name__ == "__main__":
    threading.Thread(target=generate_random_numbers, daemon=True).start()
    init_db()
    view_users()
    #view_users_code()
#    app = create_app()
    app.run(debug = True, host = "0.0.0.0", port = 50211)
