import asyncio
import sounddevice as sd
import numpy as np
from src.core.pipeline import AsyncPipeline

async def main():
    pipeline = AsyncPipeline()
    
    # Paramètres audio
    fs = 16000
    chunk_size = 512 # 32ms, recommandé pour Silero VAD
    
    def audio_callback(indata, frames, time, status):
        if status:
            print(status)
        # On pousse le chunk dans une boucle d'événement séparée car callback est bloquant
        asyncio.run_coroutine_threadsafe(pipeline.add_audio_chunk(indata.copy().flatten()), loop)

    print("--- Démarrage de la capture Audio (Micro) ---")
    print("Parlez dans le micro...")
    
    global loop
    loop = asyncio.get_running_loop()
    
    # Démarrer les tâches du pipeline
    p_task = asyncio.create_task(pipeline.process_audio_loop())
    t_task = asyncio.create_task(pipeline.transcription_loop())
    
    # Ouvrir le flux audio
    with sd.InputStream(samplerate=fs, channels=1, callback=audio_callback, blocksize=chunk_size):
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n--- Arrêt ---")
        finally:
            pipeline.stop()
            p_task.cancel()
            t_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
