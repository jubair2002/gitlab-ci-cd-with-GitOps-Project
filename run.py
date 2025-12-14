import subprocess
import time
import sys
import os

def run_service(service_name, port):
    """Run a microservice by executing 'python app.py' in the service's directory."""
    print(f"🚀 Starting {service_name} on port {port}...")
    
    # FIX: Use the 'cwd' argument. This is the robust, cross-platform way 
    # to execute a command within a specific directory.
    cmd = ["python", "app.py"] 
    # The command runs 'python app.py' but starts execution inside the 'service_name' folder.
    process = subprocess.Popen(cmd, cwd=service_name)
    return process

def main():
    print("🔧 Starting Microservices Application...")
    
    services = [
        ('auth-service', 5001),
        ('user-service', 5002),
        ('survey-service', 5003),
        ('payment-service', 5004),
    ]
    
    processes = []
    
    # Start all microservices
    for service_name, port in services:
        try:
            process = run_service(service_name, port)
            processes.append(process)
            time.sleep(2)  # Wait for service to start
        except Exception as e:
            print(f"❌ Failed to start {service_name}: {e}")
            print(f"HINT: Ensure the folder '{service_name}' exists at the root level.")
            sys.exit(1)
    
    print("⏳ Waiting for services to initialize...")
    time.sleep(3)
    
    # Start API Gateway
    print("🌐 Starting API Gateway on port 8000...")
    try:
        # FIX: Start API Gateway using cwd="api-gateway"
        gateway_process = subprocess.Popen(["python", "app.py"], cwd="api-gateway")
        processes.append(gateway_process)
    except Exception as e:
        # This catches the WinError 267 if the directory is invalid or missing
        print(f"❌ Failed to start API Gateway: {e}")
        print("HINT: Ensure the folder 'api-gateway' exists and contains its app.py at the root level.")
        sys.exit(1)
    
    print("\n✅ All services started!")
    print("📱 Access your application at: http://localhost:8000")
    print("\n⏹️  Press Ctrl+C to stop all services")
    
    try:
        # Keep running until user stops the script
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
    finally:
        for process in processes:
            # Safely terminate running processes
            if process.poll() is None: 
                 process.terminate()
        print("All services stopped.")

if __name__ == '__main__':
    main()
