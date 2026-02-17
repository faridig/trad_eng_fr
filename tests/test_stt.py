import pytest
import torch
import numpy as np
import wave
import os
from src.stt.transcriber import Transcriber

def load_wav_to_numpy(path):
    with wave.open(path, 'rb') as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        
        data = wf.readframes(n_frames)
        audio = np.frombuffer(data, dtype=np.int16)
        
        if n_channels > 1:
            audio = audio[::n_channels]
            
        return audio.astype(np.float32) / 32768.0

@pytest.mark.gpu
@pytest.mark.skipif(not torch.cuda.is_available(), reason="GPU not available")
@pytest.mark.skipif(not os.path.exists("test_micro.wav"), reason="Test file not found")
def test_transcription_on_file():
    # On utilise le défaut de la classe (large-v3)
    transcriber = Transcriber(device="cuda")
    audio = load_wav_to_numpy("test_micro.wav")
    
    text, info = transcriber.transcribe(audio, language="fr")
    
    print(f"\nTranscribed text: {text}")
    print(f"Language detected: {info.language} ({info.language_probability:.2f})")
    
    assert text != ""
    assert info.language == "fr"
