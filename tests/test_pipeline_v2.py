import pytest
import asyncio
import numpy as np
from src.core.pipeline import AsyncPipeline

@pytest.mark.asyncio
async def test_pipeline_integration():
    pipeline = AsyncPipeline(model_size="tiny") # Modèle rapide pour test
    pipeline.is_running = True
    
    # Simuler un segment audio (silence ici mais suffisant pour tester les queues)
    # Dans un vrai test on mettrait de la parole pré-enregistrée
    chunk = np.zeros(512, dtype=np.float32)
    
    # On ajoute juste assez de chunks pour déclencher la VAD si possible 
    # ou on injecte directement dans la transcription_queue pour tester la suite
    
    test_text = "Bonjour le monde"
    await pipeline.translation_queue.put((test_text, "fr", 0))
    
    # On laisse le pipeline tourner un peu
    # On ne peut pas facilement tester le TTS sans sortie audio dans le CI, 
    # mais on peut vérifier que les queues se vident
    
    # On attend que la queue de traduction soit traitée
    timeout = 10
    start = asyncio.get_event_loop().time()
    while not pipeline.translation_queue.empty() and (asyncio.get_event_loop().time() - start) < timeout:
        await asyncio.sleep(0.1)
        
    # On arrête proprement (note: start() est bloquant, on ne l'appelle pas ici)
    pipeline.stop()
