# Kokoro TTS Setup Instructions

## Prerequisites

1. **Install UV** (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install system dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y espeak-ng
   ```

## Setup Virtual Environment

1. **Navigate to the project directory**:
   ```bash
   cd /home/hehua/RepoInWSL/InternalTTS
   ```

2. **Create and activate virtual environment with UV**:
   ```bash
   uv venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   uv pip install -r requirements.txt
   ```

## Usage

### Command Line Mode
```bash
python tts.py "Hello world, this is a test of Kokoro TTS."
```

### Interactive Mode
```bash
python tts.py
# Then enter your text when prompted
```

## Features

- **Automatic model download**: Models are automatically downloaded and cached by Kokoro
- **Streaming support**: Handles long text efficiently with chunked processing
- **Heart voice**: Uses the default "Heart" voice (af_heart)
- **Timestamp naming**: Audio files are saved with timestamps (e.g., `audio_20251028_143025.wav`)
- **24kHz output**: High-quality audio at 24kHz sample rate
- **Dual input modes**: Command-line argument or interactive prompt

## Output

- Generated audio files are saved in the `audio/` directory
- Progress is shown during generation
- Final output path is displayed upon completion
