"""
dev_diagnostics.py

A diagnostic scanner for the VersePilot environment to quickly identify and report
common configuration issues before running the main application.
"""
import os
import sys
import shutil
from pathlib import Path

# --- Dependency Check ---
try:
    import sounddevice as sd
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ CRITICAL: Missing required package '{e.name}'.")
    print(f"   Please install it by running: pip install {e.name}")
    sys.exit(1)

def check_env_variables():
    """Checks for required API keys and a valid model ID in the .env file."""
    print("--- 1. Checking Environment Variables (.env) ---")
    is_ok = True
    
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    model_id = os.getenv("GROQ_MODEL_ID")
    
    if not api_key:
        print("   ❌ GROQ_API_KEY: Is missing or empty.")
        is_ok = False
    else:
        print(f"   ✅ GROQ_API_KEY: Found.")
        
    if not model_id:
        print(f"   ❌ GROQ_MODEL_ID: Is missing or empty.")
        is_ok = False
    elif model_id == "mixtral-8x7b-32768":
        print(f"   ⚠️  GROQ_MODEL_ID: Is set to a deprecated model ('{model_id}').")
        print("      → Please run 'python dev_fix_deprecated_model_and_restart.py' to fix.")
        is_ok = False
    else:
        print(f"   ✅ GROQ_MODEL_ID: Set to '{model_id}'.")
        
    return is_ok

def check_local_model():
    """Checks for the presence of the local GGUF model file."""
    print("\n--- 2. Checking Local AI Model File ---")
    model_path = Path("models/deepseek-coder-1.3b-instruct.Q5_K_M.gguf")
    
    if not model_path.exists():
        print(f"   ❌ Local Model: Not found at '{model_path}'.")
        print("      → The local AI detector will not be available.")
        print("      → To use it, download the model and place it in the 'models' directory.")
        return False
    else:
        print(f"   ✅ Local Model: Found at '{model_path}'.")
        return True

def check_audio_devices():
    """Checks for available microphone input devices."""
    print("\n--- 3. Checking Audio Devices ---")
    try:
        devices = sd.query_devices()
        input_devices = [dev for dev in devices if dev.get('max_input_channels', 0) > 0]
        if not input_devices:
            print("   ⚠️  Microphones: No input devices found. You won't be able to record.")
            return False
        else:
            print(f"   ✅ Microphones: Found {len(input_devices)} device(s).")
            return True
    except Exception as e:
        print(f"   ❌ Microphones: Could not query audio devices: {e}")
        return False

def check_disk_space():
    """Warns if available disk space is low."""
    print("\n--- 4. Checking Disk Space ---")
    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        if free_gb < 2:
            print(f"   ⚠️  Disk Space: Low ({free_gb} GB free). This may impact model performance.")
        else:
            print(f"   ✅ Disk Space: {free_gb} GB free.")
        return True
    except Exception as e:
        print(f"   ❌ Disk Space: Could not check disk space: {e}")
        return False

def main():
    """Runs all diagnostic checks and prints a summary."""
    print("\n🧪 Running VersePilot Environment Diagnostics...\n")
    
    results = {
        "env": check_env_variables(),
        "model": check_local_model(),
        "audio": check_audio_devices(),
        "disk": check_disk_space(),
    }
    
    all_ok = all(results.values())
    
    print("\n" + "="*40)
    if all_ok:
        print("\n✅ All checks passed. Your environment looks good!\n")
    else:
        print("\n⚠️  Some checks failed. Please review the messages above.\n")

if __name__ == "__main__":
    main() 