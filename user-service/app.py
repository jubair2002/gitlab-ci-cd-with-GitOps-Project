from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import os

app = Flask(__name__)
CORS(app)

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
        'service': 'user-service',
        'status': 'running',
        'endpoints': ['/health', '/profiles', '/api/user/profiles', '/api/user/profile']
    })

@app.route('/profiles', methods=['GET'])
def get_profiles_simple():
    """Simple endpoint for dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_profiles")
        profiles = cursor.fetchall()
        return jsonify({'profiles': profiles}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'user-service'}), 200

@app.route('/api/user/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
        profile = cursor.fetchone()
        
        if profile:
            return jsonify({'success': True, 'profile': profile}), 200
        else:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/user/profile', methods=['POST'])
def create_profile():
    data = request.json
    user_id = data.get('user_id')
    full_name = data.get('full_name')
    phone = data.get('phone')
    address = data.get('address')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_profiles (user_id, full_name, phone, address) VALUES (%s, %s, %s, %s)",
            (user_id, full_name, phone, address)
        )
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile created successfully',
            'profile_id': cursor.lastrowid
        }), 201
    except mysql.connector.IntegrityError:
        return jsonify({'success': False, 'message': 'Profile already exists for this user'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/user/profile/<int:user_id>', methods=['PUT'])
def update_profile(user_id):
    data = request.json
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        update_fields = []
        values = []
        
        if 'full_name' in data:
            update_fields.append("full_name = %s")
            values.append(data['full_name'])
        if 'phone' in data:
            update_fields.append("phone = %s")
            values.append(data['phone'])
        if 'address' in data:
            update_fields.append("address = %s")
            values.append(data['address'])
        
        if not update_fields:
            return jsonify({'success': False, 'message': 'No fields to update'}), 400
        
        values.append(user_id)
        query = f"UPDATE user_profiles SET {', '.join(update_fields)} WHERE user_id = %s"
        
        cursor.execute(query, values)
        conn.commit()
        
        if cursor.rowcount > 0:
            return jsonify({'success': True, 'message': 'Profile updated successfully'}), 200
        else:
            return jsonify({'success': False, 'message': 'Profile not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/user/profiles', methods=['GET'])
def get_all_profiles():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM user_profiles")
        profiles = cursor.fetchall()
        return jsonify({'success': True, 'profiles': profiles}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)