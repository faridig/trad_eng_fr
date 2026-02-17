import pytest
import asyncio
import numpy as np
from unittest.mock import patch
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
async def test_pipeline_integration(mock_pipeline_deps):
    pipeline = AsyncPipeline(model_size="tiny") # Modèle rapide pour test
    pipeline.is_running = True
    
    # Simuler un segment audio (silence ici mais suffisant pour tester les queues)
    chunk = np.zeros(512, dtype=np.float32)
    
    test_text = "Bonjour le monde"
    await pipeline.translation_queue.put((test_text, "fr", 0))
    
    # On attend que la queue de traduction soit traitée ou timeout court
    timeout = 1
    start = asyncio.get_event_loop().time()
    while not pipeline.translation_queue.empty() and (asyncio.get_event_loop().time() - start) < timeout:
        await asyncio.sleep(0.1)
        
    pipeline.stop()
