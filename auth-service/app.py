from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import os
from datetime import datetime, timedelta
import secrets
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

load_dotenv('../.env')

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 3306)),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        database=os.getenv('DB_NAME', 'microservices_app_db')
    )

@app.route('/')
def home():
    return jsonify({
        'service': 'auth-service',
        'status': 'running',
        'timestamp': datetime.now().isoformat(),
        'endpoints': ['/health', '/users', '/api/auth/login', '/api/auth/register', '/api/auth/users']
    })

@app.route('/users', methods=['GET'])
def get_users_simple():
    """Simple endpoint for dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, created_at FROM auth_users")
        users = cursor.fetchall()
        return jsonify({'users': users}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'auth-service'}), 200

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM auth_users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if user:
            # Generate token
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)
            
            cursor.execute(
                "INSERT INTO auth_sessions (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user['id'], token, expires_at)
            )
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'token': token,
                'user': {'id': user['id'], 'username': user['username'], 'email': user['email']}
            }), 200
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO auth_users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, f"hashed_{password}")
        )
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'username': username
        }), 201
    except mysql.connector.IntegrityError:
        return jsonify({'success': False, 'message': 'Username or email already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/auth/verify', methods=['POST'])
def verify_token():
    data = request.json
    token = data.get('token')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT s.*, u.username, u.email FROM auth_sessions s JOIN auth_users u ON s.user_id = u.id WHERE s.token = %s AND s.expires_at > NOW()",
            (token,)
        )
        session = cursor.fetchone()
        
        if session:
            return jsonify({
                'valid': True,
                'user': {'id': session['user_id'], 'username': session['username'], 'email': session['email']}
            }), 200
        else:
            return jsonify({'valid': False, 'message': 'Invalid or expired token'}), 401
    except Exception as e:
        return jsonify({'valid': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/auth/users', methods=['GET'])
def get_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, created_at FROM auth_users")
        users = cursor.fetchall()
        return jsonify({'success': True, 'users': users}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)