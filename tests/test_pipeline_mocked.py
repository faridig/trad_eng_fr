import pytest
import asyncio
import numpy as np
from unittest.mock import MagicMock, patch, AsyncMock
from src.core.pipeline import AsyncPipeline

# Helper pour simuler des objets complexes
class MockInfo:
    def __init__(self, language="fr", language_probability=0.9):
        self.language = language
        self.language_probability = language_probability

@pytest.fixture
def mock_pipeline_components():
    """Mocks all heavy dependencies of the pipeline."""
    with patch("src.core.pipeline.VADDetector") as MockVAD, \
         patch("src.core.pipeline.Transcriber") as MockTranscriber, \
         patch("src.core.pipeline.Translator") as MockTranslator, \
         patch("src.core.pipeline.TTS") as MockTTS, \
         patch("src.core.pipeline.T.Resample") as MockResample:
        
        # VAD Setup
        vad_instance = MockVAD.return_value
        # Par défaut, on dit que c'est de la parole
        vad_instance.is_speech.return_value = True
        
        # Transcriber Setup
        transcriber_instance = MockTranscriber.return_value
        transcriber_instance.transcribe.return_value = ("Hello World", MockInfo(language="en"))
        
        # Translator Setup
        translator_instance = MockTranslator.return_value
        translator_instance.translate.return_value = "Bonjour le monde"
        
        # TTS Setup
        tts_instance = MockTTS.return_value
        tts_instance.generate.return_value = (np.zeros(100, dtype=np.float32), 24000)
        tts_instance.play = MagicMock()
        
        # Resample Setup (just pass through or return valid tensor)
        resample_instance = MockResample.return_value
        resample_instance.side_effect = lambda x: x # Identity
        
        yield {
            "vad": vad_instance,
            "transcriber": transcriber_instance,
            "translator": translator_instance,
            "tts": tts_instance,
            "resample": resample_instance
        }

@pytest.mark.asyncio
async def test_full_pipeline_flow_mocked(mock_pipeline_components):
    """Test the full pipeline logic using mocks (CPU friendly)."""
    
    # Init Pipeline
    pipeline = AsyncPipeline(model_size="tiny", device="cpu")
    
    # Override MAX_SILENCE_CHUNKS to make test faster
    pipeline.MAX_SILENCE_CHUNKS = 2
    
    # Start tasks
    tasks = [
        asyncio.create_task(pipeline.process_audio_loop()),
        asyncio.create_task(pipeline.transcription_loop()),
        asyncio.create_task(pipeline.translation_loop()),
        asyncio.create_task(pipeline.tts_loop())
    ]
    
    try:
        # 1. Feed Speech (3 chunks)
        # Configure VAD to say "True"
        mock_pipeline_components["vad"].is_speech.return_value = True
        speech_chunk = np.random.uniform(-0.5, 0.5, 512).astype(np.float32)
        
        for _ in range(3):
            await pipeline.add_audio_chunk(speech_chunk)
            # Give a tiny bit of time for loop to pick it up
            await asyncio.sleep(0.01)
            
        # 2. Feed Silence (to trigger segment end)
        # Configure VAD to say "False"
        mock_pipeline_components["vad"].is_speech.return_value = False
        silence_chunk = np.zeros(512, dtype=np.float32)
        
        # Needs MAX_SILENCE_CHUNKS (2) + 1 to be sure
        for _ in range(4):
            await pipeline.add_audio_chunk(silence_chunk)
            await asyncio.sleep(0.01)
            
        # 3. Wait for processing
        # We expect TTS.play to be called eventually
        # Simple polling with timeout
        max_retries = 20
        for _ in range(max_retries):
            if mock_pipeline_components["tts"].play.called:
                break
            await asyncio.sleep(0.1)
            
        # Assertions
        assert mock_pipeline_components["transcriber"].transcribe.called, "Transcriber should have been called"
        assert mock_pipeline_components["translator"].translate.called, "Translator should have been called"
        assert mock_pipeline_components["tts"].generate.called, "TTS generate should have been called"
        assert mock_pipeline_components["tts"].play.called, "TTS play should have been called"
        
        # Verify args if needed
        # args, _ = mock_pipeline_components["translator"].translate.call_args
        # assert args[0] == "Hello World"
        
    finally:
        pipeline.stop()
        # Cancel all tasks
        for t in tasks:
            t.cancel()
        # Wait for cancellation to complete (suppress CancelledError)
        await asyncio.gather(*tasks, return_exceptions=True)
