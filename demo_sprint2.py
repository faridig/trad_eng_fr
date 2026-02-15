import asyncio
import numpy as np
import soundfile as sf
from src.core.pipeline import AsyncPipeline

async def run_demo():
    print("Initialisation du pipeline Sprint 2 (Robust Edition)...")
    
    # Utilisation d'un fichier avec du son (out1.wav) car test_micro.wav est vide
    test_file = 'out1.wav'
    print(f"Analyse du fichier de test '{test_file}'...")
    data, samplerate = sf.read(test_file)
    print(f"Format détecté: {samplerate}Hz, {data.ndim} canaux")

    pipeline = AsyncPipeline(model_size="large-v3", input_sample_rate=samplerate)
    
    # Lancement des boucles en arrière-plan (sans bloquer)
    tasks = [
        asyncio.create_task(pipeline.process_audio_loop()),
        asyncio.create_task(pipeline.transcription_loop()),
        asyncio.create_task(pipeline.translation_loop()),
        asyncio.create_task(pipeline.tts_loop())
    ]
    
    # Laisser un court instant pour l'amorçage des tâches
    await asyncio.sleep(0.5)
    
    # Découpage en chunks de 32ms (relatif au samplerate d'entrée)
    chunk_size = int(samplerate * 0.032) 
    print(f"Envoi de l'audio par chunks de {chunk_size} samples...")
    
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i+chunk_size]
        await pipeline.add_audio_chunk(chunk)
            
    print("Attente de la fin du traitement (15s)...")
    await asyncio.sleep(15) 
    
    pipeline.stop()
    for t in tasks:
        t.cancel()
    print("Démo terminée.")

if __name__ == "__main__":
    asyncio.run(run_demo())
