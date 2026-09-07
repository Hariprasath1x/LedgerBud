import subprocess
import sys
import os
import platform
import shutil
import time

def kill_port(port):
    """Kills any process listening on the specified port (best-effort, silent failures)."""
    if platform.system() == "Windows":
        cmd = f'for /f "tokens=5" %a in (\'netstat -aon ^| findstr ":{port}" ^| findstr "LISTENING"\') do taskkill /F /PID %a >nul 2>&1'
        os.system(cmd)
    else:
        # Only attempt if lsof is available (not present in slim Docker images)
        if shutil.which("lsof"):
            os.system(f'lsof -ti:{port} | xargs kill -9 >/dev/null 2>&1')

def main():
    print("Checking and freeing up ports (8000 for Backend, 8501 for Frontend)...")
    kill_port(8000)
    kill_port(8501)
    
    print("\nStarting LedgerBud Servers...")
    
    # We use subprocess.Popen to run both in parallel
    # Redirecting output is optional, but leaving it default prints directly to the console
    backend = subprocess.Popen([sys.executable, "run_fastapi.py"])
    
    # We use python -m streamlit to ensure we use the current environment's streamlit
    frontend = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.address", "0.0.0.0", "--server.headless", "true"])
    
    print("\n" + "="*50)
    print("LedgerBud Application is now running!")
    print("Backend API is at: http://localhost:8000")
    print("Frontend UI is at: http://localhost:8501")
    print("Press Ctrl+C to shut down both servers cleanly.")
    print("="*50 + "\n")
    
    try:
        # Keep the main thread alive to catch Ctrl+C
        while True:
            time.sleep(1)
            
            # If either process dies unexpectedly, we might want to know
            if backend.poll() is not None or frontend.poll() is not None:
                print("\nOne of the servers has stopped unexpectedly. Shutting down...")
                break
                
    except KeyboardInterrupt:
        print("\nReceived Ctrl+C. Shutting down gracefully...")
    
    finally:
        print("Terminating Backend...")
        backend.terminate()
        
        print("Terminating Frontend...")
        frontend.terminate()
        
        # Wait for them to close completely
        backend.wait()
        frontend.wait()
        
        # Double check the ports are cleared to prevent "port already in use" issues
        kill_port(8000)
        kill_port(8501)
        print("All processes stopped successfully. Goodbye!")

if __name__ == "__main__":
    main()
