#!/usr/bin/env python3
"""
AI Assistant App - Main Entry Point
"""

import sys
import signal
import time
from datetime import datetime
from src.audio.speech_recognition import SpeechRecognizer, CommandProcessor
from src.tasks.manager import TaskManager, VoiceTaskProcessor


class AIAssistant:
    """
    Main AI Assistant application
    """
    
    def __init__(self):
        self.is_running = False
        
        # Initialize components
        self.speech_recognizer = SpeechRecognizer(
            model_size="tiny",  # Lightweight model for testing
            language="ja",
            command_phrases=[
                "今のところメモ",
                "いまのところメモ", 
                "メモして",
                "タスク登録",
                "todo追加",
                "記録して"
            ]
        )
        
        self.command_processor = CommandProcessor()
        self.task_manager = TaskManager()
        self.voice_task_processor = VoiceTaskProcessor(self.task_manager)
        
        # Set up callbacks
        self.speech_recognizer.on_transcription = self._on_transcription
        self.speech_recognizer.on_command_detected = self._on_command_detected
        
    def start(self):
        """Start the AI Assistant"""
        print("🤖 AI Assistant starting...")
        print("Available commands:")
        for cmd in self.speech_recognizer.command_phrases:
            print(f"  - {cmd}")
        print("\nPress Ctrl+C to stop")
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        
        try:
            # Start speech recognition
            self.speech_recognizer.start_recognition()
            self.is_running = True
            
            # Main loop
            while self.is_running:
                time.sleep(1)
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.stop()
            
    def stop(self):
        """Stop the AI Assistant"""
        print("\n🛑 Stopping AI Assistant...")
        self.is_running = False
        
        if self.speech_recognizer:
            self.speech_recognizer.stop_recognition()
            
        print("✅ AI Assistant stopped")
        
    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.stop()
        sys.exit(0)
        
    def _on_transcription(self, transcription_entry):
        """Handle general transcription"""
        timestamp = transcription_entry["timestamp"].strftime("%H:%M:%S")
        source = transcription_entry["source"]
        text = transcription_entry["text"]
        confidence = transcription_entry["confidence"]
        
        print(f"[{timestamp}] [{source}] {text} (confidence: {confidence:.2f})")
        
    def _on_command_detected(self, command_data):
        """Handle detected voice commands"""
        print(f"\n🎯 Command detected: {command_data['command']}")
        print(f"Trigger: {command_data['trigger_text']}")
        
        # Process command and extract tasks
        processed_command = self.command_processor.process_command(command_data)
        print(f"Context: {processed_command['context_text'][:100]}...")
        
        # Create tasks from voice command
        created_tasks = self.voice_task_processor.process_voice_command(processed_command)
        
        if created_tasks:
            print(f"✅ Created {len(created_tasks)} task(s):")
            for task in created_tasks:
                print(f"  - {task.title}")
                print(f"    Description: {task.description}")
                print(f"    ID: {task.id}")
        else:
            print("ℹ️ No actionable tasks found in context")
            
        # Show task summary
        self._show_task_summary()
        
    def _show_task_summary(self):
        """Show current task summary"""
        summary = self.task_manager.get_tasks_summary()
        if summary:
            print(f"\n📋 Task Summary: {summary}")
            
    def show_pending_tasks(self):
        """Show all pending tasks"""
        pending_tasks = self.task_manager.get_tasks(status="pending", limit=10)
        
        if pending_tasks:
            print(f"\n📝 Pending Tasks ({len(pending_tasks)}):")
            for i, task in enumerate(pending_tasks, 1):
                created_time = task.created_at.strftime("%m/%d %H:%M")
                print(f"  {i}. [{created_time}] {task.title}")
                if task.description != task.title:
                    print(f"     {task.description[:80]}...")
        else:
            print("\n✨ No pending tasks!")


def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "tasks":
        # Show tasks mode
        assistant = AIAssistant()
        assistant.show_pending_tasks()
        return
        
    # Normal mode - start voice recognition
    assistant = AIAssistant()
    try:
        assistant.start()
    except KeyboardInterrupt:
        assistant.stop()


if __name__ == "__main__":
    main()