from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector
import os
import json
from dotenv import load_dotenv

# Load .env from project root (two levels up from src/survey-service/)
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
        'service': 'survey-service',
        'status': 'running',
        'endpoints': ['/health', '/surveys', '/api/survey/surveys', '/api/survey/responses']
    })

@app.route('/surveys', methods=['GET'])
def get_surveys_simple():
    """Simple endpoint for dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM surveys ORDER BY created_at DESC")
        surveys = cursor.fetchall()
        return jsonify({'surveys': surveys}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'survey-service'}), 200

@app.route('/api/survey/surveys', methods=['GET'])
def get_surveys():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM surveys ORDER BY created_at DESC")
        surveys = cursor.fetchall()
        return jsonify({'surveys': surveys}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/survey/surveys/<int:survey_id>', methods=['GET'])
def get_survey(survey_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM surveys WHERE id = %s", (survey_id,))
        survey = cursor.fetchone()
        
        if survey:
            return jsonify({'success': True, 'survey': survey}), 200
        else:
            return jsonify({'success': False, 'message': 'Survey not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/survey/surveys', methods=['POST'])
def create_survey():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    created_by = data.get('created_by', 1)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO surveys (title, description, created_by) VALUES (%s, %s, %s)",
            (title, description, created_by)
        )
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Survey created successfully',
            'survey_id': cursor.lastrowid
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/survey/responses', methods=['POST'])
def submit_response():
    data = request.json
    survey_id = data.get('survey_id')
    user_id = data.get('user_id')
    response_data = data.get('response_data')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO survey_responses (survey_id, user_id, response_data) VALUES (%s, %s, %s)",
            (survey_id, user_id, json.dumps(response_data))
        )
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'Response submitted successfully',
            'response_id': cursor.lastrowid
        }), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/survey/responses/<int:survey_id>', methods=['GET'])
def get_survey_responses(survey_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM survey_responses WHERE survey_id = %s", (survey_id,))
        responses = cursor.fetchall()
        
        # Parse JSON response_data
        for response in responses:
            if response.get('response_data'):
                response['response_data'] = json.loads(response['response_data'])
        
        return jsonify({'success': True, 'responses': responses}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@app.route('/api/survey/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total_surveys FROM surveys")
        surveys = cursor.fetchone()
        cursor.execute("SELECT COUNT(*) as total_responses FROM survey_responses")
        responses = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_surveys': surveys['total_surveys'],
                'total_responses': responses['total_responses']
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
    host = os.getenv('SURVEY_SERVICE_HOST', '0.0.0.0')
    port = int(os.getenv('SURVEY_SERVICE_PORT', '5003'))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host=host, port=port, debug=debug)