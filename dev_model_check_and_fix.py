import os
from dotenv import load_dotenv, find_dotenv

def ensure_model_id():
    """
    Ensures the .env file contains the correct, recommended GROQ_MODEL_ID.
    """
    load_dotenv()
    env_path = find_dotenv()
    if not env_path:
        env_path = ".env" # Create one if it doesn't exist

    model_var = "GROQ_MODEL_ID"
    valid_model = "mixtral-8x22b-instruct-v0.1"
    
    current_model = os.getenv(model_var)
    
    print(f"🔍 Current model ID: {current_model or '[NOT SET]'}")

    if current_model != valid_model:
        print(f"⚠️  Updating model to recommended version: {valid_model}")
        
        # Read current .env content
        lines = []
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                lines = f.readlines()

        # Write back, replacing or adding the model ID
        with open(env_path, "w") as f:
            found = False
            for line in lines:
                if line.strip().startswith(model_var + "="):
                    f.write(f"{model_var}={valid_model}\n")
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(f"\n{model_var}={valid_model}\n") # Add on a new line if not found
        
        print(f"✅ .env updated with: {model_var}={valid_model}")
        print("💡 Restart your app for the change to take effect.")
    else:
        print("✅ GROQ_MODEL_ID is already set to the recommended version.")

if __name__ == "__main__":
    ensure_model_id() 