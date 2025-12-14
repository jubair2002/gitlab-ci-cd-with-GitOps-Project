from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Service URLs
SERVICE_URLS = {
    'auth': os.getenv("AUTH_SERVICE_URL", "http://localhost:5001"),
    'user': os.getenv("USER_SERVICE_URL", "http://localhost:5002"),
    'survey': os.getenv("SURVEY_SERVICE_URL", "http://localhost:5003"),
    'payment': os.getenv("PAYMENT_SERVICE_URL", "http://localhost:5004")
}


def proxy_request(service_name, subpath=""):
    """Core logic to proxy the request to the correct microservice."""
    if service_name not in SERVICE_URLS:
        return jsonify({'error': 'Service not found'}), 404
    
    service_url = SERVICE_URLS[service_name]
    
    # Remove trailing slash from service_url
    service_url = service_url.rstrip('/')
    
    # Construct the target URL properly
    if subpath:
        target_url = f"{service_url}/{subpath}"
    else:
        target_url = service_url
    
    print(f"🔄 Proxying request to: {target_url}")
    
    try:
        resp = requests.request(
            method=request.method,
            url=target_url,
            headers={key: value for key, value in request.headers if key.lower() != 'host'},
            data=request.get_data(),
            params=request.args,
            cookies=request.cookies,
            timeout=5
        )
        
        print(f"✅ Success: {resp.status_code} from {target_url}")
        
        # Return response content, status code, and headers
        headers = dict(resp.headers)
        # Remove content-length header as it might not match after processing
        headers.pop('Content-Length', None)
        headers.pop('content-length', None)
        
        return (resp.content, resp.status_code, headers)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed: {target_url} - {str(e)}")
        return jsonify({
            'error': f'Service {service_name} unavailable',
            'detail': str(e),
            'tried_url': target_url
        }), 503

@app.route('/api/<service_name>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_service_root(service_name):
    """Handle requests directly to the service root (e.g., /api/auth)."""
    return proxy_request(service_name)

@app.route('/api/<service_name>/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_api(service_name, subpath):
    """Handle requests with a subpath (e.g., /api/auth/users)."""
    return proxy_request(service_name, subpath)

@app.route('/')
def serve_home():
    """Serve the main dashboard page."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        frontend_path = os.path.join(current_dir, '..', 'frontend', 'index.html')
        frontend_path = os.path.abspath(frontend_path)
        
        print(f"📁 Serving frontend from: {frontend_path}")
        print(f"📁 File exists: {os.path.exists(frontend_path)}")
        
        if os.path.exists(frontend_path):
            return send_file(frontend_path)
        else:
            return jsonify({
                'message': 'API Gateway is running but frontend not found',
                'available_endpoints': {
                    'gateway_health': '/health',
                    'auth_service': '/api/auth',
                    'user_service': '/api/user', 
                    'survey_service': '/api/survey',
                    'payment_service': '/api/payment'
                }
            }), 404
            
    except Exception as e:
        return f"Error loading frontend: {str(e)}", 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy', 
        'service': 'api-gateway',
        'port': 8000
    })

if __name__ == '__main__':
    print("🚀 Starting API Gateway on port 8000...")
    print("📋 Available services:")
    for service, url in SERVICE_URLS.items():
        print(f"   - {service}: {url}")
    
    app.run(host='0.0.0.0', port=8000, debug=True)