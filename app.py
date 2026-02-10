from flask import Flask, render_template, request, redirect, url_for, flash, session
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
import json
import numpy as np
from PIL import Image

try:
    import cv2
    FACE_RECOGNITION_AVAILABLE = True
    try:   
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if face_cascade.empty():
            raise FileNotFoundError("Каскад не найден")
    except Exception as e:
        print(f"Предупреждение: не удалось загрузить каскад для обнаружения лиц: {e}")
        FACE_RECOGNITION_AVAILABLE = False
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Предупреждение: библиотека opencv-python не установлена. Распознавание лиц будет недоступно.")
    print("Установите её командой: pip install opencv-python")

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

UPLOAD_FOLDER = 'static/uploads/face_photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)



random_numbers = []

def generate_random_numbers():
    global random_numbers
    while True:
        random_numbers = [random.randint(1, 9) for _ in range(11)]
        time.sleep(600)

def send_email_with_qr(recipient_email, qr_data):
    try:
        qr = qrcode.make(qr_data)
        qr_buffer = BytesIO()
        qr.save(qr_buffer, format="PNG")
        qr_buffer.seek(0)

        sender_email = "m1xt.offical@gmail.com"
        sender_password = "mamv nojo cnyo byjy"
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        subject = "Ваш QR-код бронирования"
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText("Спасибо за бронирование! Ваш QR-код приложен.", "plain"))

        attachment = MIMEBase("application", "octet-stream")
        attachment.set_payload(qr_buffer.read())
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", "attachment; filename=qr_code.png")
        msg.attach(attachment)

        with SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            print(f"Письмо успешно отправлено на {recipient_email}")
    except Exception as e:
        print(f"Ошибка отправки письма: {e}")
        raise

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_face_features(image_path):
    if not FACE_RECOGNITION_AVAILABLE:
        return None, "Библиотека opencv-python не установлена. Установите её командой: pip install opencv-python"
    try:    
        image = cv2.imread(image_path)
        if image is None:
            return None, "Не удалось загрузить изображение"
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        faces = face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        
        if len(faces) == 0:
            return None, "Лицо не найдено на изображении"
        
        if len(faces) > 1:
            return None, "На изображении найдено несколько лиц. Пожалуйста, загрузите фото с одним лицом"
        
        (x, y, w, h) = faces[0]
        
        face_roi = gray[y:y+h, x:x+w]
        
        face_resized = cv2.resize(face_roi, (64, 64))
        
        hog = cv2.HOGDescriptor((64, 64), (16, 16), (8, 8), (8, 8), 9)
        hog_features = hog.compute(face_resized)
        
        if hog_features is None or len(hog_features) == 0:
            features = []
            features.append(np.mean(face_resized))
            features.append(np.std(face_resized))
            hist = cv2.calcHist([face_resized], [0], None, [16], [0, 256])
            features.extend(hist.flatten().tolist())
            features.extend([w/h, x/image.shape[1], y/image.shape[0]])
            feature_array = np.array(features, dtype=np.float32)
        else:
            feature_array = hog_features.flatten().astype(np.float32)
        
        return feature_array.tobytes(), None
            
    except Exception as e:
        return None, f"Ошибка обработки изображения: {str(e)}"

def process_face_encoding(image_path):
    return extract_face_features(image_path)

