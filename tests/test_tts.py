import pytest
import numpy as np
from src.core.tts import TTS

@pytest.fixture(scope="module")
def tts():
    return TTS()

def test_tts_generation_en(tts):
    text = "Hello, this is a test."
    samples, sample_rate = tts.generate(text, voice="af_heart", lang="en-us")
    assert samples is not None
    assert sample_rate == 24000
    assert len(samples) > 0

def test_tts_generation_fr(tts):
    # Note: Kokoro v0.19 supporte le français avec lang="fr-fr"
    # Certaines versions de kokoro-onnx peuvent nécessiter une configuration spécifique
    text = "Bonjour, c'est un test."
    samples, sample_rate = tts.generate(text, voice="af_sarah", lang="fr-fr")
    assert samples is not None
    assert len(samples) > 0
