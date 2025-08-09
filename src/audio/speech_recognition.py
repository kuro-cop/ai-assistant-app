import asyncio
import threading
import queue
from typing import Optional, Callable, List, Dict
import numpy as np
from datetime import datetime, timedelta
import re

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Whisper not available. Install with: pip install openai-whisper")

from .capture import AudioCapture


class SpeechRecognizer:
    """
    Real-time speech recognition with command detection and buffering
    """
    
    def __init__(self, 
                 model_size: str = "tiny",
                 language: str = "ja",
                 command_phrases: List[str] = None):
        
        self.model_size = model_size
        self.language = language
        
        # Default command phrases
        self.command_phrases = command_phrases or [
            "今のところメモ",
            "いまのところメモ", 
            "メモして",
            "タスク登録",
            "todo追加"
        ]
        
        # Whisper model
        self.model = None
        self._load_model()
        
        # Audio processing
        self.audio_capture = AudioCapture()
        self.recognition_queue = queue.Queue()
        self.is_processing = False
        
        # Transcription buffer - stores recent transcriptions with timestamps
        self.transcription_buffer = []
        self.max_buffer_minutes = 5
        
        # Callbacks
        self.on_transcription: Optional[Callable] = None
        self.on_command_detected: Optional[Callable] = None
        
    def _load_model(self):
        """Load Whisper model"""
        if not WHISPER_AVAILABLE:
            print("Whisper not available")
            return
            
        try:
            print(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size)
            print("Whisper model loaded successfully")
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            
    def start_recognition(self):
        """Start real-time speech recognition"""
        if not self.model:
            print("Speech recognition model not available")
            return
            
        # Set up audio capture callback
        self.audio_capture.on_audio_chunk = self._on_audio_chunk
        
        # Start audio capture
        self.audio_capture.start_capture()
        
        # Start processing thread
        self.is_processing = True
        self.processing_thread = threading.Thread(target=self._processing_loop)
        self.processing_thread.start()
        
    def stop_recognition(self):
        """Stop speech recognition"""
        self.is_processing = False
        self.audio_capture.stop_capture()
        
        if hasattr(self, 'processing_thread'):
            self.processing_thread.join()
            
    def _on_audio_chunk(self, audio_chunk: np.ndarray, source: str):
        """Handle incoming audio chunks"""
        # Simple voice activity detection
        if self.audio_capture.detect_voice_activity(audio_chunk):
            # Add to processing queue
            self.recognition_queue.put((audio_chunk, source, datetime.now()))
            
    def _processing_loop(self):
        """Main processing loop for speech recognition"""
        accumulated_audio = []
        last_process_time = datetime.now()
        process_interval = timedelta(seconds=2)  # Process every 2 seconds
        
        while self.is_processing:
            try:
                # Get audio chunk with timeout
                audio_chunk, source, timestamp = self.recognition_queue.get(timeout=0.1)
                accumulated_audio.extend(audio_chunk)
                
                # Process accumulated audio periodically
                current_time = datetime.now()
                if current_time - last_process_time > process_interval and accumulated_audio:
                    self._process_audio_chunk(np.array(accumulated_audio), source, current_time)
                    accumulated_audio = []
                    last_process_time = current_time
                    
            except queue.Empty:
                # Process any remaining audio
                if accumulated_audio:
                    self._process_audio_chunk(np.array(accumulated_audio), source, datetime.now())
                    accumulated_audio = []
                    last_process_time = datetime.now()
                continue
            except Exception as e:
                print(f"Processing loop error: {e}")
                
    def _process_audio_chunk(self, audio_data: np.ndarray, source: str, timestamp: datetime):
        """Process audio chunk with Whisper"""
        if not self.model or len(audio_data) == 0:
            return
            
        try:
            # Convert to float32 and normalize
            audio_float = audio_data.astype(np.float32)
            if np.max(np.abs(audio_float)) > 0:
                audio_float = audio_float / np.max(np.abs(audio_float))
            
            # Run Whisper transcription
            result = self.model.transcribe(
                audio_float, 
                language=self.language,
                task="transcribe"
            )
            
            text = result["text"].strip()
            if text:
                # Store transcription with metadata
                transcription_entry = {
                    "text": text,
                    "timestamp": timestamp,
                    "source": source,  # "microphone" or "system"
                    "confidence": result.get("segments", [{}])[0].get("confidence", 0.0) if result.get("segments") else 0.0
                }
                
                self._add_to_buffer(transcription_entry)
                
                # Check for commands
                self._check_for_commands(text, transcription_entry)
                
                # Callback for general transcription
                if self.on_transcription:
                    self.on_transcription(transcription_entry)
                    
        except Exception as e:
            print(f"Transcription error: {e}")
            
    def _add_to_buffer(self, transcription_entry: Dict):
        """Add transcription to buffer and cleanup old entries"""
        self.transcription_buffer.append(transcription_entry)
        
        # Remove old entries (older than max_buffer_minutes)
        cutoff_time = datetime.now() - timedelta(minutes=self.max_buffer_minutes)
        self.transcription_buffer = [
            entry for entry in self.transcription_buffer 
            if entry["timestamp"] > cutoff_time
        ]
        
    def _check_for_commands(self, text: str, transcription_entry: Dict):
        """Check if transcription contains command phrases"""
        text_lower = text.lower()
        
        for command_phrase in self.command_phrases:
            if command_phrase.lower() in text_lower:
                print(f"Command detected: {command_phrase}")
                
                # Get recent context (last 1 minute)
                recent_transcriptions = self.get_recent_transcriptions(duration_minutes=1.0)
                
                if self.on_command_detected:
                    self.on_command_detected({
                        "command": command_phrase,
                        "trigger_text": text,
                        "timestamp": transcription_entry["timestamp"],
                        "context": recent_transcriptions
                    })
                break
                
    def get_recent_transcriptions(self, duration_minutes: float = 1.0) -> List[Dict]:
        """Get transcriptions from the last N minutes"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        return [
            entry for entry in self.transcription_buffer
            if entry["timestamp"] > cutoff_time
        ]
        
    def get_transcription_text(self, duration_minutes: float = 1.0) -> str:
        """Get concatenated text from recent transcriptions"""
        recent = self.get_recent_transcriptions(duration_minutes)
        return " ".join([entry["text"] for entry in recent])
        
    def add_command_phrase(self, phrase: str):
        """Add new command phrase"""
        if phrase not in self.command_phrases:
            self.command_phrases.append(phrase)
            
    def remove_command_phrase(self, phrase: str):
        """Remove command phrase"""
        if phrase in self.command_phrases:
            self.command_phrases.remove(phrase)


class CommandProcessor:
    """
    Process detected commands and extract actionable items
    """
    
    def __init__(self):
        # Pattern matching for todo extraction
        self.todo_patterns = [
            r"(?:する|やる|確認する|調べる|連絡する|作成する|修正する|対応する)",
            r"(?:までに|まで|by|until)",
            r"(?:タスク|todo|課題|作業|宿題)",
        ]
        
    def process_command(self, command_data: Dict) -> Dict:
        """Process command and extract actionable items"""
        context_text = " ".join([entry["text"] for entry in command_data["context"]])
        
        # Extract potential todos using patterns and keywords
        todos = self._extract_todos(context_text)
        
        return {
            "command": command_data["command"],
            "timestamp": command_data["timestamp"],
            "context_text": context_text,
            "extracted_todos": todos,
            "confidence": self._calculate_confidence(todos)
        }
        
    def _extract_todos(self, text: str) -> List[Dict]:
        """Extract todo items from text using pattern matching"""
        todos = []
        
        # Split into sentences
        sentences = re.split(r'[。．.!！？\?]', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 3:
                continue
                
            # Check if sentence contains action words
            if any(re.search(pattern, sentence) for pattern in self.todo_patterns):
                todos.append({
                    "text": sentence,
                    "type": "action_item",
                    "confidence": 0.8
                })
                
        return todos
        
    def _calculate_confidence(self, todos: List[Dict]) -> float:
        """Calculate overall confidence score"""
        if not todos:
            return 0.0
            
        return sum(todo["confidence"] for todo in todos) / len(todos)