def save_face_encoding(user_id, face_encoding_bytes):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO face_encodings (user_id, encoding) 
            VALUES (?, ?)
        ''', (user_id, face_encoding_bytes))
        conn.commit()
        encoding_id = cursor.lastrowid
        return encoding_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_user_face_encodings(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, created_at 
            FROM face_encodings 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        encodings = cursor.fetchall()
        return encodings
    finally:
        conn.close()

def delete_face_encoding(encoding_id, user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id FROM face_encodings WHERE id = ? AND user_id = ?', (encoding_id, user_id))
        if not cursor.fetchone():
            return False, "Энкодинг не найден или не принадлежит вам"
        
        cursor.execute('DELETE FROM face_encodings WHERE id = ? AND user_id = ?', (encoding_id, user_id))
        conn.commit()
        return True, "Фотография успешно удалена"
    except Exception as e:
        conn.rollback()
        return False, f"Ошибка при удалении: {str(e)}"
    finally:
        conn.close()

def verify_face(image_path, user_id):
    if not FACE_RECOGNITION_AVAILABLE:
        return False, "Библиотека opencv-python не установлена. Установите её командой: pip install opencv-python"
    try:
        unknown_features_bytes, error = extract_face_features(image_path)
        if unknown_features_bytes is None:
            return False, error
        
        unknown_features = np.frombuffer(unknown_features_bytes, dtype=np.float32)
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute('SELECT encoding FROM face_encodings WHERE user_id = ?', (user_id,))
        saved_encodings = cursor.fetchall()
        conn.close()
        
        if not saved_encodings:
            return False, "У пользователя нет сохраненных фотографий для распознавания"
        
        for (saved_encoding_bytes,) in saved_encodings:
            saved_features = np.frombuffer(saved_encoding_bytes, dtype=np.float32)
            
            if len(saved_features) != len(unknown_features):
                continue
            
            distance = np.linalg.norm(saved_features - unknown_features)
            
            threshold = 0.25
            
            if distance < threshold:
                return True, "Лицо распознано"
        
        return False, "Лицо не распознано"
    except Exception as e:
        return False, f"Ошибка распознавания: {str(e)}"

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_encodings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            encoding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

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

    @app.route("/")
    @app.route("/main")
    def main():
        return render_template("main.html")

    @app.route("/testpage")
    def testpage():
        return render_template("test.html")

    @app.route("/Nightview-Residence")
    def firsthouse():
        return render_template("first.html")

    @app.route("/Skyline-Retreat")
    def secondhouse():
        return render_template("second.html")

    @app.route("/Starlit-Villa")
    def thirdhouse():
        return render_template("third.html")

    @app.route("/contacts")
    def contacts():
        return render_template("contacts.html")


    @app.route("/login", methods=['POST', 'GET'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')

            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user[3], password):
                session['user_id'] = user[0]
                session['user_name'] = user[1]
                flash('Вы успешно вошли в аккаунт', 'success')
                return redirect(url_for('main'))
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
        return render_template("reserve.html")

    @app.route("/aboutproject")
    def aboutproject():
        return render_template("about.html")

    @app.route("/reservationNightview-Residence", methods=["POST", "GET"])
    def reservation_nightview():
        if request.method == "POST":
            user_id = session.get("user_id")
            if not user_id:
                flash("Пожалуйста, войдите в систему для бронирования.", "error")
                return redirect(url_for("login"))

            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                flash("Пользователь не найден.", "error")
                return redirect(url_for("login"))

            enable_face_recognition = request.form.get('enable_face_recognition') == 'on'
            if enable_face_recognition:
                if 'face_photos' not in request.files:
                    flash("Пожалуйста, загрузите фотографии для распознавания лица.", "error")
                    return redirect(request.url)
                
                files = request.files.getlist('face_photos')
                if not files or all(f.filename == '' for f in files):
                    flash("Пожалуйста, выберите хотя бы одну фотографию.", "error")
                    return redirect(request.url)
                
                processed_count = 0
                for file in files:
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(f"{user_id}_{secrets.token_hex(8)}_{file.filename}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        
                        face_encoding, error = process_face_encoding(filepath)
                        if face_encoding:
                            try:
                                save_face_encoding(user_id, face_encoding)
                                processed_count += 1
                            except Exception as e:
                                flash(f"Ошибка сохранения энкодинга: {e}", "error")
                        else:
                            flash(f"Ошибка обработки {file.filename}: {error}", "error")
                        
                        try:
                            os.remove(filepath)
                        except:
                            pass
                
                if processed_count > 0:
                    flash(f"Успешно обработано {processed_count} фотографий для распознавания лица.", "success")

            user_email = user[0]
            qr_data = "-".join(map(str, random_numbers))

            try:
                send_email_with_qr(user_email, qr_data)
                flash("Бронирование успешно! QR-код отправлен на ваш email.", "success")
            except Exception as e:
                flash(f"Ошибка отправки QR-кода: {e}", "error")

            return redirect(url_for("main"))

        return render_template("firstreserve.html")

    @app.route("/reservationSkyline-Retreat", methods=["POST", "GET"])
    def reservation_skyline():
        if request.method == "POST":
            user_id = session.get("user_id")
            if not user_id:
                flash("Пожалуйста, войдите в систему для бронирования.", "error")
                return redirect(url_for("login"))

            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                flash("Пользователь не найден.", "error")
                return redirect(url_for("login"))

            enable_face_recognition = request.form.get('enable_face_recognition') == 'on'
            if enable_face_recognition:
                if 'face_photos' not in request.files:
                    flash("Пожалуйста, загрузите фотографии для распознавания лица.", "error")
                    return redirect(request.url)
                
                files = request.files.getlist('face_photos')
                if not files or all(f.filename == '' for f in files):
                    flash("Пожалуйста, выберите хотя бы одну фотографию.", "error")
                    return redirect(request.url)
                
                processed_count = 0
                for file in files:
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(f"{user_id}_{secrets.token_hex(8)}_{file.filename}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        
                        face_encoding, error = process_face_encoding(filepath)
                        if face_encoding:
                            try:
                                save_face_encoding(user_id, face_encoding)
                                processed_count += 1
                            except Exception as e:
                                flash(f"Ошибка сохранения энкодинга: {e}", "error")
                        else:
                            flash(f"Ошибка обработки {file.filename}: {error}", "error")
                        
                        try:
                            os.remove(filepath)
                        except:
                            pass
                
                if processed_count > 0:
                    flash(f"Успешно обработано {processed_count} фотографий для распознавания лица.", "success")

            user_email = user[0]
            qr_data = "-".join(map(str, random_numbers))

            try:
                send_email_with_qr(user_email, qr_data)
                flash("Бронирование успешно! QR-код отправлен на ваш email.", "success")
            except Exception as e:
                flash(f"Ошибка отправки QR-кода: {e}", "error")

            return redirect(url_for("main"))

        return render_template("secondreserve.html")

    @app.route("/reservationStarlit-Villa", methods=["POST", "GET"])
    def reservation_starlit():
        if request.method == "POST":
            user_id = session.get("user_id")
            if not user_id:
                flash("Пожалуйста, войдите в систему для бронирования.", "error")
                return redirect(url_for("login"))

            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
            user = cursor.fetchone()
            conn.close()

            if not user:
                flash("Пользователь не найден.", "error")
                return redirect(url_for("login"))

            enable_face_recognition = request.form.get('enable_face_recognition') == 'on'
            if enable_face_recognition:
                if 'face_photos' not in request.files:
                    flash("Пожалуйста, загрузите фотографии для распознавания лица.", "error")
                    return redirect(request.url)
                
                files = request.files.getlist('face_photos')
                if not files or all(f.filename == '' for f in files):
                    flash("Пожалуйста, выберите хотя бы одну фотографию.", "error")
                    return redirect(request.url)
                
                processed_count = 0
                for file in files:
                    if file and file.filename != '' and allowed_file(file.filename):
                        filename = secure_filename(f"{user_id}_{secrets.token_hex(8)}_{file.filename}")
                        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(filepath)
                        
                        face_encoding, error = process_face_encoding(filepath)
                        if face_encoding:
                            try:
                                save_face_encoding(user_id, face_encoding)
                                processed_count += 1
                            except Exception as e:
                                flash(f"Ошибка сохранения энкодинга: {e}", "error")
                        else:
                            flash(f"Ошибка обработки {file.filename}: {error}", "error")
                        
                        try:
                            os.remove(filepath)
                        except:
                            pass
                
                if processed_count > 0:
                    flash(f"Успешно обработано {processed_count} фотографий для распознавания лица.", "success")

            user_email = user[0]
            qr_data = "-".join(map(str, random_numbers))

            try:
                send_email_with_qr(user_email, qr_data)
                flash("Бронирование успешно! QR-код отправлен на ваш email.", "success")
            except Exception as e:
                flash(f"Ошибка отправки QR-кода: {e}", "error")

            return redirect(url_for("main"))

        return render_template("thirdreserve.html")

    @app.route('/get_numbers', methods=['GET'])
    def get_numbers():
        return json.dumps(random_numbers, separators=(',', ':')), 200, {'Content-Type': 'application/json'}

    @app.route("/face-photos", methods=['GET'])
    def face_photos():
        user_id = session.get("user_id")
        if not user_id:
            flash("Пожалуйста, войдите в систему.", "error")
            return redirect(url_for("login"))
        
        encodings = get_user_face_encodings(user_id)
        
        return render_template("face_photos.html", encodings=encodings)

    @app.route("/delete-face-photo/<int:encoding_id>", methods=['POST'])
    def delete_face_photo(encoding_id):
        user_id = session.get("user_id")
        if not user_id:
            flash("Пожалуйста, войдите в систему.", "error")
            return redirect(url_for("login"))
        
        success, message = delete_face_encoding(encoding_id, user_id)
        if success:
            flash(message, "success")
        else:
            flash(message, "error")
        
        return redirect(url_for("face_photos"))


if __name__ == "__main__":
    threading.Thread(target=generate_random_numbers, daemon=True).start()
    init_db()
    view_users()
    app.run(debug = True, host = "0.0.0.0", port = 8080)
