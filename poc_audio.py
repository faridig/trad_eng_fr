import pulsectl
import subprocess
import os

def find_devices():
    with pulsectl.Pulse('device-finder') as pulse:
        micro = None
        system = None
        
        sources = pulse.source_list()
        for s in sources:
            # Recherche du micro digital ou casque
            if "Mic1" in s.name or "Digital Microphone" in s.description:
                micro = s.name
            # Recherche du moniteur des haut-parleurs pour le son système
            if "Speaker" in s.name and s.name.endswith(".monitor"):
                system = s.name
                
        return micro, system

def record_simultaneous(micro, system, duration=5):
    print(f"Recording simultaneous: Micro({micro}) and System({system}) for {duration}s...")
    
    # Commande unique FFmpeg pour capture parallèle avec silence technique (-loglevel error)
    cmd = [
        'ffmpeg', '-y',
        '-loglevel', 'error',
        '-f', 'pulse', '-i', micro,
        '-f', 'pulse', '-i', system,
        '-t', str(duration),
        '-map', '0:a', 'test_micro.wav',
        '-map', '1:a', 'test_system.wav'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Simultaneous recording successful.")
    except subprocess.CalledProcessError as e:
        print(f"Error during recording: {e}")
        raise

def main():
    micro, system = find_devices()
    
    if not micro or not system:
        print(f"Error: Required devices not found. Micro: {micro}, System: {system}")
        return

    record_simultaneous(micro, system)
    print("PoC Complete. Files: test_micro.wav, test_system.wav")

if __name__ == "__main__":
    main()
