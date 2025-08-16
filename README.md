# Verse Pilot 1.3 (Rollback Clean)

This branch contains the rolled-back app (no experimental presentation engine) and a clean dev setup.

## Prerequisites
- Node.js v20.19.1 (`.nvmrc`)
- Python 3.11.0 (`.python-version`)
- macOS: `brew install portaudio ffmpeg`
- Windows: Visual Studio Build Tools (C++), PortAudio (optional), FFmpeg (optional)

## Setup
```bash
# clone
git clone https://github.com/CompoundCoder/Verse-Pilot.git
cd Verse-Pilot
git checkout Verse-Pilot-1.3

# Node
nvm use
npm ci

# Frontend deps
cd frontend && npm ci && cd ..

# Python
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\Activate.ps1
pip install -r backend/requirements.lock.txt  # or requirements.txt
```

## Run (dev)
```bash
# start frontend
npm run dev:frontend
# in another terminal
npm run dev:electron
# or
npm run dev:full
```

Notes:
- Frontend runs on http://localhost:5173
- Grant mic permissions to Electron on first launch

## Not in Git (bring your own)
- Large media: `TEST RECORDINGS/`, `*.wav`, `*.mp3`
- Backups: `backups/`, `*.zip`, `*.tar.gz`
- Local envs: `.venv/`, `node_modules/`
- API keys (e.g. `GOOGLE_API_KEY` if used)

## Troubleshooting
- Use `./scripts/restore-mac-linux.sh` to restore toolchain quickly
- If Electron shows no UI, ensure frontend is on port 5173 and restart Electron
- On Windows, run PowerShell as Admin for PortAudio installs

