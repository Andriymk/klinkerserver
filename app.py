import hashlib
import hmac
import time
from flask import Flask, request, jsonify, redirect
import sqlite3

app = Flask(__name__)

# Ініціалізація бази даних
def init_db():
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            score INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Підключення до бази даних
def get_db_connection():
    conn = sqlite3.connect('game.db')
    return conn

# Функція для перевірки автентичності даних, отриманих від Telegram
def check_auth(data, token):
    check_hash = data.pop('hash')
    sorted_data = sorted(data.items(), key=lambda x: x[0])
    data_check_string = "\n".join(["{}={}".format(k, v) for k, v in sorted_data])
    secret_key = hmac.new(token.encode(), data_check_string.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(secret_key, check_hash)

# Обробка автентифікації користувача
@app.route('/auth', methods=['GET'])
def auth():
    data = request.args.to_dict()
    auth_date = int(data.get('auth_date', 0))
    if time.time() - auth_date > 86400:  # 24 години
        return jsonify({"error": "Authentication expired"}), 403
    
    token = '7024964067:AAEYZfeYp9Q83y4o3hqzSQBhs6elYJXHAeY'  # Вставте токен вашого бота тут

    if not check_auth(data, token):
        return jsonify({"error": "Invalid authentication"}), 403

    user_id = data['id']
    username = data['username']
    first_name = data.get('first_name', '')
    last_name = data.get('last_name', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, first_name, last_name))
    conn.commit()
    conn.close()

    # Перенаправлення користувача до гри
    return redirect(f"http://localhost:5000/index.html?user_id={user_id}&username={username}")

# Оновлення очок користувача
@app.route('/update_score', methods=['POST'])
def update_score():
    data = request.get_json()
    user_id = data['user_id']
    score = data['score']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET score = ?
        WHERE user_id = ?
    ''', (score, user_id))
    conn.commit()
    conn.close()

    return jsonify({"status": "success"})

# Запуск сервера
if __name__ == '__main__':
    app.run()
