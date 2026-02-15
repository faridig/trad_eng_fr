import pulsectl

def list_audio_devices():
    with pulsectl.Pulse('device-lister') as pulse:
        info = pulse.server_info()
        print(f"--- SERVER DEFAULTS ---")
        print(f"Default Sink: {info.default_sink_name}")
        print(f"Default Source: {info.default_source_name}\n")

        print("--- Audio Sources (Inputs/Monitors) ---")
        for source in pulse.source_list():
            marker = "[DEFAULT]" if source.name == info.default_source_name else ""
            print(f"ID: {source.index}, Name: {source.name} {marker}, Description: {source.description}")
            
        print("\n--- Audio Sinks (Outputs) ---")
        for sink in pulse.sink_list():
            marker = "[DEFAULT]" if sink.name == info.default_sink_name else ""
            print(f"ID: {sink.index}, Name: {sink.name} {marker}, Description: {sink.description}")

if __name__ == "__main__":
    try:
        list_audio_devices()
    except Exception as e:
        print(f"Error listing devices: {e}")
