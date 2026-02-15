import asyncio
import numpy as np
import soundfile as sf
from src.core.pipeline import AsyncPipeline

async def run_demo():
    print("Initialisation du pipeline Sprint 2 (Robust Edition)...")
    
    # Lecture du fichier de test pour obtenir le samplerate
    print("Analyse du fichier de test 'test_micro.wav'...")
    data, samplerate = sf.read('test_micro.wav')
    print(f"Format détecté: {samplerate}Hz, {data.ndim} canaux")

    pipeline = AsyncPipeline(model_size="large-v3", input_sample_rate=samplerate)
    
    # Lancement des boucles en arrière-plan
    tasks = [
        asyncio.create_task(pipeline.process_audio_loop()),
        asyncio.create_task(pipeline.transcription_loop()),
        asyncio.create_task(pipeline.translation_loop()),
        asyncio.create_task(pipeline.tts_loop())
    ]
    
    # Découpage en chunks de 32ms (relatif au samplerate d'entrée)
    chunk_size = int(samplerate * 0.032) 
    print(f"Envoi de l'audio par chunks de {chunk_size} samples...")
    
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        await pipeline.add_audio_chunk(chunk)
        # On ne simule plus le sleep ici pour aller plus vite dans le test
        # mais dans un vrai micro, ça viendrait au fil de l'eau
            
    print("Attente de la fin du traitement (15s)...")
    await asyncio.sleep(15) 
    
    pipeline.stop()
    for t in tasks:
        t.cancel()
    print("Démo terminée.")

if __name__ == "__main__":
    asyncio.run(run_demo())
