import pulsectl
import subprocess
import time
import os

def find_devices():
    with pulsectl.Pulse('device-finder') as pulse:
        micro = None
        system = None
        
        sources = pulse.source_list()
        for s in sources:
            if "Mic1" in s.name or "Digital Microphone" in s.description:
                micro = s.name
            if "Speaker" in s.name and s.name.endswith(".monitor"):
                system = s.name
                
        return micro, system

def record_ffmpeg(source, filename, duration=5):
    print(f"Recording from {source} to {filename} for {duration}s...")
    cmd = [
        'ffmpeg', '-y',
        '-f', 'pulse',
        '-i', source,
        '-t', str(duration),
        filename
    ]
    subprocess.run(cmd, check=True)

def main():
    micro, system = find_devices()
    print(f"Micro device: {micro}")
    print(f"System device: {system}")
    
    if not micro or not system:
        print("Error: Could not find required devices.")
        return

    # Record micro
    record_ffmpeg(micro, "test_micro.wav")
    
    # Record system (Loopback)
    record_ffmpeg(system, "test_system.wav")
    
    print("PoC Complete. Check test_micro.wav and test_system.wav")

if __name__ == "__main__":
    main()
