import threading
import queue
import time
from collections import deque
from typing import Optional, Callable
import sounddevice as sd
import numpy as np


class AudioCapture:
    """
    System audio capture for real-time speech recognition
    Supports both microphone input and system audio capture
    """
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 channels: int = 1,
                 chunk_duration: float = 0.1,
                 buffer_duration: float = 60.0):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = int(sample_rate * chunk_duration)
        self.buffer_duration = buffer_duration
        self.max_buffer_size = int(sample_rate * buffer_duration)
        
        # Audio buffers for different sources
        self.mic_buffer = deque(maxlen=self.max_buffer_size)
        self.system_buffer = deque(maxlen=self.max_buffer_size)
        
        # Threading
        self.is_recording = False
        self.capture_thread = None
        self.audio_queue = queue.Queue()
        
        # Callbacks
        self.on_audio_chunk: Optional[Callable] = None
        self.on_voice_detected: Optional[Callable] = None
        
    def start_capture(self):
        """Start audio capture from microphone and system"""
        if self.is_recording:
            return
            
        self.is_recording = True
        self.capture_thread = threading.Thread(target=self._capture_loop)
        self.capture_thread.start()
        
    def stop_capture(self):
        """Stop audio capture"""
        self.is_recording = False
        if self.capture_thread:
            self.capture_thread.join()
            
    def get_recent_audio(self, duration_seconds: float = 60.0, source: str = "both") -> np.ndarray:
        """
        Get recent audio from buffer
        
        Args:
            duration_seconds: Duration of audio to retrieve
            source: "mic", "system", or "both"
        """
        samples_needed = int(self.sample_rate * duration_seconds)
        
        if source == "mic":
            buffer_data = list(self.mic_buffer)
        elif source == "system":
            buffer_data = list(self.system_buffer)
        else:  # both
            # Interleave mic and system audio
            buffer_data = list(self.mic_buffer) + list(self.system_buffer)
            
        if len(buffer_data) == 0:
            return np.array([])
            
        # Take most recent samples
        if len(buffer_data) > samples_needed:
            buffer_data = buffer_data[-samples_needed:]
            
        return np.array(buffer_data, dtype=np.float32)
        
    def _capture_loop(self):
        """Main capture loop running in separate thread"""
        
        def mic_callback(indata, frames, time, status):
            """Callback for microphone input"""
            if status:
                print(f"Microphone status: {status}")
            
            audio_chunk = indata[:, 0] if indata.ndim > 1 else indata
            self.mic_buffer.extend(audio_chunk)
            
            if self.on_audio_chunk:
                self.on_audio_chunk(audio_chunk, "microphone")
                
        def system_callback(indata, frames, time, status):
            """Callback for system audio output"""
            if status:
                print(f"System audio status: {status}")
                
            audio_chunk = indata[:, 0] if indata.ndim > 1 else indata
            self.system_buffer.extend(audio_chunk)
            
            if self.on_audio_chunk:
                self.on_audio_chunk(audio_chunk, "system")
        
        try:
            # Start microphone capture
            with sd.InputStream(
                callback=mic_callback,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size
            ):
                # For system audio capture, we'll need to use WASAPI on Windows
                # This is a simplified version - full system audio needs more complex setup
                while self.is_recording:
                    time.sleep(0.1)
                    
        except Exception as e:
            print(f"Audio capture error: {e}")
            
    def detect_voice_activity(self, audio_chunk: np.ndarray, threshold: float = 0.01) -> bool:
        """
        Simple voice activity detection based on RMS energy
        """
        if len(audio_chunk) == 0:
            return False
            
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        return rms > threshold
        
    def get_audio_devices(self):
        """Get available audio input/output devices"""
        return sd.query_devices()


class SystemAudioCapture:
    """
    Windows-specific system audio capture using WASAPI
    This captures audio from all applications (Zoom, Teams, etc.)
    """
    
    def __init__(self):
        # This would require pyaudio with WASAPI support or other Windows-specific libraries
        # For now, this is a placeholder for the full implementation
        pass
        
    def capture_system_audio(self):
        """Capture system audio output (speakers/headphones)"""
        # Implementation would use:
        # - PyAudio with WASAPI loopback
        # - or Windows Core Audio APIs via ctypes
        # - or dedicated libraries like pycaw
        pass
        
    def capture_application_audio(self, app_name: str):
        """Capture audio from specific application (e.g., 'zoom.exe')"""
        # Implementation would enumerate audio sessions and 
        # capture from specific application
        pass