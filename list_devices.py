import pulsectl

def list_audio_devices():
    print("--- Audio Sources (Inputs/Monitors) ---")
    with pulsectl.Pulse('device-lister') as pulse:
        for source in pulse.source_list():
            print(f"ID: {source.index}, Name: {source.name}, Description: {source.description}")
            
    print("\n--- Audio Sinks (Outputs) ---")
    with pulsectl.Pulse('device-lister') as pulse:
        for sink in pulse.sink_list():
            print(f"ID: {sink.index}, Name: {sink.name}, Description: {sink.description}")

if __name__ == "__main__":
    try:
        list_audio_devices()
    except Exception as e:
        print(f"Error listing devices: {e}")
        print("Fallback: Use 'pactl list sources short'")
