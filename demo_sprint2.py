import asyncio
import numpy as np
import soundfile as sf
from src.core.pipeline import AsyncPipeline

async def run_demo():
    print("Initialisation du pipeline Sprint 2...")
    pipeline = AsyncPipeline(model_size="large-v3")
    
    # Lancement des boucles en arrière-plan
    tasks = [
        asyncio.create_task(pipeline.process_audio_loop()),
        asyncio.create_task(pipeline.transcription_loop()),
        asyncio.create_task(pipeline.translation_loop()),
        asyncio.create_task(pipeline.tts_loop())
    ]
    
    print("Lecture du fichier de test 'test_micro.wav'...")
    data, samplerate = sf.read('test_micro.wav')
    
    # On s'assure que c'est du 16kHz mono
    if samplerate != 16000:
        # Simplification pour la démo: on suppose que le fichier est déjà au bon format
        # ou on pourrait resampler
        pass
        
    # Découpage en chunks de 32ms (512 samples à 16kHz)
    chunk_size = 512
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        if len(chunk) == chunk_size:
            await pipeline.add_audio_chunk(chunk.astype(np.float32))
            # Simuler le temps réel
            await asyncio.sleep(0.01) # Accéléré pour la démo
            
    print("Attente de la fin du traitement...")
    await asyncio.sleep(10) # Laisse le temps au pipeline de finir
    
    pipeline.stop()
    for t in tasks:
        t.cancel()
    print("Démo terminée.")

if __name__ == "__main__":
    asyncio.run(run_demo())
