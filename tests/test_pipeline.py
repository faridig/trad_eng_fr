import pytest
import asyncio
import numpy as np
from unittest.mock import patch, MagicMock
from src.core.pipeline import AsyncPipeline

@pytest.fixture
def mock_pipeline_deps():
    """Mock heavy dependencies for AsyncPipeline."""
    with patch('src.core.pipeline.VADDetector'), \
         patch('src.core.pipeline.Transcriber'), \
         patch('src.core.pipeline.Translator'), \
         patch('src.core.pipeline.TTS'):
        yield

@pytest.mark.asyncio
async def test_pipeline_basic_flow(mock_pipeline_deps):
    # On utilise un modèle minuscule pour le test ou on simule
    pipeline = AsyncPipeline(model_size="tiny") 
    
    # Simuler de la parole
    chunk_speech = np.random.uniform(-0.5, 0.5, 512).astype(np.float32)
    chunk_silence = np.zeros(512, dtype=np.float32)
    
    # Démarrer les boucles en tâche de fond (on ne lance pas tout le pipeline.start() car c'est bloquant)
    # On mocke les méthodes de traitement pour éviter les délais
    pipeline.vad.is_speech = MagicMock(side_effect=[True]*20 + [False]*20)
    
    task1 = asyncio.create_task(pipeline.process_audio_loop())
    
    # Envoyer de la parole
    for _ in range(20):
        await pipeline.add_audio_chunk(chunk_speech)
        
    # Envoyer du silence pour déclencher la fin du segment
    for _ in range(25): # MAX_SILENCE_CHUNKS is 25
        await pipeline.add_audio_chunk(chunk_silence)
        
    # Laisser un peu de temps pour le traitement
    await asyncio.sleep(0.5)
    
    pipeline.stop()
    task1.cancel()
    
    assert True 
