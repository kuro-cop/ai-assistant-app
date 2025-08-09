#!/usr/bin/env python3
"""
Setup script for AI Assistant App
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is supported"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is supported")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    # Core dependencies
    core_packages = [
        "PyQt6>=6.6.0",
        "pystray>=0.19.4", 
        "plyer>=2.1.0",
        "sounddevice>=0.4.6",
        "numpy>=1.21.0",
        "Pillow>=10.1.0",
        "requests>=2.31.0"
    ]
    
    # Optional: Whisper for speech recognition
    whisper_packages = [
        "openai-whisper>=20231117",
        "torch>=2.1.0"
    ]
    
    try:
        # Install core packages
        for package in core_packages:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            
        # Ask about Whisper installation (large download)
        install_whisper = input("Install Whisper for speech recognition? (y/N): ").lower().startswith('y')
        
        if install_whisper:
            print("🎤 Installing Whisper (this may take a while)...")
            for package in whisper_packages:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        else:
            print("ℹ️ Skipping Whisper installation. Speech recognition will not be available.")
            
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_directories():
    """Create necessary directories"""
    print("📁 Setting up directories...")
    
    directories = [
        "data",
        "logs",
        "screenshots", 
        "recordings"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Created: {directory}/")
        else:
            print(f"Exists: {directory}/")
            
    print("✅ Directories set up successfully")

def test_audio_devices():
    """Test audio device availability"""
    print("🎤 Testing audio devices...")
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        
        print("Available audio devices:")
        for i, device in enumerate(devices):
            device_type = "🎤" if device['max_input_channels'] > 0 else "🔊"
            print(f"  {i}: {device_type} {device['name']}")
            
        # Test default devices
        default_input = sd.query_devices(kind='input')
        default_output = sd.query_devices(kind='output')
        
        print(f"\nDefault input: {default_input['name']}")
        print(f"Default output: {default_output['name']}")
        
        print("✅ Audio system is working")
        return True
        
    except ImportError:
        print("❌ sounddevice not available")
        return False
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        return False

def create_desktop_shortcut():
    """Create desktop shortcut (Windows)"""
    if sys.platform != "win32":
        return
        
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "AI Assistant.lnk")
        target = os.path.join(os.getcwd(), "main.py")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = sys.executable
        shortcut.Arguments = f'"{target}"'
        shortcut.WorkingDirectory = os.getcwd()
        shortcut.IconLocation = sys.executable
        shortcut.save()
        
        print(f"✅ Desktop shortcut created: {shortcut_path}")
        
    except ImportError:
        print("ℹ️ Install pywin32 and winshell for desktop shortcut creation")
    except Exception as e:
        print(f"ℹ️ Could not create desktop shortcut: {e}")

def main():
    """Main setup function"""
    print("🤖 AI Assistant App Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
        
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        sys.exit(1)
        
    # Setup directories
    setup_directories()
    
    # Test audio
    test_audio_devices()
    
    # Create shortcut (optional)
    create_desktop_shortcut()
    
    print("\n" + "=" * 40)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Run: python main.py")
    print("2. Try saying: '今のところメモ'")
    print("3. Check created tasks with: python main.py tasks")
    print("\nFor system tray mode (future):")
    print("4. Run: python -m src.ui.tray")

if __name__ == "__main__":
    main()