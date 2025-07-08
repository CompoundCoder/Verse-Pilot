"""
Developer utility to detect and fix a deprecated Groq model ID in the .env file
and then cleanly restart the main PyQt application.

This script specifically checks for known decommissioned models and replaces them
with a stable, preferred fallback model.
"""
import os
import subprocess
import time
from dotenv import load_dotenv, set_key, find_dotenv

def main():
    """Executes the model check, fix, and application restart sequence."""
    
    # --- 1. Find and Load .env File ---
    env_path = find_dotenv()
    if not env_path:
        # If no .env exists, set_key will create one at this path.
        env_path = ".env"
    load_dotenv(dotenv_path=env_path)

    model_key = "GROQ_MODEL_ID"
    # Models known to be decommissioned by Groq.
    decommissioned = {"mixtral-8x7b-32768"}
    # The recommended model to use as a replacement.
    preferred_fallback = "llama3-8b-8192"

    # --- 2. Detect and Fix Invalid Model ---
    current_model = os.getenv(model_key, "").strip()
    print(f"🔍 Current model ID: {current_model or '[NOT SET]'}")

    if not current_model or current_model in decommissioned:
        status = "deprecated" if current_model else "missing"
        print(f"⚠️  Model ID is {status}.")
        print(f"   → Updating .env with preferred model: {preferred_fallback}")
        
        # set_key will create the file if it doesn't exist, and update the value if it does.
        set_key(env_path, model_key, preferred_fallback)
        print("✅ .env file updated successfully.")
    else:
        print("✅ Current model ID is valid.")

    # --- 3. Restart the Application ---
    app_process_name = "qt_main.py"
    print(f"\n🚀 Restarting VersePilot app ({app_process_name})...")
    
    try:
        # Gracefully kill any existing instance of the app (macOS/Linux).
        kill_command = ["pkill", "-f", app_process_name]
        subprocess.run(kill_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)  # Brief pause for the OS to release the process.
        print("   → Old instance terminated (if any).")

        # Relaunch the application as a new, independent process.
        subprocess.Popen(["python3", app_process_name])
        print("   → New instance launched successfully.")

    except FileNotFoundError:
        print("❌ Error: 'pkill' command not found. This script is intended for macOS/Linux.")
        print("   Please kill the existing application manually and start it with 'python3 qt_main.py'")
    except Exception as e:
        print(f"❌ An unexpected error occurred during restart: {e}")

if __name__ == "__main__":
    main() 