from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import os
import secrets
from dotenv import load_dotenv

# Load .env from project root (two levels up from src/payment-service/)
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

app = Flask(__name__)
CORS(app)

def get_db_connection():
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    
    # Check if required variables exist (password can be empty string)
    if not db_host or not db_port or not db_user or db_password is None or not db_name:
        raise ValueError("Missing required database environment variables: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME")
    
    return mysql.connector.connect(
        host=db_host,
        port=int(db_port),
        user=db_user,
        password=db_password,
        database=db_name,
        connection_timeout=5,
        autocommit=False
    )

@app.route('/')
def home():
    return jsonify({
        'service': 'payment-service',
        'status': 'running',
        'endpoints': ['/health', '/payments', '/api/payment/payments', '/api/payment/charge']
    })

@app.route('/payments', methods=['GET'])
def get_payments_simple():
    """Simple endpoint for dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM payments ORDER BY created_at DESC")
        payments = cursor.fetchall()
        return jsonify({'payments': payments}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'payment-service'}), 200

@app.route('/api/payment/payments', methods=['GET'])
def get_payments():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM payments ORDER BY created_at DESC")
        payments = cursor.fetchall()
        return jsonify({'payments': payments}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/payment/payments/<int:payment_id>', methods=['GET'])
def get_payment(payment_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
        payment = cursor.fetchone()
        
        if payment:
            return jsonify({'success': True, 'payment': payment}), 200
        else:
            return jsonify({'success': False, 'message': 'Payment not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/payment/payments/user/<int:user_id>', methods=['GET'])
def get_user_payments(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM payments WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        payments = cursor.fetchall()
        return jsonify({'success': True, 'payments': payments}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/payment/charge', methods=['POST'])
def create_payment():
    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount')
    currency = data.get('currency', 'USD')  # Request parameter default
    payment_method = data.get('payment_method', 'credit_card')  # Request parameter default
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate unique transaction ID
        transaction_id = f"TXN{secrets.token_hex(8).upper()}"
        
        cursor.execute(
            """INSERT INTO payments (user_id, amount, currency, status, payment_method, transaction_id) 
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (user_id, amount, currency, 'pending', payment_method, transaction_id)
        )
        conn.commit()
        payment_id = cursor.lastrowid
        
        # Simulate payment processing
        import random
        success = random.choice([True, True, True, False])  # 75% success rate
        
        status = 'completed' if success else 'failed'
        cursor.execute("UPDATE payments SET status = %s WHERE id = %s", (status, payment_id))
        conn.commit()
        
        return jsonify({
            'success': success,
            'message': f'Payment {status}',
            'payment_id': payment_id,
            'transaction_id': transaction_id,
            'status': status
        }), 201 if success else 402
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/payment/refund/<int:payment_id>', methods=['POST'])
def refund_payment(payment_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM payments WHERE id = %s", (payment_id,))
        payment = cursor.fetchone()
        
        if not payment:
            return jsonify({'success': False, 'message': 'Payment not found'}), 404
        
        if payment['status'] != 'completed':
            return jsonify({'success': False, 'message': 'Cannot refund non-completed payment'}), 400
        
        cursor.execute("UPDATE payments SET status = %s WHERE id = %s", ('refunded', payment_id))
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment refunded successfully',
            'payment_id': payment_id
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/payment/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total_payments, SUM(amount) as total_amount FROM payments WHERE status = 'completed'")
        stats = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_payments': stats['total_payments'],
                'total_amount': float(stats['total_amount']) if stats['total_amount'] else 0
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    host = os.getenv('PAYMENT_SERVICE_HOST', '0.0.0.0')
    port = int(os.getenv('PAYMENT_SERVICE_PORT', '5004'))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host=host, port=port, debug=debug)