# VersePilot Setup Guide

This guide provides all the necessary steps to set up the VersePilot development environment on macOS.

## 1. System-Level Dependencies (Optional)

These are required only if you need NDI video output.

### NDI SDK

For live video output to ProPresenter, the NDI SDK must be installed on your system.
- **Download**: [NDI Core Suite for macOS](https://ndi.video/tools/ndi-core-suite/)
- **Installation**: Run the downloaded installer. This will install the necessary libraries in a system-wide location.

**Note**: The Python wrapper for NDI can be difficult to build. If you encounter issues during `pip install`, ensure `cmake` is installed (`brew install cmake`) and that the NDI SDK is in a standard location like `/Library/NDI SDK for Apple/` or `/Users/Shared/NDI SDK for Apple/`.

## 2. Python Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Navigate to the project root
cd /path/to/VersePilot

# Create a virtual environment
python3 -m venv .venv

# Activate the environment
source .venv/bin/activate
```

## 3. Install Python Packages

With your virtual environment activated, install all required packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

## 4. Download Models & Data

The application requires a few external files to be downloaded manually.

### Vosk Model (Required)
The speech recognition service needs a language model to function.

- **Download**: [Vosk Small English Model (v0.15)](https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip)
- **Installation**: Unzip the downloaded file and place the resulting folder (e.g., `vosk-model-small-en-us-0.15`) into the root directory of the VersePilot project.

### KJV Bible JSON (Required)
The application uses a local JSON file for offline Bible lookups.

- **File**: You will need to source a KJV Bible in JSON format. The expected structure is:
  ```json
  {
    "Genesis": {
      "1": {
        "1": "In the beginning God created the heaven and the earth."
      }
    },
    ...
  }
  ```
- **Installation**: Place the file named `kjv.json` inside the `assets/data/` directory.

### Whisper Model
The `openai-whisper` library will automatically download the required transcription model on its first run. No manual download is needed, but an internet connection is required the first time you use the listening feature.

## 5. Running the Application

To launch the VersePilot GUI, run the `app_window.py` module from the **project's root directory**:

```bash
python3 -m app.ui.app_window
```

Running it this way ensures that all the application's internal imports (`from app.core...`) work correctly.
