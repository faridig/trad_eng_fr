import asyncio
import numpy as np
import sounddevice as sd
from src.core.pipeline import AsyncPipeline

async def record_and_process():
    # Configuration
    SAMPLE_RATE = 16000
    CHUNK_DURATION = 0.032 # 32ms
    CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)
    
    print("--- 🎙️ TEST LIVE SPRINT 2 ---")
    print(f"Initialisation du pipeline avec le modèle LARGE-V3 (Précision maximale)...")
    
    # On utilise large-v3 pour éviter les hallucinations phonétiques
    pipeline = AsyncPipeline(model_size="large-v3", input_sample_rate=SAMPLE_RATE)
    
    # Lancement des tâches de fond
    tasks = [
        asyncio.create_task(pipeline.process_audio_loop()),
        asyncio.create_task(pipeline.transcription_loop()),
        asyncio.create_task(pipeline.translation_loop()),
        asyncio.create_task(pipeline.tts_loop())
    ]
    
    await asyncio.sleep(1) # Warm-up

    def audio_callback(indata, frames, time, status):
        if status:
            print(status)
        # On envoie le chunk dans la queue du pipeline de manière asynchrone
        loop.call_soon_threadsafe(pipeline.audio_queue.put_nowait, indata.copy().flatten())

    loop = asyncio.get_running_loop()
    
    print("\n✅ SYSTÈME PRÊT. Parlez maintenant (Français ou Anglais)...")
    print("Appuyez sur Ctrl+C pour arrêter.")
    
    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=audio_callback, blocksize=CHUNK_SIZE):
            while True:
                await asyncio.sleep(0.1)
    except KeyboardInterrupt:
        print("\nArrêt en cours...")
    finally:
        pipeline.stop()
        for t in tasks:
            t.cancel()
        print("Test terminé.")

if __name__ == "__main__":
    try:
        asyncio.run(record_and_process())
    except KeyboardInterrupt:
        pass
