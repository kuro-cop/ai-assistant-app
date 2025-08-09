"""
Configuration settings for AI Assistant App
"""

import os

# Audio Settings
AUDIO_CONFIG = {
    "sample_rate": 16000,
    "channels": 1,
    "chunk_duration": 0.1,  # seconds
    "buffer_duration": 300.0,  # 5 minutes
    "voice_threshold": 0.01,  # RMS threshold for voice detection
}

# Speech Recognition Settings
SPEECH_CONFIG = {
    "whisper_model": "tiny",  # tiny, base, small, medium, large
    "language": "ja",  # Japanese
    "process_interval": 2.0,  # seconds between processing
}

# Command Detection Settings
COMMAND_CONFIG = {
    "default_commands": [
        "今のところメモ",
        "いまのところメモ", 
        "メモして",
        "タスク登録",
        "todo追加",
        "記録して",
        "タスクにして"
    ],
    "context_duration": 60.0,  # seconds of context to capture
}

# Task Management Settings
TASK_CONFIG = {
    "database_path": "data/tasks.db",
    "default_priority": "medium",
    "auto_tag_voice_tasks": True,
    "confidence_threshold": 0.3,  # Minimum confidence for auto-task creation
}

# Database Settings
DATABASE_CONFIG = {
    "tasks_db": "data/tasks.db",
    "transcriptions_db": "data/transcriptions.db",
    "create_data_dir": True,
}

# UI Settings
UI_CONFIG = {
    "system_tray": True,
    "show_notifications": True,
    "notification_duration": 5000,  # milliseconds
    "log_level": "INFO",
}

# Future: Jira Integration Settings
JIRA_CONFIG = {
    "enabled": False,
    "url": "",
    "username": "",
    "api_token": "",
    "project_key": "",
    "issue_type": "Task",
}

# Future: LLM Settings
LLM_CONFIG = {
    "model_name": "microsoft/Phi-3-mini-4k-instruct",
    "max_tokens": 512,
    "temperature": 0.7,
    "local_inference": True,
}

def ensure_data_directory():
    """Create data directory if it doesn't exist"""
    if DATABASE_CONFIG["create_data_dir"]:
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"Created data directory: {data_dir}")

def get_full_db_path(db_name: str) -> str:
    """Get full path for database file"""
    ensure_data_directory()
    return os.path.join("data", db_name)