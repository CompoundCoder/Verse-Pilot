"""
Developer utility to detect and fix a deprecated Groq model ID in the .env file
and then cleanly restart the main PyQt application.

This script specifically checks for known decommissioned models and replaces them
with a stable, supported model.
"""
import os
import subprocess
import time
from dotenv import load_dotenv, set_key, find_dotenv

def main():
    """Executes the model check, fix, and application restart sequence."""
    
    # --- 1. Setup and Configuration ---
    # find_dotenv() will locate the .env file in the current or parent directories.
    env_path = find_dotenv()
    if not env_path:
        # If no .env exists, set_key will create one at this path.
        env_path = ".env"
    
    load_dotenv(dotenv_path=env_path)

    model_key = "GROQ_MODEL_ID"
    # A set of models known to be decommissioned by Groq.
    decommissioned_models = {"mixtral-8x7b-32768"}
    # The recommended model to use as a replacement.
    replacement_model = "llama3-8b-8192"

    # --- 2. Detect and Fix Deprecated Model ---
    current_model = os.getenv(model_key, "").strip()
    print(f"🔍 Current model ID: {current_model or '[NOT SET]'}")

    if not current_model or current_model in decommissioned_models:
        status = "deprecated" if current_model else "missing"
        print(f"⚠️  Model ID is {status}. Updating to a supported model.")
        print(f"   → Replacing '{current_model}' with '{replacement_model}'")
        
        # set_key creates the file if it doesn't exist and updates/adds the key.
        set_key(env_path, model_key, replacement_model)
        print("✅ .env file updated successfully.")
    else:
        print("✅ Model ID is valid. No changes needed.")

    # --- 3. Restart the Application ---
    app_process_name = "qt_main.py"
    print(f"\n🚀 Restarting VersePilot app ({app_process_name})...")
    
    try:
        # Use pkill to gracefully terminate any existing instance (macOS/Linux).
        kill_command = ["pkill", "-f", app_process_name]
        # Redirect output to prevent messages if no process is found.
        subprocess.run(kill_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)  # Brief pause for the OS to release the process.
        print("   → Old instance terminated (if any).")

        # Relaunch the application as a new, independent process.
        subprocess.Popen(["python3", app_process_name])
        print("   → New instance launched successfully.")

    except FileNotFoundError:
        print(f"❌ Error: 'pkill' command not found. Cannot automatically restart.")
        print(f"   Please kill the app manually and start it with: python3 {app_process_name}")
    except Exception as e:
        print(f"❌ An unexpected error occurred during restart: {e}")

if __name__ == "__main__":
    main() 