import pulsectl
import subprocess
import os

def find_devices():
    """Détecte dynamiquement les périphériques par défaut du système."""
    with pulsectl.Pulse('device-finder') as pulse:
        info = pulse.server_info()
        
        # Micro par défaut
        micro = info.default_source_name
        
        # Sortie par défaut (Sink) -> on utilise son moniteur pour le Loopback
        default_sink = info.default_sink_name
        system = f"{default_sink}.monitor"
        
        return micro, system

def record_simultaneous(micro, system, duration=5):
    print(f"Recording simultaneous: Micro({micro}) and System({system}) for {duration}s...")
    
    # Commande FFmpeg robuste et dynamique
    cmd = [
        'ffmpeg', '-y',
        '-loglevel', 'error',
        '-thread_queue_size', '1024', '-t', str(duration), '-f', 'pulse', '-i', micro,
        '-thread_queue_size', '1024', '-t', str(duration), '-f', 'pulse', '-i', system,
        '-map', '0:a', 'test_micro.wav',
        '-map', '1:a', 'test_system.wav'
    ]
    
    try:
        subprocess.run(cmd, check=True, timeout=duration + 5)
        print("Simultaneous recording successful.")
    except subprocess.TimeoutExpired:
        print("Error: Recording timed out. FFmpeg failed to stop.")
        raise
    except subprocess.CalledProcessError as e:
        print(f"Error during recording: {e}")
        raise

def main():
    try:
        micro, system = find_devices()
        print(f"Detected Default Micro: {micro}")
        print(f"Detected Default System (Monitor): {system}")
        
        record_simultaneous(micro, system)
        print("PoC Complete. Files: test_micro.wav, test_system.wav")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    main()
