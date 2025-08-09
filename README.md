# AI Assistant App

AI-powered personal assistant that monitors audio, screen activity, and generates insights.

## Features

- Real-time audio transcription from meetings and voice
- Screen capture during user activity
- AI-powered activity analysis and summarization
- Real-time todo extraction and notifications
- Daily activity reports and time tracking

## Tech Stack

- **Language**: Python
- **LLM**: Microsoft Phi-3 Mini (3.8B)
- **Speech Recognition**: faster-whisper
- **UI**: PyQt6 with system tray integration
- **Database**: SQLite

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Architecture

```
src/
├── audio/          # Audio capture and transcription
├── screen/         # Screen capture functionality
├── ai/            # LLM integration and analysis
├── ui/            # Desktop UI and system tray
├── database/      # Data storage and management
└── main.py        # Application entry point
```