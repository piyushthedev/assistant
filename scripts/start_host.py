import os
import time
import subprocess
from pyngrok import ngrok, conf
import sys
import ssl

# Configure pyngrok to be verbose? No, just catch exceptions better.

def start_hosting():
    with open("hosting.log", "w") as log:
        def log_print(msg):
            print(msg)
            sys.stdout.flush()
            log.write(msg + "\n")
            log.flush()

        log_print("🚀 Starting Broklin Hosting...")

        # 1. Kill existing processes
        os.system("pkill -f app.py")
        
        # SSL Fix for Mac
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        # 2. Start Flask App in background
        log_print("▶️  Starting Web App...")
        app_process = subprocess.Popen([sys.executable, "app.py"], stdout=log, stderr=log)
        
        # Give it a moment to start
        time.sleep(5)

        # 3. Start ngrok tunnel
        log_print("🌐 Connecting to Public Internet via ngrok...")
        try:
            # Set up configuration to avoid potential config file issues
            # conf.get_default().region = "us" 
            
            public_url = ngrok.connect(5001).public_url
            log_print("\n" + "="*50)
            log_print(f"✅  HOSTING SUCCESSFUL!")
            log_print(f"🌍  Public URL: {public_url}")
            log_print("="*50 + "\n")
            log_print("Share this URL with anyone. It works on Mobile too!")
        except Exception as e:
            log_print(f"❌ ngrok Error: {e}")
            log_print("Ensure you have an authtoken if required.")

        try:
            app_process.wait()
        except KeyboardInterrupt:
            log_print("\n🛑 Stopping...")
            ngrok.kill()
            app_process.terminate()

if __name__ == "__main__":
    start_hosting()
