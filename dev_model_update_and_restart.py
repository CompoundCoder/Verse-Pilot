import os
import subprocess
import time
from dotenv import load_dotenv, find_dotenv

def update_env_file(key, value):
    """Updates or adds a key-value pair to the .env file."""
    env_file = find_dotenv()
    if not env_file:
        env_file = ".env" # Create one if it doesn't exist
    
    lines = []
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            lines = f.readlines()

    found = False
    with open(env_file, "w") as f:
        for i, line in enumerate(lines):
            if line.strip().startswith(key + "="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
        if not found:
            lines.append(f"\n{key}={value}\n")
        f.writelines(lines)
    
    print(f"✅ .env updated: {key}={value}")

def main():
    """
    Ensures the correct Groq model is set in the .env file, then cleanly
    restarts the main PyQt application.
    """
    # --- 1. Load and Validate Environment ---
    load_dotenv()
    model_key = "GROQ_MODEL_ID"
    supported_models = {"llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it"}
    default_model = "llama3-8b-8192"

    current_model = os.getenv(model_key)
    print(f"🔍 Current model ID: {current_model or '[NOT SET]'}")

    if current_model not in supported_models:
        print(f"⚠️  Invalid or missing model ID. Updating to default: {default_model}")
        update_env_file(model_key, default_model)
    else:
        print(f"✅ Current model ID is valid.")

    # --- 2. Restart the Application ---
    app_process_name = "qt_main.py"
    print(f"\n🚀 Restarting VersePilot app ({app_process_name})...")
    
    try:
        # Gracefully kill any existing instance of the app
        # This is specific to macOS/Linux.
        kill_command = ["pkill", "-f", app_process_name]
        subprocess.run(kill_command, check=False) # Use check=False to ignore errors if process not found
        time.sleep(1) # Give the OS a moment to release the process
        print("   → Old instance terminated (if any).")

        # Relaunch the application as a new, independent process
        subprocess.Popen(["python3", app_process_name])
        print(f"   → New instance launched successfully.")

    except FileNotFoundError:
        print("❌ Error: 'pkill' command not found. Cannot restart the application.")
        print("   Please kill the existing application manually and start it with 'python3 qt_main.py'")
    except Exception as e:
        print(f"❌ An unexpected error occurred during restart: {e}")

if __name__ == "__main__":
    main() 